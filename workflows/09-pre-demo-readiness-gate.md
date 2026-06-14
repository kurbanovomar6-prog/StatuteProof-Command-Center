# Workflow 09: Pre-Demo Readiness Gate

Purpose: confirm StatuteProof can be shown safely in an internal or prospect demo without overclaiming source readiness, evidence, billing, or legal/compliance impact.

## Required Agents

- Product Manager: confirms the demo story solves an MLRO/compliance-team problem.
- Source Monitor: verifies source readiness counts and remediation labels.
- Evidence Trail: checks proof-backed artifacts and sample/demo boundaries.
- QA / Critic: checks routes, broken buttons, sample labels, and obvious UX issues.
- Legal Language: reviews claims, disclaimers, and regulated-market wording.
- Webapp Testing: verifies critical browser flows when possible.

## Gate Checklist

1. Worktree is clean or only demo-gate changes are staged.
2. Website does not say “13 validated sources,” “certified monitoring,” “any website,” “guaranteed compliance,” or “perfect parsing.”
3. Source readiness story matches the current canonical truth.
4. DFSA remains remediation unless live no-save and saved-baseline evidence prove otherwise.
5. Any sample brief is labeled `SAMPLE / FAKE DEMO`.
6. Evidence claims reference proof/hash/artifact paths.
7. Billing states manual activation after source readiness review.
8. Login/register/protected-route behavior is smoke-tested or limitation is documented.
9. No customer delivery, Telegram, email, or broad monitoring has run.
10. Validation commands pass or failures are documented as blockers.

## Output

Create or update a pre-demo report with:

- pass/fail per gate
- demo-safe pages
- pages/features to avoid
- exact claims allowed
- exact claims forbidden
- next required fix
