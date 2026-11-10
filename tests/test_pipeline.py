import pandas as pd

from src.pipeline import (
    classify_creator,
    is_valid_email,
    send_or_simulate,
)


def _eligible_row():
    return pd.Series({
        "name": "Demo Creator",
        "platform": "Instagram",
        "profile_url": "https://www.instagram.com/demo/",
        "followers": 12000,
        "category": "Technology Education",
        "content_themes": "software; coding; developer education",
        "engagement_rate": "2.5%",
        "metrics_source_url": "https://example.com/metrics",
        "contact_email": "demo@example.com",
        "email_source_url": "https://example.com/contact",
        "email_verification": "PUBLICLY_LISTED",
        "contact_type": "PUBLIC_CREATOR_COLLAB_CONTACT",
    })


def test_classification_passes_for_complete_technology_creator():
    row = _eligible_row()
    row["category"] = "Technology Education"
    row["content_themes"] = "coding; software engineering; developer education"
    row["metrics_source_url"] = "https://example.com/metrics"
    status, reason, score = classify_creator(row)
    assert status == "PASS"
    assert "technology & coding education" in reason.lower()
    assert score > 0


def test_generic_education_does_not_pass_technology_campaign():
    row = _eligible_row()
    row["category"] = "General Education"
    row["content_themes"] = "teaching; learning; student guidance"
    status, reason, _ = classify_creator(row)
    assert status == "PENDING"
    assert "technology & coding" in reason.lower()


def test_missing_engagement_rate_stays_pending():
    row = _eligible_row()
    row["category"] = "Technology"
    row["content_themes"] = "software; coding"
    row["engagement_rate"] = "Not Found"
    status, reason, _ = classify_creator(row)
    assert status == "PENDING"
    assert "engagement rate unavailable" in reason.lower()


def test_outside_follower_range_fails():
    row = _eligible_row()
    row["followers"] = 250000
    status, reason, _ = classify_creator(row)
    assert status == "FAIL"
    assert "above" in reason.lower()


def test_email_syntax_validation():
    assert is_valid_email("demo@example.com")
    assert not is_valid_email("Not Found")
    assert not is_valid_email("demo@invalid")


def test_email_simulation_and_duplicate_prevention(tmp_path, monkeypatch):
    import src.pipeline as pipeline
    db_path = tmp_path / "test.db"
    monkeypatch.setattr(pipeline, "DB_PATH", db_path)
    row = _eligible_row()

    first = pipeline.send_or_simulate(
        row, "Subject: Demo\n\nHello creator", "Hi there, nice work!",
        simulate=True, channel="EMAIL",
    )
    second = pipeline.send_or_simulate(
        row, "Subject: Demo\n\nHello creator", "Hi there, nice work!",
        simulate=True, channel="EMAIL",
    )
    assert first[0] is True
    assert "simulation logged" in first[1].lower()
    assert second[0] is False
    assert "duplicate" in second[1].lower()


def test_email_requires_public_source_metadata(tmp_path, monkeypatch):
    import src.pipeline as pipeline
    monkeypatch.setattr(pipeline, "DB_PATH", tmp_path / "test.db")
    row = _eligible_row()
    row["email_source_url"] = "Not Found"
    ok, message = pipeline.send_or_simulate(row, "email", "dm", channel="EMAIL")
    assert not ok
    assert "public email source" in message.lower()


def test_social_message_is_manual_only(tmp_path, monkeypatch):
    import src.pipeline as pipeline
    monkeypatch.setattr(pipeline, "DB_PATH", tmp_path / "test.db")
    row = _eligible_row()
    ok, message = pipeline.send_or_simulate(
        row, "email", "Hi creator, let's collaborate!",
        simulate=True, channel="SOCIAL_DM",
    )
    assert ok
    assert "no dm was sent" in message.lower()


