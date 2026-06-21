import { ArrowLeft, ShieldCheck } from 'lucide-react'

const CONTENT = {
  terms: {
    title: 'Terms of Service',
    kicker: 'Terms',
    body: [
      'StatuteProof provides official-source monitoring intelligence, hash-verified source evidence, and review-support summaries. It does not provide legal advice, regulatory advice, compliance determination, or a legal opinion.',
      'Access to monitored sources, custom sources, weekly briefs, exports, and billing is subject to source readiness review, manual activation, and workspace configuration.',
      'Users remain responsible for reviewing official source material directly, validating evidence records, and consulting qualified legal or compliance professionals before making regulatory decisions.',
    ],
  },
  privacy: {
    title: 'Privacy Policy',
    kicker: 'Privacy',
    body: [
      'StatuteProof account and workspace data may include work email, company profile, monitored-source configuration, contact requests, and usage records needed to operate the service.',
      'Do not submit passwords, client secrets, private portal URLs, or confidential customer data as custom source URLs. StatuteProof is designed for public official sources and authorized public material.',
      'Evidence records may include official source URLs, timestamps, hashes, extracted text metadata, source status, failure reasons, and proof paths used to support compliance review workflows.',
    ],
  },
  disclaimer: {
    title: 'Monitoring Disclaimer',
    kicker: 'Disclaimer',
    body: [
      'StatuteProof reports are generated from monitored official-source records and are provided for information and compliance review support only.',
      'StatuteProof reports do not constitute legal advice, regulatory advice, compliance determination, or a legal opinion. StatuteProof does not replace qualified legal counsel, compliance professionals, MLROs, or other professional advisers.',
      'StatuteProof does not determine compliance outcomes, prevent fines, or confirm that all regulatory updates have been captured. Source monitoring may be affected by publication delays, website changes, PDF formatting, access limits, or source structure changes.',
      'Users should verify official source material directly and review evidence records, hashes, timestamps, and diffs before relying on a report.',
    ],
  },
}

export default function LegalPage({ type = 'disclaimer', onBack }) {
  const page = CONTENT[type] || CONTENT.disclaimer

  return (
    <div className="min-h-dvh bg-[#07111F] text-slate-200">
      <header className="border-b border-slate-800 bg-[#06101D]/92">
        <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-6">
          <button onClick={onBack} className="flex items-center gap-2 text-sm text-slate-400 hover:text-white">
            <ArrowLeft className="h-4 w-4" />
            Back
          </button>
          <div className="flex items-center gap-2">
            <img src="/brand/regradar-logo-navbar.png" alt="StatuteProof" className="h-8 w-auto" />
            <span className="font-bold text-white">Statute<span className="text-[#16D9F5]">Proof</span></span>
          </div>
          <div className="w-14" />
        </div>
      </header>

      <main className="mx-auto max-w-3xl px-6 py-16">
        <div className="sp-kicker mb-5">
          <ShieldCheck className="h-4 w-4" />
          {page.kicker}
        </div>
        <h1 className="text-4xl font-semibold text-white">{page.title}</h1>
        <div className="sp-panel mt-8 space-y-5 p-6">
          {page.body.map(paragraph => (
            <p key={paragraph} className="text-sm leading-relaxed text-slate-300">
              {paragraph}
            </p>
          ))}
        </div>
      </main>
    </div>
  )
}
