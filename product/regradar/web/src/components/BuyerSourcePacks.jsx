import { ArrowRight, Layers3 } from "lucide-react";
import { SOURCE_PACKS as PACKS } from "../data/sourcePacks";

// coverage: 'strong' | 'good' | 'partial' | 'limited'
// Pack contents live in src/data/sourcePacks.js — a single structured source
// keyed off the real source_ids in product/regradar/sources.json, guarded by
// src/data/sourcePacks.test.js so a layer can never silently over-claim.

// A DISCRETE tier (segments filled of 4), never a percentage fill — the coverage
// rating is a relative tier, not a "% of sources you need" ratio (which the product
// does not measure). See the footer note.
const COVERAGE_CONFIG = {
  strong: {
    label: "Strong selected-source",
    badge: "border-emerald-400/25 bg-emerald-400/10 text-emerald-300",
    bar: "bg-emerald-400",
    segments: 4,
  },
  good: {
    label: "Good selected-source",
    badge: "border-cyan-400/25 bg-cyan-400/10 text-cyan-200",
    bar: "bg-cyan-400",
    segments: 3,
  },
  partial: {
    label: "Partial selected-source",
    badge: "border-amber-400/25 bg-amber-400/10 text-amber-300",
    bar: "bg-amber-400",
    segments: 2,
  },
  limited: {
    label: "Limited selected-source",
    badge: "border-rose-400/25 bg-rose-400/10 text-rose-300",
    bar: "bg-rose-400",
    segments: 1,
  },
};

const LAYER_DOT = {
  active: "bg-emerald-400",
  roadmap: "bg-amber-400",
  pending: "bg-amber-400",
  evidence_only: "bg-[var(--text-muted)]",
  out_of_scope: "bg-[var(--text-muted)]",
  geo_blocked: "bg-rose-400",
};

const LAYER_TEXT = {
  active: "text-[var(--text-secondary)]",
  roadmap: "text-[var(--text-muted)] italic",
  pending: "text-[var(--text-muted)]",
  evidence_only: "text-[var(--text-muted)]",
  out_of_scope: "text-[var(--text-muted)] line-through decoration-[var(--border)]",
  geo_blocked: "text-rose-400/80",
};

const LAYER_SUFFIX = {
  roadmap: " — roadmap",
  pending: " — pending validation, not alert-eligible yet",
  evidence_only: " — evidence archive, not change-monitored",
  out_of_scope: " — outside current scope",
  geo_blocked: " — geo-restricted",
};

