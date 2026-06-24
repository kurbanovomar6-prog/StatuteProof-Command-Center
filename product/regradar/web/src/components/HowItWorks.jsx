import { MapPin, ScanLine, FileText, ShieldCheck } from "lucide-react";

const STEPS = [
  {
    n: "01",
    icon: MapPin,
    title: "We map your regulatory scope",
    desc: "You tell us which UAE regulators apply to your licence type — DFSA, CBUAE, VARA, UAE CMA, or others. We match those to the official sources we monitor and confirm which are active before your pilot begins.",
  },
  {
    n: "02",
    icon: ScanLine,
    title: "We monitor the official sources",
    desc: "StatuteProof checks each configured official source every 24 hours (high-priority regulatory sources checked twice daily) and records a timestamped evidence snapshot every monitoring run. Source access status, extraction method, and quality score are logged on every check. Each source is fetched on a 24-hour cycle. The detection timestamp, extraction quality score, and SHA-256 hash are recorded for every run — whether the content changed or not.",
  },
  {
    n: "03",
    icon: FileText,
    title: "When something changes, you get a brief",
    desc: "Detected changes produce a structured monitoring brief: what changed, which official source, when it was detected, and a risk tier. Human review means your team reviews the brief — not StatuteProof. Your MLRO or CCO is the reviewer of record. StatuteProof provides the evidence record and draft brief; your compliance professional makes the decision and their review is logged with a timestamp.",
  },
  {
    n: "04",
    icon: ShieldCheck,
    title: "Your evidence trail is preserved",
    desc: "Every monitoring run produces a cryptographic hash, a stored snapshot, and a diff record. Your compliance team can demonstrate that a source was tracked, when it was checked, and exactly what was captured.",
  },
];

export default function HowItWorks() {
  return (
    <section className="py-20 bg-[#07111F]" id="how-it-works">
      <div className="max-w-6xl mx-auto px-4 sm:px-6">
        <div className="text-center mb-14">
          <span className="sp-badge-trust mb-4 inline-flex">How it works</span>
          <h2 className="sp-heading text-3xl font-bold text-white mb-3 mt-4">
            From regulatory scope to evidence trail
          </h2>
          <p className="text-slate-400 max-w-xl mx-auto text-sm leading-relaxed">
            StatuteProof is built around one question your auditor will
            eventually ask: can you show what you were monitoring, when you
            checked it, and what it said?
          </p>
        </div>

        <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-5">
          {STEPS.map((step, i) => {
            const Icon = step.icon;
            const delays = [
              "sp-delay-1",
              "sp-delay-2",
              "sp-delay-3",
              "sp-delay-4",
            ];
            return (
              <div
                key={step.n}
                className={`sp-glass sp-animate-fade-up ${delays[i] || "sp-delay-4"} flex flex-col`}
              >
                <div className="mb-4">
                  <span className="sp-display text-4xl font-bold text-cyan-300/30 leading-none block mb-3">
                    {step.n}
                  </span>
                  <div className="w-9 h-9 rounded-lg bg-cyan-400/10 border border-cyan-300/20 flex items-center justify-center">
                    <Icon className="w-4 h-4 text-cyan-300" />
                  </div>
                </div>
                <h3 className="sp-heading font-semibold text-white text-sm mb-2 leading-snug">
                  {step.title}
                </h3>
                <p className="text-xs text-slate-400 leading-relaxed">
                  {step.desc}
                </p>
              </div>
            );
          })}
        </div>

        <div className="mt-10 text-center">
          <p className="text-[11px] text-slate-500 max-w-2xl mx-auto leading-relaxed">
            StatuteProof monitoring briefs require human review before any
            compliance or regulatory action. Not legal advice.
          </p>
        </div>
      </div>
    </section>
  );
}
