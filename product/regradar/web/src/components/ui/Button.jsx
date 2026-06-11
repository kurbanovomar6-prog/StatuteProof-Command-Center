import { clsx } from 'clsx'

const variants = {
  primary:  'bg-blue-600 hover:bg-blue-700 text-white shadow-sm',
  outline:  'border border-slate-300 hover:border-blue-500 hover:text-blue-600 text-slate-700 bg-white',
  ghost:    'hover:bg-slate-100 text-slate-600',
  danger:   'bg-red-600 hover:bg-red-700 text-white',
}

const sizes = {
  sm:  'px-3 py-1.5 text-sm',
  md:  'px-5 py-2.5 text-sm font-medium',
  lg:  'px-7 py-3 text-base font-semibold',
}

export function Button({ children, variant = 'primary', size = 'md', className, ...props }) {
  return (
    <button
      className={clsx(
        'inline-flex items-center justify-center gap-2 rounded-lg transition-colors duration-150 cursor-pointer focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 disabled:opacity-50',
        variants[variant],
        sizes[size],
        className,
      )}
      {...props}
    >
      {children}
    </button>
  )
}
