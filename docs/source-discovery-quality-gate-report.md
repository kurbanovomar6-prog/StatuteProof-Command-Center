# Source Discovery Quality Gate Report

## Improved Gate

The source activation gate now distinguishes discovery problems from parser problems.

Added failure codes:

- `TABLE_ADAPTER_REQUIRED`
- `REGISTER_ADAPTER_REQUIRED`
- `RULEBOOK_ADAPTER_REQUIRED`
- `DISCOVERY_FOUND_BETTER_ENDPOINT`
- `SITEMAP_DISCOVERY_REQUIRED`
- `NETWORK_ENDPOINT_DISCOVERY_REQUIRED`

Existing strict gate remains:

- no-save is preview only;
- one proof run is not monitoring-ready;
- activation requires proof, baseline, and gates;
- high noise/source-health risk blocks activation unless resolved;
- nav-shell and duplicate shell hashes block activation.

## Officially Linked Candidate Rule

Off-domain documents can only become `officially_linked` candidates when they are discovered from a public official source page. They are not active by default, use `manual_review_required`, and must pass provenance, evidence, baseline, QA, legal language, and product relevance gates before any activation.

## Public Chrome False Positives

The gate no longer treats normal public-page login links or recaptcha script assets as proof that the page is private. It still blocks true login forms, captcha walls, paywalls, private portals, and auth-looking URLs.

## Discovery Answers Before No-Save

For a submitted URL, discovery can now answer:

- Is this same-domain official-looking?
- Are there sitemap URLs?
- Are there RSS/Atom feeds?
- Are there PDF/document links?
- Are there public JSON/XML/PDF XHR candidates?
- Are there table/listing/register/rulebook candidates?
- Is there a better endpoint than the submitted page?
- What adapter should be tried first?

## What Discovery Cannot Do

Discovery cannot:

- save evidence;
- activate monitoring;
- claim a source is ready;
- bypass access controls;
- determine legal obligations;
- claim broad website coverage.
