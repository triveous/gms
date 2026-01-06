import { Navigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import type { JSX } from 'react'

export default function ProtectedRoute({ children }: { children: JSX.Element }) {
  const { isLoggedIn, loading } = useAuth()

  if (loading) return <div>Loading...</div>
  if (!isLoggedIn) return <Navigate to="/dashboard/login" replace />

  return children
}
