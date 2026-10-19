import { useEffect, useRef, useState, type FocusEvent } from 'react'
import { Link, Outlet, useNavigate } from 'react-router-dom'
import { useStore } from './store-context'
import type { CartItem } from './types'

function CartContents({ close }: { close: () => void }) {
  const { cart, cartCount, subtotal, setQuantity, removeItem } = useStore()
  const navigate = useNavigate()
  return (
    <section className="cart-popover" aria-label="Shopping cart" role="dialog">
      <div className="cart-popover-head"><div><span className="eyebrow">Your selection</span><h2>Your bag <small>({cartCount})</small></h2></div><button className="icon-close" onClick={close} aria-label="Close cart">×</button></div>
      {cart.length === 0 ? <div className="cart-empty"><p>Your bag is waiting for something good.</p><Link className="button button-dark" to="/#new" onClick={close}>Explore drops</Link></div> : <>
        <div className="cart-lines">{cart.map((item: CartItem) => <article className="cart-line" key={item.product_id}>
          <div className="cart-line-image" style={{ backgroundImage: `url(${item.image_url ?? ''})` }} />
          <div className="cart-line-info"><Link to={`/products/${item.product_id}`} onClick={close}>{item.name}</Link><small>${item.price}</small><div className="cart-quantity"><button aria-label="Decrease quantity" onClick={() => void setQuantity(item, Math.max(1, item.quantity - 1))}>−</button><span>{item.quantity}</span><button aria-label="Increase quantity" disabled={item.quantity >= item.stock} onClick={() => void setQuantity(item, item.quantity + 1)}>+</button><button className="remove-item" onClick={() => void removeItem(item)}>Remove</button></div></div>
          <strong>${item.line_total}</strong>
        </article>)}</div>
        <div className="cart-total"><span>Subtotal</span><strong>${subtotal.toFixed(2)}</strong></div>
        <p className="cart-note">Shipping and taxes calculated at checkout.</p>
        <button className="button button-brown cart-checkout" onClick={() => { close(); navigate('/checkout') }}>Continue to checkout <span>→</span></button>
      </>}
    </section>
  )
}

function StoreHeader() {
  const { cartCount, user, signOut } = useStore()
  const [cartOpen, setCartOpen] = useState(false)
  const [cartPinned, setCartPinned] = useState(false)
  const cartRegionRef = useRef<HTMLDivElement>(null)
  const cartButtonRef = useRef<HTMLButtonElement>(null)

  useEffect(() => {
    if (!cartOpen) return

    function handlePointerDown(event: PointerEvent) {
      if (event.target instanceof Node && !cartRegionRef.current?.contains(event.target)) {
        setCartOpen(false)
        setCartPinned(false)
      }
    }

    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === 'Escape') {
        setCartOpen(false)
        setCartPinned(false)
        cartButtonRef.current?.focus()
      }
    }

    document.addEventListener('pointerdown', handlePointerDown)
    document.addEventListener('keydown', handleKeyDown)
    return () => {
      document.removeEventListener('pointerdown', handlePointerDown)
      document.removeEventListener('keydown', handleKeyDown)
    }
  }, [cartOpen])

  function closeCart() {
    setCartOpen(false)
    setCartPinned(false)
  }

  function closeWhenLeaving(event: FocusEvent<HTMLDivElement>) {
    if (!event.currentTarget.contains(event.relatedTarget as Node | null) && !cartPinned) setCartOpen(false)
  }

  return <>
    <div className="shipping-bar">FREE SHIPPING ON ORDERS OVER $150 <span>•</span> EASY 30-DAY RETURNS <span>•</span> PAY LATER WITH AFTERPAY</div>
    <header className="header">
      <Link className="logo" to="/">Exit<span>Drop.</span></Link>
      <nav>
        <Link to="/#new">New Arrivals</Link><Link to="/#sneakers">Sneakers</Link><Link to="/#apparel">Apparel</Link><Link to="/#accessories">Accessories</Link><Link to="/#story">Our Story</Link><Link to="/#new">Sale</Link>
      </nav>
      <div className="header-actions"><button aria-label="Search">⌕</button><Link aria-label="Account" to={user ? '/account' : '/login'}>♙</Link><button aria-label="Wishlist">♡</button>
        <div
          className="cart-hover-region"
          ref={cartRegionRef}
          onMouseEnter={() => setCartOpen(true)}
          onMouseLeave={() => { if (!cartPinned) setCartOpen(false) }}
          onFocus={() => setCartOpen(true)}
          onBlur={closeWhenLeaving}
        >
          <button
            ref={cartButtonRef}
            aria-label={`Shopping cart, ${cartCount} items`}
            aria-expanded={cartOpen}
            aria-haspopup="dialog"
            onClick={() => {
              const nextOpen = !cartPinned
              setCartPinned(nextOpen)
              setCartOpen(nextOpen)
            }}
          >▢<b>{cartCount}</b></button>
          {cartOpen && <CartContents close={closeCart} />}
        </div>
        {user && <button className="sign-out-button" onClick={() => void signOut()}>Sign out</button>}
      </div>
    </header>
  </>
}

function StoreFooter() {
  return <footer className="footer"><div><Link className="logo" to="/">Exit<span>Drop.</span></Link><p>Curated sneakers and streetwear<br />for the culture. Join the movement.</p><div className="socials">◎ ♫ ◉ ▶</div></div><div><b>SHOP</b><Link to="/#new">New Arrivals</Link><Link to="/#sneakers">Sneakers</Link><Link to="/#apparel">Apparel</Link><Link to="/#accessories">Accessories</Link></div><div><b>CUSTOMER CARE</b><a href="mailto:hello@exitdrop.co">Contact Us</a><a href="#top">Shipping &amp; Delivery</a><a href="#top">Returns &amp; Exchanges</a><a href="#top">FAQ</a></div><div><b>ABOUT</b><Link to="/#story">Our Story</Link><a href="#story">Careers</a><a href="#story">Store Locator</a><a href="#story">Privacy Policy</a></div><div><b>GET THE APP</b><div className="app-badges"> App Store<br />▶ Google Play</div></div><small className="copyright">© 2026 ExitDrop. All Rights Reserved.</small></footer>
}

export default function StoreLayout() {
  return <div className="store"><StoreHeader /><Outlet /><StoreFooter /></div>
}
