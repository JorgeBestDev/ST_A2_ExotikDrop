import './App.css'

type Product = {
  name: string
  price: string
  image: string
  tag?: string
}

const products: Product[] = [
  { name: 'Air Jordan 1 Retro Low OG “Mocha”', price: '$160.00', image: 'https://images.unsplash.com/photo-1552346154-21d32810aba3?auto=format&fit=crop&w=800&q=85' },
  { name: 'adidas Samba OG “Cream Black”', price: '$120.00', image: 'https://images.unsplash.com/photo-1542291026-7eec264c27ff?auto=format&fit=crop&w=800&q=85' },
  { name: 'ExitDrop Washed Hoodie', price: '$89.00', image: 'https://images.unsplash.com/photo-1556821840-3a63f95609a7?auto=format&fit=crop&w=800&q=85' },
  { name: 'ExitDrop Cargo Pants “Brown”', price: '$99.00', image: 'https://images.unsplash.com/photo-1517841905240-472988babdf9?auto=format&fit=crop&w=800&q=85' },
  { name: 'ExitDrop Logo Cap', price: '$39.00', image: 'https://images.unsplash.com/photo-1521369909029-2afed882baee?auto=format&fit=crop&w=800&q=85' },
]

const categories = [
  { title: 'Sneakers', image: products[0].image },
  { title: 'Hoodies', image: products[2].image },
  { title: 'T-Shirts', image: 'https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?auto=format&fit=crop&w=800&q=85' },
  { title: 'Pants', image: products[3].image },
  { title: 'Hats & Accessories', image: products[4].image },
]

const Arrow = () => <span className="arrow">→</span>
const Heart = () => <span className="heart" aria-label="Add to wishlist">♡</span>

