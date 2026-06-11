import { ArrowRight, FileSearch, ShieldCheck } from 'lucide-react'

const MATRIX_ROWS = [
  {
    category: 'Financial regulation',
    map: 'CBUAE / payments / AML layers',
    status: 'Under validation',
    statusTone: 'validation',
    extraction: 'HTML / rulebook / adapter review',
    limitation: 'Some CBUAE pages may require mirror/WAF strategy',
  },
  {
    category: 'Virtual assets',
    map: 'VARA publications and rulebooks',
    status: 'Under validation',
    statusTone: 'validation',
    extraction: 'HTML + document-link validation',
    limitation: 'PDF/document content may be deferred',
  },
  {
    category: 'DIFC / DFSA',
    map: 'DIFC Laws / DFSA rulebook / consultations',
    status: 'Validated + under validation',
    statusTone: 'validated',
    extraction: 'HTML / item-level validation',
    limitation: 'Some DFSA sources may require WAF/mirror review',
  },
  {
    category: 'ADGM / FSRA',
    map: 'FSRA circulars / ADGM publications',
    status: 'Under validation',
    statusTone: 'validation',
    extraction: 'HTML row extraction / proof-diff',
    limitation: 'Generic pages require item-level mapping',
  },
  {
    category: 'AML / sanctions',
    map: 'UAE FIU / EOCN / MoET AML',
    status: 'Under validation',
    statusTone: 'validation',
    extraction: 'HTML / JS validation',
    limitation: 'Some FIU pages may require JS rendering',
  },
  {
    category: 'Tax / corporate',
    map: 'FTA clarifications / guides / MoF',
    status: 'Candidate',
    statusTone: 'adapter',
    extraction: 'HTML / PDF-link validation',
    limitation: 'Activation requires item-level source check',
  },
  {
    category: 'Data protection',
    map: 'DIFC DP / ADGM DP / UAE PDPL',
    status: 'Candidate',
    statusTone: 'adapter',
    extraction: 'HTML guidance pages',
    limitation: 'UAE Data Office status requires validation',
  },
  {
    category: 'Legislation / gazettes',
    map: 'UAE legislation / Dubai Gazette',
    status: 'Limited / blocked',
    statusTone: 'limited',
    extraction: 'WAF / item-level validation',
    limitation: 'Not active until access is reliable',
  },
]

const BADGE_STYLES = {
  validated: 'border-emerald-400/25 bg-emerald-400/10 text-emerald-300',
  validation: 'border-amber-400/25 bg-amber-400/10 text-amber-300',
  adapter: 'border-cyan-400/25 bg-cyan-400/10 text-cyan-200',
  limited: 'border-rose-400/25 bg-rose-400/10 text-rose-300',
}

function StatusBadge({ tone, children }) {
  return (
    <span className={`inline-flex rounded-full border px-2.5 py-1 text-[11px] font-semibold ${BADGE_STYLES[tone] || BADGE_STYLES.adapter}`}>
      {children}
    </span>
  )
}

export default function SourceTransparencyMatrix({ onCreateWorkspace }) {
  return (
    <section className="bg-[#0A1628] py-20" id="source-transparency-matrix">
      <div className="mx-auto max-w-6xl px-4 sm:px-6">
        <div className="mb-10 grid gap-8 lg:grid-cols-[1fr_360px] lg:items-end">
          <div>
            <div className="mb-4 inline-flex items-center gap-2 rounded-full border border-cyan-400/20 bg-cyan-400/10 px-4 py-1.5 text-sm font-medium text-cyan-200">
              <FileSearch className="h-4 w-4" />
              Activation standard
            </div>
            <h2 className="mb-4 text-3xl font-bold text-white">
              Broad source map. Strict activation standard.
            </h2>
            <p className="max-w-3xl text-slate-400">
              Mapped does not mean active. Only validated sources enter client monitoring profiles.
            </p>
          </div>

          <div className="rounded-xl border border-cyan-400/20 bg-slate-950/45 p-4">
            <div className="mb-2 flex items-center gap-2 text-sm font-semibold text-white">
              <ShieldCheck className="h-4 w-4 text-emerald-300" />
              Pilot transparency
            </div>
            <p className="text-sm leading-relaxed text-slate-400">
              Every pilot includes a source transparency report showing active, under-validation, limited and blocked sources.
            </p>
          </div>
        </div>

        <div className="overflow-x-auto rounded-xl border border-slate-800 bg-[#07111F] shadow-[0_20px_60px_rgba(0,0,0,0.28)]">
          <table className="w-full min-w-[980px] text-sm">
            <thead className="border-b border-slate-800 bg-slate-950/60">
              <tr>
                {['Regulatory layer', 'Source map', 'Validation status', 'Extraction method', 'Limitation'].map(column => (
                  <th key={column} className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">
                    {column}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {MATRIX_ROWS.map(row => (
                <tr key={row.category} className="border-b border-slate-800/80 last:border-0">
                  <td className="px-4 py-4 align-top font-semibold text-slate-100">{row.category}</td>
                  <td className="px-4 py-4 align-top text-slate-400">{row.map}</td>
                  <td className="px-4 py-4 align-top">
                    <StatusBadge tone={row.statusTone}>{row.status}</StatusBadge>
                  </td>
                  <td className="px-4 py-4 align-top text-slate-400">{row.extraction}</td>
                  <td className="px-4 py-4 align-top text-slate-400">{row.limitation}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="mt-8 rounded-2xl border border-cyan-400/20 bg-slate-950/55 p-6 sm:p-7">
          <div className="grid gap-5 lg:grid-cols-[1fr_auto] lg:items-center">
            <div>
              <h3 className="text-2xl font-bold text-white">
                Start with your UAE source profile
              </h3>
              <p className="mt-3 max-w-3xl text-sm leading-relaxed text-slate-400">
                Create a workspace to save your licence profile, map the official sources that matter,
                and review validation status before any pilot.
              </p>
            </div>
            <div className="flex flex-col gap-2 sm:flex-row lg:flex-col">
              <button
                type="button"
                onClick={onCreateWorkspace}
                className="inline-flex items-center justify-center gap-2 rounded-lg bg-[#16D9F5] px-5 py-2.5 text-sm font-semibold text-[#07111F] transition-colors hover:bg-[#11c2db]"
              >
                Create workspace to start source readiness review
                <ArrowRight className="h-4 w-4" />
              </button>
              <a
                href="#sample-brief"
                className="inline-flex items-center justify-center rounded-lg border border-slate-700 px-5 py-2.5 text-sm font-semibold text-slate-300 transition-colors hover:border-slate-500 hover:text-white"
              >
                See sample brief
              </a>
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}
