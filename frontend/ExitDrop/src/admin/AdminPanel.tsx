import { useEffect, useState, type FormEvent, type ReactNode } from 'react'
import { Link, Navigate, NavLink, Outlet, useNavigate } from 'react-router-dom'
import { ApiError, apiRequest } from '../api'
import { useStore } from '../store-context'
import type { Category } from '../types'
import { AdminFeedback, AdminPageHeading } from './AdminShared'
import './admin.css'

type CaptchaChallenge = { challenge_id: string; question: string }
type AdminUser = { id: number; full_name: string; email: string; is_admin: boolean; is_active: boolean; created_at: string | null }
type AdminDrop = { id: number; name: string; description: string | null; starts_at: string; ends_at: string; status: string }
type AdminProduct = {
  id: number
  category_id: number
  category: string | null
  drop_id: number | null
  drop: string | null
  name: string
  description: string | null
  price: string
  stock: number
  image_url: string | null
  is_active: boolean
}
type DashboardData = {
  month: string
  monthly_sales: number
  best_selling_product: { id: number; name: string; units_sold: number; revenue: number } | null
  latest_drop: (AdminDrop & { sales: number; remaining_units: number; remaining_seconds: number }) | null
}

const currency = new Intl.NumberFormat('es-MX', { style: 'currency', currency: 'USD' })

function formatCurrency(value: number) {
  return currency.format(value)
}

function formatDate(value: string | null) {
  return value ? new Date(value).toLocaleDateString('es-MX', { year: 'numeric', month: 'short', day: 'numeric' }) : '—'
}

function formatDateTime(value: string) {
  return new Date(value).toLocaleString('es-MX', { dateStyle: 'medium', timeStyle: 'short' })
}

export function AdminGate({ children }: { children: ReactNode }) {
  const { user, authReady } = useStore()
  const [verification, setVerification] = useState<{ userId: number; status: 'allowed' | 'denied' | 'error'; message?: string } | null>(null)
  const [retry, setRetry] = useState(0)

  useEffect(() => {
    if (!authReady || !user?.is_admin) return
    let cancelled = false
    apiRequest('/admin/auth/me').then(() => {
      if (!cancelled) setVerification({ userId: user.id, status: 'allowed' })
    }).catch((reason: unknown) => {
      if (cancelled) return
      if (reason instanceof ApiError && (reason.status === 401 || reason.status === 403)) {
        setVerification({ userId: user.id, status: 'denied' })
      } else {
        setVerification({
          userId: user.id,
          status: 'error',
          message: reason instanceof Error ? reason.message : 'No se pudo verificar la sesión administrativa.',
        })
      }
    })
    return () => { cancelled = true }
  }, [authReady, user, retry])

  if (!authReady) {
    return <main className="admin-loading"><span className="admin-spinner" />Verificando acceso…</main>
  }
  if (!user?.is_admin) return <Navigate to="/admin/login" replace />
  if (verification?.userId !== user.id) {
    return <main className="admin-loading"><span className="admin-spinner" />Verificando acceso…</main>
  }
  if (verification.status === 'denied') return <Navigate to="/admin/login" replace />
  if (verification.status === 'error') {
    return <main className="admin-loading"><AdminFeedback error={verification.message} /><button className="admin-secondary-button" onClick={() => setRetry((value) => value + 1)}>Reintentar</button></main>
  }
  return children
}

