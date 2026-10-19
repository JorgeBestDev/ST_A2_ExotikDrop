import { BrowserRouter, Link, Navigate, Route, Routes, useLocation } from 'react-router-dom'
import type { ReactNode } from 'react'
import './App.css'
import './flows.css'
import './cart-checkout.css'
import AccountPage from './AccountPage'
import AuthPage from './AuthPage'
import { CheckoutPage, OrderConfirmationPage } from './CheckoutPage'
import HomePage from './HomePage'
import ProductPage from './ProductPage'
import { StoreProvider } from './StoreContext'
import { useStore } from './store-context'
import StoreLayout from './StoreLayout'

function AccountGate({ children }: { children: ReactNode }) {
  const { user, authReady } = useStore()
  const location = useLocation()
  if (!authReady) return <main className="flow-page"><p>Loading your account…</p></main>
  if (!user) return <Navigate to="/login" replace state={{ from: `${location.pathname}${location.search}` }} />
  return children
}

function NotFound() {
  return <main className="flow-page"><section className="flow-card"><p className="eyebrow">Not found</p><h1>This page has left the district.</h1><Link className="button button-dark" to="/">Return home</Link></section></main>
}

function AppRoutes() {
  return <Routes>
    <Route element={<StoreLayout />}>
      <Route index element={<HomePage />} />
      <Route path="products/:productId" element={<ProductPage />} />
      <Route path="checkout" element={<CheckoutPage />} />
      <Route path="orders/:orderId/confirmation" element={<AccountGate><OrderConfirmationPage /></AccountGate>} />
      <Route path="login" element={<AuthPage mode="login" />} />
      <Route path="register" element={<AuthPage mode="register" />} />
      <Route path="account" element={<AccountGate><AccountPage /></AccountGate>} />
      <Route path="*" element={<NotFound />} />
    </Route>
  </Routes>
}

function App() {
  return <BrowserRouter><StoreProvider><AppRoutes /></StoreProvider></BrowserRouter>
}

export default App
