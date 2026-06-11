const stats = [
  { value: '18',    label: 'Regulatory changes detected' },
  { value: '5',     label: 'Required compliance action' },
  { value: '~32 h', label: 'Manual monitoring hours saved' },
  { value: '<2 h',  label: 'Alert to brief delivery time' },
]

export default function TimeSavings() {
  return (
    <section className="py-20 bg-slate-50">
      <div className="max-w-6xl mx-auto px-4 sm:px-6">

        <div className="text-center mb-12">
          <h2 className="text-3xl font-bold text-slate-900 mb-3">
            Show leadership how much monitoring saves
          </h2>
          <p className="text-slate-600 max-w-2xl mx-auto">
            StatuteProof turns manual source checking into a measurable process: how many sources were
            checked, how many changes were found, and how many hours were saved.
          </p>
        </div>

        <div className="grid grid-cols-2 lg:grid-cols-4 gap-5 mb-6">
          {stats.map(s => (
            <div
              key={s.label}
              className="bg-white border border-slate-200 rounded-2xl p-6 text-center shadow-sm"
            >
              <div className="text-4xl font-bold text-blue-600 mb-2 tabular-nums">{s.value}</div>
              <div className="text-sm text-slate-600 leading-tight">{s.label}</div>
            </div>
          ))}
        </div>

        <p className="text-center text-xs text-slate-400 max-w-xl mx-auto">
          Illustrative figures. Actual savings depend on the number of sources and monitoring frequency.
        </p>

      </div>
    </section>
  )
}
