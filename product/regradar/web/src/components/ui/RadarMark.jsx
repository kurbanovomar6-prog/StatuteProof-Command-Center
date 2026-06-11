export default function RadarMark({ className = '' }) {
  return (
    <svg viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg" className={className}>
      <defs>
        <linearGradient id="rr-sig" x1="17" y1="15" x2="23" y2="9" gradientUnits="userSpaceOnUse">
          <stop offset="0" stopColor="#1E50C8"/>
          <stop offset="1" stopColor="#00C4FF"/>
        </linearGradient>
      </defs>

      {/* Three monitoring rings — precision instrument hierarchy */}
      <circle cx="16" cy="16" r="10"   stroke="#1E3350" strokeWidth="0.75"/>
      <circle cx="16" cy="16" r="6.5"  stroke="#2B4060" strokeWidth="0.7"/>
      <circle cx="16" cy="16" r="3.25" stroke="#C4D4E8" strokeOpacity="0.34" strokeWidth="0.9"/>

      {/* Cardinal precision ticks — N S E W */}
      <line x1="16" y1="6"    x2="16" y2="7.5"  stroke="#3D5878" strokeWidth="0.7" strokeLinecap="round" opacity="0.55"/>
      <line x1="16" y1="26"   x2="16" y2="24.5" stroke="#3D5878" strokeWidth="0.7" strokeLinecap="round" opacity="0.55"/>
      <line x1="26" y1="16"   x2="24.5" y2="16" stroke="#3D5878" strokeWidth="0.7" strokeLinecap="round" opacity="0.55"/>
      <line x1="6"  y1="16"   x2="7.5"  y2="16" stroke="#3D5878" strokeWidth="0.7" strokeLinecap="round" opacity="0.55"/>

      {/* Detection vector — thin, gradient */}
      <line x1="16.9" y1="15.1" x2="22.7" y2="9.3" stroke="url(#rr-sig)" strokeWidth="1.2" strokeLinecap="round"/>

      {/* Center intelligence dot */}
      <circle cx="16" cy="16" r="1.1" fill="#00C4FF"/>

      {/* Active detected signal — on monitoring perimeter, small and precise */}
      <circle cx="23.05" cy="8.95" r="1.85" stroke="#00C4FF" strokeWidth="0.8" opacity="0.18"/>
      <circle cx="23.05" cy="8.95" r="1.05" fill="#00C4FF"/>
    </svg>
  )
}
