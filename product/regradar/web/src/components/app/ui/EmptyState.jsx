/** Standard empty state: icon + one-sentence explanation of what will appear here. */
export default function EmptyState({ icon: Icon, title, children, className = '' }) {
  return (
    <div className={`px-5 py-10 text-center ${className}`}>
      {Icon && <Icon className="mx-auto mb-3 h-5 w-5 text-slate-500" aria-hidden="true" />}
      <p className="text-sm font-medium text-slate-300">{title}</p>
      {children && <p className="mx-auto mt-2 max-w-md text-xs leading-relaxed text-slate-500">{children}</p>}
    </div>
  )
}
