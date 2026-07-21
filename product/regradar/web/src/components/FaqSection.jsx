import { ChevronDown, FileText, ShieldCheck } from 'lucide-react'

// ─── Block 12 — FAQ / objections + vendor due-diligence kit ───────────────────
//
// Consolidates the objections a UAE MLRO must clear to finish vendor due
// diligence rep-free, answered with SHIPPED mechanisms — not promises. Every
// answer is written to survive the legal_safety forbidden-claims scan and the
// delivery-channel honesty guard (alerts require a linked Telegram chat; that
// is stated, never softened). The vendor-DD documents linked below are the real
// files under docs/vendor-dd/, copied to /public/vendor-dd for download.

const FAQS = [
  {
    q: 'Where does our data live, and do you hold our client PII?',
    a: 'The content StatuteProof monitors is public regulator material — rulebooks, circulars, and notices. Your workspace stores your firm profile and your team’s review decisions; alerts route to your linked Telegram chat (a linked chat is required). It is not built to ingest your customer files, so it holds little to no client PII by design. The data-flow and residency note below describes what is stored and where.',
  },
  {
    q: 'Is this legal or compliance advice?',
    a: 'No. StatuteProof is official-source monitoring with evidence-backed briefs for human review. Reports do not constitute legal advice, regulatory advice, or compliance certification, and do not replace qualified counsel or your MLRO. Every brief carries the full disclaimer, and a human on your team reviews it before any action.',
  },
  {
    q: 'What if monitoring silently breaks — how would we know?',
    a: 'Extraction failures are not hidden. A source whose text extraction degrades is recorded as QUALITY_DROP rather than being counted as a healthy check, StatuteProof re-verifies its own sealed records on a routine self-check, and the coverage certificate discloses which sources were blocked, geo-restricted, or in remediation for the period. The coverage matrix on this page shows the current state per source.',
  },
  {
    q: 'Which sources exactly — and how current are they?',
    a: 'The source transparency matrix on this page lists every source by tier: fresh-alert eligible, disclosed-with-caveat, access-blocked, and roadmap. It names the blocked hosts (for example CBUAE rulebook pages that return HTTP 403 to our production egress) instead of quietly dropping them. This is selected-source monitoring, not complete UAE coverage.',
  },
]

const DD_DOCS = [
  ['Security overview', '/vendor-dd/SECURITY-OVERVIEW.md'],
  ['Data flow & residency', '/vendor-dd/DATA-FLOW-AND-RESIDENCY.md'],
  ['Vendor DD FAQ', '/vendor-dd/VENDOR-DD-FAQ.md'],
  ['Evidence integrity whitepaper', '/vendor-dd/EVIDENCE-INTEGRITY-WHITEPAPER.md'],
]

export default function FaqSection() {
  return (
    <section className="bg-[#07111F] py-20" id="faq">
      <div className="mx-auto max-w-4xl px-4 sm:px-6">
        <div className="mb-10 text-center">
          <div className="sp-kicker mb-4 inline-flex items-center gap-2 rounded-full border border-cyan-400/20 bg-cyan-400/10 px-4 py-1.5 text-sm font-medium text-cyan-200">
            Due-diligence answers
          </div>
          <h2 className="mb-3 text-3xl font-bold text-white">
            The questions your vendor review will ask
          </h2>
          <p className="mx-auto max-w-2xl text-slate-400">
            Answered with mechanisms that already ship, so you can complete most
            of the review before you ever contact us.
          </p>
        </div>

        <div className="space-y-3">
          {FAQS.map(({ q, a }) => (
            <details
              key={q}
              className="group rounded-xl border border-slate-800 bg-[#0A1628] px-5 py-4 [&_summary::-webkit-details-marker]:hidden"
            >
              <summary className="flex cursor-pointer list-none items-center justify-between gap-4 text-left text-base font-semibold text-slate-100">
                {q}
                <ChevronDown className="h-5 w-5 flex-shrink-0 text-cyan-300 transition-transform duration-200 group-open:rotate-180" />
              </summary>
              <p className="mt-3 text-sm leading-relaxed text-slate-400">{a}</p>
            </details>
          ))}
        </div>

        {/* Vendor due-diligence kit */}
        <div className="mt-8 rounded-xl border border-cyan-400/20 bg-[#0D1B2E] p-6">
          <div className="mb-4 flex items-center gap-2">
            <ShieldCheck className="h-5 w-5 text-cyan-300" />
            <h3 className="text-base font-semibold text-white">Vendor due-diligence kit</h3>
          </div>
          <p className="mb-4 text-sm leading-relaxed text-slate-400">
            The same documents we would send a procurement or risk team, available
            to read now. Monitoring information only. Not legal advice.
          </p>
          <div className="grid gap-2 sm:grid-cols-2">
            {DD_DOCS.map(([label, href]) => (
              <a
                key={href}
                href={href}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-2 rounded-lg border border-slate-700 bg-slate-950/40 px-4 py-2.5 text-sm font-medium text-slate-200 transition-colors hover:border-cyan-400/35 hover:text-cyan-200"
              >
                <FileText className="h-4 w-4 flex-shrink-0 text-cyan-300" />
                {label}
              </a>
            ))}
          </div>
        </div>
      </div>
    </section>
  )
}
