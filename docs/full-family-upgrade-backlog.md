# Full UAE Source Family Upgrade Backlog

Date: 2026-06-21

## Ordered Backlog

| Priority | Family | Target for this sprint | Likely improvement type | Risk | First check | Stop condition |
| ---: | --- | --- | --- | --- | --- | --- |
| 1 | ADGM/FSRA | 6.0 -> 6.8 if honest | Canonical evidence + exact alert links for fresh-alert sources | Medium | Dry-run `AE-adgm-fsra-financial-crime-prevention` and `AE-adgm-fsra-rulebooks` | Stop before activating candidates without proof/baseline. |
| 2 | DIFC | 6.0 -> 6.5 if honest | Canonical evidence + exact alert link | Medium | Dry-run `AE-difc-data-protection-regulation-10` | Stop before claiming complete DIFC legal database coverage. |
| 3 | SCA | 5.2 -> 5.8 if honest | Canonical evidence + exact alert link; keep parser warning | High | Dry-run `AE-sca-circulars-rules-procedures` | Stop before treating AML/CFT large diff as material without parser review. |
| 4 | DFSA | 6.9 -> 7.2 if honest | More evidence-linked alerts | Low/medium | Dry-run consultation and enforcement alerts | Stop before claiming complete DFSA coverage. |
| 5 | UAE FIU | Hold 6.3 unless review/new endpoint | Human review readiness, blocker clarity | Medium | Check existing typology/system-guide evidence | Stop if no distinct FIU circular endpoint exists. |
| 6 | MoF | Hold 4.0 unless new proof appears | Evidence review or official listing proof | Medium | Check existing MoF canonical records and alert queue | Stop if only evidence-library homepage alert is available. |
| 7 | MoJ/Gazette | Hold 1.0 unless safe endpoint appears | Blocker dossier | High | Check for safe public official mirror/feed/API | Stop on WAF/access-control/private portal. |

## Score Rule Reminder

No source count increase is allowed without official public source proof,
meaningful extraction, hashes, repeat baseline, and validators. No family score
increase is allowed for documentation-only changes.

