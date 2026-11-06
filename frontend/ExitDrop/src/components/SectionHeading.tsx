import type { ReactNode } from 'react'

type SectionHeadingProps = {
  eyebrow: string
  title: string
  description?: ReactNode
  action?: ReactNode
}

export default function SectionHeading({ eyebrow, title, description, action }: SectionHeadingProps) {
  return <div className="section-heading">
    <div>
      <p className="eyebrow">{eyebrow}</p>
      <h2>{title}</h2>
      {description && <p>{description}</p>}
    </div>
    {action}
  </div>
}
