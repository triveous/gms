import { useFrappeAuth } from 'frappe-react-sdk'
import { useEffect, type JSX } from 'react'
import { useLocation } from 'react-router'

export default function ProtectedRoute({ children }: { children: JSX.Element }) {
  const { currentUser, isLoading, isValidating } = useFrappeAuth()
  const location = useLocation()

  useEffect(() => {
    if (!currentUser && !isLoading && !isValidating) {
      window.location.href = `/login?redirect-to=${location.pathname}`
    }

  }, [currentUser])
  return children
}
