# ui-ux-pro-max-skill — Reference Notes

**Repo:** https://github.com/nextlevelbuilder/ui-ux-pro-max-skill
**License:** MIT
**Inspected:** 2026-06-11

## What ui-ux-pro-max-skill Is

An AI skill by nextlevelbuilder (uupm.cc) providing design intelligence across multiple domains: product type, UI styles, font pairings, color palettes, landing page structure, chart types, and UX best practices. Backed by CSV databases and a Python BM25 search engine. 161 reasoning rules, 67 UI styles.

## What Was Useful for StatuteProof

**Domain review categories:** landing, product, style, typography, color, ux, chart. These six domains structured the approach to the UI/UX review skill.

**UX best-practices and anti-patterns domain:** The vocabulary for reviewing dashboard elements — cognitive load, trust signals, friction reduction, information hierarchy.

**Landing page structure:** Sections (hero, proof, features, pricing, CTA) mapped to the StatuteProof landing page review framework.

**"Score each dimension independently" methodology:** Adopted for the ui-ux-review skill (seven dimensions, each 1–10).

## What Was Rejected

| Rejected | Why |
|----------|-----|
| Python search scripts (search.py, core.py) | Not needed; StatuteProof is document-only |
| CSV databases (67 UI styles, 161 rules) | Too generic; adapted principles instead |
| CLI installer (uipro-cli npm package) | Not relevant |
| Stack-specific guidelines (React, SwiftUI, etc.) | Not relevant to StatuteProof's current stack |

## What Was Created Based on ui-ux-pro-max-skill

`skills/ui-ux-review/SKILL.md` — UX review for StatuteProof landing page and dashboard. Covers trust signals, CTA, copy safety, source transparency, and design quality.

## License Note

MIT licensed. Review domain categories and scoring methodology adapted; no Python code or CSV data copied.
