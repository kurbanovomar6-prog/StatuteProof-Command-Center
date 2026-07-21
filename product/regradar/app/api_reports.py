"""Reports + audit-export request handlers, extracted from ``app.api``.

One cohesive slice of the HTTP surface — the monthly assurance report,
coverage certificate, effective-dates calendar, assurance-digest preview,
canonical-evidence review action, audit vault, evidence pack, regulator binder,
and change-register export — as a mixin that ``app.api._Handler`` inherits. The
method bodies are byte-identical to their former inline definitions; only their
host class/file changed.

Bare module globals the moved bodies read are imported here FROM ``app.api`` so
they are the SAME objects the rest of the handler uses (and so tests that
monkeypatch ``app.api_reports.<name>`` steer these methods exactly as they
previously steered ``app.api.<name>``). Shared per-request helpers (``_send_json``,
``_rate_limited``, ``_rbac_guard``, ``_read_json_strict``, ``_require_capability``,
``_entitle_source_ids``, ``_denied_custom_source_ids``, ``_caller_org_id``,
``_rbac_log_export`` …) stay on ``_Handler`` and are reached through ``self``.
Function-local imports inside bodies resolve at call time against their source
modules.
"""
from __future__ import annotations

from app.api import (
    _EXPORT_LIMITER,
    datetime,
    logger,
    parse_qs,
    rbac_runtime,
    redact_effective_dates_for_plan,
    require_auth,
    timezone,
    urlparse,
)


