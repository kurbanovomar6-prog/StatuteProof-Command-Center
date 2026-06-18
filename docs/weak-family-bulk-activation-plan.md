# Weak-Family Bulk Activation Plan

Date: 2026-06-18

## Current Truth

- 81 enabled UAE sources
- 80 monitoring-active sources
- 1 remediation source

## Goal

Test more than 25 top-250 weak-family candidates while the founder is away, then activate as many as honestly pass the full gate sequence.

## Batch Strategy

Target 60-80 no-save checks, selected from weak or commercially important families:

- FTA / Tax
- SCA
- UAE FIU
- EOCN / sanctions / TFS
- Ministry of Economy / DNFBP AML
- Ministry of Justice / UAE Legislation / Gazette
- DFM / ADX / DMCC and adjacent market-rule sources if weak-family candidates run out

## Activation Rules

A candidate may be added to `sources.json` as active only if it has:

1. public official or officially linked URL;
2. stable `source_id`;
3. meaningful no-save extraction;
4. no nav-shell, shallow, duplicate, private, login, CAPTCHA, or access-blocked issue;
5. saved proof/evidence;
6. repeat baseline completed;
7. mass-monitor dry-run `MONITOR_OK`;
8. source-health/noise risk acceptable;
9. legal-safe notes;
10. validators passing.

## Expected Outcome

Aggressive testing, conservative activation. The desired outcome is more than 25 active additions, but the source truth will not be inflated if the evidence does not support it.

## What Will Not Be Claimed

- complete UAE coverage;
- all-source coverage;
- guaranteed compliance;
- legal advice;
- perfect parsing;
- never miss updates;
- regulator certification.
