import { useCallback, useEffect, useMemo, useState, type ReactNode } from 'react'
import { apiRequest } from './api'
import { StoreContext, type StoreContextValue } from './store-context'
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
  const [authReady, setAuthReady] = useState(false)
  const [cart, setCart] = useState<CartItem[]>([])
  const [error, setError] = useState<string | null>(null)

  const refreshCart = useCallback(async () => {
    if (!user) {
      setCart(readGuestCart())
      return
    }
    const response = await apiRequest<{ items: CartItem[] }>('/cart')
    setCart(response.items)
  }, [user])

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

  useEffect(() => {
    let cancelled = false
    apiRequest<User>('/auth/me').then(async (currentUser) => {
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
    }).catch((reason: unknown) => {
      if (!cancelled && !(reason instanceof Error && 'status' in reason && reason.status === 401)) {
        setError(reason instanceof Error ? reason.message : 'No se pudo cargar la sesión.')
      }
      if (!cancelled) setCart(readGuestCart())
    }).finally(() => {
      if (!cancelled) setAuthReady(true)
    })
    return () => { cancelled = true }
  }, [])

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
  }, [mergeGuestCart])

  const register = useCallback(async (name: string, email: string, password: string) => {
    const registeredUser = await apiRequest<User>('/auth/register', {
      method: 'POST',
      body: JSON.stringify({ full_name: name, email, password }),
    })
    setUser(registeredUser)
    await mergeGuestCart()
    const response = await apiRequest<{ items: CartItem[] }>('/cart')
    setCart(response.items)
  }, [mergeGuestCart])

  const signOut = useCallback(async () => {
    await apiRequest('/auth/logout', { method: 'POST' })
    setUser(null)
    setCart(readGuestCart())
  }, [])

  const value = useMemo<StoreContextValue>(() => ({
    user,
    authReady,
    cart,
    cartCount: cart.reduce((count, item) => count + item.quantity, 0),
    subtotal: cart.reduce((total, item) => total + Number(item.line_total), 0),
    error,
    clearError: () => setError(null),
    addToCart,
    setQuantity,
    removeItem,
    signIn,
    register,
    signOut,
    refreshCart,
  }), [user, authReady, cart, error, addToCart, setQuantity, removeItem, signIn, register, signOut, refreshCart])

  return <StoreContext.Provider value={value}>{children}</StoreContext.Provider>
}
