import { useEffect, useState, type FormEvent } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { apiRequest } from './api'
import { useStore } from './store-context'
import type { Order, ShippingAddress } from './types'

type AddressInput = Omit<ShippingAddress, 'id' | 'is_default'>
const emptyAddress: AddressInput = { recipient: '', phone: '', line1: '', line2: '', city: '', region: '', postal_code: '', country: '' }

export function CheckoutPage() {
  const { cart, subtotal, user, setQuantity, removeItem, refreshCart } = useStore()
  const navigate = useNavigate()
  const [addresses, setAddresses] = useState<ShippingAddress[]>([])
  const [selectedAddress, setSelectedAddress] = useState<number | ''>('')
  const [address, setAddress] = useState<AddressInput>(emptyAddress)
  const [addAddress, setAddAddress] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  useEffect(() => {
    if (!user) return
    apiRequest<ShippingAddress[]>('/account/addresses').then((result) => {
      setAddresses(result)
      const preferred = result.find((entry) => entry.is_default) ?? result[0]
      if (preferred) setSelectedAddress(preferred.id)
      else setAddAddress(true)
    }).catch((reason: unknown) => setError(reason instanceof Error ? reason.message : 'Could not load shipping addresses.'))
  }, [user])

  if (!user) return <main className="flow-page"><section className="flow-card"><h1>Sign in to checkout</h1><p className="flow-lead">Your bag will be here when you return.</p><Link className="button button-brown" to="/login" state={{ from: '/checkout' }}>Continue to sign in</Link></section></main>
  if (!cart.length) return <main className="flow-page"><section className="flow-card"><h1>Your bag is empty</h1><Link className="button button-dark" to="/#new">Shop the drops</Link></section></main>

  function setAddressField(field: keyof AddressInput, value: string) {
    setAddress((previous) => ({ ...previous, [field]: value }))
  }

  async function updateCartItem(item: (typeof cart)[number], quantity: number) {
    setError(null)
    try {
      await setQuantity(item, quantity)
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Could not update the bag.')
    }
  }

  async function deleteCartItem(item: (typeof cart)[number]) {
    setError(null)
    try {
      await removeItem(item)
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Could not remove this item.')
    }
  }

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setBusy(true)
    setError(null)
    try {
      let addressId = selectedAddress
      if (addAddress) {
        const created = await apiRequest<ShippingAddress>('/account/addresses', {
          method: 'POST',
          body: JSON.stringify({ ...address, is_default: addresses.length === 0 }),
        })
        addressId = created.id
      }
      if (!addressId) throw new Error('Select a shipping address.')
      const order = await apiRequest<Order>('/orders', {
        method: 'POST',
        body: JSON.stringify({ address_id: addressId, payment_method: 'simulated_card' }),
      })
      await refreshCart()
      navigate(`/orders/${order.id}/confirmation`)
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Could not place your order.')
    } finally {
      setBusy(false)
    }
  }

  return <main className="flow-page checkout-page">
    <div className="flow-title"><p className="eyebrow">Almost yours</p><h1>Checkout</h1><p className="flow-lead">Your order is reserved once you confirm below.</p></div>
    <form className="checkout-grid" onSubmit={(event) => void submit(event)}>
      <div className="checkout-main">
        <section className="flow-card checkout-section">
          <div className="step-heading"><span>01</span><div><h2>Delivery details</h2><p>Where should we send your drop?</p></div></div>
          {addresses.length > 0 && !addAddress && <div className="address-options">{addresses.map((entry) => <label className="address-option" key={entry.id}><input type="radio" name="address" value={entry.id} checked={selectedAddress === entry.id} onChange={() => setSelectedAddress(entry.id)} /><span><strong>{entry.recipient} {entry.is_default && <small>DEFAULT</small>}</strong><br />{entry.line1}{entry.line2 ? `, ${entry.line2}` : ''}<br />{entry.city}, {entry.region} {entry.postal_code}<br />{entry.country} · {entry.phone}</span></label>)}</div>}
          {addAddress && <div className="address-form-grid">
            <label>Recipient<input required value={address.recipient} onChange={(event) => setAddressField('recipient', event.target.value)} /></label>
            <label>Phone<input required value={address.phone} onChange={(event) => setAddressField('phone', event.target.value)} /></label>
            <label className="span-two">Address line 1<input required value={address.line1} onChange={(event) => setAddressField('line1', event.target.value)} /></label>
            <label className="span-two">Address line 2 <small>(optional)</small><input value={address.line2 ?? ''} onChange={(event) => setAddressField('line2', event.target.value)} /></label>
            <label>City<input required value={address.city} onChange={(event) => setAddressField('city', event.target.value)} /></label>
            <label>State / region<input required value={address.region} onChange={(event) => setAddressField('region', event.target.value)} /></label>
            <label>Postal code<input required value={address.postal_code} onChange={(event) => setAddressField('postal_code', event.target.value)} /></label>
            <label>Country<input required value={address.country} onChange={(event) => setAddressField('country', event.target.value)} /></label>
          </div>}
          {addresses.length > 0 && <button className="inline-action" type="button" onClick={() => setAddAddress((value) => !value)}>{addAddress ? 'Choose a saved address' : '+ Add another address'}</button>}
        </section>
        <section className="flow-card checkout-section">
          <div className="step-heading"><span>02</span><div><h2>Payment</h2><p>Payment processing is not connected yet.</p></div></div>
          <label className="payment-choice"><input type="radio" checked readOnly /><span className="mock-card-icon">▰</span><span><strong>Simulated card payment</strong><small>Demo only — no card number or security code is collected.</small></span><b>DEMO</b></label>
        </section>
      </div>
      <aside className="flow-card order-summary">
        <h2>Order summary</h2>
        <div className="summary-products">{cart.map((item) => <div className="summary-product" key={item.product_id}>
          <div className="summary-image" style={{ backgroundImage: `url(${item.image_url ?? ''})` }} />
          <div className="summary-product-info">
            <strong>{item.name}</strong>
            <div className="summary-product-controls" role="group" aria-label={`${item.name} quantity controls`}>
              <button type="button" aria-label={`Decrease quantity of ${item.name}`} disabled={busy || item.quantity <= 1} onClick={() => void updateCartItem(item, Math.max(1, item.quantity - 1))}>−</button>
              <span>{item.quantity}</span>
              <button type="button" aria-label={`Increase quantity of ${item.name}`} disabled={busy || item.quantity >= item.stock} onClick={() => void updateCartItem(item, item.quantity + 1)}>+</button>
              <button type="button" className="summary-remove-item" disabled={busy} onClick={() => void deleteCartItem(item)}>Remove</button>
            </div>
          </div>
          <span>${item.line_total}</span>
        </div>)}</div>
        <Link className="summary-add-items" to="/#new">Add more items</Link>
        <div className="summary-row"><span>Subtotal</span><span>${subtotal.toFixed(2)}</span></div><div className="summary-row"><span>Shipping</span><span>Calculated after confirmation</span></div>
        <div className="summary-total"><span>Estimated total</span><strong>${subtotal.toFixed(2)}</strong></div>
        {error && <p className="form-error" role="alert">{error}</p>}
        <button className="button button-brown" disabled={busy}>{busy ? 'Placing order…' : 'Place demo order'}</button>
        <small className="summary-disclaimer">This is a development checkout. No payment is charged.</small>
      </aside>
    </form>
  </main>
}

