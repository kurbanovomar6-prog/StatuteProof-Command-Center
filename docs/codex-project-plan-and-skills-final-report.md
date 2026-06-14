# Codex Project Plan and Skills Final Report

## 1. Project Review Summary
StatuteProof has real product code in `product/regradar`, including source fetching, normalization, SHA-256 hashes, comparison, JSONL source runs, snapshots, proof blocks, diffs, risk scoring, AI/fallback brief generation, alert review, weekly brief rendering, auth/profile persistence, and a React frontend. The current enabled source registry shows 13 enabled UAE sources, not the previously stated 16. Historical evidence exists for more UAE source IDs, so the source pack needs reconciliation before public claims.

## 2. Current Plans
The next plan is evidence-first: verify current UAE source readiness, run one clean safe evidence dry run, generate one SAMPLE brief from proof, then update the homepage/dashboard to show real evidence and limitations instead of mock claims.

## 3. Skills Marketplace Findings
- skills.sh was useful for finding `just-scrape`, `pdf`, `ui-ux-pro-max`, `copywriting`, `webapp-testing`, and related candidates.
- skillhub.club was useful for discovering Codex-compatible skill categories such as systematic debugging, Obsidian markdown, UI/UX, file search, and skill creation.
- skillsmp.com was useful for broader marketplace context and the `code-reviewer` detail page.

No third-party skill was installed. The safest path was to adapt concepts into StatuteProof-specific Codex skills.

## 4. Skills Added
- `.agents/skills/statuteproof-project-review/SKILL.md`
- `.agents/skills/evidence-readiness-review/SKILL.md`
- `.agents/skills/source-monitoring-review/SKILL.md`
- `.agents/skills/legal-safe-copy-review/SKILL.md`
- `.agents/skills/mlro-homepage-review/SKILL.md`
- `.agents/skills/custom-source-monitoring-spec/SKILL.md`
- `.agents/skills/anti-slop-b2b-copy/SKILL.md`
- `.agents/skills/skill-marketplace-research/SKILL.md`

## 5. Skills Rejected
- just-scrape: external API key/credits and broad scrape/crawl/monitor behavior.
- browser-use: broad browser automation risk; product already uses Playwright.
- generic code-reviewer full import: useful principles but too generic.
- generic marketing/content skills: too broad and not legal-safe enough for regulated SaaS.
- lark/Feishu/office skills: not core to source monitoring.
- video/image/cloud/runtime skills: unrelated.

## 6. How Codex Should Use These Skills
Invoke explicitly when useful:
- "Use evidence-readiness-review on the current UAE source pack."
- "Use mlro-homepage-review on the landing page."
- "Use legal-safe-copy-review before publishing this CTA."
- "Use custom-source-monitoring-spec for Add Your Source."
- "Use skill-marketplace-research before adding any new skill."

## 7. Remaining Gaps
- Evidence readiness pass for the current enabled source pack.
- First current dry run report.
- Homepage proof-first upgrade.
- Registration/login production hardening.
- Custom source monitoring flow.
- Dashboard live connection to source runs/proof files.

## 8. Next 3 Actions
1. Run current 16-source evidence readiness pass.
2. Build/update proof-first homepage and source readiness CTA.
3. Implement or specify custom source monitoring flow.

## 9. Recommended Next Prompt
Use evidence-readiness-review, source-monitoring-review, legal-safe-copy-review, and QA/Critic to run a current evidence readiness pass for the UAE source pack in `product/regradar`. Do not run broad live monitoring or customer delivery. First reconcile `sources.json`: current enabled UAE source count appears to be 13, while prior planning says 16. Read `sources.json`, `data/source_runs/source_runs.jsonl`, latest snapshots, proof files, and diff files. Produce `docs/current-uae-source-evidence-readiness-report.md` with source-by-source status, latest run status, proof path, normalized hash, extraction quality, limitation notes, and whether each source can support a human-reviewed sample brief. Do not send Telegram, email, AI calls, or deploy.
