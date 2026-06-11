import { CheckCircle, Radio, User2, Filter, ListChecks, Zap } from 'lucide-react'

const points = [
  'Monitors selected public regulatory sources on a scheduled basis',
  'Detects content changes and logs them as structured alert cards',
  'Explains what changed in plain English — clear for the whole compliance team',
  'Assigns a risk level to each change: High, Medium or Low',
  'Supports Telegram pairing and sample delivery during pilot setup',
  'Focuses the default workspace on UAE official source layers',
]

const VALUE_CARDS = [
  {
    Icon: User2,
    iconColor: 'text-blue-600',
    iconBg: 'bg-blue-50',
    accentBg: 'bg-blue-400',
    title: 'Custom source profile',
    desc: 'Tailored to your markets, industry and regulators',
  },
  {
    Icon: Filter,
    iconColor: 'text-violet-600',
    iconBg: 'bg-violet-50',
    accentBg: 'bg-violet-400',
    title: 'Relevant changes only',
    desc: 'No noise from jurisdictions that don\'t apply to you',
  },
  {
    Icon: ListChecks,
    iconColor: 'text-emerald-600',
    iconBg: 'bg-emerald-50',
    accentBg: 'bg-emerald-400',
    title: 'Action-ready briefs',
    desc: 'What changed, who is affected and what to do next',
  },
  {
    Icon: Zap,
    iconColor: 'text-amber-600',
    iconBg: 'bg-amber-50',
    accentBg: 'bg-amber-400',
    title: 'Telegram alerts',
    desc: 'Connected account delivery is staged after pilot validation',
  },
]

export default function Solution() {
  return (
    <section className="py-20 bg-white" id="product">
      <div className="max-w-6xl mx-auto px-4 sm:px-6">
        <div className="flex flex-col lg:flex-row items-center gap-14">

          {/* Copy */}
          <div className="flex-1">
            <div className="inline-flex items-center gap-2 text-blue-600 bg-blue-50 border border-blue-200 rounded-full px-4 py-1.5 text-sm font-medium mb-6">
              <Radio className="w-4 h-4" />
              The StatuteProof approach
            </div>
            <h2 className="text-3xl font-bold text-slate-900 mb-5">
              Automated monitoring that turns regulatory changes into clear actions.
            </h2>
            <p className="text-slate-600 mb-8 leading-relaxed">
              StatuteProof is built for compliance teams, legal departments and risk managers
              piloting UAE-first regulatory monitoring with source proof and documented limitations.
            </p>
            <ul className="space-y-3">
              {points.map(p => (
                <li key={p} className="flex items-start gap-3 text-sm text-slate-700">
                  <CheckCircle className="w-4 h-4 text-emerald-500 flex-shrink-0 mt-0.5" />
                  {p}
                </li>
              ))}
            </ul>
          </div>

          {/* 4 value cards 2×2 */}
          <div className="flex-1 grid grid-cols-2 gap-4 w-full max-w-sm mx-auto">
            {VALUE_CARDS.map(({ Icon, iconColor, iconBg, accentBg, title, desc }) => (
              <div
                key={title}
                className="relative bg-white border border-slate-200 rounded-xl p-5 shadow-sm overflow-hidden transition-all duration-200 hover:-translate-y-1 hover:shadow-md hover:border-slate-300"
              >
                <div className={`absolute top-0 left-0 right-0 h-[3px] ${accentBg}`} />
                <div className={`w-10 h-10 ${iconBg} rounded-lg flex items-center justify-center mb-3 mt-1`}>
                  <Icon className={`w-5 h-5 ${iconColor}`} />
                </div>
                <div className="text-sm font-semibold text-slate-800 leading-tight mb-1">{title}</div>
                <div className="text-xs text-slate-500 leading-relaxed">{desc}</div>
              </div>
            ))}
          </div>

        </div>
      </div>
    </section>
  )
}
