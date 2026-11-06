import type { ReactNode } from 'react'

export default function FlowCard({ children, className = '' }: { children: ReactNode; className?: string }) {
  return <section className={`flow-card${className ? ` ${className}` : ''}`}>{children}</section>
}
