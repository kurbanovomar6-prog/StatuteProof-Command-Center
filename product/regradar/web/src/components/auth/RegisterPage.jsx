import { useEffect, useState } from 'react'
import { CheckCircle, Eye, EyeOff, FileCheck2, LockKeyhole, Mail, ShieldCheck } from 'lucide-react'
import { auth } from '../../api'

const JOB_TITLES = [
  'MLRO',
  'CCO',
  'Head of Compliance',
  'Compliance Manager',
  'Legal Counsel',
  'Founder',
  'Other',
]

const COMPANY_TYPES = [
  'VARA-licensed VASP',
  'UAE fintech',
  'DFSA-authorised firm',
  'ADGM FSRA-regulated firm',
  'Compliance consultancy',
  'Law firm',
  'Other',
]

const JURISDICTIONS = [
  'Dubai / VARA',
  'DIFC / DFSA',
  'ADGM / FSRA',
  'UAE Federal',
  'Multiple',
]

function AuthLayout({ children }) {
  return (
    <div className="sp-page-orbit flex min-h-dvh items-center px-4 py-10 text-slate-200 selection:bg-[#16D9F5]/30">
      <div className="relative z-10 mx-auto grid w-full max-w-6xl items-center gap-8 lg:grid-cols-[0.78fr_0.92fr]">
        <aside className="hidden lg:block">
          <a href="/" className="mb-10 flex items-center gap-3 hover:opacity-80 transition-opacity">
            <img src="/brand/regradar-logo-navbar.png" alt="StatuteProof" className="h-10 w-auto" />
            <span className="text-2xl font-extrabold tracking-tight text-white">
              Statute<span className="text-[#16D9F5]">Proof</span>
            </span>
          </a>
          <div className="max-w-md">
            <div className="mb-5 inline-flex items-center gap-2 rounded-full border border-cyan-300/25 bg-cyan-300/10 px-3 py-1.5 text-xs font-semibold text-cyan-100">
              <ShieldCheck className="h-3.5 w-3.5" />
              Pilot workspace setup
            </div>
            <h2 className="text-4xl font-semibold leading-tight text-white">
              Create one accountable workspace per verified email.
            </h2>
            <p className="mt-5 text-base leading-relaxed text-slate-400">
              Registration captures the compliance profile needed to scope selected-source monitoring
              without implying complete regulatory coverage.
            </p>
          </div>

          <div className="mt-8 max-w-md rounded-3xl border border-slate-800 bg-slate-950/42 p-5">
            {[
              ['1', 'Account', 'case-insensitive unique work email'],
              ['2', 'Profile', 'licence type and primary jurisdiction'],
              ['3', 'Scope', 'source readiness before activation'],
            ].map(([num, title, detail]) => (
              <div key={title} className="flex gap-3 border-b border-slate-800 py-3 last:border-b-0">
                <span className="sp-mono flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-lg bg-cyan-300/10 text-sm font-bold text-cyan-200">
                  {num}
                </span>
                <div>
                  <p className="text-sm font-semibold text-white">{title}</p>
                  <p className="text-xs leading-relaxed text-slate-500">{detail}</p>
                </div>
              </div>
            ))}
            <div className="mt-4 flex items-start gap-2 rounded-2xl border border-amber-400/20 bg-amber-400/10 px-4 py-3 text-xs leading-relaxed text-amber-100/80">
              <FileCheck2 className="mt-0.5 h-4 w-4 flex-shrink-0 text-amber-200" />
              <span>Registration does not activate source monitoring or customer brief delivery.</span>
            </div>
          </div>
        </aside>

        <section className="sp-paper-panel w-full p-6 sm:p-8">
          {children}
        </section>
      </div>
    </div>
  )
}

