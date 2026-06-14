import { useState } from 'react'
import { CheckCircle, AlertTriangle, ArrowRight, Building2, Globe, Shield, Bell } from 'lucide-react'
import {
  COMPANY_TYPES, MARKETS, TOPICS, DELIVERY, RECOMMENDATIONS,
} from '../data/watchlistOptions'

// ── Payload builder ────────────────────────────────────────────────────────────

function buildSummaryText(company, markets, topics, delivery) {
  const mNames = markets.map(m => m.label).join(', ')
  const tNames = topics.map(t => t.label).join(', ')
  const dNames = delivery.length > 0 ? delivery.map(d => d.label).join(', ') : 'To be discussed'

  return [
    'Pilot request context:',
    `Company type: ${company.label}`,
    `Markets: ${mNames}`,
    `Topics: ${tNames}`,
    `Delivery: ${dNames}`,
    '',
    'Requested setup:',
    `Configure a regulatory watchlist focused on ${tNames.toLowerCase()} across ${mNames}.`,
    '',
    'Note: Actual pilot setup depends on confirmed official sources and access limitations per market.',
  ].join('\n')
}

// ── Helpers ────────────────────────────────────────────────────────────────────

function isRecommended(id, recs) {
  return recs ? recs.includes(id) : false
}

function ChipButton({ label, active, recommended, note, onClick }) {
  return (
    <button
      onClick={onClick}
      className={`relative text-left px-3 py-2 rounded-lg border text-xs font-medium transition-all ${
        active
          ? 'border-cyan-500/50 bg-cyan-500/10 text-cyan-300'
          : 'border-slate-700 bg-slate-800/60 text-slate-400 hover:border-slate-600 hover:text-slate-300'
      }`}
    >
      {label}
      {recommended && !active && (
        <span className="absolute -top-1.5 -right-1.5 text-[9px] font-bold bg-amber-500/20 text-amber-400 border border-amber-500/30 px-1 py-0.5 rounded-full leading-none">
          Rec
        </span>
      )}
      {note && (
        <span className="block text-[9px] text-slate-500 mt-0.5 font-normal">{note}</span>
      )}
    </button>
  )
}

function StepLabel({ number, label, icon: Icon }) {
  return (
    <div className="flex items-center gap-2.5 mb-3">
      <div className="flex items-center justify-center w-6 h-6 rounded-full bg-cyan-500/15 border border-cyan-500/30 text-cyan-400 text-[10px] font-bold flex-shrink-0">
        {number}
      </div>
      {Icon && <Icon className="w-3.5 h-3.5 text-slate-500 flex-shrink-0" />}
      <p className="text-xs font-semibold text-slate-300 uppercase tracking-wide">{label}</p>
    </div>
  )
}

// ── Watchlist Preview ──────────────────────────────────────────────────────────

