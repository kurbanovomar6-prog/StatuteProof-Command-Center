import { CheckCircle, Zap, Wrench, XCircle, Send, ScanSearch, ClipboardCheck } from 'lucide-react'
import { Badge } from './ui/Badge'
import { Card } from './ui/Card'

const STATUSES = [
  {
    key: 'ready',
    icon: CheckCircle,
    iconColor: 'text-emerald-500',
    bgColor: 'bg-emerald-50',
    borderColor: 'border-emerald-200',
    label: 'Readiness-supported',
    desc: 'The source can be connected to scheduled checks after readiness review.',
  },
  {
    key: 'limited',
    icon: Zap,
    iconColor: 'text-amber-500',
    bgColor: 'bg-amber-50',
    borderColor: 'border-amber-200',
    label: 'Limited monitoring',
    desc: 'The source is accessible but some content may require manual verification.',
  },
  {
    key: 'custom',
    icon: Wrench,
    iconColor: 'text-blue-500',
    bgColor: 'bg-blue-50',
    borderColor: 'border-blue-200',
    label: 'Adapter required',
    desc: 'The source is important but reliable monitoring requires custom configuration.',
  },
  {
    key: 'unavailable',
    icon: XCircle,
    iconColor: 'text-slate-400',
    bgColor: 'bg-slate-50',
    borderColor: 'border-slate-200',
    label: 'Source unavailable',
    desc: 'The site does not open reliably. A different official address may be needed.',
  },
]

const FLOW_STEPS = [
  {
    Icon: Send,
    n: '01',
    title: 'You submit your source list',
    desc: 'For example: a central bank website, tax authority, legal portal or official publications page.',
  },
  {
    Icon: ScanSearch,
    n: '02',
    title: 'StatuteProof tests each source',
    desc: 'The system determines how reliably a source can be connected to monitoring, whether manual checks are needed, or whether custom configuration is required.',
  },
  {
    Icon: ClipboardCheck,
    n: '03',
    title: 'You receive a clear assessment',
    desc: 'Readiness-supported · Limited monitoring · Adapter required · Source unavailable',
  },
]

const CHECK_LIST = [
  { n: '01', label: 'Whether the source can be connected',    detail: 'Availability and page loading stability' },
  { n: '02', label: 'How reliably it opens',                  detail: 'Content quality and completeness on the page' },
  { n: '03', label: 'Which sections can be tracked',          detail: 'Publications, official notices and news feeds' },
  { n: '04', label: 'Whether documents and attachments exist', detail: 'Document availability across different formats' },
  { n: '05', label: 'Whether custom configuration is needed', detail: 'Recommended status and readiness level' },
  { n: '06', label: 'What to do next',                        detail: 'Suggested next step for your compliance team' },
]

export default function SourceOnboarding() {
  return (
    <section className="py-20 bg-white" id="onboarding">
      <div className="max-w-6xl mx-auto px-4 sm:px-6">

        <div className="text-center mb-12">
          <Badge variant="blue" className="mb-4">Pre-connection check</Badge>
          <h2 className="text-3xl font-bold text-slate-900 mb-4">
            Send us your sources — StatuteProof shows what can be automated
          </h2>
          <p className="text-slate-600 max-w-2xl mx-auto">
            Submit regulator websites, ministry pages, legal portals or publication feeds.
            StatuteProof checks availability, content quality and connection reliability — without the technical details.
          </p>
        </div>

        {/* 3-step flow */}
        <div className="grid md:grid-cols-3 gap-5 mb-12">
          {FLOW_STEPS.map(({ Icon, n, title, desc }) => (
            <div key={n} className="bg-slate-50 rounded-xl border border-slate-200 p-6">
              <div className="flex items-center gap-3 mb-3">
                <div className="w-9 h-9 rounded-lg bg-blue-600 flex items-center justify-center flex-shrink-0">
                  <Icon className="w-4 h-4 text-white" />
                </div>
                <span className="text-xs font-mono text-slate-400">{n}</span>
              </div>
              <h3 className="font-semibold text-slate-800 text-sm mb-2">{title}</h3>
              <p className="text-xs text-slate-500 leading-relaxed">{desc}</p>
            </div>
          ))}
        </div>

        {/* 4 status types */}
        <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-12">
          {STATUSES.map(({ key, icon: Icon, iconColor, bgColor, borderColor, label, desc }) => (
            <Card key={key} className={`p-5 border ${borderColor} ${bgColor} flex flex-col gap-3`}>
              <Icon className={`w-5 h-5 ${iconColor}`} />
              <div>
                <h3 className="font-semibold text-slate-900 text-sm mb-1">{label}</h3>
                <p className="text-xs text-slate-600 leading-relaxed">{desc}</p>
              </div>
            </Card>
          ))}
        </div>

        {/* Dark block */}
        <div className="bg-slate-900 rounded-2xl p-8 text-white">
          <h3 className="font-semibold text-lg mb-5">What you receive after a source assessment</h3>
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4 text-sm text-slate-300">
            {CHECK_LIST.map(item => (
              <div key={item.label} className="flex gap-3">
                <span className="text-xs font-mono text-blue-400 mt-0.5 flex-shrink-0">{item.n}</span>
                <div>
                  <div className="font-medium text-white">{item.label}</div>
                  <div className="text-xs text-slate-400 mt-0.5">{item.detail}</div>
                </div>
              </div>
            ))}
          </div>

          <div className="border-t border-slate-700 mt-6 pt-5 text-xs text-slate-500">
            No bypass of access controls, no authentication attempts, no grey-area methods. Public sources only — with an honest readiness assessment.
          </div>
        </div>

      </div>
    </section>
  )
}
