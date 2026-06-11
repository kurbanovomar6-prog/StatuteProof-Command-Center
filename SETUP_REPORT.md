# StatuteProof Command Center — Setup Report

**Setup date:** 2026-06-11
**Setup by:** Claude Code (claude-sonnet-4-6)
**Workspace path:** `/Users/kurbnovomar/StatuteProof-Command-Center`
**Status:** COMPLETE — Validation PASSED

---

## Folder Created

`/Users/kurbnovomar/StatuteProof-Command-Center` — created fresh (no prior folder existed).
No backup required.

---

## Reference Repos Inspected

Cloned into `.reference_tmp/` (excluded from git):

| Repo | What Was Inspected | License |
|------|--------------------|---------|
| `coreyhaines31/marketingskills` | CLAUDE.md, skills/cold-email, skills/copywriting, skills/customer-research | MIT |
| `hardikpandya/stop-slop` | SKILL.md, references/phrases.md, references/structures.md | MIT |
| `nextlevelbuilder/ui-ux-pro-max-skill` | CLAUDE.md, README.md, skill structure | MIT |
| `kurbanovomar6-prog/AI-Company-Agent-OS` | All agents, skills, docs, examples | Proprietary (same owner) |

---

## What Was Imported

### From AI-Company-Agent-OS

| Source | Destination | Notes |
|--------|-------------|-------|
| `.claude/agents/chief-of-staff.md` | `.claude/agents/chief-of-staff.md` | Imported as-is |
| `.claude/agents/code-architect-dev.md` | `.claude/agents/code-architect-dev.md` | Imported as-is |
| `.claude/agents/evidence-trail.md` | `.claude/agents/evidence-trail.md` | Imported as-is |
| `.claude/agents/icp-lead-research.md` | `.claude/agents/icp-lead-research.md` | Imported as-is |
| `.claude/agents/legal-language.md` | `.claude/agents/legal-language.md` | Imported as-is |
| `.claude/agents/outreach-writer.md` | `.claude/agents/outreach-writer.md` | Imported as-is |
| `.claude/agents/product-manager.md` | `.claude/agents/product-manager.md` | Imported as-is |
| `.claude/agents/qa-critic.md` | `.claude/agents/qa-critic.md` | Imported as-is |
| `.claude/agents/risk-brief-pipeline.md` | `.claude/agents/risk-brief-pipeline.md` | Imported as-is |
| `.claude/agents/source-monitor.md` | `.claude/agents/source-monitor.md` | Imported as-is |
| `.claude/skills/evidence-audit/SKILL.md` | `.claude/skills/evidence-audit/SKILL.md` | Imported as-is |
| `.claude/skills/risk-brief-review/SKILL.md` | `.claude/skills/risk-brief-review/SKILL.md` | Imported as-is |
| `.claude/skills/weekly-founder-plan/SKILL.md` | `.claude/skills/weekly-founder-plan/SKILL.md` | Imported as-is |
| `agents/06-source-monitor/system-prompt.md` | `agents/source-monitor.md` | Renamed, imported as-is |
| `agents/07-evidence-trail/system-prompt.md` | `agents/evidence-trail.md` | Renamed, imported as-is |
| `agents/08-risk-brief-pipeline/system-prompt.md` | `agents/risk-brief-pipeline.md` | Renamed, imported as-is |
| `agents/05-legal-language/system-prompt.md` | `agents/legal-language.md` | Renamed, imported as-is |
| `agents/04-qa-critic/system-prompt.md` | `agents/qa-critic.md` | Renamed, imported as-is |
| `agents/02-product-manager/system-prompt.md` | `agents/product-manager.md` | Renamed, imported as-is |
| `agents/03-code-architect-dev/system-prompt.md` | `agents/code-architect-dev.md` | Renamed, imported as-is |
| `agents/09-icp-lead-research/system-prompt.md` | `agents/icp-lead-research.md` | Renamed, imported as-is |
| `agents/10-outreach-writer/system-prompt.md` | `agents/outreach-writer.md` | Renamed, imported as-is |
| `docs/source-monitor-spec-guide.md` | `docs/source-monitor-spec-guide.md` | Imported as-is |
| `docs/evidence-record-spec.md` | `docs/evidence-record-spec.md` | Imported as-is |
| `docs/risk-scoring-guide.md` | `docs/risk-scoring-guide.md` | Imported as-is |
| `docs/legal-safety-system.md` | `docs/legal-safety-system.md` | Imported as-is |
| `docs/forbidden-phrases-reference.md` | `docs/forbidden-phrases-reference.md` | Imported; 21 duplicate "V3 completeness note" lines removed |
| `docs/statuteproof-mvp-plan.md` | `docs/statuteproof-mvp-plan.md` | Imported as-is |
| `docs/outreach-strategy.md` | `docs/outreach-strategy.md` | Imported as-is |
| `docs/github-workflow.md` | `docs/github-workflow.md` | Imported as-is |
| `examples/sample-compliance-brief.md` | `examples/sample-compliance-brief.md` | Imported as-is |
| `examples/sample-evidence-record.json` | `examples/sample-evidence-record.json` | Imported as-is |
| `examples/sample-source-spec.md` | `examples/sample-source-spec.md` | Imported as-is |
| `examples/sample-outreach-messages.md` | `examples/sample-outreach-messages.md` | Imported as-is |

