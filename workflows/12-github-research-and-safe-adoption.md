# Workflow 12: GitHub Research And Safe Adoption

Purpose: use open-source research to improve StatuteProof without blindly copying code, adding risky dependencies, or vendoring third-party repositories into runtime.

## Required Agents

- Code Architect: evaluates architecture fit and dependency risk.
- Source Monitor: checks parser/source monitoring relevance.
- Evidence Trail: checks evidence/proof impact.
- QA / Critic: checks maintainability and regression risk.
- Legal Language: checks license/attribution and customer-facing claims.
- Security reviewer function: checks supply chain and sensitive-data implications.

## Research Rules

1. Prefer reading docs and repo structure before code.
2. Use shallow local clones only in ignored reference folders when needed.
3. Do not run third-party install scripts.
4. Do not vendor repositories into product runtime.
5. Do not copy code without license review and attribution.
6. Prefer adapting ideas independently.
7. Reject heavy dependencies unless they solve a proven P0/P1 problem.
8. Document adoption status: adopt now, adopt later, research only, or reject.

## Evaluation Fields

For each repo/tool:

- URL
- purpose
- maturity
- license visibility
- useful idea
- dependency risk
- security risk
- adoption decision
- what not to copy

## Output

Update a research report with:

- sources reviewed
- top ideas
- adopt now/later/reject
- license and safety notes
- exact future implementation prompt
