import { Building2, Landmark, Scale, ShieldCheck, BriefcaseBusiness, FileSearch } from 'lucide-react'

const PROFILES = [
  {
    icon: ShieldCheck,
    title: 'Crypto / VASP firms',
    sources: 'Primary regulators: VARA, CBUAE, UAE FIU',
    scope: 'Alert focus: VARA rulebook amendments, VASP licensing updates, CBUAE payment system notices that touch virtual assets, and UAE FIU AML/CFT guidance for virtual asset service providers. Not included by default: DFSA, ADGM/FSRA, UAE Ministry of Economy.',
  },
  {
    icon: Landmark,
    title: 'Payments and fintech',
    sources: 'Primary regulators: CBUAE, UAE FIU, Ministry of Finance',
    scope: 'Alert focus: CBUAE payment system regulations, licensing circulars, UAE FIU AML/CFT guidance for payment service providers, and Ministry of Finance financial policy notices. VARA is added only when virtual asset products are in scope.',
  },
  {
    icon: Building2,
    title: 'DIFC-regulated firms',
    sources: 'Primary regulators: DFSA, DIFC Laws, UAE FIU',
    scope: 'Alert focus after readiness review: DIFC primary and subsidiary legislation, plus DFSA rulebook and enforcement modules. UAE FIU is scoped only when a usable publications source clears readiness review.',
  },
  {
    icon: BriefcaseBusiness,
    title: 'ADGM-regulated firms',
    sources: 'Primary regulators: ADGM / FSRA, UAE FIU',
    scope: 'Alert focus after readiness review: ADGM/FSRA main-source updates and ADGM legislative context. FSRA rulebook/circular layers stay outside fresh-alert scope until source readiness checks clear. Not included by default: CBUAE, DFSA, VARA.',
  },
  {
    icon: FileSearch,
    title: 'AML and compliance consultants',
    sources: 'Primary regulators: UAE FIU, CBUAE, UAE Ministry of Economy, selected UAE CMA/DFSA sources',
    scope: 'Alert focus: UAE FIU typologies and guidance, CBUAE AML/CFT compliance notices, UAE Ministry of Economy beneficial ownership and AML policy, and selected SCA/DFSA AML/CFT guidance where relevant. Multi-client consultants can request separate monitoring profiles.',
  },
  {
    icon: Scale,
    title: 'Capital markets and law firms',
    sources: 'Primary regulators: UAE Capital Market Authority (UAE CMA), UAE Legislation Portal, Ministry of Finance, DIFC Laws',
    scope: 'Alert focus: selected capital markets updates, Ministry of Finance financial markets notices, and DIFC Laws changes. Source note: UAE CMA coverage is actively expanding and the UAE Legislation Portal is remediation, so federal-law alternatives must be confirmed before pilot setup.',
  },
]

export default function ConfiguredMonitoring() {
  return (
    <section className="py-20 bg-[#07111F]" id="configured-monitoring">
      <div className="max-w-6xl mx-auto px-4 sm:px-6">
        <div className="text-center mb-12">
          <span className="inline-block text-xs font-semibold text-cyan-300 uppercase tracking-widest mb-4">
            Alert Profiles
          </span>
          <h2 className="text-3xl font-bold text-white mb-3">
            Your alerts are matched to your regulatory profile
          </h2>
          <p className="text-slate-400 max-w-3xl mx-auto leading-relaxed">
            StatuteProof does not broadcast the same alert to every client. Each pilot is configured around
            your licence type, business activity, and the specific regulators relevant to your operations.
            A change at VARA is not relevant to a payments firm with no virtual asset exposure.
          </p>
        </div>

        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-5 mb-8">
          {PROFILES.map(profile => {
            const Icon = profile.icon
            return (
              <div key={profile.title} className="bg-[#0D1B2E] border border-slate-800 rounded-xl p-5 shadow-[0_14px_45px_rgba(0,0,0,0.22)]">
                <div className="w-10 h-10 rounded-lg bg-cyan-400/10 border border-cyan-400/20 flex items-center justify-center mb-4">
                  <Icon className="w-5 h-5 text-cyan-200" />
                </div>
                <h3 className="font-semibold text-white text-sm mb-2">{profile.title}</h3>
                <p className="text-xs font-semibold text-slate-300 mb-2">{profile.sources}</p>
                <p className="text-xs text-slate-500 leading-relaxed">{profile.scope}</p>
              </div>
            )
          })}
        </div>

        <div className="rounded-xl border border-cyan-400/20 bg-[#0D1B2E] p-6">
          <p className="text-sm text-slate-400 leading-relaxed max-w-4xl mx-auto text-center">
            Every pilot starts with a source readiness review that maps your specific regulators — and
            documents which sources are fresh-alert eligible, which have access limitations, and what your alert scope
            will be. No shared alert stream. No irrelevant sources.
          </p>
        </div>
      </div>
    </section>
  )
}
