import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { apiRequest } from './api'
import type { Category, Product } from './types'

const Arrow = () => <span className="arrow">→</span>
const Heart = () => <span className="heart" aria-label="Add to wishlist">♡</span>

export default function HomePage() {
  const [products, setProducts] = useState<Product[]>([])
  const [categories, setCategories] = useState<Category[]>([])
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    Promise.all([apiRequest<Product[]>('/products'), apiRequest<Category[]>('/categories')])
      .then(([productData, categoryData]) => {
        setProducts(productData)
        setCategories(categoryData)
      })
      .catch((reason: unknown) => setError(reason instanceof Error ? reason.message : 'Could not load the latest drops.'))
  }, [])

  return <main id="top">
    <section className="hero">
      <div className="hero-content"><p className="eyebrow">Exit. Style. District.</p><h1>BUILT ON<br />CULTURE.<br /><strong>WORN BY YOU.</strong></h1><p className="hero-subtitle">Curated sneakers and streetwear<br />for those who set the pace.</p><div className="hero-buttons"><Link className="button button-brown" to="/#new">Shop New Arrivals</Link><Link className="button button-outline" to="/#apparel">Shop Apparel</Link></div></div>
      <div className="hero-image" />
    </section>

    <section className="category-section section-light" id="sneakers">
      <div className="category-intro"><p className="eyebrow">Shop by category</p><h2>EXPLORE OUR<br />WORLD</h2><Link className="button button-dark" to="/#apparel">View all categories</Link></div>
      <div className="category-grid">{categories.map((category) => <Link className="category-card" to="/#new" key={category.id}><div className="category-image" style={{ backgroundImage: `url(${category.image_url ?? ''})` }} /><h3>{category.name}</h3><span>Shop now <Arrow /></span></Link>)}</div>
    </section>

    <section className="drops section-dark" id="new">
      <div className="section-heading"><div><p className="eyebrow">New drops</p><h2>JUST LANDED</h2><p>The latest heat. Fresh styles.<br />Limited quantities.</p>{error && <small className="api-error">{error}</small>}</div><Link className="button button-brown" to="/#new">Shop all new drops</Link></div>
      <div className="product-grid">{products.slice(0, 5).map((product) => <article className="product-card" key={product.id}><Link to={`/products/${product.id}`} aria-label={`View ${product.name}`}><div className="product-photo" style={{ backgroundImage: `url(${product.image_url ?? ''})` }}><Heart /></div><h3>{product.name}</h3><strong>${Number(product.price).toFixed(2)}</strong></Link></article>)}</div>
      <div className="slider-dots"><i /><i className="active" /><i /><i /></div>
    </section>

    <section className="story" id="story">
      <div className="story-photo" /><div className="story-copy"><p className="eyebrow">Our story</p><h2>MORE THAN A BRAND.<br />IT&apos;S A MOVEMENT.</h2><p>ExitDrop was built for the culture. Inspired by the streets, driven by community. We curate what&apos;s real and authentic—so you can wear your story.</p><Link className="button button-outline" to="/#community">Learn more about us</Link></div><div className="story-values"><div>♢ <span>Curated<br />quality</span></div><div>♧ <span>Limited<br />releases</span></div><div>◉ <span>Culture<br />first</span></div><div>♙ <span>Community<br />driven</span></div></div>
    </section>

    <section className="featured-drop">
      <div className="featured-shoe" /><div className="featured-copy"><p className="eyebrow">Limited release</p><h2>AIR JORDAN 1 HIGH OG “MOCHA”</h2><p>Iconic colorway. Timeless energy.<br />Strictly limited.</p><div className="countdown"><span>02<small>days</small></span><span>14<small>hrs</small></span><span>37<small>mins</small></span><span>48<small>secs</small></span></div></div><div className="featured-buy"><strong>$180.00</strong><Link className="button button-brown" to={products[0] ? `/products/${products[0].id}` : '/#new'}>View drop</Link><small>Limited to 1 per customer</small></div>
    </section>

    <section className="community section-light" id="community">
      <div className="community-intro"><p className="eyebrow">Real people. Real style.</p><h2>WHAT OUR COMMUNITY<br />SAYS</h2><Link className="button button-dark" to="/#community">View all reviews</Link><div className="rating">★★★★★ <small>4.9 / 5 from 3,200+ reviews</small></div></div>
      <div className="reviews"><blockquote>“<p>ExitDrop always comes through with the heat and the service. My go-to for exclusive drops!</p><footer>— Marcus T.</footer><b>★★★★★</b></blockquote><blockquote>“<p>The quality is unmatched and the pieces hit different in person. 10/10 recommend.</p><footer>— Jasmine R.</footer><b>★★★★★</b></blockquote><blockquote>“<p>Fast shipping, dope packaging, and legit products. You&apos;ve got a customer for life.</p><footer>— Daniel K.</footer><b>★★★★★</b></blockquote></div>
    </section>

    <section className="guides section-dark" id="apparel"><div className="section-heading"><div><p className="eyebrow">Style guide</p><h2>INSPO FROM THE DISTRICT</h2><p>Outfit ideas, culture stories, and style tips<br />to keep you ahead of the game.</p></div><Link className="button button-brown" to="/#apparel">View all articles</Link></div><div className="article-grid"><article><div className="article-image article-one" /><small>MAY 12, 2026</small><h3>5 WAYS TO STYLE CARGO<br />PANTS THIS SEASON</h3><span>Read more →</span></article><article><div className="article-image article-two" /><small>MAY 5, 2026</small><h3>WHY NEUTRALS ARE ALWAYS<br />A GOOD IDEA</h3><span>Read more →</span></article><article><div className="article-image article-three" /><small>APR 18, 2026</small><h3>THE RISE OF STREETWEAR:<br />THEN &amp; NOW</h3><span>Read more →</span></article></div></section>

    <section className="newsletter section-light"><div><h2>STAY IN THE DISTRICT</h2><p>Be the first to know about new drops, exclusive offers,<br />and culture content.</p></div><form className="email-box" onSubmit={(event) => event.preventDefault()}><input type="email" placeholder="Enter your email address" aria-label="Email address" /><button>SIGN UP</button><div><span>◯ Exclusive access</span><span>◯ Early drops</span><span>◯ Special offers</span></div></form><div className="newsletter-mark">ED</div></section>
  </main>
}
