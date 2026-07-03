// Timestamp formatting — one format everywhere.
// Absolute times are shown in Gulf Standard Time (Asia/Dubai, UTC+4, no DST),
// the timezone of the UAE regulators being monitored.

const GST_TZ = 'Asia/Dubai'

export function parseTimestamp(value) {
  if (!value) return null
  const d = new Date(value)
  return Number.isNaN(d.getTime()) ? null : d
}

/** "04 Jul 2026, 15:22 GST" */
export function formatGst(value) {
  const d = parseTimestamp(value)
  if (!d) return null
  const date = d.toLocaleDateString('en-GB', {
    timeZone: GST_TZ, day: '2-digit', month: 'short', year: 'numeric',
  })
  const time = d.toLocaleTimeString('en-GB', {
    timeZone: GST_TZ, hour: '2-digit', minute: '2-digit',
  })
  return `${date}, ${time} GST`
}

/** "14 min ago" / "3 hours ago" / "12 days ago" — falls back to absolute for old dates */
export function timeAgo(value, now = new Date()) {
  const d = parseTimestamp(value)
  if (!d) return null
  const diffMs = now - d
  if (diffMs < 0) return formatGst(value)
  const min = Math.floor(diffMs / 60000)
  if (min < 1) return 'just now'
  if (min < 60) return `${min} min ago`
  const hours = Math.floor(min / 60)
  if (hours < 24) return hours === 1 ? '1 hour ago' : `${hours} hours ago`
  const days = Math.floor(hours / 24)
  if (days < 60) return days === 1 ? '1 day ago' : `${days} days ago`
  return formatGst(value)
}

/** "14 min ago · 04 Jul 2026, 15:22 GST" — for tooltips */
export function fullStamp(value) {
  const rel = timeAgo(value)
  const abs = formatGst(value)
  if (!rel || !abs) return null
  return rel === abs ? abs : `${rel} · ${abs}`
}

/** Hours elapsed since the timestamp, or null. Used for freshness checks. */
export function hoursSince(value, now = new Date()) {
  const d = parseTimestamp(value)
  if (!d) return null
  return (now - d) / 3600000
}
