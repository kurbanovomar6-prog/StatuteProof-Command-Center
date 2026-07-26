import {
  useReactTable,
  getCoreRowModel,
  flexRender,
  createColumnHelper,
} from '@tanstack/react-table'
import { sourceHealthRows } from '../data/mockData'
import { Badge } from './ui/Badge'
import { ShieldCheck, Clock, FileSearch, Activity, Link2, Gauge } from 'lucide-react'

const qualityLabel   = { readiness_supported: 'Fresh-alert eligible', underReview: 'Under review', geo_blocked: 'Geo-restricted — not monitored' }
const qualityVariant = { readiness_supported: 'green',                remediation: 'yellow',        geo_blocked: 'red' }
const statusLabel    = { readiness_supported: 'Fresh-alert eligible', underReview: 'Under review', geo_blocked: 'Geo-restricted — not monitored' }
const statusVariant  = { readiness_supported: 'green',                remediation: 'yellow',        geo_blocked: 'red' }
const verdictLabel   = { READINESS: 'Readiness', REVIEW: 'Review', BLOCKED: 'Blocked' }
const verdictVariant = { READINESS: 'green', BLOCKED: 'red' }
const accessVariant  = { Accessible: 'green', Limited: 'yellow' }

const col = createColumnHelper()

const columns = [
  col.accessor('name', {
    header: 'Source',
    cell: i => <span className="font-medium text-slate-200 text-sm">{i.getValue()}</span>,
  }),
  col.accessor('jurisdiction', {
    header: 'Market',
    cell: i => <span className="text-xs text-slate-400 font-mono">{i.getValue()}</span>,
  }),
  col.accessor('access', {
    header: 'Access',
    cell: i => (
      <Badge variant={accessVariant[i.getValue()] || 'slate'}>
        {i.getValue()}
      </Badge>
    ),
  }),
  col.accessor('quality', {
    header: 'Extraction quality',
    cell: i => (
      <Badge variant={qualityVariant[i.getValue()] || 'slate'}>
        {qualityLabel[i.getValue()] || i.getValue()}
      </Badge>
    ),
  }),
  col.accessor('status', {
    header: 'Status',
    cell: i => (
      <Badge variant={statusVariant[i.getValue()] || 'slate'}>
        {statusLabel[i.getValue()] || i.getValue()}
      </Badge>
    ),
  }),
  col.accessor('verdict', {
    header: 'Result',
    cell: i => (
      <Badge variant={verdictVariant[i.getValue()] || 'yellow'}>
        {verdictLabel[i.getValue()] || i.getValue()}
      </Badge>
    ),
  }),
]

const CARDS = [
  {
    icon: ShieldCheck,
    title: 'Readiness-supported / Limited / Blocked',
    desc: 'Each official source is tested for accessibility, extraction quality, and monitoring reliability.',
  },
  {
    icon: FileSearch,
    title: 'Extraction quality',
    desc: 'HTML structured content, PDF text, or page snapshot — each source’s extraction method is documented.',
  },
  {
    icon: Activity,
    title: 'Delta detection',
    desc: 'FIRST_SEEN · UNCHANGED · CHANGED · QUALITY_DROP. CHANGED surfaces for review. QUALITY_DROP triggers a human check before any alert is issued.',
  },
  {
    icon: Link2,
    title: 'Evidence trail',
    desc: 'Every alert carries source URL, timestamp, hash, extraction quality, and limitations.',
  },
]

