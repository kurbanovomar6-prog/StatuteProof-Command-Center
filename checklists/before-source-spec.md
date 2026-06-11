# Checklist: Before Source Spec

Complete all items before adding a new source to sources.json.

## URL Verification

- [ ] URL is from an official regulatory domain (vara.ae, centralbank.ae, dfsa.ae, adgm.com, mof.gov.ae, amlcft.ae, uaelegislation.gov.ae, difclaw.difc.ae, moec.gov.ae)
- [ ] URL was manually opened in a browser and loads correctly
- [ ] Page contains regulatory content (not a homepage redirect or error page)
- [ ] Page does not require login or authentication
- [ ] Page does not require JavaScript rendering that the HTTP fetcher cannot handle (if it does: use playwright fetch_method)

## Spec Completeness

- [ ] source_id follows the format: AE-[REGULATOR]-[AREA]-[TYPE]
- [ ] source_name is human-readable and unique
- [ ] regulator matches the official name (not abbreviated unless that is the official name)
- [ ] official_url is the exact URL, not a shortened or redirect URL
- [ ] fetch_method is http or playwright (not manual, unless truly inaccessible)
- [ ] monitoring_frequency is daily or weekly (not hourly)
- [ ] priority is HIGH, MEDIUM, or LOW with a documented reason

## Risk Check

- [ ] This source is not already in sources.json (check for duplicate source_id)
- [ ] This source is within the UAE regulatory scope (not a foreign regulator)
- [ ] The content monitored is regulatory text, not a news feed, blog, or social media

## Approval

- [ ] Source Monitor Agent reviewed the spec
- [ ] enabled is set to false (not yet enabled)
- [ ] Dry run is next step (workflow/03-evidence-dry-run.md)
