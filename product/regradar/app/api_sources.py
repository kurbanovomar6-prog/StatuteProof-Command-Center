"""Source-status + custom-source request handlers, extracted from ``app.api``.

One cohesive slice of the HTTP surface — the sources-status list, sources
summary, per-source health timeline, the single-source connectivity test, and
the custom-source lifecycle (list / discover / test / add) — as a mixin that
``app.api._Handler`` inherits. The method bodies are byte-identical to their
former inline definitions; only their host class/file changed.

Bare module globals the moved bodies read are imported here FROM ``app.api`` so
they are the SAME objects the rest of the handler uses (and so tests that
monkeypatch ``app.api_sources.<name>`` steer these methods exactly as they
previously steered ``app.api.<name>``). Shared per-request helpers stay on
``_Handler`` and are reached through ``self``. Function-local imports inside
bodies resolve at call time against their source modules.
"""
from __future__ import annotations

from app.api import (
    _SOURCE_TEST_LIMITER,
    _same_owner,
    logger,
    parse_qs,
    rbac_runtime,
    require_auth,
    urlparse,
)


class _SourcesHandlerMixin:
    def _handle_sources_status(self) -> None:
        """
        GET /api/sources/status?market=AE

        Returns live source run status from source_runs.jsonl merged with the
        enabled source list from sources.json.

        Requires session auth (same as all other protected endpoints).
        Returns status counts even when no runs have been recorded yet.
        """
        user = require_auth(self)
        if not user:
            self._send_json({"ok": False, "message": "Unauthenticated."}, 401)
            return

        params = parse_qs(urlparse(self.path).query)
        market = str((params.get("market") or ["AE"])[0]).upper().strip() or "AE"

        try:
            from app.source_readiness import load_market_sources
            from app.source_runs import latest_runs
            from app.source_health_timeline import (
                FRESHNESS_NEVER_RUN,
                FRESHNESS_STALE,
                FRESHNESS_UNKNOWN,
                build_source_timeline,
                check_freshness,
            )

            all_sources = load_market_sources(market)
            enabled_sources = [s for s in all_sources if s.get("enabled", False)]
            # Cross-tenant scope: drop custom sources this user does not own so a
            # victim's private source_id / name / URL never leaks to another
            # authenticated account. Official / shared sources always survive.
            enabled_sources = self._visible_sources_for(user, enabled_sources)

            # latest_runs returns dict keyed by source_id (or url fallback).
            # Cycles skipped by the circuit breaker fetched nothing, so they
            # must not be reported as the source's last check.
            run_map = latest_runs(market, include_skipped=False)

            sources_out: list[dict] = []
            last_run_at: str | None = None

            for src in enabled_sources:
                source_id = str(src.get("source_id") or src.get("id") or "")
                name = str(src.get("name") or "")

                # Try lookup by source_id first, then by name
                run = run_map.get(source_id) or run_map.get(name)

                if run:
                    change_status = str(run.get("change_status") or "UNKNOWN")
                    run_at = str(run.get("timestamp_utc") or run.get("run_at") or "")
                    access_status = str(run.get("access_status") or "unknown")
                    extraction_quality = str(run.get("extraction_quality") or "UNKNOWN")
                    normalized_hash = str(run.get("normalized_hash") or run.get("content_hash") or "")
                    proof_path = str(run.get("proof_block_path") or "")
                    last_evidence_at = run_at if proof_path else None
                    # Track most recent run timestamp across all sources
                    if run_at and (last_run_at is None or run_at > last_run_at):
                        last_run_at = run_at
                else:
                    change_status = "NOT_RUN"
                    run_at = None
                    access_status = "unknown"
                    extraction_quality = "UNKNOWN"
                    normalized_hash = ""
                    proof_path = ""
                    last_evidence_at = None

                try:
                    timeline_event_count = int(build_source_timeline(
                        source_id, org_id=self._caller_org_id(user), limit=200
                    ).get("total_events") or 0)
                except Exception:
                    timeline_event_count = 0

                # How old is the check behind this row. Derived from the run trail,
                # never from the registry: sources.json carries hand-written
                # last_monitor_status values that monitoring runs do not update
                # (mass_monitoring_runner sets sources_json_changed = False), so
                # every alert-eligible row said MONITOR_OK at a median recorded age
                # of 36 days. A caller must be able to see the age, not just a word.
                freshness = check_freshness(run_at)
                registry_status = str(src.get("status") or "active")
                # "active" is a CONFIGURATION state, not a health state. Never let
                # it read as healthy when no recent check backs it.
                if freshness["state"] in (FRESHNESS_STALE, FRESHNESS_NEVER_RUN, FRESHNESS_UNKNOWN):
                    reported_status = freshness["state"]
                else:
                    reported_status = registry_status

                sources_out.append({
                    "source_id": source_id,
                    "name": name,
                    "category": str(src.get("category") or ""),
                    "url": str(src.get("url") or ""),
                    "status": reported_status,
                    "configured_status": registry_status,
                    "freshness": freshness["state"],
                    "last_run_age_days": freshness["age_days"],
                    "stale_after_days": freshness["stale_after_days"],
                    "change_status": change_status,
                    "last_run_at": run_at,
                    "last_evidence_at": last_evidence_at,
                    "access_status": access_status,
                    "extraction_quality": extraction_quality,
                    "normalized_hash": normalized_hash,
                    "proof_block_path": proof_path,
                    "timeline_event_count": timeline_event_count,
                    "remediation_reason": str(src.get("remediation_reason") or src.get("notes") or src.get("scraper_notes") or ""),
                })

            # Build summary counts
            summary: dict[str, int] = {}
            for s in sources_out:
                cs = s["change_status"]
                summary[cs] = summary.get(cs, 0) + 1

            # Freshness belongs in the summary too. A per-row field is easy to miss
            # in a long table; a headline count is not, and "how many of these am I
            # actually still checking" is the question the table exists to answer.
            freshness_summary: dict[str, int] = {}
            for s in sources_out:
                freshness_summary[s["freshness"]] = freshness_summary.get(s["freshness"], 0) + 1

            self._send_json({
                "ok": True,
                "market": market,
                "sources": sources_out,
                "summary": summary,
                "freshness_summary": freshness_summary,
                "total_sources": len(sources_out),
                "last_run_at": last_run_at,
                "disclaimer": "Not legal advice. For monitoring information only.",
            })
        except Exception as exc:
            logger.error("sources/status failed: %s", type(exc).__name__)
            self._send_json({"ok": False, "message": "Internal server error."}, 500)

    def _handle_sources_summary(self) -> None:
        """GET /api/sources/summary?market=AE — canonical source counts."""
        user = require_auth(self)
        if not user:
            self._send_json({"ok": False, "message": "Unauthenticated."}, 401)
            return
        params = parse_qs(urlparse(self.path).query)
        market = str((params.get("market") or ["AE"])[0]).upper().strip() or "AE"
        try:
            from app.source_summary import build_sources_summary

            # Cross-tenant scope: exclude custom sources this user does not own so
            # the aggregate counts never reflect another tenant's private sources.
            self._send_json(build_sources_summary(
                market,
                excluded_source_ids=self._denied_custom_source_ids(user),
            ))
        except Exception as exc:
            logger.error("sources/summary failed: %s", type(exc).__name__)
            self._send_json({"ok": False, "message": "Internal server error."}, 500)

    def _handle_source_timeline_get(self) -> None:
        user = require_auth(self)
        if not user:
            self._send_json({"ok": False, "message": "Unauthenticated."}, 401)
            return
        params = parse_qs(urlparse(self.path).query)
        source_id = str((params.get("source_id") or params.get("id") or [""])[0]).strip()
        if not source_id:
            self._send_json({"ok": False, "message": "source_id is required."}, 400)
            return
        # Cross-tenant scope: another tenant's private custom source must not leak
        # its identity / URL / health via a guessed source_id. Return "not found"
        # (do not confirm the source exists) rather than 403 so existence is not
        # disclosed. Official / shared sources are unaffected.
        if not self._source_visible_to(user, source_id):
            self._send_json({"ok": False, "message": "Source not found."}, 404)
            return
        try:
            from app.source_health_timeline import build_source_timeline

            try:
                limit = int((params.get("limit") or ["100"])[0])
            except (TypeError, ValueError):
                limit = 100
            timeline = build_source_timeline(
                source_id, org_id=self._caller_org_id(user), limit=max(1, min(limit, 200))
            )
            self._send_json(timeline)
        except ValueError as exc:
            self._send_json({"ok": False, "message": str(exc)}, 400)
        except Exception as exc:
            logger.error("source timeline load failed: %s", type(exc).__name__)
            self._send_json({"ok": False, "message": "Internal server error."}, 500)

    def _handle_source_test(self) -> None:
        """
        Run a source compatibility check on a user-supplied URL.

        Uses existing test_source_url logic (SSRF-safe, no AI, no Telegram).
        Returns a standardised result for the frontend testing UI.
        """
        user = require_auth(self)
        if not user:
            self._send_json({"ok": False, "message": "Unauthenticated."}, 401)
            return
        if self._rate_limited(_SOURCE_TEST_LIMITER, "source_test"):
            return

        from app.source_tester import test_source_url, validate_public_url

        body = self._read_json()
        url  = str(body.get("url", "")).strip()

        if not url:
            self._send_json({"ok": False, "message": "URL is required."}, 400)
            return

        # Quick safety check before any network call
        safe, safety_msg = validate_public_url(url)
        if not safe:
            self._send_json({
                "ok":             False,
                "status":         "FAILED",
                "message":        f"URL failed safety check: {safety_msg}",
                "recommendation": "This URL cannot be used.",
                "extraction":     [],
                "chars":          0,
            }, 400)
            return

        try:
            result = test_source_url(url)
        except Exception as exc:
            logger.error("source-test error: %s: %s", type(exc).__name__, exc)
            self._send_json({"ok": False, "message": "Source test failed internally."}, 500)
            return

        verdict = result.get("verdict", "cannot_monitor")
        chars   = result.get("extracted_chars", 0)
        method  = result.get("recommended_method", "")
        reason  = result.get("reason", "")

        if verdict == "can_monitor":
            status         = "PASS"
            extraction     = ["HTML", "JS"] if "playwright" in method else ["HTML"]
            recommendation = "Can be monitored automatically."
        elif verdict == "needs_adapter":
            status         = "NEEDS_ADAPTER"
            extraction     = ["Limited"]
            recommendation = "Needs custom adapter for reliable extraction."
        else:
            status         = "FAILED"
            extraction     = []
            recommendation = "Not enough content to monitor reliably."

        self._send_json({
            "ok":             True,
            "status":         status,
            "extraction":     extraction,
            "chars":          chars,
            "message":        reason,
            "recommendation": recommendation,
        })

    def _handle_custom_sources_list(self) -> None:
        """
        List custom (user-added) sources for the authenticated user.

        GET /api/custom-sources
        Custom sources are identified by 'custom': True in sources.json.
        """
        user = require_auth(self)
        if not user:
            self._send_json({"ok": False, "message": "Unauthenticated."}, 401)
            return
        try:
            user_id = int(user["id"])
            from app.source_intake import load_sources_json
            sources = load_sources_json()
            # Tenancy: only return the caller's own custom sources. A custom
            # source with no owner recorded (legacy, pre-tenancy) is treated as
            # unowned and is NOT leaked to an arbitrary user.
            custom = [
                s
                for s in sources
                if s.get("custom") is True
                and s.get("owner_user_id") is not None
                and _same_owner(s.get("owner_user_id"), user_id)
            ]
            self._send_json({"ok": True, "sources": custom})
        except Exception as exc:
            logger.error("custom-sources list error: %s", exc)
            self._send_json({"ok": False, "message": "Failed to load custom sources."}, 500)

    def _handle_custom_source_discover(self) -> None:
        """
        Discover public endpoint candidates for a custom source URL.

        POST /api/custom-sources/discover
        Body: { "url": "https://...", "use_js": false }
        Returns structured no-save discovery data only. It never writes evidence
        and never marks a source ready.
        """
        user = require_auth(self)
        if not user:
            self._send_json({"ok": False, "message": "Unauthenticated."}, 401)
            return
        if self._rate_limited(_SOURCE_TEST_LIMITER, "custom_source_discover"):
            return

        body = self._read_json()
        url = str(body.get("url", "")).strip()
        if not url:
            self._send_json({"ok": False, "message": "URL is required."}, 400)
            return

        from app.source_tester import validate_public_url
        safe, safety_msg = validate_public_url(url)
        if not safe:
            self._send_json({"status": "BLOCKED", "reason": safety_msg, "ok": False}, 400)
            return

        try:
            from app.source_discovery import discover_source
            report = discover_source(
                url,
                use_js=bool(body.get("use_js") or body.get("js")),
                include_network=bool(body.get("network")),
                include_sitemap=body.get("sitemap", True) is not False,
                include_feeds=body.get("feeds", True) is not False,
                include_documents=body.get("documents", True) is not False,
                max_links=int(body.get("max_links") or 50),
                max_depth=int(body.get("max_depth") or 1),
            )
            self._send_json({
                "ok": True,
                "discovery": report,
                "evidence_written": False,
                "evidence_level": "PREVIEW_ONLY",
                "can_activate_monitoring": False,
                "message": "Discovery completed. Run a no-save Source Lab test before any evidence or activation step.",
            })
        except Exception as exc:
            logger.error("custom-source discovery error: %s: %s", type(exc).__name__, exc)
            self._send_json({"ok": False, "message": "Source discovery failed."}, 500)

    def _handle_custom_source_test(self) -> None:
        """
        Test a custom source URL using the intake layer.

        POST /api/custom-sources/test
        Body: { "url": "https://...", "name": "optional label" }
        Returns: intake result with status, quality fields, evidence level,
        can_save_for_validation, and can_activate_monitoring.
        """
        user = require_auth(self)
        if not user:
            self._send_json({"ok": False, "message": "Unauthenticated."}, 401)
            return
        if self._rate_limited(_SOURCE_TEST_LIMITER, "custom_source_test"):
            return

        body = self._read_json()
        url = str(body.get("url", "")).strip()

        if not url:
            self._send_json({"ok": False, "message": "URL is required."}, 400)
            return

        from app.source_tester import validate_public_url
        safe, safety_msg = validate_public_url(url)
        if not safe:
            self._send_json({"status": "BLOCKED", "reason": safety_msg, "ok": False}, 400)
            return

        try:
            from app.source_intake import run_source_intake, load_sources_json, STATUS_LABELS, build_source_lab_contract
            source = {"url": url, "source_id": "", "name": body.get("name", "")}
            if body.get("content_selector"):
                source["content_selector"] = str(body.get("content_selector"))
            if body.get("wait_for_selector"):
                source["wait_for_selector"] = str(body.get("wait_for_selector"))
            if body.get("expected_min_length"):
                source["expected_min_length"] = int(body.get("expected_min_length") or 0)
            if body.get("fetch_method") == "playwright":
                source["fetch_method"] = "playwright"
            if body.get("pdf_mode"):
                source["source_type"] = "pdf"
            if body.get("adapter_family"):
                source["adapter_family"] = str(body.get("adapter_family"))
            if body.get("adapter_name"):
                source["adapter_name"] = str(body.get("adapter_name"))
            adapter_config = body.get("adapter_config")
            if isinstance(adapter_config, dict):
                source["adapter_config"] = adapter_config
            all_sources = load_sources_json()
            result = run_source_intake(source, all_sources=all_sources, write_evidence=False)

            contract = build_source_lab_contract(result)
            normalized_hash = result.get("normalized_hash") or result.get("content_hash", "")
            # Tenancy: a hash collision against another tenant's PRIVATE custom
            # source must not disclose that source's id. Keep the collision signal
            # (so the caller knows the content is a duplicate) but hide whose it is
            # unless the colliding source is visible to this caller (official, or
            # the caller's own custom source).
            collision_source_id = result.get("collision_source_id") or ""
            if collision_source_id and not self._source_visible_to(user, collision_source_id):
                collision_source_id = ""
            self._send_json({
                "ok": True,
                "status": result["status"],
                "readiness_status": result["status"],
                "status_label": STATUS_LABELS.get(result["status"], result["status"]),
                "can_save_for_validation": contract["can_save_for_validation"],
                "can_activate_monitoring": contract["can_activate_monitoring"],
                "can_activate": contract["can_activate_monitoring"],
                "activation_readiness": contract["activation_readiness"],
                "baseline_runs_completed": contract["baseline_runs_completed"],
                "baseline_runs_required": contract["baseline_runs_required"],
                "source_type": "custom_public_source",
                # extraction details
                "chars": result["chars_normalized"],
                "normalized_length": result["chars_normalized"],
                "chars_raw": result["chars_raw"],
                "pdf_chars": result["pdf_chars"],
                "extraction_method": result.get("extraction_method", ""),
                "provider_used": result.get("provider_used") or result.get("extraction_method", ""),
                "adapter_used": result.get("adapter_used", False),
                "adapter_family": result.get("adapter_family", ""),
                "adapter_name": result.get("adapter_name", ""),
                "adapter_version": result.get("adapter_version", ""),
                "extraction_strategy": result.get("extraction_strategy", ""),
                "adapter_metadata": result.get("adapter_metadata", {}),
                "adapter_warnings": result.get("adapter_warnings", []),
                "dom_investigation": result.get("dom_investigation", {}),
                "normalized_hash": normalized_hash,
                "normalized_preview": result.get("normalized_preview", ""),
                # quality
                "quality": result["quality"],
                "quality_label": result["quality"],
                "quality_score": result.get("quality_score", 0),
                "quality_breakdown": result.get("quality_breakdown", {}),
                # safety flags
                "nav_shell_detected": result["nav_shell_detected"],
                "hash_collision": result["hash_collision"],
                "collision_source_id": collision_source_id,
                "official_status": result.get("official_status", ""),
                "access_status": result.get("access_status", ""),
                "meaningful_content": result.get("meaningful_content", False),
                "shallow_content": result.get("shallow_content", False),
                "duplicate_hash": result.get("duplicate_hash", False),
                "noise_risk": result.get("noise_risk", "unknown"),
                "source_health_risk": result.get("source_health_risk", "unknown"),
                # failure detail
                "failure_code": result.get("failure_code", ""),
                "failure_reason": result.get("failure_reason", ""),
                "remediation_hint": result.get("remediation_hint", ""),
                "warnings": result.get("errors", []),
                "notes": result["notes"],
                # evidence status for this no-save test
                "evidence_written": False,
                "evidence_required": True,
                "proof_path": None,
                "evidence_level": result.get("evidence_level", "PREVIEW_ONLY"),
                "certification_status": result.get("certification_status", ""),
                "certification": result.get("certification", {}),
                "legal_policy_status": result.get("legal_policy_status", "PUBLIC_SOURCE_ONLY"),
            })
        except Exception as exc:
            logger.error("custom-source test error: %s: %s", type(exc).__name__, exc)
            self._send_json({"ok": False, "message": "Source test failed."}, 500)

    def _handle_custom_sources_add(self) -> None:
        """
        Add a custom source after a successful test.

        POST /api/custom-sources
        Body: { "url": "https://...", "name": "Label", "category": "financial_regulator", "jurisdiction": "AE" }
        """
        user = require_auth(self)
        if not user:
            self._send_json({"ok": False, "message": "Unauthenticated."}, 401)
            return
        # RBAC Stage-2: adding a monitored source mutates configuration. Owner
        # passes; a read-only auditor seat is denied 403. No-op for accounts today.
        if not self._rbac_guard(user, rbac_runtime.SOURCE_EDIT, resource_type="source"):
            return

        # SEC-3: enforce the custom_sources plan cap SERVER-SIDE (was defined in
        # plan.py but never checked here). Rate-limit the write too — each add
        # triggers a real outbound fetch via run_source_intake, and this handler
        # previously had no limiter at all (its discover/test siblings do).
        if self._rate_limited(_SOURCE_TEST_LIMITER, "custom_source_add"):
            return
        if not self._require_capability(user, "custom_sources"):
            return
        try:
            from app.plan import capabilities_for as _caps_for
            from app.source_intake import load_sources_json as _load_sources_for_cap

            _uid = int(user["id"])
            _cap = int(_caps_for(_uid).get("custom_sources") or 0)
            _owned = sum(
                1
                for s in _load_sources_for_cap()
                if s.get("custom") is True
                and s.get("owner_user_id") is not None
                and _same_owner(s.get("owner_user_id"), _uid)
            )
            if _cap and _owned >= _cap:
                self._send_json(
                    {
                        "ok": False,
                        "message": f"Your plan allows up to {_cap} custom source(s). Remove one or upgrade to add more.",
                    },
                    403,
                )
                return
        except Exception:  # noqa: BLE001 — a broken limit check must fail CLOSED
            self._send_json({"ok": False, "message": "Could not verify your custom-source limit."}, 403)
            return

        body = self._read_json()
        url = str(body.get("url", "")).strip()
        name = str(body.get("name", "")).strip() or url
        category = str(body.get("category", "custom")).strip()
        jurisdiction = str(body.get("jurisdiction", "AE")).strip()
        legal_confirmed = bool(body.get("legal_confirmed") or body.get("legalConfirmation"))

        if not url:
            self._send_json({"ok": False, "message": "URL is required."}, 400)
            return
        if not legal_confirmed:
            self._send_json({
                "ok": False,
                "message": "Legal confirmation is required before saving a custom source.",
            }, 400)
            return

        try:
            from app.source_tester import (
                validate_public_url,
                source_url_exists_for_user,
                append_source_to_json,
            )
            from app.source_intake import run_source_intake, load_sources_json
            import hashlib

            safe, reason = validate_public_url(url)
            if not safe:
                self._send_json({"ok": False, "message": f"URL blocked: {reason}"}, 400)
                return

            # SCOPED duplicate check (not the GLOBAL source_url_exists): only an
            # official source or THIS user's own custom source counts as a
            # visible duplicate. A URL another tenant added as a private custom
            # source is treated as absent here, so this 409 can never become a
            # cross-tenant "user B monitors URL X" oracle.
            if source_url_exists_for_user(url, user.get("id")):
                self._send_json({"ok": False, "message": "This URL is already in your source list."}, 409)
                return

            intake_result = run_source_intake(
                {
                    "url": url,
                    "source_id": "",
                    "name": name,
                    "category": category,
                    "jurisdiction": jurisdiction,
                },
                all_sources=load_sources_json(),
                write_evidence=False,
            )
            if intake_result.get("status") != "CONFIRMED_ACCESSIBLE":
                self._send_json({
                    "ok": False,
                    "message": "Source cannot be saved until readiness test passes.",
                    "readiness_status": intake_result.get("status"),
                    "failure_reason": intake_result.get("failure_reason", ""),
                    "remediation_hint": intake_result.get("remediation_hint", ""),
                }, 400)
                return

            source_id = f"custom-{hashlib.sha256(url.encode()).hexdigest()[:8]}"
            new_source = {
                "source_id": source_id,
                "name": name,
                "url": url,
                "jurisdiction": jurisdiction,
                "category": category,
                "enabled": False,
                "status": "pending_validation",
                "custom": True,
                "tier": "custom",
                # Tenancy stamp: this custom source belongs to the creating user.
                # The list endpoint and export entitlement checks filter on it so
                # one customer's custom sources never leak to another.
                "owner_user_id": int(user["id"]),
            }
            # append_source_to_json enforces GLOBAL url/source_id uniqueness. The
            # scoped check above already passed, so a False here means the URL is
            # held by ANOTHER tenant's custom source (identical deterministic
            # source_id). Report a NON-oracle failure — deliberately not "already
            # in the list" — so we neither falsely claim success nor reveal that
            # another tenant monitors this URL.
            # SEC-3 (TOCTOU): pass the owner + cap so append_source_to_json can
            # re-check the owned count UNDER its write lock — the early prefilter
            # above reads the count without a lock, so concurrent adds could each
            # see 0-of-cap and collectively exceed the plan cap. `_cap` was computed
            # by that prefilter (reached only on the success path); recompute
            # defensively so this never depends on that block's local staying bound.
            from app.plan import capabilities_for as _caps_authoritative

            _cap_authoritative = int(_caps_authoritative(int(user["id"])).get("custom_sources") or 0)
            if not append_source_to_json(
                new_source,
                owner_user_id=int(user["id"]),
                custom_cap=_cap_authoritative or None,
            ):
                self._send_json({
                    "ok": False,
                    "message": "This source could not be saved. Please re-run the readiness test and try again.",
                }, 409)
                return
            self._send_json({
                "ok": True,
                "source_id": source_id,
                "message": "Custom source saved for validation. It is not active until readiness and evidence checks pass.",
            })
        except Exception as exc:
            logger.error("custom-sources add error: %s: %s", type(exc).__name__, exc)
            self._send_json({"ok": False, "message": "Failed to add source."}, 500)
