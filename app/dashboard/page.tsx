'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import styles from './page.module.css'

export default function DashboardPage() {
  const [username, setUsername] = useState('')
  const router = useRouter()

  useEffect(() => {
    // Check if user is logged in
    const isLoggedIn = sessionStorage.getItem('isLoggedIn')
    const storedUsername = sessionStorage.getItem('username')

    if (!isLoggedIn) {
      router.push('/')
      return
    }

    if (storedUsername) {
      setUsername(storedUsername)
    }
  }, [router])

  const handleTakeTest = () => {
    router.push('/exam')
  }

  const handleLogout = () => {
    sessionStorage.removeItem('isLoggedIn')
    sessionStorage.removeItem('username')
    router.push('/')
  }

  return (
    <div className={styles.container}>
      <div className={styles.dashboardCard}>
        <h1 className={styles.title}>Welcome, {username}!</h1>
        <p className={styles.subtitle}>Ready to test your knowledge?</p>
        
        <button onClick={handleTakeTest} className={styles.testButton}>
          Take Test
        </button>

        <button onClick={handleLogout} className={styles.logoutButton}>
          Logout
        </button>
      </div>
    </div>
  )
}

