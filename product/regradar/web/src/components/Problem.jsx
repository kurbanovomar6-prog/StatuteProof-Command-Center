import { Clock, FileX, MessageSquare, Search } from 'lucide-react'

const problems = [
  {
    Icon: Search,
    iconColor: 'text-amber-200',
    iconBg: 'bg-amber-400/10 border border-amber-300/20',
    accentBg: 'bg-amber-400',
    title: 'You are checking 10+ regulator websites by hand',
    desc: 'CBUAE, VARA, DFSA, ADGM/FSRA, UAE FIU, DIFC, Ministry of Finance, Ministry of Economy — each publishes independently. There is no aggregated feed. A compliance officer doing this manually will spend two to four hours a week copying page text into a spreadsheet and hoping nothing was missed.',
  },
  {
    Icon: Clock,
    iconColor: 'text-cyan-200',
    iconBg: 'bg-cyan-400/10 border border-cyan-300/20',
    accentBg: 'bg-[#16D9F5]',
    title: 'You find out about rule changes from peers, not from a system',
    desc: "When VARA issued its updated Virtual Assets and Related Activities Regulations, some compliance teams learned about it from a consultant or a LinkedIn post — not from a live monitor on the official portal. That gap between publication and internal awareness is the window your regulator is watching.",
  },
  {
    Icon: FileX,
    iconColor: 'text-emerald-200',
    iconBg: 'bg-emerald-400/10 border border-emerald-300/20',
    accentBg: 'bg-emerald-400',
    title: 'Your board asks for evidence — your spreadsheet is not evidence',
    desc: "When the board or an internal audit asks how you track regulatory changes, a manually maintained spreadsheet with no timestamps, no source URLs, and no change history does not hold up. What they are asking for is a documented record: which source, when it changed, and what your team did in response.",
  },
  {
    Icon: MessageSquare,
    iconColor: 'text-purple-200',
    iconBg: 'bg-purple-400/10 border border-purple-300/20',
    accentBg: 'bg-purple-400',
    title: 'A raw source alert is not the same as a brief you can act on',
    desc: 'Knowing that CBUAE published something is not the same as knowing whether it affects your licence type, your AML obligations, or your customer onboarding procedures. Without relevance filtering tied to your specific profile, every alert is noise until someone reads the whole document.',
  },
]

export default function Problem() {
  return (
    <section className="py-20 bg-[#07111F]">
      <div className="max-w-6xl mx-auto px-4 sm:px-6">

        <div className="text-center mb-12">
          <div className="sp-kicker inline-flex items-center gap-2 text-amber-200 bg-amber-400/10 border border-amber-300/20 rounded-full px-4 py-1.5 text-sm font-medium mb-4">
            The compliance monitoring gap
          </div>
          <h2 className="text-3xl font-bold text-white mb-4">
            Regulatory changes do not wait for your Monday review.
          </h2>
          <p className="text-slate-400 max-w-2xl mx-auto">
            UAE financial authorities publish across federal, DIFC, ADGM, and specialist regulator layers.
            Most compliance teams are still monitoring the old way — manually, infrequently, and without a documented record.
          </p>
        </div>

        <div className="grid sm:grid-cols-2 gap-6">
          {problems.map(({ Icon, iconColor, iconBg, accentBg, title, desc }) => (
            <div
              key={title}
              className="sp-panel relative bg-[#0A1628] rounded-xl border border-slate-800 p-6 shadow-[0_18px_48px_rgba(0,0,0,0.24)] overflow-hidden transition-all duration-200 hover:-translate-y-1 hover:border-cyan-400/30"
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

        <div className="mt-12 rounded-xl border border-cyan-400/20 bg-[#0D1B2E] px-8 py-6 text-center">
          <p className="text-slate-300 text-base leading-relaxed max-w-3xl mx-auto">
            StatuteProof monitors these sources on a defined schedule and delivers a structured brief when something changes — with a source URL, timestamp, change delta, and evidence record your board can inspect.
          </p>
        </div>

      </div>
    </section>
  )
}
