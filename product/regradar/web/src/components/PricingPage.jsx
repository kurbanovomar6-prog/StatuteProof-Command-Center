import { useState } from "react";
import {
  CheckCircle,
  X,
  ArrowLeft,
  ArrowRight,
  HelpCircle,
} from "lucide-react";
import { CONTACT_EMAIL } from "../data/constants";
import { PLAN_CAPABILITIES } from "../data/planCapabilities";

// Evidence-retention copy is DERIVED from the single source of truth
// (planCapabilities.js retentionDays) so the pricing page can never drift from
// what the product actually enforces or from the privacy policy. See
// pricingRetention.test.jsx for the drift guard.
function retentionLabel(days) {
  if (!days || days <= 0) return "Sample only";
  if (days >= 900) return "Custom (extended) — export on demand";
  return `${days} days`;
}

// Honest feature status labels shown in the table
// ✓ = available  ✗ = not included  text = qualified/roadmap
const PLANS_DATA = [
  {
    id: "free",
    name: "Source Readiness Review",
    price: "Free",
    period: "",
    badge: "Start here",
    highlight: false,
    purpose:
      "See which official UAE sources are fresh-alert eligible, which have access limits, and which are outside current scope — for your licence profile. No live monitoring included.",
    cta: "Request source readiness review",
    ctaPrimary: false,
    features: [
      { label: "Official UAE sources", value: "0 live" },
      { label: "Monitoring cycle", value: "N/A" },
      { label: "Source readiness review", value: "Sample" },
      { label: "Sample evidence record", value: true },
      { label: "Sample brief preview", value: true },
      { label: "Evidence records (live)", value: false },
      { label: "Diff view", value: false },
      { label: "Custom sources", value: false },
      { label: "Weekly MLRO brief", value: false },
      { label: "High-risk review queue", value: false },
      { label: "MLRO response log", value: false },
      { label: "Audit binder export", value: false },
      { label: "Users", value: "1" },
      {
        label: "Evidence retention",
        value: retentionLabel(PLAN_CAPABILITIES.evidence_preview.retentionDays),
      },
      { label: "Multiple workspaces", value: false },
    ],
  },
  {
    id: "starter_pilot",
    name: "Founding Pilot",
    price: "$199",
    period: "/ month",
    badge: null,
    highlight: false,
    purpose:
      "First paid plan for early users. Up to 3 official UAE sources, evidence records, basic diff view, and weekly source status summary. Manually activated.",
    cta: "Start founding pilot",
    ctaPrimary: false,
    features: [
      { label: "Official UAE sources", value: "Up to 3" },
      {
        label: "Monitoring cycle",
        value:
          "Target once activated: up to every 24h per source; actual cadence is operator-set and confirmed at pilot onboarding",
      },
      { label: "Source readiness review", value: true },
      { label: "Evidence records", value: true },
      { label: "Diff view", value: true },
      { label: "Custom sources", value: false },
      {
        label: "Weekly MLRO brief",
        value: "Email + Telegram (source status summary)",
      },
      { label: "High-risk review queue", value: false },
      { label: "MLRO response log", value: false },
      { label: "Audit binder export", value: false },
      { label: "Users", value: "1" },
      {
        label: "Evidence retention",
        value: retentionLabel(PLAN_CAPABILITIES.starter_pilot.retentionDays),
      },
      { label: "Multiple workspaces", value: false },
    ],
  },
  {
    id: "professional",
    name: "UAE Monitor",
    price: "$399",
    period: "/ month",
    badge: "Recommended",
    highlight: true,
    purpose:
      "For MLROs and CCOs at UAE-regulated firms. Selected fresh-alert eligible official UAE sources across VARA, DFSA (rulebook platform), ADGM/FSRA, DIFC, UAE CMA, EOCN, MoF and related public sources — with evidence on each configured run. CBUAE and DFSA-site sources are currently in disclosed remediation (production access blocked).",
    cta: "Upgrade to UAE Monitor",
    ctaPrimary: true,
    features: [
      {
        label: "Official UAE sources",
        value: "Selected official endpoints after source readiness review",
      },
      {
        label: "Monitoring cycle",
        value:
          "Target once activated: up to every 24h per source (priority target 12h); actual cadence is operator-set and confirmed at pilot onboarding",
      },
      { label: "Source readiness review", value: true },
      { label: "Evidence records + full diff view", key: "Diff view", value: true },
      { label: "Custom sources", value: "Up to 2 — requires activation" },
      { label: "Weekly MLRO brief", value: "Email + Telegram" },
      { label: "High-risk review queue", value: true },
      { label: "MLRO response log", value: "Roadmap Q3 2026" },
      {
        label: "Audit binder export",
        value: "PDF audit pack + Markdown/HTML for internal compliance files",
      },
      {
        label: "PDF / Markdown export",
        value: "PDF audit pack included for saved evidence records",
      },
      { label: "Users", value: "2" },
      {
        label: "Evidence retention",
        value: retentionLabel(PLAN_CAPABILITIES.professional.retentionDays),
      },
      { label: "Multiple workspaces", value: false },
    ],
  },
  {
    id: "consultant",
    name: "Compliance Consultant",
    price: "Talk to us",
    period: "",
    badge: null,
    highlight: false,
    purpose:
      "Advisory firms managing multiple UAE-regulated clients. Custom source scope and extended retention. Multi-workspace and white-label on the roadmap.",
    cta: "Talk to us",
    ctaPrimary: false,
    features: [
      { label: "Official UAE sources", value: "Custom scope" },
      {
        label: "Monitoring cycle",
        value:
          "Target once activated: up to every 24h per source (priority target 12h); actual cadence is operator-set and confirmed at pilot onboarding",
      },
      { label: "Source readiness review", value: true },
      { label: "Evidence records + full diff view", key: "Diff view", value: true },
      { label: "Custom sources", value: "Custom — pilot roadmap" },
      { label: "Weekly MLRO brief", value: "Email + Telegram + API (roadmap)" },
      { label: "High-risk review queue", value: "Pilot roadmap" },
      { label: "MLRO response log", value: "Roadmap Q3 2026" },
      {
        label: "Audit binder export",
        value: "PDF audit pack + Markdown/HTML for internal compliance files",
      },
      { label: "White-label reports", value: "Pilot roadmap" },
      { label: "Users", value: "Custom" },
      {
        label: "Evidence retention",
        value: retentionLabel(PLAN_CAPABILITIES.consultant.retentionDays),
      },
      { label: "Multiple workspaces", value: "Pilot roadmap" },
    ],
  },
];