export default function BuyerSourcePacks({ onCreateWorkspace }) {
  return (
    <section className="bg-[var(--bg-navy)] py-20" id="source-packs">
      <div className="mx-auto max-w-6xl px-4 sm:px-6">
        <div className="mb-12 max-w-3xl">
          <div className="mb-4 inline-flex items-center gap-2 rounded-full border border-cyan-400/20 bg-cyan-400/10 px-4 py-1.5 text-sm font-medium text-cyan-200">
            <Layers3 className="h-4 w-4" />
            Source packs by licence type
          </div>
          <h2 className="mb-4 text-3xl font-bold text-white">
            What's monitored for your regulatory profile
          </h2>
          <p className="text-[var(--text-secondary)]">
            Each pack shows exactly which sources are fresh-alert eligible,
            which are pending validation, and where gaps exist — before you
            commit to a pilot.
          </p>
        </div>

        {/* Legend */}
        <div className="mb-3 flex flex-wrap items-center gap-4 text-xs text-[var(--text-muted)]">
          <span className="font-semibold uppercase tracking-wide">Key:</span>
          {[
            [
              "bg-emerald-400",
              "Fresh-alert eligible — source is proof-backed and eligible for monitoring once activated",
            ],
            ["bg-amber-400", "Pending validation / roadmap"],
            ["bg-[var(--text-muted)]", "Evidence archive only"],
            ["bg-rose-400", "Geo-restricted"],
          ].map(([dot, label]) => (
            <span key={label} className="flex items-center gap-1.5">
              <span className={`h-2 w-2 rounded-full ${dot}`} />
              {label}
            </span>
          ))}
        </div>
        <p className="mb-4 text-xs text-[var(--text-muted)] max-w-2xl">
          Fresh-alert eligible means a source has passed proof-backed baseline
          validation, produces reliable text extraction, and is configured for
          checking on an operator-set cycle once monitoring is activated (target
          up to every 24h). Sources on the roadmap or pending validation are not
          delivered as alerts until they pass the same gate.
        </p>

        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {PACKS.map((pack) => {
            const cfg = COVERAGE_CONFIG[pack.coverage];
            return (
              <article
                key={pack.profile}
                className="flex flex-col rounded-xl border border-[var(--border-muted)] bg-[var(--bg-surface)] p-5 shadow-[0_18px_48px_rgba(0,0,0,0.24)]"
              >
                {/* Header */}
                <div className="mb-4">
                  <div className="flex items-start justify-between gap-2 mb-2">
                    <h3 className="text-lg font-semibold text-white">
                      {pack.profile}
                    </h3>
                    <span
                      className={`flex-shrink-0 rounded-full border px-2.5 py-0.5 text-[10px] font-semibold ${cfg.badge}`}
                    >
                      {cfg.label}
                    </span>
                  </div>
                  {/* Coverage tier — DISCRETE segments (a relative tier, not a
                      coverage percentage). */}
                  <div
                    className="mb-2 flex gap-1"
                    aria-label={`Coverage tier ${cfg.segments} of 4`}
                  >
                    {[0, 1, 2, 3].map((i) => (
                      <span
                        key={i}
                        className={`h-1 flex-1 rounded-full ${i < cfg.segments ? cfg.bar : "bg-[var(--border-muted)]"}`}
                      />
                    ))}
                  </div>
                  <p className="text-xs leading-relaxed text-[var(--text-muted)]">
                    <span className="font-semibold text-[var(--text-secondary)]">
                      Best for:
                    </span>{" "}
                    {pack.bestFor}
                  </p>
                </div>

                {/* Source layers */}
                <div className="mb-4 flex-1">
                  <p className="mb-3 text-xs font-semibold uppercase tracking-wide text-[var(--text-muted)]">
                    Source layers
                  </p>
                  <ul className="space-y-2">
                    {pack.layers.map((layer) => (
                      <li
                        key={layer.text}
                        className="flex gap-2 text-xs leading-relaxed"
                      >
                        <span
                          className={`mt-1.5 h-1.5 w-1.5 flex-shrink-0 rounded-full ${LAYER_DOT[layer.status] || "bg-[var(--text-muted)]"}`}
                        />
                        <span
                          className={
                            LAYER_TEXT[layer.status] || "text-[var(--text-secondary)]"
                          }
                        >
                          {layer.text}
                          {LAYER_SUFFIX[layer.status] ? (
                            <span className="text-[var(--text-muted)]">
                              {LAYER_SUFFIX[layer.status]}
                            </span>
                          ) : null}
                        </span>
                      </li>
                    ))}
                  </ul>
                </div>

                {/* Caveat note */}
                {pack.caveat && (
                  <div className="mb-4 rounded-lg border border-amber-400/15 bg-amber-400/5 px-3 py-2 text-[11px] leading-snug text-amber-200/80">
                    {pack.caveat}
                  </div>
                )}

                <button
                  type="button"
                  onClick={onCreateWorkspace}
                  className="inline-flex items-center justify-between gap-2 rounded-lg border border-cyan-400/25 bg-cyan-400/10 px-3 py-2 text-xs font-semibold text-cyan-200 transition-colors hover:border-cyan-300/50 hover:bg-cyan-400/15"
                >
                  Get your free source readiness review
                  <ArrowRight className="h-3.5 w-3.5" />
                </button>
              </article>
            );
          })}
        </div>

        <div className="mt-6 rounded-xl border border-[var(--border-muted)] bg-[var(--bg-navy)] p-4 text-sm leading-relaxed text-[var(--text-secondary)]">
          Source packs show the monitoring scope per licence type. Coverage
          ratings are a relative tier of how many sources are currently
          fresh-alert eligible for this profile — not regulatory significance,
          not a completeness percentage, and not a ratio of all the sources your
          firm may need. Roadmap and pending sources are not delivered to clients
          until they pass proof-backed baseline checks. Geo-restricted sources
          are documented, not hidden. Once monitoring is activated, active
          sources are checked on an operator-set cycle (target up to every 24h).
          Source check timestamps and SHA-256 hashes are stored for every run
          and available in the evidence log.
        </div>
      </div>
    </section>
  );
}
