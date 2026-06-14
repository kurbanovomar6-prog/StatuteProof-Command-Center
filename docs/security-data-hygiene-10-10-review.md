# Security and Data Hygiene 10/10 Review

## 1. Scope

Reviewed:

- `.gitignore`
- tracked runtime data paths
- tracked source/docs for secret-like patterns
- parser URL safety posture from existing reports
- generated data handling
- frontend/API exposure risk at a high level

No `.env` file was printed or read for values.

## 2. Secret Scan Result

Status: PASS AFTER SAFE FIX

Two scans were run:

1. A broad string scan for environment variable names and sensitive words.
2. A stricter regex scan for key-shaped values such as Stripe keys, OpenAI keys, Anthropic keys, Telegram tokens, and private key blocks.

The broad scan found many safe references to environment variable names in code, docs, examples, and validators. These are expected and not secrets by themselves.

The stricter scan initially found one OpenAI-style key-shaped test placeholder in `product/Makefile` line 24. The value was not printed. It was replaced with `anthropic-test-placeholder`, and the strict scan then passed.

## 3. Runtime Data Review

`.gitignore` already ignores:

- `.env` and `.env.*`
- `.reference_parser_repos/`
- `product/regradar/data/source_runs/*.jsonl`
- `product/regradar/data/source_snapshots/`
- `product/regradar/data/alert_queue/*.json`
- `product/regradar/data/alert_reviews/`
- `product/regradar/data/diagnostics/`

Important limitation:

Some historical `product/regradar/data/alert_queue/*.json` files are already tracked in git. This pass did not untrack or delete them because that is a separate repository hygiene decision and could affect project history or demos. They should be reviewed in a dedicated cleanup task.

## 4. Security Strengths

- Custom source intake has explicit public-source safety posture in current docs and validators.
- Private/protected/login/CAPTCHA/paywall sources are treated as blocked or remediation in parser policy.
- Reference repositories are ignored and not vendored into runtime.
- Product claim validators scan for high-risk overclaim phrases.
- No live deployment, Cloudflare, DigitalOcean, customer messaging, or broad monitoring was touched.

## 5. Remaining Risks

| Risk | Severity | Recommendation |
|---|---:|---|
| Historical tracked alert queue JSON | P1 | Dedicated cleanup: inspect, redact if needed, then untrack with owner approval |
| Many docs contain env var names | P2 | Acceptable if no values; keep strict regex scan in review workflow |
| Browser auth smoke not yet automated | P1 | Add committed smoke test script after local server behavior is stable |
| Existing product tree has legacy modules outside `product/regradar` | P2 | Keep future security scans scoped but include tracked files |
| Runtime evidence data may contain sensitive customer data in future | P1 | Define retention/redaction policy before real customers |

## 6. Safe Fix Made

- Replaced a secret-shaped Anthropic test placeholder in `product/Makefile` with `anthropic-test-placeholder`.

## 7. Next Exact Task

Run a dedicated tracked-runtime-data cleanup for `product/regradar/data/alert_queue/*.json`, including owner confirmation on whether to untrack historical generated alert records.
