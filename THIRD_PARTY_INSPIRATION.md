# Third-Party Inspiration

This workspace was informed by seven open-source reference repositories. No full repos were copied. Individual patterns were extracted and adapted.

## 1. marketingskills — coreyhaines31

**Repo:** https://github.com/coreyhaines31/marketingskills
**License:** MIT
**What was extracted:**

The skill file format and YAML frontmatter structure. Specifically:
- `name`, `description`, `metadata.trigger`, `metadata.author`, `metadata.version` fields
- The pattern of loading product context from a file before asking questions
- The "check for product-marketing-context.md before asking" pattern → adapted to "check for STATUTEPROOF_CONTEXT.md"
- The cold-email principle: "lead with their world, not yours" → adapted for StatuteProof outreach
- The customer-research extraction framework (pains, triggers, desired outcomes, language used)

**What was not taken:**
- The 51 Node.js CLI tools (not needed)
- The Composio integration layer (not needed)
- The ad/ASO/SEO/community-marketing skills (not relevant to StatuteProof)

**Attribution:** Corey Haines, MIT License.

---

## 2. stop-slop — hardikpandya

**Repo:** https://github.com/hardikpandya/stop-slop
**License:** MIT
**What was extracted:**

The anti-AI-writing pattern system for `skills/anti-slop-writing-review/SKILL.md`:
- The 12 Quick Check rules (adverbs, passive voice, inanimate verbs, throat-clearing)
- The scoring table (Directness, Rhythm, Trust, Authenticity, Density — each rated 1-10)
- The "below 35/50: revise" threshold
- The banned phrases list structure (throat-clearing openers, emphasis crutches, binary contrasts)
- The structural patterns to avoid (binary contrasts, negative listings, dramatic fragmentation, rhetorical setups)

Adapted for StatuteProof context: compliance-professional audience, evidence-backed tone requirements, short-form outreach messages.

**What was not taken:**
- The full references/ folder was not copied
- No source code copied (the repo has no executable code)

**Attribution:** Hardik Pandya (hvpandya.com), MIT License.

---

## 3. ui-ux-pro-max-skill — nextlevelbuilder

**Repo:** https://github.com/nextlevelbuilder/ui-ux-pro-max-skill
**License:** MIT
**What was extracted:**

Design review principles for `skills/ui-ux-review/SKILL.md`:
- Domain search categories: `landing`, `product`, `style`, `typography`, `color`, `ux`
- The UX best-practices and anti-patterns domain
- Landing page structure and CTA strategy concepts
- The "score each dimension separately" review methodology
- Anti-pattern vocabulary: trust signals, friction reduction, cognitive load

Adapted for StatuteProof: compliance-audience landing page, dashboard source transparency matrix, evidence trail display, mock-data risk flagging.

**What was not taken:**
- The Python search scripts (`scripts/search.py`, `scripts/core.py`) — not needed
- The CSV databases (`data/products.csv` etc.) — not relevant
- The CLI installer (`cli/`) — not needed
- The 67 UI styles data or 161 reasoning rules data files — not copied

**Attribution:** nextlevelbuilder, MIT License.

---

## 4. AI-Company-Agent-OS — kurbanovomar6-prog

**Repo:** https://github.com/kurbanovomar6-prog/AI-Company-Agent-OS
**License:** Proprietary (same owner)
**What was imported:**

Directly imported (as the authoritative source):
- `.claude/agents/` — all 10 agent system prompts (chief-of-staff through outreach-writer)
- `.claude/skills/evidence-audit/` — full skill
- `.claude/skills/risk-brief-review/` — full skill
- `.claude/skills/weekly-founder-plan/` — full skill
- `agents/` — 9 agent system prompt docs (source-monitor through outreach-writer)
- `docs/source-monitor-spec-guide.md`
- `docs/evidence-record-spec.md`
- `docs/risk-scoring-guide.md`
- `docs/legal-safety-system.md`
- `docs/forbidden-phrases-reference.md`
- `docs/statuteproof-mvp-plan.md`
- `docs/outreach-strategy.md`
- `docs/github-workflow.md`
- `examples/sample-compliance-brief.md`
- `examples/sample-evidence-record.json`
- `examples/sample-source-spec.md`
- `examples/sample-outreach-messages.md`