function App() {
  return (
    <div className="store">
      <div className="shipping-bar">FREE SHIPPING ON ORDERS OVER $150 <span>•</span> EASY 30-DAY RETURNS <span>•</span> PAY LATER WITH AFTERPAY</div>
      <header className="header">
        <a className="logo" href="#top">Exit<span>Drop.</span></a>
        <nav>
          <a href="#new">New Arrivals</a><a href="#sneakers">Sneakers</a><a href="#apparel">Apparel</a><a href="#accessories">Accessories</a><a href="#story">Brands</a><a href="#new">Sale</a>
        </nav>
        <div className="header-actions"><button aria-label="Search">⌕</button><button aria-label="Account">♙</button><button aria-label="Wishlist">♡</button><button aria-label="Cart">▢<b>0</b></button></div>
      </header>

      <main id="top">
        <section className="hero">
          <div className="hero-content">
            <p className="eyebrow">Sole. Style. District.</p>
            <h1>BUILT ON<br />CULTURE.<br /><strong>WORN BY YOU.</strong></h1>
            <p className="hero-subtitle">Curated sneakers and streetwear<br />for those who set the pace.</p>
            <div className="hero-buttons"><a className="button button-brown" href="#new">Shop New Arrivals</a><a className="button button-outline" href="#apparel">Shop Apparel</a></div>
          </div>
          <div className="hero-image" />
        </section>

        <section className="category-section section-light" id="sneakers">
          <div className="category-intro"><p className="eyebrow">Shop by category</p><h2>EXPLORE OUR<br />WORLD</h2><a className="button button-dark" href="#apparel">View all categories</a></div>
          <div className="category-grid">{categories.map((category) => <a className="category-card" href="#new" key={category.title}><div className="category-image" style={{ backgroundImage: `url(${category.image})` }} /><h3>{category.title}</h3><span>Shop now <Arrow /></span></a>)}</div>
        </section>

        <section className="drops section-dark" id="new">
          <div className="section-heading"><div><p className="eyebrow">New drops</p><h2>JUST LANDED</h2><p>The latest heat. Fresh styles.<br />Limited quantities.</p></div><a className="button button-brown" href="#new">Shop all new drops</a></div>
          <div className="product-grid">{products.map((product) => <article className="product-card" key={product.name}><div className="product-photo" style={{ backgroundImage: `url(${product.image})` }}><Heart /></div><h3>{product.name}</h3><strong>{product.price}</strong></article>)}</div>
          <div className="slider-dots"><i /><i className="active" /><i /><i /></div>
        </section>

        <section className="story" id="story">
          <div className="story-photo" />
          <div className="story-copy"><p className="eyebrow">Our story</p><h2>MORE THAN A BRAND.<br />IT&apos;S A MOVEMENT.</h2><p>ExitDrop was built for the culture. Inspired by the streets, driven by community. We curate what&apos;s real and authentic—so you can wear your story.</p><a className="button button-outline" href="#community">Learn more about us</a></div>
          <div className="story-values"><div>♢ <span>Curated<br />quality</span></div><div>♧ <span>Limited<br />releases</span></div><div>◉ <span>Culture<br />first</span></div><div>♙ <span>Community<br />driven</span></div></div>
        </section>

        <section className="featured-drop">
          <div className="featured-shoe" />
          <div className="featured-copy"><p className="eyebrow">Limited release</p><h2>AIR JORDAN 1 HIGH OG “MOCHA”</h2><p>Iconic colorway. Timeless energy.<br />Strictly limited.</p><div className="countdown"><span>02<small>days</small></span><span>14<small>hrs</small></span><span>37<small>mins</small></span><span>48<small>secs</small></span></div></div>
          <div className="featured-buy"><strong>$180.00</strong><a className="button button-brown" href="#community">Notify me</a><small>Limited to 1 per customer</small></div>
        </section>

        <section className="community section-light" id="community">
          <div className="community-intro"><p className="eyebrow">Real people. Real style.</p><h2>WHAT OUR COMMUNITY<br />SAYS</h2><a className="button button-dark" href="#community">View all reviews</a><div className="rating">★★★★★ <small>4.9 / 5 from 3,200+ reviews</small></div></div>
          <div className="reviews"><blockquote>“<p>ExitDrop always comes through with the heat and the service. My go-to for exclusive drops!</p><footer>— Marcus T.</footer><b>★★★★★</b></blockquote><blockquote>“<p>The quality is unmatched and the pieces hit different in person. 10/10 recommend.</p><footer>— Jasmine R.</footer><b>★★★★★</b></blockquote><blockquote>“<p>Fast shipping, dope packaging, and legit products. You&apos;ve got a customer for life.</p><footer>— Daniel K.</footer><b>★★★★★</b></blockquote></div>
        </section>

        <section className="guides section-dark" id="apparel"><div className="section-heading"><div><p className="eyebrow">Style guide</p><h2>INSPO FROM THE DISTRICT</h2><p>Outfit ideas, culture stories, and style tips<br />to keep you ahead of the game.</p></div><a className="button button-brown" href="#apparel">View all articles</a></div><div className="article-grid"><article><div className="article-image article-one" /><small>MAY 12, 2024</small><h3>5 WAYS TO STYLE CARGO<br />PANTS THIS SEASON</h3><span>Read more →</span></article><article><div className="article-image article-two" /><small>MAY 5, 2024</small><h3>WHY NEUTRALS ARE ALWAYS<br />A GOOD IDEA</h3><span>Read more →</span></article><article><div className="article-image article-three" /><small>APR 18, 2024</small><h3>THE RISE OF STREETWEAR:<br />THEN &amp; NOW</h3><span>Read more →</span></article></div></section>

        <section className="newsletter section-light"><div><h2>STAY IN THE DISTRICT</h2><p>Be the first to know about new drops, exclusive offers,<br />and culture content.</p></div><div className="email-box"><input placeholder="Enter your email address" /><button>SIGN UP</button><div><span>◯ Exclusive access</span><span>◯ Early drops</span><span>◯ Special offers</span></div></div><div className="newsletter-mark">SD</div></section>
      </main>
      <footer className="footer"><div><a className="logo" href="#top">Exit<span>Drop.</span></a><p>Curated sneakers and streetwear<br />for the culture. Join the movement.</p><div className="socials">◎ ♫ ◉ ▶</div></div><div><b>SHOP</b><a href="#new">New Arrivals</a><a href="#sneakers">Sneakers</a><a href="#apparel">Apparel</a><a href="#accessories">Accessories</a></div><div><b>CUSTOMER CARE</b><a href="#top">Contact Us</a><a href="#top">Shipping &amp; Delivery</a><a href="#top">Returns &amp; Exchanges</a><a href="#top">FAQ</a></div><div><b>ABOUT</b><a href="#story">Our Story</a><a href="#story">Careers</a><a href="#story">Store Locator</a><a href="#story">Privacy Policy</a></div><div><b>GET THE APP</b><div className="app-badges"> App Store<br />▶ Google Play</div></div><small className="copyright">© 2024 ExitDrop. All Rights Reserved.</small></footer>
    </div>
  )
}

export default App
