"""Evidence-record + audit-export request handlers, extracted from ``app.api``.

This module holds one cohesive slice of the HTTP surface — the evidence list,
per-run diff, per-record review/history/assess, the audit-pack export
(get/download/post) and its private ``_write_evidence_export`` writer, the
review queue, the canonical-evidence read, and the owner-scoped audit-log read —
as a mixin that ``app.api._Handler`` inherits. The method bodies are
byte-identical to their former inline definitions; only their host class/file
changed.

Names the moved bodies read as bare globals are imported here FROM ``app.api``
so they are the SAME objects the rest of the handler uses (and so tests that
monkeypatch ``app.api_evidence.<name>`` steer these methods exactly as they
previously steered ``app.api.<name>``). ``BASE_DIR`` / ``_EXPORT_LIMITER`` are
imported here as SEPARATE bindings, so a test that repoints them on ``app.api``
must ALSO repoint them on ``app.api_evidence`` for the moved handlers to see the
change. The function-local imports inside bodies (``from app.source_runs
import …``, ``from app.evidence_assessment import …``, ``from app.review_queue
import …``, ``from app.audit_export import …``, ``from app.source_health_timeline
import …``) resolve at call time against their source modules. Shared
per-request helpers (``_send_json``, ``_rate_limited``, ``_rbac_guard``,
``_read_json_strict``, ``_denied_custom_source_ids``, ``_source_visible_to``,
``_evidence_source_out_of_scope``, ``_caller_org_id``, ``_require_capability``,
``_rbac_log_export``) stay on ``_Handler`` and are reached through ``self``.
"""
from __future__ import annotations

from app.api import (
    BASE_DIR,
    _CANONICAL_EVIDENCE_LIMITER,
    _EVIDENCE_LIST_LIMITER,
    _EXPORT_LIMITER,
    _SECURITY_HEADERS,
    _cors_headers,
    _official_alert_blocked_by_plan,
    _truthy_param,
    json,
    logger,
    parse_qs,
    rbac_runtime,
    require_auth,
    urlparse,
)


