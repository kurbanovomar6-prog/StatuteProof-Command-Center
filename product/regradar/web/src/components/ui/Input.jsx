import { clsx } from 'clsx'

export function Input({ className, ...props }) {
  return (
    <input
      className={clsx(
        'w-full rounded-lg border border-slate-300 bg-white px-3 py-2.5 text-sm text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition',
        className,
      )}
      {...props}
    />
  )
}