---

## What Was Not Imported

| Item | Reason |
|------|--------|
| `.reference_extracts/`, `.reference_review_extracts/`, `.reference_v2_extracts/`, `.reference_v3_extracts/` | Third-party content, not StatuteProof property |
| `planning-reports/` | Local planning artifacts, transient |
| `evals/` | Evaluation rubrics not needed in Command Center |
| `schemas/` | JSON schemas live in regradar codebase |
| `dist/` | Build artifacts |
| `AGENT_SCORECARDS.md`, `AGENT_ROUTER.md`, `AGENT_RULES.md`, `AGENT_CATALOG.md` | Covered by this workspace's AGENTS.md and TOOL_ROUTER.md |
| `COMPANY_CONTEXT.md` | Replaced by STATUTEPROOF_CONTEXT.md (more focused) |
| `ERRORS_TO_AVOID.md` | Covered by checklists in this workspace |
| `STATUTEPROOF_PROJECT_AUDIT.md` | One-time audit report, not an operating doc |
| `workflows/` from AI-Company-Agent-OS | Replaced with new StatuteProof-specific workflows |
| `checklists/` from AI-Company-Agent-OS | Replaced with new checklists in this workspace |
| Node.js tools, Composio integrations | Not relevant to StatuteProof |
| Full repo copies of marketingskills, stop-slop, ui-ux-pro-max-skill | Only patterns extracted, not full repos |

---

## Third-Party Inspiration Notes

### marketingskills → skills/marketing-outreach-review/SKILL.md

Extracted:
- YAML frontmatter skill format
- Cold-email principle: lead with the lead's world, not the product
- Customer-research extraction framework (pains, triggers, desired outcomes)
- The "check for product-marketing-context.md before asking" pattern → adapted to STATUTEPROOF_CONTEXT.md

### stop-slop → skills/anti-slop-writing-review/SKILL.md

Extracted:
- 12 Quick Check rules (adverbs, passive voice, throat-clearing, binary contrasts)
- Scoring table (Directness, Rhythm, Trust, Authenticity, Density — each 1-10)
- 35/50 pass threshold
- Banned phrase list structure (throat-clearing, emphasis crutches, structural patterns)

Adapted:
- Added StatuteProof-specific banned phrases (navigating the regulatory landscape, etc.)
- Added compliance-audience tone standard

### ui-ux-pro-max-skill → skills/ui-ux-review/SKILL.md

Extracted:
- Domain review categories: landing, product, style, ux, trust signals
- "Score each dimension separately" methodology
- Anti-pattern vocabulary: friction reduction, cognitive load, trust signals

Adapted:
- Added StatuteProof-specific dimensions (Source Transparency, Mock Data check)
- Added mock data risk severity table
- Added compliance-audience CTA guidance

---

## Validation Results

**Validator:** `tools/validate_workspace.py`
**Run date:** 2026-06-11
**Result:** PASSED — workspace is clean

Checks passed:
- All required directories exist (19 directories)
- All required root files exist (9 files)
- All required agent files exist (9 agents)
- All required skill files exist (6 skills)
- All required docs exist (9 docs)
- All required prompts exist (6 prompts)
- All required workflows exist (6 workflows)
- All required checklists exist (5 checklists)
- No secrets found
- No node_modules
- No .git folders inside references (fixed: removed .git from .reference_tmp clones)
- No forbidden claims as product claims in CLAUDE.md
- SAMPLE / FAKE labels present in examples/

Files created (excluding .reference_tmp/): **69 files**

---

## Total Files Created

