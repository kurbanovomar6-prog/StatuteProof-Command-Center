import { Bell, Clock, CalendarDays } from 'lucide-react'

// SAMPLE / FAKE — illustrative content only, not real regulatory data

const CONSULTATIONS = [
  {
    regulator: 'DFSA',
    paper: 'CP145 — Market Conduct Rule Amendments',
    published: '2026-06-01',
    closes: '2026-07-01',
    status: 'OPEN',
    daysLeft: 7,
  },
  {
    regulator: 'ADGM FSRA',
    paper: 'Consultation on Capital Adequacy Updates',
    published: '2026-05-15',
    closes: '2026-06-15',
    status: 'CLOSED',
    daysLeft: null,
  },
  {
    regulator: 'VARA',
    paper: 'Proposed amendments to VASP Compliance Rulebook',
    published: '2026-06-10',
    closes: '2026-07-10',
    status: 'OPEN',
    daysLeft: 16,
  },
  {
    regulator: 'CBUAE',
    paper: 'Payment Services Regulatory Framework Review',
    published: '2026-04-01',
    closes: '2026-05-01',
    status: 'CLOSED',
    daysLeft: null,
  },
]

function PulsingDot() {
  return (
    <span className="relative flex h-2.5 w-2.5 shrink-0">
      <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-amber-400 opacity-60" />
      <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-amber-400" />
    </span>
  )
}

export default function ConsultationTracker() {
  return (
    <section className="bg-[#07111F] py-20" id="consultation-tracker">
      <div className="mx-auto max-w-6xl px-4 sm:px-6">

        {/* Header */}
        <div className="mb-10 text-center">
          <div className="mb-3 flex items-center justify-center gap-2">
            <span className="inline-flex items-center gap-1.5 rounded-full border border-cyan-400/20 bg-cyan-400/10 px-4 py-1.5 text-sm font-medium text-cyan-200">
              <Bell className="h-4 w-4" />
              Consultation deadline tracker
            </span>
            <span className="inline-flex items-center gap-1.5 rounded-full border border-amber-400/30 bg-amber-400/10 px-3 py-1.5 text-xs font-bold text-amber-300 uppercase tracking-wide">
              Roadmap — Q3 2026
            </span>
          </div>
          <h2 className="mb-3 text-3xl font-bold text-white">
            Consultation deadline tracker
          </h2>
          <p className="mx-auto max-w-3xl text-slate-400 text-sm leading-relaxed">
            StatuteProof detects consultation paper publications and tracks response windows.
            You receive an alert when a consultation opens and a reminder 7 days before it closes.
          </p>
        </div>

        {/* Table card */}
        <div className="mx-auto max-w-4xl rounded-2xl border border-slate-700 bg-[#0A1628] overflow-hidden shadow-[0_18px_48px_rgba(0,0,0,0.35)]">

          {/* SAMPLE badge bar */}
          <div className="flex items-center justify-between border-b border-slate-700 bg-slate-950 px-5 py-3">
            <div className="flex items-center gap-2 text-xs text-slate-400">
              <CalendarDays className="h-3.5 w-3.5" />
              <span>Consultation papers — Q2/Q3 2026</span>
            </div>
            <span className="rounded border border-amber-400/30 bg-amber-400/10 px-2 py-0.5 text-[10px] font-bold text-amber-300 uppercase tracking-wide">
              SAMPLE / FAKE
            </span>
          </div>

          {/* Table */}
          <div className="overflow-x-auto">
            <table className="w-full text-sm border-collapse">
              <thead>
                <tr className="border-b border-slate-700 bg-slate-900/50">
                  {['Regulator', 'Paper', 'Published', 'Closes', 'Status'].map(h => (
                    <th key={h} className="py-3 px-4 text-left text-[10px] font-semibold uppercase tracking-widest text-slate-400">
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {CONSULTATIONS.map((row, i) => {
                  const isOpen = row.status === 'OPEN'
                  return (
                    <tr
                      key={i}
                      className={`border-b border-slate-800 ${isOpen ? 'bg-amber-400/5' : 'opacity-60'}`}
                    >
                      <td className="py-3.5 px-4">
                        <span className={`text-xs font-semibold px-2 py-0.5 rounded ${
                          isOpen
                            ? 'text-white bg-slate-700 border border-slate-600'
                            : 'text-slate-400 bg-slate-800 border border-slate-700'
                        }`}>
                          {row.regulator}
                        </span>
                      </td>
                      <td className={`py-3.5 px-4 text-xs leading-snug max-w-[240px] ${
                        isOpen ? 'text-slate-200 font-medium' : 'text-slate-400 line-through decoration-slate-600'
                      }`}>
                        {row.paper}
                      </td>
                      <td className={`py-3.5 px-4 font-mono text-xs ${isOpen ? 'text-slate-400' : 'text-slate-600'}`}>
                        {row.published}
                      </td>
                      <td className={`py-3.5 px-4 font-mono text-xs ${isOpen ? 'text-slate-300' : 'text-slate-600 line-through decoration-slate-600'}`}>
                        {row.closes}
                      </td>
                      <td className="py-3.5 px-4">
                        {isOpen ? (
                          <div className="flex items-center gap-2">
                            <PulsingDot />
                            <span className="text-xs font-bold text-amber-300">
                              {row.daysLeft} {row.daysLeft === 1 ? 'day' : 'days'} left
                            </span>
                          </div>
                        ) : (
                          <div className="flex items-center gap-1.5">
                            <span className="h-2 w-2 rounded-full bg-slate-600 shrink-0" />
                            <span className="text-xs text-slate-400">Closed</span>
                          </div>
                        )}
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>

          {/* Footer */}
          <div className="flex items-start gap-2.5 border-t border-slate-700 bg-slate-950/50 px-5 py-4">
            <Clock className="h-4 w-4 text-amber-500 shrink-0 mt-0.5" />
            <p className="text-xs leading-relaxed text-slate-400">
              <span className="font-semibold text-slate-400">SAMPLE / FAKE — illustrative content only.</span>
              {' '}Consultation deadline tracking is on the StatuteProof product roadmap for Q3 2026.
              Monitoring intelligence only. Not legal advice.
              Consultation windows shown above are illustrative and do not reflect real regulatory deadlines.
              Verify all information against official source publications.
            </p>
          </div>

        </div>

        {/* Feature description cards */}
        <div className="mx-auto mt-6 max-w-4xl grid sm:grid-cols-3 gap-4">
          {[
            {
              icon: Bell,
              label: 'Open alert',
              desc: 'Alert sent when a new consultation paper is published by a monitored regulator.',
            },
            {
              icon: Clock,
              label: '7-day reminder',
              desc: 'Reminder delivered 7 days before the response deadline, with the paper link.',
            },
            {
              icon: CalendarDays,
              label: 'Closed confirmation',
              desc: 'Confirmation when the window closes. Response window log retained in evidence archive.',
            },
          ].map(({ icon: Icon, label, desc }) => (
            <div key={label} className="rounded-xl border border-slate-800 bg-[#0A1628] px-4 py-4 flex items-start gap-3">
              <div className="w-8 h-8 rounded-lg bg-cyan-400/10 border border-cyan-300/20 flex items-center justify-center shrink-0">
                <Icon className="w-4 h-4 text-cyan-300" />
              </div>
              <div>
                <div className="text-xs font-semibold text-white mb-1">{label}</div>
                <div className="text-xs text-slate-400 leading-relaxed">{desc}</div>
              </div>
            </div>
          ))}
        </div>

      </div>
    </section>
  )
}