export function AdminLogin() {
  const { adminSignIn } = useStore()
  const navigate = useNavigate()
  const [challenge, setChallenge] = useState<CaptchaChallenge | null>(null)
  const [refresh, setRefresh] = useState(0)
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [captchaAnswer, setCaptchaAnswer] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  useEffect(() => {
    let cancelled = false
    apiRequest<CaptchaChallenge>('/admin/auth/captcha').then((value) => {
      if (!cancelled) setChallenge(value)
    }).catch((reason: unknown) => {
      if (!cancelled) setError(reason instanceof Error ? reason.message : 'No se pudo cargar el CAPTCHA.')
    })
    return () => { cancelled = true }
  }, [refresh])

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!challenge) return
    setBusy(true)
    setError(null)
    try {
      await adminSignIn(email, password, challenge.challenge_id, captchaAnswer)
      navigate('/admin/dashboard', { replace: true })
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'No se pudo iniciar sesión.')
      setChallenge(null)
      setCaptchaAnswer('')
      setRefresh((value) => value + 1)
    } finally {
      setBusy(false)
    }
  }

  return <main className="admin-login-page">
    <section className="admin-login-card">
      <Link to="/" className="admin-brand"><span className="brand-mark">E</span><span>exotik<span>drop</span></span></Link>
      <p className="admin-eyebrow">Acceso restringido</p>
      <h1>Panel administrador</h1>
      <p className="admin-muted">Inicia sesión con una cuenta autorizada para administrar la tienda.</p>
      <form className="admin-form" onSubmit={(event) => void submit(event)}>
        <label>Email<input type="email" autoComplete="username" value={email} onChange={(event) => setEmail(event.target.value)} required /></label>
        <label>Contraseña<input type="password" autoComplete="current-password" value={password} onChange={(event) => setPassword(event.target.value)} required /></label>
        <label className="captcha-label">{challenge?.question ?? 'Cargando CAPTCHA…'}
          <input inputMode="numeric" autoComplete="off" aria-label="Respuesta del CAPTCHA" value={captchaAnswer} onChange={(event) => setCaptchaAnswer(event.target.value)} required disabled={!challenge} />
        </label>
        {!challenge && <button className="text-button captcha-retry" type="button" onClick={() => { setError(null); setRefresh((value) => value + 1) }}>Volver a cargar el CAPTCHA</button>}
        <AdminFeedback error={error} />
        <button className="admin-primary-button" disabled={busy || !challenge}>{busy ? 'Validando…' : 'Entrar al panel'}<span aria-hidden="true">→</span></button>
      </form>
      <Link className="admin-back-link" to="/">← Volver a ExotikDrop</Link>
    </section>
  </main>
}

export function AdminLayout() {
  const { user, signOut } = useStore()
  const navigate = useNavigate()
  const [logoutError, setLogoutError] = useState<string | null>(null)

  async function logout() {
    setLogoutError(null)
    try {
      await signOut()
      navigate('/admin/login', { replace: true })
    } catch (reason) {
      setLogoutError(reason instanceof Error ? reason.message : 'No se pudo cerrar la sesión.')
    }
  }

  return <div className="admin-app">
    <aside className="admin-sidebar">
      <Link to="/admin/dashboard" className="admin-brand"><span className="brand-mark">E</span><span>exotik<span>drop</span></span></Link>
      <div className="sidebar-label">MENÚ PRINCIPAL</div>
      <nav className="admin-nav">
        <NavLink to="/admin/dashboard"><span>◫</span>Dashboard</NavLink>
        <NavLink to="/admin/users"><span>♙</span>Usuarios</NavLink>
        <NavLink to="/admin/products"><span>◈</span>Productos</NavLink>
        <NavLink to="/admin/drops"><span>◷</span>Drops</NavLink>
      </nav>
      <div className="sidebar-bottom">
        <div className="admin-profile"><span className="profile-avatar">{user?.full_name.slice(0, 1).toUpperCase() ?? 'A'}</span><div><strong>{user?.full_name ?? 'Administrador'}</strong><small>Administrador</small></div></div>
        <button className="admin-logout" onClick={() => void logout()}><span>↪</span>Cerrar sesión</button>
      </div>
    </aside>
    <section className="admin-main">
      <header className="admin-topbar"><div><span className="admin-status-dot" />Panel de administración</div><span className="admin-date">{new Date().toLocaleDateString('es-MX', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })}</span></header>
      <main className="admin-content"><AdminFeedback error={logoutError} /><Outlet /></main>
    </section>
  </div>
}

