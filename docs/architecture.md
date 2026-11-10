# Architecture and workflow

CreatorIQ uses a small modular architecture intended for a local assignment prototype.

## Modules

- `app.py`: Streamlit presentation layer. It reads the creator dataset, displays qualification outcomes, lets the user inspect generated drafts, and exposes the two outreach workflows.
- `src/pipeline.py`: data normalization, rule-based classification, optional LLM generation with deterministic fallback, email eligibility checks, creator identity hashing, SQLite initialization/migration and outreach logging.
- `data/influencers.csv`: source-of-truth creator discovery/enrichment dataset. Missing facts are retained as `Not Found`.
- `data/outreach.db`: created on first outreach action; stores outreach records and enforces uniqueness by creator + channel.

## Data flow

1. `load_data()` reads and normalizes the CSV.
2. `classify_creator()` checks the 5K–100K audience window, explicit Technology & Coding Education relevance, and a source-reported engagement percentage with a source URL. Records with missing evidence remain PENDING.
3. The dashboard shows the dataset and computed status/reason/fit score.
4. `personalized_messages()` uses recorded creator context. OpenAI is optional; deterministic fallback is available.
5. The user reviews the draft and chooses email simulation or manual social-message preparation.
6. `send_or_simulate()` validates the channel-specific conditions and inserts a row into SQLite.
7. The unique database constraint blocks repeat outreach for the same creator and channel.

## Safety boundaries

- Email mode is simulation-only in this version. No SMTP message is sent.
- Social mode logs `READY_FOR_MANUAL_SEND`; it does not call platform messaging APIs.
- Email syntax validation is not mailbox verification.
- Public source URLs and verification labels are required before email simulation.
- Missing metrics, contact details and recent-post signals are not fabricated.
