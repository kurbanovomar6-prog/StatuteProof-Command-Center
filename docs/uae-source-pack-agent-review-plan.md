# UAE Source Pack Agent Review Plan

## 1. Agents And Skills Used

This task uses the existing 10-agent roster only. No new active agent is added.

| Agent / skill | How it applies to UAE 40-60 source expansion |
|---|---|
| Product Manager | Defines what a professional UAE default pack must solve for MLROs, CCOs, compliance managers, legal counsel, VASPs, payment firms, DFSA/ADGM firms, and consultants. |
| ICP Lead Research | Prioritizes source groups by buyer relevance, not raw URL count. |
| Source Monitor | Reviews each candidate source for official status, source ID, URL role, fetch/extraction route, readiness status, and remediation reason. |
| Code Architect | Keeps candidate file schema, validators, and registry changes clean and minimal. |
| Evidence Trail | Blocks evidence/readiness claims unless proof artifacts, hashes, paths, diffs, and baseline status justify them. |
| QA / Critic | Blocks source-count inflation, duplicate URLs, wrong-country regulators, source shells, and fake-ready labels. |
| Legal Language | Blocks legal advice, guarantee, regulator certification, official partnership, and “validated source pack” overclaims. |
| `source-monitoring-review` | Used for registry/source ID, parser route, status, failure handling, nav-shell, and hash/collision concerns. |
| `evidence-readiness-review` | Used for proof/evidence boundary and activation readiness. |
| `custom-source-parser` | Used for no-save Source Lab result interpretation. |
| `custom-source-monitoring-spec` | Used for public custom-source and candidate-source boundaries. |
| `legal-safe-copy-review` | Used for candidate/status copy and public claims. |
| `verification-before-completion` | Requires fresh validation before final claims, commit, or push. |

## 2. Review Gates Before A Source Becomes Customer-Facing

Gate 1: Product relevance

- Source belongs to a UAE federal, Dubai/VARA, DIFC/DFSA, ADGM/FSRA, SCA, AML/sanctions, tax, or official legislation/compliance category.
- MLRO/compliance buyer reason is explicit.
- Source is not included just to increase count.

Gate 2: Official provenance

- URL is official or officially linked.
- Third-party hosted rulebooks are allowed only when regulator-linked or regulator-recognized.
- Wrong-country regulators are rejected.

Gate 3: Public access safety

- Public `http(s)` only.
- No credentials in URL.
- No login/CAPTCHA/paywall/private portal.
- No access-control bypass.

Gate 4: No-garbage quality

- Not a generic homepage if a better subpage exists.
- Not a pure navigation shell.
- Not duplicate content/hash without a distinct source purpose.
- Has stable source owner, type, jurisdiction, and category.

Gate 5: Source Lab no-save validation

- Test is scoped to one URL at a time.
- No save, no evidence write, no alerts, no customer delivery.
- Output records provider, extraction method, normalized length/hash, quality, nav-shell, collision, warnings, failure reason, remediation hint, and preview.

Gate 6: Evidence readiness

- No-save means preview only.
- Evidence confirmed requires saved proof artifacts and hashes.
- Monitoring-ready requires baseline/activation-readiness checks and review approval.

Gate 7: Legal-safe customer wording

- Allowed: candidate, readiness-supported, under extraction remediation, blocked, no-save tested.
- Forbidden: validated, certified, regulator certified, comprehensive, guaranteed, perfect parsing, any website, legal advice.

## 3. Candidate Status Definitions

| Status | Meaning | Customer-facing? |
|---|---|---|
| `candidate` | Official/relevant candidate, not tested yet. | Internal or “source expansion in progress” only. |
| `no_save_tested` | Tested in Source Lab without evidence write. | Only if described as preview/no-save. |
| `readiness_supported` | No-save extraction passes strict quality criteria. | Yes, but not evidence-confirmed or monitoring-ready. |
| `remediation` | Useful source, but selector/parser/source model needs work. | Yes, as remediation/pending only. |
| `blocked` | Login/CAPTCHA/paywall/private/unsafe/unavailable. | Yes, only as blocked/not included. |
| `rejected` | Not official, irrelevant, duplicate, wrong-country, garbage. | No, except internal rejection log. |

## 4. Forbidden Overclaims

- “60 validated sources”
- “40+ monitored sources” before validation and activation
- “comprehensive UAE monitor”
- “any website can be parsed”
- “guaranteed parsing”
- “perfect parsing”
- “never miss updates”
- “legal advice”
- “guarantee compliance”
- “regulator certified”
- “official regulator partner”
- “DFSA ready” unless strict DFSA criteria pass

## 5. Required Output Before Registry Change

Before any `sources.json` change, the task must produce:

1. current source inventory;
2. UAE source taxonomy;
3. candidate discovery report;
4. no-garbage policy;
5. candidate JSON file;
6. source-pack validator;
7. no-save validation report;
8. default packs by plan;
9. registry change report.

If no candidates have passed strict no-save checks, `sources.json` stays unchanged.