def test_personalized_messages_meet_assignment_word_counts_for_qualified_shortlist():
    from src.pipeline import load_data, evaluate, personalized_messages
    data = evaluate(load_data())
    shortlist = data[data["computed_status"] == "PASS"]
    assert len(shortlist) >= 1
    for _, row in shortlist.iterrows():
        email, dm = personalized_messages(row)
        body = email.split("\n\n", 1)[1].split("\n\nBest,")[0]
        assert 60 <= len(body.split()) <= 90, (row["name"], len(body.split()))
        assert 15 <= len(dm.split()) <= 30, (row["name"], len(dm.split()))


def test_creator_greeting_uses_first_name():
    from src.pipeline import personalized_messages
    email, dm = personalized_messages(_eligible_row().copy())
    assert "Hi Demo," in email


def test_third_party_directory_contact_is_not_email_eligible():
    from src.pipeline import _email_has_public_source
    row = _eligible_row()
    row["contact_type"] = "THIRD_PARTY_DIRECTORY_CONTACT"
    assert not _email_has_public_source(row)


def test_professional_title_is_removed_from_greeting():
    from src.pipeline import personalized_messages
    row = _eligible_row()
    row["name"] = "Dr Rishabh Jain"
    email, dm = personalized_messages(row)
    assert "Hi Rishabh," in email
    assert "Hi Dr," not in email


def test_dataset_contains_at_least_50_directory_listed_in_range():
    from src.pipeline import load_data
    data = load_data()
    in_range = data["followers"].between(5000, 100000)
    assert int(in_range.sum()) >= 50


def test_dataset_profile_urls_are_unique():
    from src.pipeline import load_data
    data = load_data()
    assert not data.duplicated(subset=["platform", "profile_url"]).any()


def test_only_qualified_creators_are_in_shortlist_export():
    from src.pipeline import load_data, evaluate
    data = evaluate(load_data())
    assert (data.loc[data.computed_status == "PASS", "followers"].between(5000, 100000)).all()
    assert data.loc[data.computed_status == "PASS", "engagement_rate"].astype(str).str.contains("%", regex=False).all()


def test_unqualified_creator_cannot_be_queued(tmp_path, monkeypatch):
    import src.pipeline as pipeline
    monkeypatch.setattr(pipeline, "DB_PATH", tmp_path / "test.db")
    row = _eligible_row()
    row["category"] = "Food"
    row["content_themes"] = "recipes; cooking"
    ok, message = pipeline.send_or_simulate(row, "email", "dm", channel="EMAIL")
    assert not ok
    assert "not pass-qualified" in message.lower()


def test_ai_keyword_requires_word_boundary():
    row = _eligible_row()
    row["category"] = "General Education"
    row["content_themes"] = "said; retail; mail; detailed explanations"
    status, reason, _ = classify_creator(row)
    assert status == "PENDING"
    assert "no explicit technology" in reason.lower()


def test_email_filter_rule_matches_outreach_eligibility():
    from src.pipeline import _email_has_public_source
    row = _eligible_row()
    assert _email_has_public_source(row)
    row["contact_type"] = "THIRD_PARTY_DIRECTORY_CONTACT"
    assert not _email_has_public_source(row)
    row["contact_type"] = "PUBLIC_CREATOR_COLLAB_CONTACT"
    row["email_verification"] = "NOT_VERIFIED"
    assert not _email_has_public_source(row)


def test_manual_social_duplicate_is_blocked_but_other_channel_is_distinct(tmp_path, monkeypatch):
    import src.pipeline as pipeline
    monkeypatch.setattr(pipeline, "DB_PATH", tmp_path / "test.db")
    row = _eligible_row()
    first = pipeline.send_or_simulate(
        row, "email", "Hi creator, let's collaborate!", channel="SOCIAL_DM"
    )
    duplicate = pipeline.send_or_simulate(
        row, "email", "Hi creator, let's collaborate!", channel="SOCIAL_DM"
    )
    email = pipeline.send_or_simulate(
        row, "Subject: Demo\n\nHello creator", "Hi creator!", channel="EMAIL"
    )
    assert first[0] is True
    assert duplicate[0] is False
    assert "duplicate" in duplicate[1].lower()
    assert email[0] is True
