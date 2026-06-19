# Agent Council Execution Roadmap

Date: 2026-06-19

## P0 - Truth And Evidence Gates

1. Consolidated fresh-alert evidence validator.
   - Owner: Code Architect.
   - Review: Evidence Trail, QA / Critic.
   - Goal: fail when fresh-alert sources lack proof path, normalized path, normalized hash, daily metadata, baseline, or MONITOR_OK.

2. Canonical evidence-record validator.
   - Owner: Evidence Trail.
   - Review: Risk + Brief Pipeline, QA / Critic.
   - Goal: block customer briefs unless production evidence records are complete.

3. Stale UI/source claim cleanup.
   - Owner: Product Manager.
   - Review: Legal Language, QA / Critic.
   - Goal: remove stale `225 monitoring-active`, broad SCA/FIU/MoJ/MoF claims, and complete-coverage implications.

4. Status vs monitoring_mode reconciliation.
   - Owner: Source Monitor.
   - Review: Code Architect, QA / Critic.
   - Goal: separate legacy active status from fresh-alert, evidence-library, candidate, and remediation modes.

5. `source_summary` fresh-alert count fix.
   - Owner: Code Architect.
   - Review: Product Manager, QA / Critic.
   - Goal: stop using legacy active count as customer monitoring count.

## P1 - Adapter / Source Expansion

1. VARA one source to 25.
   - Build regulatory-notice, enforcement, or register adapter only if public content passes gates.

2. DFSA publication/guidance/policy listing adapter.
   - Fix Go-to-Homepage/nav-shell extraction before adding sources.

3. SCA table/download adapter.
   - Find public table/filter/download endpoint; do not force nav-shell pages.

4. DIFC consultation/legal listing adapter.
   - Isolate consultation cards/PDF rows and exclude business/laws navigation.

5. ADGM/FSRA selector cleanup.
   - Convert candidate pages from brittle custom elements to stable itemized extraction.

6. MoF publication/decision adapter.
   - Grow from the publications hub into specific official decision/news/legal/tax/publication endpoints.

7. FIU circulars public-source investigation.
   - Prove whether public FIU circular endpoints exist; keep goAML blocked.

8. MoJ/Gazette official alternative research.
   - Find accessible official endpoints; do not bypass WAF/access controls.

## P2 - Sales / Product

1. Source-family strength panel.
   - Show Strong, Good, Partial, Weak, Missing with exact blocker notes.

2. Safe pilot source readiness page.
   - Show fresh-alert, evidence-library, candidate, and remediation counts separately.

3. Outreach only for approved anchors.
   - Current safe anchors: CBUAE, MoE/DNFBP AML, FTA, EOCN/TFS selected-source, and scoped VARA/DFSA/ADGM.

## Operating Principle

The council optimizes for evidence-backed customer trust, not impressive source counts.