export function OrderConfirmationPage() {
  const { orderId } = useParams()
  const [order, setOrder] = useState<Order | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!orderId) return
    apiRequest<Order>(`/orders/${orderId}`).then(setOrder).catch((reason: unknown) => {
      setError(reason instanceof Error ? reason.message : 'Could not load the order.')
    })
  }, [orderId])

  return <main className="flow-page"><section className="flow-card confirmation-card">
    {error ? <p className="form-error">{error}</p> : !order ? <p>Loading order…</p> : <>
      <div className="confirmation-check">✓</div><p className="eyebrow">Order received</p><h1>Thanks for your order.</h1><p className="flow-lead">Order #ED-{order.id.toString().padStart(6, '0')} is confirmed for development.</p>
      <div className="confirmation-details"><div><strong>Delivery to</strong><p>{order.shipping_address.recipient}<br />{order.shipping_address.line1}<br />{order.shipping_address.city}, {order.shipping_address.region} {order.shipping_address.postal_code}<br />{order.shipping_address.country}</p></div><div><strong>Demo payment</strong><p>Simulated card · {order.payment?.status}</p><strong>Total</strong><p>${order.total}</p></div></div>
      <h2>Items</h2>{order.items.map((item) => <p key={item.product_id}>{item.quantity} × {item.name} — ${item.total_price}</p>)}
      <Link className="button button-dark" to="/account">Go to your account</Link>
    </>}
  </section></main>
}
