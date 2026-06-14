# Codex Skills Marketplace Research for StatuteProof

## 1. Sources Searched
- skills.sh: accessible. The directory states it supports Codex and lists skills such as `just-scrape`, `pdf`, `ui-ux-pro-max`, `copywriting`, `webapp-testing`, and others.
- skillhub.club: accessible. It describes semantic search and Codex-compatible skills, and highlights `systematic-debugging`, `obsidian-markdown`, `ui-ux-pro-max`, `file-search`, and skill creation.
- skillsmp.com: accessible. It describes a marketplace for Claude Code, Codex, ChatGPT, and SKILL.md users, with categories for tools, business, development, testing/security, data/AI, and documentation.

Sources used: skills.sh homepage and detail pages for `just-scrape` and `pdf`; SkillHub homepage; SkillsMP homepage and `code-reviewer` detail page.

## 2. Search Queries Used
- web scraping
- browser automation
- PDF extraction
- HTML cleanup
- URL normalization
- regulatory monitoring
- compliance review
- legal-safe copy
- B2B SaaS landing page
- dashboard UX
- UI/UX review
- evidence audit documentation
- code review
- security review
- testing
- anti-slop writing
- outbound sales
- ICP research
- Obsidian markdown

## 3. Candidate Skills
| Skill name | Source website | Repo/link if available | Category | What it does | Usefulness for StatuteProof | Risk | Install/adapt/reject | Reason |
|---|---|---|---|---|---|---|---|---|
| just-scrape | skills.sh | scrapegraphai/just-scrape | scraping | Search/scrape/extract/crawl/monitor using ScrapeGraph AI CLI | Low for current product because StatuteProof already has fetcher/parser | High | Reject now | Requires SGAI_API_KEY, credits, external CLI, stealth/crawl features too broad |
| pdf | skills.sh | anthropics/skills | PDF | PDF text/table/OCR processing guidance | Medium | Medium | Later | Useful for regulatory PDFs, but current product already has document extraction; do not import until PDF gap is proven |
| browser-use | skills.sh / SkillsMP | browser-use/browser-use | browser automation | Browser interactions, screenshots, extraction | Medium | High | Reject now | Product already uses Playwright; adding browser automation skill could encourage broad live browsing |
| ui-ux-pro-max | skills.sh / SkillHub / SkillsMP | nextlevelbuilder/ui-ux-pro-max-skill | UI/UX | UI/UX review/build guidance | Medium | Medium | Adapted already locally | Existing repo has adapted UI/UX skills; no need for full import |
| frontend-design | skills.sh / SkillsMP | anthropics/skills | frontend | Production-grade frontend interfaces | Medium | Medium | Later | Useful for homepage work, but not evidence-specific |
| webapp-testing | skills.sh | anthropics/skills | testing | Local web app testing workflow | Medium | Low | Later | Useful after dashboard live endpoint exists |
| code-reviewer | SkillsMP | Shubhamsaboo/awesome-llm-apps | code review/security | Security, performance, correctness review | Medium | Medium | Adapt only | Generic; StatuteProof needs evidence/source-specific code review |
| systematic-debugging | SkillHub | obra/superpowers | debugging | Root-cause debugging process | Medium | Low | Later | Good process, but not specific to current needs |
| file-search | SkillHub | massgen | code search | ripgrep/ast-grep guidance | Low | Low | Reject now | Codex already has strong local search instructions |
| obsidian-markdown | SkillHub | kepano | markdown/Obsidian | Obsidian markdown syntax | Low | Low | Reject now | Nice-to-have, not core to product proof |
| copywriting | skills.sh | coreyhaines31/marketingskills | writing | Marketing copy guidance | Medium | Medium | Adapted | Existing anti-slop/outreach skills already cover this with StatuteProof constraints |
| copy-editing | skills.sh | coreyhaines31/marketingskills | writing | Copy editing | Medium | Medium | Adapted | Covered by anti-slop-b2b-copy and legal-safe-copy-review |
| marketing-psychology | skills.sh | coreyhaines31/marketingskills | GTM | Marketing psychology | Low | Medium | Reject now | Too generic for evidence-first regulated SaaS |
| lark-markdown | skills.sh | larksuite/open.feishu | docs | Markdown/doc collaboration | Low | Medium | Reject now | Not needed for current workflow |

## 4. Top 10 Candidate Skills
1. code-reviewer - adapt principles into source/evidence review.
2. ui-ux-pro-max - adapt for MLRO homepage/dashboard review.
3. pdf - consider later for regulatory PDF extraction quality.
4. webapp-testing - consider later after live dashboard integration.
5. systematic-debugging - later for production incidents.
6. copywriting - adapt only for concrete B2B copy.
7. copy-editing - adapt into anti-slop/legal-safe reviews.
8. frontend-design - later for homepage implementation.
9. browser-use - reject for now because Playwright exists and broad scraping risk is high.
10. just-scrape - reject for now because it requires third-party scraping API/credits and broad monitor/crawl behavior.

## 5. Install Now / Later / Reject
| Decision | Skills |
|---|---|
| Install now | None |
| Adapt now | Project review, evidence readiness, source monitoring, legal-safe copy, MLRO homepage, custom source monitoring, anti-slop B2B copy, marketplace research |
| Later | PDF, webapp-testing, frontend-design, systematic-debugging |
| Reject now | just-scrape, browser-use, generic marketing-psychology, lark/Feishu skills, broad cloud/AI/video skills, generic code-reviewer full import |

## 6. Safety Review
- Scripts: no third-party scripts copied into `.agents/skills`.
- Shell commands: no install commands embedded as required execution.
- Network use: skills require approval before live source checks or marketplace installs.
- Secrets risk: rejected skills requiring external API keys for scraping.
- Broad file access: skills are procedural Markdown only.
- Vague instructions: rewritten into StatuteProof-specific checklists.
- License/attribution: reports cite marketplace/repo names; no third-party SKILL.md copied verbatim.

## 7. Recommended StatuteProof Skills
1. statuteproof-project-review.
2. evidence-readiness-review.
3. source-monitoring-review.
4. legal-safe-copy-review.
5. mlro-homepage-review.
6. custom-source-monitoring-spec.
7. anti-slop-b2b-copy.
8. skill-marketplace-research.

## 8. Why Not To Install Everything
Skill bloat creates conflicting procedures, accidental runtime behavior, legal-copy drift, and broad scraping/dependency risk. StatuteProof needs fewer, stricter skills that reinforce evidence readiness, official-source limits, human review, and legal-safe language.
