# START HERE

## This workspace is for StatuteProof only.

---

## Sequence

1. Open this folder for StatuteProof work only.

2. Read `STATUTEPROOF_CONTEXT.md` to understand what StatuteProof is and is not.

3. Start with `workflows/02-first-source-spec.md`.
   Define the first real UAE source spec for VARA, CBUAE, or DFSA.

4. Then run `workflows/03-evidence-dry-run.md`.
   Execute a real pipeline run against the source. Verify FAILED ≠ UNCHANGED. Verify the evidence record saves correctly.

5. Then create one SAMPLE / FAKE brief.
   Use `prompts/sample-brief-prompt.md` and `workflows/04-monitoring-to-brief.md`.
   Label it SAMPLE / FAKE. Run it through `skills/risk-brief-review/` before sharing.

6. Do not improve this workspace endlessly.
   If the folder exists but no evidence record exists, the workspace is not working yet.

7. Do not build or update the dashboard before the evidence dry run is complete.
   Mock data on a live product page is a legal and trust risk.

8. Do not automate with n8n, Zapier, or any external pipeline before you have done it manually at least once.
   Manual proof comes before automation.

---

## What to do when you are stuck

| Stuck on | Go to |
|----------|-------|
| Source URL is not accessible | `docs/source-monitor-spec-guide.md` → fallback handling |
| Evidence record not saving | `docs/evidence-record-spec.md` → required fields |
| Brief wording feels risky | `docs/forbidden-phrases-reference.md` |
| Score assigned without evidence | Stop. Evidence first. See `workflows/03-evidence-dry-run.md` |
| Customer-facing copy | `docs/legal-safety-system.md` + Legal Language Agent |
| Outreach message | `skills/anti-slop-writing-review/SKILL.md` + `skills/marketing-outreach-review/SKILL.md` |

---

## What not to do

- Do not create an 11th StatuteProof agent.
- Do not copy this folder into AI-Company-Agent-OS or any other workspace.
- Do not add Polymarket, Excel, or YouTube tools here.
- Do not push any file containing `.env` values to GitHub.
- Do not deliver a brief to a customer without human review.
