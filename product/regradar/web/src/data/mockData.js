export const sourceHealthRows = [
  { id: 1,  name: 'CBUAE Main',                  jurisdiction: 'AE', flag: '🇦🇪', access: 'Accessible', quality: 'readiness_supported', status: 'readiness_supported', verdict: 'READINESS' },
  { id: 2,  name: 'CBUAE Regulations',           jurisdiction: 'AE', flag: '🇦🇪', access: 'Accessible', quality: 'readiness_supported', status: 'readiness_supported', verdict: 'READINESS' },
  { id: 3,  name: 'UAE Ministry of Finance',     jurisdiction: 'AE', flag: '🇦🇪', access: 'Accessible', quality: 'readiness_supported', status: 'readiness_supported', verdict: 'READINESS' },
  { id: 4,  name: 'VARA Main',                   jurisdiction: 'AE', flag: '🇦🇪', access: 'Accessible', quality: 'readiness_supported', status: 'readiness_supported', verdict: 'READINESS' },
  { id: 5,  name: 'VARA Enforcement Notices',    jurisdiction: 'AE', flag: '🇦🇪', access: 'Accessible', quality: 'readiness_supported', status: 'readiness_supported', verdict: 'READINESS' },
  { id: 6,  name: 'ADGM FSRA Main',              jurisdiction: 'AE', flag: '🇦🇪', access: 'Accessible', quality: 'readiness_supported', status: 'readiness_supported', verdict: 'READINESS' },
  { id: 7,  name: 'UAE FIU Circulars',           jurisdiction: 'AE', flag: '🇦🇪', access: 'Accessible', quality: 'readiness_supported', status: 'readiness_supported', verdict: 'READINESS' },
  { id: 8,  name: 'DIFC Laws and Regulations',   jurisdiction: 'AE', flag: '🇦🇪', access: 'Accessible', quality: 'readiness_supported', status: 'readiness_supported', verdict: 'READINESS' },
  { id: 9,  name: 'UAE Legislation Portal',      jurisdiction: 'AE', flag: '🇦🇪', access: 'Accessible', quality: 'readiness_supported', status: 'readiness_supported', verdict: 'READINESS' },
  { id: 10, name: 'UAE Ministry of Economy',     jurisdiction: 'AE', flag: '🇦🇪', access: 'Accessible', quality: 'readiness_supported', status: 'readiness_supported', verdict: 'READINESS' },
  { id: 11, name: 'DFSA Annual Reports',          jurisdiction: 'AE', flag: '🇦🇪', access: 'Active',                 quality: 'monitoring_active', status: 'monitoring_active', verdict: 'ACTIVE' },
  { id: 12, name: 'DFSA Annual AML Reports',     jurisdiction: 'AE', flag: '🇦🇪', access: 'Active',                 quality: 'monitoring_active', status: 'monitoring_active', verdict: 'ACTIVE' },
  { id: 13, name: 'UAE FIU Homepage',            jurisdiction: 'AE', flag: '🇦🇪', access: 'Covered via sub-sources', quality: 'sub_sources',       status: 'sub_sources',       verdict: 'COVERED' },
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
  { icon: 'Search',        title: 'Official-source monitoring',      desc: 'Your monitored UAE regulatory sources are checked on a defined schedule — CBUAE, VARA, DFSA, ADGM/FSRA, UAE FIU, and more. When something changes on an official portal, you know about it from the source, not from a peer.' },
  { icon: 'FileText',      title: 'Source-backed compliance briefs', desc: 'Every detected change produces a structured brief: what changed, which official source published it, and what your licence profile requires next. No raw text dumps — a brief you can act on.' },
  { icon: 'Globe',         title: 'Documented extraction methods',    desc: 'You see exactly how each source is monitored — HTML, PDF, or page snapshot — and any known limitations are disclosed upfront. If a source has restricted access, that is documented before your pilot begins.' },
  { icon: 'MessageSquare', title: 'Profile-scoped alert delivery',    desc: 'Alerts are filtered to the regulators and business activities relevant to your licence type. A VARA update does not reach a payments firm with no virtual asset exposure.' },
  { icon: 'BarChart2',     title: 'Source readiness reporting',       desc: 'Before monitoring begins, you receive a clear view of which UAE regulatory sources are accessible, which are PDF-primary, and which are currently out of scope. No surprises after sign-off.' },
  { icon: 'BrainCircuit',  title: 'Client-specific source profiles',  desc: 'Configure the exact regulators, jurisdictions, and compliance topics relevant to your business. No noise from sources that do not apply to your licence type.' },
  { icon: 'Languages',     title: 'English compliance briefs',        desc: 'Official source content from Arabic or mixed-language portals is summarised in English briefs, with a direct link back to the original source so you can verify the primary text.' },
  { icon: 'ShieldCheck',   title: 'Evidence trail on every alert',    desc: 'Every alert carries a source URL, timestamp, change delta, extraction quality rating, and evidence snippet. When your board asks how a change was caught, you have a documented record.' },
]