const COMPARISON_ROWS = [
  { label: "Official UAE sources", key: "Official UAE sources" },
  { label: "Monitoring cycle", key: "Monitoring cycle" },
  { label: "Evidence records", key: "Evidence records" },
  { label: "Diff view", key: "Diff view" },
  { label: "Custom sources", key: "Custom sources" },
  { label: "Weekly MLRO brief", key: "Weekly MLRO brief" },
  { label: "High-risk review queue", key: "High-risk review queue" },
  { label: "MLRO response log", key: "MLRO response log" },
  { label: "Audit binder export", key: "Audit binder export" },
  { label: "Multiple workspaces", key: "Multiple workspaces" },
  { label: "Evidence retention", key: "Evidence retention" },
  { label: "Legal advice included", special: "legal_advice" },
];

const FAQS = [
  {
    q: "How often is each source checked?",
    a: "Once monitoring is activated, each configured source is fetched on an operator-set schedule, agreed during pilot onboarding and disclosed in your workspace. Once activated, every run is recorded with a SHA-256 hash and timestamp regardless of whether content changed — the monitoring log shows both CHANGED and UNCHANGED runs, so the evidence trail covers checks, not just change events.",
  },
  {
    q: "Is this legal advice?",
    a: "No. StatuteProof provides official-source regulatory monitoring intelligence. Reports are for information and compliance review support only. They do not constitute legal advice, regulatory advice, or compliance determination. Consult qualified legal or compliance professionals before making regulatory decisions.",
  },
  {
    q: "How do you verify a source is actually monitored?",
    a: "Before monitoring begins, we run a source readiness check on each UAE regulatory source: is it publicly accessible, can we extract text reliably, and does the diff produce meaningful output? Sources that pass are marked fresh-alert eligible. Sources with access issues, geo-blocking, or unreliable extraction are disclosed before your pilot — not after a gap.",
  },
  {
    q: "Can I add my own sources?",
    a: "Yes — on the UAE Monitor and Consultant plans. Custom public sources require a source readiness check before monitoring begins. We document access quality, extraction method, and any known limitations before activating.",
  },
  {
    q: "What happens if a source goes down or becomes inaccessible?",
    a: "Source failures are logged in your evidence records. Every failed or degraded run is surfaced — it is never silently dropped. You are notified when a source becomes unavailable, and the limitation is recorded in your audit trail.",
  },
  {
    q: "Can consultants use it for multiple clients?",
    a: "Multi-workspace support is on the pilot roadmap for the Compliance Consultant plan. Contact us to discuss your requirements and timeline.",
  },
  {
    q: "Is billing automatic?",
    a: "No. During the founding pilot, billing is manually activated after source readiness review and pilot confirmation. No payment method is stored until billing is formally set up. You will receive advance notice before any charges.",
  },
  {
    q: "What does the audit binder export contain?",
    a: "The PDF audit binder includes: (1) a complete monitoring run log for the period — every source, every check date, CHANGED / UNCHANGED status; (2) full diff records with SHA-256 hashes for before and after states; (3) the source URL and detection timestamp for each change event; (4) the structured brief text as delivered to your team; (5) a chain integrity verification record. The binder is designed to be presented directly to a regulator, internal auditor, or board risk committee: it documents the monitoring runs that were performed; it is not a certification of completeness or compliance. Markdown and HTML exports are also available for integration into GRC systems.",
  },
  {
    q: "Which regulators are covered on the UAE Monitor plan?",
    a: "Selected-source monitoring includes fresh-alert eligible sources across VARA, DFSA, ADGM/FSRA, DIFC laws and data protection, Ministry of Finance, Executive Office for AML/CFT (EOCN) sanctions sources, UAE CMA, and related official public sources. Source access is environment-dependent and disclosed rather than assumed: some regulator websites apply access restrictions that can affect automated monitoring infrastructure — right now the CBUAE rulebook subdomain and the www.dfsa.ae website return HTTP 403 to our production infrastructure (since 11 July 2026), so those sources are disclosed as in remediation and are not counted as fresh-alert eligible — DFSA rulebook depth continues via dfsaen.thomsonreuters.com, which does work from production, so it is the www.dfsa.ae website sources, not DFSA rulebook coverage, that are restricted. Before your pilot begins, the source readiness review reports the recorded access status of every source in your pack from our monitoring infrastructure; any source we cannot reach reliably is disclosed with its access limitation and is not counted as fresh-alert eligible coverage. The UAE FIU website is currently geo-restricted from outside the UAE and is not counted in fresh-alert coverage. MoJ/UAE legislation/gazette sources remain blocked or candidate, and FTA listing sources remain candidate pending the fresh-alert gate.",
  },
];

