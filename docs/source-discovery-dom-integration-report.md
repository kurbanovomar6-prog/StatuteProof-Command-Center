# Source Discovery / Auto DOM Integration Report

## Integration

The Source Discovery Engine now calls Auto DOM Investigator through `build_discovery_report_from_html`.

Flow:

1. Fetch one public URL.
2. Build discovery report from robots, feeds, documents, same-domain links, tables/listings, and optional network responses.
3. Run `investigate_html` on the fetched HTML.
4. Include `dom_investigation` in the discovery output.
5. Recommend inactive activation paths with adapter families and next actions.

## Output Contract

Discovery reports include:

- `input_url`
- `final_url`
- `official_domain`
- `robots_status`
- `sitemap_urls`
- `feed_urls`
- `document_links`
- `pdf_links`
- `public_json_candidates`
- `xhr_candidates`
- `listing_candidates`
- `table_candidates`
- `rulebook_candidates`
- `register_candidates`
- `same_domain_candidate_urls`
- `rejected_urls`
- `dom_investigation`
- `recommended_activation_paths`

## No-Save Boundary

Discovery output can recommend `run_no_save_test`, but cannot claim:

- evidence confirmed;
- monitoring ready;
- source activated;
- 50/60 working sources.

## Best Use

Use discovery before Source Lab no-save when a regulator source is:

- nav-shell;
- shallow;
- JS-heavy;
- listing-heavy;
- PDF/document-heavy;
- likely backed by public JSON/XML endpoints.

