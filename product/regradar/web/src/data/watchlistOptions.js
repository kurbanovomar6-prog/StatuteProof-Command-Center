// StatuteProof — Client Watchlist Builder static data

export const COMPANY_TYPES = [
  { id: 'vasp',       label: 'Crypto / VASP firm' },
  { id: 'fintech',    label: 'Fintech / payment provider' },
  { id: 'legal',      label: 'Legal advisory firm' },
  { id: 'compliance', label: 'Compliance consultant' },
  { id: 'bank',       label: 'Bank / financial institution' },
  { id: 'crossborder',label: 'Cross-border business team' },
]

export const MARKETS = [
  { id: 'AE', flag: '🇦🇪', label: 'UAE',          note: null },
  { id: 'DIFC', flag: '🇦🇪', label: 'DIFC',        note: 'Free-zone source pack' },
  { id: 'ADGM', flag: '🇦🇪', label: 'ADGM',        note: 'Free-zone source pack' },
  { id: 'UAE-OTHER', flag: '🇦🇪', label: 'Other UAE source', note: 'Requires validation' },
]

export const TOPICS = [
  { id: 'aml',          label: 'AML / CFT' },
  { id: 'payments',     label: 'Payments and licensing' },
  { id: 'crypto',       label: 'Crypto / VASP' },
  { id: 'capital',      label: 'Capital markets' },
  { id: 'tax',          label: 'Tax and reporting' },
  { id: 'data',         label: 'Data protection' },
  { id: 'legislation',  label: 'Official legislation' },
  { id: 'consultations',label: 'Regulatory consultations' },
]

export const DELIVERY = [
  { id: 'telegram', label: 'Telegram' },
  { id: 'email',    label: 'Email' },
  { id: 'weekly',   label: 'Weekly digest' },
  { id: 'monthly',  label: 'Monthly coverage report' },
]

// Recommendation map: companyType id → { topics: [], markets: [] }
export const RECOMMENDATIONS = {
  vasp: {
    topics:  ['crypto', 'aml', 'legislation'],
    markets: ['AE', 'DIFC', 'ADGM'],
  },
  fintech: {
    topics:  ['payments', 'aml', 'tax'],
    markets: ['AE', 'DIFC', 'ADGM'],
  },
  legal: {
    topics:  ['legislation', 'capital', 'tax', 'aml'],
    markets: ['AE', 'DIFC', 'ADGM'],
  },
  compliance: {
    topics:  ['aml', 'payments', 'legislation', 'consultations'],
    markets: ['AE', 'DIFC', 'ADGM'],
  },
  bank: {
    topics:  ['aml', 'capital', 'payments', 'data'],
    markets: ['AE', 'DIFC', 'ADGM'],
  },
  crossborder: {
    topics:  ['tax', 'payments', 'legislation', 'aml'],
    markets: ['AE', 'DIFC', 'ADGM'],
  },
}
