
const footerLinks = [
  { label: 'How It Works', href: '#how-it-works' },
  { label: 'Source Coverage', href: '#coverage' },
  { label: 'Evidence', href: '#evidence' },
  { label: 'Pricing', href: '#pricing' },
  { label: 'Contact', href: 'mailto:hello@statuteproof.com' },
]

export default function Footer() {
  return (
    <footer className="bg-[#081425] border-t border-slate-800 text-slate-400">

      {/* Top section */}
      <div className="max-w-6xl mx-auto px-6 py-12">
        <div className="flex flex-col md:flex-row gap-10 justify-between">

          {/* Logo + description */}
          <div className="max-w-xs">
            <div className="flex items-center gap-2.5 mb-4">
              <img src="/brand/regradar-logo-navbar.png" alt="StatuteProof" className="h-8 w-auto flex-shrink-0" />
              <span className="sp-display text-base font-extrabold text-white tracking-tight">
                Statute<span className="text-[#16D9F5]">Proof</span>
              </span>
            </div>
            <p className="text-sm text-slate-500 leading-relaxed">
              Official-source regulatory monitoring with hash-verified evidence records and human-review
              workflows for UAE financial firms. Source limitations disclosed. Not legal advice.
            </p>
          </div>

          {/* Nav links */}
          <div className="flex flex-wrap gap-x-8 gap-y-3 text-sm">
            {footerLinks.map(l => (
              <a
                key={l.label}
                href={l.href}
                className="text-slate-400 hover:text-slate-100 transition-colors"
              >
                {l.label}
              </a>
            ))}
          </div>
        </div>
      </div>

      {/* Disclaimer */}
      <div className="border-t border-slate-800/60">
        <div className="max-w-6xl mx-auto px-6 py-8">
          <p className="text-xs text-slate-400 leading-relaxed max-w-4xl">
            StatuteProof reports are generated from monitored official-source records and are provided
            for information and compliance review support only. StatuteProof reports do not constitute
            legal advice, regulatory advice, compliance determination, or a legal opinion. StatuteProof
            does not replace qualified legal counsel, compliance professionals, MLROs, or other
            professional advisers. StatuteProof does not determine compliance outcomes, prevent fines, or determine
            that all regulatory updates have been captured. Source monitoring may be affected by
            publication delays, website changes, PDF formatting, access limits, or source structure
            changes. Users should verify official source material directly and review evidence records,
            hashes, timestamps, and diffs before relying on a report. Users should consult qualified
            legal or compliance professionals before making regulatory, filing, operational, or customer
            decisions based on a report.
          </p>
        </div>
      </div>

      {/* Bottom bar */}
      <div className="border-t border-slate-800/40">
        <div className="max-w-6xl mx-auto px-6 py-5 flex flex-col sm:flex-row items-center justify-between gap-4 text-xs text-slate-400">
          <p>&copy; {new Date().getFullYear()} StatuteProof. All rights reserved.</p>
          <div className="flex items-center gap-5">
            <a href="/verify" className="hover:text-white transition-colors">Verify a record</a>
            <a href="/terms" className="hover:text-white transition-colors">Terms</a>
            <a href="/privacy" className="hover:text-white transition-colors">Privacy</a>
            <a href="/disclaimer" className="hover:text-white transition-colors">Disclaimer</a>
          </div>
          <p className="text-slate-400">Monitoring intelligence only — not legal advice and not a guarantee of compliance.</p>
        </div>
      </div>

    </footer>
  )
}
