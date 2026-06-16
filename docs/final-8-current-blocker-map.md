# Final-8 Current Blocker Map

Date: 2026-06-16

## Fastest Path To 50

The project needs **8 more** readiness-supported sources. The fastest safe path is not more broad discovery; it is converting already identified official endpoints that are closest to activation:

1. CBUAE official rulebook section variants where `cbuae_document_listing` already proved stable.
2. DFSA current public pages where `dfsa_notice_listing` already proved stable.
3. VARA official `rulebooks.vara.ae` pages if direct PDF or static drift can be controlled.
4. ADGM alternate component pages only if selectors produce meaningful, non-duplicate content.
5. DIFC only if public selectors/access are safe.

## Closest Candidates

| Group | Candidate examples | Current blocker | Fix path |
| --- | --- | --- | --- |
| CBUAE rulebook variants | Stored Value, Complaints, Open Finance, Payment Token, Risk Management | Need exact official rulebook URLs and stable document listing output | Use official `rulebook.centralbank.ae` pages with `cbuae_document_listing`; avoid static body drift. |
| DFSA leftovers | Published decisions, publications, AML/CTF sanctions, public register | Some pages are broad/search-like or duplicate of activated DFSA current listings | Test with `dfsa_notice_listing`; only activate unique detail/listing sources. |
| VARA PDF/static pages | AML/CFT controls, compliance/risk rulebook, direct PDF files | Direct PDF shallow path; static rulebook hash drift | Add/verify direct PDF extraction; hold drifting static pages if not stable. |
| ADGM alternate | Data protection regulatory actions, media announcements, listing authority announcements | Alternate web component or nav-shell under current selector | DOM/XHR inspect; use card/listing extraction only if meaningful. |
| DIFC | Data protection, consultations, legal database | Access/selector issue | Test public unauthenticated access; keep blocked if access controls or shell persist. |
| FIU leftovers | Press releases, strategic analysis, NRA 2024 | Duplicate FIU hub hashes or shallow routes | Find unique document endpoints or reject/hold duplicates. |

## Candidates With No-Save Pass But No Activation

- `AE-vara-compliance-risk-rulebook`: no-save passed but mass-monitor dry-run produced `QUALITY_DROP` and hash drift. Needs stable extraction or hold.
- Static CBUAE rulebook body variants previously passed but drifted. Use document-list variants instead; do not activate static duplicates.

## Candidates With Evidence But Held

- `AE-vara-compliance-risk-rulebook`: evidence existed but dry-run drift blocked activation.
- Static CBUAE body variants: evidence existed but document-list variants replaced them.

## Candidates Blocked By PDF / Selector / XHR

- VARA direct PDF files: public official PDFs but current path returned shallow/no text.
- DIFC pages: access/selector blocked.
- ADGM alternate components: component selectors not yet reliable.
- FIU residual pages: SPA route aliases and duplicate document hubs.

## Reject / Hold Rules

- Do not activate duplicate FIU/CBUAE/DFSA hash aliases.
- Do not activate generic homepages or broad discovery hubs.
- Do not activate search/register pages unless rows are public, stable, and useful to MLRO/CCO users.
- Do not activate direct PDFs unless text extraction is meaningful and baseline-stable.
