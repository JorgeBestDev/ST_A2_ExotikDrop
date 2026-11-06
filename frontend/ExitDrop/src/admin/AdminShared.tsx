import type { ReactNode } from 'react'

export function AdminPageHeading({
  eyebrow,
  title,
  description,
  action,
}: {
  eyebrow: string
  title: string
  description: string
  action?: ReactNode
}) {
  return <div className="admin-page-heading">
    <div>
      <p className="admin-eyebrow">{eyebrow}</p>
      <h1>{title}</h1>
      <p className="admin-muted">{description}</p>
    </div>
    {action}
  </div>
}

export function AdminFeedback({ error, notice }: { error?: string | null; notice?: string | null }) {
  return <>
    {error && <p className="admin-error" role="alert">{error}</p>}
    {notice && <p className="admin-notice" role="status">{notice}</p>}
  </>
}
