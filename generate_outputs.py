from pathlib import Path
import pandas as pd
from src.pipeline import load_data, evaluate, personalized_messages

ROOT = Path(__file__).resolve().parent
scored = evaluate(load_data())
# Keep the canonical export decision fields in sync with the executable rule.
scored['decision'] = scored['computed_status']
scored['decision_reason'] = scored['computed_reason']
scored.to_csv(ROOT / 'data' / 'evaluated_dataset.csv', index=False)
base_export = scored.drop(columns=['computed_status', 'computed_reason', 'fit_score'])
base_export['decision'] = scored['computed_status']
base_export['decision_reason'] = scored['computed_reason']
base_export.to_csv(ROOT / 'data' / 'influencers.csv', index=False)

short = scored[scored['computed_status'] == 'PASS'].copy()
short.to_csv(ROOT / 'data' / 'shortlisted_creators.csv', index=False)
rows = []
for _, row in short.iterrows():
    email, dm = personalized_messages(row)
    body = email.split('\n\n', 1)[1].split('\n\nBest,', 1)[0]
    rows.append({
        'influencer_name': row['name'],
        'platform': row['platform'],
        'profile_url': row['profile_url'],
        'email': row['contact_email'],
        'qualification_status': row['computed_status'],
        'qualification_reason': row['computed_reason'],
        'email_pitch': email,
        'email_word_count': len(body.split()),
        'instagram_dm': dm,
        'dm_word_count': len(dm.split()),
        'draft_status': 'DRAFT - HUMAN REVIEW REQUIRED',
    })
pd.DataFrame(rows).to_csv(ROOT / 'data' / 'personalized_messages.csv', index=False)
pd.DataFrame(columns=[
    'influencer_name', 'channel', 'email', 'message_generated',
    'sent', 'date', 'status', 'mode', 'source_url'
]).to_csv(ROOT / 'data' / 'outreach_tracker.csv', index=False)
print(
    f"Discovered: {len(scored)} | In follower range: {int(scored.followers.between(5000, 100000).sum())} "
    f"| Qualified: {len(short)} | Pending review: {int((scored.computed_status == 'PENDING').sum())} "
    f"| Failed: {int((scored.computed_status == 'FAIL').sum())}"
)
