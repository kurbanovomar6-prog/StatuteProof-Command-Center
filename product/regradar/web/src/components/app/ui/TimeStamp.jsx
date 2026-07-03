import { formatGst, timeAgo, fullStamp } from '../../../utils/time'

/**
 * Consistent timestamp element: relative text with the absolute GST time on
 * hover ("14 min ago · 04 Jul 2026, 15:22 GST"), or absolute-first with
 * `mode="absolute"` for evidence-grade rows.
 */
export default function TimeStamp({ value, mode = 'relative', fallback = 'Not recorded', className = '' }) {
  const abs = formatGst(value)
  if (!abs) return <span className={className}>{fallback}</span>
  const rel = timeAgo(value)
  const text = mode === 'absolute' ? abs : rel
  return (
    <time dateTime={value} title={fullStamp(value)} className={className}>
      {text}
    </time>
  )
}
