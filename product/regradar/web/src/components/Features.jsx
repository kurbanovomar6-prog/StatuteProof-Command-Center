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

// Stagger delay classes cycle through delay-1/2/3
const DELAY_CLASSES = ['sp-delay-1', 'sp-delay-2', 'sp-delay-3']

export default function Features() {
  return (
    <section className="py-20 bg-[#040B16]" id="features">
      <div className="max-w-6xl mx-auto px-4 sm:px-6">

        <div className="text-center mb-12">
          <span className="sp-badge-trust mb-4 inline-flex">Capabilities</span>
          <h2 className="sp-heading text-3xl text-white mb-3">What StatuteProof monitors and delivers</h2>
          <p className="text-slate-400 max-w-xl mx-auto">
            Every capability maps to a concrete compliance task — official source monitoring,
            source proof, evidence trail, and team-ready briefs.
          </p>
        </div>

        <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-5">
          {features.map((f, index) => {
            const Icon = ICON_MAP[f.icon] || Globe
            const delayClass = DELAY_CLASSES[index % DELAY_CLASSES.length]
            return (
              <div
                key={f.title}
                className={`sp-glass group rounded-xl p-5 transition-all duration-200 hover:-translate-y-1 hover:shadow-[0_8px_32px_rgba(25,211,243,0.08)] sp-animate-fade-up ${delayClass}`}
              >
                <div className="sp-badge-trust p-2 rounded-xl mb-4 inline-flex items-center justify-center">
                  <Icon className="w-5 h-5 text-cyan-300" />
                </div>
                <h3 className="font-semibold text-slate-100 text-sm mb-1.5">{f.title}</h3>
                <p className="text-xs text-slate-400 leading-relaxed">{f.desc}</p>
              </div>
            )
          })}
        </div>

      </div>
    </section>
  )
}
