import { Clock, FileX, MessageSquare, Search } from 'lucide-react'

const problems = [
  {
    Icon: Search,
    iconColor: 'text-amber-200',
    iconBg: 'bg-amber-400/10 border border-amber-300/20',
    accentBg: 'bg-amber-400',
    title: 'Six UAE regulators. No shared feed. No alert when something changes.',
    desc: 'CBUAE, VARA, DFSA, ADGM/FSRA, UAE CMA, and UAE FIU each publish independently across PDFs, web pages, and consultation portals. There is no aggregated feed. Checking them manually means two to four hours a week per compliance officer — and every site you do not check that day is a gap in your monitoring record.',
  },
  {
    Icon: Clock,
    iconColor: 'text-cyan-200',
    iconBg: 'bg-cyan-400/10 border border-cyan-300/20',
    accentBg: 'bg-[#16D9F5]',
    title: 'Your team found out about the VARA update from a LinkedIn post — not a system',
    desc: 'Regulators update rulebooks and circulars without individual notice. When a change reaches a compliance team through a consultant or a peer instead of a monitor on the official portal, the gap between the publication date and the internal awareness date is exactly what an enforcement review examines — "when did you know, and what did you do?"',
  },
  {
    Icon: FileX,
    iconColor: 'text-emerald-200',
    iconBg: 'bg-emerald-400/10 border border-emerald-300/20',
    accentBg: 'bg-emerald-400',
    title: 'Your board asks for the audit trail. A spreadsheet with no timestamps is not one.',
    desc: 'Internal audit and board risk committees are asking for documented evidence of how regulatory changes are tracked. A manually updated spreadsheet with no source URL, no timestamp, and no change delta does not constitute a monitoring record. What they need: which source, what changed, when it was detected, and what decision was made in response.',
  },
  {
    Icon: MessageSquare,
    iconColor: 'text-purple-200',
    iconBg: 'bg-purple-400/10 border border-purple-300/20',
    accentBg: 'bg-purple-400',
    title: 'A DFSA consultation closed last month. Did your team log the response decision?',
    desc: 'Knowing that CBUAE or DFSA published something is not the same as knowing whether it affects your licence category, triggers a response obligation, or requires a procedure update. Without a structured brief tied to your firm profile, every publication is noise until someone reads the full document — and consultation deadlines pass silently.',
  },
]

export default function Problem() {
  return (
    <section className="py-20 bg-[#07111F]">
      <div className="max-w-6xl mx-auto px-4 sm:px-6">

        <div className="text-center mb-12">
          <div className="sp-kicker inline-flex items-center gap-2 text-amber-200 bg-amber-400/10 border border-amber-300/20 rounded-full px-4 py-1.5 text-sm font-medium mb-4">
            The monitoring gap an enforcement review surfaces
          </div>
          <h2 className="text-3xl font-bold text-white mb-4">
            The circular was published three weeks ago. Did your MLRO know by end of day?
          </h2>
          <p className="text-slate-400 max-w-2xl mx-auto">
            UAE financial regulators publish circulars, guidance notes, and consultation papers across
            CBUAE, VARA, DFSA, ADGM/FSRA, UAE CMA, and UAE FIU — without notifying you.
            Most compliance teams are monitoring manually, infrequently, and without a documented record that holds up in an enforcement review.
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
            StatuteProof monitors selected UAE official sources on an operator-set schedule. When monitored text changes, it delivers a structured brief — source URL, change diff, detection timestamp, SHA-256 hash — with a logged MLRO review gate before anything reaches your team. Monitoring intelligence only. Not legal advice. Not complete UAE coverage.
          </p>
        </div>

      </div>
    </section>
  )
}