class _ReportsHandlerMixin:
    # ── GET /api/reports/monthly-assurance ────────────────────────────────────

    def _handle_monthly_assurance_report(self) -> None:
        """Return a monthly monitoring assurance report as JSON (markdown or PDF)."""
        user = require_auth(self)
        if not user:
            self._send_json({"ok": False, "message": "Unauthenticated."}, 401)
            return
        if self._rate_limited(_EXPORT_LIMITER, "monthly_assurance"):
            return
        # The monthly assurance report is a paid deliverable — gate it exactly
        # like the sibling audit exports so a free/unactivated account cannot pull
        # a report for arbitrary source_ids (incl. other tenants' custom sources).
        if not self._require_capability(user, "audit_export"):
            return
        # RBAC Stage-2 (Part A): record the authorized monthly-assurance export.
        self._rbac_log_export(user, resource_type="monthly_assurance")
        from app.monthly_assurance_report import compute_monthly_stats, render_assurance_report_markdown, generate_monthly_report_pdf
        parsed = urlparse(self.path)
        qs = parse_qs(parsed.query)
        now = datetime.now(timezone.utc)
        try:
            year = int((qs.get("year") or [str(now.year)])[0])
            month = int((qs.get("month") or [str(now.month)])[0])
        except (ValueError, IndexError):
            self._send_json({"status": "error", "message": "Invalid year or month."}, 400)
            return
        source_ids_raw = (qs.get("source_ids") or [""])[0]
        source_ids = [s.strip() for s in source_ids_raw.split(",") if s.strip()] or None
        # Tenancy + plan-limit clipping when the caller names sources. If the
        # caller named sources but none survive entitlement, refuse rather than
        # silently widening the query back to every source.
        if source_ids is not None:
            entitled = self._entitle_source_ids(user, source_ids)
            if not entitled:
                self._send_json(
                    {"status": "error", "message": "None of the requested sources are in your plan scope."},
                    403,
                )
                return
            source_ids = entitled
        client_name = (qs.get("client_name") or [""])[0]
        fmt = ((qs.get("format") or ["markdown"])[0]).lower().strip()
        try:
            stats = compute_monthly_stats(source_ids, year, month)
            if fmt == "pdf":
                pdf_path = generate_monthly_report_pdf(stats, client_name=client_name)
                self._send_json({"status": "ok", "report_path": str(pdf_path)})
            else:
                report = render_assurance_report_markdown(stats, client_name=client_name)
                self._send_json({"status": "ok", "report": report, "stats": stats})
        except Exception as exc:
            logger.error("monthly-assurance error: %s", type(exc).__name__)
            self._send_json({"status": "error", "message": "Internal server error."}, 500)

    # ── GET /api/reports/coverage-certificate ─────────────────────────────────

    def _handle_coverage_certificate(self) -> None:
        """Return a negative-assurance coverage certificate (json/markdown/html/pdf).

        Auth-scoped: an unauthenticated caller gets 401. The period is given as
        either ?year=&month= (a calendar month) or ?period_start=&period_end=
        (inclusive ISO dates). ?source_ids= restricts the certified sources.
        """
        user = require_auth(self)
        if not user:
            self._send_json({"ok": False, "message": "Unauthenticated."}, 401)
            return
        if self._rate_limited(_EXPORT_LIMITER, "coverage_certificate"):
            return
        from app.coverage_certificate import (
            build_coverage_certificate,
            enabled_source_ids,
            month_period,
            render_coverage_certificate_markdown,
            render_coverage_certificate_html,
            generate_coverage_certificate_pdf,
        )

        parsed = urlparse(self.path)
        qs = parse_qs(parsed.query)
        now = datetime.now(timezone.utc)
        period_start = (qs.get("period_start") or [""])[0].strip()
        period_end = (qs.get("period_end") or [""])[0].strip()
        if not (period_start and period_end):
            try:
                year = int((qs.get("year") or [str(now.year)])[0])
                month = int((qs.get("month") or [str(now.month)])[0])
                if not 1 <= month <= 12:
                    raise ValueError("month out of range")
                period_start, period_end = month_period(year, month)
            except (ValueError, IndexError):
                self._send_json({"status": "error", "message": "Invalid period."}, 400)
                return

        source_ids_raw = (qs.get("source_ids") or [""])[0]
        source_ids = [s.strip() for s in source_ids_raw.split(",") if s.strip()] or None
        # Tenancy: when the caller explicitly names sources, clip them to the
        # user's entitled scope so a custom source owned by another customer can
        # never be certified into this report.
        if source_ids is not None:
            source_ids = self._entitle_source_ids(user, source_ids) or None
        # Default customer scope: when the caller does not restrict the source
        # set, certify the customer's monitored (enabled) sources so a fully-dark
        # configured source surfaces as NO_COVERAGE instead of vanishing. Falls
        # back to None (run-derived scope) when no enabled sources are configured.
        # Tenancy: drop any custom source the caller does not own from that
        # default set so another tenant's custom source can never be certified
        # into this report (official/global sources are shared and stay).
        if source_ids is None:
            default_ids = enabled_source_ids() or []
            denied = self._denied_custom_source_ids(user)
            source_ids = [s for s in default_ids if s not in denied] or None
        client_name = (qs.get("client_name") or [""])[0]
        fmt = ((qs.get("format") or ["markdown"])[0]).lower().strip()
        # The PDF coverage certificate is a paid deliverable (professional /
        # consultant). Other formats stay available for in-dashboard review.
        if fmt == "pdf" and not self._require_capability(user, "pdf_export"):
            return

        # RBAC Stage-2 (Part A): record the authorized coverage-certificate export.
        self._rbac_log_export(user, resource_type="coverage_certificate")
        try:
            certificate = build_coverage_certificate(
                period_start=period_start,
                period_end=period_end,
                source_ids=source_ids,
                client_name=client_name,
            )
            if fmt == "json":
                self._send_json({"status": "ok", "certificate": certificate})
            elif fmt == "html":
                report = render_coverage_certificate_html(certificate)
                self._send_json({"status": "ok", "report": report, "certificate": certificate})
            elif fmt == "pdf":
                pdf_path = generate_coverage_certificate_pdf(certificate)
                self._send_json({"status": "ok", "report_path": str(pdf_path), "certificate": certificate})
            else:
                report = render_coverage_certificate_markdown(certificate)
                self._send_json({"status": "ok", "report": report, "certificate": certificate})
        except ValueError as exc:
            self._send_json({"status": "error", "message": str(exc)}, 400)
        except Exception as exc:
            logger.error("coverage-certificate error: %s", type(exc).__name__)
            self._send_json({"status": "error", "message": "Internal server error."}, 500)

    def _handle_effective_dates_calendar(self) -> None:
        """GET /api/calendar/effective-dates — forward-looking detected key dates.

        A read-only, own-scope view of dates StatuteProof DETECTED in the changed
        text of monitored sources (effective dates / deadlines / consultation
        closes) and sealed into evidence records. Each item carries its
        verification pointer — the sealed record_hash + evidence_record_id — plus
        the honest "detected in the changed text, verify against source" framing
        and the short disclaimer. It never asserts the reader's obligations and
        makes no completeness claim.

        Window: ?days=N (default 90, clamped 1..365) forward from today, OR an
        explicit ?from=&to= (inclusive ISO dates). ?source_ids= restricts the
        reported sources; the caller's entitled scope is always enforced.

        Mirrors the coverage-certificate handler discipline: auth -> rate limit ->
        entitled scope -> RBAC export log -> build -> render.
        """
        user = require_auth(self)
        if not user:
            self._send_json({"ok": False, "message": "Unauthenticated."}, 401)
            return
        if self._rate_limited(_EXPORT_LIMITER, "effective_dates_calendar"):
            return
        from datetime import date

        from app.effective_dates import upcoming_key_dates

        qs = parse_qs(urlparse(self.path).query)

        def _iso(name: str):
            raw = (qs.get(name) or [""])[0].strip()
            if not raw:
                return None
            try:
                return date.fromisoformat(raw[:10])
            except ValueError:
                return "invalid"

        date_from = _iso("from")
        date_to = _iso("to")
        if date_from == "invalid" or date_to == "invalid":
            self._send_json({"ok": False, "message": "Invalid from/to date (use YYYY-MM-DD)."}, 400)
            return
        try:
            horizon_days = int((qs.get("days") or ["90"])[0])
        except (ValueError, IndexError):
            self._send_json({"ok": False, "message": "Invalid days."}, 400)
            return

        # Tenancy — identical semantics to the coverage certificate. Named sources
        # are clipped to the caller's entitled scope; the default (unnamed) view
        # still excludes any custom source the caller does not own so another
        # tenant's private source can never surface.
        source_ids_raw = (qs.get("source_ids") or [""])[0]
        named = [s.strip() for s in source_ids_raw.split(",") if s.strip()]
        allow_source_ids = None
        if named:
            allow_source_ids = self._entitle_source_ids(user, named)
            if not allow_source_ids:
                self._send_json({"ok": False, "message": "Those sources are not in your plan scope."}, 403)
                return
        excluded_source_ids = self._denied_custom_source_ids(user)

        # RBAC Stage-2 (Part A): record the authorized calendar read.
        self._rbac_log_export(user, resource_type="effective_dates_calendar")
        try:
            result = upcoming_key_dates(
                source_ids=allow_source_ids,
                excluded_source_ids=excluded_source_ids,
                horizon_days=horizon_days,
                date_from=date_from,
                date_to=date_to,
            )
            # Entitlement: each item carries a VERBATIM excerpt of the changed
            # official-source text plus the official URL — the same paid field
            # class the preview withholds and the redline/diff/brief refuse with
            # 402. Routed through the ONE redaction choke point in
            # app/alert_routing.py (same flag, same eligibility helper); the
            # date, its type and the sealed pointer stay, and a free owner's own
            # custom source stays fully visible.
            result = redact_effective_dates_for_plan(int(user["id"]), result)
            self._send_json({"ok": True, **result})
        except Exception as exc:
            logger.error("effective-dates calendar error: %s", type(exc).__name__)
            self._send_json({"ok": False, "message": "Internal server error."}, 500)

    def _handle_assurance_digest_preview(self) -> None:
        """GET /api/digest/assurance-preview — preview the negative-assurance digest.

        A read-only, own-scope PREVIEW of the periodic monitoring-activity digest:
        what was checked, which changes were captured and sealed (each linked to
        its sealed record hash), which sources showed no change DETECTED, and where
        coverage has gaps. It NEVER sends anything and does NOT touch the existing
        alert delivery path — scheduling/sending is a later step.

        Period: ?period_start=&period_end= (inclusive ISO dates) or ?days=N
        (default 7 = weekly, clamped 1..90) ending today. ?source_ids= restricts
        the reported sources; the caller's entitled scope is always enforced.
        Mirrors the coverage-certificate handler discipline: auth -> rate limit ->
        entitled scope -> build -> render.
        """
        user = require_auth(self)
        if not user:
            self._send_json({"ok": False, "message": "Unauthenticated."}, 401)
            return
        if self._rate_limited(_EXPORT_LIMITER, "assurance_digest_preview"):
            return
        from app.assurance_digest import (
            build_assurance_digest,
            render_assurance_digest_email_text,
            render_assurance_digest_markdown,
        )
        from datetime import timedelta

        from app.coverage_certificate import enabled_source_ids

        parsed = urlparse(self.path)
        qs = parse_qs(parsed.query)
        now = datetime.now(timezone.utc)
        period_start = (qs.get("period_start") or [""])[0].strip()
        period_end = (qs.get("period_end") or [""])[0].strip()
        if not (period_start and period_end):
            try:
                days = int((qs.get("days") or ["7"])[0])
            except (TypeError, ValueError):
                days = 7
            days = max(1, min(days, 90))
            end_date = now.date()
            period_end = end_date.isoformat()
            period_start = (end_date - timedelta(days=days - 1)).isoformat()

        source_ids_raw = (qs.get("source_ids") or [""])[0]
        requested_ids = [s.strip() for s in source_ids_raw.split(",") if s.strip()] or None
        # Resolve to an EXPLICIT scope list (never None). This is tenancy-critical:
        # collapsing an empty entitled scope to None would let build_* re-open the
        # global, cross-tenant default scope. An empty list here means "nothing in
        # scope" and yields an honest empty digest instead.
        if requested_ids is not None:
            # Caller named sources: report only the subset they are entitled to.
            scope_ids = self._entitle_source_ids(user, requested_ids)
        else:
            # Default own scope: the customer's monitored (enabled) sources, minus
            # any custom source they do not own — so a fully-dark configured source
            # still surfaces as a gap, and no other tenant's custom source leaks in.
            default_ids = enabled_source_ids() or []
            denied = self._denied_custom_source_ids(user)
            scope_ids = [s for s in default_ids if s not in denied]

        client_name = (qs.get("client_name") or [""])[0].strip()[:200]
        fmt = ((qs.get("format") or ["all"])[0]).lower().strip()
        if fmt not in ("all", "markdown", "email", "text", "json"):
            fmt = "all"

        # RBAC Stage-2 (Part A): record the authorized preview of sealed evidence
        # content, mirroring the coverage-certificate export audit trail.
        self._rbac_log_export(user, resource_type="assurance_digest")
        try:
            digest = build_assurance_digest(
                period_start=period_start,
                period_end=period_end,
                source_ids=scope_ids,
                client_name=client_name,
                now=now,
            )
            payload: dict = {"ok": True, "digest": digest}
            # Always run at least one full-body render so the render-time guard
            # sweeps the assembled document even when only JSON is requested.
            markdown = render_assurance_digest_markdown(digest)
            if fmt in ("all", "markdown"):
                payload["markdown"] = markdown
            if fmt in ("all", "email", "text"):
                payload["email_text"] = render_assurance_digest_email_text(digest)
        except ValueError as exc:
            # Includes ForbiddenClaimError (a ValueError) from the legal-safety guard.
            self._send_json({"ok": False, "message": str(exc)}, 400)
            return
        except Exception as exc:
            logger.error("assurance-digest preview error: %s", type(exc).__name__)
            self._send_json({"ok": False, "message": "Internal server error."}, 500)
            return
        self._send_json(payload)

    def _handle_canonical_evidence_review_action(self) -> None:
        """Append an approval/rejection/block decision for canonical evidence."""
        user = require_auth(self)
        if not user:
            self._send_json({"ok": False, "message": "Unauthenticated."}, 401)
            return
        # RBAC Stage-2: the canonical human review gate (approve/reject/block).
        # Owner passes; a read-only auditor seat is denied 403. No-op today.
        if not self._rbac_guard(user, rbac_runtime.REVIEW_APPROVE, resource_type="review"):
            return
        body, error = self._read_json_strict()
        if error:
            self._send_json({"ok": False, "message": error}, 400)
            return
        if body is None:
            self._send_json({"ok": False, "message": "Request body required."}, 400)
            return
        record_id = str(body.get("record_id") or body.get("evidence_record_id") or "").strip()
        raw_decision = str(body.get("decision") or body.get("action") or "").strip().lower()
        decision = {
            "approve": "approved",
            "approved": "approved",
            "reject": "rejected",
            "rejected": "rejected",
            "block": "blocked",
            "blocked": "blocked",
        }.get(raw_decision, raw_decision)
        note = str(body.get("note") or body.get("reason") or "").strip()
        reviewer = str(user.get("full_name") or user.get("email") or f"user:{user.get('id')}" or "").strip()
        if not record_id or not decision or not note:
            self._send_json({"ok": False, "message": "record_id, decision, and note are required."}, 400)
            return
        # IDOR guard: a reviewer must not append a decision against another
        # tenant's private custom-source canonical record.
        if self._canonical_record_out_of_scope(user, record_id):
            self._send_json({"ok": False, "message": "That evidence record is not in your scope."}, 403)
            return
        # SEC-2: a decision on a SHARED official record changes brief-eligibility
        # for EVERY tenant that relies on that record (build_risk_brief_inputs), so
        # any self-registered ROLE_OWNER could otherwise block or force-approve
        # other tenants' evidence. Restrict shared-official reviews to a
        # global/operator principal; a caller may still review their OWN
        # custom-source record (private to their tenant).
        if not self._caller_is_operator(user) and not self._canonical_record_is_own_custom(user, record_id):
            self._send_json(
                {"ok": False, "message": "Only an operator may review shared official evidence."},
                403,
            )
            return
        try:
            from app.review_queue import record_canonical_review_action

            result = record_canonical_review_action(
                record_id,
                decision=decision,
                reviewer=reviewer,
                note=note,
            )
            if result.get("status") == "error":
                self._send_json({"ok": False, **result}, 400)
            else:
                self._send_json({"ok": True, **result})
        except Exception as exc:
            logger.error("canonical evidence review action error: %s", type(exc).__name__)
            self._send_json({"ok": False, "message": "Internal server error."}, 500)

    # ── POST /api/audit/vault ─────────────────────────────────────────────────

    def _handle_audit_vault(self) -> None:
        """Build a period-based audit vault ZIP from matching evidence records."""
        user = require_auth(self)
        if not user:
            self._send_json({"ok": False, "message": "Unauthenticated."}, 401)
            return
        if self._rate_limited(_EXPORT_LIMITER, "audit_vault"):
            return
        from app.audit_export import build_period_audit_vault, validate_date_range, validate_source_ids
        body, error = self._read_json_strict()
        if error:
            self._send_json({"ok": False, "message": error}, 400)
            return
        if body is None:
            self._send_json({"ok": False, "message": "Request body required."}, 400)
            return
        source_ids = body.get("source_ids")
        date_from = str(body.get("date_from") or "").strip()
        date_to = str(body.get("date_to") or "").strip()
        ids_ok, ids_err = validate_source_ids(source_ids)
        if not ids_ok:
            self._send_json({"ok": False, "message": ids_err}, 400)
            return
        if not self._require_capability(user, "audit_export"):
            return
        valid, err = validate_date_range(date_from, date_to)
        if not valid:
            self._send_json({"ok": False, "message": err}, 400)
            return
        source_ids = self._entitle_source_ids(user, source_ids)
        if not source_ids:
            self._send_json(
                {"ok": False, "message": "None of the requested sources are in your plan scope."},
                403,
            )
            return
        # RBAC Stage-2 (Part A): record the authorized audit-vault export.
        self._rbac_log_export(user, resource_type="audit_vault", resource_id=",".join(source_ids)[:200])
        try:
            result = build_period_audit_vault(source_ids, date_from, date_to)
            status = result.get("status")
            if status == "error":
                # Never forward the builder's internal exception text to the client:
                # it can carry absolute server paths or other internal detail. Log it
                # server-side, return a generic 500.
                logger.error("audit vault build failed: %s", result.get("message"))
                self._send_json({"ok": False, "message": "Failed to build the audit vault."}, 500)
            elif status == "too_large":
                # Availability guard tripped: the selection exceeds MAX_AUDIT_VAULT_RECORDS.
                # 413 with a safe, actionable message (narrow the selection).
                self._send_json(
                    {
                        "ok": False,
                        "message": result.get("message", "Selection too large; narrow the period or sources."),
                        "max_records": result.get("max_records"),
                    },
                    413,
                )
            elif status == "empty":
                self._send_json({"ok": False, **result}, 404)
            else:
                self._send_json({"ok": True, **result})
        except Exception as exc:
            logger.error("audit vault error: %s", type(exc).__name__)
            self._send_json({"ok": False, "message": "Internal server error."}, 500)

    # ── POST /api/evidence/pack ───────────────────────────────────────────────

    def _handle_evidence_pack(self) -> None:
        """Build a self-serve, self-verifiable Evidence Pack ZIP for the client.

        Auth-scoped: an unauthenticated caller gets 401 and no pack. The pack is
        strictly restricted to the requested source_ids — evidence for any other
        source is never included. On success the sealed ZIP (manifest.json +
        standalone verify.py + HOW-TO-VERIFY.md + snapshots + disclaimer) is
        returned as an application/zip download so the customer's own auditor can
        re-hash the bytes offline and confirm they match the manifest.
        """
        user = require_auth(self)
        if not user:
            self._send_json({"ok": False, "message": "Unauthenticated."}, 401)
            return
        if self._rate_limited(_EXPORT_LIMITER, "evidence_pack"):
            return
        from pathlib import Path
        from app.audit_export import validate_date_range, validate_source_ids
        from app.evidence_pack import build_evidence_pack
        body, error = self._read_json_strict()
        if error:
            self._send_json({"ok": False, "message": error}, 400)
            return
        if body is None:
            self._send_json({"ok": False, "message": "Request body required."}, 400)
            return
        source_ids = body.get("source_ids")
        date_from = str(body.get("date_from") or "").strip()
        date_to = str(body.get("date_to") or "").strip()
        ids_ok, ids_err = validate_source_ids(source_ids)
        if not ids_ok:
            self._send_json({"ok": False, "message": ids_err}, 400)
            return
        if not self._require_capability(user, "audit_export"):
            return
        valid, err = validate_date_range(date_from, date_to)
        if not valid:
            self._send_json({"ok": False, "message": err}, 400)
            return
        source_ids = self._entitle_source_ids(user, source_ids)
        if not source_ids:
            self._send_json(
                {"ok": False, "message": "None of the requested sources are in your plan scope."},
                403,
            )
            return
        # RBAC Stage-2 (Part A): record the authorized evidence-pack export.
        self._rbac_log_export(user, resource_type="evidence_pack", resource_id=",".join(source_ids)[:200])
        try:
            result = build_evidence_pack(source_ids, date_from, date_to)
            status = result.get("status")
            if status == "error":
                # Never forward the builder's internal exception text to the client:
                # it can carry absolute server paths or other internal detail. Log it
                # server-side, return a generic 500.
                logger.error("evidence pack build failed: %s", result.get("message"))
                self._send_json({"ok": False, "message": "Failed to build the evidence pack."}, 500)
                return
            if status == "too_large":
                # Availability guard tripped: the selection exceeds MAX_EVIDENCE_PACK_RECORDS.
                # 413 with a safe, actionable message (narrow the selection).
                self._send_json(
                    {
                        "ok": False,
                        "message": result.get("message", "Selection too large; narrow the period or sources."),
                        "max_records": result.get("max_records"),
                    },
                    413,
                )
                return
            if status == "empty":
                self._send_json({"ok": False, **result}, 404)
                return
            pack_path = Path(str(result.get("pack_path") or ""))
            if not pack_path.exists():
                self._send_json({"ok": False, "message": "Evidence pack was not generated."}, 500)
                return
            filename = result.get("pack_filename") or pack_path.name
            try:
                payload = pack_path.read_bytes()
            finally:
                # One-shot download: don't accumulate generated ZIPs on the server's disk.
                pack_path.unlink(missing_ok=True)
            self._send_bytes(
                payload,
                "application/zip",
                extra_headers=[("Content-Disposition", f'attachment; filename="{filename}"')],
            )
        except Exception as exc:
            logger.error("evidence pack error: %s", type(exc).__name__)
            self._send_json({"ok": False, "message": "Internal server error."}, 500)

    # ── POST /api/reports/regulator-binder ────────────────────────────────────

    def _handle_regulator_binder(self) -> None:
        """Build the Regulator-ready Evidence Binder ZIP for the client.

        A period+source-scoped, multi-record extension of the Evidence Pack: for
        the chosen source(s) over the chosen period it bundles every captured
        change (sealed evidence records + raw/normalized snapshots + diffs), a
        machine manifest with a tamper-evident binder content hash, an honest
        COVER.md timeline, and a standalone offline verify.py — so an examiner can
        re-hash everything without trusting StatuteProof.

        Mirrors ``_handle_audit_vault`` / ``_handle_evidence_pack`` exactly:
        require_auth → rate limit → validate_source_ids + validate_date_range →
        require_capability("audit_export") → owner-scope source_ids via
        ``_entitle_source_ids`` (403 if none in scope) → build → stream the ZIP.
        Fails closed; never 500s to the client with an internal detail.
        """
        user = require_auth(self)
        if not user:
            self._send_json({"ok": False, "message": "Unauthenticated."}, 401)
            return
        if self._rate_limited(_EXPORT_LIMITER, "regulator_binder"):
            return
        from pathlib import Path
        from app.audit_export import validate_date_range, validate_source_ids
        from app.regulator_binder import build_regulator_binder
        body, error = self._read_json_strict()
        if error:
            self._send_json({"ok": False, "message": error}, 400)
            return
        if body is None:
            self._send_json({"ok": False, "message": "Request body required."}, 400)
            return
        source_ids = body.get("source_ids")
        date_from = str(body.get("date_from") or "").strip()
        date_to = str(body.get("date_to") or "").strip()
        ids_ok, ids_err = validate_source_ids(source_ids)
        if not ids_ok:
            self._send_json({"ok": False, "message": ids_err}, 400)
            return
        if not self._require_capability(user, "audit_export"):
            return
        valid, err = validate_date_range(date_from, date_to)
        if not valid:
            self._send_json({"ok": False, "message": err}, 400)
            return
        # Owner-scope tenancy: clip to the sources the caller is entitled to. A
        # custom source owned by another tenant is dropped here and never reaches
        # the builder; if nothing survives, 403 (never build another tenant's pack).
        source_ids = self._entitle_source_ids(user, source_ids)
        if not source_ids:
            self._send_json(
                {"ok": False, "message": "None of the requested sources are in your plan scope."},
                403,
            )
            return
        # RBAC Stage-2 (Part A): record the authorized regulator-binder export.
        self._rbac_log_export(user, resource_type="regulator_binder", resource_id=",".join(source_ids)[:200])
        try:
            result = build_regulator_binder(source_ids, date_from, date_to)
            status = result.get("status")
            if status == "error":
                # Never forward the builder's internal exception text to the client:
                # it can carry absolute server paths or other internal detail. Log it
                # server-side, return a generic 500.
                logger.error("regulator binder build failed: %s", result.get("message"))
                self._send_json({"ok": False, "message": "Failed to build regulator binder."}, 500)
                return
            if status == "too_large":
                # Availability guard tripped: the selection exceeds MAX_BINDER_RECORDS.
                # 413 with a safe, actionable message (narrow the selection).
                self._send_json(
                    {
                        "ok": False,
                        "message": result.get("message", "Selection too large; narrow the period or sources."),
                        "max_records": result.get("max_records"),
                    },
                    413,
                )
                return
            if status == "empty":
                self._send_json({"ok": False, **result}, 404)
                return
            binder_path = Path(str(result.get("binder_path") or ""))
            if not binder_path.exists():
                self._send_json({"ok": False, "message": "Regulator binder was not generated."}, 500)
                return
            filename = result.get("binder_filename") or binder_path.name
            try:
                payload = binder_path.read_bytes()
            finally:
                # One-shot download: don't accumulate generated ZIPs on the server's disk.
                binder_path.unlink(missing_ok=True)
            self._send_bytes(
                payload,
                "application/zip",
                extra_headers=[("Content-Disposition", f'attachment; filename="{filename}"')],
            )
        except Exception as exc:
            logger.error("regulator binder error: %s", type(exc).__name__)
            self._send_json({"ok": False, "message": "Internal server error."}, 500)

    # ── POST /api/change-register/export ──────────────────────────────────────

    def _handle_change_register_export(self) -> None:
        """Export the regulatory change register (CSV + XLSX + HTML).

        Auth-guarded; the act/monitor/no_action decision column is scoped to the
        requesting client's own action log (user id). Supports an optional date
        range and optional source_id / regulator filter. An empty range yields an
        empty-but-valid register rather than an error.
        """
        user = require_auth(self)
        if not user:
            self._send_json({"ok": False, "message": "Unauthenticated."}, 401)
            return
        if self._rate_limited(_EXPORT_LIMITER, "change_register_export"):
            return
        from app.change_register import build_change_register_export, validate_register_date_range
        body, error = self._read_json_strict()
        if error:
            self._send_json({"ok": False, "message": error}, 400)
            return
        if body is None:
            self._send_json({"ok": False, "message": "Request body required."}, 400)
            return
        if not self._require_capability(user, "audit_export"):
            return
        date_from = str(body.get("date_from") or "").strip()
        date_to = str(body.get("date_to") or "").strip()
        source_id = str(body.get("source_id") or "").strip()
        regulator = str(body.get("regulator") or body.get("regulator_code") or "").strip()
        export_format = str(body.get("format") or "all").strip() or "all"
        # Tenancy: a named custom source may only be exported by its owner. An
        # official source (or no filter) passes through unchanged.
        if source_id and source_id not in self._entitle_source_ids(user, [source_id]):
            self._send_json(
                {"ok": False, "message": "That source is not in your plan scope."},
                403,
            )
            return
        # Default-scope tenancy guard: even with NO source_id filter, the register
        # must never surface another customer's private custom source. Exclude any
        # custom source the caller does not own from the row set unconditionally.
        excluded_source_ids = self._denied_custom_source_ids(user)
        valid, err = validate_register_date_range(date_from, date_to)
        if not valid:
            self._send_json({"ok": False, "message": err}, 400)
            return
        # RBAC Stage-2 (Part A): record the authorized change-register export.
        self._rbac_log_export(user, resource_type="change_register", resource_id=source_id)
        try:
            result = build_change_register_export(
                user_id=int(user["id"]),
                date_from=date_from,
                date_to=date_to,
                source_id=source_id,
                regulator=regulator,
                export_format=export_format,
                excluded_source_ids=excluded_source_ids,
                org_id=self._caller_org_id(user),
            )
            if result.get("status") == "error":
                self._send_json({"ok": False, **result}, 400)
            else:
                self._send_json({"ok": True, **result})
        except Exception as exc:
            logger.error("change register export error: %s", type(exc).__name__)
            self._send_json({"ok": False, "message": "Internal server error."}, 500)
