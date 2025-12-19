
import {
  useFrappeAuth
} from 'frappe-react-sdk'
import React, { createContext, useContext, useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'

type AuthContextType = {
  user: string | null
  isLoggedIn: boolean
  login: (email: string, password: string) => Promise<void>
  logout: () => Promise<void>
  loading: boolean
}

const AuthContext = createContext<AuthContextType | null>(null)

export const AuthProvider = ({ children }: { children: React.ReactNode }) => {
  const navigate = useNavigate()
  const {
    login: frappeLogin,
    logout: frappeLogout,
    currentUser,
    isLoading
  } = useFrappeAuth()

  const [user, setUser] = useState<string | null>(null)

  useEffect(() => {
    if (!isLoading) {
      setUser(currentUser ?? null)
    }
  }, [currentUser, isLoading])

  const login = async (email: string, password: string) => {
    try {
      await frappeLogin({
        username: email,
        password
      })
      setUser(currentUser)
      navigate('/')
    } catch {
      throw new Error('Invalid email or password')
    }
  }

  const logout = async () => {
    await frappeLogout()
    setUser(null)
    window.location.href = '/login'
  }

  return (
    <AuthContext.Provider
      value={{
        user,
        isLoggedIn: !!user,
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
