import {
  Globe, Zap, Activity, BrainCircuit,
  Languages, MessageSquare, FileText, ShieldCheck,
  Search, BarChart2,
} from 'lucide-react'
import { features } from '../data/mockData'

const ICON_MAP = {
  Globe, Zap, Activity, BrainCircuit, Languages,
  MessageSquare, FileText, ShieldCheck, Search, BarChart2,
}

export default function Features() {
  return (
    <section className="py-20 bg-white" id="features">
      <div className="max-w-6xl mx-auto px-4 sm:px-6">

        <div className="text-center mb-12">
          <span className="inline-block text-xs font-semibold text-blue-600 uppercase tracking-widest mb-4">Capabilities</span>
          <h2 className="text-3xl font-bold text-slate-900 mb-3">What StatuteProof monitors and delivers</h2>
          <p className="text-slate-600 max-w-xl mx-auto">
            Every capability maps to a concrete compliance task — official source monitoring,
            source proof, evidence trail, and team-ready briefs.
          </p>
        </div>

        <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-5">
          {features.map(f => {
            const Icon = ICON_MAP[f.icon] || Globe
            return (
              <div
                key={f.title}
                className="group bg-slate-50 hover:bg-blue-50 border border-slate-200 hover:border-blue-200 rounded-xl p-5 transition-colors"
              >
                <div className="w-10 h-10 bg-white group-hover:bg-blue-100 rounded-lg border border-slate-200 group-hover:border-blue-200 flex items-center justify-center mb-4 transition-colors">
                  <Icon className="w-5 h-5 text-slate-500 group-hover:text-blue-600 transition-colors" />
                </div>
                <h3 className="font-semibold text-slate-800 text-sm mb-1.5">{f.title}</h3>
                <p className="text-xs text-slate-500 leading-relaxed">{f.desc}</p>
              </div>
            )
          })}
        </div>

      </div>
    </section>
  )
}
