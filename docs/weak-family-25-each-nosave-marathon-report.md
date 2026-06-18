# Weak-Family 25-Each No-Save Marathon Report

Date: 2026-06-18

## Summary

This sprint ran a focused no-save marathon for FTA and exploratory no-save probes for SCA. It did not broad-crawl, bypass private access, or write no-save-only rows to `sources.json`.

| Family | No-save tested | Strong no-save passes | Held / failed | Notes |
| --- | ---: | ---: | ---: | --- |
| FTA / Tax | 27 | 25 | 2 | 25 official PDFs passed. Two FTA PDFs were held for weak/problematic extraction. |
| SCA | 3 detail endpoints probed manually | 1 candidate pass | 2+ held | SCA document/download handling needs a source-specific adapter before a broad batch. |
| Other target families | 0 in this commit | 0 | Not run | Left for next targeted adapter batches; no source count inflation. |

Detailed machine-readable FTA no-save results:

- `docs/weak-family-25-each-nosave-results.json`

## Held FTA PDFs

Held examples included:

- A Maskan supplier portal manual with quality below the activation threshold.
- A large corporate tax registration/resubmission user manual that returned `PDF_EXTRACTION_NEEDED`.

These were not activated.

## SCA Probe Result

SCA’s VASP guideline endpoint can be parsed as a PDF candidate, but several `/assets/download/...` endpoints behave as downloads or Office/zip-like files. SCA needs a dedicated document/download adapter before mass activation.

## Verdict

FTA passed the no-save threshold for a 25-source activation batch. Other weak families remain below 25 because this sprint did not yet provide enough proof-backed, repeat-baseline-tested active endpoints.
