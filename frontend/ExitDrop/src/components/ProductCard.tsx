import { Link } from 'react-router-dom'
import type { Product } from '../types'

export default function ProductCard({ product }: { product: Product }) {
  return <article className="product-card">
    <Link to={`/products/${product.id}`} aria-label={`View ${product.name}`}>
      <div
        className="product-photo"
        role="img"
        aria-label={product.name}
        style={{ backgroundImage: `url(${product.image_url ?? ''})` }}
      >
        <span className="heart" aria-hidden="true">♡</span>
      </div>
      <h3>{product.name}</h3>
      <strong>${Number(product.price).toFixed(2)}</strong>
    </Link>
  </article>
}
