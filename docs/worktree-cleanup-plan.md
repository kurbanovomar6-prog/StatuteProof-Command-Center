# Worktree Cleanup Plan

Date: 2026-06-14

Scope: repository hygiene only. No parser implementation, DFSA live checks, deployment, infrastructure changes, or runtime monitoring.

## Current Dirty State

| File/path | Status | Category | Keep/Ignore/Delete/Ask | Reason |
|---|---:|---|---|---|
| `AGENTS.md` | Modified | parser/agent/skills routing | Keep | Adds repo-scoped Codex skill guidance; useful for parser/source/evidence tasks if strengthened with public-source and activation-readiness boundaries. |
| `TOOL_ROUTER.md` | Modified | parser/agent/skills routing | Keep | Adds Codex skill routing; useful if aligned to Source Monitor, Evidence Trail, QA, and Legal gates. |
| `docs/current-uae-source-readiness-validation-report.md` | Modified | parser/source readiness docs | Keep | Safer wording avoids overclaiming “confirmed” before readiness checks complete. |
| `.codex/agents/*.toml` | Untracked | parser/agent/skills routing | Keep after review | Exactly ten project agent configs are expected; must not add an 11th active agent. |
| `.agents/skills/source-monitoring-review/SKILL.md` | Untracked | Codex/Claude skill files | Keep after review | Directly supports source monitoring review. |
| `.agents/skills/evidence-readiness-review/SKILL.md` | Untracked | Codex/Claude skill files | Keep after review | Directly supports evidence/proof readiness checks. |
| `.agents/skills/custom-source-monitoring-spec/SKILL.md` | Untracked | Codex/Claude skill files | Keep after review | Directly supports custom-source intake planning. |
| `.agents/skills/legal-safe-copy-review/SKILL.md` | Untracked | Codex/Claude skill files | Keep after review | Directly supports customer-facing legal-safety review. |
| `.agents/skills/prompt-injection-review/SKILL.md` | Untracked | Codex/Claude skill files | Keep after review | Useful for future skill and external-content safety checks. |
| `.agents/skills/statuteproof-project-review/SKILL.md` | Untracked | Codex/Claude skill files | Keep after review | StatuteProof-specific broad audit skill. |
| `.agents/skills/systematic-debugging/SKILL.md` | Untracked | Codex/Claude skill files | Keep after review | Useful for parser/API/test failures. |
| `.agents/skills/test-driven-development/SKILL.md` | Untracked | Codex/Claude skill files | Keep after review | Useful for parser quality tests. |
| `.agents/skills/verification-before-completion/SKILL.md` | Untracked | Codex/Claude skill files | Keep after review | Required style of verification before completion claims. |
| `.agents/skills/webapp-testing/SKILL.md` | Untracked | Codex/Claude skill files | Keep after review | Useful for Source Lab and app route validation. |
| `.agents/skills/evidence-audit/SKILL.md` | Untracked | Codex/Claude skill files | Keep after review | Useful for proof/evidence completeness review. |
| `.agents/skills/anti-slop-b2b-copy/SKILL.md` | Untracked | Codex/Claude skill files | Keep after review | Useful for StatuteProof public copy safety and specificity. |
| `.agents/skills/mlro-homepage-review/SKILL.md` | Untracked | Codex/Claude skill files | Keep after review | Useful for MLRO-focused messaging review. |
| `.agents/skills/agent-browser/SKILL.md` | Untracked | Codex/Claude skill files | Ask | Useful for browser QA, but not parser-critical. |
| `.agents/skills/design/SKILL.md` | Untracked | Codex/Claude skill files | Ask | Broad design skill; keep only if safe and already useful. |
| `.agents/skills/redesign-skill/SKILL.md` | Untracked | Codex/Claude skill files | Ask | Visual-upgrade helper; not required for parser cleanup. |
| `.agents/skills/taste-skill/SKILL.md` | Untracked | Codex/Claude skill files | Ask | Large design/taste skill; commit only if reviewed and intentionally accepted. |
| `.agents/skills/ui-ux-pro-max/SKILL.md` | Untracked | Codex/Claude skill files | Ask | Large UI skill; commit only if reviewed and intentionally accepted. |
| `.agents/skills/pdf/SKILL.md` | Untracked | Codex/Claude skill files | Ask | Useful for PDF evidence work; contains safe password example text that must be documented. |
| `.agents/skills/docx/SKILL.md` | Untracked | Codex/Claude skill files | Ask | Document tool skill; not parser-critical. |
| `.agents/skills/*` remaining broad marketing/planning/research skills | Untracked | Codex/Claude skill files | Ask | Potentially useful, but broad and not required for parser/DFSA readiness. Do not commit blindly. |
| `docs/codex-skills-usage-guide.md` | Untracked | parser/agent/skills routing | Keep after review | Explains how to use repo-scoped skills. |
| `docs/codex-skills-marketplace-research.md` | Untracked | parser/agent/skills routing | Keep after review | Documents skill provenance/research. |
| `docs/codex-project-plan-and-skills-final-report.md` | Untracked | parser/agent/skills routing | Keep after review | Captures skill setup decisions. |
| `docs/codex-current-project-review.md` | Untracked | parser/source readiness docs | Keep after review | Useful audit/history if no stale unsafe claims. |
| `docs/statuteproof-project-plan-from-codex.md` | Untracked | parser/source readiness docs | Keep after review | Useful plan/history if marked as report. |
| `docs/statuteproof-independent-project-review.md` | Untracked | parser/source readiness docs | Keep after review | Useful project audit if no unsafe claims. |
| `docs/premium-website-auth-dashboard-implementation-report.md` | Untracked | visual/design report docs | Keep after review | Useful visual-upgrade history, but not part of parser task. |
| `docs/actual-hosting-location-audit.md` | Untracked | ops/hosting docs | Keep after review | Useful ops audit; secret-pattern hit appears to be safety language, but must be verified. |
| `product/regradar/data/alert_queue/*.json` | Untracked | generated runtime data | Delete and ignore | Runtime alert queue artifacts; should not be committed. |

## Intended Commit Groups

1. `.gitignore` rule for generated alert queue JSON, if missing.
2. Approved agent routing, `.codex/agents`, focused `.agents/skills`, and cleanup/skills reports.
3. Useful project readiness and audit docs after safety review.

## Non-Goals

- No parser or Source Lab implementation work.
- No DFSA live verification.
- No deployment or infrastructure change.
- No broad staging.
- No generated runtime data commit.
