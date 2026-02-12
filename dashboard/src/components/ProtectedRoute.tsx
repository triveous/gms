import { useFrappeAuth } from 'frappe-react-sdk'
import { useEffect, type JSX } from 'react'

export default function ProtectedRoute({ children }: { children: JSX.Element }) {
  const { currentUser, isLoading, isValidating } = useFrappeAuth()

  useEffect(() => {
    if (!currentUser && !isLoading && !isValidating) {
      window.location.href = '/login?redirect-to=/'
    }

  }, [currentUser])
  return children
}
