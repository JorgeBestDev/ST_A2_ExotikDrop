import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { apiRequest } from './api'
import { ActionButton, ActionLink } from './components/Actions'
import Breadcrumbs from './components/Breadcrumbs'
import FlowCard from './components/FlowCard'
import { useStore } from './store-context'
import type { CartItem, Product } from './types'

export default function ProductPage() {
  const { productId } = useParams()
  const { addToCart } = useStore()
  const navigate = useNavigate()
  const [product, setProduct] = useState<Product | null>(null)
  const [quantity, setQuantity] = useState(1)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!productId) return
    let cancelled = false
    apiRequest<Product>(`/products/${productId}`)
      .then((data) => {
        if (!cancelled) setProduct(data)
      })
      .catch((reason: unknown) => {
        if (!cancelled) setError(reason instanceof Error ? reason.message : 'Unable to load product.')
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })
    return () => { cancelled = true }
  }, [productId])

  if (loading) return <main className="flow-page"><p>Loading product…</p></main>
  if (!product) return <main className="flow-page">
    <FlowCard>
      <p className="form-error">{error ?? 'Product not found.'}</p>
      <ActionLink variant="dark" to="/">Return to the store</ActionLink>
    </FlowCard>
  </main>

  const cartItem: CartItem = {
    id: null,
    product_id: product.id,
    name: product.name,
    price: product.price,
    image_url: product.image_url,
    quantity,
    stock: product.stock,
    line_total: (Number(product.price) * quantity).toFixed(2),
  }

  async function add(buyNow = false) {
    try {
      await addToCart(cartItem, quantity)
      if (buyNow) navigate('/checkout')
      else setError('Added to your bag.')
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Could not add product to your bag.')
    }
  }

  return <main className="product-detail flow-page">
    <Breadcrumbs items={[
      { label: 'Home', to: '/' },
      { label: 'New drops', to: '/#new' },
      { label: product.name },
    ]} />
    <div className="product-detail-grid">
      <div
        className="detail-image"
        role="img"
        aria-label={product.name}
        style={{ backgroundImage: `url(${product.image_url ?? ''})` }}
      >
        <span className="detail-tag">Limited release</span>
      </div>
      <section className="product-info">
        <p className="eyebrow">{product.category ?? 'ExitDrop collection'}</p>
        <h1>{product.name}</h1>
        <strong className="detail-price">${Number(product.price).toFixed(2)}</strong>
        <div className="detail-rating">★★★★★ <span>4.9 · Limited drop</span></div>
        <p className="detail-description">{product.description || 'A limited piece selected by ExitDrop. Designed for everyday wear and made to stand out.'}</p>
        <p className={`stock-status ${product.stock > 0 ? '' : 'sold-out'}`}>
          {product.stock > 0 ? `${product.stock} available` : 'Sold out'}
        </p>
        {product.stock > 0 && <div className="detail-purchase">
          <div className="quantity-select" role="group" aria-label="Quantity controls">
            <span>Quantity</span>
            <button type="button" aria-label="Decrease quantity" disabled={quantity <= 1} onClick={() => setQuantity((value) => Math.max(1, value - 1))}>−</button>
            <span aria-live="polite">{quantity}</span>
            <button type="button" aria-label="Increase quantity" disabled={quantity >= product.stock} onClick={() => setQuantity((value) => Math.min(product.stock, value + 1))}>+</button>
          </div>
          <ActionButton variant="outline" onClick={() => void add()}>Add to bag</ActionButton>
          <ActionButton onClick={() => void add(true)}>Buy now <span>→</span></ActionButton>
        </div>}
        {error && <p className={error.startsWith('Added') ? 'form-success' : 'form-error'} role={error.startsWith('Added') ? 'status' : 'alert'}>{error}</p>}
        <div className="detail-perks">
          <p>✓ Secure checkout</p>
          <p>✓ Easy 30-day returns</p>
          <p>✓ Carefully packed by ExitDrop</p>
        </div>
        <details className="detail-accordion">
          <summary>Product details</summary>
          <p>{product.description || 'Curated streetwear and limited releases from ExitDrop.'}</p>
          <p>Category: {product.category ?? 'Collection'} · SKU: ED-{product.id.toString().padStart(5, '0')}</p>
        </details>
        <details className="detail-accordion">
          <summary>Shipping &amp; returns</summary>
          <p>Shipping is calculated at checkout. Eligible items can be returned within 30 days of delivery.</p>
        </details>
      </section>
    </div>
  </main>
}