export default function RegisterPage({ onRegister, onLogin }) {
  const [form, setForm] = useState({
    firstName: '',
    lastName: '',
    email: '',
    password: '',
    company: '',
    jobTitle: 'MLRO',
    companyType: 'VARA-licensed VASP',
    jurisdiction: 'Dubai / VARA',
  })
  const [showPass, setShowPass] = useState(false)
  const [verificationSent, setVerificationSent] = useState(false)
  const [verifiedEmail, setVerifiedEmail] = useState('')
  const [resendLoading, setResendLoading] = useState(false)
  const [resendMessage, setResendMessage] = useState('')
  const [termsAccepted, setTermsAccepted] = useState(false)
  const [privacyAccepted, setPrivacyAccepted] = useState(false)
  const [disclaimerAcknowledged, setDisclaimerAcknowledged] = useState(false)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [googleStatus, setGoogleStatus] = useState({ loading: true, available: false, message: '' })
  const set = key => e => setForm(f => ({ ...f, [key]: e.target.value }))

  useEffect(() => {
    let active = true
    auth.googleStatus()
      .then(data => {
        if (active) {
          setGoogleStatus({
            loading: false,
            available: Boolean(data.available),
            message: data.message || '',
          })
        }
      })
      .catch(() => {
        if (active) {
          setGoogleStatus({
            loading: false,
            available: false,
            message: 'Google sign-up is not configured for this environment.',
          })
        }
      })
    return () => { active = false }
  }, [])

  async function handleSubmit(e) {
    e.preventDefault()
    setError('')

    if (!termsAccepted || !privacyAccepted || !disclaimerAcknowledged) {
      setError('Please accept the terms, privacy policy, and legal disclaimer to continue.')
      return
    }
    if (!form.firstName.trim()) {
      setError('First name is required.')
      return
    }

    setLoading(true)
    try {
      const data = await auth.register({
        full_name: `${form.firstName.trim()} ${form.lastName.trim()}`.trim(),
        email: form.email,
        password: form.password,
        company_name: form.company,
        industry: form.companyType,
        job_title: form.jobTitle,
        company_type: form.companyType,
        jurisdiction: form.jurisdiction,
      })
      if (data.requires_verification) {
        setVerifiedEmail(data.email || form.email)
        setVerificationSent(true)
        return
      }
      onRegister(data.user)
    } catch (err) {
      setError(err.message || 'Could not create workspace.')
    } finally {
      setLoading(false)
    }
  }

  function handleGoogleRegister() {
    setError('')
    if (!googleStatus.available) {
      setError(googleStatus.message || 'Google sign-up is not configured for this environment.')
      return
    }
    window.location.assign(auth.googleStartUrl('/app'))
  }

  async function handleResend() {
    setResendLoading(true)
    setResendMessage('')
    try {
      const data = await auth.resendVerification(verifiedEmail)
      setResendMessage(data.message || 'Verification email sent. Check your inbox.')
    } catch (err) {
      setResendMessage(err.message || 'Could not resend verification email. Please try again.')
    } finally {
      setResendLoading(false)
    }
  }

  if (verificationSent) {
    return (
      <AuthLayout>
        <div className="flex flex-col items-center gap-6 py-4 text-center">
          <div className="flex h-16 w-16 items-center justify-center rounded-full border border-cyan-300/30 bg-cyan-300/10">
            <Mail className="h-8 w-8 text-cyan-300" />
          </div>
          <div>
            <h1 className="text-2xl font-semibold text-slate-950">Check your email</h1>
            <p className="mt-2 text-sm leading-relaxed text-slate-600">
              We sent a verification link to{' '}
              <span className="font-semibold text-slate-900">{verifiedEmail}</span>.
              Click the link in that email to activate your account.
            </p>
            <p className="mt-2 text-xs text-slate-500">The link expires after 24 hours.</p>
          </div>

          {resendMessage && (
            <div className="w-full rounded-xl border border-emerald-200 bg-emerald-50 px-3 py-2.5 text-sm text-emerald-800">
              {resendMessage}
            </div>
          )}

          <button
            type="button"
            onClick={handleResend}
            disabled={resendLoading}
            className="inline-flex min-h-11 w-full items-center justify-center gap-2 rounded-xl border border-slate-300 bg-white px-5 py-2.5 text-sm font-semibold text-slate-800 shadow-sm transition hover:border-cyan-400 hover:bg-cyan-50 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {resendLoading ? 'Sending...' : 'Resend verification email'}
          </button>

          <div className="border-t border-slate-200 pt-4 text-center text-sm text-slate-600">
            Already verified?{' '}
            <button
              onClick={onLogin}
              className="font-bold text-cyan-800 hover:underline focus:outline-none"
            >
              Sign in
            </button>
          </div>
        </div>
      </AuthLayout>
    )
  }

  const inputCls = 'w-full rounded-xl border border-slate-300 bg-white px-4 py-3 text-sm text-slate-950 placeholder:text-slate-400 shadow-sm focus:border-cyan-500 focus:outline-none focus:ring-4 focus:ring-cyan-500/10'
  const selectCls = 'w-full rounded-xl border border-slate-300 bg-white px-4 py-3 text-sm text-slate-950 shadow-sm focus:border-cyan-500 focus:outline-none focus:ring-4 focus:ring-cyan-500/10'
  const labelCls = 'block text-xs font-bold uppercase tracking-wide text-slate-600 mb-1.5'

  return (
    <AuthLayout>
      <div className="mb-7">
        <div className="mb-3 inline-flex items-center gap-2 rounded-full border border-cyan-300 bg-cyan-50 px-3 py-1 text-xs font-bold text-cyan-900 lg:hidden">
          <LockKeyhole className="h-3.5 w-3.5" />
          Pilot workspace setup
        </div>
        <h1 className="text-3xl font-semibold leading-tight text-slate-950">Create your StatuteProof workspace</h1>
        <p className="mt-2 text-sm leading-relaxed text-slate-600">
          One work email maps to one persisted account. Your profile helps scope the source-readiness review.
        </p>
      </div>

      <div className="mb-5">
        <button
          type="button"
          disabled={googleStatus.loading || !googleStatus.available}
          onClick={handleGoogleRegister}
          className={`flex min-h-12 w-full items-center justify-center gap-2.5 rounded-xl border py-3 text-sm font-semibold transition ${
            googleStatus.loading
              ? 'cursor-wait border-slate-200 bg-slate-50 text-slate-400'
              : googleStatus.available
                ? 'border-slate-300 bg-white text-slate-900 shadow-sm hover:border-cyan-400 hover:bg-cyan-50 hover:shadow-md active:scale-[0.99]'
                : 'cursor-not-allowed border-slate-200 bg-slate-50 text-slate-400'
          }`}
        >
          {!googleStatus.loading && (
            <svg className="h-4 w-4 flex-shrink-0" viewBox="0 0 24 24" aria-hidden="true">
              <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
              <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
              <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l3.66-2.84z"/>
              <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
            </svg>
          )}
          {googleStatus.loading
            ? 'Checking…'
            : googleStatus.available
              ? 'Continue with Google'
              : 'Google sign-up not available'}
        </button>
      </div>

      <div className="mb-5 flex items-center gap-3">
        <div className="h-px flex-1 bg-slate-200" />
        <span className="text-xs font-semibold text-slate-400">or register with email</span>
        <div className="h-px flex-1 bg-slate-200" />
      </div>

      <form className="space-y-4" onSubmit={handleSubmit}>
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
          <div>
            <label className={labelCls}>First name *</label>
            <input type="text" placeholder="First" value={form.firstName} onChange={set('firstName')} className={inputCls} required />
          </div>
          <div>
            <label className={labelCls}>Last name</label>
            <input type="text" placeholder="Last" value={form.lastName} onChange={set('lastName')} className={inputCls} />
          </div>
        </div>

        <div>
          <label className={labelCls}>Work email *</label>
          <input type="email" placeholder="name@company.com" value={form.email} onChange={set('email')} className={inputCls} required autoComplete="email" />
          <p className="mt-1.5 text-xs text-slate-500">Email uniqueness is checked case-insensitively after trimming spaces.</p>
        </div>

        <div>
          <label className={labelCls}>Password *</label>
          <div className="relative">
            <input
              type={showPass ? 'text' : 'password'}
              placeholder="Min. 8 characters"
              value={form.password}
              onChange={set('password')}
              className={`${inputCls} pr-11`}
              required
              minLength={8}
            />
            <button
              type="button"
              onClick={() => setShowPass(v => !v)}
              className="absolute right-2.5 top-1/2 flex h-9 w-9 -translate-y-1/2 items-center justify-center rounded-lg text-slate-500 hover:bg-slate-100 hover:text-slate-800"
              aria-label={showPass ? 'Hide password' : 'Show password'}
            >
              {showPass ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
            </button>
          </div>
        </div>

        <div>
          <label className={labelCls}>Company name *</label>
          <input type="text" placeholder="Your organisation" value={form.company} onChange={set('company')} className={inputCls} required />
        </div>

        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
          <div>
            <label className={labelCls}>Job title</label>
            <select value={form.jobTitle} onChange={set('jobTitle')} className={selectCls}>
              {JOB_TITLES.map(t => <option key={t}>{t}</option>)}
            </select>
          </div>
          <div>
            <label className={labelCls}>Company type</label>
            <select value={form.companyType} onChange={set('companyType')} className={selectCls}>
              {COMPANY_TYPES.map(t => <option key={t}>{t}</option>)}
            </select>
          </div>
        </div>

        <div>
          <label className={labelCls}>Primary jurisdiction</label>
          <select value={form.jurisdiction} onChange={set('jurisdiction')} className={selectCls}>
            {JURISDICTIONS.map(j => <option key={j}>{j}</option>)}
          </select>
        </div>

        <div className="space-y-3 rounded-2xl border border-slate-200 bg-slate-50 p-4">
          {[
            {
              id: 'terms',
              checked: termsAccepted,
              onChange: e => setTermsAccepted(e.target.checked),
              text: 'I agree to the StatuteProof Terms of Service.',
            },
            {
              id: 'privacy',
              checked: privacyAccepted,
              onChange: e => setPrivacyAccepted(e.target.checked),
              text: 'I agree to the StatuteProof Privacy Policy.',
            },
            {
              id: 'disclaimer',
              checked: disclaimerAcknowledged,
              onChange: e => setDisclaimerAcknowledged(e.target.checked),
              text: 'I understand StatuteProof provides monitoring intelligence and review-support summaries only. It does not provide legal advice or determine compliance outcomes.',
            },
          ].map(({ id, checked, onChange, text }) => (
            <label key={id} className="flex cursor-pointer items-start gap-3">
              <input
                type="checkbox"
                checked={checked}
                onChange={onChange}
                className="mt-0.5 h-4 w-4 flex-shrink-0 rounded border-slate-300 accent-cyan-700"
              />
              <span className="text-xs leading-relaxed text-slate-700">{text}</span>
            </label>
          ))}
        </div>

        {error && (
          <div className="rounded-xl border border-red-200 bg-red-50 px-3 py-2.5 text-sm text-red-800">
            {error}
          </div>
        )}

        <button
          type="submit"
          disabled={loading}
          className="inline-flex min-h-12 w-full items-center justify-center gap-2 rounded-xl bg-slate-950 px-5 py-3 text-sm font-bold text-white shadow-lg shadow-slate-900/20 transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-60"
        >
          {loading ? 'Creating workspace...' : 'Create workspace'}
        </button>
      </form>

      <div className="mt-5 flex items-start gap-2 rounded-2xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-xs leading-relaxed text-emerald-900">
        <CheckCircle className="mt-0.5 h-4 w-4 flex-shrink-0" />
        <span>Monitoring intelligence only. Not legal advice. Official source links included.</span>
      </div>

      <div className="mt-5 border-t border-slate-200 pt-5 text-center text-sm text-slate-600">
        Already have an account?{' '}
        <button onClick={onLogin} className="font-bold text-cyan-800 hover:underline focus:outline-none">
          Sign in
        </button>
      </div>
    </AuthLayout>
  )
}