**What was not imported:**
- Reference extract archives (`.reference_extracts/`, etc.) — third-party content
- `planning-reports/` — local planning artifacts
- `evals/` — evaluation rubrics (not needed in Command Center)
- `schemas/` — JSON schemas (live in regradar codebase, not here)
- Chief of Staff agent was imported but not added as an active 11th StatuteProof agent

---

## 5. emilkowalski/skill — Emil Kowalski

**Repo:** https://github.com/emilkowalski/skill
**License:** No explicit license stated
**What was extracted:**

Design engineering principles for `skills/design-polish/SKILL.md`:
- The animation decision framework: 3 sequential questions (Should this animate? What is the purpose? What easing?)
- Frequency table (constant use → no animation; occasional → standard transition)
- Easing rules: ease-out for entering, ease-in for exiting, never bounce or elastic
- Before/After/Why table format for code review output
- Core philosophy: "unseen details compound" — the aggregate of invisible correctness creates interfaces people love without knowing why
- Trust as leverage: compliance professionals select tools on overall experience

Adapted for StatuteProof: added the trust-first regulated-industry constraint (no animation on evidence data updates or source health changes).

**What was not taken:**
- No source code copied (the skill is a SKILL.md only)
- The course link (animations.dev) was not included

**Attribution:** Emil Kowalski.

---

## 6. impeccable — pbakaus

**Repo:** https://github.com/pbakaus/impeccable
**License:** Apache 2.0
**What was extracted:**

Design review system for `skills/ui-ux-review/SKILL.md` and `skills/design-polish/SKILL.md`:
- Brand vs. Product register distinction (brand = landing/marketing, product = app UI/dashboard)
- The "AI slop test" concept and first-order/second-order reflex check
- Absolute ban list: gradient text, glassmorphism as default, hero-metric template, identical card grids, side-stripe borders, cream/sand/beige background, eyebrow on every section
- Color rules: OKLCH, contrast ≥ 4.5:1, no gray on colored backgrounds, no cream/warm-neutral default
- Typography rules: 65–75ch line length, display tracking ≥ -0.04em, text-wrap: balance
- The 5-dimension audit scoring system (Accessibility, Performance, Theming, Responsive, Anti-Patterns) — adapted to StatuteProof's 7-dimension system
- Layout rules: cards as lazy default, nested cards always wrong, semantic z-index scale
- Motion rules: ease-out with exponential curves, reduced-motion required, no section fade uniform reflex

**What was not taken:**
- The 23 command structure and CLI tooling (not relevant)
- The Astro/Cloudflare deployment system
- The PRODUCT.md/DESIGN.md setup flow (replaced by STATUTEPROOF_CONTEXT.md)
- The 41 deterministic detector rules (specific to impeccable's CLI tool)

**Attribution:** pbakaus, Apache 2.0 License.

---

## 7. taste-skill — leonxlnx

**Repo:** https://github.com/leonxlnx/taste-skill
**License:** MIT
**What was extracted:**

Design configuration system for `skills/ui-ux-review/SKILL.md` and `skills/design-polish/SKILL.md`:
- The three-dial system (DESIGN_VARIANCE, MOTION_INTENSITY, VISUAL_DENSITY)
- The trust-first / regulated industry preset: VARIANCE=3–4, MOTION=2–3, DENSITY=4–5
- Brief inference system: "read the room before generating" — declare a one-line design read
- Anti-default discipline: explicitly name the LLM defaults and refuse them (AI-purple gradients, centered hero over dark mesh, three equal feature cards, glassmorphism everywhere, Inter + slate-900)
- Design system selection table (when to reach for govuk-frontend vs. shadcn/ui vs. Carbon etc.)
- Quiet constraints concept: regulated industries, accessibility-critical, trust-first commerce OVERRIDE aesthetic preference

Adapted for StatuteProof: the regulated-industry preset is the fixed baseline (not adjustable), because StatuteProof always targets compliance professionals with high trust requirements.

**What was not taken:**
- Image-generation skills (brandkit, imagegen-frontend-web, etc.) — not relevant
- Full brutalist-skill, minimalist-skill, soft-skill (too narrow)
- The npx CLI installer

**Attribution:** leonxlnx (Leonxlnx), MIT License.

---

## License Notice

All third-party content used under MIT license. All StatuteProof-specific content (agents, docs, workflows, prompts, skills) is proprietary to the workspace owner.
