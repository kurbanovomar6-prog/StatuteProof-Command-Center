import { ArrowRight, CheckCircle, ShieldCheck } from 'lucide-react'

export default function Contact({ onCreateWorkspace, onSignIn }) {
  return (
    <section className="py-20 bg-[#0A1628]" id="contact">
      <div className="max-w-6xl mx-auto px-4 sm:px-6">
        <div className="mx-auto max-w-4xl rounded-2xl border border-cyan-400/20 bg-[#0D1B2E] p-7 shadow-[0_20px_70px_rgba(0,0,0,0.28)] sm:p-10">
          <div className="grid gap-8 lg:grid-cols-[1fr_320px] lg:items-center">
            <div>
              <div className="mb-4 inline-flex items-center gap-2 rounded-full border border-cyan-400/20 bg-cyan-400/10 px-4 py-1.5 text-sm font-medium text-cyan-200">
                <ShieldCheck className="h-4 w-4" />
                Pilot workspace
              </div>
              <h2 className="mb-4 text-3xl font-bold text-white">
                Create your UAE source readiness workspace
              </h2>
              <p className="text-sm leading-relaxed text-slate-400 sm:text-base">
                Set up your StatuteProof pilot workspace, choose your UAE regulatory profile,
                and review source readiness before any monitoring commitment.
              </p>

              <div className="mt-6 grid gap-3 sm:grid-cols-2">
                {[
                  'Save your company and licence profile',
                  'Select UAE source layers that matter to your team',
                  'Connect Telegram for sample brief and reviewed alert previews',
                  'See which sources are readiness-supported, under validation, or limited',
                ].map(item => (
                  <div key={item} className="flex gap-2 text-sm leading-relaxed text-slate-300">
                    <CheckCircle className="mt-0.5 h-4 w-4 flex-shrink-0 text-emerald-300" />
                    <span>{item}</span>
                  </div>
                ))}
              </div>
              <p className="mt-5 text-xs leading-relaxed text-slate-500">
                StatuteProof is not legal advice. Source activation depends on technical validation.
              </p>
            </div>
            <div className="rounded-xl border border-slate-800 bg-slate-950/45 p-5">
              <p className="mb-4 text-xs font-semibold uppercase tracking-wide text-slate-500">
                Start in two minutes
              </p>
              <div className="flex flex-col gap-3">
                <button
                  type="button"
                  onClick={onCreateWorkspace}
                  className="inline-flex items-center justify-center gap-2 rounded-lg bg-[#16D9F5] px-5 py-3 text-sm font-bold text-[#07111F] transition-colors hover:bg-[#11c2db]"
                >
                  Create pilot workspace
                  <ArrowRight className="h-4 w-4" />
                </button>
                <button
                  type="button"
                  onClick={onSignIn}
                  className="inline-flex items-center justify-center rounded-lg border border-slate-700 px-5 py-3 text-sm font-semibold text-slate-300 transition-colors hover:border-slate-500 hover:text-white"
                >
                  Sign in
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}
