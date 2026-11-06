import { useEffect, useState, type FormEvent } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { apiRequest } from './api'
import { ActionButton, ActionLink } from './components/Actions'
import CartQuantityControls from './components/CartQuantityControls'
import FlowCard from './components/FlowCard'
import { useStore } from './store-context'
import type { CartItem, Order, ShippingAddress } from './types'

type AddressInput = Omit<ShippingAddress, 'id' | 'is_default'>
const emptyAddress: AddressInput = {
  recipient: '',
  phone: '',
  line1: '',
  line2: '',
  city: '',
  region: '',
  postal_code: '',
  country: '',
}

const addressFields: Array<{ key: keyof AddressInput; label: string; required?: boolean; className?: string; optional?: boolean }> = [
  { key: 'recipient', label: 'Recipient', required: true },
  { key: 'phone', label: 'Phone', required: true },
  { key: 'line1', label: 'Address line 1', required: true, className: 'span-two' },
  { key: 'line2', label: 'Address line 2', className: 'span-two', optional: true },
  { key: 'city', label: 'City', required: true },
  { key: 'region', label: 'State / region', required: true },
  { key: 'postal_code', label: 'Postal code', required: true },
  { key: 'country', label: 'Country', required: true },
]

function AddressFields({
  address,
  onChange,
}: {
  address: AddressInput
  onChange: (field: keyof AddressInput, value: string) => void
}) {
  return <div className="address-form-grid">
    {addressFields.map(({ key, label, required, className, optional }) => <label className={className} key={key}>
      {label} {optional && <small>(optional)</small>}
      <input
        required={required}
        value={address[key] ?? ''}
        onChange={(event) => onChange(key, event.target.value)}
      />
    </label>)}
  </div>
}

function SavedAddressOptions({
  addresses,
  selectedAddress,
  onSelect,
}: {
  addresses: ShippingAddress[]
  selectedAddress: number | ''
  onSelect: (id: number) => void
}) {
  return <div className="address-options">{addresses.map((entry) => <label className="address-option" key={entry.id}>
    <input
      type="radio"
      name="address"
      value={entry.id}
      checked={selectedAddress === entry.id}
      onChange={() => onSelect(entry.id)}
    />
    <span>
      <strong>{entry.recipient} {entry.is_default && <small>DEFAULT</small>}</strong><br />
      {entry.line1}{entry.line2 ? `, ${entry.line2}` : ''}<br />
      {entry.city}, {entry.region} {entry.postal_code}<br />
      {entry.country} · {entry.phone}
    </span>
  </label>)}</div>
}

