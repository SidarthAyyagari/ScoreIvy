'use client'

import { useEffect, useState } from 'react'
import styles from './DevModeBanner.module.css'

export function DevModeBanner() {
  const [skipAdminAuth, setSkipAdminAuth] = useState(false)
  const [loaded, setLoaded] = useState(false)

  useEffect(() => {
    const base = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
    fetch(`${base}/api/health`)
      .then((res) => res.json())
      .then((data: { skip_admin_auth?: boolean }) => {
        setSkipAdminAuth(!!data.skip_admin_auth)
      })
      .catch(() => setSkipAdminAuth(false))
      .finally(() => setLoaded(true))
  }, [])

  if (!loaded || !skipAdminAuth) {
    return null
  }

  return (
    <div className={styles.banner} role="status">
      Dev mode: SKIP_ADMIN_AUTH is on — use &quot;Continue without Google&quot; on the login page.
      Turn off before production.
    </div>
  )
}
