import { ExternalLink } from 'lucide-react'

// ─── Block 11 — Honest category comparison ───────────────────────────────────
//
// Positioning against the three things a UAE MLRO is likely already using or
// pricing. Per the iron honesty rule, the StatuteProof column states ONLY what
// WE do — never a universal competitor negative. Every competitor cell is a fact drawn
// from that competitor's OWN published page, with the link so the reader can
// check it. No invented weaknesses.

const COLUMNS = [
  {
    name: 'Monthly regulatory newsletters',
    example: 'e.g. Waystone regional update',
    href: 'https://compliance.waystone.com/regulatory-update-june-2026-me-region',
    tone: 'muted',
  },
  {
    name: 'DIY page-change monitors',
    example: 'e.g. Visualping',
    href: 'https://visualping.io/',
    tone: 'muted',
  },
  {
    name: 'Enterprise RCM platforms',
    example: 'e.g. RegAlytics',
    href: 'https://regalytics.ai/',
    tone: 'muted',
  },
  {
    name: 'StatuteProof',
    example: 'Selected-source UAE monitoring',
    href: null,
    tone: 'accent',
  },
]

// rows[i] = [dimension, newsletter, diyMonitor, enterpriseRcm, statuteproof]
const ROWS = [
  [
    'Update latency',
    'Periodic digest — the May 2026 edition was published on 9 June 2026, roughly a month after the period it covers.',
    'Near-real-time when the page is reachable and returns stable HTML.',
    'Feeds vary by tier and subscription.',
    'Monitored pages are checked on an operator-set cycle (target up to every 24h); the detection timestamp is sealed with each capture.',
  ],
  [
    'UAE regulators that block bots',
    'Human editors read the sites, so a bot wall does not stop coverage.',
    'Visualping states it follows good-bot / robots conventions, so a regulator that blocks automated access is not covered.',
    'Depends on the vendor’s own source integrations.',
    'Blocked, geo-restricted, or 403-returning UAE sources are disclosed in the coverage matrix rather than silently dropped.',
  ],
  [
    'Evidence you can verify',
    'Prose summary; no per-change hash or timestamp you can re-check.',
    'Screenshot / diff of the page at check time.',
    'Depends on the platform’s export format.',
    'Every capture is sealed under SHA-256 and chained; anyone can re-hash the exact bytes at /verify — no account, no trust in us required.',
  ],
  [
    'Entry price',
    'Often free or low-cost as a marketing channel.',
    'Published plans from a low monthly rate.',
    'RegAlytics does not publish pricing on its site — no figures are shown, so cost is quote-only.',
    'Published pilot tiers — see Pricing.',
  ],
  [
    'Human review before it reaches you',
    'Editorial, but not tied to your firm profile.',
    'None — it is a raw page-change signal.',
    'Varies by configuration.',
    'Each brief is drafted for your MLRO or CCO to review before any action — a logged decision gate, not an automated decision.',
  ],
]

export default function Comparison() {
  return (
    <section className="bg-[var(--bg-navy,#06101D)] py-20" id="comparison">
      <div className="mx-auto max-w-6xl px-4 sm:px-6">
        <div className="mb-10 max-w-3xl">
          <div className="sp-kicker mb-4 inline-flex items-center gap-2 rounded-full border border-cyan-400/20 bg-cyan-400/10 px-4 py-1.5 text-sm font-medium text-cyan-200">
            Where StatuteProof sits
          </div>
          <h2 className="mb-4 text-3xl font-bold text-white">
            The newsletter you already read, the monitor you could rig yourself, and the platform you priced
          </h2>
          <p className="text-slate-400">
            An honest side-by-side. Each competitor cell states a fact from that
            provider’s own published page — follow the link and check it. The
            StatuteProof column describes only what StatuteProof does.
          </p>
        </div>

        <div className="min-w-0 overflow-x-auto rounded-xl border border-slate-800 bg-[#0A1628] shadow-[0_18px_48px_rgba(0,0,0,0.24)]">
          <table className="w-full min-w-[720px] border-collapse text-sm">
            <thead>
              <tr className="border-b border-slate-800">
                <th className="w-40 px-4 py-4 text-left text-xs font-semibold uppercase tracking-wide text-slate-400" />
                {COLUMNS.map((col) => (
                  <th
                    key={col.name}
                    className={`px-4 py-4 text-left align-top ${
                      col.tone === 'accent' ? 'bg-cyan-400/5' : ''
                    }`}
                  >
                    <div
                      className={`text-sm font-bold ${
                        col.tone === 'accent' ? 'text-cyan-200' : 'text-slate-200'
                      }`}
                    >
                      {col.name}
                    </div>
                    {col.href ? (
                      <a
                        href={col.href}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="mt-1 inline-flex items-center gap-1 text-[11px] font-medium text-slate-400 transition-colors hover:text-cyan-300"
                      >
                        {col.example}
                        <ExternalLink className="h-3 w-3" />
                      </a>
                    ) : (
                      <div className="mt-1 text-[11px] font-medium text-cyan-300/70">
                        {col.example}
                      </div>
                    )}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {ROWS.map((row) => (
                <tr key={row[0]} className="border-b border-slate-800/60 last:border-b-0">
                  <th className="px-4 py-4 text-left align-top text-xs font-semibold uppercase tracking-wide text-slate-400">
                    {row[0]}
                  </th>
                  {row.slice(1).map((cell, i) => (
                    <td
                      key={i}
                      className={`px-4 py-4 align-top text-[13px] leading-relaxed ${
                        COLUMNS[i].tone === 'accent'
                          ? 'bg-cyan-400/5 text-slate-200'
                          : 'text-slate-400'
                      }`}
                    >
                      {cell}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <p className="mt-5 max-w-3xl text-xs leading-relaxed text-slate-400">
          Competitor facts are drawn from each provider’s own public pages
          (linked above) and may change — verify at the source. StatuteProof is
          selected-source UAE monitoring, not complete coverage. Monitoring
          information only. Not legal advice.
        </p>
      </div>
    </section>
  )
}