function CheckoutOrderSummary({
  cart,
  subtotal,
  busy,
  error,
  onUpdate,
  onRemove,
}: {
  cart: CartItem[]
  subtotal: number
  busy: boolean
  error: string | null
  onUpdate: (item: CartItem, quantity: number) => void
  onRemove: (item: CartItem) => void
}) {
  return <aside className="flow-card order-summary">
    <h2>Order summary</h2>
    <div className="summary-products">{cart.map((item) => <div className="summary-product" key={item.product_id}>
      <div className="summary-image" style={{ backgroundImage: `url(${item.image_url ?? ''})` }} />
      <div className="summary-product-info">
        <strong>{item.name}</strong>
        <CartQuantityControls
          className="summary-product-controls"
          quantity={item.quantity}
          label={`${item.name} quantity controls`}
          decreaseLabel={`Decrease quantity of ${item.name}`}
          increaseLabel={`Increase quantity of ${item.name}`}
          onDecrease={() => onUpdate(item, item.quantity - 1)}
          onIncrease={() => onUpdate(item, item.quantity + 1)}
          canIncrease={item.quantity < item.stock}
          disabled={busy}
          onRemove={() => onRemove(item)}
          removeClassName="summary-remove-item"
        />
      </div>
      <span>${item.line_total}</span>
    </div>)}</div>
    <Link className="summary-add-items" to="/#new">Add more items</Link>
    <div className="summary-row"><span>Subtotal</span><span>${subtotal.toFixed(2)}</span></div>
    <div className="summary-row"><span>Shipping</span><span>Calculated after confirmation</span></div>
    <div className="summary-total"><span>Estimated total</span><strong>${subtotal.toFixed(2)}</strong></div>
    {error && <p className="form-error" role="alert">{error}</p>}
    <ActionButton type="submit" disabled={busy}>{busy ? 'Placing order…' : 'Place demo order'}</ActionButton>
    <small className="summary-disclaimer">This is a development checkout. No payment is charged.</small>
  </aside>
}

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

  if (!user) return <main className="flow-page">
    <FlowCard>
      <h1>Sign in to checkout</h1>
      <p className="flow-lead">Your bag will be here when you return.</p>
      <ActionLink to="/login" state={{ from: '/checkout' }}>Continue to sign in</ActionLink>
    </FlowCard>
  </main>
  if (!cart.length) return <main className="flow-page">
    <FlowCard>
      <h1>Your bag is empty</h1>
      <ActionLink variant="dark" to="/#new">Shop the drops</ActionLink>
    </FlowCard>
  </main>

  function setAddressField(field: keyof AddressInput, value: string) {
    setAddress((previous) => ({ ...previous, [field]: value }))
  }

  async function updateCartItem(item: CartItem, quantity: number) {
    setError(null)
    try {
      await setQuantity(item, quantity)
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Could not update the bag.')
    }
  }

  async function deleteCartItem(item: CartItem) {
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
    <div className="flow-title">
      <p className="eyebrow">Almost yours</p>
      <h1>Checkout</h1>
      <p className="flow-lead">Your order is reserved once you confirm below.</p>
    </div>
    <form className="checkout-grid" onSubmit={(event) => void submit(event)}>
      <div className="checkout-main">
        <FlowCard className="checkout-section">
          <div className="step-heading">
            <span>01</span>
            <div><h2>Delivery details</h2><p>Where should we send your drop?</p></div>
          </div>
          {addresses.length > 0 && !addAddress && <SavedAddressOptions
            addresses={addresses}
            selectedAddress={selectedAddress}
            onSelect={setSelectedAddress}
          />}
          {addAddress && <AddressFields address={address} onChange={setAddressField} />}
          {addresses.length > 0 && <button className="inline-action" type="button" onClick={() => setAddAddress((value) => !value)}>
            {addAddress ? 'Choose a saved address' : '+ Add another address'}
          </button>}
        </FlowCard>
        <FlowCard className="checkout-section">
          <div className="step-heading">
            <span>02</span>
            <div><h2>Payment</h2><p>Payment processing is not connected yet.</p></div>
          </div>
          <label className="payment-choice">
            <input type="radio" checked readOnly />
            <span className="mock-card-icon">▰</span>
            <span><strong>Simulated card payment</strong><small>Demo only — no card number or security code is collected.</small></span>
            <b>DEMO</b>
          </label>
        </FlowCard>
      </div>
      <CheckoutOrderSummary
        cart={cart}
        subtotal={subtotal}
        busy={busy}
        error={error}
        onUpdate={(item, quantity) => void updateCartItem(item, quantity)}
        onRemove={(item) => void deleteCartItem(item)}
      />
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

  return <main className="flow-page">
    <FlowCard className="confirmation-card">
      {error ? <p className="form-error" role="alert">{error}</p> : !order ? <p>Loading order…</p> : <>
        <div className="confirmation-check">✓</div>
        <p className="eyebrow">Order received</p>
        <h1>Thanks for your order.</h1>
        <p className="flow-lead">Order #ED-{order.id.toString().padStart(6, '0')} is confirmed for development.</p>
        <div className="confirmation-details">
          <div><strong>Delivery to</strong><p>{order.shipping_address.recipient}<br />{order.shipping_address.line1}<br />{order.shipping_address.city}, {order.shipping_address.region} {order.shipping_address.postal_code}<br />{order.shipping_address.country}</p></div>
          <div><strong>Demo payment</strong><p>Simulated card · {order.payment?.status}</p><strong>Total</strong><p>${order.total}</p></div>
        </div>
        <h2>Items</h2>
        {order.items.map((item) => <p key={item.product_id}>{item.quantity} × {item.name} — ${item.total_price}</p>)}
        <ActionLink variant="dark" to="/account">Go to your account</ActionLink>
      </>}
    </FlowCard>
  </main>
}
