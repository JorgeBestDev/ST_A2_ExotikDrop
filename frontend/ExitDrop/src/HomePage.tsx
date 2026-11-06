import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { apiRequest } from './api'
import { ActionLink } from './components/Actions'
import FeaturedDrop from './components/FeaturedDrop'
import ProductCard from './components/ProductCard'
import SectionHeading from './components/SectionHeading'
import type { Category, Product } from './types'

const reviews = [
  {
    quote: 'ExitDrop always comes through with the heat and the service. My go-to for exclusive drops!',
    author: 'Marcus T.',
  },
  {
    quote: 'The quality is unmatched and the pieces hit different in person. 10/10 recommend.',
    author: 'Jasmine R.',
  },
  {
    quote: 'Fast shipping, dope packaging, and legit products. You’ve got a customer for life.',
    author: 'Daniel K.',
  },
]

const articles = [
  { date: 'MAY 12, 2026', title: '5 WAYS TO STYLE CARGO PANTS THIS SEASON', imageClass: 'article-one' },
  { date: 'MAY 5, 2026', title: 'WHY NEUTRALS ARE ALWAYS A GOOD IDEA', imageClass: 'article-two' },
  { date: 'APR 18, 2026', title: 'THE RISE OF STREETWEAR: THEN & NOW', imageClass: 'article-three' },
]

function CategoryCard({ category }: { category: Category }) {
  return <Link className="category-card" to="/#new">
    <div className="category-image" style={{ backgroundImage: `url(${category.image_url ?? ''})` }} />
    <h3>{category.name}</h3>
    <span>Shop now <span className="arrow" aria-hidden="true">→</span></span>
  </Link>
}

function ReviewCard({ quote, author }: { quote: string; author: string }) {
  return <blockquote>
    <p>“{quote}”</p>
    <footer>— {author}</footer>
    <b aria-label="5 out of 5 stars">★★★★★</b>
  </blockquote>
}

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
      <div className="hero-content">
        <p className="eyebrow">Exit. Style. District.</p>
        <h1>BUILT ON<br />CULTURE.<br /><strong>WORN BY YOU.</strong></h1>
        <p className="hero-subtitle">Curated sneakers and streetwear<br />for those who set the pace.</p>
        <div className="hero-buttons">
          <ActionLink to="/#new">Shop New Arrivals</ActionLink>
          <ActionLink variant="outline" to="/#apparel">Shop Apparel</ActionLink>
        </div>
      </div>
      <div className="hero-image" />
    </section>

    <FeaturedDrop />

    <section className="category-section section-light" id="sneakers">
      <div className="category-intro">
        <p className="eyebrow">Shop by category</p>
        <h2>EXPLORE OUR<br />WORLD</h2>
        <ActionLink variant="dark" to="/#apparel">View all categories</ActionLink>
      </div>
      <div className="category-grid">{categories.map((category) => <CategoryCard key={category.id} category={category} />)}</div>
    </section>

    <section className="drops section-dark" id="new">
      <SectionHeading
        eyebrow="New drops"
        title="JUST LANDED"
        description={<>The latest heat. Fresh styles.<br />Limited quantities.</>}
        action={<ActionLink to="/#new">Shop all new drops</ActionLink>}
      />
      {error && <small className="api-error" role="alert">{error}</small>}
      <div className="product-grid">{products.slice(0, 5).map((product) => <ProductCard key={product.id} product={product} />)}</div>
      <div className="slider-dots" aria-hidden="true"><i /><i className="active" /><i /><i /></div>
    </section>

    <section className="story" id="story">
      <div className="story-photo" />
      <div className="story-copy">
        <p className="eyebrow">Our story</p>
        <h2>MORE THAN A BRAND.<br />IT&apos;S A MOVEMENT.</h2>
        <p>ExitDrop was built for the culture. Inspired by the streets, driven by community. We curate what&apos;s real and authentic—so you can wear your story.</p>
        <ActionLink variant="outline" to="/#community">Learn more about us</ActionLink>
      </div>
      <div className="story-values">
        <div>♢ <span>Curated<br />quality</span></div>
        <div>♧ <span>Limited<br />releases</span></div>
        <div>◉ <span>Culture<br />first</span></div>
        <div>♙ <span>Community<br />driven</span></div>
      </div>
    </section>

    <section className="community section-light" id="community">
      <div className="community-intro">
        <p className="eyebrow">Real people. Real style.</p>
        <h2>WHAT OUR COMMUNITY<br />SAYS</h2>
        <ActionLink variant="dark" to="/#community">View all reviews</ActionLink>
        <div className="rating">★★★★★ <small>4.9 / 5 from 3,200+ reviews</small></div>
      </div>
      <div className="reviews">{reviews.map((review) => <ReviewCard key={review.author} {...review} />)}</div>
    </section>

    <section className="guides section-dark" id="apparel">
      <SectionHeading
        eyebrow="Style guide"
        title="INSPO FROM THE DISTRICT"
        description={<>Outfit ideas, culture stories, and style tips<br />to keep you ahead of the game.</>}
        action={<ActionLink to="/#apparel">View all articles</ActionLink>}
      />
      <div className="article-grid">{articles.map((article) => <article key={article.title}>
        <div className={`article-image ${article.imageClass}`} />
        <small>{article.date}</small>
        <h3>{article.title}</h3>
        <span>Read more →</span>
      </article>)}</div>
    </section>

    <section className="newsletter section-light">
      <div>
        <h2>STAY IN THE DISTRICT</h2>
        <p>Be the first to know about new drops, exclusive offers,<br />and culture content.</p>
      </div>
      <form className="email-box" onSubmit={(event) => event.preventDefault()}>
        <input type="email" placeholder="Enter your email address" aria-label="Email address" />
        <button>SIGN UP</button>
        <div><span>◯ Exclusive access</span><span>◯ Early drops</span><span>◯ Special offers</span></div>
      </form>
      <div className="newsletter-mark">ED</div>
    </section>
  </main>
}
