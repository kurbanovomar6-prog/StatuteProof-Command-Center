import { Building2, Landmark, Scale, ShieldCheck, BriefcaseBusiness, FileSearch } from 'lucide-react'

const PROFILES = [
  {
    icon: ShieldCheck,
    title: 'Crypto / VASP firms',
    sources: 'Primary regulators: VARA, CBUAE, UAE CMA, EOCN',
    scope: 'Alert focus: VARA rulebook revision updates and enforcement notices, CBUAE Payment Token Services Regulation, UAE CMA virtual-asset rules, and EOCN sanctions/TFS updates. UAE FIU is geo-restricted and not offered as an alert layer today. Not included by default: DFSA, ADGM/FSRA, UAE Ministry of Economy.',
  },
  {
    icon: Landmark,
    title: 'Payments and fintech',
    sources: 'Primary regulators: CBUAE, Ministry of Finance, UAE CMA',
    scope: 'Alert focus: CBUAE rulebook payment regulations (payment token, retail payment services, stored value, open finance), CBUAE AML/CFT modules, Ministry of Finance financial policy notices, and the UAE CMA fintech sandbox. VARA is added only when virtual asset products are in scope.',
  },
  {
    icon: Building2,
    title: 'DIFC-regulated firms',
    sources: 'Primary regulators: DFSA, DIFC Laws',
    scope: 'Alert focus after readiness review: DIFC laws, legal database and data protection, plus DFSA rulebook (including the AML module), consultations, enforcement and MLRO letters. UAE FIU is geo-restricted; FIU-layer alerts are not offered until an accessible official route clears readiness review.',
  },
  {
    icon: BriefcaseBusiness,
    title: 'ADGM-regulated firms',
    sources: 'Primary regulators: ADGM / FSRA',
    scope: 'Alert focus after readiness review: FSRA rules and regulations, guidance and policy statements, supervision circulars, financial/cyber crime prevention and public consultations. FSRA regulatory alerts, waivers register and RA circulars remain candidate layers until validation clears. Not included by default: CBUAE, DFSA, VARA.',
  },
  {
    icon: FileSearch,
    title: 'AML and compliance consultants',
    sources: 'Primary regulators: EOCN, CBUAE, UAE Ministry of Economy, selected UAE CMA/DFSA sources',
    scope: 'Alert focus: EOCN sanctions/TFS and AML/CFT law updates, CBUAE AML/CFT rulebook sections, UAE Ministry of Economy beneficial ownership and DNFBP AML policy, and selected UAE CMA/DFSA AML/CFT sources. The UAE FIU website is geo-restricted and disclosed as a gap, not sold as covered. Multi-client consultants can request separate monitoring profiles.',
  },
  {
    icon: Scale,
    title: 'Capital markets and law firms',
    sources: 'Primary regulators: UAE Capital Market Authority (UAE CMA), Ministry of Finance, DIFC Laws',
    scope: 'Alert focus: UAE CMA circulars, regulations listing and corporate governance rules, Ministry of Finance financial markets notices, and DIFC Laws changes. Source note: the UAE Legislation Portal is geo-restricted from outside the UAE, so federal-law alternatives must be confirmed before pilot setup.',
  },
]

export default function ConfiguredMonitoring() {
  return (
    <section className="py-20 bg-[var(--bg-navy)]" id="configured-monitoring">
      <div className="max-w-6xl mx-auto px-4 sm:px-6">
        <div className="text-center mb-12">
          {/* Pill kicker (matches sibling sections) — no uppercase eyebrows per design system. */}
          <div className="mb-4 inline-flex items-center rounded-full border border-cyan-400/20 bg-cyan-400/10 px-4 py-1.5 text-sm font-medium text-cyan-200">
            Alert profiles
          </div>
          <h2 className="text-3xl font-bold text-white mb-3">
            Your alerts are matched to your regulatory profile
          </h2>
          <p className="text-[var(--text-secondary)] max-w-3xl mx-auto leading-relaxed">
            StatuteProof does not broadcast the same alert to every client. Each pilot is configured around
            your licence type, business activity, and the specific regulators relevant to your operations.
            A change at VARA is not relevant to a payments firm with no virtual asset exposure.
          </p>
        </div>

        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-5 mb-8">
          {PROFILES.map(profile => {
            const Icon = profile.icon
            return (
              <div key={profile.title} className="bg-[var(--bg-elevated)] border border-[var(--border-muted)] rounded-xl p-5 shadow-[0_14px_45px_rgba(0,0,0,0.22)]">
                <div className="w-10 h-10 rounded-lg bg-cyan-400/10 border border-cyan-400/20 flex items-center justify-center mb-4">
                  <Icon className="w-5 h-5 text-cyan-200" />
                </div>
                <h3 className="font-semibold text-white text-sm mb-2">{profile.title}</h3>
                <p className="text-xs font-semibold text-[var(--text-secondary)] mb-2">{profile.sources}</p>
                <p className="text-xs text-[var(--text-muted)] leading-relaxed">{profile.scope}</p>
              </div>
            )
          })}
        </div>

        <div className="rounded-xl border border-cyan-400/20 bg-[var(--bg-elevated)] p-6">
          <p className="text-sm text-[var(--text-secondary)] leading-relaxed max-w-4xl mx-auto text-center">
            Every pilot starts with a source readiness review that maps your specific regulators — and
            documents which sources are fresh-alert eligible, which have access limitations, and what your alert scope
            will be. No shared alert stream. No irrelevant sources.
          </p>
        </div>
      </div>
    </section>
  )
}
