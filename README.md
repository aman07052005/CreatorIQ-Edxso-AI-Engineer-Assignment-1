# CreatorIQ — Edxso AI Engineer Intern Assignment

CreatorIQ is a Python + Streamlit prototype for discovering creators, filtering by audience size and content relevance, enriching public contact data, generating personalized outreach drafts, and logging safe outreach simulations.

## What's included

- Streamlit dashboard with Overview, Discover & Qualify, Outreach Studio, and Activity Tracker tabs.
- A 97-record discovery dataset (`data/influencers.csv`).
- 55 records whose directory-reported follower counts fall between 5,000 and 100,000.
- 42 out-of-range records retained as discovery failures rather than silently deleted.
- 7 email and social-message draft pairs generated only for creators passing the campaign qualification rule.
- Downloadable filtered/evaluated dataset and outreach history.
- SQLite outreach log with duplicate prevention by creator + channel.
- Unit tests and architecture notes.

## Dataset quality and interpretation

**Important distinction:** 55 records are *directory-listed in the 5K–100K range*. This is not the same as 55 live-verified platform counts. Some public directory pages were indexed several months before this research snapshot, and the prototype does not have official Instagram/YouTube APIs connected. Recheck each profile's current follower count and ownership before contacting a creator.

The expanded records are sourced from public creator-directory pages. Instagram handles shown on those pages are used for profile links. YouTube handles are used only where the directory provides an exact handle. Where a directory does not expose a reliable email or engagement figure, the dataset says `Not Found`. A profile URL assembled from a directory-published handle is a profile locator, not independent proof of ownership or current availability.

### Snapshot metrics (10 Nov 2026)

| Measure | Result |
|---|---:|
| Total discovery records | 97 |
| Directory-reported records in 5K–100K range | 55 |
| Out-of-range discovery records retained | 42 |
| Fully qualified Technology & Coding Education creators | 7 |
| In-range rows with a non-Not Found email field | 18 |
| In-range rows with a recorded engagement rate | 12 |
| In-range rows with recent average views | 18 |
| Email-eligible public contact routes (all records) | 15 |
| Email-eligible public contact routes (in-range) | 15 |
| Personalized message sets generated for PASS creators | 7 |
| Automated tests | 19 passed |

The 19 non-`Not Found` email fields across the full 97-record dataset are **not 19 direct creator emails**. They include professional, channel, organization, public collaboration, manager, business, and third-party directory routes. The three Socialveins intermediary addresses are explicitly labeled `THIRD_PARTY_DIRECTORY_CONTACT` and are excluded from the email-simulation eligibility rule. Manager/business contacts are identified by `contact_type` and should be checked for campaign suitability before use.

Average views are stored separately in `avg_views_recent`; they are never converted into an engagement rate. A directory-reported engagement value is not independently recalculated by this prototype.

### Sources used for the expanded dataset

- The Influencer Sync — Indian micro tech and gaming list: https://theinfluencersync.com/influencer-list/list-of-micro-tech-and-gaming-influencers-with-over-10k-followers-upto-99k
- The Influencer Sync — Indian micro business and finance list: https://theinfluencersync.com/influencer-list/list-of-micro-business-and-finance-influencers-with-over-10k-followers-upto-99k
- The Influencer Sync — Indian micro sports and fitness list: https://theinfluencersync.com/influencer-list/list-of-micro-sports-and-fitness-influencers-with-over-10k-followers-upto-99k
- The Influencer Sync — Indian micro food list: https://theinfluencersync.com/influencer-list/list-of-micro-food-influencers-with-over-10k-followers-upto-99k
- InfluencerUnion — Indian creator category directories and individual YouTube creator pages, including finance, education/commentary, technology, and B2B/SaaS.
- Existing source links for the original 57 records remain in `source_url`, `metrics_source_url`, `content_signal_source_url`, and `email_source_url`.

Source pages are public third-party directories, not endorsements or official platform verification. Some The Influencer Sync pages were indexed 3–5 months before the 10 Nov 2026 snapshot; treat their counts as dated directory snapshots. The `source_checked_at` field records when the source page was reviewed for this dataset, not the date on which the directory originally measured the follower count.

## Qualification logic — completed category: Technology & Coding Education

The prototype implements one explicit campaign category rather than treating unrelated niches as a single audience:

