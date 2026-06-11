export const sourceHealthRows = [
  { id: 1, name: 'Central Bank of the UAE (CBUAE)',          jurisdiction: 'AE',  flag: '🇦🇪', access: 'Active', quality: 'good', status: 'active',  verdict: 'PASS' },
  { id: 2, name: 'Virtual Assets Regulatory Authority (VARA)', jurisdiction: 'AE', flag: '🇦🇪', access: 'Active', quality: 'good', status: 'active', verdict: 'PASS' },
  { id: 3, name: 'Dubai Financial Services Authority (DFSA)', jurisdiction: 'AE', flag: '🇦🇪', access: 'Active', quality: 'good', status: 'active', verdict: 'PASS' },
  { id: 4, name: 'ADGM / Financial Services Regulatory Authority (FSRA)', jurisdiction: 'AE', flag: '🇦🇪', access: 'Active', quality: 'good', status: 'active', verdict: 'PASS' },
  { id: 5, name: 'UAE Financial Intelligence Unit (UAE FIU)', jurisdiction: 'AE', flag: '🇦🇪', access: 'Active', quality: 'good', status: 'active', verdict: 'PASS' },
  { id: 6, name: 'Ministry of Finance',                       jurisdiction: 'AE', flag: '🇦🇪', access: 'Active', quality: 'good', status: 'active', verdict: 'PASS' },
  { id: 7, name: 'UAE Legislation Portal',                     jurisdiction: 'AE', flag: '🇦🇪', access: 'Active', quality: 'good', status: 'active', verdict: 'PASS' },
  { id: 8, name: 'DIFC Laws',                                  jurisdiction: 'AE', flag: '🇦🇪', access: 'Active', quality: 'good', status: 'active', verdict: 'PASS' },
  { id: 9, name: 'Ministry of Economy',                        jurisdiction: 'AE', flag: '🇦🇪', access: 'Active', quality: 'good', status: 'active', verdict: 'PASS' },
  { id: 10, name: 'Federal Tax Authority (FTA)',                jurisdiction: 'AE', flag: '🇦🇪', access: 'Limited', quality: 'low_content', status: 'limited', verdict: 'REVIEW' },
  { id: 11, name: 'Official Gazette / Al-Jaridah Al-Rasmiah',  jurisdiction: 'AE', flag: '🇦🇪', access: 'Blocked', quality: 'failed', status: 'disabled', verdict: 'FAIL' },
]

export const riskTrendData = [
  { week: 'Apr W1', HIGH: 1, MEDIUM: 2, LOW: 4 },
  { week: 'Apr W2', HIGH: 0, MEDIUM: 3, LOW: 4 },
  { week: 'Apr W3', HIGH: 2, MEDIUM: 1, LOW: 4 },
  { week: 'Apr W4', HIGH: 1, MEDIUM: 2, LOW: 4 },
  { week: 'May W1', HIGH: 3, MEDIUM: 2, LOW: 2 },
  { week: 'May W2', HIGH: 1, MEDIUM: 3, LOW: 3 },
  { week: 'May W3', HIGH: 0, MEDIUM: 2, LOW: 5 },
]

export const features = [
  { icon: 'Search',        title: 'Official-source monitoring',      desc: 'StatuteProof monitors configured official regulator, legal, finance, free zone, and AML/CFT sources after readiness checks and source access validation.' },
  { icon: 'FileText',      title: 'Source-backed compliance briefs', desc: 'Every detected change produces a structured brief: what changed, which official source confirmed it, and what your profile requires next.' },
  { icon: 'Globe',         title: 'Documented extraction methods',    desc: 'HTML structured content, PDF text, or page snapshots are recorded per source so limitations are visible.' },
  { icon: 'MessageSquare', title: 'Profile-scoped alert delivery',    desc: 'Alerts are scoped to the regulators and business activities that apply to your licence type and risk exposure.' },
  { icon: 'BarChart2',     title: 'Source readiness reporting',       desc: 'Source checks show active, limited, and blocked sources before a pilot begins, with access restrictions documented.' },
  { icon: 'BrainCircuit',  title: 'Client-specific source profiles',  desc: 'Configure the exact regulators, jurisdictions, and compliance topics relevant to your business. No irrelevant sources.' },
  { icon: 'Languages',     title: 'English compliance briefs',        desc: 'Official source content is converted into concise English briefs while preserving proof back to the original source.' },
  { icon: 'ShieldCheck',   title: 'Evidence trail on every alert',    desc: 'Every alert includes source URL, timestamp, delta status, extraction quality, evidence snippet, and known limitations.' },
]

