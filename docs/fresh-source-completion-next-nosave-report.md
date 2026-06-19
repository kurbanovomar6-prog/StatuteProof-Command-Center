# Fresh Source Completion Next No-Save Report

- No-save/probe records documented: 16
- Strong no-save passes: 6
- Held/rejected/blocker rows: 10

## Strong Passes

- `AE-uaeiec-news-listing-next` (EOCN/TFS): q65 / 2290 chars / hash `5cf7c49a8103` / adapter `eocn_news_listing`
- `AE-vara-news-circulars-listing` (VARA): q65 / 22738 chars / hash `15ce525ac291` / adapter `vara_news_listing`
- `AE-dfsa-laws-rules-2dee8ba9` (DFSA): q65 / 16947 chars / hash `c4fdcae99dae` / adapter `dfsa_notice_listing`
- `AE-adgm-adgm-courts-legislation-and-procedures-66abfd89` (ADGM/FSRA): q65 / 9714 chars / hash `5d1d32dd304d` / adapter `adgm_fsra_listing`
- `AE-adgm-adgm-courts-forms-fees-and-guides-a3b9d695` (ADGM/FSRA): q61 / 35949 chars / hash `7073f9831858` / adapter `adgm_fsra_listing`
- `AE-mof-publications-and-releases` (MoF): q61 / 20049 chars / hash `9969f3f74f2b` / adapter `uae_legal_database`

## Held / Blockers

- `AE-vara-regulatory-notices-listing` (VARA): Quality score 59 and no structured listing items isolated; not enough for proof-backed fresh_alert activation.. Recommendation: held.
- `AE-vara-notice-endorsements` (VARA): Static notice text, quality 47, no structured listing items; evidence-library only at most.. Recommendation: held.
- `AE-vara-unlicensed-vasps` (VARA): NAV_SHELL_ONLY under current adapter; needs targeted enforcement/register adapter.. Recommendation: held.
- `AE-dfsa-guidance-notes` (DFSA): Playwright fallback returned Go to Homepage nav-shell only.. Recommendation: held.
- `AE-dfsa-publications` (DFSA): Playwright fallback returned Go to Homepage nav-shell only.. Recommendation: held.
- `AE-dfsa-policy-statements` (DFSA): Playwright fallback returned Go to Homepage nav-shell only.. Recommendation: held.
- `AE-difc-consultation-papers` (DIFC): Quality 59; current adapter still includes business/laws navigation and does not pass save gate.. Recommendation: held.
- `AE-adgm-abu-dhabi-legislation-next` (ADGM/FSRA): Quality 59; not enough for evidence save gate without better selector.. Recommendation: held.
- `AE-sca-regulations-listing-next` (SCA): NAV_SHELL_ONLY; needs SCA table/filter endpoint or stronger adapter.. Recommendation: held.
- `AE-moj-laws-next` (MoJ/Gazette): NAV_SHELL_ONLY; legal listing not extractable through current public DOM.. Recommendation: held.
