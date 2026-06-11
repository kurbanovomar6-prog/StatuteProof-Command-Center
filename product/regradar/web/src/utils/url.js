export function normalizeExternalUrl(url) {
  if (!url) return ''
  const trimmed = String(url).trim()
  if (!trimmed) return ''
  if (trimmed.startsWith('http://') || trimmed.startsWith('https://')) return trimmed
  if (trimmed.includes(':')) return ''
  return `https://${trimmed}`
}
