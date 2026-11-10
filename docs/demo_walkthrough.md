# Local demo walkthrough

## Install and launch

```bash
python -m venv .venv
# Windows PowerShell
.venv\\Scripts\\Activate.ps1
pip install -r requirements.txt
streamlit run app.py
```

## Suggested demo sequence

1. Open **Overview** and show total discovery records, in-range count, email routes and qualified count.
2. Open **Discover & qualify**. Filter to Technology Education / Technology and show `PASS`, `PENDING` and `FAIL` with reasons and source links.
3. Open **Outreach studio**. Select one of the seven PASS-qualified creators; review the email and DM word counts and source-backed personalization.
4. For a creator with an eligible public contact route, choose **Email simulation** and log it. The interface clearly states that no email is delivered.
5. Choose **Manual social message** to create a manual-ready DM record. No Instagram DM is sent.
6. Open **Activity tracker** and show status, timestamp, channel and duplicate protection.
7. Download the evaluated dataset and personalized messages from the interface.

## Evidence capture checklist

For a final interview/submission demo, capture screenshots locally after launching the app:

- Overview dashboard
- Discover & qualify table with PASS/PENDING/FAIL reasons
- Outreach Studio showing one email and one DM with word counts
- Activity Tracker after an email simulation and manual-ready DM

Do not create screenshots from mock data or claim a live email/DM was sent.
