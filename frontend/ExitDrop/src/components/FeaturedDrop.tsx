import { useEffect, useState } from 'react'
import { apiRequest } from '../api'
import type { FeaturedDropData, Product } from '../types'
import { ActionButton, ActionLink } from './Actions'

function formatCountdown(totalSeconds: number) {
  const days = Math.floor(totalSeconds / 86400)
  const hours = Math.floor((totalSeconds % 86400) / 3600)
  const minutes = Math.floor((totalSeconds % 3600) / 60)
  const seconds = totalSeconds % 60

  return [
    { value: days, label: 'days' },
    { value: hours, label: 'hrs' },
    { value: minutes, label: 'mins' },
    { value: seconds, label: 'secs' },
  ]
}

function DropProductImage({ product }: { product: Product }) {
  return product.image_url
    ? <img className="featured-product-image" src={product.image_url} alt={product.name} />
    : <div className="featured-product-placeholder" role="img" aria-label={`${product.name}: image unavailable`} />
}

export default function FeaturedDrop() {
  const [featured, setFeatured] = useState<FeaturedDropData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [retry, setRetry] = useState(0)
  const [activeIndex, setActiveIndex] = useState(0)
  const [secondsRemaining, setSecondsRemaining] = useState(0)
  const [notice, setNotice] = useState('')

  useEffect(() => {
    let cancelled = false
    apiRequest<FeaturedDropData | null>('/drops/featured')
      .then((data) => {
        if (!cancelled) {
          setFeatured(data)
          setActiveIndex(0)
          const endTime = data?.status === 'active' ? Date.parse(data.drop.ends_at) : Number.NaN
          setSecondsRemaining(Number.isNaN(endTime) ? 0 : Math.max(0, Math.floor((endTime - Date.now()) / 1000)))
        }
      })
      .catch((reason: unknown) => {
        if (!cancelled) setError(reason instanceof Error ? reason.message : 'Could not load the featured drop.')
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })

    return () => { cancelled = true }
  }, [retry])

  const products = featured?.products.filter((product) => product.drop_id === featured.drop.id) ?? []
  const currentProduct = products[activeIndex] ?? products[0]
  const isDropInProgress = featured?.status === 'active' && secondsRemaining > 0

  useEffect(() => {
    if (!isDropInProgress || products.length < 2) return
    const timer = window.setInterval(() => {
      setActiveIndex((index) => (index + 1) % products.length)
    }, 5000)
    return () => window.clearInterval(timer)
  }, [isDropInProgress, products.length])

  useEffect(() => {
    if (featured?.status !== 'active') return

    const endTime = Date.parse(featured.drop.ends_at)
    if (Number.isNaN(endTime)) return

    const updateCountdown = () => {
      setSecondsRemaining(Math.max(0, Math.floor((endTime - Date.now()) / 1000)))
    }
    const timer = window.setInterval(updateCountdown, 1000)
    return () => window.clearInterval(timer)
  }, [featured])

  useEffect(() => {
    if (!notice) return
    const timer = window.setTimeout(() => setNotice(''), 3500)
    return () => window.clearTimeout(timer)
  }, [notice])

  function notifyMe() {
    setNotice('¡Gracias! Te avisaremos cuando llegue un nuevo drop.')
  }

  const dateIsValid = !featured || !Number.isNaN(Date.parse(featured.drop.ends_at))
  const visibleError = error ?? (dateIsValid ? null : 'The featured drop has an invalid end time.')

  if (loading) {
    return <section className="featured-drop featured-drop-state" aria-busy="true"><p>Loading featured drop…</p></section>
  }

  if (visibleError) {
    return <section className="featured-drop featured-drop-state" aria-labelledby="featured-drop-title">
      <div><p className="eyebrow">Featured drop</p><h2 id="featured-drop-title">We couldn’t load the drop</h2><p className="api-error" role="alert">{visibleError}</p></div>
      <ActionButton variant="outline" onClick={() => {
        setLoading(true)
        setError(null)
        setRetry((value) => value + 1)
      }}>Try again</ActionButton>
    </section>
  }

  if (!featured) {
    return <section className="featured-drop featured-drop-state" aria-labelledby="featured-drop-title">
      <div><p className="eyebrow">Stay in the district</p><h2 id="featured-drop-title">No drops available right now</h2><p>Check back soon for the next release.</p></div>
      <div className="featured-buy">
        <ActionButton onClick={notifyMe}>Notify me</ActionButton>
        {notice && <p className="featured-notice" role="status">{notice}</p>}
      </div>
    </section>
  }

  const isActive = isDropInProgress

  return <section className="featured-drop" aria-labelledby="featured-drop-title">
    <div
      className="featured-shoe"
      role={products.length > 1 ? 'group' : undefined}
      aria-roledescription={products.length > 1 ? 'carousel' : undefined}
      aria-label={products.length > 1 ? 'Drop product previews' : undefined}
    >
      {currentProduct && <div className="featured-image-track">
        <div className="featured-image-slide" key={currentProduct.id}>
          <DropProductImage product={currentProduct} />
        </div>
      </div>}
    </div>

    <div className="featured-copy">
      <p className="eyebrow">{isActive ? 'Limited release' : 'Past drop'}</p>
      <h2 id="featured-drop-title">{featured.drop.name}</h2>
      {currentProduct && <h3 className="featured-product-name">{currentProduct.name}</h3>}
      <p>{currentProduct?.description || featured.drop.description || (isActive ? 'Explore this limited release.' : 'This release has ended.')}</p>
      {currentProduct && <p className="featured-stock">{isActive && currentProduct.stock > 0 ? `${currentProduct.stock} units available` : 'Sold out'}</p>}
      {!currentProduct && <p>{isActive ? 'No active products are assigned to this drop.' : 'All products in this drop are sold out.'}</p>}
      {isActive && <div className="countdown" aria-label="Time remaining">
        {formatCountdown(secondsRemaining).map(({ value, label }) => <span key={label}>{String(value).padStart(2, '0')}<small>{label}</small></span>)}
      </div>}
    </div>

    <div className="featured-buy">
      {currentProduct && <strong>${Number(currentProduct.price).toFixed(2)}</strong>}
      {isActive && currentProduct
        ? <ActionLink to={`/products/${currentProduct.id}`}>View drop</ActionLink>
        : <ActionButton onClick={notifyMe}>Notify me</ActionButton>}
      {isActive && currentProduct && <small>Limited release</small>}
      {notice && <p className="featured-notice" role="status">{notice}</p>}
    </div>
  </section>
}