| Category | Count |
|----------|-------|
| Root files (README, CLAUDE, START_HERE, etc.) | 9 |
| .gitignore | 1 |
| .claude/agents | 10 |
| .claude/skills | 3 |
| agents/ (system prompt docs) | 9 |
| skills/ (new: marketing-outreach-review, anti-slop, ui-ux-review) | 3 |
| docs/ | 9 |
| prompts/ | 6 |
| workflows/ | 6 |
| examples/ | 6 |
| checklists/ | 5 |
| tools/ | 2 |
| references/ | 1 |
| **Total** | **69** |

---

## Next 3 Actions

**Action 1: Verify first 3 official UAE source URLs**

Open in a browser and confirm each URL is accessible and shows regulatory content:
- VARA: https://www.vara.ae/
- CBUAE: https://www.centralbank.ae/
- DFSA: https://www.dfsa.ae/

These are already in `regradar/sources.json` and have real run records. Verification is to confirm they are still accessible and the content matches what is stored in recent snapshots.

**Action 2: Create first real source spec**

Follow `workflows/02-first-source-spec.md`.
Pick one specific page within VARA, CBUAE, or DFSA (not just the homepage).
For example: the VARA fee schedule page or the CBUAE circulars page.
Use `prompts/source-spec-prompt.md` and run `checklists/before-source-spec.md`.

**Action 3: Run first evidence dry run**

Follow `workflows/03-evidence-dry-run.md` for the new source spec from Action 2.
Confirm FIRST_SEEN or UNCHANGED with GOOD proof_quality.
Run the FAILED ≠ UNCHANGED invariant check.
Enable the source only after PASS.

---

---

## Phase 3 Expansion — 2026-06-11

### Additional Repos Inspected

| Repo | Author | License | Purpose |
|------|--------|---------|---------|
| [emilkowalski/skill](https://github.com/emilkowalski/skill) | Emil Kowalski | MIT | Design-read pattern, specificity-first feedback format |
| [impeccable](https://github.com/pbakaus/impeccable) | pbakaus | Apache 2.0 | Brand/product register, AI slop detection methodology |
| [taste-skill](https://github.com/leonxlnx/taste-skill) | leonxlnx | MIT | Three-dial system, trust-first preset for regulated industries |
| [ruflo](https://github.com/ruvnet/ruflo) | rUv | MIT | Sequential-challenge philosophy (inspiration only — no runtime) |

Reference notes in `references/` (8 files total, all repos documented).

### New Skills Added

| Skill | Adapted From |
|-------|-------------|
| `skills/design-taste-review/SKILL.md` | emilkowalski/skill + impeccable + taste-skill |
| `skills/landing-page-conversion-review/SKILL.md` | marketingskills CRO framework |
| `skills/agent-council-review/SKILL.md` | Ruflo sequential-challenge concept (docs only) |

### New Docs Added

| File | Purpose |
|------|---------|
| `docs/design-quality-system.md` | Two registers, trust-first dial preset, absolute ban table |
| `docs/anti-slop-writing-system.md` | Writing standards for all StatuteProof output |
| `docs/agent-council-decision-system.md` | When/how to run the agent council |

### New Prompts Added

- `prompts/agent-council-prompt.md` — 7-stage council review trigger
- `prompts/landing-page-conversion-prompt.md` — Landing page conversion review

### New Workflows, Checklists, Examples

- `workflows/07-agent-council-review.md`
- `checklists/before-agent-council-decision.md`
- `examples/sample-agent-council-decision.md` (SAMPLE/FAKE labeled)

### Updated Files

| File | What Changed |
|------|-------------|
| `CLAUDE.md` | Added skills table, Agent Council section, Ruflo Rule |
| `TOOL_ROUTER.md` | Added routing for 3 new skills + agent-council in both tables |
| `START_HERE.md` | Added step 6 (workflow 07 for high-stakes), two new "stuck on" rows |
| `tools/validate_workspace.py` | Added 3 new skill dirs, 3 new docs, 2 new prompts, 1 new workflow, 1 new checklist; added max-10-agents check; added Ruflo-runtime-in-non-reference check |

### Phase 3 Validation

```
Validation PASSED — workspace is clean.
```

23 files changed, 1580 insertions in commit `1a707b4`.

---

## Workspace Is Not Complete Until:

- [ ] At least 3 official UAE source URLs are verified by hand
- [ ] At least 1 real source spec exists using this workspace's `prompts/source-spec-prompt.md`
- [ ] At least 1 evidence dry run produces PASS
- [ ] Dashboard mock data is either connected to live API or labeled SAMPLE / FAKE
- [ ] At least 1 SAMPLE / FAKE brief has been reviewed with `#risk-brief-review`

Having this folder is not enough. The workspace is operational when evidence exists.
