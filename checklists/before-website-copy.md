# Checklist: Before Website Copy

Complete all items before publishing any StatuteProof landing page or dashboard update.

## Mock Data

- [ ] Every data point displayed on the landing page is identified as REAL or MOCK
- [ ] If any data is MOCK: it is labeled SAMPLE / FAKE on the page or component
- [ ] sourceHealthRows in mockData.js is not displayed without SAMPLE / FAKE label
- [ ] riskTrendData is not displayed as real monitoring history without label
- [ ] Last-checked timestamps are real run timestamps from source_runs.jsonl, or labeled

## Landing Page Copy

- [ ] Hero headline states a specific capability (not a promise)
- [ ] Sub-headline explains what the product does (not what it promises)
- [ ] No forbidden phrases in any headline, subheading, CTA, or badge
- [ ] Proof section elements (hashes, timestamps, diff excerpts) are labeled SAMPLE / FAKE if fabricated
- [ ] Source list contains only sources enabled in sources.json with real run records
- [ ] Pricing/pilot descriptions do not contain compliance guarantee language

## Disclaimer

- [ ] Full standard disclaimer is present on the page (or linked from a clearly visible link)
- [ ] Short disclaimer is present on the pricing section or within CTAs if the full version is not inline
- [ ] Disclaimer is visible without excessive scrolling for a new visitor

## Legal Safety

- [ ] Legal Language Agent reviewed all new copy additions
- [ ] No claim of regulator affiliation, endorsement, or certification
- [ ] No guarantee of compliance or regulatory coverage
- [ ] No "AI lawyer" or legal services positioning
- [ ] No "100% accurate", "never miss", or "always up to date" language

## Dashboard (Before Demo)

- [ ] Source health matrix is connected to live GET /api/sources/health, OR
- [ ] All dashboard data is labeled SAMPLE / FAKE on the UI component
- [ ] No customer will see fabricated source health status presented as real monitoring activity

## Review Complete

- [ ] `#ui-ux-review` score >= 45/60
- [ ] Legal Language Agent PASS
- [ ] Decision: DEMO-READY or REVISE (never demo on BLOCK)