function SourceTable() {
  "use no memo"
  const table = useReactTable({ data: sourceHealthRows, columns, getCoreRowModel: getCoreRowModel() })
  return (
    <div className="overflow-x-auto rounded-lg border border-slate-800">
      <table className="w-full text-sm">
        <thead className="bg-slate-950/70 border-b border-slate-800">
          {table.getHeaderGroups().map(hg => (
            <tr key={hg.id}>
              {hg.headers.map(h => (
                <th key={h.id} className="px-4 py-3 text-left text-xs font-semibold text-slate-400 uppercase tracking-wide">
                  {flexRender(h.column.columnDef.header, h.getContext())}
                </th>
              ))}
            </tr>
          ))}
        </thead>
        <tbody>
          {table.getRowModel().rows.map(row => (
            <tr key={row.id} className="border-b border-slate-800 last:border-0 hover:bg-slate-900/45 transition-colors">
              {row.getVisibleCells().map(cell => (
                <td key={cell.id} className="px-4 py-3">
                  {flexRender(cell.column.columnDef.cell, cell.getContext())}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

function SourceStatusSummary() {
  return (
    <>
      <div className="text-slate-300 text-sm mt-0.5">
        Configured official-source pack · source proof attached · limits disclosed
      </div>
      <div className="text-slate-400 text-xs mt-1">
        Sample run only. Registry counts live in source transparency and authenticated command-center views.
      </div>
    </>
  )
}

export default function DashboardPreview() {
  return (
    <section className="py-20 bg-[#07111F]" id="dashboard">
      <div className="max-w-6xl mx-auto px-4 sm:px-6">

        <div className="text-center mb-10">
          <span className="inline-block rounded-md border border-amber-400/25 bg-amber-400/10 px-3 py-1 text-xs font-semibold text-amber-200 uppercase tracking-widest mb-4">
            SAMPLE / DEMO - illustrative readiness snapshot
          </span>
          <h2 className="text-3xl font-bold text-white mb-3">
            A source run your team can audit
          </h2>
          <p className="text-slate-400 max-w-3xl mx-auto leading-relaxed">
            This sample shows the operating model: configured official sources are checked, meaningful changes
            are queued for human review, and every brief carries proof back to the source.
          </p>
        </div>

        <div className="rounded-2xl border border-slate-800 bg-[#0D1B2E] p-6 mb-8 shadow-[0_18px_70px_rgba(0,0,0,0.28)]">
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
            <div className="flex items-start gap-4">
              <div className="w-10 h-10 rounded-full bg-emerald-500 flex items-center justify-center flex-shrink-0">
                <ShieldCheck className="w-5 h-5 text-white" />
              </div>
              <div>
                <div className="text-white font-bold text-lg">
                  UAE monitoring — official sources
                </div>
                <SourceStatusSummary />
                <div className="text-slate-400 text-sm mt-2 max-w-3xl leading-relaxed">
                  UAE source pack status is shown as a transparency layer after readiness review.
                  Not legal advice. For monitoring information only.
                </div>
              </div>
            </div>
            <div className="text-right flex-shrink-0">
              <div className="flex items-center gap-2 text-slate-300 text-sm">
                <Clock className="w-4 h-4" />
                Monitored sources: AE
              </div>
              <div className="text-slate-400 text-xs mt-1">Changes queued for human review</div>
              <div className="text-emerald-400 text-xs mt-1 font-medium">Source proof attached</div>
            </div>
          </div>
        </div>

        <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          {CARDS.map(card => {
            const Icon = card.icon || Gauge
            return (
              <div key={card.title} className="rounded-xl border border-slate-800 bg-[#0D1B2E] p-5">
                <div className="w-10 h-10 bg-cyan-400/10 rounded-lg border border-cyan-400/20 flex items-center justify-center mb-4">
                  <Icon className="w-5 h-5 text-cyan-200" />
                </div>
                <h3 className="font-semibold text-white text-sm mb-2">{card.title}</h3>
                <p className="text-xs text-slate-400 leading-relaxed">{card.desc}</p>
              </div>
            )
          })}
        </div>

        <div className="rounded-xl border border-slate-800 bg-[#0D1B2E] p-6 shadow-[0_18px_70px_rgba(0,0,0,0.25)]">
          <h3 className="font-semibold text-white mb-1 text-sm">Sample source set</h3>
          <p className="text-xs text-slate-400 mb-4">
            Sample source set - illustrative. Remediation sources are not treated as ready until
            extraction quality is fixed and rerun.
          </p>
          <SourceTable />
        </div>

      </div>
    </section>
  )
}
