import { useState, useMemo } from 'react'
import { CheckCircle2, ChevronRight, MapPin, Building2, Tag, Plus } from 'lucide-react'

const COUNTRIES = [
  'UAE', 'DIFC', 'ADGM', 'Other UAE source',
  'International standards',
]

const INDUSTRIES = [
  'Bank', 'Fintech', 'Payment institution',
  'Crypto / VASP', 'Microfinance',
  'Insurance', 'Investment firm / broker',
  'Law firm', 'Consulting',
  'Other / custom profile',
]

const TOPICS = [
  'Central bank', 'AML / CFT', 'Tax',
  'Licensing', 'Reporting', 'Payment services',
  'Sanctions', 'FATF / BIS',
]

const STEPS = [
  { id: 'countries', Icon: MapPin,    label: 'Where do you operate?' },
  { id: 'industry',  Icon: Building2, label: 'Your industry' },
  { id: 'topics',    Icon: Tag,       label: 'Regulatory topics' },
]

const TOPIC_SOURCES = {
  'Central bank':      ['Central banks', 'Financial regulators'],
  'AML / CFT':         ['AML / CFT monitoring', 'Sanctions lists'],
  'Tax':               ['Tax authorities', 'Finance ministries'],
  'Licensing':         ['Licensing authorities', 'Financial regulators'],
  'Reporting':         ['Financial regulators', 'Legal portals'],
  'Payment services':  ['Payment regulators', 'Financial regulators'],
  'Sanctions':         ['Sanctions lists', 'FATF / BIS / OECD'],
  'FATF / BIS':        ['FATF / BIS / OECD'],
}

const INDUSTRY_SOURCES = {
  'Bank':                  ['Central banks', 'Financial regulators', 'Legal portals'],
  'Fintech':               ['Payment regulators', 'Financial regulators', 'Licensing authorities'],
  'Payment institution':   ['Payment regulators', 'AML / CFT monitoring'],
  'Crypto / VASP':         ['Financial regulators', 'Sanctions lists', 'FATF / BIS / OECD'],
  'Microfinance':          ['Financial regulators', 'Licensing authorities'],
  'Insurance':             ['Financial regulators', 'Legal portals'],
  'Investment firm / broker': ['Financial regulators', 'Licensing authorities'],
  'Law firm':              ['Legal portals', 'Finance ministries'],
  'Consulting':            ['Legal portals', 'Financial regulators'],
}

const ALL_SOURCE_TYPES = [
  'Central banks', 'Financial regulators', 'Tax authorities',
  'AML / CFT monitoring', 'Finance ministries', 'Legal portals',
  'Licensing authorities', 'Payment regulators', 'Sanctions lists', 'FATF / BIS / OECD',
]

function CheckOption({ label, checked, onClick }) {
  return (
    <button
      onClick={onClick}
      className={`flex items-center gap-2.5 w-full text-left px-3 py-2.5 rounded-lg border text-sm transition-all ${
        checked
          ? 'border-[#16D9F5]/50 bg-[#16D9F5]/10 text-[#16D9F5] font-medium'
          : 'border-slate-700 bg-slate-900 text-slate-400 hover:border-slate-500 hover:text-white'
      }`}
    >
      <div className={`w-4 h-4 rounded flex items-center justify-center flex-shrink-0 border transition-colors ${
        checked ? 'bg-[#16D9F5] border-[#16D9F5]' : 'border-slate-600 bg-slate-800'
      }`}>
        {checked && (
          <svg className="w-2.5 h-2.5 text-[#07111F]" fill="none" viewBox="0 0 10 10">
            <path d="M2 5l2.5 2.5L8 3" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
        )}
      </div>
      {label}
    </button>
  )
}

