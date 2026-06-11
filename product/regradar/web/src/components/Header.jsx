import { useState } from 'react'
import { Menu, X } from 'lucide-react'

const navLinks = [
  { label: 'How It Works',    href: '#how-it-works' },
  { label: 'Source Coverage', href: '#coverage' },
  { label: 'Alert Profiles',  href: '#configured-monitoring' },
  { label: 'Evidence',        href: '#trust' },
  { label: 'Pricing',         href: '#pricing' },
]

export default function Header({ onSignIn, onCreateWorkspace }) {
  const [open, setOpen] = useState(false)

  return (
    <header className="fixed top-0 left-0 right-0 z-50 bg-[#0f172a]/90 backdrop-blur-md border-b border-slate-800">
      <div className="max-w-7xl mx-auto px-6 h-20 flex items-center justify-between">

        {/* Logo */}
        <div
          className="flex items-center gap-2.5 cursor-pointer group"
          onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}
          aria-label="StatuteProof home"
        >
          <img
            src="/brand/regradar-logo-navbar.png"
            alt="StatuteProof"
            className="h-9 w-9 flex-shrink-0 object-contain transition-transform duration-300 group-hover:scale-105"
          />
          <span className="text-xl font-extrabold tracking-normal text-white">
            Statute<span className="text-[#16D9F5]">Proof</span>
          </span>
        </div>

        {/* Desktop nav */}
        <nav className="hidden md:flex items-center gap-8 text-sm font-medium text-slate-300">
          {navLinks.map(l => (
            <a key={l.label} href={l.href}
              className="hover:text-[#16D9F5] transition-colors">
              {l.label}
            </a>
          ))}
        </nav>

        {/* Desktop actions */}
        <div className="hidden md:flex items-center gap-3">
          <button
            onClick={onSignIn}
            className="text-sm font-semibold text-slate-300 hover:text-[#16D9F5] transition-colors"
          >
            Sign in
          </button>
          <button
            onClick={onCreateWorkspace}
            className="text-sm font-bold bg-[#16D9F5] hover:bg-[#11c2db] text-[#07111F] px-5 py-2 rounded-lg transition-colors"
          >
            Create pilot workspace
          </button>
        </div>

        {/* Mobile toggle */}
        <button className="md:hidden p-2 text-slate-400 hover:text-white" onClick={() => setOpen(o => !o)}>
          {open ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
        </button>
      </div>

      {/* Mobile menu */}
      {open && (
        <div className="md:hidden bg-[#0f172a] border-t border-slate-800 px-6 py-4 flex flex-col gap-3">
          {navLinks.map(l => (
            <a key={l.label} href={l.href} onClick={() => setOpen(false)}
              className="text-sm font-medium text-slate-300 hover:text-[#16D9F5] transition-colors py-1">
              {l.label}
            </a>
          ))}
          <div className="pt-2 border-t border-slate-800 flex flex-col gap-2 mt-1">
            <button
              onClick={() => { setOpen(false); onSignIn?.() }}
              className="text-sm font-semibold text-slate-300 hover:text-[#16D9F5] py-2 text-center transition-colors"
            >
              Sign in
            </button>
            <button
              onClick={() => { setOpen(false); onCreateWorkspace?.() }}
              className="text-sm font-bold bg-[#16D9F5] text-[#07111F] py-2 rounded-lg text-center"
            >
              Create pilot workspace
            </button>
          </div>
        </div>
      )}
    </header>
  )
}
