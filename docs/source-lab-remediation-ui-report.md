# Source Lab Remediation UI Report

Date: 2026-06-15

## Summary

Source Lab UI now surfaces more remediation data and safe retry controls.

## Added UI Fields

The result panel can show:

- DOM investigation result;
- recommended adapter;
- content selector;
- selector confidence;
- failure code;
- noise risk;
- source-health risk;
- existing evidence/activation/baseline fields.

## Added Controls

Added safe controls:

- `Retry with JS`
- `Try listing adapter`
- `Try PDF listing`
- `Mark remediation` disabled roadmap action
- `Save baseline` disabled roadmap action

The active retry buttons only update extraction settings and ask the user to rerun a no-save test. They do not save evidence, activate monitoring, or send delivery.

## Legal / QA Notes

- No claim of evidence is shown unless backend returns evidence fields.
- Monitoring activation remains locked.
- Saved baseline is disabled until an evidence-save workflow is available and gated.
- No customer-facing 50/60 source claim was added.
