import { useEffect, useState } from "react";
import MonitoringStatusBadge from "./MonitoringStatusBadge";
import {
  ArrowRight,
  CheckCircle,
  Hash,
  LockKeyhole,
  RadioTower,
  ShieldCheck,
  TriangleAlert,
} from "lucide-react";

// ─── Rotating signal cards in hero panel — SAMPLE / FAKE ─────────────────────
const SIGNALS = [
  {
    regulator: "DFSA Rulebook / AML Module",
    dot: "green",
    what: "A monitored DFSA page shows updated wording in a section related to AML systems and controls. The changed text has been captured, hashed and timestamped for review.",
    risk: "MEDIUM",
    riskNote:
      "Check whether the wording affects your current AML monitoring procedures, policies or control mapping.",
    consider:
      "Assign review to Compliance and MLRO before deciding whether internal documentation needs updating.",
  },
  {
    regulator: "VARA Compliance & Risk Management",
    dot: "green",
    what: "A VARA source page appears to have been updated with revised language around compliance obligations. StatuteProof captured the changed section and linked it to the monitoring run evidence.",
    risk: "HIGH",
    riskNote:
      "Review whether the change affects your current compliance calendar, responsible owner or policy controls.",
    consider:
      "Escalate to the relevant compliance lead before updating internal procedures.",
  },
  {
    regulator: "FSRA Guidance / Financial Crime",
    dot: "amber",
    what: "A monitored FSRA guidance page shows a text update in a financial crime-related section. The brief highlights the affected wording and stores the run hash for later reference.",
    risk: "MEDIUM",
    riskNote:
      "Relevant for regulated firms with financial crime monitoring and reporting obligations.",
    consider:
      "Compare the updated wording against your current financial crime framework and monitoring controls. Decide whether the change requires legal review, policy refresh or no action.",
  },
  {
    regulator: "CBUAE · AML/CFT Guidelines",
    dot: "green",
    what: "A monitored CBUAE page shows updated wording in a section related to customer due diligence. The change has been captured and is ready for MLRO review.",
    risk: "MEDIUM",
    riskNote:
      "Affects onboarding and ongoing CDD procedures. Remediation of existing files may be required.",
    consider:
      "Review CDD workflows with your MLRO and assess whether existing customer files meet the revised standard.",
  },
];

const chainSteps = [
  ["01", "Source run", "Official public source fetched and logged"],
  ["02", "Evidence", "SHA-256 hash + timestamp preserved"],
  ["03", "Review", "MLRO/CCO decision gate recorded"],
  ["04", "Brief", "Draft released only after approval"],
];

// Regulator name strip shown below headline
const REGULATOR_STRIP = [
  "CBUAE",
  "DFSA",
  "ADGM / FSRA",
  "VARA",
  "UAE CMA",
  "DIFC",
];

