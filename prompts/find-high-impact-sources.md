# Prompt — find the sources that would make StatuteProof materially better

Use this to hunt for **new monitoring sources with the highest impact per unit of effort**. It is written to avoid the failure modes measured on the current registry (2026-07-22 audit), not to produce another generic list of regulator homepages.

Copy everything between the `---` markers as the task prompt. Run it through parallel research agents (one per family), then an adversarial verifier, then a synthesis pass.

---

## MISSION

Find official-source pages worth ADDING to StatuteProof's monitoring registry, ranked by how much each one would **change what a customer does** — not by how often the page changes.

StatuteProof monitors official regulator pages, detects text changes, seals cryptographic evidence (hash + timestamp + sealed diff, publicly verifiable), and alerts the customer. The buyer is a **UAE MLRO / compliance officer who is personally and criminally exposed**:

- 2026-06-24: CBUAE fined a foreign-bank branch AED 20M **and its Head of Compliance/MLRO AED 300K personally** for "failure to fulfil his responsibilities".
- Federal Decree-Law No. 10 of 2025: knowledge can be **inferred from factual circumstances** ("should-have-known") — up to 10 years imprisonment.
- Therefore the product's value is a timestamped, independently-verifiable record of **what the official page said and when the customer was told**.

A source is valuable in exact proportion to how badly the buyer would be hurt by learning about that change late.

## WHAT THE CURRENT REGISTRY LOOKS LIKE (measured — do not repeat its mistakes)

- **455 entries, 140 enabled, 452 distinct URLs across 164 domains.** Assume broad coverage already exists: all UAE federal + free-zone regulators, the full GCC, and the main international AML/sanctions bodies each have *at least one* URL present.
- **Only ~20 of the 140 enabled sources actually changed** in a 2-week observation window. ~85 are reachable-but-static reference texts (laws, rulebook bodies). **The registry's weakness is not breadth — it is that too few entries are live, action-bearing channels.**
- Disabled-reason census (why things were switched off): `non_uae` 86, `covered_by_hub` 56, `static_pdf` 48, `static_doc` 35, `geo_blocked` 18, `path_moved` 14, `duplicate` 3.

**Your job is therefore NOT "find more regulators". It is: find the specific high-signal, action-bearing, machine-readable UPDATE CHANNELS that are missing.**

## SCORE EVERY CANDIDATE ON THESE SIX AXES (1–5 each, and report each score)

1. **Action-forcing (weight ×3 — the dominant axis).** If this page changes, does the customer have to *do* something — file, notify, freeze, screen, re-train, update a policy, stop onboarding a client? Enforcement decisions, sanctions-list designations, filing deadlines, new/amended obligations, licence conditions = 5. Press photos, event announcements, speeches, annual reports = 1. **A page that updates weekly with nothing actionable is worth less than a page that updates twice a year with a new obligation.**
2. **Cadence.** Confirmed dated items: multiple per month = 5, quarterly = 3, "updates when something happens but that something matters" = still 4 if axis 1 is 5. State the evidence (dates you actually saw).
3. **Primacy.** Is this the **official issuing authority's own page** (5) or a mirror/aggregator/law-firm summary (1–2)? StatuteProof's entire promise is official-source. Never propose a law-firm blog, news outlet, or commercial aggregator as a monitored source. **Exception:** an official *vendor-hosted rulebook mirror* the regulator itself publishes through (e.g. Thomson Reuters-hosted rulebooks) is acceptable and often more reliable — flag it as a mirror and say why it is legitimate.
4. **Feasibility (be brutally honest — see the WAF/geo map below).** Server-rendered HTML listing with visible dates, or an RSS/Atom/XML/CSV feed = 5. Server-rendered but paginated/JS-enhanced = 4. Requires headless browser = 2. Behind Cloudflare/Incapsula/403-to-bots = 1. Geo-blocked to UAE IPs = 1 (note it separately, it is an infrastructure blocker not a code problem).
5. **Diff quality.** Will a text-diff of this page produce a *meaningful* excerpt, or noise? A dated listing of titled items = 5. A page with rotating banners, "last updated" stamps, view counters, session tokens, or a carousel = 2 (it will fire false CHANGED alerts forever). A PDF-only inventory where the HTML is just chrome = 2 unless the PDF itself can be fetched.
6. **Non-duplication.** Is this genuinely distinct from what a hub page already covers? A specific `/enforcement` or `/circulars` sub-page is distinct from the regulator homepage. Two URLs that are the same office on an old and a new domain are NOT distinct.

