# Assignment requirement traceability

| Assignment requirement | Implementation / evidence | Result |
|---|---|---|
| Discover at least 50 creators | `data/influencers.csv`: 97 directory-sourced records across Instagram and YouTube, with profile and source URLs | Met numerically; third-party directory snapshots, not live API verification |
| Define micro-influencer range | Default 5,000–100,000 follower range in `src/pipeline.py` and sidebar controls in `app.py` | Met |
| Implement one complete filtering category | Technology & Coding Education rule; explicit keyword relevance + follower range + source-reported engagement rate + metrics source URL | Implemented; 7 PASS, 48 PENDING, 42 FAIL in current snapshot |
| Explain pass/fail reasons | `computed_reason` and synchronized `decision_reason` in evaluated and raw CSV exports | Met |
| Enrich shortlisted creator profile | 7 PASS records contain name, platform, profile URL, follower count, engagement %, category, content themes and contact email or explicit `Not Found` | Met for current PASS shortlist; audience demographics not available consistently |
| Email pitch per qualified creator | `data/personalized_messages.csv`; generated only for PASS records; 60–90 body words | Met; 7 drafts |
| Instagram/social DM per qualified creator | Same output; 15–30 words, generated from recorded creator signals | Met; 7 drafts |
| Sending layer | `send_or_simulate()` validates qualification, email syntax, public source, verification and contact type; Discover uses the same shared email eligibility function | Met as simulation; no email delivered |
| Manual DM workflow | Social DM marked `READY_FOR_MANUAL_SEND`; no automated platform access | Met |
| Prevent duplicate outreach | SQLite unique constraint on creator key + channel | Met |
| Maintain outreach log | SQLite `outreach` table and Activity Tracker tab | Met |
| README / setup / stack / sources / limitations | `README.md`, `docs/source_methodology.md`, `docs/architecture.md` | Met |
| Error handling and tests | deterministic fallback, guarded LLM path, email validation, whole-word relevance matching, shared email eligibility, duplicate handling across both channels; 19 pytest tests | Met in automated tests |

## Important evidence limitations

- The 97 records are sourced from public directories and profile URLs; they are not 97 live platform API lookups.
- Current PASS is a rule-based, source-snapshot result, not a guarantee of current account ownership, audience demographics, authenticity, or brand fit.
- The directory's engagement calculation method is not independently audited. Average views are never substituted for engagement rate.
- `Not Found` emails are retained as such; those creators can receive a manually reviewed social DM, but cannot enter email simulation. The Discover email-only checkbox now filters using the exact eligibility rule used by the outreach workflow.
- Manager/business/organization contacts are explicitly typed and should be confirmed before real outreach. Third-party directory relay addresses are excluded from email eligibility.
- Email sending is simulated and Instagram/social sending is manual-only by design.
