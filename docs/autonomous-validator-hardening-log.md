# Autonomous Validator Hardening Log

Date: 2026-06-15

## Added

- `tools/validate_batch_onboarding.py`

## What It Blocks

- Missing scoreboard file.
- Missing required target fields.
- Duplicate scoreboard source IDs.
- Active UAE sources missing activation-ready scoreboard rows.
- `activation_ready` rows without proof paths, unless explicitly marked as legacy active evidence-index debt.
- `activation_ready` rows with incomplete baseline.
- High-noise or high-source-health-risk active rows.
- Non-legacy activation-ready rows without all six gates passing.
- Scoreboard summary count drift.
- Fake `did_reach_50` with fewer than 50 activation-ready rows.
- Forbidden public claims in root public docs.

## Existing Validators Updated

- `tools/validate_uae_source_pack.py`: expected truth updated to 33/29/4.
- `tools/validate_mass_source_activation_pipeline.py`: expected truth updated to 33/29/4.
- `tools/validate_mass_monitoring_runner.py`: expected truth updated to 33/29/4.
- Adapter allowlists updated for `eocn_news_listing`.

## Remaining Validator Work

Add a dedicated duplicate-normalized-hash validator across `uae_50_activation_scoreboard.json` and `sources.json` so route aliases like FIU mutual evaluation cannot be proposed for activation when they duplicate an already active source.