function WatchlistPreview({ companyType, selectedMarkets, selectedTopics, selectedDelivery }) {
  const company  = COMPANY_TYPES.find(c => c.id === companyType)
  const markets  = MARKETS.filter(m => selectedMarkets.includes(m.id))
  const topics   = TOPICS.filter(t => selectedTopics.includes(t.id))
  const delivery = DELIVERY.filter(d => selectedDelivery.includes(d.id))

  const hasProfile = company && markets.length > 0 && topics.length > 0

  return (
    <div className="bg-[#0D1B2E] border border-slate-700/50 rounded-xl overflow-hidden">

      <div className="px-5 py-3.5 border-b border-slate-800 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Shield className="w-3.5 h-3.5 text-cyan-400" />
          <p className="text-xs font-semibold text-slate-300">Custom pilot preview</p>
        </div>
        <span className="text-[10px] font-medium bg-amber-500/15 text-amber-400 border border-amber-500/25 px-2 py-0.5 rounded-full">
          Illustrative
        </span>
      </div>

      {!hasProfile && (
        <div className="px-5 py-10 text-center">
          <p className="text-sm text-slate-500">Select your profile above to generate a preview.</p>
          <p className="text-xs text-slate-600 mt-1">Choose company type, at least one market, and at least one topic.</p>
        </div>
      )}

      {hasProfile && (
        <div className="divide-y divide-slate-800 text-xs">

          <div className="px-5 py-3.5">
            <p className="text-[10px] font-semibold text-slate-500 uppercase tracking-wide mb-1">Profile</p>
            <p className="text-slate-200 font-medium">{company.label}</p>
          </div>

          <div className="px-5 py-3.5">
            <p className="text-[10px] font-semibold text-slate-500 uppercase tracking-wide mb-1.5">Markets</p>
            <div className="flex flex-wrap gap-1.5">
              {markets.map(m => (
                <span key={m.id} className="bg-slate-800 border border-slate-700 text-slate-300 px-2 py-0.5 rounded-full">
                  {m.flag} {m.label}
                  {m.note && <span className="text-amber-400/70 ml-1">*</span>}
                </span>
              ))}
            </div>
          </div>

          <div className="px-5 py-3.5">
            <p className="text-[10px] font-semibold text-slate-500 uppercase tracking-wide mb-1.5">Monitoring focus</p>
            <ul className="space-y-1">
              {topics.map(t => (
                <li key={t.id} className="flex items-center gap-1.5 text-slate-300">
                  <CheckCircle className="w-3 h-3 text-emerald-400 flex-shrink-0" />
                  {t.label}
                </li>
              ))}
            </ul>
          </div>

          <div className="px-5 py-3.5">
            <p className="text-[10px] font-semibold text-slate-500 uppercase tracking-wide mb-1.5">What StatuteProof would deliver</p>
            <ul className="space-y-1">
              {[
                'Risk-ranked regulatory briefs',
                'Official source proof on each alert',
                delivery.length > 0 ? `Alerts via ${delivery.map(d => d.label).join(', ')}` : 'Alert delivery to be confirmed',
                'Source coverage transparency',
                'Weekly pilot summary',
              ].map(item => (
                <li key={item} className="flex items-center gap-1.5 text-slate-300">
                  <CheckCircle className="w-3 h-3 text-cyan-400 flex-shrink-0" />
                  {item}
                </li>
              ))}
            </ul>
          </div>

          <div className="px-5 py-3.5">
            <p className="text-[10px] font-semibold text-slate-500 uppercase tracking-wide mb-2">Example alert format</p>
            <div className="bg-slate-900/80 border border-slate-700/50 rounded-lg p-3 space-y-1.5">
              <div className="flex items-center gap-2">
                <span className="text-[10px] font-bold bg-red-500/15 text-red-400 border border-red-500/25 px-1.5 py-0.5 rounded-full">HIGH</span>
                <span className="text-slate-500 text-[10px]">
                  {markets[0]?.flag} {markets[0]?.label} · {topics[0]?.label}
                </span>
              </div>
              <p className="text-slate-300 text-[11px] font-medium leading-snug">
                Regulatory update detected from official source
              </p>
              <p className="text-slate-500 text-[10px] leading-relaxed">
                An update relevant to your watchlist profile was detected. Source proof and suggested review steps included.
              </p>
              <div className="flex items-center gap-1 text-[10px] text-emerald-400 pt-1">
                <Shield className="w-2.5 h-2.5" />
                <span>Source proof · Official source link · Not legal advice</span>
              </div>
            </div>
          </div>

          <div className="px-5 py-3.5">
            <div className="flex items-start gap-2">
              <AlertTriangle className="w-3 h-3 text-amber-400 flex-shrink-0 mt-0.5" />
              <div>
                <p className="text-[10px] font-semibold text-amber-400/80 uppercase tracking-wide mb-1">Coverage limitations</p>
                <p className="text-[11px] text-slate-400 leading-relaxed">
                  This preview is illustrative. Actual pilot setup depends on confirmed official sources and access limitations per market.
                  {markets.some(m => m.note) && (
                    <span className="block mt-1 text-amber-400/70">
                      * {markets.filter(m => m.note).map(m => `${m.label}: ${m.note}`).join(' · ')}
                    </span>
                  )}
                </p>
              </div>
            </div>
          </div>

        </div>
      )}
    </div>
  )
}

