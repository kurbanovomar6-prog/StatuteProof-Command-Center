export const sourceHealthRows = [
  { id: 1,  name: 'CBUAE Main',                  jurisdiction: 'AE', flag: '🇦🇪', access: 'Accessible', quality: 'readiness_supported', status: 'readiness_supported', verdict: 'READINESS' },
  { id: 2,  name: 'CBUAE Regulations',           jurisdiction: 'AE', flag: '🇦🇪', access: 'Accessible', quality: 'readiness_supported', status: 'readiness_supported', verdict: 'READINESS' },
  { id: 3,  name: 'UAE Ministry of Finance',     jurisdiction: 'AE', flag: '🇦🇪', access: 'Accessible', quality: 'readiness_supported', status: 'readiness_supported', verdict: 'READINESS' },
  { id: 4,  name: 'VARA Main',                   jurisdiction: 'AE', flag: '🇦🇪', access: 'Accessible', quality: 'readiness_supported', status: 'readiness_supported', verdict: 'READINESS' },
  { id: 5,  name: 'VARA Enforcement Notices',    jurisdiction: 'AE', flag: '🇦🇪', access: 'Accessible', quality: 'readiness_supported', status: 'readiness_supported', verdict: 'READINESS' },
  { id: 6,  name: 'ADGM FSRA Main',              jurisdiction: 'AE', flag: '🇦🇪', access: 'Accessible', quality: 'readiness_supported', status: 'readiness_supported', verdict: 'READINESS' },
  { id: 7,  name: 'UAE FIU Circulars',           jurisdiction: 'AE', flag: '🇦🇪', access: 'Accessible', quality: 'readiness_supported', status: 'readiness_supported', verdict: 'READINESS' },
  { id: 8,  name: 'DIFC Laws and Regulations',   jurisdiction: 'AE', flag: '🇦🇪', access: 'Limited',    quality: 'remediation', status: 'remediation', verdict: 'REVIEW' },
  { id: 9,  name: 'UAE Legislation Portal',      jurisdiction: 'AE', flag: '🇦🇪', access: 'Accessible', quality: 'readiness_supported', status: 'readiness_supported', verdict: 'READINESS' },
  { id: 10, name: 'UAE Ministry of Economy',     jurisdiction: 'AE', flag: '🇦🇪', access: 'Accessible', quality: 'readiness_supported', status: 'readiness_supported', verdict: 'READINESS' },
  { id: 11, name: 'DFSA Rulebook',               jurisdiction: 'AE', flag: '🇦🇪', access: 'Limited',    quality: 'remediation', status: 'remediation', verdict: 'REVIEW' },
  { id: 12, name: 'DFSA Regulatory Notices',     jurisdiction: 'AE', flag: '🇦🇪', access: 'Limited',    quality: 'remediation', status: 'remediation', verdict: 'REVIEW' },
  { id: 13, name: 'UAE FIU Homepage',            jurisdiction: 'AE', flag: '🇦🇪', access: 'Limited',    quality: 'remediation', status: 'remediation', verdict: 'REVIEW' },
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
  { icon: 'FileText',      title: 'Source-backed compliance briefs', desc: 'Every detected change produces a structured brief: what changed, which official source produced it, and what your profile requires next.' },
  { icon: 'Globe',         title: 'Documented extraction methods',    desc: 'HTML structured content, PDF text, or page snapshots are recorded per source so limitations are visible.' },
  { icon: 'MessageSquare', title: 'Profile-scoped alert delivery',    desc: 'Alerts are scoped to the regulators and business activities that apply to your licence type and risk exposure.' },
  { icon: 'BarChart2',     title: 'Source readiness reporting',       desc: 'Source checks show readiness-supported, limited, and blocked sources before a pilot begins, with access restrictions documented.' },
  { icon: 'BrainCircuit',  title: 'Client-specific source profiles',  desc: 'Configure the exact regulators, jurisdictions, and compliance topics relevant to your business. No irrelevant sources.' },
  { icon: 'Languages',     title: 'English compliance briefs',        desc: 'Official source content is converted into concise English briefs while preserving proof back to the original source.' },
  { icon: 'ShieldCheck',   title: 'Evidence trail on every alert',    desc: 'Every alert includes source URL, timestamp, delta status, extraction quality, evidence snippet, and known limitations.' },
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
      { name: 'DIFC Laws and Regulations', status: 'remediation' },
      { name: 'UAE Legislation Portal', status: 'readiness_supported' },
      { name: 'UAE Ministry of Economy', status: 'readiness_supported' },
      { name: 'DFSA Rulebook', status: 'remediation' },
      { name: 'DFSA Regulatory Notices', status: 'remediation' },
      { name: 'UAE FIU Homepage', status: 'remediation' },
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
    desc: 'A no-cost review of which UAE regulatory sources are technically accessible, extractable, limited, or blocked for your compliance profile.',
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
    desc: 'First paid plan for early users. Up to 3 official UAE sources, evidence records, basic diff view, and weekly source status summary. Manually activated.',
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
    desc: 'MLRO or CCO workspace for the UAE pack. 66 enabled official-source endpoints: 62 readiness-supported after proof and baseline gates, 4 under extraction remediation.',
    features: [
      '62 readiness-supported UAE sources',
      'High-risk review queue',
      'Weekly MLRO brief requires activation',
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
    desc: 'For advisory firms managing multiple UAE-regulated clients. Custom scope, custom retention, and consultant workflows are reviewed manually.',
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
