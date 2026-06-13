# Live Source Verification Runbook

## Purpose

Verify one public official source at a time without running broad monitoring, customer delivery, Telegram, email, or deployment.

## Safety Rules

- Run one URL only.
- Use `--no-save` first.
- Do not bypass login, CAPTCHA, paywall, or private portals.
- Do not print `.env`.
- Do not run `all`, `watch`, customer delivery, Telegram, or email commands.
- Do not mark a source certified from a single test.

## DFSA No-Save Checks

```bash
cd /Users/kurbnovomar/StatuteProof-Command-Center/product/regradar
python run.py source-lab https://www.dfsa.ae/rules-and-standards --no-save --json --js --content-selector main --wait-for-selector main
python run.py source-lab https://www.dfsa.ae/regulation/notices-public-registers --no-save --json --js --content-selector main --wait-for-selector main
```

Record:

- readiness_status
- normalized_length
- normalized_hash
- provider_used
- nav_shell_detected
- hash_collision
- quality_score
- evidence_level
- certification_status
- normalized_preview

## DFSA Save Checks

Run only after no-save output shows meaningful content and no nav-shell/collision:

```bash
cd /Users/kurbnovomar/StatuteProof-Command-Center/product/regradar
python run.py source-lab https://www.dfsa.ae/rules-and-standards --save --json --js --content-selector main --wait-for-selector main
python run.py source-lab https://www.dfsa.ae/regulation/notices-public-registers --save --json --js --content-selector main --wait-for-selector main
```

Save mode should create at least BASIC/FULL evidence paths. It still does not create `MONITORING_CERTIFIED` unless baseline requirements are met.

## Interpreting Playwright Errors

- Browser launch failure: local runtime issue, not source certification.
- Selector timeout: `NEEDS_SELECTOR_REVIEW`; review selector or adapter.
- Empty content after selector: source is not confirmed.
- Full-page fallback must not be used to confirm selector-configured sources.

## Updating Selectors

Only update `sources.json` selectors after:

1. no-save test returns meaningful content;
2. normalized hash is unique;
3. content preview is regulatory, not header/nav/footer;
4. quality score is at least ACCEPTABLE;
5. no policy warnings appear.

## Certifying A Source

Certification requires:

- evidence run with proof path and normalized hash;
- baseline repeat run count met;
- no unresolved nav-shell/collision/access failure;
- human review where selector ambiguity exists.