function useRemainingSeconds(endsAt: string | null) {
  const [now, setNow] = useState(() => Date.now())
  useEffect(() => {
    const timer = window.setInterval(() => setNow(Date.now()), 1000)
    return () => window.clearInterval(timer)
  }, [])
  const seconds = endsAt ? Math.max(0, Math.floor((new Date(endsAt).getTime() - now) / 1000)) : 0
  const days = Math.floor(seconds / 86400)
  const hours = Math.floor((seconds % 86400) / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  const remaining = seconds % 60
  return {
    seconds,
    label: `${days}d ${String(hours).padStart(2, '0')}h ${String(minutes).padStart(2, '0')}m ${String(remaining).padStart(2, '0')}s`,
  }
}

export function AdminDashboard() {
  const [data, setData] = useState<DashboardData | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [reload, setReload] = useState(0)

  useEffect(() => {
    let cancelled = false
    apiRequest<DashboardData>('/admin/dashboard').then((value) => {
      if (!cancelled) {
        setData(value)
        setError(null)
      }
    }).catch((reason: unknown) => {
      if (!cancelled) setError(reason instanceof Error ? reason.message : 'No se pudo cargar el dashboard.')
    })
    return () => { cancelled = true }
  }, [reload])

  const remaining = useRemainingSeconds(data?.latest_drop?.ends_at ?? null)
  const monthLabel = data ? new Date(data.month).toLocaleDateString('es-MX', { month: 'long', year: 'numeric' }) : ''

  return <div>
    <AdminPageHeading eyebrow="Resumen de la tienda" title="Dashboard" description={`Vista general de ExotikDrop · ${monthLabel}`} action={<button className="admin-secondary-button" onClick={() => setReload((value) => value + 1)}>↻ Actualizar</button>} />
    <AdminFeedback error={error} />
    {!data ? <div className="admin-loading-panel"><span className="admin-spinner" />Cargando métricas…</div> : <>
      <section className="metric-grid">
        <article className="metric-card"><div className="metric-card-top"><span>VENTAS DEL MES</span><span className="metric-icon metric-icon-rust">$</span></div><strong>{formatCurrency(data.monthly_sales)}</strong><small>Pedidos creados · {monthLabel}</small></article>
        <article className="metric-card"><div className="metric-card-top"><span>PRODUCTO MÁS VENDIDO</span><span className="metric-icon metric-icon-purple">↗</span></div><strong className="metric-product">{data.best_selling_product?.name ?? 'Sin ventas'}</strong><small>{data.best_selling_product ? `${data.best_selling_product.units_sold} unidades vendidas` : 'Aún no hay pedidos registrados'}</small></article>
        <article className="metric-card"><div className="metric-card-top"><span>UNIDADES VENDIDAS</span><span className="metric-icon metric-icon-green">▤</span></div><strong>{data.best_selling_product?.units_sold ?? 0}</strong><small>Del producto líder, histórico</small></article>
      </section>
      <section className="latest-drop-card">
        <div className="latest-drop-heading"><div><p className="admin-eyebrow">Lanzamiento más reciente</p><h2>{data.latest_drop?.name ?? 'Todavía no hay drops lanzados'}</h2></div>{data.latest_drop && <span className={`drop-status-pill ${remaining.seconds > 0 ? 'is-live' : 'is-ended'}`}>{remaining.seconds > 0 ? 'EN CURSO' : 'FINALIZADO'}</span>}</div>
        {!data.latest_drop ? <p className="admin-muted">Cuando un drop tenga una fecha de inicio pasada, su actividad aparecerá aquí.</p> : <div className="drop-metrics">
          <div><small>VENTAS DEL DROP</small><strong>{formatCurrency(data.latest_drop.sales)}</strong></div>
          <div><small>UNIDADES RESTANTES</small><strong>{data.latest_drop.remaining_units.toLocaleString('es-MX')}</strong></div>
          <div><small>TIEMPO RESTANTE</small><strong className="drop-countdown">{remaining.label}</strong><span>Finaliza {formatDateTime(data.latest_drop.ends_at)}</span></div>
        </div>}
      </section>
      <p className="admin-footnote">Las ventas reflejan el total de pedidos creados, incluidos aquellos cuyo pago sigue pendiente.</p>
    </>}
  </div>
}

type UserForm = { id?: number; full_name: string; email: string; password: string; is_admin: boolean }
const emptyUserForm: UserForm = { full_name: '', email: '', password: '', is_admin: false }

export function AdminUsers() {
  const [users, setUsers] = useState<AdminUser[]>([])
  const [form, setForm] = useState<UserForm>(emptyUserForm)
  const [error, setError] = useState<string | null>(null)
  const [notice, setNotice] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)
  const { user: currentUser } = useStore()

  async function loadUsers() {
    setUsers(await apiRequest<AdminUser[]>('/admin/users'))
  }

  useEffect(() => {
    let cancelled = false
    apiRequest<AdminUser[]>('/admin/users').then((value) => {
      if (!cancelled) setUsers(value)
    }).catch((reason: unknown) => {
      if (!cancelled) setError(reason instanceof Error ? reason.message : 'No se pudieron cargar los usuarios.')
    })
    return () => { cancelled = true }
  }, [])

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setBusy(true)
    setError(null)
    setNotice(null)
    const payload: Record<string, unknown> = {
      full_name: form.full_name,
      email: form.email,
      is_admin: form.is_admin,
    }
    if (form.password) payload.password = form.password
    try {
      if (form.id) await apiRequest(`/admin/users/${form.id}`, { method: 'PUT', body: JSON.stringify(payload) })
      else await apiRequest('/admin/users', { method: 'POST', body: JSON.stringify({ ...payload, password: form.password }) })
      await loadUsers()
      setNotice(form.id ? 'Usuario actualizado.' : 'Usuario creado.')
      setForm(emptyUserForm)
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'No se pudo guardar el usuario.')
    } finally {
      setBusy(false)
    }
  }

  async function toggleActive(target: AdminUser) {
    setError(null)
    setNotice(null)
    try {
      if (target.is_active) await apiRequest(`/admin/users/${target.id}`, { method: 'DELETE' })
      else await apiRequest(`/admin/users/${target.id}`, { method: 'PUT', body: JSON.stringify({ ...target, is_active: true }) })
      await loadUsers()
      setNotice(target.is_active ? 'Cuenta desactivada.' : 'Cuenta reactivada.')
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'No se pudo cambiar el estado del usuario.')
    }
  }

  return <div>
    <AdminPageHeading eyebrow="Control de acceso" title="Usuarios" description="Administra las cuentas, permisos y acceso a la tienda." />
    <AdminFeedback error={error} notice={notice} />
    <div className="admin-resource-layout">
      <section className="admin-panel"><div className="admin-panel-heading"><h2>Cuentas</h2><span>{users.length} registradas</span></div>
        <div className="admin-table-wrap"><table className="admin-table"><thead><tr><th>Usuario</th><th>Rol</th><th>Estado</th><th>Registro</th><th>Acciones</th></tr></thead><tbody>
          {users.map((entry) => <tr key={entry.id}><td><strong>{entry.full_name}</strong><small>{entry.email}</small></td><td>{entry.is_admin ? 'Administrador' : 'Cliente'}</td><td><span className={`state-pill ${entry.is_active ? 'state-active' : 'state-inactive'}`}>{entry.is_active ? 'Activo' : 'Inactivo'}</span></td><td>{formatDate(entry.created_at)}</td><td className="table-actions"><button onClick={() => { setForm({ id: entry.id, full_name: entry.full_name, email: entry.email, password: '', is_admin: entry.is_admin }); setError(null) }}>Editar</button><button disabled={entry.id === currentUser?.id} onClick={() => void toggleActive(entry)}>{entry.is_active ? 'Desactivar' : 'Reactivar'}</button></td></tr>)}
          {!users.length && <tr><td colSpan={5} className="empty-table">No hay usuarios registrados.</td></tr>}
        </tbody></table></div>
      </section>
      <section className="admin-panel admin-form-panel"><div className="admin-panel-heading"><h2>{form.id ? 'Editar usuario' : 'Crear usuario'}</h2>{form.id && <button className="text-button" onClick={() => setForm(emptyUserForm)}>Cancelar</button>}</div>
        <form className="admin-form" onSubmit={(event) => void submit(event)}>
          <label>Nombre completo<input value={form.full_name} onChange={(event) => setForm({ ...form, full_name: event.target.value })} required /></label>
          <label>Email<input type="email" value={form.email} onChange={(event) => setForm({ ...form, email: event.target.value })} required /></label>
          <label>{form.id ? 'Nueva contraseña (opcional)' : 'Contraseña'}<input type="password" minLength={8} autoComplete="new-password" value={form.password} onChange={(event) => setForm({ ...form, password: event.target.value })} required={!form.id} /></label>
          <label className="admin-checkbox"><input type="checkbox" checked={form.is_admin} onChange={(event) => setForm({ ...form, is_admin: event.target.checked })} /> Permisos de administrador</label>
          <button className="admin-primary-button" disabled={busy}>{busy ? 'Guardando…' : form.id ? 'Guardar cambios' : 'Crear cuenta'}</button>
        </form>
      </section>
    </div>
  </div>
}

