// Client-side iCalendar (RFC 5545) builder for the detected key-date calendar.
//
// LEGAL FRAMING (load-bearing): a "detected date" is a date StatuteProof found
// in the CHANGED text of a monitored source and sealed into an evidence record.
// It is a monitoring signal to help a human decide what to review — NOT the
// reader's legal deadline, NOT advice, NOT a guarantee. Every VEVENT SUMMARY and
// DESCRIPTION is worded accordingly ("Detected …", "verify against the official
// source"), never "deadline: you must". The short disclaimer rides in every
// DESCRIPTION. The builder never invents an event: it maps exactly the dates it
// is given.

const SHORT_DISCLAIMER =
  'For monitoring information only. Not legal advice and not a guarantee of compliance.'

// RFC 5545 §3.3.11 TEXT escaping: backslash, semicolon, comma, and newlines.
function escapeText(value) {
  return String(value == null ? '' : value)
    .replace(/\\/g, '\\\\')
    .replace(/;/g, '\\;')
    .replace(/,/g, '\\,')
    .replace(/\r\n|\r|\n/g, '\\n')
}

// RFC 5545 §3.1 content-line folding: lines longer than 75 octets are folded
// with CRLF + a single leading space. We fold on character count (ASCII-safe for
// our authored text) which keeps common calendar clients happy.
function foldLine(line) {
  if (line.length <= 75) return line
  const parts = []
  let rest = line
  parts.push(rest.slice(0, 75))
  rest = rest.slice(75)
  while (rest.length > 74) {
    parts.push(' ' + rest.slice(0, 74))
    rest = rest.slice(74)
  }
  if (rest.length) parts.push(' ' + rest)
  return parts.join('\r\n')
}

// "2026-09-01" -> "20260901" (DATE value, all-day event).
function toIcsDate(iso) {
  return String(iso || '').slice(0, 10).replace(/-/g, '')
}

// "2026-07-01T09:00:00Z" or now -> "20260701T090000Z" (UTC DATE-TIME).
function toIcsStamp(value) {
  const d = value ? new Date(value) : new Date()
  const safe = Number.isNaN(d.getTime()) ? new Date() : d
  return safe.toISOString().replace(/[-:]/g, '').replace(/\.\d{3}Z$/, 'Z')
}

function typeLabel(item) {
  return item.type_label || 'date'
}

// Honest, obligation-free VEVENT summary — this title travels OUTSIDE the product
// into a third-party calendar, so the "StatuteProof-detected" prefix makes the
// monitoring/detection nature unmissable even read standalone (never "Deadline:
// file by X"). Never "you must".
export function eventSummary(item) {
  const source = item.source_name || item.source_id || 'monitored source'
  return `StatuteProof-detected ${typeLabel(item)} (verify) — ${source}`
}

// Honest VEVENT description: framing + the detected excerpt + the sealed
// verification pointer + the disclaimer. Never asserts the reader's obligation.
export function eventDescription(item) {
  const lines = []
  lines.push(
    item.framing ||
      `A ${typeLabel(item)} StatuteProof detected in the changed text of a ` +
        'monitored source. A monitoring signal to help you decide what to review — ' +
        'not a legal deadline and not advice. Verify against the official source.',
  )
  if (item.raw_date_text) lines.push(`Source text: "${item.raw_date_text}"`)
  if (item.date_ambiguous) {
    lines.push('Date format is ambiguous (day/month vs month/day); verify against the source.')
  }
  if (item.excerpt) lines.push(`Detected in changed text: ${item.excerpt}`)
  if (item.evidence_record_id) lines.push(`Evidence record: ${item.evidence_record_id}`)
  if (item.record_hash) lines.push(`Record hash: ${item.record_hash}`)
  if (item.official_url) lines.push(`Official source: ${item.official_url}`)
  lines.push(item.disclaimer || SHORT_DISCLAIMER)
  return lines.join('\n\n')
}

// Stable UID so re-importing the same calendar does not duplicate events.
function eventUid(item) {
  const seed = [item.record_hash || item.evidence_record_id || 'unknown', item.date, item.detected_type]
    .join('-')
    .replace(/[^A-Za-z0-9:_-]/g, '')
  return `${seed}@statuteproof`
}

/**
 * Build a standards-valid iCalendar string from detected key dates.
 * @param {Array<object>} dates - items from /api/calendar/effective-dates
 * @returns {string} an .ics document (CRLF line endings)
 */
export function buildEffectiveDatesIcs(dates) {
  const stamp = toIcsStamp()
  const lines = [
    'BEGIN:VCALENDAR',
    'VERSION:2.0',
    'PRODID:-//StatuteProof//Effective-Date Calendar//EN',
    'CALSCALE:GREGORIAN',
    'METHOD:PUBLISH',
    'X-WR-CALNAME:StatuteProof detected key dates',
    `X-WR-CALDESC:${escapeText(SHORT_DISCLAIMER)}`,
  ]

  for (const item of Array.isArray(dates) ? dates : []) {
    const start = toIcsDate(item.date)
    if (!start) continue
    lines.push('BEGIN:VEVENT')
    lines.push(`UID:${escapeText(eventUid(item))}`)
    lines.push(`DTSTAMP:${stamp}`)
    lines.push(`DTSTART;VALUE=DATE:${start}`)
    lines.push(`SUMMARY:${escapeText(eventSummary(item))}`)
    lines.push(`DESCRIPTION:${escapeText(eventDescription(item))}`)
    lines.push('TRANSP:TRANSPARENT')
    lines.push('END:VEVENT')
  }

  lines.push('END:VCALENDAR')
  return lines.map(foldLine).join('\r\n') + '\r\n'
}

export { SHORT_DISCLAIMER }