function FeatureVal({ val }) {
  if (val === true)
    return <CheckCircle className="w-4 h-4 text-emerald-400 mx-auto" />;
  if (val === false) return <X className="w-4 h-4 text-slate-600 mx-auto" />;
  return <span className="text-xs text-slate-300">{val}</span>;
}

export default function PricingPage({
  onBack,
  onCreateWorkspace,
  onSourceReview,
  onSelectPlan,
}) {
  const [openFaq, setOpenFaq] = useState(null);

  function handleCta(plan) {
    if (plan.id === "consultant") {
      window.location.assign(
        `mailto:${CONTACT_EMAIL}?subject=Consultant%20Plan%20Enquiry`,
      );
      return;
    }
    if (plan.id === "free") {
      onSourceReview?.();
      return;
    }
    if (plan.id === "starter_pilot") {
      onSelectPlan?.("starter_pilot");
      return;
    }
    if (plan.id === "professional") {
      onSelectPlan?.("professional");
      return;
    }
    onCreateWorkspace?.();
  }

  return (
    <div className="min-h-dvh bg-[#07111F] text-slate-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 py-12">
        {/* Back */}
        <button
          onClick={onBack}
          className="flex items-center gap-1.5 text-sm text-slate-400 hover:text-white mb-8 transition-colors"
        >
          <ArrowLeft className="w-4 h-4" /> Back
        </button>

        {/* Hero */}
        <div className="text-center mb-12">
          <div className="sp-kicker mb-5">
            Manual activation after readiness review
          </div>
          <h1 className="text-4xl font-semibold text-white mb-4">
            Choose the source monitoring plan that matches your UAE compliance
            footprint
          </h1>
          <p className="text-slate-400 max-w-2xl mx-auto text-sm leading-relaxed">
            Founding pilots are manually activated after source readiness
            review. No payment method required to start. Source readiness
            validation is required before activation.
          </p>
        </div>

        {/* Plan cards */}
        <div className="grid sm:grid-cols-2 xl:grid-cols-4 gap-5 mb-16">
          {PLANS_DATA.map((plan) => (
            <div
              key={plan.id}
              className={`sp-panel p-6 flex flex-col ${
                plan.highlight
                  ? "border-[var(--accent)]/40 bg-[#16D9F5]/5 shadow-[0_0_30px_rgba(22,217,245,0.08)]"
                  : ""
              }`}
            >
              {plan.badge && (
                <div className="text-[10px] font-bold text-[var(--accent)] uppercase tracking-widest mb-2">
                  {plan.badge}
                </div>
              )}
              <h3 className="font-bold text-lg text-white mb-1">{plan.name}</h3>
              <div className="flex items-baseline gap-1 mb-3">
                <span className="text-3xl font-bold text-white">
                  {plan.price}
                </span>
                {plan.period && (
                  <span className="text-xs text-slate-400">{plan.period}</span>
                )}
              </div>
              <p className="text-xs text-slate-400 leading-relaxed mb-5 flex-1">
                {plan.purpose}
              </p>
              {plan.id === "consultant" && (
                <div className="mt-2 rounded-lg border border-cyan-400/15 bg-cyan-400/5 px-3 py-2 text-[11px] leading-snug text-cyan-200/80 mb-4">
                  <p className="font-semibold mb-1">Consultant pricing model</p>
                  <p>1–3 client workspaces: $299/workspace/month</p>
                  <p>4–9 workspaces: $199/workspace/month</p>
                  <p>10+ workspaces: $149/workspace/month</p>
                  <p className="mt-1 text-slate-400">
                    Each workspace has its own source scope, brief history, and
                    evidence log. White-label PDF export: roadmap Q4 2026. Talk
                    to us to set up your first workspace.
                  </p>
                </div>
              )}
              <button
                onClick={() => handleCta(plan)}
                className={`w-full py-2.5 rounded-lg text-sm font-semibold transition-colors ${
                  plan.ctaPrimary
                    ? "bg-[#16D9F5] hover:bg-[#11c2db] text-[#07111F]"
                    : "border border-slate-700 text-slate-300 hover:border-[var(--accent)]/40 hover:text-white"
                }`}
              >
                {plan.cta}
              </button>
            </div>
          ))}
        </div>

        {/* Feature comparison table */}
        <div className="mb-16 overflow-x-auto">
          <h2 className="text-xl font-bold text-white mb-6 text-center">
            Feature comparison
          </h2>
          <table className="w-full text-sm border-collapse min-w-[640px]">
            <thead>
              <tr className="border-b border-slate-800">
                <th className="text-left py-3 pr-4 text-slate-400 font-medium text-xs w-1/3">
                  Feature
                </th>
                {PLANS_DATA.map((p) => (
                  <th
                    key={p.id}
                    className={`text-center py-3 px-2 text-xs font-semibold ${p.highlight ? "text-[var(--accent)]" : "text-slate-300"}`}
                  >
                    {p.name}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {COMPARISON_ROWS.map((row) => (
                <tr key={row.label} className="border-b border-slate-800/50">
                  <td className="py-2.5 pr-4 text-xs text-slate-400">
                    {row.label}
                  </td>
                  {PLANS_DATA.map((p) => (
                    <td
                      key={p.id}
                      className={`py-2.5 px-2 text-center ${p.highlight ? "bg-[#16D9F5]/3" : ""}`}
                    >
                      {row.special === "legal_advice" ? (
                        <span className="text-[10px] text-slate-500">
                          No — monitoring only
                        </span>
                      ) : (
                        <FeatureVal
                          val={
                            p.features.find(
                              (f) =>
                                f.key === row.key ||
                                f.label === row.label ||
                                f.label.startsWith(row.label),
                            )?.value ?? false
                          }
                        />
                      )}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* FAQ */}
        <div className="max-w-2xl mx-auto mb-16">
          <h2 className="text-xl font-bold text-white mb-6 text-center">
            Frequently asked questions
          </h2>
          <div className="space-y-2">
            {FAQS.map((faq, i) => (
              <div
                key={i}
                className="border border-slate-800 rounded-xl overflow-hidden"
              >
                <button
                  onClick={() => setOpenFaq(openFaq === i ? null : i)}
                  className="w-full flex items-center justify-between px-4 py-3.5 text-left text-sm font-medium text-slate-200 hover:text-white"
                >
                  {faq.q}
                  <HelpCircle
                    className={`w-4 h-4 flex-shrink-0 ml-2 transition-colors ${openFaq === i ? "text-[var(--accent)]" : "text-slate-500"}`}
                  />
                </button>
                {openFaq === i && (
                  <div className="px-4 pb-4 text-xs text-slate-400 leading-relaxed border-t border-slate-800">
                    <div className="pt-3">{faq.a}</div>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* CTA section */}
        <div className="text-center bg-[#0D1B2E] border border-slate-800 rounded-2xl p-10">
          <h2 className="text-2xl font-bold text-white mb-3">
            Ready to start?
          </h2>
          <p className="text-slate-400 text-sm mb-6 max-w-lg mx-auto">
            Request a source readiness review, start a founding pilot, or talk
            to us about your UAE compliance footprint.
          </p>
          <div className="flex flex-wrap gap-3 justify-center">
            <button
              onClick={onSourceReview}
              className="sp-btn-primary inline-flex items-center gap-2"
            >
              Request source readiness review <ArrowRight className="w-4 h-4" />
            </button>
            <button
              onClick={() => onSelectPlan?.("starter_pilot")}
              className="sp-btn-secondary inline-flex items-center gap-2"
            >
              Start founding pilot
            </button>
            <a
              href={`mailto:${CONTACT_EMAIL}?subject=StatuteProof%20Enquiry`}
              className="sp-btn-secondary inline-flex items-center gap-2"
            >
              Talk to us
            </a>
          </div>
        </div>

        <p className="text-center text-xs text-slate-600 mt-8">
          Monitoring intelligence only. Not legal advice. StatuteProof does not
          determine compliance outcomes, prevent fines, or determine regulatory
          coverage. Source readiness validation required before activation.
          Features marked "pilot roadmap" are not live by default. Founding
          pilot pricing applies to the first cohort while source validation and
          brief format are being refined.
        </p>
      </div>
    </div>
  );
}