type ProductForm = { id?: number; name: string; category_id: string; drop_id: string; price: string; stock: string; description: string; image_url: string; is_active: boolean }
const emptyProductForm: ProductForm = { name: '', category_id: '', drop_id: '', price: '', stock: '0', description: '', image_url: '', is_active: true }
const MAX_PRODUCT_IMAGE_SIZE = 10 * 1024 * 1024
const PRODUCT_IMAGE_TYPES = ['image/jpeg', 'image/png', 'image/webp', 'image/avif']

async function uploadProductImage(file: File): Promise<string> {
  const cloudName = import.meta.env.VITE_CLOUDINARY_CLOUD_NAME?.trim()
  const uploadPreset = import.meta.env.VITE_CLOUDINARY_UPLOAD_PRESET?.trim()
  if (!cloudName || !uploadPreset) {
    throw new Error('Configura VITE_CLOUDINARY_CLOUD_NAME y VITE_CLOUDINARY_UPLOAD_PRESET en frontend/ExitDrop/.env.local.')
  }
  if (!/^[a-zA-Z0-9_-]+$/.test(cloudName)) {
    throw new Error('VITE_CLOUDINARY_CLOUD_NAME tiene un formato no válido.')
  }

  const body = new FormData()
  body.append('file', file)
  body.append('upload_preset', uploadPreset)
  const response = await fetch(`https://api.cloudinary.com/v1_1/${encodeURIComponent(cloudName)}/image/upload`, {
    method: 'POST',
    body,
  })
  const result = await response.json() as { secure_url?: string; error?: { message?: string } }
  if (!response.ok) {
    throw new Error(result.error?.message ?? 'Cloudinary no pudo guardar la imagen.')
  }
  if (!result.secure_url) {
    throw new Error('Cloudinary no devolvió una URL segura para la imagen.')
  }
  const uploadedUrl = new URL(result.secure_url)
  if (uploadedUrl.protocol !== 'https:' || !uploadedUrl.hostname.endsWith('.cloudinary.com')) {
    throw new Error('Cloudinary devolvió una URL de imagen no válida.')
  }
  return uploadedUrl.toString()
}

