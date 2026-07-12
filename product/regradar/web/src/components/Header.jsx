import { useState } from 'react'
import { Menu, X } from 'lucide-react'

const navLinks = [
  { label: 'How It Works',    href: '#how-it-works' },
  { label: 'Source Coverage', href: '#coverage' },
  { label: 'Evidence',        href: '#evidence' },
  { label: 'Pricing',         action: 'pricing' },
]

export default function Header({ onSignIn, onCreateWorkspace, onSourceReview, onPricing }) {
  const [open, setOpen] = useState(false)

  function handleNav(link) {
    if (link.action === 'pricing') {
      onPricing?.()
      setOpen(false)
    }
  }

  return (
    <header className="fixed top-0 left-0 right-0 z-50 border-b border-slate-800/70 bg-[#06101D]/92 backdrop-blur-md transition-all">
      <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">

        {/* Logo */}
        <div
          className="flex items-center gap-2.5 cursor-pointer group"
          onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}
          aria-label="StatuteProof home"
        >
          <img
            src="/brand/regradar-logo-navbar.png"
            alt="StatuteProof"
            className="h-8 w-8 flex-shrink-0 object-contain transition-transform duration-300 group-hover:scale-105"
          />
          <span className="sp-display text-lg font-extrabold tracking-tight text-white">
            Statute<span className="text-[#16D9F5]">Proof</span>
          </span>
          <span className="sp-live-dot" />
        </div>

        {/* Desktop nav — center */}
        <nav className="hidden md:flex items-center gap-7 text-sm font-medium text-slate-400">
          {navLinks.map(l => (
            l.href ? (
              <a
                key={l.label}
                href={l.href}
                className="hover:text-cyan-300 transition-colors"
              >
                {l.label}
              </a>
            ) : (
              <button
                key={l.label}
                type="button"
                onClick={() => handleNav(l)}
                className="text-slate-400 hover:text-cyan-300 transition-colors"
              >
                {l.label}
              </button>
            )
          ))}
        </nav>

        {/* Desktop actions — right */}
        <div className="hidden md:flex items-center gap-2">
          <button
            onClick={onSignIn}
            className="inline-flex min-h-10 items-center gap-2 rounded-lg px-4 py-2 text-sm font-medium text-slate-400 hover:bg-slate-800/60 hover:text-slate-200"
          >
            Login
          </button>
          <button
            onClick={onCreateWorkspace}
            className="inline-flex min-h-10 items-center gap-2 rounded-lg border border-slate-700 bg-[#0D1B2E] px-4 py-2 text-sm font-semibold text-slate-200 hover:border-cyan-400/35 hover:bg-slate-800"
          >
            Register
          </button>
          <button
            onClick={onSourceReview}
            className="sp-btn-primary min-h-10 px-5 py-2 text-sm"
          >
            Get your free source readiness review
          </button>
        </div>

        {/* Mobile toggle */}
        <button
          className="md:hidden p-2 text-slate-400 hover:text-white transition-colors"
          onClick={() => setOpen(o => !o)}
          aria-label="Toggle menu"
        >
          {open ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
        </button>
      </div>

      {/* Mobile menu */}
      {open && (
        <div className="md:hidden bg-[#0A1628] border-t border-slate-800 px-6 py-5 flex flex-col gap-2">
          {navLinks.map(l => (
            l.href ? (
              <a
                key={l.label}
                href={l.href}
                onClick={() => setOpen(false)}
                className="text-sm font-medium text-slate-300 hover:text-[#16D9F5] transition-colors py-1.5"
              >
                {l.label}
              </a>
            ) : (
              <button
                key={l.label}
                type="button"
                onClick={() => handleNav(l)}
                className="py-1.5 text-left text-sm font-medium text-slate-300 hover:text-[#16D9F5]"
              >
                {l.label}
              </button>
            )
          ))}
          <div className="pt-3 border-t border-slate-800 flex flex-col gap-2 mt-1">
            <button
              onClick={() => { setOpen(false); onSignIn?.() }}
              className="text-sm font-medium text-slate-300 hover:text-[#16D9F5] py-2 text-center transition-colors"
            >
              Login
            </button>
            <button
              onClick={() => { setOpen(false); onCreateWorkspace?.() }}
              className="text-sm font-semibold text-slate-200 border border-slate-700 py-2.5 rounded-lg text-center hover:bg-slate-800 transition-colors"
            >
              Register
            </button>
            <button
              onClick={() => { setOpen(false); onSourceReview?.() }}
              className="text-sm font-bold bg-[#16D9F5] hover:bg-[#0EC8E4] text-[#07111F] py-2.5 rounded-lg text-center transition-colors"
            >
              Get your free source readiness review
            </button>
          </div>
        </div>
      )}
    </header>
  )
}
