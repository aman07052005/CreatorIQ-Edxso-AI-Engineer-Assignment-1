# CreatorIQ final QA report — 10 November 2026

## Automated checks

- Dataset rows: 97
- Directory-reported follower range 5K–100K: 55
- Qualification results: 7 PASS / 48 PENDING / 42 FAIL
- Shortlist export: 7 PASS records only
- Personalized message export: 7 pairs only
- Email body word count: 78–80 (required 60–90)
- Social DM word count: 22–24 (required 15–30)
- Shortlist mandatory profile fields: populated; contact email uses `Not Found` where unavailable
- Email-eligible public routes: 15 overall; 15 in-range (shared rule used by dashboard and send/simulate validation)
- In-range populated email fields: 18; in-range engagement rates: 12; in-range recent average views: 18
- Unit tests: 19 passed
- Python compilation: passed for app.py, src/pipeline.py, generate_outputs.py and src/youtube_discovery.py
- CSV cross-checks: passed; source dataset, evaluated export, shortlist and message export counts reconcile
- ZIP integrity: verified after packaging
- Local UI verification: user launched the Streamlit app successfully and supplied screenshots showing Overview, Discover & Qualify, Outreach Studio and Activity Tracker rendering.

## Data-quality caveats

- Creator metrics are public third-party directory snapshots, not official live platform API results.
- PASS means the implemented rule's evidence threshold is met; it does not guarantee live account ownership, audience quality, demographics, brand fit or deliverability.
- Directory-reported engagement rates are not independently recalculated. Average views are never substituted for engagement rates.
- Missing email values remain `Not Found`; manager, business, organization and other routes must be checked for suitability before use.
- Email is simulated only; social DMs are manual-ready only. The supplied screenshots show logged simulation/manual-ready states, not actual delivery.

## Targeted corrections completed in this release

- Discover's email filter now uses the same public-source, verification and contact-type eligibility function as the outreach workflow.
- Dashboard metric is labelled `Email-eligible routes`, not generic public email fields.
- Technology keyword matching uses word/phrase boundaries to prevent false matches from `ai` appearing inside unrelated words.
- Tests cover accidental `ai` substring matches, shared email eligibility rules, and duplicate prevention for both email and social channels.
- README, QA report and requirement traceability counts reconciled to the generated dataset and 19-test suite.
