import { useEffect, useMemo, useState } from 'react'
import { AlertTriangle, CheckCircle, FileText, Search, ShieldCheck, ChevronDown, ChevronUp, Zap } from 'lucide-react'

import { briefs as briefsApi } from '../../api'

function GeneratedBriefPanel({ briefMarkdown, onDismiss }) {
  if (!briefMarkdown) return null
  return (
    <div className="mt-3 rounded-lg border border-cyan-400/25 bg-cyan-400/5 p-3 space-y-2">
      <div className="flex items-center justify-between">
        <p className="text-[10px] font-semibold uppercase tracking-wider text-cyan-400">Generated brief</p>
        <button
          type="button"
          onClick={onDismiss}
          className="text-[10px] text-slate-500 hover:text-slate-300 transition-colors"
        >
          dismiss
        </button>
      </div>
      <div className="rounded-md border border-slate-700 bg-slate-900/60 px-3 py-2.5 max-h-64 overflow-y-auto">
        {briefMarkdown.split('\n').map((line, i) => {
          const isHeading = line.startsWith('#')
          const isBold = line.startsWith('**') && line.endsWith('**')
          return (
            <p
              key={i}
              className={`text-xs leading-relaxed ${
                isHeading
                  ? 'font-semibold text-white mt-2 mb-1'
                  : isBold
                  ? 'font-semibold text-amber-200/90'
                  : 'text-slate-300'
              } ${i > 0 && !isHeading ? 'mt-0.5' : ''}`}
            >
              {line.replace(/^#+\s*/, '').replace(/\*\*/g, '') || ' '}
            </p>
          )
        })}
      </div>
      <p className="text-[10px] text-slate-500 leading-relaxed">
        Monitoring intelligence only. Not legal advice. Not customer delivery. Human review required before any external use.
      </p>
    </div>
  )
}

function BriefContent({ brief }) {
  const [expanded, setExpanded] = useState(false)
  const [generating, setGenerating] = useState(false)
  const [generatedMarkdown, setGeneratedMarkdown] = useState('')
  const [generateError, setGenerateError] = useState('')
  const hasNotes = Boolean(brief.notes && brief.notes.trim())

  function handleGenerate() {
    if (!brief.source_id || generating) return
    setGenerating(true)
    setGenerateError('')
    setGeneratedMarkdown('')
    briefsApi.generate(brief.source_id, brief.run_id || undefined)
      .then(data => {
        setGeneratedMarkdown(data.brief_markdown || '')
      })
      .catch(err => {
        setGenerateError(err.message || 'Brief generation failed.')
      })
      .finally(() => {
        setGenerating(false)
      })
  }

  return (
    <div className="mt-3 rounded-lg border border-slate-800 bg-slate-950/40">
      <div className="flex items-center justify-between px-3 py-2.5">
        <button
          type="button"
          onClick={() => setExpanded(v => !v)}
          className="flex flex-1 items-center gap-2 text-left"
        >
          <span className="text-xs font-semibold text-white">Brief content</span>
          {expanded
            ? <ChevronUp className="h-3.5 w-3.5 text-slate-400" />
            : <ChevronDown className="h-3.5 w-3.5 text-slate-400" />}
        </button>
        {!hasNotes && brief.source_id && (
          <button
            type="button"
            onClick={handleGenerate}
            disabled={generating}
            className="flex items-center gap-1.5 rounded-md border border-cyan-400/30 bg-cyan-400/10 px-2.5 py-1 text-[10px] font-semibold text-cyan-300 transition-colors hover:bg-cyan-400/20 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <Zap className="h-3 w-3" />
            {generating ? 'Generating…' : 'Generate Brief'}
          </button>
        )}
      </div>

      {generateError && (
        <div className="border-t border-slate-800 px-3 py-2 flex items-start gap-2">
          <AlertTriangle className="mt-0.5 h-3 w-3 flex-shrink-0 text-rose-400" />
          <p className="text-[11px] text-rose-300">{generateError}</p>
        </div>
      )}

      {generatedMarkdown && (
        <div className="border-t border-slate-800 px-3 pb-3 pt-0">
          <GeneratedBriefPanel
            briefMarkdown={generatedMarkdown}
            onDismiss={() => setGeneratedMarkdown('')}
          />
        </div>
      )}

      {expanded && (
        <div className="border-t border-slate-800 px-3 pb-3 pt-2.5 space-y-3">
          {hasNotes ? (
            <div>
              <p className="mb-1.5 text-[10px] font-semibold uppercase tracking-wider text-slate-500">
                Reviewer notes
              </p>
              <div className="rounded-md border border-slate-700 bg-slate-900/60 px-3 py-2.5">
                {brief.notes.split('\n').map((line, i) => (
                  <p key={i} className={`text-xs leading-relaxed text-slate-200 ${i > 0 ? 'mt-1' : ''}`}>
                    {line || ' '}
                  </p>
                ))}
              </div>
            </div>
          ) : (
            <div className="rounded-md border border-amber-400/20 bg-amber-400/5 px-3 py-2.5">
              <p className="text-xs text-amber-200/80">
                No brief text has been written for this record yet. Use the Generate Brief button above to create one from the detected change.
              </p>
            </div>
          )}

          {(brief.reviewer || brief.reviewed_at) && (
            <div className="grid gap-2 text-xs sm:grid-cols-2">
              {brief.reviewer && (
                <div>
                  <p className="text-slate-500">Reviewed by</p>
                  <p className="text-slate-300">{brief.reviewer}</p>
                </div>
              )}
              {brief.reviewed_at && (
                <div>
                  <p className="text-slate-500">Reviewed at</p>
                  <p className="text-slate-300">{brief.reviewed_at}</p>
                </div>
              )}
            </div>
          )}

          {brief.evidence_record_id && (
            <div>
              <p className="text-slate-500 text-xs">Evidence record ID</p>
              <p className="sp-mono text-[11px] text-slate-400 break-all">{brief.evidence_record_id}</p>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

const STATUS_STYLE = {
  approved: 'border-emerald-400/30 bg-emerald-400/10 text-emerald-200',
  pending: 'border-amber-400/30 bg-amber-400/10 text-amber-200',
  draft: 'border-slate-600 bg-slate-800 text-slate-300',
}

export default function AIBriefPage() {
  const [briefs, setBriefs] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [search, setSearch] = useState('')

  useEffect(() => {
    let active = true
    briefsApi.list('AE', 100)
      .then(data => {
        if (active) setBriefs(data.briefs || [])
      })
      .catch(err => {
        if (active) setError(err.message || 'Could not load monitoring briefs.')
      })
      .finally(() => {
        if (active) setLoading(false)
      })
    return () => { active = false }
  }, [])

  const filtered = useMemo(() => briefs.filter(brief => {
    const haystack = [
      brief.source_id,
      brief.run_id,
      brief.change_status,
      brief.status,
      brief.alert_id,
      brief.notes,
      brief.reviewer,
    ].join(' ').toLowerCase()
    return !search || haystack.includes(search.toLowerCase())
  }), [briefs, search])

  return (
    <div className="min-h-full space-y-5 bg-[#07111F] p-5 pb-10">
      <div>
        <h1 className="text-lg font-bold text-white mb-1">Monitoring Briefs</h1>
        <p className="max-w-3xl text-sm leading-relaxed text-slate-400">
          Brief records are loaded from approved local queue files. If no reviewed brief exists, this page stays empty instead of falling back to sample content.
        </p>
      </div>

      <div className="sp-command-panel p-5">
        <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
          <div>
            <h2 className="text-sm font-semibold text-white">Reviewed monitoring brief queue</h2>
            <p className="mt-1 max-w-3xl text-sm leading-relaxed text-slate-400">
              Brief drafts require canonical evidence, human review, legal-language scan, and explicit delivery approval. This is not legal advice.
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            {['Evidence-gated', 'Human review gate', 'No sample fallback', 'Delivery requires setup'].map(label => (
              <span key={label} className="rounded-full border border-slate-700 bg-slate-900 px-2.5 py-1 text-[11px] font-semibold text-slate-300">
                {label}
              </span>
            ))}
          </div>
        </div>
        <div className="mt-4 grid gap-2 md:grid-cols-4">
          {[
            ['Evidence', 'canonical record required'],
            ['Review', 'human decision required'],
            ['Scan', 'forbidden phrases blocked'],
            ['Delivery', 'off until approved'],
          ].map(([title, body]) => (
            <div key={title} className="rounded-xl border border-slate-800 bg-slate-950/45 p-3">
              <p className="text-xs font-semibold text-white">{title}</p>
              <p className="mt-1 text-[11px] leading-relaxed text-slate-500">{body}</p>
            </div>
          ))}
        </div>
      </div>

      <div className="relative max-w-md">
        <Search className="absolute left-3 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-slate-500" />
        <input
          type="text"
          placeholder="Search brief queue"
          value={search}
          onChange={event => setSearch(event.target.value)}
          className="w-full rounded-lg border border-slate-700 bg-slate-900 py-2 pl-9 pr-3 text-xs text-white placeholder:text-slate-500 focus:border-cyan-500 focus:outline-none"
        />
      </div>

      {loading && (
        <div className="rounded-xl border border-slate-800 bg-[#0D1B2E] px-5 py-8 text-sm text-slate-400">
          Loading monitoring briefs...
        </div>
      )}

      {!loading && error && (
        <div className="flex items-start gap-3 rounded-xl border border-rose-500/20 bg-rose-500/5 px-5 py-4">
          <AlertTriangle className="mt-0.5 h-4 w-4 flex-shrink-0 text-rose-400" />
          <div>
            <p className="text-sm font-semibold text-rose-200">Could not load monitoring briefs.</p>
            <p className="mt-1 text-xs text-rose-300/80">{error}</p>
          </div>
        </div>
      )}

      {!loading && !error && filtered.length === 0 && (
        <div className="rounded-xl border border-slate-800 bg-slate-950/35 px-6 py-12 text-center">
          <FileText className="mx-auto mb-3 h-8 w-8 text-slate-600" />
          <p className="text-sm font-semibold text-white">No reviewed monitoring briefs yet.</p>
          <p className="mx-auto mt-2 max-w-2xl text-sm leading-relaxed text-slate-500">
            Monitoring briefs will appear after evidence records are queued and approved for brief delivery. No sample briefs are shown in this authenticated workspace.
          </p>
        </div>
      )}

      {!loading && !error && filtered.length > 0 && (
        <div className="grid gap-3 lg:grid-cols-2">
          {filtered.map((brief, index) => {
            const status = brief.delivery_approved
              ? 'approved'
              : brief.human_reviewed
              ? 'pending'
              : 'draft'
            const briefKey = brief.alert_id || brief.id || `${brief.source_id || 'brief'}-${brief.run_id || index}`
            return (
              <article key={briefKey} className="rounded-xl border border-slate-800 bg-[#0D1B2E] p-4">
                <div className="mb-3 flex flex-wrap items-center gap-2">
                  <span className={`rounded-full border px-2 py-0.5 text-[10px] font-bold ${STATUS_STYLE[status]}`}>
                    {brief.delivery_approved ? 'Delivery approved' : brief.human_reviewed ? 'Reviewed' : 'Draft queue'}
                  </span>
                  <span className="rounded-full border border-cyan-400/25 bg-cyan-400/10 px-2 py-0.5 text-[10px] font-semibold text-cyan-200">
                    {brief.change_status || 'UNKNOWN'}
                  </span>
                </div>
                <h3 className="text-sm font-semibold text-white">{brief.source_id || 'Queued source'}</h3>
                <div className="mt-3 grid gap-2 text-xs sm:grid-cols-2">
                  <div>
                    <p className="text-slate-500">Alert ID</p>
                    <p className="break-all text-slate-300">{brief.alert_id}</p>
                  </div>
                  <div>
                    <p className="text-slate-500">Run ID</p>
                    <p className="break-all text-slate-300">{brief.run_id || 'not recorded'}</p>
                  </div>
                  <div>
                    <p className="text-slate-500">Queued</p>
                    <p className="text-slate-300">{brief.queued_at || brief.run_at || 'not recorded'}</p>
                  </div>
                  <div>
                    <p className="text-slate-500">Hash</p>
                    <p className="sp-mono text-slate-300">{brief.normalized_hash ? brief.normalized_hash.slice(0, 12) : 'not recorded'}</p>
                  </div>
                </div>
                <BriefContent brief={brief} />

                <div className="mt-3 flex items-start gap-2 rounded-lg border border-slate-800 bg-slate-950/35 px-3 py-3">
                  {brief.delivery_approved ? (
                    <CheckCircle className="mt-0.5 h-4 w-4 flex-shrink-0 text-emerald-300" />
                  ) : (
                    <ShieldCheck className="mt-0.5 h-4 w-4 flex-shrink-0 text-slate-500" />
                  )}
                  <p className="text-xs leading-relaxed text-slate-500">
                    Delivery requires evidence, routing approval, and configured delivery channel. Monitoring intelligence only. Not legal advice.
                  </p>
                </div>
              </article>
            )
          })}
        </div>
      )}
    </div>
  )
}
