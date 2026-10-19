import { useCallback, useEffect, useState, type FormEvent } from 'react'
import { Link } from 'react-router-dom'
import { apiRequest } from './api'
import { useStore } from './store-context'
import type { Order, ShippingAddress } from './types'

type AddressForm = Omit<ShippingAddress, 'id' | 'is_default'>
type PaymentMethod = { method: string; status: string }
const blankAddress: AddressForm = { recipient: '', phone: '', line1: '', line2: '', city: '', region: '', postal_code: '', country: '' }

export default function AccountPage() {
  const { user } = useStore()
  const [addresses, setAddresses] = useState<ShippingAddress[]>([])
  const [orders, setOrders] = useState<Order[]>([])
  const [paymentMethods, setPaymentMethods] = useState<PaymentMethod[]>([])
  const [profileName, setProfileName] = useState(user?.full_name ?? '')
  const [profileEmail, setProfileEmail] = useState(user?.email ?? '')
  const [addressForm, setAddressForm] = useState<AddressForm>(blankAddress)
  const [editingAddress, setEditingAddress] = useState<number | null>(null)
  const [currentPassword, setCurrentPassword] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [notice, setNotice] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  const loadAccountData = useCallback(async () => {
    try {
      const [addressData, orderData, paymentData] = await Promise.all([
        apiRequest<ShippingAddress[]>('/account/addresses'),
        apiRequest<Order[]>('/orders'),
        apiRequest<PaymentMethod[]>('/account/payment-methods'),
      ])
      setAddresses(addressData)
      setOrders(orderData)
      setPaymentMethods(paymentData)
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Could not load account data.')
    }
  }, [])

  useEffect(() => {
    const timer = window.setTimeout(() => { void loadAccountData() }, 0)
    return () => window.clearTimeout(timer)
  }, [loadAccountData])

  function setAddressField(field: keyof AddressForm, value: string) {
    setAddressForm((previous) => ({ ...previous, [field]: value }))
  }

  async function saveProfile(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError(null)
    setNotice(null)
    try {
      await apiRequest('/account/profile', { method: 'PUT', body: JSON.stringify({ full_name: profileName, email: profileEmail }) })
      setNotice('Profile updated.')
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Could not update your profile.')
    }
  }

  function editAddress(address: ShippingAddress) {
    const { id } = address
    const fields: AddressForm = {
      recipient: address.recipient,
      phone: address.phone,
      line1: address.line1,
      line2: address.line2,
      city: address.city,
      region: address.region,
      postal_code: address.postal_code,
      country: address.country,
    }
    setAddressForm(fields)
    setEditingAddress(id)
  }

  async function saveAddress(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError(null)
    setNotice(null)
    try {
      await apiRequest(`/account/addresses${editingAddress ? `/${editingAddress}` : ''}`, {
        method: editingAddress ? 'PUT' : 'POST',
        body: JSON.stringify({ ...addressForm, is_default: addresses.length === 0 }),
      })
      setAddressForm(blankAddress)
      setEditingAddress(null)
      setNotice('Address saved.')
      await loadAccountData()
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Could not save your address.')
    }
  }

  async function makeDefault(address: ShippingAddress) {
    try {
      await apiRequest(`/account/addresses/${address.id}`, { method: 'PUT', body: JSON.stringify({ is_default: true }) })
      await loadAccountData()
      setNotice('Default address updated.')
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Could not update the address.')
    }
  }

  async function deleteAddress(address: ShippingAddress) {
    try {
      await apiRequest(`/account/addresses/${address.id}`, { method: 'DELETE' })
      await loadAccountData()
      setNotice('Address removed.')
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Could not remove the address.')
    }
  }

  async function changePassword(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    try {
      await apiRequest('/account/password', {
        method: 'PUT',
        body: JSON.stringify({ current_password: currentPassword, new_password: newPassword }),
      })
      setCurrentPassword('')
      setNewPassword('')
      setNotice('Password changed.')
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Could not change your password.')
    }
  }

  return <main className="flow-page account-page">
    <div className="flow-title"><p className="eyebrow">Your district</p><h1>Account</h1><p className="flow-lead">Welcome back, {user?.full_name}.</p></div>
    {(error || notice) && <p className={error ? 'form-error' : 'form-success'} role="status">{error ?? notice}</p>}
    <nav className="account-nav"><a href="#profile">Profile</a><a href="#addresses">Addresses</a><a href="#orders">Orders</a><a href="#payments">Payment activity</a><a href="#security">Security</a></nav>

    <section className="flow-card account-section" id="profile"><div className="step-heading"><span>01</span><div><h2>Profile details</h2><p>Update the details on your account.</p></div></div>
      <form className="address-form-grid" onSubmit={(event) => void saveProfile(event)}>
        <label>Full name<input required value={profileName} onChange={(event) => setProfileName(event.target.value)} /></label>
        <label>Email<input type="email" required value={profileEmail} onChange={(event) => setProfileEmail(event.target.value)} /></label>
        <div className="span-two"><button className="button button-dark">Save profile</button></div>
      </form>
    </section>

    <section className="flow-card account-section" id="addresses"><div className="step-heading"><span>02</span><div><h2>Shipping addresses</h2><p>Manage multiple destinations and choose a default.</p></div></div>
      {addresses.length > 0 && <div className="saved-addresses">{addresses.map((address) => <article className="saved-address" key={address.id}><div><strong>{address.recipient} {address.is_default && <small>DEFAULT</small>}</strong><p>{address.line1}{address.line2 ? `, ${address.line2}` : ''}<br />{address.city}, {address.region} {address.postal_code}<br />{address.country} · {address.phone}</p></div><div className="address-actions"><button onClick={() => editAddress(address)}>Edit</button>{!address.is_default && <button onClick={() => void makeDefault(address)}>Set default</button>}<button onClick={() => void deleteAddress(address)}>Remove</button></div></article>)}</div>}
      <h3>{editingAddress ? 'Edit address' : 'Add an address'}</h3>
      <form className="address-form-grid" onSubmit={(event) => void saveAddress(event)}>
        <label>Recipient<input required value={addressForm.recipient} onChange={(event) => setAddressField('recipient', event.target.value)} /></label>
        <label>Phone<input required value={addressForm.phone} onChange={(event) => setAddressField('phone', event.target.value)} /></label>
        <label className="span-two">Address line 1<input required value={addressForm.line1} onChange={(event) => setAddressField('line1', event.target.value)} /></label>
        <label className="span-two">Address line 2 <small>(optional)</small><input value={addressForm.line2 ?? ''} onChange={(event) => setAddressField('line2', event.target.value)} /></label>
        <label>City<input required value={addressForm.city} onChange={(event) => setAddressField('city', event.target.value)} /></label>
        <label>State / region<input required value={addressForm.region} onChange={(event) => setAddressField('region', event.target.value)} /></label>
        <label>Postal code<input required value={addressForm.postal_code} onChange={(event) => setAddressField('postal_code', event.target.value)} /></label>
        <label>Country<input required value={addressForm.country} onChange={(event) => setAddressField('country', event.target.value)} /></label>
        <div className="span-two"><button className="button button-brown">{editingAddress ? 'Save address' : 'Add address'}</button>{editingAddress && <button className="inline-action" type="button" onClick={() => { setEditingAddress(null); setAddressForm(blankAddress) }}>Cancel edit</button>}</div>
      </form>
    </section>

    <section className="flow-card account-section" id="orders"><div className="step-heading"><span>03</span><div><h2>Order history</h2><p>Your purchases and their current status.</p></div></div>
      {orders.length ? <div className="order-list">{orders.map((order) => <article key={order.id}><div><strong>Order ED-{order.id.toString().padStart(6, '0')}</strong><small>{order.created_at ? new Date(order.created_at).toLocaleDateString() : 'Date unavailable'} · {order.status}</small></div><strong>${order.total}</strong><span>{order.items.length} items</span></article>)}</div> : <p className="muted-copy">No orders yet. Your next favorite might be in <Link to="/#new">the latest drops</Link>.</p>}
    </section>

    <section className="flow-card account-section" id="payments"><div className="step-heading"><span>04</span><div><h2>Payment activity</h2><p>Demo method history only. No card data is stored.</p></div></div>
      {paymentMethods.length ? paymentMethods.map((method) => <div className="payment-history" key={`${method.method}-${method.status}`}><span>▰</span><strong>{method.method === 'simulated_card' ? 'Simulated card' : method.method}</strong><small>{method.status}</small></div>) : <p className="muted-copy">No payment activity yet. Checkout currently uses a simulated card option.</p>}
    </section>

    <section className="flow-card account-section" id="security"><div className="step-heading"><span>05</span><div><h2>Security</h2><p>Choose a strong password with at least 8 characters.</p></div></div>
      <form className="address-form-grid" onSubmit={(event) => void changePassword(event)}>
        <label>Current password<input type="password" autoComplete="current-password" required value={currentPassword} onChange={(event) => setCurrentPassword(event.target.value)} /></label>
        <label>New password<input type="password" autoComplete="new-password" minLength={8} required value={newPassword} onChange={(event) => setNewPassword(event.target.value)} /></label>
        <div className="span-two"><button className="button button-dark">Change password</button></div>
      </form>
    </section>
  </main>
}
