import { useCallback, useEffect, useMemo, useState, type ReactNode } from 'react'
import { ApiError, apiRequest } from './api'
import { StoreContext, type CheckoutReservation, type StoreContextValue } from './store-context'
import type { CartItem, User } from './types'

const GUEST_CART_KEY = 'exitdrop.guest-cart'

function readGuestCart(): CartItem[] {
  try {
    const value: unknown = JSON.parse(localStorage.getItem(GUEST_CART_KEY) ?? '[]')
    return Array.isArray(value) ? value as CartItem[] : []
  } catch {
    return []
  }
}

function saveGuestCart(items: CartItem[]) {
  localStorage.setItem(GUEST_CART_KEY, JSON.stringify(items))
}

export function StoreProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [adminUser, setAdminUser] = useState<User | null>(null)
  const [authReady, setAuthReady] = useState(false)
  const [adminAuthReady, setAdminAuthReady] = useState(false)
  const [adminAuthError, setAdminAuthError] = useState<string | null>(null)
  const [cart, setCart] = useState<CartItem[]>([])
  const [error, setError] = useState<string | null>(null)
  const [reservation, setReservation] = useState<CheckoutReservation | null>(null)
  const [reservationServerOffset, setReservationServerOffset] = useState(0)

  const refreshCart = useCallback(async () => {
    if (!user) {
      setCart(readGuestCart())
      return
    }
    const response = await apiRequest<{ items: CartItem[] }>('/cart')
    setCart(response.items)
  }, [user])

  const refreshReservation = useCallback(async () => {
    const response = await apiRequest<{
      reservation: CheckoutReservation | null
      server_time: string
    }>('/checkout/reservation')
    setReservation(response.reservation)
    setReservationServerOffset(Date.parse(response.server_time) - Date.now())
  }, [])

  const mergeGuestCart = useCallback(async () => {
    const guestItems = readGuestCart()
    if (guestItems.length) {
      await apiRequest('/cart/merge', {
        method: 'POST',
        body: JSON.stringify({ items: guestItems.map((item) => ({ product_id: item.product_id, quantity: item.quantity })) }),
      })
      localStorage.removeItem(GUEST_CART_KEY)
    }
  }, [])

  const refreshAdminSession = useCallback(async () => {
    setAdminAuthError(null)
    try {
      const currentAdmin = await apiRequest<User>('/admin/auth/me')
      setAdminUser(currentAdmin)
    } catch (reason) {
      setAdminUser(null)
      if (reason instanceof ApiError && reason.status === 401) return
      const message = reason instanceof Error ? reason.message : 'No se pudo verificar la sesión administrativa.'
      setAdminAuthError(message)
      throw reason
    }
  }, [])

  useEffect(() => {
    let cancelled = false
    async function loadCustomerSession() {
      try {
        const currentUser = await apiRequest<User>('/auth/me')
        if (cancelled) return
        setUser(currentUser)
        const guestItems = readGuestCart()
        if (guestItems.length) {
          await apiRequest('/cart/merge', {
            method: 'POST',
            body: JSON.stringify({ items: guestItems.map((item) => ({ product_id: item.product_id, quantity: item.quantity })) }),
          })
          localStorage.removeItem(GUEST_CART_KEY)
        }
        const response = await apiRequest<{ items: CartItem[] }>('/cart')
        if (!cancelled) setCart(response.items)
        await refreshReservation()
      } catch (reason) {
        if (!cancelled && !(reason instanceof ApiError && reason.status === 401)) {
          setError(reason instanceof Error ? reason.message : 'No se pudo cargar la sesión.')
        }
        if (!cancelled) setCart(readGuestCart())
      } finally {
        if (!cancelled) setAuthReady(true)
      }
    }

    async function loadAdminSession() {
      try {
        const currentAdmin = await apiRequest<User>('/admin/auth/me')
        if (!cancelled) setAdminUser(currentAdmin)
      } catch (reason) {
        if (!cancelled && !(reason instanceof ApiError && reason.status === 401)) {
          setAdminAuthError(reason instanceof Error ? reason.message : 'No se pudo verificar la sesión administrativa.')
        }
      } finally {
        if (!cancelled) setAdminAuthReady(true)
      }
    }

    void loadCustomerSession()
    void loadAdminSession()
    return () => { cancelled = true }
  }, [refreshReservation])

  const addToCart = useCallback(async (product: CartItem, quantity: number) => {
    setError(null)
    if (user) {
      const response = await apiRequest<{ items: CartItem[] }>('/cart/items', {
        method: 'POST',
        body: JSON.stringify({ product_id: product.product_id, quantity }),
      })
      setCart(response.items)
      return
    }
    const guestCart = readGuestCart()
    const existing = guestCart.find((item) => item.product_id === product.product_id)
    const next = existing
      ? guestCart.map((item) => item.product_id === product.product_id ? { ...item, quantity: item.quantity + quantity, line_total: ((item.quantity + quantity) * Number(item.price)).toFixed(2) } : item)
      : [...guestCart, { ...product, id: null, quantity, line_total: (quantity * Number(product.price)).toFixed(2) }]
    if (next.some((item) => item.quantity > item.stock)) throw new Error('La cantidad solicitada supera el inventario disponible.')
    saveGuestCart(next)
    setCart(next)
  }, [user])

  const setQuantity = useCallback(async (item: CartItem, quantity: number) => {
    if (!user) {
      const next = cart.map((entry) => entry.product_id === item.product_id
        ? { ...entry, quantity, line_total: (quantity * Number(entry.price)).toFixed(2) }
        : entry)
      saveGuestCart(next)
      setCart(next)
      return
    }
    if (item.id === null) return
    const response = await apiRequest<{ items: CartItem[] }>(`/cart/items/${item.id}`, {
      method: 'PUT',
      body: JSON.stringify({ quantity }),
    })
    setCart(response.items)
  }, [cart, user])

  const removeItem = useCallback(async (item: CartItem) => {
    if (!user) {
      const next = cart.filter((entry) => entry.product_id !== item.product_id)
      saveGuestCart(next)
      setCart(next)
      return
    }
    if (item.id === null) return
    const response = await apiRequest<{ items: CartItem[] }>(`/cart/items/${item.id}`, { method: 'DELETE' })
    setCart(response.items)
  }, [cart, user])

  const signIn = useCallback(async (email: string, password: string) => {
    const signedInUser = await apiRequest<User>('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    })
    setUser(signedInUser)
    await mergeGuestCart()
    const response = await apiRequest<{ items: CartItem[] }>('/cart')
    setCart(response.items)
    await refreshReservation()
  }, [mergeGuestCart, refreshReservation])

  const adminSignIn = useCallback(async (email: string, password: string, challengeId: string, captchaAnswer: string) => {
    const signedInUser = await apiRequest<User>('/admin/auth/login', {
      method: 'POST',
      body: JSON.stringify({
        email,
        password,
        challenge_id: challengeId,
        captcha_answer: captchaAnswer,
      }),
    })
    setAdminUser(signedInUser)
    setAdminAuthError(null)
    setAdminAuthReady(true)
  }, [])

  const register = useCallback(async (name: string, email: string, password: string) => {
    const registeredUser = await apiRequest<User>('/auth/register', {
      method: 'POST',
      body: JSON.stringify({ full_name: name, email, password }),
    })
    setUser(registeredUser)
    await mergeGuestCart()
    const response = await apiRequest<{ items: CartItem[] }>('/cart')
    setCart(response.items)
    await refreshReservation()
  }, [mergeGuestCart, refreshReservation])

  const signOut = useCallback(async () => {
    await apiRequest('/auth/logout', { method: 'POST' })
    setUser(null)
    setCart(readGuestCart())
    setReservation(null)
  }, [])

  const adminSignOut = useCallback(async () => {
    await apiRequest('/admin/auth/logout', { method: 'POST' })
    setAdminUser(null)
  }, [])

  const value = useMemo<StoreContextValue>(() => ({
    user,
    adminUser,
    authReady,
    adminAuthReady,
    adminAuthError,
    cart,
    cartCount: cart.reduce((count, item) => count + item.quantity, 0),
    subtotal: cart.reduce((total, item) => total + Number(item.line_total), 0),
    error,
    reservation,
    reservationServerOffset,
    clearError: () => setError(null),
    addToCart,
    setQuantity,
    removeItem,
    signIn,
    adminSignIn,
    adminSignOut,
    refreshAdminSession,
    register,
    signOut,
    refreshCart,
    refreshReservation,
  }), [user, adminUser, authReady, adminAuthReady, adminAuthError, cart, error, reservation, reservationServerOffset, addToCart, setQuantity, removeItem, signIn, adminSignIn, adminSignOut, refreshAdminSession, register, signOut, refreshCart, refreshReservation])

  return <StoreContext.Provider value={value}>{children}</StoreContext.Provider>
}