Report a **total weighted score** and a one-line justification.

## HARD RULES

1. **Evidence or it does not exist.** For every candidate, actually load the page (WebFetch) and report: the most recent 2–3 dated item titles + dates you saw, roughly how many items are listed, and whether the list was present in the server HTML. **Never propose a URL you have not loaded.** If it 403s/404s/redirects, say exactly that — a documented block is a useful finding, an invented URL is a fatal one.
2. **Deduplicate against the existing registry.** You will be given the list of existing domains (and, if available, URLs). If your candidate is on an existing domain, you must explain what distinct *channel* it adds (e.g. "registry has the rulebook body; this is the revision change-log"). Flag `likely_duplicate: true` when unsure — a false dup-flag costs nothing, a duplicate source costs credibility.
3. **Follow redirects and report them.** Regulator sites rename constantly. Known live examples: `sca.gov.ae → uaecma.gov.ae` (301), `moec.gov.ae → moet.gov.ae` (301 **to the homepage** on deep links — a monitor on the old URL reports "changed once, then silent forever"). If a URL redirects, propose the **destination** and note the redirect.
4. **No invented facts, no guessed dates.** If you cannot confirm cadence, say `cadence: unconfirmed` and set confidence low.
5. **Prefer one page that carries many changes over many pages that each carry one.** A regulator's **"revision updates" / change-log** page is the single highest-value shape: it aggregates every amendment with a date. Actively hunt for these — they exist under names like "View Updates", "Revision History", "What's New", "Recent Changes", "Amendments". (Confirmed examples already found: VARA rulebook change-log with 803 dated entries; CBUAE rulebook `view-revision-updates`.)
6. **Hunt machine-readable feeds explicitly.** For sanctions/AML lists, the *feed* URL beats the HTML page: XML/CSV/ODS consolidated lists, RSS. Report the exact feed URL and its format.

## ANTI-PATTERNS — do NOT propose these (each was a real problem in this registry)

- **Static law/act texts.** "Federal Decree-Law No. X of Year" full text: already 85 of these; they change once a decade.
- **Navigation shells.** A page whose body is a menu. The audit found nav-shells exceeding 500 characters and passing the content-length gate while carrying zero substance — two different ADGM pages returned byte-identical 1283-character shells.
- **Old/new domain duplicate pairs.** Two entries for the same office across a domain migration.
- **PDF-inventory pages where the extractor grabs page chrome** instead of the PDF list (measured: an MoF PDF-listing yielded 377 characters of navigation).
- **Aggregators, law-firm insight blogs, news outlets.** Not official sources; they also paraphrase, which destroys the evidentiary value.
- **Login-walled, search-form-only, or geo-blocked pages** — unless you flag them explicitly as infrastructure-blocked findings.

## FEASIBILITY MAP (measured 2026-07-22 — use it, and correct it if you find otherwise)

- **403 to automated fetchers (need headless/browser-UA adapter):** `centralbank.ae` and `rulebook.centralbank.ae`, `www.dfsa.ae`, `namlcftc.gov.ae`, `fatf-gafi.org`, `dubaidet.gov.ae`, plus the known "403 club": `namlcftc`, `dgcx`, `adx`, `dubaidet`.
- **Rate-limited / heavy JS:** `difc.com` (429 + Next.js), `rakicc.com` (Incapsula).
- **Geo-blocked to non-UAE egress (infrastructure, not code):** `uaefiu.gov.ae` (11 entries), `uaelegislation.gov.ae`, `uaecabinet.ae`.
- **Working mirrors — prefer these:** `dfsaen.thomsonreuters.com` works while `dfsa.ae` is walled; `qfcra-en.thomsonreuters.com` for QFCRA; `en.adgm.thomsonreuters.com` for ADGM Courts.
- **Content mirroring is a legitimate workaround:** NAMLCFTC decisions are re-published in EOCN / `uaeiec.gov.ae` news, which is reachable. **Always ask: is this walled content published anywhere reachable?** That answer is worth more than the walled URL.
- **Confirmed clean and server-rendered (good models of what to look for):** `adgm.com` enforcement/alerts tables, `vara.ae` notices, `tax.gov.ae` clarification listings, `mof.gov.ae` legislation, `difccourts.ae` judgments, `uaecma.gov.ae` listings.