export const coverage = [
  { flag: '🇦🇪', region: 'UAE', sources: ['CBUAE', 'VARA', 'DFSA', 'ADGM/FSRA', 'UAE FIU', 'Ministry of Finance', 'UAE Legislation Portal', 'DIFC Laws', 'Ministry of Economy'] },
]

export const pricingPlans = [
  {
    name: 'Source Readiness Review',
    price: 'Free',
    period: 'one-time source readiness assessment',
    highlight: true,
    badge: 'Start here',
    ctaType: 'workspace',
    desc: 'Create a workspace and save your regulatory profile. StatuteProof uses it to prepare a structured source readiness view before any monitoring commitment.',
    features: [
      'Named regulators reviewed',
      'Active / Limited / Blocked status per source',
      'Extraction quality assessment',
      'Pilot scope recommendation',
      'Known gaps documented',
      'Sample brief format included',
    ],
    cta: 'Create pilot workspace',
  },
  {
    name: 'Founding Pilot',
    price: '$99',
    period: '/ month',
    highlight: false,
    ctaType: 'workspace',
    desc: '5-8 validated official sources matched to your regulatory profile. Reviewed brief previews include source proof, delta status, and extraction quality. Founding pilot pricing.',
    features: [
      '1 regulatory profile',
      'Validated source scope matched to your profile',
      'Profile relevance filtering',
      'Evidence-backed brief previews',
      'Source proof on every reviewed alert',
      'Human review before client delivery',
      'Limitations disclosed in pilot setup',
    ],
    cta: 'Create pilot workspace',
  },
  {
    name: 'Profile Pilot',
    price: '$249',
    period: '/ month',
    highlight: false,
    ctaType: 'workspace',
    desc: 'Broader source profile across your selected regulators. Risk-ranked reviewed previews and source readiness reporting matched to your regulatory profile.',
    features: [
      'Extended source profile',
      'Validated official source set',
      'Profile-scoped review queue',
      'Source-backed action briefs with proof',
      'Human-reviewed preview summaries',
      'Source readiness reporting',
    ],
    cta: 'Build your source profile',
  },
  {
    name: 'Custom Profile',
    price: '$499',
    period: '/ month',
    highlight: false,
    ctaType: 'workspace',
    desc: 'Built around your specific regulators, jurisdictions, and compliance domains. Source validation and onboarding included. Custom alert frequency.',
    features: [
      'Custom source selection and validation',
      'Dedicated monitoring profile',
      'Custom alert frequency',
      'Source onboarding included',
      'Reviewed executive brief preview',
    ],
    cta: 'Create pilot workspace',
  },
]

export const steps = [
  { n: '01', title: 'Source readiness assessment', desc: 'Each official source is tested before monitoring begins: is it accessible? What extraction method does it require? What is the quality of extracted content? Active, Limited, and Blocked sources are documented. You see this before agreeing to a pilot.' },
  { n: '02', title: 'Scheduled source monitoring', desc: 'Configured sources are checked on a defined schedule. Each run produces a delta status: FIRST_SEEN, UNCHANGED, CHANGED, FAILED, or QUALITY_DROP.' },
  { n: '03', title: 'Change detection and quality check', desc: 'When a source returns CHANGED, extracted content is compared against the prior run. When extraction quality drops below threshold, the run is flagged for human review before any alert is issued.' },
  { n: '04', title: 'Profile relevance matching', desc: 'Detected changes are evaluated against your regulatory profile — your licence type, business activity, and monitored regulators. A VARA update does not go to a payments firm with no virtual asset exposure.' },
  { n: '05', title: 'Evidence-backed brief', desc: 'Your team receives a structured brief: what changed, which official source confirmed it, source URL, timestamp, extraction quality, evidence snippet, known limitations, and a not-legal-advice disclaimer. Every brief is verifiable against the original source.' },
]