class _EvidenceHandlerMixin:
    """Evidence-record + audit-export request handlers for ``_Handler``."""

    def _handle_evidence_list(self) -> None:
        """GET /api/evidence — returns source run records from source_runs.jsonl."""
        user = require_auth(self)
        if not user:
            self._send_json({"ok": False, "message": "Unauthenticated."}, 401)
            return
        if self._rate_limited(_EVIDENCE_LIST_LIMITER, "evidence_list"):
            return
        try:
            params = parse_qs(urlparse(self.path).query)
            market = str((params.get("market") or ["AE"])[0]).upper().strip() or "AE"
            limit_raw = (params.get("limit") or ["50"])[0]
            try:
                limit = max(1, min(int(limit_raw), 200))
            except (TypeError, ValueError):
                limit = 50

            # Cross-tenant scope: evidence rows carry source_name + official_url,
            # so a victim's private custom source must not surface here to another
            # authenticated caller. Drop runs whose source_id is a custom source
            # this user does not own (official sources are never denied).
            denied_source_ids = self._denied_custom_source_ids(user)

            from app.source_runs import is_skipped_cycle

            runs_path = BASE_DIR / "data" / "source_runs" / "source_runs.jsonl"
            records: list[dict] = []
            if runs_path.exists():
                with runs_path.open(encoding="utf-8") as fh:
                    for line in fh:
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            rec = json.loads(line)
                        except json.JSONDecodeError:
                            continue
                        if str(rec.get("source_id") or "").strip() in denied_source_ids:
                            continue
                        if str(rec.get("market") or rec.get("jurisdiction") or "").upper() == market:
                            records.append({
                                "run_id": rec.get("run_id"),
                                "evidence_record_id": rec.get("run_id"),
                                "source_id": rec.get("source_id"),
                                "source_name": rec.get("source_name") or rec.get("name"),
                                "official_url": rec.get("official_url") or rec.get("final_url"),
                                "change_status": rec.get("change_status"),
                                "access_status": rec.get("access_status"),
                                "extraction_quality": rec.get("extraction_quality"),
                                "extracted_chars": rec.get("extracted_chars", 0),
                                "normalized_hash": rec.get("normalized_hash"),
                                "raw_hash": rec.get("raw_hash"),
                                "content_hash": rec.get("content_hash") or rec.get("normalized_hash"),
                                "proof_block_path": rec.get("proof_block_path"),
                                "diff_json_path": rec.get("diff_json_path"),
                                "diff_md_path": rec.get("diff_md_path"),
                                "snapshot_normalized_path": rec.get("snapshot_normalized_path"),
                                "timestamp_utc": rec.get("timestamp_utc") or rec.get("run_at"),
                                "category": rec.get("category"),
                                "error": rec.get("error"),
                                # A CIRCUIT_OPEN record documents a cycle the
                                # monitor SKIPPED — no request was issued. Left
                                # unlabelled it reads as an ordinary
                                # failed-extraction evidence row, and the one
                                # field that explains it (limitations_notes)
                                # never reached the customer.
                                "not_fetched_this_cycle": is_skipped_cycle(rec),
                                "limitations_notes": rec.get("limitations_notes"),
                            })

            records.sort(key=lambda r: r.get("timestamp_utc") or "", reverse=True)
            self._send_json({
                "ok": True,
                "market": market,
                "evidence": records[:limit],
                "total": len(records),
                "disclaimer": "Not legal advice. For monitoring information only.",
            })
        except Exception as exc:
            logger.error("evidence list failed: %s", type(exc).__name__)
            self._send_json({"ok": False, "message": "Internal server error."}, 500)

    def _handle_evidence_diff_get(self) -> None:
        """GET /api/evidence/diff?run_id=<run_id> — returns diff.md text for the given run."""
        user = require_auth(self)
        if not user:
            self._send_json({"ok": False, "message": "Unauthenticated."}, 401)
            return
        params = parse_qs(urlparse(self.path).query)
        run_id = str((params.get("run_id") or [""])[0]).strip()
        if not run_id:
            self._send_json({"ok": False, "message": "run_id is required."}, 400)
            return
        try:
            runs_path = BASE_DIR / "data" / "source_runs" / "source_runs.jsonl"
            diff_md_path: str | None = None
            diff_json_path: str | None = None
            run_source_id: str = ""
            if runs_path.exists():
                with runs_path.open(encoding="utf-8") as fh:
                    for line in fh:
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            rec = json.loads(line)
                        except json.JSONDecodeError:
                            continue
                        if rec.get("run_id") == run_id:
                            diff_md_path = rec.get("diff_md_path")
                            diff_json_path = rec.get("diff_json_path")
                            run_source_id = str(rec.get("source_id") or "").strip()
                            break
            # Tenancy: a diff for another tenant's private custom source must not
            # leak. Return the SAME 404 as "no diff" so the response never
            # confirms the run exists for a source the caller cannot see.
            if run_source_id and not self._source_visible_to(user, run_source_id):
                self._send_json({"ok": False, "message": "No diff available for this run."}, 404)
                return
            # Entitlement: the diff body IS the paid official-source deliverable
            # — the same content the preview redacts and the redline refuses.
            # run_ids are discoverable through GET /api/evidence, so leaving this
            # ungated kept the boundary open. Same flag, same eligibility helper;
            # own custom sources and the listing metadata stay readable.
            if _official_alert_blocked_by_plan(int(user["id"]), run_source_id):
                self._send_json({
                    "ok": False,
                    "message": "Official-source diff text requires an active plan.",
                    "reason": "plan_required",
                }, 402)
                return
            if not diff_md_path and not diff_json_path:
                self._send_json({"ok": False, "message": "No diff available for this run."}, 404)
                return
            candidate = diff_md_path or diff_json_path
            if not candidate:  # guaranteed by the check above; narrows type for Pyright
                self._send_json({"ok": False, "message": "No diff available for this run."}, 404)
                return
            full_path = BASE_DIR / candidate
            if not full_path.exists():
                self._send_json({"ok": False, "message": "Diff file not found on disk."}, 404)
                return
            diff_text = full_path.read_text(encoding="utf-8")
            self._send_json({
                "ok": True,
                "run_id": run_id,
                "diff_text": diff_text,
                "disclaimer": "Monitoring intelligence only. Not legal advice.",
            })
        except Exception as exc:
            logger.error("evidence diff fetch failed: %s", type(exc).__name__)
            self._send_json({"ok": False, "message": "Internal server error."}, 500)

    def _handle_evidence_review_get(self) -> None:
        user = require_auth(self)
        if not user:
            self._send_json({"ok": False, "message": "Unauthenticated."}, 401)
            return
        params = parse_qs(urlparse(self.path).query)
        evidence_id = str((params.get("evidence_record_id") or params.get("run_id") or [""])[0]).strip()
        if not evidence_id:
            self._send_json({"ok": False, "message": "evidence_record_id is required."}, 400)
            return
        if self._evidence_source_out_of_scope(user, evidence_id):
            self._send_json({"ok": False, "message": "That evidence record is not in your scope."}, 403)
            return
        try:
            from app.evidence_assessment import latest_assessment_for

            # Scope to the caller's org — assessment notes are private per-tenant.
            assessment = latest_assessment_for(evidence_id, org_id=self._caller_org_id(user))
            self._send_json({
                "ok": True,
                "evidence_record_id": evidence_id,
                "assessment": assessment,
                "disclaimer": "Monitoring intelligence only. Not legal advice.",
            })
        except Exception as exc:
            logger.error("evidence review load failed: %s", type(exc).__name__)
            self._send_json({"ok": False, "message": "Internal server error."}, 500)

    def _handle_evidence_review_history_get(self) -> None:
        user = require_auth(self)
        if not user:
            self._send_json({"ok": False, "message": "Unauthenticated."}, 401)
            return
        params = parse_qs(urlparse(self.path).query)
        evidence_id = str((params.get("evidence_record_id") or params.get("run_id") or [""])[0]).strip()
        if not evidence_id:
            self._send_json({"ok": False, "message": "evidence_record_id is required."}, 400)
            return
        if self._evidence_source_out_of_scope(user, evidence_id):
            self._send_json({"ok": False, "message": "That evidence record is not in your scope."}, 403)
            return
        try:
            from app.source_health_timeline import build_evidence_review_history

            history = build_evidence_review_history(evidence_id, org_id=self._caller_org_id(user))
            self._send_json(history)
        except ValueError as exc:
            self._send_json({"ok": False, "message": str(exc)}, 400)
        except Exception as exc:
            logger.error("evidence review-history load failed: %s", type(exc).__name__)
            self._send_json({"ok": False, "message": "Internal server error."}, 500)

    def _handle_evidence_assess(self) -> None:
        user = require_auth(self)
        if not user:
            self._send_json({"ok": False, "message": "Unauthenticated."}, 401)
            return
        # RBAC Stage-2: writing an evidence assessment is a review write. Owner
        # passes; a read-only auditor seat is denied 403. No-op for accounts today.
        if not self._rbac_guard(user, rbac_runtime.REVIEW_SUBMIT, resource_type="review"):
            return
        body, error = self._read_json_strict()
        if error:
            self._send_json({"ok": False, "message": error}, 400)
            return
        if body is None:
            self._send_json({"ok": False, "message": "Request body required."}, 400)
            return
        assess_evidence_id = str(body.get("evidence_record_id") or body.get("run_id") or "").strip()
        # IDOR guard: a reviewer must not write an assessment against another
        # tenant's private custom-source evidence record.
        if assess_evidence_id and self._evidence_source_out_of_scope(user, assess_evidence_id):
            self._send_json({"ok": False, "message": "That evidence record is not in your scope."}, 403)
            return
        try:
            from app.evidence_assessment import create_assessment

            assessment = create_assessment(
                evidence_record_id=assess_evidence_id,
                impact_level=str(body.get("impact_level") or "").strip(),
                internal_note=str(body.get("internal_note") or body.get("note") or "").strip(),
                next_action=str(body.get("next_action") or "").strip(),
                reviewer_user_id=int(user["id"]),
                reviewer_name=str(user.get("full_name") or user.get("email") or "Reviewer"),
                org_id=self._caller_org_id(user),
            )
            self._send_json({"ok": True, "assessment": assessment}, 201)
        except ValueError as exc:
            self._send_json({"ok": False, "message": str(exc)}, 400)
        except Exception as exc:
            logger.error("evidence assess failed: %s", type(exc).__name__)
            self._send_json({"ok": False, "message": "Internal server error."}, 500)

    def _handle_evidence_export_get(self) -> None:
        user = require_auth(self)
        if not user:
            self._send_json({"ok": False, "message": "Unauthenticated."}, 401)
            return
        if self._rate_limited(_EXPORT_LIMITER, "evidence_export"):
            return
        params = parse_qs(urlparse(self.path).query)
        evidence_id = str((params.get("evidence_record_id") or params.get("run_id") or [""])[0]).strip()
        if not evidence_id:
            self._send_json({"ok": False, "message": "evidence_record_id is required."}, 400)
            return
        if self._evidence_source_out_of_scope(user, evidence_id):
            self._send_json({"ok": False, "message": "That evidence record is not in your scope."}, 403)
            return
        export_format = (str((params.get("format") or ["md_html"])[0]).strip().lower() or "md_html")
        # Paywall: the per-record audit pack is a paid deliverable and is gated
        # exactly like every bulk export (audit vault, evidence pack, monthly
        # assurance). A free evidence_preview account has audit_export/pdf_export
        # off and is rejected here before any export work happens.
        if not self._require_capability(user, "audit_export"):
            return
        if export_format in {"pdf", "application/pdf"} and not self._require_capability(user, "pdf_export"):
            return
        # RBAC Stage-2 (Part A): record the authorized evidence export. Additive
        # audit only — never blocks or alters the export.
        self._rbac_log_export(user, resource_id=evidence_id)
        customer_delivery = _truthy_param((params.get("customer_delivery") or ["false"])[0])
        self._write_evidence_export(
            evidence_id,
            export_format=export_format,
            customer_delivery=customer_delivery,
            org_id=self._caller_org_id(user),
        )

    def _handle_evidence_export_download(self) -> None:
        """GET /api/evidence/export-download?evidence_record_id=<id>&format=<pdf|md_html>
        Writes the audit pack and streams the output file to the browser as a download.
        """
        user = require_auth(self)
        if not user:
            self._send_json({"ok": False, "message": "Unauthenticated."}, 401)
            return
        if self._rate_limited(_EXPORT_LIMITER, "evidence_export"):
            return
        params = parse_qs(urlparse(self.path).query)
        evidence_id = str((params.get("evidence_record_id") or params.get("run_id") or [""])[0]).strip()
        if not evidence_id:
            self._send_json({"ok": False, "message": "evidence_record_id is required."}, 400)
            return
        if self._evidence_source_out_of_scope(user, evidence_id):
            self._send_json({"ok": False, "message": "That evidence record is not in your scope."}, 403)
            return
        export_format = (str((params.get("format") or ["md_html"])[0]).strip().lower() or "md_html")
        # Paywall: same paid-export gate as the bulk endpoints (see _handle_evidence_export_get).
        if not self._require_capability(user, "audit_export"):
            return
        if export_format in {"pdf", "application/pdf"} and not self._require_capability(user, "pdf_export"):
            return
        # RBAC Stage-2 (Part A): record the authorized evidence export/download.
        self._rbac_log_export(user, resource_id=evidence_id)
        try:
            from app.audit_export import write_audit_pack, write_audit_pack_pdf
            from app.evidence_assessment import find_evidence_record, latest_assessment_for

            record = find_evidence_record(evidence_id)
            assessment = latest_assessment_for(evidence_id, org_id=self._caller_org_id(user))

            want_pdf = export_format in {"pdf", "application/pdf"}
            if want_pdf:
                paths = write_audit_pack_pdf(record, assessment=assessment)
                file_path = BASE_DIR / paths["pdf_path"]
                content_type = "application/pdf"
                filename = file_path.name
            else:
                paths = write_audit_pack(record, assessment=assessment)
                file_path = BASE_DIR / paths["md_path"]
                content_type = "text/markdown; charset=utf-8"
                filename = file_path.name

            if not file_path.exists():
                self._send_json({"ok": False, "message": "Export file was not generated."}, 500)
                return

            data = file_path.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Disposition", f'attachment; filename="{filename}"')
            self.send_header("Content-Length", str(len(data)))
            for k, v in _cors_headers(self.headers.get("Origin")).items():
                self.send_header(k, v)
            for k, v in _SECURITY_HEADERS.items():
                self.send_header(k, v)
            self.end_headers()
            self.wfile.write(data)
        except ValueError as exc:
            self._send_json({"ok": False, "message": str(exc)}, 400)
        except RuntimeError as exc:
            logger.warning("evidence export download runtime error: %s", type(exc).__name__)
            self._send_json({"ok": False, "message": "Internal server error."}, 500)
        except Exception as exc:
            logger.error("evidence export download failed: %s", type(exc).__name__)
            self._send_json({"ok": False, "message": "Internal server error."}, 500)

    def _handle_reviews_queue_get(self) -> None:
        """GET /api/reviews/queue — saved evidence review queue."""
        user = require_auth(self)
        if not user:
            self._send_json({"ok": False, "message": "Unauthenticated."}, 401)
            return
        params = parse_qs(urlparse(self.path).query)
        try:
            from app.review_queue import build_review_queue

            try:
                limit = int((params.get("limit") or ["50"])[0])
            except (TypeError, ValueError):
                limit = 50
            queue = build_review_queue(
                market=str((params.get("market") or ["AE"])[0]).upper().strip() or "AE",
                status=str((params.get("status") or ["pending"])[0]).strip() or "pending",
                impact_level=str((params.get("impact_level") or [""])[0]).strip() or None,
                source_health_status=str((params.get("source_health_status") or [""])[0]).strip() or None,
                change_status=str((params.get("change_status") or [""])[0]).strip() or None,
                source_id=str((params.get("source_id") or [""])[0]).strip() or None,
                excluded_source_ids=self._denied_custom_source_ids(user),
                org_id=self._caller_org_id(user),
                limit=limit,
            )
            self._send_json(queue)
        except Exception as exc:
            logger.error("reviews/queue failed: %s", type(exc).__name__)
            self._send_json({"ok": False, "message": "Internal server error."}, 500)

    def _handle_canonical_evidence_get(self) -> None:
        """GET /api/canonical-evidence — append-only canonical evidence review state."""
        if self._rate_limited(_CANONICAL_EVIDENCE_LIMITER, "canonical_evidence_get"):
            return
        user = require_auth(self)
        if not user:
            self._send_json({"ok": False, "message": "Unauthenticated."}, 401)
            return
        try:
            from app.review_queue import build_canonical_evidence_review_queue

            self._send_json(build_canonical_evidence_review_queue(
                excluded_source_ids=self._denied_custom_source_ids(user),
            ))
        except Exception as exc:
            logger.error("canonical evidence list failed: %s", type(exc).__name__)
            self._send_json({"ok": False, "message": "Internal server error."}, 500)

    def _handle_audit_log_get(self) -> None:
        """GET /api/audit-log — owner-scoped, read-only view of the append-only
        access log.

        The access log records who did what, when, allowed or denied. Until now it
        had no reader, so the record that justifies its append-only triggers could
        not be shown to a customer, an auditor, or the founder without raw SQLite.
        This returns ONLY the caller's org rows (never another tenant's) and is
        gated to the workspace owner.
        """
        user = require_auth(self)
        if not user:
            self._send_json({"ok": False, "message": "Unauthenticated."}, 401)
            return
        try:
            principal = rbac_runtime.resolve_principal(user)
            if principal.role != rbac_runtime.ROLE_OWNER:
                self._send_json(
                    {"ok": False, "message": "Only the workspace owner can view the audit log."},
                    403,
                )
                return
            # FAIL CLOSED on an unresolved org. resolve_principal yields org_id=None
            # for a brand-new solo user before backfill (role=owner) and for a
            # denied/error resolution (role=denied); either way passing org_id=None
            # to read_access_log would return EVERY tenant's rows (cross-tenant
            # disclosure). Never do a scope-less read here.
            if principal.org_id is None:
                self._send_json(
                    {"ok": False, "message": "Your workspace could not be resolved. Try again later."},
                    403,
                )
                return
            params = parse_qs(urlparse(self.path).query)
            try:
                limit = int((params.get("limit") or ["100"])[0])
            except (TypeError, ValueError):
                limit = 100
            rows = rbac_runtime.read_access_log(limit=limit, org_id=principal.org_id)
            self._send_json({
                "ok": True,
                "org_id": principal.org_id,
                "entries": rows,
                "count": len(rows),
                "disclaimer": "Read-only access log. Append-only; entries cannot be edited or deleted.",
            })
        except Exception as exc:
            logger.error("audit-log read failed: %s", type(exc).__name__)
            self._send_json({"ok": False, "message": "Internal server error."}, 500)

    def _handle_evidence_export_post(self) -> None:
        user = require_auth(self)
        if not user:
            self._send_json({"ok": False, "message": "Unauthenticated."}, 401)
            return
        if self._rate_limited(_EXPORT_LIMITER, "evidence_export"):
            return
        body, error = self._read_json_strict()
        if error:
            self._send_json({"ok": False, "message": error}, 400)
            return
        if body is None:
            self._send_json({"ok": False, "message": "Request body required."}, 400)
            return
        evidence_id = str(body.get("evidence_record_id") or body.get("run_id") or "").strip()
        if not evidence_id:
            self._send_json({"ok": False, "message": "evidence_record_id is required."}, 400)
            return
        if self._evidence_source_out_of_scope(user, evidence_id):
            self._send_json({"ok": False, "message": "That evidence record is not in your scope."}, 403)
            return
        export_format = (str(body.get("format") or "md_html").strip().lower() or "md_html")
        # Paywall: same paid-export gate as the bulk endpoints (see _handle_evidence_export_get).
        if not self._require_capability(user, "audit_export"):
            return
        if export_format in {"pdf", "application/pdf"} and not self._require_capability(user, "pdf_export"):
            return
        # RBAC Stage-2 (Part A): record the authorized evidence export.
        self._rbac_log_export(user, resource_id=evidence_id)
        customer_delivery = _truthy_param(body.get("customer_delivery"))
        self._write_evidence_export(
            evidence_id,
            export_format=export_format,
            customer_delivery=customer_delivery,
            org_id=self._caller_org_id(user),
        )

    def _write_evidence_export(
        self,
        evidence_id: str,
        *,
        export_format: str = "md_html",
        customer_delivery: bool = False,
        org_id=None,
    ) -> None:
        try:
            from app.audit_export import build_audit_pack_export_response, build_customer_audit_pack_export_response
            from app.evidence_assessment import find_evidence_record, latest_assessment_for

            if customer_delivery:
                response = build_customer_audit_pack_export_response(
                    evidence_id,
                    export_format=export_format,
                )
                self._send_json(response)
                return

            record = find_evidence_record(evidence_id)
            # Attach only the caller's own org's assessment to their audit pack.
            assessment = latest_assessment_for(evidence_id, org_id=org_id)
            response = build_audit_pack_export_response(
                record,
                assessment=assessment,
                export_format=export_format,
            )
            response["evidence_record_id"] = evidence_id
            self._send_json(response)
        except ValueError as exc:
            self._send_json({"ok": False, "message": str(exc)}, 400)
        except RuntimeError as exc:
            logger.warning("evidence export runtime error: %s", type(exc).__name__)
            self._send_json({"ok": False, "message": "Internal server error."}, 500)
        except Exception as exc:
            logger.error("evidence export failed: %s", type(exc).__name__)
            self._send_json({"ok": False, "message": "Internal server error."}, 500)
