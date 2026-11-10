from __future__ import annotations

import pandas as pd
import streamlit as st

from src.pipeline import (
    load_data, evaluate, classify_creator, personalized_messages,
    send_or_simulate, outreach_log, is_valid_email, _email_has_public_source,
)

st.set_page_config(
    page_title="CreatorIQ | Creator Intelligence",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    .block-container {padding-top: 1.6rem; padding-bottom: 2.5rem;}
    .hero {
        padding: 1.35rem 1.5rem; border-radius: 18px;
        background: linear-gradient(115deg, rgba(28,54,96,.95), rgba(63,80,132,.88));
        color: white; margin-bottom: 1rem;
    }
    .hero h1 {font-size: 2.15rem; margin: 0 0 .25rem 0; color: white;}
    .hero p {margin: 0; opacity: .9;}
    div[data-testid="stMetric"] {
        border: 1px solid rgba(128,128,128,.22);
        padding: .8rem 1rem; border-radius: 14px;
        background: rgba(128,128,128,.045);
    }
    .small-note {font-size: .82rem; opacity: .8;}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="hero">
  <h1>🎯 CreatorIQ</h1>
  <p>Creator discovery · qualification · enrichment · personalized outreach</p>
  <p class="small-note">Edxso AI Engineer Intern Assignment · Evidence-first prototype</p>
</div>
""", unsafe_allow_html=True)

base = load_data()
scored = evaluate(base)

with st.sidebar:
    st.header("⚙️ Campaign workspace")
    st.caption("Tune your target creator segment")
    min_followers = st.number_input("Minimum followers", 1000, 100000, 5000, 1000)
    max_followers = st.number_input("Maximum followers", 5000, 1000000, 100000, 5000)
    platform_options = ["All"] + sorted(scored["platform"].dropna().astype(str).unique().tolist())
    platform_filter = st.selectbox("Platform", platform_options)
    category_options = ["All"] + sorted(scored["category"].dropna().astype(str).unique().tolist())
    category_filter = st.selectbox("Niche", category_options)
    campaign = st.text_input(
        "Campaign theme",
        "Future-ready learning and institutional growth",
    )
    use_llm = st.checkbox(
        "Use OpenAI personalization (optional API key)",
        value=False,
        help="If unavailable or quota-limited, deterministic local generation is used.",
    )
    st.divider()
    st.info(
        "Safe mode: email actions are simulated only. Instagram/social messages "
        "are prepared for manual review; no platform automation is performed."
    )

scored[["computed_status", "computed_reason", "fit_score"]] = scored.apply(
    lambda row: classify_creator(row, int(min_followers), int(max_followers)),
    axis=1,
    result_type="expand",
)
in_range = scored["followers"].between(min_followers, max_followers)
email_eligible = scored.apply(
    lambda r: is_valid_email(r.get("contact_email", ""))
    and _email_has_public_source(r),
    axis=1,
)
profile_refresh = scored["enrichment_notes"].astype(str).str.contains(
    "directory snapshot|directory listing|recheck|recheck live", case=False, regex=True
)

# Dashboard summary
m1, m2, m3, m4 = st.columns(4)
m1.metric("Creator records", f"{len(scored):,}")
m2.metric("In selected range", f"{int(in_range.sum()):,}")
m3.metric("Email-eligible routes", f"{int(email_eligible.sum()):,}")
m4.metric("Qualified for campaign", f"{int((scored.computed_status == 'PASS').sum()):,}")

st.warning(
    f"Data-quality notice: {int(in_range.sum())} records currently fall inside the selected follower range "
    "according to their cited directory snapshots. Several directory pages are not live platform APIs; "
    "recheck current follower counts, audience geography and profile activity before real outreach."
)

overview, discovery, outreach, tracker = st.tabs(
    ["📊 Overview", "🔎 Discover & qualify", "✉️ Outreach studio", "📬 Activity tracker"]
)

with overview:
    left, right = st.columns([1.2, 1])
    with left:
        st.subheader("Audience-size distribution")
        bins = pd.cut(
            scored["followers"],
            bins=[0, 5000, 10000, 50000, 100000, 500000, float("inf")],
            labels=["<5K", "5–10K", "10–50K", "50–100K", "100–500K", "500K+"],
            include_lowest=True,
        )
        dist = bins.value_counts(sort=False).rename_axis("Follower tier").to_frame("Creators")
        st.bar_chart(dist)
    with right:
        st.subheader("Niche coverage")
        niche_counts = scored["category"].astype(str).value_counts().head(8)
        st.bar_chart(niche_counts)
        st.caption("Top 8 niches by record count.")
    st.subheader("Data quality snapshot")
    q1, q2, q3 = st.columns(3)
    q1.metric("Engagement rates present", int((scored.engagement_rate.astype(str) != "Not Found").sum()))
    q2.metric("Email fields populated", int((scored.contact_email.astype(str) != "Not Found").sum()))
    q3.metric("Recent average views present", int((scored.avg_views_recent.astype(str) != "Not Found").sum()))
    st.caption(
        "Average views are a separate reach signal and are never converted into an engagement rate. "
        "A listed email is not proof of deliverability."
    )
    st.download_button(
        "⬇️ Download full dataset",
        scored.to_csv(index=False).encode("utf-8"),
        "creatoriq_full_dataset.csv",
        "text/csv",
        use_container_width=True,
    )

with discovery:
    st.subheader("Search and filter creator records")
    search = st.text_input("Search by creator, niche, theme or platform", key="creator_search")
    only_in_range = st.checkbox("Show only creators in selected follower range", value=True)
    only_email = st.checkbox("Show only email-eligible contact routes", value=False)
    only_engagement = st.checkbox("Show only records with engagement data", value=False)

    view = scored.copy()
    if only_in_range:
        view = view[in_range]
    if platform_filter != "All":
        view = view[view["platform"].astype(str) == platform_filter]
    if category_filter != "All":
        view = view[view["category"].astype(str) == category_filter]
    if only_email:
        view = view[email_eligible.reindex(view.index, fill_value=False)]
    if only_engagement:
        view = view[view["engagement_rate"].astype(str) != "Not Found"]
    if search:
        mask = view.astype(str).apply(
            lambda col: col.str.contains(search, case=False, na=False)
        ).any(axis=1)
        view = view[mask]

    show_cols = [
        "name", "platform", "followers", "category", "engagement_rate",
        "avg_views_recent", "contact_email", "contact_type",
        "computed_status", "computed_reason", "profile_url", "source_url",
    ]
    st.caption(f"Showing {len(view)} records")
    st.dataframe(
        view[[c for c in show_cols if c in view.columns]],
        use_container_width=True,
        hide_index=True,
        column_config={
            "profile_url": st.column_config.LinkColumn("Creator profile"),
            "source_url": st.column_config.LinkColumn("Data source"),
        },
    )
    st.download_button(
        "⬇️ Export current filtered view",
        view.to_csv(index=False).encode("utf-8"),
        "creatoriq_filtered_creators.csv",
        "text/csv",
        use_container_width=True,
    )
    with st.expander("Understand qualification logic"):
        st.markdown("""
        - **PASS:** 5K–100K followers, explicit Technology & Coding Education relevance, and a source-reported engagement rate with a source URL.
        - **PENDING:** follower range fits, but niche relevance or a required metric still needs review.
        - **FAIL:** outside the selected follower range.
        - **Email simulation eligibility:** syntactically valid address, a public source URL and a permitted contact type.
        - Missing data remains `Not Found`; no inferred engagement rate, guessed email or fabricated demographic is added.
        """)

with outreach:
    st.subheader("Personalized creator outreach — qualified creators only")
    candidates = scored[scored.computed_status == "PASS"].copy()
    if platform_filter != "All":
        candidates = candidates[candidates.platform.astype(str) == platform_filter]
    if category_filter != "All":
        candidates = candidates[candidates.category.astype(str) == category_filter]

    if candidates.empty:
        st.info("No fully qualified creator matches the current campaign filters. Review pending records in Discover & qualify; do not outreach until qualification is complete.")
    else:
        chosen = st.selectbox("Select creator", candidates["name"].tolist())
        row = candidates[candidates.name == chosen].iloc[0]
        email_text, dm_text = personalized_messages(
            row, campaign=campaign, use_llm=use_llm
        )
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**Email pitch**")
            st.text_area("Editable email draft", email_text, height=260, key="email_draft")
            email_body = email_text.split("\n\n", 1)[1].split("\n\nBest,", 1)[0]
            email_words = len(email_body.split())
            st.caption(f"{email_words} words in email body · target 60–90")
        with c2:
            st.markdown("**Instagram / social DM**")
            st.text_area("Editable social draft", dm_text, height=180, key="dm_draft")
            st.caption(f"{len(dm_text.split())} words · target 15–30")
            st.caption(f"Creator profile: {row.profile_url}")
        st.caption(
            "Only PASS-qualified creators appear here. Personalization uses recorded niche and content themes. "
            "It does not claim to have viewed a recent post."
        )
        channel = st.radio(
            "Outreach mode",
            ["Email simulation", "Manual social message"],
            horizontal=True,
        )
        if channel == "Email simulation":
            email = str(row.get("contact_email", "")).strip()
            source = str(row.get("email_source_url", "")).strip()
            verified = str(row.get("email_verification", "")).upper() in {"PUBLICLY_LISTED", "VERIFIED"}
            contact_type = str(row.get("contact_type", "")).upper()
            if not is_valid_email(email):
                st.error("No syntactically valid email is recorded for this creator.")
            elif contact_type == "THIRD_PARTY_DIRECTORY_CONTACT":
                st.error("This is an intermediary directory route, not a direct creator contact.")
            elif not source.lower().startswith(("https://", "http://")) or not verified:
                st.error("Public email source and verification status are required.")
            else:
                st.info(f"Recipient route: {email} · Type: {contact_type}")
                if st.button("Log email simulation", type="primary", use_container_width=True):
                    ok, msg = send_or_simulate(
                        row, st.session_state.get("email_draft", email_text),
                        st.session_state.get("dm_draft", dm_text),
                        simulate=True, channel="EMAIL",
                    )
                    (st.success if ok else st.warning)(msg)
        else:
            st.info("This prepares a message for you to review and send manually. No Instagram DM is sent.")
            if st.button("Mark as ready for manual sending", type="primary", use_container_width=True):
                ok, msg = send_or_simulate(
                    row, st.session_state.get("email_draft", email_text),
                    st.session_state.get("dm_draft", dm_text),
                    simulate=True, channel="SOCIAL_DM",
                )
                (st.success if ok else st.warning)(msg)

with tracker:
    st.subheader("Outreach history")
    log = outreach_log()
    if log.empty:
        st.info("No outreach activity has been recorded yet.")
    else:
        st.dataframe(log, use_container_width=True, hide_index=True)
        st.download_button(
            "⬇️ Download outreach log",
            log.to_csv(index=False).encode("utf-8"),
            "creatoriq_outreach_log.csv",
            "text/csv",
        )
    st.caption("Unique creator + channel keys prevent duplicate outreach entries.")

st.divider()
st.caption(
    "CreatorIQ is a research prototype. Directory counts are snapshots, not live API checks. "
    "Revalidate profile ownership, current audience size, geography, recent engagement and contact routes before outreach."
)
