# Source and research methodology

## Campaign scope

The completed qualification category is **Technology & Coding Education**. The discovery pool retains profiles from multiple niches because the assignment asks for at least 50 discovered creators; unrelated creators are not silently treated as campaign-qualified. The rule qualifies only profiles with explicit technology/software/coding signals and source-reported engagement data.

## Sources

- The Influencer Sync, Indian micro tech and gaming listing: https://theinfluencersync.com/influencer-list/list-of-micro-tech-and-gaming-influencers-with-over-10k-followers-upto-99k
- The Influencer Sync category pages for business/finance, sports/fitness and food (discovery pool only; not automatic campaign fit).
- InfluencerUnion individual creator/channel pages and Indian category listings.
- Feedspot Indian education creator listing for the original discovery records.
- Socialveins directory listing for the three identified directory-contact routes.

## Evidence policy

Each record stores a source URL and source-check date where available. Directory-reported followers, engagement and average views are snapshots, not official platform API results. Average views are never converted into engagement rate. Engagement rates are stored only when the source explicitly displays a percentage. Emails are stored only when visible in a public source; unavailable values remain `Not Found`. Masked email addresses are never reconstructed. `contact_type` distinguishes creator, manager, business, organization, channel, professional and third-party directory routes.

## Qualification

- FAIL: follower count outside the selected 5K–100K interval.
- PENDING: follower range fits, but a Technology & Coding Education content signal or source-reported engagement rate/source URL is missing.
- PASS: follower range fits, explicit technology/coding relevance is found in the recorded category/content themes, and an engagement percentage plus its source URL are present.

The rule is deterministic and inspectable in `src/pipeline.py`. The current evaluated output contains 7 PASS, 48 PENDING and 42 FAIL from 97 records. PASS means the evidence meets this prototype's rule; it does not mean live profile ownership, demographics, audience quality, deliverability or brand suitability have been independently verified.

## Contact and sending safety

A valid email is not necessarily a deliverable or appropriate email. Email simulation requires a syntactically valid address, public source URL, an approved verification label, and a non-intermediary contact type. Manager addresses are visibly labeled as manager routes. No email is actually sent. Social messages are manual-ready only; the system does not automate Instagram DMs.

## Limitations

- No official Instagram/YouTube API integration or live profile revalidation.
- Audience age, gender and geography are not available consistently and are not fabricated.
- Some source pages may have been indexed or measured months before the research snapshot.
- Directory engagement methodology is not independently audited.
- Human review is required before any external contact.
