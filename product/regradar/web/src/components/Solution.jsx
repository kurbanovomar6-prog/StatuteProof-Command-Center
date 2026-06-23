import { CheckCircle, Radio, User2, Filter, ListChecks, ShieldCheck } from 'lucide-react'

const points = [
  'Monitors official UAE regulatory sources across all major licence types on a scheduled basis',
  'Detects content changes and creates a timestamped evidence record per run',
  'Generates a structured monitoring brief — what changed, which source, when',
  'Assigns a risk tier to each change: High, Medium, Low, or Non-material',
  'Every brief requires human review before delivery to your compliance team',
  'Source limitations and access constraints are disclosed before activation',
]

const VALUE_CARDS = [
  {
    Icon: User2,
    iconColor: 'text-cyan-300',
    iconBg: 'bg-cyan-400/10',
    borderColor: 'border-cyan-400/20',
    accentBg: 'bg-cyan-400',
    title: 'Scoped to your licence',
    desc: 'Alerts and briefs are matched to the regulators and sectors that apply to your business — not every UAE source.',
  },
  {
    Icon: Filter,
    iconColor: 'text-violet-300',
    iconBg: 'bg-violet-400/10',
    borderColor: 'border-violet-400/20',
    accentBg: 'bg-violet-400',
    title: 'Relevant changes only',
    desc: 'Risk tiering filters out non-material changes so your team focuses on what matters.',
  },
  {
    Icon: ListChecks,
    iconColor: 'text-emerald-300',
    iconBg: 'bg-emerald-400/10',
    borderColor: 'border-emerald-400/20',
    accentBg: 'bg-emerald-400',
    title: 'Structured monitoring briefs',
    desc: 'What changed, which official source confirmed it, and what your profile requires for review next.',
  },
  {
    Icon: ShieldCheck,
    iconColor: 'text-amber-300',
    iconBg: 'bg-amber-400/10',
    borderColor: 'border-amber-400/20',
    accentBg: 'bg-amber-400',
    title: 'Evidence on every run',
    desc: 'Cryptographic hash, stored snapshot, and diff record for every monitoring run. Verifiable, not just reported.',
  },
]

const TRUST_CREDENTIALS = [
  {
    Icon: ShieldCheck,
    label: 'SHA-256 хэширование',
    detail: 'Every source run is hash-verified before evidence storage.',
  },
  {
    Icon: CheckCircle,
    label: 'Cryptographic evidence',
    detail: 'Snapshot, hash, diff and timestamp on every monitoring run.',
  },
  {
    Icon: Radio,
    label: 'Official sources only',
    detail: 'Monitored directly from official UAE regulatory publications.',
  },
]

export default function Solution() {
  return (
    <section className="py-20 bg-[#0A1628]" id="product">
      <div className="max-w-6xl mx-auto px-4 sm:px-6">

        {/* Trust credentials strip */}
        <div className="mb-12 grid gap-3 sm:grid-cols-3 sp-animate-fade-up sp-delay-1">
          {TRUST_CREDENTIALS.map(({ Icon, label, detail }) => (
            <div key={label} className="sp-glass rounded-xl px-5 py-4 flex items-start gap-3">
              <span className="sp-badge-trust p-1.5 rounded-lg inline-flex shrink-0 mt-0.5">
                <Icon className="w-4 h-4 text-cyan-300" />
              </span>
              <div>
                <p className="text-sm font-semibold text-slate-100">{label}</p>
                <p className="mt-0.5 text-xs text-slate-400 leading-relaxed">{detail}</p>
              </div>
            </div>
          ))}
        </div>

        <div className="flex flex-col lg:flex-row items-start gap-14">

          {/* Copy */}
          <div className="flex-1 sp-animate-fade-up sp-delay-2">
            <div className="inline-flex items-center gap-2 border border-cyan-400/20 bg-cyan-400/10 rounded-full px-4 py-1.5 text-sm font-medium text-cyan-200 mb-6">
              <Radio className="w-4 h-4" />
              The StatuteProof approach
            </div>
            <h2 className="sp-heading text-3xl text-white mb-5">
              Official-source monitoring built for UAE compliance teams.
            </h2>
            <p className="text-slate-400 mb-8 leading-relaxed">
              StatuteProof monitors selected official UAE regulatory sources, detects text changes,
              preserves timestamped evidence records, and prepares structured monitoring briefs for
              your compliance team to review — before any action is taken.
            </p>
            <ul className="space-y-3">
              {points.map(p => (
                <li key={p} className="flex items-start gap-3 text-sm text-slate-300">
                  <CheckCircle className="w-4 h-4 text-emerald-400 flex-shrink-0 mt-0.5" />
                  {p}
                </li>
              ))}
            </ul>
            <p className="mt-6 text-xs text-slate-500 leading-relaxed">
              Monitoring intelligence only. Not legal advice. Not a substitute for qualified legal or compliance professionals.
            </p>
          </div>

          {/* 4 value cards 2×2 */}
          <div className="flex-1 grid grid-cols-2 gap-4 w-full max-w-sm mx-auto sp-animate-fade-up sp-delay-3">
            {VALUE_CARDS.map(({ Icon, iconColor, iconBg, borderColor, accentBg, title, desc }) => (
              <div
                key={title}
                className={`sp-glass relative rounded-xl p-5 overflow-hidden transition-all duration-200 hover:-translate-y-1 hover:shadow-[0_8px_32px_rgba(25,211,243,0.08)]`}
              >
                <div className={`absolute top-0 left-0 right-0 h-[3px] ${accentBg} opacity-60`} />
                <div className={`w-10 h-10 ${iconBg} rounded-lg flex items-center justify-center mb-3 mt-1 border ${borderColor}`}>
                  <Icon className={`w-5 h-5 ${iconColor}`} />
                </div>
                <div className="text-sm font-semibold text-slate-100 leading-tight mb-1">{title}</div>
                <div className="text-xs text-slate-400 leading-relaxed">{desc}</div>
              </div>
            ))}
          </div>

        </div>
      </div>
    </section>
  )
}
