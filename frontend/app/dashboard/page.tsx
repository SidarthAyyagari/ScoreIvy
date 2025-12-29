'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '../contexts/AuthContext'
import { apiJson } from '../utils/api'
import styles from './page.module.css'

interface Package {
  id: number
  name: string
  description: string | null
  test_count: number
  price: number
}

interface UserPackage {
  id: number
  package_id: number
  tests_remaining: number
  purchased_at: string
  expires_at: string | null
  package?: Package
}

export default function DashboardPage() {
  const { user, logout, isAuthenticated } = useAuth()
  const router = useRouter()
  const [availablePackages, setAvailablePackages] = useState<Package[]>([])
  const [userPackages, setUserPackages] = useState<UserPackage[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!isAuthenticated) {
      router.push('/')
      return
    }

    fetchData()
  }, [isAuthenticated, router])

  const fetchData = async () => {
    try {
      setLoading(true)
      
      // Fetch available packages
      const packages = await apiJson<Package[]>('/api/packages/')
      setAvailablePackages(packages)
      
      // Fetch user packages (now includes package details)
      const userPkgs = await apiJson<UserPackage[]>('/api/packages/user/purchased')
      setUserPackages(userPkgs)
    } catch (err) {
      console.error('Error fetching data:', err)
    } finally {
      setLoading(false)
    }
  }

  const handlePurchase = async (packageId: number) => {
    try {
      await apiJson(`/api/packages/${packageId}/purchase`, {
        method: 'POST',
      })
      
      // Refresh data
      fetchData()
      alert('Package purchased successfully!')
    } catch (err: any) {
      alert(err.message || 'Failed to purchase package')
    }
  }

  const handleViewPackage = (userPackageId: number) => {
    router.push(`/package/${userPackageId}`)
  }

  if (loading) {
    return (
      <div className={styles.container}>
        <div className={styles.dashboardCard}>
          <p>Loading...</p>
        </div>
      </div>
    )
  }

  return (
    <div className={styles.container}>
      <div className={styles.dashboardCard}>
        <div className={styles.header}>
          <div>
            <h1 className={styles.title}>Welcome{user?.name ? `, ${user.name}` : ''}!</h1>
            <p className={styles.subtitle}>Manage your test packages and start practicing</p>
          </div>
          <button onClick={logout} className={styles.logoutButton}>
            Logout
          </button>
        </div>

        <div className={styles.panels}>
          {/* Active Packages Panel */}
          <div className={styles.panel}>
            <h2 className={styles.panelTitle}>My Packages</h2>
            {userPackages.length === 0 ? (
              <div className={styles.emptyState}>
                <p>You haven't purchased any packages yet.</p>
                <p>Browse available packages below to get started!</p>
              </div>
            ) : (
              <div className={styles.packageList}>
                {userPackages.map((userPkg) => (
                  <div key={userPkg.id} className={styles.packageCard}>
                    <div className={styles.packageInfo}>
                      <h3>{userPkg.package?.name || 'Package'}</h3>
                      <p>{userPkg.package?.description || 'Test package'}</p>
                      <div className={styles.packageStats}>
                        <span>Tests Remaining: {userPkg.tests_remaining}</span>
                        <span>Total Tests: {userPkg.package?.test_count || 0}</span>
                      </div>
                    </div>
                    <button
                      onClick={() => handleViewPackage(userPkg.id)}
                      className={styles.viewButton}
                    >
                      View Package
        </button>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Available Packages Panel */}
          <div className={styles.panel}>
            <h2 className={styles.panelTitle}>Available Packages</h2>
            {availablePackages.length === 0 ? (
              <div className={styles.emptyState}>
                <p>No packages available at the moment.</p>
              </div>
            ) : (
              <div className={styles.packageList}>
                {availablePackages.map((pkg) => (
                  <div key={pkg.id} className={styles.packageCard}>
                    <div className={styles.packageInfo}>
                      <h3>{pkg.name}</h3>
                      <p>{pkg.description || 'Test package'}</p>
                      <div className={styles.packageStats}>
                        <span className={styles.price}>${pkg.price.toFixed(2)}</span>
                        <span>{pkg.test_count} Tests</span>
                      </div>
                    </div>
                    <button
                      onClick={() => handlePurchase(pkg.id)}
                      className={styles.purchaseButton}
                    >
                      Purchase
        </button>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