- Follower window: 5,000–100,000 (configurable in the sidebar).
- Relevance terms include technology, software, AI, coding, programming, developer education, computer science, cybersecurity, data science, machine learning, Android, Linux, IoT, engineering and tech explainers. Matching uses whole-word/phrase boundaries (so `ai` cannot accidentally match inside words such as `said`, `retail` or `mail`).
- `PASS`: in-range, at least one explicit technology/coding signal, a source-reported engagement percentage, and a metrics source URL.
- `PENDING`: in-range but missing a required relevance or engagement evidence item.
- `FAIL`: outside the selected follower window.
- Contact email is not required to classify campaign fit: if unavailable, the field is `Not Found` and the creator cannot be selected for email simulation. Manual social outreach remains a human action.
- Current evaluation: 7 PASS, 48 PENDING, 42 FAIL out of 97 discovery records. The 55 in-range records are not represented as 55 qualified creators.
- Human review remains necessary for audience geography, profile activity, authenticity, content quality, audience fit and contact-route suitability. Demographics are not inferred.

## Contact enrichment rules

- No email is guessed or reconstructed from a masked address.
- `Not Found` is used when a public contact route is not available.
- `contact_type` distinguishes creator collaboration email, manager contact, business contact, organization contact, professional contact, channel public contact, and third-party directory contact.
- Email simulation requires a syntactically valid email, a public source URL, `PUBLICLY_LISTED` or `VERIFIED` status, and a contact type other than `THIRD_PARTY_DIRECTORY_CONTACT`. The Discover email-only filter calls the same shared eligibility function. A syntax check does not verify mailbox deliverability.
- Third-party directory relay emails are not treated as direct creator emails and are blocked from email simulation.

## Personalization

- Deterministic local message generation works without an API key or paid model credits.
- Email body target: 60–90 words.
- Social DM target: 15–30 words.
- Drafts use the creator's recorded name, niche, and content themes. They do not claim to have watched a recent post or invent audience demographics.
- Optional OpenAI personalization is disabled by default and falls back to deterministic generation if the API is unavailable.

## Outreach workflow and safety

- Email is simulation-only; no SMTP delivery occurs.
- Social/Instagram outreach is manual-ready only; no Instagram automation or DM sending occurs.
- SQLite logs creator, channel, status, timestamp, mode, and source URL.
- A unique creator + channel key prevents duplicate outreach records. The test suite checks duplicate rejection for both email simulation and manual social-message logging, while allowing the same creator to have one record per distinct channel.
- The user must review the draft, contact route, and profile before sending anything externally.

## Tech stack

- Python 3
- Streamlit
- Pandas
- SQLite
- python-dotenv
- OpenAI Python SDK (optional; deterministic fallback does not require it)
- pytest

## Run locally

```bash
python -m venv .venv
# Windows
.venv\\Scripts\\activate
# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt
streamlit run app.py
```

Run tests:

```bash
pytest -q
```

Regenerate evaluated dataset, shortlist, message drafts, and tracker template:

```bash
python generate_outputs.py
```

## Project structure

```text
creatoriq/
├── app.py
├── generate_outputs.py
├── requirements.txt
├── data/
│   ├── influencers.csv
│   ├── evaluated_dataset.csv
│   ├── shortlisted_creators.csv
│   ├── personalized_messages.csv
│   └── outreach_tracker.csv
├── docs/
│   └── architecture.md
├── src/
│   ├── pipeline.py
│   └── youtube_discovery.py
└── tests/
    ├── conftest.py
    └── test_pipeline.py
```

## Known limitations and next production steps

1. Connect approved official platform APIs or a compliant licensed provider for live follower counts, post-level engagement, audience demographics, and profile ownership checks.
2. Revalidate all directory-listed profiles and record the date of each live check.
3. Verify email deliverability and whether the route belongs to the creator, a manager, or an organization before outreach.
4. Add role-based access, secrets management, rate limiting, observability, and a persistent deployment database before production use.
5. Keep Instagram outreach manual unless the platform's current policies and an approved API explicitly permit the intended automation.

**This is a functional assignment prototype with a 97-row directory-sourced discovery set, 55 directory-listed in-range profiles, and 7 records currently passing the implemented Technology & Coding Education rule. These are source-snapshot-qualified, not live-platform-verified. It is not a production outreach platform.**

## AI model and prompt policy

The optional LLM path uses the OpenAI Python SDK with `gpt-4o-mini` by default (override with `OPENAI_MODEL`). It is off by default and requires the user's own `OPENAI_API_KEY`; no API key is bundled. The prompt supplies only the creator's recorded name, platform, category and content themes, requests JSON containing an email subject/body and DM, enforces the assignment word ranges, and explicitly prohibits inventing recent posts, demographics, metrics or contact details. If the API key is absent, billing/quota fails, the response is invalid, or word limits are missed, the local deterministic generator is used. No paid API is needed for the prototype's core workflow.

## Requirement traceability and demo

See [`docs/requirement_traceability.md`](docs/requirement_traceability.md) for a requirement-by-requirement implementation map, [`docs/demo_walkthrough.md`](docs/demo_walkthrough.md) for a reproducible local demo sequence, and [`docs/demo_evidence/README.md`](docs/demo_evidence/README.md) for screenshots captured from the locally running four-tab app.
