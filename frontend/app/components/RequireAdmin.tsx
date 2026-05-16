'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '../contexts/AuthContext'

export function RequireAdmin({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, isAdmin, isLoading } = useAuth()
  const router = useRouter()

  useEffect(() => {
    if (isLoading) return
    if (!isAuthenticated) {
      router.replace('/')
      return
    }
    if (!isAdmin) {
      router.replace('/dashboard')
    }
  }, [isAuthenticated, isAdmin, isLoading, router])

  if (isLoading || !isAuthenticated || !isAdmin) {
    return null
  }

  return <>{children}</>
}