export const coverage = [
  {
    flag: '🇦🇪',
    region: 'UAE',
    sources: [
      { name: 'CBUAE Main', status: 'readiness_supported' },
      { name: 'CBUAE Regulations', status: 'readiness_supported' },
      { name: 'UAE Ministry of Finance', status: 'readiness_supported' },
      { name: 'VARA Main', status: 'readiness_supported' },
      { name: 'VARA Enforcement Notices', status: 'readiness_supported' },
      { name: 'ADGM FSRA Main', status: 'readiness_supported' },
      { name: 'UAE FIU Circulars', status: 'readiness_supported' },
      { name: 'DIFC Laws and Regulations', status: 'readiness_supported' },
      { name: 'UAE Legislation Portal', status: 'readiness_supported' },
      { name: 'UAE Ministry of Economy', status: 'readiness_supported' },
      { name: 'DFSA Annual Reports', status: 'monitoring_active' },
      { name: 'DFSA Annual AML Reports', status: 'monitoring_active' },
      { name: 'UAE FIU Homepage', status: 'sub_sources' },
    ],
  },
]

export const pricingPlans = [
  {
    name: 'Source Readiness Review',
    price: 'Free',
    period: 'source readiness assessment',
    highlight: false,
    badge: 'Start here',
    ctaType: 'source_review',
    desc: 'Before committing to monitoring, know exactly which UAE regulatory sources are accessible for your licence type, what content can be extracted, and what is currently out of scope.',
    features: [
      'UAE source pack readiness view',
      'Extraction quality and failure reasons',
      'Known limitations documented',
      'Pilot scope recommendation',
      'Sample brief format included',
    ],
    cta: 'Request source readiness review',
  },
  {
    name: 'Founding Pilot',
    price: '$199',
    period: '/ month',
    highlight: false,
    ctaType: 'plan',
    routePlan: 'starter_pilot',
    desc: 'For a compliance officer who wants to monitor 3 core UAE sources with full evidence records. Manually activated after source readiness review.',
    features: [
      '1 regulatory profile',
      'Up to 3 official UAE sources',
      'Evidence records and basic diff view',
      '30-day evidence retention',
      'Source status summary',
      'Manual activation after review',
    ],
    cta: 'Start founding pilot',
  },
  {
    name: 'UAE Monitor',
    price: '$399',
    period: '/ month',
    highlight: true,
    badge: 'Recommended',
    ctaType: 'plan',
    routePlan: 'professional',
    desc: 'Selected official UAE regulatory source pack across VARA, CBUAE, DFSA, ADGM, FIU, DIFC and related public authorities. Built for an MLRO who needs evidence that regulatory changes were tracked.',
    features: [
      '146 monitoring-active official-source endpoints',
      'Priority review queue for high-risk changes',
      'Weekly monitoring brief (activation required)',
      'Up to 2 custom sources after review',
      '180-day evidence retention',
      '2 users',
    ],
    cta: 'Upgrade to UAE Monitor',
  },
  {
    name: 'Compliance Consultant',
    price: 'Talk to us',
    period: '',
    highlight: false,
    ctaType: 'consultant',
    desc: 'For advisory firms with multiple UAE-regulated clients. Custom scope and retention reviewed per engagement.',
    features: [
      'Custom source scope',
      'Consultant workflow review',
      'Extended retention options',
      'Multiple workspaces on pilot roadmap',
      'White-label reports on pilot roadmap',
    ],
    cta: 'Talk to us',
  },
]

export const steps = [
  { n: '01', title: 'Source readiness assessment', desc: 'Each official source is tested before monitoring begins: is it accessible? What extraction method does it require? What is the quality of extracted content? Readiness-supported, limited, and blocked sources are documented. You see this before agreeing to a pilot.' },
  { n: '02', title: 'Scheduled source monitoring', desc: 'Configured sources are checked on a defined schedule. Each run produces a delta status: FIRST_SEEN, UNCHANGED, CHANGED, FAILED, or QUALITY_DROP.' },
  { n: '03', title: 'Change detection and quality check', desc: 'When a source returns CHANGED, extracted content is compared against the prior run. When extraction quality drops below threshold, the run is flagged for human review before any alert is issued.' },
  { n: '04', title: 'Profile relevance matching', desc: 'Detected changes are evaluated against your regulatory profile — your licence type, business activity, and monitored regulators. A VARA update does not go to a payments firm with no virtual asset exposure.' },
  { n: '05', title: 'Evidence-backed brief', desc: 'Your team receives a structured brief: what changed, the official source URL, timestamp, extraction quality, evidence snippet, known limitations, and a not-legal-advice disclaimer. Every brief is verifiable against the original source.' },
]
