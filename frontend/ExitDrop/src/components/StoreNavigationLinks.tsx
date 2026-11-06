import { Link } from 'react-router-dom'

const headerLinks = [
  { label: 'New Arrivals', to: '/#new' },
  { label: 'Sneakers', to: '/#sneakers' },
  { label: 'Apparel', to: '/#apparel' },
  { label: 'Accessories', to: '/#accessories' },
  { label: 'Our Story', to: '/#story' },
  { label: 'Sale', to: '/#new' },
]

const shopLinks = headerLinks.slice(0, 4)

export function StoreHeaderLinks() {
  return <>{headerLinks.map(({ label, to }) => <Link key={label} to={to}>{label}</Link>)}</>
}

export function StoreShopLinks() {
  return <>{shopLinks.map(({ label, to }) => <Link key={label} to={to}>{label}</Link>)}</>
}