## WHERE TO HUNT (families — cover yours exhaustively, not a token sample)

Priority A — UAE core: CBUAE (enforcement/sanctions, rulebook change-log, AML guidance, consumer warnings) · SCA/CMA (`uaecma.gov.ae`: circulars, board decisions, violations register, warnings, drafts) · VARA · DFSA · DIFC (incl. Data Protection Commissioner decisions/fines) · ADGM FSRA + Registration Authority (enforcement, alerts, consultations) · FTA + MoF (public clarifications, decisions, deadlines) · EOCN / UAE FIU / NAMLCFTC / MoJ / MoET (DNFBP supervisors) · Cabinet & Official Gazette · Dubai SLC legislation portal · free zones (DMCC, JAFZA, DAFZA, RAKEZ, Masdar, DIFC RoC).

Priority B — international obligations binding on UAE firms: UN Security Council Consolidated List (XML feed) · OFAC SDN/Consolidated data files + recent actions · EU consolidated sanctions (feed) · UK OFSI consolidated list + recent changes · FATF public statements + high-risk jurisdictions · MENAFATF · Egmont · Wolfsberg (**absent from the registry**) · IOSCO · BIS/FSB where they create direct obligations.

Priority C — GCC (**never yet researched systematically — likely the biggest untapped area**): SAMA circulars + enforcement · CMA Saudi board resolutions/enforcement · QCB + QFCRA + QFIU · CBK + CMA Kuwait · CBB Bahrain rulebook updates + enforcement · CBO/CMA/FSA Oman. Judge these by whether a UAE-licensed firm with GCC exposure would have to act.

Also actively look for **shapes** the registry may lack anywhere: enforcement/decision registers · warning & scam alert lists · consultation papers (advance warning of obligations) · "dear CEO/SEO/MLRO" letter series · licence/authorisation registers with visible revocations · sanctions-list feeds · rulebook change-logs · filing-deadline calendars · court practice directions and judgments where they bind licensed firms.

## ADVERSARIAL VERIFICATION (a second agent must do this, not the researcher)

For each proposed candidate, independently load it and rule:
- **KEEP** — live, dated, genuinely updating, action-bearing, distinct, readable.
- **DOWNGRADE** — real but low-cadence, WAF-hard, or noisy-diff. Say which.
- **DROP** — dead/404, static text, duplicate, navigation shell, aggregator, or unloadable with no reachable mirror.

Be skeptical by default. A static "Law No. X" text is a DROP even if it is genuinely official. A page that will fire a false CHANGED on every visit (rotating content) is a DROP no matter how official.

## DELIVERABLE

1. A **ranked table** (highest weighted score first) with, per source: name · URL · regulator · jurisdiction · content type · confirmed cadence with the dates you saw · six axis scores + weighted total · feasibility (adapter type + WAF/geo risk) · one-line "why the buyer cares".
2. **Config-ready rows** matching the registry shape: `{"name", "url", "jurisdiction", "category", "enabled", "status"}` — so they can be pasted in and put through the readiness gate.
3. **"One adapter unlocks N" analysis** — group the WAF-hard candidates by the single adapter that would unlock them, so the engineering effort can be prioritised by unlock count.
4. **Blocked-findings list** — walled/geo-blocked pages with, for each, whether a reachable mirror or re-publication exists.
5. **Honest gaps** — families or shapes you could not verify, and why. Unfinished work goes in the report; do not paper over it.

---

## Notes for whoever runs this

- Feed the agents the existing domain list first: `python3 -c "import json;d=json.load(open('product/regradar/sources.json'));from urllib.parse import urlparse;print(sorted({urlparse(s['url']).netloc.replace('www.','') for s in (d if isinstance(d,list) else d['sources']) if s.get('url')}))"`
- The cheapest win is not new sources at all: **23 already-enabled sources sit in `status: candidate`** (UN consolidated XML, OFAC recent-actions, EU FSD RSS, OFSI ConList, MENAFATF, SAMA circulars…). Two baseline runs promotes them into the alert core with zero research and zero code.
- Judge any *existing* source the same way: join `data/source_runs/source_runs.jsonl` to the registry on `official_url` and look at `change_status` — that is how "only 20 of 140 actually change" was measured.
