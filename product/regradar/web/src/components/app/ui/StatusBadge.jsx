import {
  CheckCircle2, AlertTriangle, XCircle, CircleDashed, Eye, Wrench,
  ShieldCheck, Clock, MinusCircle, FlaskConical, Ban, FileCheck2,
} from 'lucide-react'

// One visual vocabulary for every status a customer can see.
// tone: success | warning | critical | neutral | accent — status semantics only.
// `explain` is shown as a native tooltip so no status is ever undecodable.
const REGISTRY = {
  // ── monitoring run / change statuses ────────────────────────────────────
  CHANGED:      { label: 'Changed',      tone: 'accent',   icon: Eye,          explain: 'The monitored text changed since the previous run. Needs human review before any conclusion.' },
  FIRST_SEEN:   { label: 'First seen',   tone: 'accent',   icon: Eye,          explain: 'First recorded run for this source. Baseline captured; treated as a change for review purposes.' },
  UNCHANGED:    { label: 'Unchanged',    tone: 'neutral',  icon: CheckCircle2, explain: 'The monitored text is identical to the previous run (same content hash).' },
  FAILED:       { label: 'Fetch failed', tone: 'critical', icon: XCircle,      explain: 'The last monitoring run could not fetch or extract this source. Needs operator attention.' },
  QUALITY_DROP: { label: 'Quality drop', tone: 'warning',  icon: AlertTriangle, explain: 'The last run extracted less content than the established baseline. A source-health signal, not a regulatory conclusion.' },
  NOT_RUN:      { label: 'Not run yet',  tone: 'neutral',  icon: CircleDashed, explain: 'No monitoring run has been recorded for this source yet.' },

  // ── source readiness statuses ───────────────────────────────────────────
  'Readiness supported':    { label: 'Readiness supported', tone: 'success',  icon: ShieldCheck,  explain: 'Source passed accessibility and extraction checks; eligible for monitoring runs.' },
  'Needs remediation':      { label: 'Needs remediation',   tone: 'warning',  icon: Wrench,       explain: 'A known access or extraction issue is being worked on. Not counted toward monitored scope.' },
  'Monitoring not started': { label: 'Not started',         tone: 'neutral',  icon: CircleDashed, explain: 'Source is registered but no monitoring run has been recorded yet.' },
  'Under validation':       { label: 'Under validation',    tone: 'warning',  icon: FlaskConical, explain: 'Source is being validated (accessibility, extraction quality, content depth) before activation.' },
  Limited:                  { label: 'Limited',             tone: 'neutral',  icon: MinusCircle,  explain: 'Source is monitored with known limitations (partial content or restricted structure).' },
  Partial:                  { label: 'Partial',             tone: 'neutral',  icon: MinusCircle,  explain: 'Only part of this source can be monitored reliably.' },
  'Needs adapter':          { label: 'Needs adapter',       tone: 'warning',  icon: Wrench,       explain: 'Source requires a dedicated extraction adapter before it can be monitored.' },
  Blocked:                  { label: 'Blocked',             tone: 'critical', icon: Ban,          explain: 'Source actively blocks automated access. Not monitored.' },
  Candidate:                { label: 'Candidate',           tone: 'neutral',  icon: CircleDashed, explain: 'Identified as a potential source; not yet validated or monitored.' },
  'Evidence library':       { label: 'Evidence library',    tone: 'neutral',  icon: FileCheck2,   explain: 'Kept for its stored evidence records; not part of fresh-alert monitoring.' },
  'User source':            { label: 'User source',         tone: 'accent',   icon: FlaskConical, explain: 'Added by your workspace; queued for readiness validation before monitoring.' },

  // ── review statuses ──────────────────────────────────────────────────────
  pending:  { label: 'Pending review', tone: 'warning', icon: Clock,        explain: 'Awaiting a human review decision.' },
  PENDING_REVIEW: { label: 'Pending review', tone: 'warning', icon: Clock,  explain: 'Awaiting a human review decision.' },
  assessed: { label: 'Assessed',       tone: 'success', icon: CheckCircle2, explain: 'An internal Acknowledge & Assess note has been recorded.' },
  approved: { label: 'Approved',       tone: 'success', icon: CheckCircle2, explain: 'Approved by a human reviewer.' },
  rejected: { label: 'Rejected',       tone: 'critical', icon: XCircle,     explain: 'Rejected by a human reviewer.' },
  none:     { label: 'No decision',    tone: 'neutral', icon: CircleDashed, explain: 'No review decision has been recorded yet.' },

  // ── evidence ─────────────────────────────────────────────────────────────
  PROOF_RECORDED: { label: 'Evidence recorded', tone: 'success', icon: FileCheck2,   explain: 'A content hash and proof artifact are recorded for this source.' },
  AWAITING_RUN:   { label: 'Awaiting first run', tone: 'neutral', icon: CircleDashed, explain: 'No evidence recorded yet. The first monitoring run creates the hash, snapshot, and proof artifact.' },

  // ── delivery / system ────────────────────────────────────────────────────
  test_mode:    { label: 'Test mode',    tone: 'neutral', icon: FlaskConical, explain: 'Deliveries are written to a local outbox. No external customer email is sent.' },
  local_outbox: { label: 'Local outbox', tone: 'neutral', icon: FlaskConical, explain: 'Email provider is not configured; payloads are written locally instead of being sent.' },
}

const TONE_CLS = {
  success:  'border-emerald-400/25 bg-emerald-400/10 text-emerald-300',
  warning:  'border-amber-400/25 bg-amber-400/10 text-amber-300',
  critical: 'border-rose-400/25 bg-rose-400/10 text-rose-300',
  accent:   'border-cyan-400/25 bg-cyan-400/10 text-cyan-200',
  neutral:  'border-slate-600 bg-slate-800/80 text-slate-300',
}

function statusMeta(code) {
  if (code == null || code === '') return null
  return REGISTRY[code] || REGISTRY[String(code).trim()] || null
}

/**
 * <StatusBadge code="QUALITY_DROP" /> → pill with icon, human label, and a
 * tooltip explaining what the status means. Unknown codes render the raw
 * value humanized (underscores stripped, sentence case) rather than raw enums.
 */
export default function StatusBadge({ code, explainSuffix = '', className = '' }) {
  if (code == null || code === '') return null
  const meta = statusMeta(code) || {
    label: String(code).replace(/_/g, ' ').toLowerCase().replace(/^./, c => c.toUpperCase()),
    tone: 'neutral',
    icon: CircleDashed,
    explain: 'Status reported by the monitoring pipeline.',
  }
  const Icon = meta.icon
  return (
    <span
      title={explainSuffix ? `${meta.explain} ${explainSuffix}` : meta.explain}
      className={`inline-flex items-center gap-1.5 whitespace-nowrap rounded-full border px-2.5 py-1 text-[11px] font-semibold ${TONE_CLS[meta.tone]} ${className}`}
    >
      <Icon className="h-3.5 w-3.5 flex-shrink-0" aria-hidden="true" />
      {meta.label}
    </span>
  )
}
