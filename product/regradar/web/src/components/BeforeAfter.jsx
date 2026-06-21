import { X, Check } from 'lucide-react'

const before = [
  'Manual checking across regulator portals',
  'Updates discovered late through peers, legal counsel, or clients',
  'No consistent proof trail',
  'Relevance checked manually',
  'Compliance review starts reactively',
]

const after = [
  'Scheduled official-source monitoring',
  'Meaningful changes surfaced for review',
  'Client profile relevance filtering',
  'Human review before client delivery',
  'Evidence-gated draft brief with official source URL, timestamp, extraction quality, and limitations',
]

export default function BeforeAfter() {
  return (
    <section className="py-20 bg-white">
      <div className="max-w-6xl mx-auto px-4 sm:px-6">

        <div className="text-center mb-12">
          <h2 className="text-3xl font-bold text-slate-900 mb-3">
            Without StatuteProof — and with it
          </h2>
          <p className="text-slate-600 max-w-xl mx-auto">
            Official-source monitoring is not just website checking. The value is a repeatable workflow:
            source run, evidence trail, relevance filter, human review, and a brief your team can verify.
          </p>
        </div>

        <div className="grid md:grid-cols-2 gap-6 max-w-4xl mx-auto">

          {/* Before */}
          <div className="bg-red-50 border border-red-200 rounded-2xl p-7">
            <div className="flex items-center gap-3 mb-6">
              <div className="w-8 h-8 rounded-full bg-red-100 flex items-center justify-center flex-shrink-0">
                <X className="w-4 h-4 text-red-500" />
              </div>
              <span className="font-bold text-slate-800 text-lg">Without StatuteProof</span>
            </div>
            <ul className="space-y-4">
              {before.map(item => (
                <li key={item} className="flex items-start gap-3 text-sm text-slate-600 leading-relaxed">
                  <X className="w-4 h-4 text-red-400 flex-shrink-0 mt-0.5" />
                  {item}
                </li>
              ))}
            </ul>
          </div>

          {/* After */}
          <div className="bg-emerald-50 border border-emerald-200 rounded-2xl p-7">
            <div className="flex items-center gap-3 mb-6">
              <div className="w-8 h-8 rounded-full bg-emerald-100 flex items-center justify-center flex-shrink-0">
                <Check className="w-4 h-4 text-emerald-600" />
              </div>
              <span className="font-bold text-slate-800 text-lg">With StatuteProof</span>
            </div>
            <ul className="space-y-4">
              {after.map(item => (
                <li key={item} className="flex items-start gap-3 text-sm text-slate-600 leading-relaxed">
                  <Check className="w-4 h-4 text-emerald-500 flex-shrink-0 mt-0.5" />
                  {item}
                </li>
              ))}
            </ul>
          </div>

        </div>
      </div>
    </section>
  )
}
