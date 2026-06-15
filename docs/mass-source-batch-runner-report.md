# Mass Source Batch Runner Report

Date: 2026-06-15

## Verdict

Safe batch runner implemented.

## Files Added / Updated

- Added `product/regradar/app/mass_source_activation_runner.py`.
- Updated `product/regradar/run.py` with `mass-source-activate` CLI.
- Updated `tools/validate_mass_source_activation_pipeline.py` to require runner safety markers.
- Added `product/regradar/tests/test_mass_source_activation_runner.py`.

## Runner Behavior

Command:

`python3 run.py mass-source-activate --queue product/regradar/config/mass_source_activation_queue.json --no-save-only --limit 10 --regulator SCA`

Supported modes:

- `--discover-only`
- `--no-save-only` default
- `--save-passing` explicit only
- `--repeat-baseline N` accepted as explicit request marker; repeat baseline is not run without evidence support

Safety behavior:

- No `sources.json` update.
- No customer delivery.
- No Telegram/email.
- No all-source monitor.
- Default mode uses `write_evidence=False`.
- Queue entries are re-evaluated by `evaluate_activation()`.
- Activation-ready remains impossible without proof, repeat baseline, and gates.

## Tests Added

- Runner default does not save evidence.
- Runner updates candidate/remediation statuses.
- Runner respects regulator/source_id/limit.
- Runner refuses save when no-save fails.
- Runner does not modify `sources.json`.

## Known Limits

- Runner does not yet implement real repeat-baseline automation.
- Save mode is explicit and should only be used after strong no-save results.
- Source-specific adapters still determine whether candidates can actually progress.
