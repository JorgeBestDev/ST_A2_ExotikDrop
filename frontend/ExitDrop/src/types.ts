export type User = { id: number; email: string; full_name: string; is_admin: boolean }

export type Product = {
  id: number
  category_id: number
  category?: string | null
  name: string
  description: string | null
  price: string
  stock: number
  image_url: string | null
  is_active: boolean
}

export type Category = { id: number; name: string; image_url: string | null; description?: string | null }

export type CartItem = {
  id: number | null
  product_id: number
  name: string
  price: string
  image_url: string | null
  quantity: number
  stock: number
  line_total: string
}

export type ShippingAddress = {
  id: number
  recipient: string
  phone: string
  line1: string
  line2: string | null
  city: string
  region: string
  postal_code: string
  country: string
  is_default: boolean
}

export type Order = {
  id: number
  total: string
  status: string
  created_at: string | null
  shipping_address: Omit<ShippingAddress, 'id' | 'is_default'>
  items: Array<{ product_id: number; name: string; image_url?: string | null; quantity: number; unit_price: string; total_price: string }>
  payment: { method: string; status: string } | null
}
