'use client'

import { createContext, useContext, useState, useEffect, ReactNode, useCallback } from 'react'
import { useRouter } from 'next/navigation'
import { apiJson } from '../utils/api'
import { isAdminGateEnabled } from '../lib/config'

interface User {
  id: number
  email: string
  name: string | null
  picture: string | null
  is_admin?: boolean
}

interface AuthContextType {
  user: User | null
  token: string | null
  login: (user: User, authToken: string) => void
  logout: () => void
  isAuthenticated: boolean
  isAdmin: boolean
  adminGateEnabled: boolean
  isLoading: boolean
  refreshUser: () => Promise<void>
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [token, setToken] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const router = useRouter()

  const refreshUser = useCallback(async () => {
    const storedToken = localStorage.getItem('auth_token')
    if (!storedToken) {
      setIsLoading(false)
      return
    }

    try {
      const me = await apiJson<User>('/api/auth/me', {
        headers: { Authorization: `Bearer ${storedToken}` },
      })
      setToken(storedToken)
      setUser(me)
      localStorage.setItem('user', JSON.stringify(me))
    } catch {
      setUser(null)
      setToken(null)
      localStorage.removeItem('auth_token')
      localStorage.removeItem('user')
    } finally {
      setIsLoading(false)
    }
  }, [])

  useEffect(() => {
    const storedToken = localStorage.getItem('auth_token')
    const storedUser = localStorage.getItem('user')

    if (storedToken && storedUser) {
      setToken(storedToken)
      setUser(JSON.parse(storedUser))
      refreshUser()
    } else {
      setIsLoading(false)
    }
  }, [refreshUser])

  const login = (userData: User, authToken: string) => {
    setToken(authToken)
    setUser(userData)
    localStorage.setItem('auth_token', authToken)
    localStorage.setItem('user', JSON.stringify(userData))
  }

  const logout = () => {
    setUser(null)
    setToken(null)
    localStorage.removeItem('auth_token')
    localStorage.removeItem('user')
    router.push('/')
  }

  const adminGateEnabled = isAdminGateEnabled()
  const isAdmin = adminGateEnabled ? !!user?.is_admin : !!token && !!user

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        login,
        logout,
        isAuthenticated: !!token && !!user,
        isAdmin,
        adminGateEnabled,
        isLoading,
        refreshUser,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}
