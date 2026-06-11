import { AlertTriangle, Clock, Building2, FileX, Globe } from 'lucide-react'

const problems = [
  {
    Icon: Globe,
    iconColor: 'text-cyan-200',
    iconBg: 'bg-cyan-400/10 border border-cyan-300/20',
    accentBg: 'bg-[#16D9F5]',
    title: 'Core regulatory sources are published across separate official portals',
    desc: 'CBUAE, VARA, DFSA, ADGM/FSRA, UAE FIU, Ministry of Finance, UAE Legislation Portal, DIFC Laws, Ministry of Economy — each publishes independently. There is no aggregated notification feed.',
  },
  {
    Icon: Clock,
    iconColor: 'text-amber-200',
    iconBg: 'bg-amber-400/10 border border-amber-300/20',
    accentBg: 'bg-amber-400',
    title: 'Regulatory pace in the UAE has accelerated',
    desc: "VARA's rulebook framework, the Capital Market Authority transition under Federal Decree-Law No. 32 of 2025, and ongoing AML/CFT updates mean the publication cadence is not slowing down. Manual weekly reviews create structural lag.",
  },
  {
    Icon: FileX,
    iconColor: 'text-emerald-200',
    iconBg: 'bg-emerald-400/10 border border-emerald-300/20',
    accentBg: 'bg-emerald-400',
    title: 'Not every official source is accessible the same way',
    desc: 'Some UAE regulator portals are restricted, PDF-primary, or dynamically rendered in ways that make automated extraction unreliable. A monitoring service that does not tell you its limitations cannot be trusted for compliance purposes.',
  },
  {
    Icon: Building2,
    iconColor: 'text-cyan-200',
    iconBg: 'bg-cyan-400/10 border border-cyan-300/20',
    accentBg: 'bg-cyan-400',
    title: 'A source feed is not the same as a compliance brief',
    desc: 'Knowing that CBUAE published something is not the same as knowing whether it affects your licence type, your business activity, or your AML obligations. Relevance filtering matched to your regulatory profile is what converts a source change into an actionable brief.',
  },
]

export default function Problem() {
  return (
    <section className="py-20 bg-[#07111F]">
      <div className="max-w-6xl mx-auto px-4 sm:px-6">

        <div className="text-center mb-12">
          <div className="inline-flex items-center gap-2 text-amber-200 bg-amber-400/10 border border-amber-300/20 rounded-full px-4 py-1.5 text-sm font-medium mb-4">
            <AlertTriangle className="w-4 h-4" />
            The compliance monitoring gap
          </div>
          <h2 className="text-3xl font-bold text-white mb-4">
            Regulatory changes do not announce themselves.
          </h2>
          <p className="text-slate-400 max-w-2xl mx-auto">
            UAE financial authorities publish across federal, DIFC, ADGM, and specialist regulator layers
            with no unified notification channel. Most compliance teams find out about changes the same way
            everyone else does.
          </p>
        </div>

        <div className="grid sm:grid-cols-2 gap-6">
          {problems.map(({ Icon, iconColor, iconBg, accentBg, title, desc }) => (
            <div
              key={title}
              className="relative bg-[#0A1628] rounded-xl border border-slate-800 p-6 shadow-[0_18px_48px_rgba(0,0,0,0.24)] overflow-hidden transition-all duration-200 hover:-translate-y-1 hover:border-cyan-400/30"
            >
              <div className={`absolute top-0 left-0 right-0 h-[3px] ${accentBg}`} />
              <div className={`w-10 h-10 ${iconBg} rounded-lg flex items-center justify-center mb-4 mt-1`}>
                <Icon className={`w-5 h-5 ${iconColor}`} />
              </div>
              <h3 className="font-semibold text-slate-100 mb-2">{title}</h3>
              <p className="text-sm text-slate-400 leading-relaxed">{desc}</p>
            </div>
          ))}
        </div>

      </div>
    </section>
  )
}
