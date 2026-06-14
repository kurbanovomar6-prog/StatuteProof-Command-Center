# Evidence + Repeat Baseline Automation Report

Date: 2026-06-15

## Summary

Evidence/baseline automation was improved at the contract/gate level, not as broad live automation.

## What Improved

- `can_save_evidence` now distinguishes a strict evidence-save gate from simple no-save preview success.
- Source Lab payload exposes failure code, meaningful content, noise risk, and source-health risk before any save.
- `build_source_lab_contract` continues to block monitoring activation unless certified evidence and baseline requirements pass.
- Source activation validator checks that activation-ready sources require proof paths and baseline completion.

## What Was Not Built

No broad `source-baseline --repeat` runner was added in this sprint.

Reason:

- Live no-save validation produced zero strict passes.
- Adding repeat-baseline automation before sources pass no-save would encourage weak evidence capture.

## Existing Rule Preserved

One saved run is evidence, not monitoring-ready. Repeat baseline and gates remain required before activation.

## Next Step

After SCA/DFSA/CBUAE DOM/API remediation produces strict no-save passes, add a scoped command:

`python3 run.py source-baseline <source_id_or_url> --repeat 2 --json`

It should save only approved sources and record proof paths, hashes, baseline count, and gate status.
