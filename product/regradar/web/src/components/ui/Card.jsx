import { clsx } from 'clsx'

export function Card({ children, className, ...props }) {
  return (
    <div
      className={clsx('bg-white rounded-xl border border-slate-200 shadow-sm', className)}
      {...props}
    >
      {children}
    </div>
  )
}

export function CardHeader({ children, className }) {
  return <div className={clsx('px-6 pt-6 pb-4', className)}>{children}</div>
}

export function CardBody({ children, className }) {
  return <div className={clsx('px-6 pb-6', className)}>{children}</div>
}