export default function MonitoringProfile() {
  const [step, setStep]           = useState(0)
  const [countries, setCountries] = useState([])
  const [industry, setIndustry]   = useState([])
  const [topics, setTopics]       = useState([])

  const toggle = (arr, setArr, value) =>
    setArr(arr.includes(value) ? arr.filter(v => v !== value) : [...arr, value])

  const intlSelected  = countries.includes('International standards')
  const nonIntl       = countries.filter(c => c !== 'International standards')
  const hasCustom     = industry.includes('Other / custom profile')
  const mainIndustry  = industry.find(i => i !== 'Other / custom profile')
  const hasSelections = nonIntl.length > 0 || industry.length > 0 || topics.length > 0 || intlSelected

  const profileTitle = [
    mainIndustry || (industry.length ? 'Your industry' : null),
    nonIntl.length === 1
      ? nonIntl[0]
      : nonIntl.length > 1
      ? nonIntl.join(' + ')
      : null,
  ].filter(Boolean).join(' · ') || 'Your profile'

  const recommendedSources = useMemo(() => {
    const set = new Set()
    topics.forEach(t => (TOPIC_SOURCES[t] || []).forEach(s => set.add(s)))
    industry.filter(i => i !== 'Other / custom profile')
            .forEach(i => (INDUSTRY_SOURCES[i] || []).forEach(s => set.add(s)))
    if (nonIntl.length > 0) { set.add('Central banks'); set.add('Legal portals') }
    if (intlSelected) set.add('FATF / BIS / OECD')
    return [...set]
  }, [topics, industry, nonIntl, intlSelected])

  const scrollToContact = () =>
    document.querySelector('#contact').scrollIntoView({ behavior: 'smooth' })

  return (
    <section className="py-20 bg-[#07111F]" id="profile">
      <div className="max-w-6xl mx-auto px-4 sm:px-6">

        <div className="text-center mb-12">
          <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-slate-800/50 border border-slate-700 text-[#16D9F5] text-[11px] font-semibold mb-5 uppercase tracking-widest">
            Custom monitoring profile
          </div>
          <h2 className="text-3xl font-bold text-white mb-4">
            Build a monitoring setup for your company
          </h2>
          <p className="text-slate-400 max-w-2xl mx-auto">
            You choose the markets, industry and regulatory topics. StatuteProof selects the
            relevant source types, checks their monitoring readiness, and surfaces only the
            changes that apply to your business.
          </p>
        </div>

        <div className="grid lg:grid-cols-5 gap-6 items-start">

          {/* Wizard */}
          <div className="lg:col-span-3 bg-[#0D1B2E] rounded-2xl border border-slate-800 shadow-sm overflow-hidden">

            {/* Step tabs */}
            <div className="flex border-b border-slate-800">
              {STEPS.map(({ id, Icon, label }, idx) => {
                const active = step === idx
                const done   = step > idx
                return (
                  <button
                    key={id}
                    onClick={() => setStep(idx)}
                    className={`flex-1 flex flex-col items-center gap-1 py-4 px-2 text-xs font-medium transition-colors border-b-2 ${
                      active ? 'border-[#16D9F5] text-[#16D9F5] bg-[#16D9F5]/5'
                      : done  ? 'border-transparent text-emerald-400 bg-emerald-500/5 hover:bg-slate-800/30'
                              : 'border-transparent text-slate-500 hover:bg-slate-800/30 hover:text-slate-300'
                    }`}
                  >
                    <div className={`w-6 h-6 rounded-full flex items-center justify-center ${
                      active ? 'bg-[#16D9F5] text-[#07111F]'
                      : done  ? 'bg-emerald-500 text-white'
                              : 'bg-slate-700 text-slate-400'
                    }`}>
                      {done ? (
                        <svg className="w-3 h-3" fill="none" viewBox="0 0 10 10">
                          <path d="M2 5l2.5 2.5L8 3" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
                        </svg>
                      ) : (
                        <Icon className="w-3 h-3" />
                      )}
                    </div>
                    <span className="hidden sm:block text-center leading-tight">{label}</span>
                  </button>
                )
              })}
            </div>

            {/* Step content */}
            <div className="p-6">
              {step === 0 && (
                <>
                  <h3 className="font-semibold text-white mb-4">Where do you operate?</h3>
                  <div className="grid sm:grid-cols-2 gap-2">
                    {COUNTRIES.map(c => (
                      <CheckOption key={c} label={c} checked={countries.includes(c)}
                        onClick={() => toggle(countries, setCountries, c)} />
                    ))}
                  </div>
                </>
              )}

              {step === 1 && (
                <>
                  <h3 className="font-semibold text-white mb-4">What is your industry?</h3>
                  <div className="grid sm:grid-cols-2 gap-2">
                    {INDUSTRIES.map(i => (
                      <CheckOption key={i} label={i} checked={industry.includes(i)}
                        onClick={() => toggle(industry, setIndustry, i)} />
                    ))}
                  </div>
                  {hasCustom && (
                    <div className="mt-4 bg-[#16D9F5]/5 border border-[#16D9F5]/20 rounded-lg p-4 text-sm text-[#16D9F5]/80">
                      Describe your sector — StatuteProof will suggest a starting source set and show which can be connected automatically.
                    </div>
                  )}
                </>
              )}

              {step === 2 && (
                <>
                  <h3 className="font-semibold text-white mb-4">Which topics matter to you?</h3>
                  <div className="grid sm:grid-cols-2 gap-2">
                    {TOPICS.map(t => (
                      <CheckOption key={t} label={t} checked={topics.includes(t)}
                        onClick={() => toggle(topics, setTopics, t)} />
                    ))}
                  </div>
                  <div className="mt-5 border-t border-slate-800 pt-4">
                    <p className="text-xs text-slate-500 leading-relaxed">
                      <span className="font-medium text-slate-400">Can't find your regulator?</span>{' '}
                      On the demo call, you can add your own regulator websites — StatuteProof will test how reliably they can be connected for monitoring.
                    </p>
                  </div>
                </>
              )}
            </div>

            {/* Nav buttons */}
            <div className="px-6 pb-6 flex justify-between">
              <button
                onClick={() => setStep(s => Math.max(0, s - 1))}
                disabled={step === 0}
                className="text-sm text-slate-500 hover:text-slate-300 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
              >
                ← Back
              </button>
              {step < 2 ? (
                <button
                  onClick={() => setStep(s => s + 1)}
                  className="flex items-center gap-1.5 text-sm font-semibold bg-[#16D9F5] hover:bg-[#11c2db] text-[#07111F] px-4 py-2 rounded-lg transition-colors"
                >
                  Next <ChevronRight className="w-4 h-4" />
                </button>
              ) : (
                <button
                  onClick={scrollToContact}
                  className="flex items-center gap-1.5 text-sm font-semibold bg-[#16D9F5] hover:bg-[#11c2db] text-[#07111F] px-4 py-2 rounded-lg transition-colors"
                >
                  Build my profile on the demo <ChevronRight className="w-4 h-4" />
                </button>
              )}
            </div>
          </div>

          {/* Profile summary card */}
          <div className="lg:col-span-2">
            <div className="bg-slate-900 rounded-2xl p-6 text-white sticky top-24 space-y-5">

              <div>
                <div className="text-xs text-slate-400 uppercase tracking-wide mb-1">Your monitoring profile</div>
                <div className="text-lg font-bold text-white leading-snug min-h-[2.5rem]">
                  {profileTitle}
                </div>
              </div>

              <div className="space-y-2">
                <div className="flex items-center gap-2 text-sm">
                  <CheckCircle2 className={`w-4 h-4 flex-shrink-0 ${nonIntl.length ? 'text-emerald-400' : 'text-slate-600'}`} />
                  <span className={nonIntl.length ? 'text-white' : 'text-slate-500'}>
                    {nonIntl.length ? `${nonIntl.length} market${nonIntl.length > 1 ? 's' : ''} selected` : 'Select markets'}
                  </span>
                </div>
                <div className="flex items-center gap-2 text-sm">
                  <CheckCircle2 className={`w-4 h-4 flex-shrink-0 ${topics.length ? 'text-emerald-400' : 'text-slate-600'}`} />
                  <span className={topics.length ? 'text-white' : 'text-slate-500'}>
                    {topics.length ? `${topics.length} topic${topics.length > 1 ? 's' : ''} selected` : 'Select topics'}
                  </span>
                </div>
                <div className="flex items-center gap-2 text-sm">
                  <CheckCircle2 className={`w-4 h-4 flex-shrink-0 ${intlSelected ? 'text-emerald-400' : 'text-slate-600'}`} />
                  <span className={intlSelected ? 'text-white' : 'text-slate-500'}>
                    {intlSelected ? 'International standards included' : 'International standards'}
                  </span>
                </div>
              </div>

              <div className="border-t border-slate-700 pt-4">
                <div className="text-xs text-slate-400 mb-2.5">
                  {hasSelections ? 'Recommended source types:' : 'Available source types:'}
                </div>
                <div className="flex flex-wrap gap-1.5">
                  {(hasSelections ? recommendedSources : ALL_SOURCE_TYPES).map(s => (
                    <span
                      key={s}
                      className={`text-xs px-2 py-0.5 rounded-full border ${
                        hasSelections
                          ? 'bg-[#16D9F5]/10 text-[#16D9F5] border-[#16D9F5]/30'
                          : 'bg-slate-800 text-slate-500 border-slate-700'
                      }`}
                    >
                      {s}
                    </span>
                  ))}
                </div>
                <p className="text-xs text-slate-600 mt-2.5 leading-relaxed">
                  {hasSelections
                    ? 'Exact source list is generated from your selected markets, industry and topics.'
                    : 'Select parameters — StatuteProof will show the relevant source types.'}
                </p>
              </div>

              <div className="border-t border-slate-700 pt-4">
                <div className="text-xs text-slate-400 mb-2.5">StatuteProof will prepare:</div>
                <ul className="space-y-1.5">
                  {[
                    'Personalised source list for your profile',
                    'Reliability check for each source',
                    'Daily automated monitoring',
                    'AI compliance briefs in English',
                  ].map(item => (
                    <li key={item} className="flex items-start gap-2 text-sm text-slate-300">
                      <ChevronRight className="w-3.5 h-3.5 text-blue-400 flex-shrink-0 mt-0.5" />
                      {item}
                    </li>
                  ))}
                </ul>
              </div>

              <div className="border border-slate-700 rounded-xl p-4">
                <div className="text-xs font-medium text-slate-300 mb-1.5">Can't find your regulator?</div>
                <p className="text-xs text-slate-500 leading-relaxed mb-3">
                  Add regulator websites, ministry pages or legal portals. StatuteProof will test how reliably they can be connected for monitoring.
                </p>
                <button
                  onClick={scrollToContact}
                  className="flex items-center gap-1.5 text-xs text-[#16D9F5] hover:text-[#11c2db] transition-colors"
                >
                  <Plus className="w-3 h-3" />
                  Add custom sources on the demo
                </button>
              </div>

              <button
                onClick={scrollToContact}
                className="w-full text-sm font-semibold bg-[#16D9F5] hover:bg-[#11c2db] text-[#07111F] py-2.5 rounded-lg transition-colors"
              >
                Build my profile on the demo
              </button>

              <p className="text-center text-xs text-slate-600 leading-relaxed">
                Coverage is actively expanding. Demo sessions verify specific sources for your company.
              </p>

            </div>
          </div>

        </div>
      </div>
    </section>
  )
}
