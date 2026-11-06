import { Link } from 'react-router-dom'

export type BreadcrumbItem = {
  label: string
  to?: string
}

export default function Breadcrumbs({ items }: { items: BreadcrumbItem[] }) {
  return <nav className="breadcrumbs" aria-label="Breadcrumb">
    {items.map((item, index) => <span className="breadcrumb-item" key={`${item.label}-${index}`}>
      {index > 0 && <span aria-hidden="true">/</span>}
      {item.to
        ? <Link to={item.to}>{item.label}</Link>
        : <span aria-current="page">{item.label}</span>}
    </span>)}
  </nav>
}