export function AdminProducts() {
  const [products, setProducts] = useState<AdminProduct[]>([])
  const [categories, setCategories] = useState<Category[]>([])
  const [drops, setDrops] = useState<AdminDrop[]>([])
  const [form, setForm] = useState<ProductForm>(emptyProductForm)
  const [error, setError] = useState<string | null>(null)
  const [notice, setNotice] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)
  const [imageUploading, setImageUploading] = useState(false)
  const [imageName, setImageName] = useState('')

  async function loadData() {
    const [nextProducts, nextCategories, nextDrops] = await Promise.all([
      apiRequest<AdminProduct[]>('/admin/products'),
      apiRequest<Category[]>('/categories'),
      apiRequest<AdminDrop[]>('/admin/drops'),
    ])
    setProducts(nextProducts)
    setCategories(nextCategories)
    setDrops(nextDrops)
  }

  useEffect(() => {
    let cancelled = false
    Promise.all([
      apiRequest<AdminProduct[]>('/admin/products'),
      apiRequest<Category[]>('/categories'),
      apiRequest<AdminDrop[]>('/admin/drops'),
    ]).then(([nextProducts, nextCategories, nextDrops]) => {
      if (!cancelled) {
        setProducts(nextProducts)
        setCategories(nextCategories)
        setDrops(nextDrops)
      }
    }).catch((reason: unknown) => {
      if (!cancelled) setError(reason instanceof Error ? reason.message : 'No se pudieron cargar los productos.')
    })
    return () => { cancelled = true }
  }, [])

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setBusy(true)
    setError(null)
    setNotice(null)
    const payload = {
      name: form.name,
      category_id: Number(form.category_id),
      drop_id: form.drop_id ? Number(form.drop_id) : null,
      price: form.price,
      stock: Number(form.stock),
      description: form.description || null,
      image_url: form.image_url || null,
      is_active: form.is_active,
    }
    try {
      if (form.id) await apiRequest(`/admin/products/${form.id}`, { method: 'PUT', body: JSON.stringify(payload) })
      else await apiRequest('/admin/products', { method: 'POST', body: JSON.stringify(payload) })
      await loadData()
      setNotice(form.id ? 'Producto actualizado.' : 'Producto creado.')
      setForm(emptyProductForm)
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'No se pudo guardar el producto.')
    } finally {
      setBusy(false)
    }
  }

  async function toggleActive(product: AdminProduct) {
    setError(null)
    setNotice(null)
    try {
      await apiRequest(`/admin/products/${product.id}`, {
        method: product.is_active ? 'DELETE' : 'PUT',
        ...(product.is_active ? {} : { body: JSON.stringify({ ...product, is_active: true }) }),
      })
      await loadData()
      setNotice(product.is_active ? 'Producto desactivado; su historial se conserva.' : 'Producto reactivado.')
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'No se pudo cambiar el estado del producto.')
    }
  }

  async function selectProductImage(file: File | undefined) {
    if (!file) return
    setError(null)
    setNotice(null)
    if (!PRODUCT_IMAGE_TYPES.includes(file.type)) {
      setError('Elige una imagen JPG, PNG, WebP o AVIF.')
      return
    }
    if (file.size > MAX_PRODUCT_IMAGE_SIZE) {
      setError('La imagen debe pesar 10 MB o menos.')
      return
    }

    setImageUploading(true)
    setImageName(file.name)
    try {
      const imageUrl = await uploadProductImage(file)
      setForm((current) => ({ ...current, image_url: imageUrl }))
      setNotice('Imagen subida correctamente a Cloudinary.')
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'No se pudo subir la imagen a Cloudinary.')
    } finally {
      setImageUploading(false)
    }
  }

  function editProduct(product: AdminProduct) {
    setForm({
      id: product.id,
      name: product.name,
      category_id: String(product.category_id),
      drop_id: product.drop_id ? String(product.drop_id) : '',
      price: product.price,
      stock: String(product.stock),
      description: product.description ?? '',
      image_url: product.image_url ?? '',
      is_active: product.is_active,
    })
    setImageName('')
    setError(null)
  }

  return <div>
    <AdminPageHeading eyebrow="Catálogo" title="Productos" description="Actualiza el catálogo, inventario y relación con cada drop." />
    <AdminFeedback error={error} notice={notice} />
    <div className="admin-resource-layout">
      <section className="admin-panel"><div className="admin-panel-heading"><h2>Inventario</h2><span>{products.length} productos</span></div>
        <div className="admin-table-wrap"><table className="admin-table"><thead><tr><th>Producto</th><th>Categoría / drop</th><th>Precio</th><th>Stock</th><th>Estado</th><th>Acciones</th></tr></thead><tbody>
          {products.map((product) => <tr key={product.id}><td><strong>{product.name}</strong><small>#{product.id}</small></td><td>{product.category ?? '—'}<small>{product.drop ?? 'Sin drop'}</small></td><td>{formatCurrency(Number(product.price))}</td><td>{product.stock}</td><td><span className={`state-pill ${product.is_active ? 'state-active' : 'state-inactive'}`}>{product.is_active ? 'Activo' : 'Inactivo'}</span></td><td className="table-actions"><button disabled={imageUploading} onClick={() => editProduct(product)}>Editar</button><button disabled={imageUploading} onClick={() => void toggleActive(product)}>{product.is_active ? 'Desactivar' : 'Reactivar'}</button></td></tr>)}
          {!products.length && <tr><td colSpan={6} className="empty-table">No hay productos para mostrar.</td></tr>}
        </tbody></table></div>
      </section>
      <section className="admin-panel admin-form-panel"><div className="admin-panel-heading"><h2>{form.id ? 'Editar producto' : 'Nuevo producto'}</h2>{form.id && <button className="text-button" disabled={imageUploading} onClick={() => { setForm(emptyProductForm); setImageName('') }}>Cancelar</button>}</div>
        <form className="admin-form" onSubmit={(event) => void submit(event)}>
          <label>Nombre<input value={form.name} onChange={(event) => setForm({ ...form, name: event.target.value })} required /></label>
          <div className="form-two-columns"><label>Categoría<select value={form.category_id} onChange={(event) => setForm({ ...form, category_id: event.target.value })} required><option value="">Selecciona…</option>{categories.map((category) => <option key={category.id} value={category.id}>{category.name}</option>)}</select></label><label>Drop<select value={form.drop_id} onChange={(event) => setForm({ ...form, drop_id: event.target.value })}><option value="">Sin drop</option>{drops.map((drop) => <option key={drop.id} value={drop.id}>{drop.name}</option>)}</select></label></div>
          <div className="form-two-columns"><label>Precio<input type="number" step="0.01" min="0.01" value={form.price} onChange={(event) => setForm({ ...form, price: event.target.value })} required /></label><label>Unidades<input type="number" min="0" step="1" value={form.stock} onChange={(event) => setForm({ ...form, stock: event.target.value })} required /></label></div>
          <label className="product-image-label">Imagen del producto
            <input className="product-image-input" type="file" accept="image/jpeg,image/png,image/webp,image/avif" onChange={(event) => { void selectProductImage(event.target.files?.[0]); event.currentTarget.value = '' }} disabled={imageUploading} />
            <span className="product-image-hint">JPG, PNG, WebP o AVIF · máximo 10 MB · se subirá a Cloudinary</span>
          </label>
          {form.image_url && <div className="product-image-preview"><img src={form.image_url} alt="Vista previa del producto" /><div><strong>{imageName || (form.id ? 'Imagen actual del producto' : 'Imagen lista')}</strong><button className="text-button" type="button" onClick={() => { setForm({ ...form, image_url: '' }); setImageName('') }}>Quitar imagen</button></div></div>}
          {imageUploading && <p className="image-uploading" role="status"><span className="admin-spinner" />Subiendo {imageName}…</p>}
          <label>Descripción<textarea rows={3} value={form.description} onChange={(event) => setForm({ ...form, description: event.target.value })} /></label>
          {form.id && <label className="admin-checkbox"><input type="checkbox" checked={form.is_active} onChange={(event) => setForm({ ...form, is_active: event.target.checked })} /> Producto activo en tienda</label>}
          <button className="admin-primary-button" disabled={busy || imageUploading || !categories.length}>{imageUploading ? 'Subiendo imagen…' : busy ? 'Guardando…' : form.id ? 'Guardar cambios' : 'Crear producto'}</button>
        </form>
      </section>
    </div>
  </div>
}

type DropForm = { id?: number; name: string; description: string; starts_at: string; ends_at: string; status: string }
const emptyDropForm: DropForm = { name: '', description: '', starts_at: '', ends_at: '', status: 'scheduled' }

function dateTimeLocal(value: string) {
  const date = new Date(value)
  const local = new Date(date.getTime() - date.getTimezoneOffset() * 60000)
  return local.toISOString().slice(0, 16)
}

function asIso(value: string) {
  return new Date(value).toISOString()
}

export function AdminDrops() {
  const [drops, setDrops] = useState<AdminDrop[]>([])
  const [form, setForm] = useState<DropForm>(emptyDropForm)
  const [error, setError] = useState<string | null>(null)
  const [notice, setNotice] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  async function loadDrops() {
    setDrops(await apiRequest<AdminDrop[]>('/admin/drops'))
  }

  useEffect(() => {
    let cancelled = false
    apiRequest<AdminDrop[]>('/admin/drops').then((value) => {
      if (!cancelled) setDrops(value)
    }).catch((reason: unknown) => {
      if (!cancelled) setError(reason instanceof Error ? reason.message : 'No se pudieron cargar los drops.')
    })
    return () => { cancelled = true }
  }, [])

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setBusy(true)
    setError(null)
    setNotice(null)
    try {
      const payload = {
        name: form.name,
        description: form.description || null,
        starts_at: asIso(form.starts_at),
        ends_at: asIso(form.ends_at),
        status: form.status,
      }
      if (form.id) await apiRequest(`/admin/drops/${form.id}`, { method: 'PUT', body: JSON.stringify(payload) })
      else await apiRequest('/admin/drops', { method: 'POST', body: JSON.stringify(payload) })
      await loadDrops()
      setNotice(form.id ? 'Drop actualizado.' : 'Drop creado.')
      setForm(emptyDropForm)
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'No se pudo guardar el drop.')
    } finally {
      setBusy(false)
    }
  }

  async function deleteDrop(drop: AdminDrop) {
    if (!window.confirm(`¿Eliminar el drop "${drop.name}"?`)) return
    setError(null)
    setNotice(null)
    try {
      await apiRequest(`/admin/drops/${drop.id}`, { method: 'DELETE' })
      await loadDrops()
      setNotice('Drop eliminado.')
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'No se pudo eliminar el drop.')
    }
  }

  return <div>
    <AdminPageHeading eyebrow="Lanzamientos" title="Drops" description="Programa lanzamientos y administra sus fechas, estado y productos vinculados." />
    <AdminFeedback error={error} notice={notice} />
    <div className="admin-resource-layout">
      <section className="admin-panel"><div className="admin-panel-heading"><h2>Lanzamientos</h2><span>{drops.length} drops</span></div>
        <div className="admin-table-wrap"><table className="admin-table"><thead><tr><th>Drop</th><th>Inicio</th><th>Fin</th><th>Estado</th><th>Acciones</th></tr></thead><tbody>
          {drops.map((drop) => <tr key={drop.id}><td><strong>{drop.name}</strong><small>{drop.description || 'Sin descripción'}</small></td><td>{formatDateTime(drop.starts_at)}</td><td>{formatDateTime(drop.ends_at)}</td><td><span className="state-pill state-neutral">{drop.status}</span></td><td className="table-actions"><button onClick={() => setForm({ id: drop.id, name: drop.name, description: drop.description ?? '', starts_at: dateTimeLocal(drop.starts_at), ends_at: dateTimeLocal(drop.ends_at), status: drop.status })}>Editar</button><button onClick={() => void deleteDrop(drop)}>Eliminar</button></td></tr>)}
          {!drops.length && <tr><td colSpan={5} className="empty-table">No hay drops programados.</td></tr>}
        </tbody></table></div>
      </section>
      <section className="admin-panel admin-form-panel"><div className="admin-panel-heading"><h2>{form.id ? 'Editar drop' : 'Nuevo drop'}</h2>{form.id && <button className="text-button" onClick={() => setForm(emptyDropForm)}>Cancelar</button>}</div>
        <form className="admin-form" onSubmit={(event) => void submit(event)}>
          <label>Nombre<input value={form.name} onChange={(event) => setForm({ ...form, name: event.target.value })} required /></label>
          <label>Descripción<textarea rows={3} value={form.description} onChange={(event) => setForm({ ...form, description: event.target.value })} /></label>
          <label>Fecha de inicio<input type="datetime-local" value={form.starts_at} onChange={(event) => setForm({ ...form, starts_at: event.target.value })} required /></label>
          <label>Fecha de finalización<input type="datetime-local" value={form.ends_at} onChange={(event) => setForm({ ...form, ends_at: event.target.value })} required /></label>
          <label>Estado<select value={form.status} onChange={(event) => setForm({ ...form, status: event.target.value })}><option value="scheduled">Programado</option><option value="active">Activo</option><option value="ended">Finalizado</option><option value="cancelled">Cancelado</option></select></label>
          <button className="admin-primary-button" disabled={busy}>{busy ? 'Guardando…' : form.id ? 'Guardar cambios' : 'Crear drop'}</button>
        </form>
      </section>
    </div>
  </div>
}
