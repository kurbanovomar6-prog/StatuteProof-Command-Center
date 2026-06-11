


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

        <div className="border-t border-slate-800 mt-8 pt-8 text-xs text-slate-600 text-center space-y-2">
          <p>© {new Date().getFullYear()} StatuteProof. All rights reserved.</p>
          <p className="max-w-2xl mx-auto leading-relaxed">
            StatuteProof monitors publicly available UAE regulatory sources and helps identify changes that may require
            compliance review. It is not a law firm and does not provide legal advice. Coverage quality varies by source
            accessibility, extraction quality, and official portal restrictions. Source readiness scores reflect technical
            accessibility, not legal significance. Final compliance decisions should be reviewed by qualified professionals.
          </p>
        </div>

      </div>
    </footer>
  )
}
