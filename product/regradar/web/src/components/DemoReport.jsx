import { AlertTriangle, Users, Clock, FileCheck, ChevronRight, ClipboardList, Download, ExternalLink } from 'lucide-react'
import { Badge } from './ui/Badge'
import { Card, CardBody } from './ui/Card'
import { Button } from './ui/Button'

export default function DemoReport() {
  return (
    <section className="py-20 bg-slate-50" id="demo">
      <div className="max-w-6xl mx-auto px-4 sm:px-6">

        <div className="text-center mb-10">
          <h2 className="text-3xl font-bold text-slate-900 mb-3">Sample compliance brief</h2>
          <p className="text-slate-600 max-w-xl mx-auto">
            This is the type of alert card StatuteProof generates automatically after detecting a high-risk regulatory change.
          </p>
        </div>

        <div className="grid lg:grid-cols-5 gap-8 items-start max-w-5xl mx-auto">

          {/* Brief card */}
          <div className="lg:col-span-3">
            <Card>
              {/* Header */}
              <div className="bg-red-600 rounded-t-xl px-6 py-4 flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <AlertTriangle className="w-5 h-5 text-white" />
                  <span className="text-white font-bold text-lg">HIGH RISK — Action required</span>
                </div>
                <Badge variant="red" className="bg-red-800 text-red-100 border-red-700">
                  Semantic analysis
                </Badge>
              </div>

              <CardBody className="pt-6 space-y-5">

                {/* Metadata */}
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
                  {[
                    { icon: <Users className="w-4 h-4 text-slate-400" />,     label: 'Affected',        value: 'Banks, fintechs, payment providers' },
                    { icon: <Clock className="w-4 h-4 text-slate-400" />,     label: 'Deadline',        value: '15 working days' },
                    { icon: <FileCheck className="w-4 h-4 text-slate-400" />, label: 'Legal review',    value: 'Recommended' },
                  ].map(m => (
                    <div key={m.label} className="bg-slate-50 rounded-lg p-4">
                      <div className="flex items-center gap-1.5 text-xs text-slate-500 mb-1.5">
                        {m.icon}
                        <span>{m.label}</span>
                      </div>
                      <div className="text-sm font-semibold text-slate-800">{m.value}</div>
                    </div>
                  ))}
                </div>

                {/* Signal tags */}
                <div className="flex flex-wrap gap-2">
                  {[
                    { label: 'New requirement',   v: 'red' },
                    { label: 'Deadline detected', v: 'red' },
                    { label: 'Reporting impact',  v: 'yellow' },
                    { label: 'Regulatory risk',   v: 'red' },
                    { label: 'Review required',   v: 'red' },
                  ].map(t => (
                    <Badge key={t.label} variant={t.v}>{t.label}</Badge>
                  ))}
                </div>

                {/* Content */}
                <div className="border-t border-slate-100 pt-4 space-y-3">
                  <div>
                    <h4 className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-1">Summary</h4>
                    <p className="text-sm text-slate-800 font-medium">
                      New reporting requirement introduced for payment organisations.
                    </p>
                  </div>
                  <div>
                    <h4 className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-1">What changed</h4>
                    <p className="text-sm text-slate-600 leading-relaxed">
                      The reporting deadline has been reduced from 30 calendar days to 15 working days from the date of the transaction.
                      A requirement to appoint a designated compliance officer has also been added.
                    </p>
                  </div>
                  <div>
                    <h4 className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-1">Why it matters</h4>
                    <p className="text-sm text-slate-600 leading-relaxed">
                      Organisations need to prepare documentation faster. Missing the deadline may create regulatory risk
                      and expose the entity to administrative consequences.
                    </p>
                  </div>
                </div>

                {/* What to do */}
                <div className="bg-amber-50 border border-amber-200 rounded-lg p-4">
                  <h4 className="text-sm font-semibold text-amber-800 mb-2">Suggested next steps</h4>
                  <p className="text-sm text-amber-700 leading-relaxed">
                    Review the internal reporting calendar and adjust deadlines accordingly.
                    Designate a compliance officer responsible for payment operations.
                  </p>
                </div>

                {/* Action buttons (mock) */}
                <div className="flex flex-wrap gap-2 pt-1">
                  <Button size="sm" variant="outline" className="flex items-center gap-1.5">
                    <ClipboardList className="w-3.5 h-3.5" />
                    Assign task
                  </Button>
                  <Button size="sm" variant="outline" className="flex items-center gap-1.5">
                    <Download className="w-3.5 h-3.5" />
                    Download report
                  </Button>
                  <Button size="sm" variant="outline" className="flex items-center gap-1.5">
                    <ExternalLink className="w-3.5 h-3.5" />
                    Open source
                  </Button>
                </div>

                {/* Footer */}
                <div className="flex items-center gap-3 text-xs pt-1">
                  <span className="text-slate-400">StatuteProof confidence: High</span>
                  <span className="text-slate-300">·</span>
                  <div className="flex items-center gap-1 text-slate-400">
                    <ChevronRight className="w-3.5 h-3.5" />
                    <span>Demo content — not real regulatory data</span>
                  </div>
                </div>

              </CardBody>
            </Card>
          </div>

          {/* Why it works */}
          <div className="lg:col-span-2">
            <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm">
              <h3 className="font-semibold text-slate-800 mb-4">Why this format works</h3>
              <ul className="space-y-4">
                {[
                  { who: 'Leadership',       what: 'Gets the key point in 10 seconds' },
                  { who: 'Legal team',       what: 'Sees exactly what changed in the text' },
                  { who: 'Compliance team',  what: 'Receives a specific required action' },
                  { who: 'Deadline',         what: 'Surfaced separately and clearly' },
                  { who: 'Risk level',       what: 'Explained, not just labelled' },
                ].map(item => (
                  <li key={item.who} className="flex items-start gap-3">
                    <div className="w-1.5 h-1.5 rounded-full bg-blue-500 flex-shrink-0 mt-2" />
                    <div>
                      <div className="text-sm font-medium text-slate-800">{item.who}</div>
                      <div className="text-xs text-slate-500 mt-0.5">{item.what}</div>
                    </div>
                  </li>
                ))}
              </ul>
            </div>
          </div>

        </div>
      </div>
    </section>
  )
}
