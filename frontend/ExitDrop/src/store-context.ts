import { createContext, useContext } from 'react'
import type { CartItem, User } from './types'

export type StoreContextValue = {
  user: User | null
  authReady: boolean
  cart: CartItem[]
  cartCount: number
  subtotal: number
  error: string | null
  clearError: () => void
  addToCart: (product: CartItem, quantity: number) => Promise<void>
  setQuantity: (item: CartItem, quantity: number) => Promise<void>
  removeItem: (item: CartItem) => Promise<void>
  signIn: (email: string, password: string) => Promise<void>
  register: (name: string, email: string, password: string) => Promise<void>
  signOut: () => Promise<void>
  refreshCart: () => Promise<void>
}

export const StoreContext = createContext<StoreContextValue | null>(null)

export function useStore() {
  const context = useContext(StoreContext)
  if (!context) throw new Error('useStore must be used within StoreProvider')
  return context
}
