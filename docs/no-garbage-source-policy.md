# No-Garbage Source Policy

## 1. Purpose

StatuteProof source counts must mean compliance expertise, not URL padding. This policy defines what can enter a UAE default source pack and what must be rejected, blocked, or kept in remediation.

## 2. Allowed Source Criteria

A source is allowed as a candidate only if all of these are true:

1. It is official or officially linked.
2. It is public and permitted to monitor.
3. It is relevant to UAE regulatory, AML, sanctions, tax, data protection, financial services, virtual assets, or compliance operations.
4. It has meaningful content or a meaningful listing.
5. It is not just a homepage/nav shell when a better subpage exists.
6. It is not a duplicate of another source without a distinct monitoring purpose.
7. It has a stable URL or a documented reason if dynamic.
8. It can receive a clear readiness status: `candidate`, `no_save_tested`, `readiness_supported`, `remediation`, `blocked`, or `rejected`.
9. It has a clear owner/regulator/category.
10. It has a customer-facing reason an MLRO, CCO, compliance manager, legal counsel, VASP, fintech, payment firm, or consultant would care.

## 3. Rejected Source Types

Reject:

- marketing pages with no regulatory/compliance content;
- generic homepages when specific regulatory subpages are available;
- social media;
- blogs/news commentary;
- law firm articles;
- scraped search result pages;
- private portals;
- paywalls;
- login/CAPTCHA pages;
- generic PDFs with no compliance relevance;
- empty pages;
- pages returning 404 shells;
- duplicated content/hash without a distinct source role;
- pages that create legal/access risk;
- non-UAE regulators unless explicitly scoped for a cross-border product;
- Saudi CMA when the intended source is UAE SCA.

## 4. Status Rules

| Status | When to use |
|---|---|
| `candidate` | Official/relevant but not yet Source Lab tested. |
| `no_save_tested` | Tested without evidence write; preview only. |
| `readiness_supported` | No-save test produced meaningful non-nav-shell content with acceptable quality and unique hash. |
| `remediation` | Useful but parser/selector/source model needs work. |
| `blocked` | Login, CAPTCHA, paywall, private portal, access restriction, legal risk, or repeated blocking. |
| `rejected` | Wrong source, wrong country, duplicate, irrelevant, commentary, or garbage. |

Do not use `validated` as a customer-facing source status.

## 5. Readiness Boundaries

- No-save test means preview only.
- One successful no-save extraction does not mean monitoring-ready.
- Evidence confirmed requires saved proof artifacts.
- Monitoring-ready requires baseline/activation-readiness checks.
- A source can be officially important and still remain remediation.
- DFSA remains remediation until strict selector/source-model checks pass.

## 6. Customer-Facing Copy Rules

Allowed:

- “13 enabled UAE sources; 9 readiness-supported; 4 under extraction remediation.”
- “UAE source expansion in progress.”
- “Default source pack under validation.”
- “Source Lab can test public official sources and explain readiness.”
- “Monitoring intelligence only. Not legal advice.”
- “X candidate official-source endpoints mapped.”
- “Y no-save tests passed readiness checks.”

Forbidden:

- “60 validated sources”
- “comprehensive UAE monitor”
- “perfect parsing”
- “any website can be parsed”
- “never miss updates”
- “legal advice”
- “guaranteed compliance”
- “official regulator certified”
- “official regulator partner”

## 7. Registry Change Rules

Do not add a source to active `sources.json` unless:

- candidate discovery exists;
- no-save validation report exists;
- the URL is stable and reachable;
- extraction is meaningful;
- source is not nav-shell;
- hash is unique for its content role;
- quality is acceptable;
- source status is conservative;
- source does not imply evidence-confirmed or monitoring-ready without proof/baseline.

Untested sources belong in `product/regradar/config/uae_source_candidates.json`, not active monitoring.
