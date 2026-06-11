"""Structured JSON report builder and terminal display for discover-source."""


def build_json_report(onboarding_result: dict) -> dict:
    """Build standardised JSON output from onboarding result."""
    r = onboarding_result
    verdict = r.get("verdict", "cannot_monitor")
    score   = r.get("quality_score", 0)
    chars   = r.get("extracted_chars", 0)
    method  = r.get("connection_method", "unavailable")

    if verdict == "can_monitor" and score >= 75:
        summary = (
            f"Recommended monitoring via {method}. "
            f"{chars:,} chars extracted from best URL. "
            f"Quality score: {score}/100 ({r.get('quality_label', '')})."
        )
        next_steps = [f"Activate source for monitoring using {method} method."]
    elif verdict == "can_monitor":
        summary = (
            f"Source monitorable with limitations. "
            f"{chars:,} chars extracted. Quality score: {score}/100."
        )
        next_steps = ["Activate for pilot monitoring and review extraction quality periodically."]
    elif verdict == "needs_adapter":
        summary = (
            f"Source requires a custom adapter. "
            f"Generic methods yielded only {chars:,} chars."
        )
        next_steps = [
            "Build a custom adapter targeting stable page structure.",
            "Check for official API, RSS feed, or sitemap as alternative.",
        ]
    else:
        summary = "Source could not be accessed. Verify URL or try an alternative official source."
        next_steps = ["Verify the official URL and retry.", "Search for an alternative official source."]

    lang_list = r.get("language_versions", [])
    lang = lang_list[0]["language"] if lang_list else "Unknown"

    return {
        "submittedUrl":       r.get("submitted_url", ""),
        "bestMonitoringUrl":  r.get("best_monitoring_url", ""),
        "sourceName":         r.get("name", ""),
        "jurisdiction":       r.get("jurisdiction", ""),
        "category":           r.get("category", ""),
        "recommendedStatus":  r.get("recommended_status", "disabled"),
        "connectionMethod":   method,
        "qualityScore":       score,
        "qualityLabel":       r.get("quality_label", "unusable"),
        "extractedChars":     chars,
        "documentsFound":     r.get("documents_found", 0),
        "rssFeedsFound":      r.get("rss_feeds_found", 0),
        "sitemapsFound":      r.get("sitemaps_found", 0),
        "apiEndpointsFound":  r.get("api_endpoints_found", 0),
        "language":           lang,
        "limitations":        r.get("limitations", []),
        "testedMethods":      r.get("tested_methods", []),
        "deepUrlCandidates":  r.get("deep_url_candidates", []),
        "languageVersions":   r.get("language_versions", []),
        "apiEndpoints":       r.get("stages", {}).get("api_endpoints", {}).get("endpoints", []),
        "verdict":            verdict,
        "reason":             r.get("reason", ""),
        "summary":            summary,
        "nextSteps":          next_steps,
        "generatedAt":        r.get("generated_at", ""),
    }