// ── Main component ─────────────────────────────────────────────────────────────

export default function ClientWatchlistBuilder({ onRequestPilot = () => {} }) {
  const [companyType,      setCompanyType]      = useState(null)
  const [selectedMarkets,  setSelectedMarkets]  = useState([])
  const [selectedTopics,   setSelectedTopics]   = useState([])
  const [selectedDelivery, setSelectedDelivery] = useState([])
  const [requested,        setRequested]        = useState(false)

  const recs = companyType ? RECOMMENDATIONS[companyType] : null

  function handleCompanyType(id) {
    const next = companyType === id ? null : id
    setCompanyType(next)
    if (next && RECOMMENDATIONS[next]) {
      const r = RECOMMENDATIONS[next]
      setSelectedMarkets(r.markets)
      setSelectedTopics(r.topics)
    } else if (!next) {
      setSelectedMarkets([])
      setSelectedTopics([])
    }
  }

  function toggleMarket(id) {
    setSelectedMarkets(prev =>
      prev.includes(id) ? prev.filter(m => m !== id) : [...prev, id]
    )
  }

  function toggleTopic(id) {
    setSelectedTopics(prev =>
      prev.includes(id) ? prev.filter(t => t !== id) : [...prev, id]
    )
  }

  function toggleDelivery(id) {
    setSelectedDelivery(prev =>
      prev.includes(id) ? prev.filter(d => d !== id) : [...prev, id]
    )
  }

  const hasWatchlist = companyType && selectedMarkets.length > 0 && selectedTopics.length > 0

  function handleRequestPilot() {
    if (!hasWatchlist) return
    const company  = COMPANY_TYPES.find(c => c.id === companyType)
    const markets  = MARKETS.filter(m => selectedMarkets.includes(m.id))
    const topics   = TOPICS.filter(t => selectedTopics.includes(t.id))
    const delivery = DELIVERY.filter(d => selectedDelivery.includes(d.id))
    const summaryText = buildSummaryText(company, markets, topics, delivery)
    onRequestPilot({ companyType: company, markets, topics, delivery, summaryText })
    setRequested(true)
    document.querySelector('#contact')?.scrollIntoView({ behavior: 'smooth' })
    setTimeout(() => setRequested(false), 4000)
  }

  return (
    <section className="py-20 bg-[#07111F]" id="watchlist-builder">
      <div className="max-w-6xl mx-auto px-4 sm:px-6">

        <div className="text-center mb-12">
          <span className="inline-block text-xs font-semibold text-cyan-400 uppercase tracking-widest mb-3">
            Configure your pilot
          </span>
          <h2 className="text-3xl font-bold text-white mb-4">
            Build your regulatory watchlist
          </h2>
          <p className="text-slate-400 max-w-2xl mx-auto leading-relaxed">
            Tell StatuteProof what kind of team you are, which markets matter, and which regulatory risks
            you want to track. The pilot is configured around your actual watchlist.
          </p>
        </div>

        <div className="grid lg:grid-cols-[1fr_400px] gap-8 items-start">

          {/* Left: configuration steps */}
          <div className="space-y-8">

            <div className="bg-[#0D1B2E] border border-slate-800 rounded-xl p-5">
              <StepLabel number="1" label="What type of company are you?" icon={Building2} />
              <div className="flex flex-wrap gap-2">
                {COMPANY_TYPES.map(c => (
                  <button
                    key={c.id}
                    onClick={() => handleCompanyType(c.id)}
                    className={`px-3.5 py-2 rounded-lg border text-xs font-medium transition-all ${
                      companyType === c.id
                        ? 'border-cyan-500/50 bg-cyan-500/10 text-cyan-300'
                        : 'border-slate-700 bg-slate-800/60 text-slate-400 hover:border-slate-600 hover:text-slate-300'
                    }`}
                  >
                    {c.label}
                  </button>
                ))}
              </div>
              {companyType && recs && (
                <p className="text-[11px] text-slate-500 mt-2.5">
                  Recommended markets and topics pre-filled. Adjust as needed.
                </p>
              )}
            </div>

            <div className="bg-[#0D1B2E] border border-slate-800 rounded-xl p-5">
              <StepLabel number="2" label="Which markets do you operate in?" icon={Globe} />
              <div className="flex flex-wrap gap-2">
                {MARKETS.map(m => (
                  <ChipButton
                    key={m.id}
                    label={`${m.flag} ${m.label}`}
                    active={selectedMarkets.includes(m.id)}
                    recommended={isRecommended(m.id, recs?.markets)}
                    note={m.note}
                    onClick={() => toggleMarket(m.id)}
                  />
                ))}
              </div>
              <p className="text-[11px] text-slate-600 mt-3">
                Market availability depends on confirmed official sources and access limitations.
              </p>
            </div>

            <div className="bg-[#0D1B2E] border border-slate-800 rounded-xl p-5">
              <StepLabel number="3" label="Which regulatory topics matter to you?" icon={Shield} />
              <div className="flex flex-wrap gap-2">
                {TOPICS.map(t => (
                  <ChipButton
                    key={t.id}
                    label={t.label}
                    active={selectedTopics.includes(t.id)}
                    recommended={isRecommended(t.id, recs?.topics)}
                    onClick={() => toggleTopic(t.id)}
                  />
                ))}
              </div>
            </div>

            <div className="bg-[#0D1B2E] border border-slate-800 rounded-xl p-5">
              <StepLabel number="4" label="How should alerts be delivered?" icon={Bell} />
              <div className="flex flex-wrap gap-2">
                {DELIVERY.map(d => (
                  <ChipButton
                    key={d.id}
                    label={d.label}
                    active={selectedDelivery.includes(d.id)}
                    onClick={() => toggleDelivery(d.id)}
                  />
                ))}
              </div>
            </div>

          </div>

          {/* Right: preview + CTAs (sticky on desktop) */}
          <div className="lg:sticky lg:top-8 space-y-4">
            <WatchlistPreview
              companyType={companyType}
              selectedMarkets={selectedMarkets}
              selectedTopics={selectedTopics}
              selectedDelivery={selectedDelivery}
            />

            <div className="space-y-2">
              <button
                onClick={handleRequestPilot}
                disabled={!hasWatchlist}
                className={`w-full flex items-center justify-center gap-2 px-5 py-3 rounded-xl text-sm font-semibold transition-all ${
                  requested
                    ? 'bg-emerald-500/20 border border-emerald-500/40 text-emerald-400 cursor-default'
                    : hasWatchlist
                    ? 'bg-cyan-500 hover:bg-cyan-400 text-slate-950'
                    : 'bg-slate-800 text-slate-600 cursor-not-allowed border border-slate-700'
                }`}
              >
                {requested ? (
                  <>
                    <CheckCircle className="w-4 h-4" />
                    Watchlist sent to contact form
                  </>
                ) : (
                  <>
                    Request pilot with this watchlist
                    <ArrowRight className="w-4 h-4" />
                  </>
                )}
              </button>
              <button
                onClick={() => document.querySelector('#contact')?.scrollIntoView({ behavior: 'smooth' })}
                className="w-full px-5 py-2.5 rounded-xl border border-slate-700 text-sm font-medium text-slate-400 hover:text-slate-300 hover:border-slate-600 transition-colors"
              >
                Discuss source coverage
              </button>
            </div>

            <div className="bg-slate-800/40 border border-slate-700/40 rounded-xl px-4 py-3">
              <p className="text-[11px] text-slate-500 leading-relaxed">
                StatuteProof does not claim complete legal coverage. Each pilot uses a confirmed set of
                official sources, with limitations documented in the source proof layer.
              </p>
            </div>
          </div>

        </div>

      </div>
    </section>
  )
}
