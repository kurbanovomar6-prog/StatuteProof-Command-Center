


export default function Footer() {
  return (
    <footer className="bg-[#07111F] border-t border-slate-800 text-slate-400 py-12">
      <div className="max-w-6xl mx-auto px-4 sm:px-6">

        <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
          <div>
            <div className="mb-2">
              <img src="/brand/regradar-logo-navbar.png" alt="StatuteProof" className="h-9 w-auto" />
            </div>
            <p className="text-sm text-slate-500 max-w-xs">
              Official-source regulatory intelligence for UAE financial firms. Source limitations disclosed. Not legal advice.
            </p>
          </div>

          <div className="flex flex-wrap gap-6 text-sm">
            {[
              { label: 'Contact', href: '#contact' },
            ].map(l => (
              <a
                key={l.label}
                href={l.href}
                target={l.external ? '_blank' : undefined}
                rel={l.external ? 'noopener noreferrer' : undefined}
                className="hover:text-white transition-colors"
              >
                {l.label}
              </a>
            ))}
          </div>
        </div>

        <div className="border-t border-slate-800 mt-8 pt-8 text-xs text-slate-600 text-center space-y-3">
          <p>© {new Date().getFullYear()} StatuteProof. All rights reserved.</p>
          <p className="max-w-3xl mx-auto leading-relaxed">
            StatuteProof reports are generated from monitored official-source records and are provided for information
            and compliance review support only. StatuteProof reports do not constitute legal advice, regulatory advice,
            compliance certification, or a legal opinion. StatuteProof does not replace qualified legal counsel,
            compliance professionals, MLROs, or other professional advisers. StatuteProof does not guarantee compliance,
            prevent fines, or certify that all regulatory updates have been captured. Source monitoring may be affected
            by publication delays, website changes, PDF formatting, access limits, or source structure changes. Users
            should verify official source material directly and review evidence records, hashes, timestamps, and diffs
            before relying on a report. Users should consult qualified legal or compliance professionals before making
            regulatory, filing, operational, or customer decisions based on a report.
          </p>
          <p className="text-slate-700">
            Monitoring intelligence only — not legal advice and not a guarantee of compliance.
          </p>
        </div>

      </div>
    </footer>
  )
}
