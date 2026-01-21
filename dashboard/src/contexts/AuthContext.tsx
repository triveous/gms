
import {
  useFrappeAuth,
  useFrappeGetDocList
} from 'frappe-react-sdk'
import React, { createContext, useContext } from 'react'

type AuthContextType = {
  user: string | null
  userData: any
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
    isLoading: isAuthLoading,
  } = useFrappeAuth()

  const { data: userList, isLoading: isUserLoading } = useFrappeGetDocList(
    'User',
    {
      fields: ['username'],
      filters: [['name', '=', currentUser ?? '']]
    },
    { enabled: !!currentUser }
  )
  const userDoc = userList?.[0]


  const login = async (email: string, password: string) => {
    try {
      await frappeLogin({
        username: email,
        password
      })
      window.location.href = '/dashboard'
    } catch {
      throw new Error('Invalid email or password')
    }
  }

  const logout = async () => {
    await frappeLogout()
    window.location.href = '/login#login'
  }

  return (
    <AuthContext.Provider
      value={{
        user: currentUser ?? null,
        userData: userDoc,
        isLoggedIn: !!currentUser,
        login,
        logout,
        loading: isAuthLoading || isUserLoading
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
