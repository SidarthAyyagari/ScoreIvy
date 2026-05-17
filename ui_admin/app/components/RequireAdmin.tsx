'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '../contexts/AuthContext'
import { isAdminGateEnabled } from '../lib/config'
import styles from './RequireAdmin.module.css'

export function RequireAdmin({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, isAdmin, isLoading } = useAuth()
  const router = useRouter()
  const adminGateEnabled = isAdminGateEnabled()

  useEffect(() => {
    if (isLoading) return
    if (!isAuthenticated) {
      router.replace('/')
      return
    }
    if (adminGateEnabled && !isAdmin) {
      router.replace('/?error=not_admin')
    }
  }, [isAuthenticated, isAdmin, isLoading, adminGateEnabled, router])

  if (isLoading) {
    return <div className={styles.loading}>Loading…</div>
  }

  if (!isAuthenticated || (adminGateEnabled && !isAdmin)) {
    return null
  }

  return <>{children}</>
}
