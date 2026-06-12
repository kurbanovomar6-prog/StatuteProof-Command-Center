import { useEffect, useState } from 'react'
import {
  useReactTable,
  getCoreRowModel,
  flexRender,
  createColumnHelper,
} from '@tanstack/react-table'
import { sourceHealthRows } from '../data/mockData'
import { Badge } from './ui/Badge'
import { ShieldCheck, Clock, FileSearch, Activity, Link2, Gauge } from 'lucide-react'
import { sources as sourcesApi } from '../api'

const qualityLabel   = { good: 'Stable', low_content: 'Limited', failed: 'Blocked' }
const qualityVariant = { good: 'green',  low_content: 'yellow',  failed: 'red' }
const statusLabel    = { active: 'Active', limited: 'Limited', disabled: 'Blocked' }
const statusVariant  = { active: 'green',  limited: 'yellow',  disabled: 'red' }
const verdictLabel   = { PASS: 'Pass', REVIEW: 'Review', FAIL: 'Fail' }
const accessVariant  = { Active: 'green', Limited: 'yellow', Blocked: 'red' }

const col = createColumnHelper()

const columns = [
  col.accessor('name', {
    header: 'Source',
    cell: i => <span className="font-medium text-slate-800 text-sm">{i.getValue()}</span>,
  }),
  col.accessor('jurisdiction', {
    header: 'Market',
    cell: i => <span className="text-xs text-slate-500 font-mono">{i.getValue()}</span>,
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
      <Badge variant={i.getValue() === 'PASS' ? 'green' : i.getValue() === 'REVIEW' ? 'yellow' : 'red'}>
        {verdictLabel[i.getValue()] || i.getValue()}
      </Badge>
    ),
  }),
]

const CARDS = [
  {
    icon: ShieldCheck,
    title: 'Active / Limited / Blocked',
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
    <div className="overflow-x-auto rounded-lg border border-slate-200">
      <table className="w-full text-sm">
        <thead className="bg-slate-50 border-b border-slate-200">
          {table.getHeaderGroups().map(hg => (
            <tr key={hg.id}>
              {hg.headers.map(h => (
                <th key={h.id} className="px-4 py-3 text-left text-xs font-semibold text-slate-500 uppercase tracking-wide">
                  {flexRender(h.column.columnDef.header, h.getContext())}
                </th>
              ))}
            </tr>
          ))}
        </thead>
        <tbody>
          {table.getRowModel().rows.map(row => (
            <tr key={row.id} className="border-b border-slate-100 last:border-0 hover:bg-slate-50 transition-colors">
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
  const [statusData, setStatusData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    let active = true
    sourcesApi.status('AE')
      .then(data => { if (active) setStatusData(data) })
      .catch(() => { if (active) setError(true) })
      .finally(() => { if (active) setLoading(false) })
    return () => { active = false }
  }, [])

  if (loading) {
    return (
      <div className="text-slate-300 text-sm mt-0.5">
        Loading source status...
      </div>
    )
  }

  if (error || !statusData) {
    return (
      <div className="text-slate-300 text-sm mt-0.5">
        Could not load source status
      </div>
    )
  }

  const { summary, total_sources, last_run_at } = statusData
  const changed = summary['CHANGED'] || 0
  const unchanged = (summary['UNCHANGED'] || 0) + (summary['FIRST_SEEN'] || 0)
  const notRun = summary['NOT_RUN'] || 0
  const failed = summary['FAILED'] || 0

  if (notRun === total_sources) {
    return (
      <div className="text-slate-300 text-sm mt-0.5">
        No monitoring runs yet — {total_sources} sources configured
      </div>
    )
  }

  const lastRunStr = last_run_at
    ? new Date(last_run_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    : null

  const parts = [
    `${total_sources} sources checked`,
    changed > 0 ? `${changed} change${changed !== 1 ? 's' : ''} detected` : null,
    unchanged > 0 ? `${unchanged} unchanged` : null,
    failed > 0 ? `${failed} failed` : null,
  ].filter(Boolean).join(' · ')

  return (
    <>
      <div className="text-slate-300 text-sm mt-0.5">
        {parts} · source proof attached
      </div>
      {lastRunStr && (
        <div className="text-slate-400 text-xs mt-1">
          Last run: {lastRunStr} UTC
        </div>
      )}
    </>
  )
}

export default function DashboardPreview() {
  return (
    <section className="py-20 bg-white" id="dashboard">
      <div className="max-w-6xl mx-auto px-4 sm:px-6">

        <div className="text-center mb-10">
          <span className="inline-block text-xs font-semibold text-blue-600 uppercase tracking-widest mb-4">
            Sample UAE Monitoring Session — Illustrative
          </span>
          <h2 className="text-3xl font-bold text-slate-900 mb-3">
            A source run your team can audit
          </h2>
          <p className="text-slate-600 max-w-3xl mx-auto leading-relaxed">
            This sample shows the operating model: configured official sources are checked, meaningful changes
            are queued for human review, and every brief carries proof back to the source.
          </p>
        </div>

        <div className="bg-slate-900 rounded-2xl p-6 mb-8">
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
            <div className="flex items-start gap-4">
              <div className="w-10 h-10 rounded-full bg-emerald-500 flex items-center justify-center flex-shrink-0">
                <ShieldCheck className="w-5 h-5 text-white" />
              </div>
              <div>
                <div className="text-white font-bold text-lg">
                  UAE monitoring — official sources
                </div>
                {/* TODO: mock data below (last-check time, review queue, proof note) — replace when scheduler/run-history API is wired */}
                <SourceStatusSummary />
                <div className="text-slate-400 text-sm mt-2 max-w-3xl leading-relaxed">
                  Official sources: VARA / CBUAE / DFSA / ADGM and others. Not legal advice. For monitoring information only.
                </div>
              </div>
            </div>
            <div className="text-right flex-shrink-0">
              {/* TODO: last-check time and review queue are mock — wire to scheduler run data */}
              <div className="flex items-center gap-2 text-slate-300 text-sm">
                <Clock className="w-4 h-4" />
                Monitored sources: AE
              </div>
              <div className="text-slate-500 text-xs mt-1">Changes queued for human review</div>
              <div className="text-emerald-400 text-xs mt-1 font-medium">Source proof attached</div>
            </div>
          </div>
        </div>

        <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          {CARDS.map(card => {
            const Icon = card.icon || Gauge
            return (
              <div key={card.title} className="bg-slate-50 border border-slate-200 rounded-xl p-5">
                <div className="w-10 h-10 bg-white rounded-lg border border-slate-200 flex items-center justify-center mb-4">
                  <Icon className="w-5 h-5 text-blue-600" />
                </div>
                <h3 className="font-semibold text-slate-800 text-sm mb-2">{card.title}</h3>
                <p className="text-xs text-slate-500 leading-relaxed">{card.desc}</p>
              </div>
            )
          })}
        </div>

        <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm">
          <h3 className="font-semibold text-slate-800 mb-1 text-sm">Sample source set</h3>
          <p className="text-xs text-slate-400 mb-4">
            Sample source set — illustrative. Access status and extraction quality shown.
            Pilot sources confirmed after source review.
          </p>
          <SourceTable />
        </div>

      </div>
    </section>
  )
}
