# Mega Audit Research Notes

Date: 2026-06-14

Web access was available. This was a focused check only; no repositories were cloned and no new dependencies were added.

## Sources Checked

| Source | Useful Finding | Mapping To StatuteProof |
| --- | --- | --- |
| NIST Cybersecurity Framework page | NIST frames cybersecurity work around risk management, profiles, mappings, and quick-start guides for specific goals. | StatuteProof should keep source monitoring tied to explicit risk/governance profiles: source scope, evidence requirements, review gates, and limitations. |
| "Change Detection and Notification of Webpages: A Survey" | Webpages are dynamic and change often; change detection systems exist because tracking valuable web changes manually is challenging. The survey classifies techniques and challenges. | StatuteProof should treat source monitoring as a change-detection system with known uncertainty, false positives, dynamic pages, and selector/quality issues, not as perfect regulatory coverage. |
| `dgtlmoon/changedetection.io` GitHub repository | Mature change-monitoring products use targeted selectors, visual selector tooling, Playwright/browser fetchers, filters, PDF monitoring, checksums, screenshots, schedules, and notifications. | StatuteProof already has selectors, Playwright, PDF text, hashing, and notifications; next upgrades should be rendered evidence/screenshot capture, per-source selectors, source schedules, and stronger filters before customer delivery. |

## Practical Takeaways

1. Source-specific selectors are a core product capability, not an advanced edge case.
2. Browser rendering should be paired with rendered DOM/screenshot evidence for hard JS pages.
3. Filters and exclusions matter because navigation, counters, and dynamic shells can create noisy diffs.
4. Scheduling should eventually be per-source and risk-aware, not one global interval.
5. PDF monitoring needs both text extraction and checksums/metadata; shallow or image PDFs should be labeled OCR-needed.
6. Notification/delivery must stay downstream of evidence and human review.
7. "Official-source monitoring" should be described as risk management support with visible limitations, not guaranteed capture.

## StatuteProof-Specific Recommendations

| Recommendation | Priority | Reason |
| --- | --- | --- |
| Add rendered HTML/screenshot evidence for Playwright sources. | P1 | DFSA-class sources need proof of what the browser actually rendered. |
| Add source-specific selector/adaptor registry fields. | P1 | Hard regulatory sources rarely work with generic `main` forever. |
| Add ignore/filter rules for counters, menus, and known noisy blocks. | P1 | CBUAE counter changes and nav shells can cause false-positive or false-ready states. |
| Add source-level schedules after pilot. | P2 | High-value sources can be checked more frequently than static legal databases. |
| Add checksum/metadata records for PDFs. | P2 | PDF text alone is not enough for robust evidence. |
| Add a demo-safe notification policy. | P0 | Mature change systems can notify many channels, but StatuteProof must require human review and no accidental customer sends. |

## What Not To Copy Blindly

- Do not add broad browser-step automation for login/private pages. StatuteProof should not bypass login, CAPTCHA, paywalls, or private portals.
- Do not adopt AI change summarization as the source of truth for whether content changed.
- Do not add proxy/anti-bot services until there is a legal and source-policy review.
- Do not add large dependencies until a specific source class proves the need.

## Links

- NIST Cybersecurity Framework: https://www.nist.gov/cyberframework
- Change Detection and Notification of Webpages: A Survey: https://arxiv.org/abs/1901.02660
- changedetection.io GitHub repository: https://github.com/dgtlmoon/changedetection.io
