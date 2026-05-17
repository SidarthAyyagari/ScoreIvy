'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '../contexts/AuthContext'
import styles from './RequireAdmin.module.css'

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
      router.replace('/?error=not_admin')
    }
  }, [isAuthenticated, isAdmin, isLoading, router])

  if (isLoading) {
    return <div className={styles.loading}>Loading…</div>
  }

  if (!isAuthenticated || !isAdmin) {
    return null
  }

  return <>{children}</>
}
