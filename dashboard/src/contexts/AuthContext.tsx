
import {
  useFrappeAuth
} from 'frappe-react-sdk'
import React, { createContext, useContext } from 'react'

type AuthContextType = {
  user: string | null
  isLoggedIn: boolean
  login: (email: string, password: string) => Promise<void>
  logout: () => Promise<void>
  loading: boolean
}

const AuthContext = createContext<AuthContextType | null>(null)

export const AuthProvider = ({ children }: { children: React.ReactNode }) => {
  const {
    login: frappeLogin,
    logout: frappeLogout,
    currentUser,
    isLoading,
  } = useFrappeAuth()

  const login = async (email: string, password: string) => {
    try {
      await frappeLogin({
        username: email,
        password
      })
      window.location.href = '/'
    } catch {
      throw new Error('Invalid email or password')
    }
  }

  const logout = async () => {
    await frappeLogout()
    window.location.href = '/login'
  }

  return (
    <AuthContext.Provider
      value={{
        user: currentUser ?? null,
        isLoggedIn: !!currentUser,
        login,
        logout,
        loading: isLoading
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used inside AuthProvider')
  return ctx
}