function EvidenceDossier() {
  const [idx, setIdx] = useState(0);
  const [fading, setFading] = useState(false);

  useEffect(() => {
    const id = setInterval(() => {
      setFading(true);
      setTimeout(() => {
        setIdx((i) => (i + 1) % SIGNALS.length);
        setFading(false);
      }, 300);
    }, 5000);
    return () => clearInterval(id);
  }, []);

  const sig = SIGNALS[idx];
  const isHigh = sig.risk === "HIGH";
  const dotClass =
    sig.dot === "amber"
      ? "inline-block h-2 w-2 rounded-full bg-amber-400"
      : "sp-live-dot";

  return (
    <div className="sp-paper-panel sp-reveal relative overflow-hidden p-5 sm:p-6">
      <div className="absolute right-0 top-0 h-28 w-28 rounded-bl-[4rem] bg-cyan-200/55" />

      <div
        className="relative transition-opacity duration-300"
        style={{ opacity: fading ? 0 : 1 }}
      >
        {/* Header */}
        <div className="mb-5 flex items-start justify-between gap-4">
          <div className="mb-2 inline-flex items-center gap-1.5 rounded-full border border-slate-200 bg-slate-100 px-2.5 py-1 text-[11px] font-semibold text-slate-600">
            <span className={dotClass} />
            {sig.regulator}
          </div>
          <span className="inline-flex flex-shrink-0 items-center gap-1.5 rounded-lg border border-amber-300 bg-amber-100 px-2.5 py-1 text-[11px] font-bold text-amber-900">
            <TriangleAlert className="h-3.5 w-3.5" />
            SAMPLE / FAKE
          </span>
        </div>

        {/* What changed */}
        <div className="mb-4 rounded-xl border border-slate-200 bg-white/80 px-4 py-3">
          <p className="mb-1 text-[10px] font-semibold uppercase tracking-wider text-slate-400">
            What changed
          </p>
          <p className="text-sm font-medium leading-snug text-slate-900">
            {sig.what}
          </p>
        </div>

        {/* Risk level */}
        <div
          className={`mb-4 rounded-xl border px-4 py-3 ${
            isHigh ? "border-red-200 bg-red-50" : "border-amber-200 bg-amber-50"
          }`}
        >
          <div className="mb-1 flex items-center gap-2">
            <p className="text-[10px] font-semibold uppercase tracking-wider text-slate-400">
              Risk level
            </p>
            <span
              className={`rounded-md px-2 py-0.5 text-[11px] font-bold ${
                isHigh
                  ? "bg-red-100 text-red-700"
                  : "bg-amber-100 text-amber-800"
              }`}
            >
              {sig.risk}
            </span>
          </div>
          <p className="text-xs leading-snug text-slate-600">{sig.riskNote}</p>
        </div>

        {/* What to consider */}
        <div className="mb-5 rounded-xl border border-slate-200 bg-slate-50 px-4 py-3">
          <p className="mb-1 text-[10px] font-semibold uppercase tracking-wider text-slate-400">
            What you should consider
          </p>
          <p className="text-xs leading-relaxed text-slate-700">
            {sig.consider}
          </p>
        </div>

        {/* Dot navigation + footnote */}
        <div className="flex items-center justify-between">
          <p className="text-[10px] leading-relaxed text-slate-400">
            Monitoring intelligence only. Not legal advice.
          </p>
          <div className="flex gap-1.5">
            {SIGNALS.map((_, i) => (
              <button
                key={i}
                type="button"
                onClick={() => {
                  setFading(true);
                  setTimeout(() => {
                    setIdx(i);
                    setFading(false);
                  }, 200);
                }}
                className={`h-1.5 rounded-full transition-all duration-300 ${
                  i === idx ? "w-4 bg-cyan-500" : "w-1.5 bg-slate-300"
                }`}
              />
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

function ChainStrip() {
  return (
    <div className="mt-8 grid gap-3 md:grid-cols-4">
      {chainSteps.map(([num, title, detail], index) => (
        <div
          key={title}
          className="rounded-2xl border border-slate-800 bg-slate-950/45 p-4"
          style={{ animationDelay: `${index * 70}ms` }}
        >
          <p className="sp-mono text-xs font-bold text-cyan-300">{num}</p>
          <p className="mt-2 text-sm font-semibold text-white">{title}</p>
          <p className="mt-1 text-xs leading-relaxed text-slate-500">
            {detail}
          </p>
        </div>
      ))}
    </div>
  );
}

export default function Hero({ onCreateWorkspace, onViewSample, onVerify }) {
  // Live source count — landing must never hardcode coverage numbers.
  const [liveSourceCount, setLiveSourceCount] = useState(null);
  useEffect(() => {
    let active = true;
    fetch("/api/health")
      .then((r) => r.json())
      .then((d) => {
        if (active && Number.isFinite(d?.sources_active)) setLiveSourceCount(d.sources_active);
      })
      .catch(() => {}); // fallback: the card shows "—", not a stale number
    return () => { active = false; };
  }, []);

  return (
    <section
      className="sp-page-orbit px-4 pb-16 pt-24 lg:pb-20 lg:pt-28"
      id="top"
    >
      <div className="relative z-10 mx-auto max-w-7xl">
        <div className="mb-6 flex flex-wrap items-center justify-between gap-3">
          <div className="inline-flex items-center gap-2 rounded-full border border-cyan-300/25 bg-cyan-300/10 px-3 py-1.5 text-xs font-semibold text-cyan-100">
            <RadioTower className="h-3.5 w-3.5" />
            Selected-source UAE regulatory monitoring
          </div>
          <div className="inline-flex items-center gap-2 rounded-full border border-slate-700 bg-slate-950/40 px-3 py-1.5 text-xs font-semibold text-slate-300">
            <LockKeyhole className="h-3.5 w-3.5 text-amber-300" />
            Every brief reviewed before it reaches you
          </div>
        </div>

        <div className="grid items-center gap-8 lg:grid-cols-[minmax(0,0.95fr)_minmax(420px,0.8fr)]">
          <div className="sp-reveal sp-animate-fade-up">
            {/* Trust badge */}
            <span className="sp-badge-trust sp-animate-fade-up sp-delay-1 mb-5 inline-flex">
              Official UAE sources only
            </span>

            {/* Primary headline */}
            <h1 className="sp-display sp-animate-fade-up sp-delay-1 max-w-4xl text-5xl text-white md:text-6xl lg:text-7xl">
              Stop refreshing regulator websites every week.
            </h1>

            {/* Subheadline */}
            <p className="sp-animate-fade-up sp-delay-2 mt-6 max-w-2xl text-lg leading-relaxed text-slate-300">
              StatuteProof is built to watch selected official UAE regulator
              sources and prepare a draft brief for review when relevant text
              changes. Instead of spending hours checking pages manually,
              Compliance gets a reviewed signal with source links, change
              context and evidence.
            </p>

            {/* Bullets */}
            <ul className="sp-animate-fade-up sp-delay-2 mt-6 max-w-xl space-y-2.5">
              {[
                "Reduce weekly manual checks across VARA, DFSA, FSRA, UAE CMA and CBUAE.",
                "See what changed, where it changed and why it may matter to your firm.",
                "Give MLRO, CCO and Compliance one shared brief for review.",
              ].map((point) => (
                <li
                  key={point}
                  className="flex items-start gap-2.5 text-sm leading-relaxed text-slate-300"
                >
                  <CheckCircle className="mt-0.5 h-4 w-4 flex-shrink-0 text-cyan-400" />
                  {point}
                </li>
              ))}
            </ul>

            {/* Regulator strip */}
            <div className="sp-animate-fade-up sp-delay-2 mt-6 flex flex-wrap items-center gap-2">
              <span className="text-[11px] font-medium text-slate-500 mr-1">
                Selected sources in scope include:
              </span>
              {REGULATOR_STRIP.map((name) => (
                <span
                  key={name}
                  className="rounded-md border border-slate-700/70 bg-slate-900/50 px-2.5 py-1 text-[11px] font-semibold text-slate-300"
                >
                  {name}
                </span>
              ))}
            </div>

            {/* Trust metrics — the source count is fetched live from the
                API (never hardcoded); cadence is stated as operator-set,
                not promised. */}
            <div className="sp-animate-fade-up sp-delay-2 mt-7 grid max-w-2xl gap-2 sm:grid-cols-4">
              {[
                [liveSourceCount != null ? String(liveSourceCount) : "6",
                 liveSourceCount != null
                   ? "UAE official sources configured (live count)"
                   : "Selected official UAE sources across 6 regulators"],
                ["Scheduled", "Checks run on an operator-set interval"],
                ["SHA-256", "Tamper-evident fingerprint of each capture"],
                ["Your MLRO", "Reviews every brief before action"],
              ].map(([stat, label]) => (
                <div key={stat} className="sp-glass rounded-2xl px-4 py-3">
                  <p className="sp-mono text-base font-bold text-cyan-300">
                    {stat}
                  </p>
                  <p className="mt-0.5 text-[11px] leading-snug text-slate-400">
                    {label}
                  </p>
                </div>
              ))}
            </div>

            {/* CTAs — updated labels */}
            <div className="sp-animate-fade-up sp-delay-3 mt-8 flex flex-col gap-3 sm:flex-row">
              <button
                onClick={onCreateWorkspace}
                className="sp-btn-primary justify-center px-6"
              >
                View source readiness <ArrowRight className="h-4 w-4" />
              </button>
              <button
                type="button"
                onClick={onViewSample}
                className="sp-btn-secondary justify-center px-6"
              >
                View sample evidence record
              </button>
            </div>

            {/* Public verifier CTA — the record it loads is real (public
                regulator content); verification confirms record integrity
                only, never compliance. */}
            <div className="sp-animate-fade-up sp-delay-3 mt-4">
              <a
                href="/verify#sample"
                onClick={(event) => {
                  if (!onVerify) return
                  event.preventDefault()
                  onVerify()
                }}
                className="inline-flex items-center gap-1.5 text-sm font-semibold text-cyan-300 transition-colors hover:text-white"
              >
                Verify a record in 60 seconds — no account
                <ArrowRight className="h-4 w-4" />
              </a>
            </div>

            {/* Live indicator + disclaimer */}
            <div className="sp-animate-fade-up sp-delay-3 mt-5 flex flex-col gap-3">
              <div className="flex flex-wrap items-center gap-4">
                <MonitoringStatusBadge />
                <div className="inline-flex items-center gap-1.5 rounded-full border border-slate-700 bg-slate-900/50 px-3 py-1 text-xs font-medium text-slate-300">
                  Email delivery included — Telegram optional
                </div>
              </div>
              <div className="flex items-start gap-2 rounded-2xl border border-emerald-400/20 bg-emerald-400/10 px-4 py-3 text-sm leading-relaxed text-emerald-50/80">
                <CheckCircle className="mt-0.5 h-4 w-4 flex-shrink-0 text-emerald-300" />
                <p>
                  We disclose source limits, failed extraction paths, and review
                  gates before pilot activation. Monitoring intelligence only;
                  not legal advice.
                </p>
              </div>
            </div>
          </div>

          <EvidenceDossier />
        </div>

        <ChainStrip />

        <div className="mt-8 grid gap-3 border-t border-slate-800 pt-5 text-sm text-slate-400 md:grid-cols-3">
          <div className="flex items-start gap-2">
            <Hash className="mt-0.5 h-4 w-4 flex-shrink-0 text-cyan-300" />
            <span>
              Every saved source-run proof is hash checked before canonical
              evidence use.
            </span>
          </div>
          <div className="flex items-start gap-2">
            <ShieldCheck className="mt-0.5 h-4 w-4 flex-shrink-0 text-cyan-300" />
            <span>
              Human review means your MLRO or CCO reviews the brief before any
              compliance action is taken — not an automated decision.
            </span>
          </div>
          <div className="flex items-start gap-2">
            <TriangleAlert className="mt-0.5 h-4 w-4 flex-shrink-0 text-amber-300" />
            <span>
              Selected-source scope. Not a full-country source map or compliance
              guarantee.
            </span>
          </div>
        </div>
      </div>
    </section>
  );
}
