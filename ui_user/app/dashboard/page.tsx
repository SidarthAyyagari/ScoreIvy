'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '../contexts/AuthContext'
import { apiJson } from '../utils/api'
import styles from './page.module.css'

interface Exam {
  id: number
  slug: string
  name: string
  description: string | null
}

interface Package {
  id: number
  exam_id: number | null
  name: string
  description: string | null
  test_count: number
  price: number
  validity_days: number | null
}

interface UserPackage {
  id: number
  package_id: number
  tests_remaining: number
  purchased_at: string
  expires_at: string | null
  is_expired: boolean
  exam: { id: number; slug: string; name: string } | null
  package?: Package
}

export default function DashboardPage() {
  const { user, logout, isAuthenticated } = useAuth()
  const router = useRouter()
  const [exams, setExams] = useState<Exam[]>([])
  const [selectedExamId, setSelectedExamId] = useState<number | null>(null)
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
      const [examList, packages, userPkgs] = await Promise.all([
        apiJson<Exam[]>('/api/exams/'),
        apiJson<Package[]>('/api/packages/'),
        apiJson<UserPackage[]>('/api/packages/user/purchased'),
      ])
      setExams(examList)
      setSelectedExamId((current) => current ?? examList[0]?.id ?? null)
      setAvailablePackages(packages)
      setUserPackages(userPkgs)
    } catch (err) {
      console.error('Error fetching data:', err)
    } finally {
      setLoading(false)
    }
  }

  const visiblePackages = selectedExamId === null
    ? availablePackages
    : availablePackages.filter((pkg) => pkg.exam_id === selectedExamId)

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
                      {userPkg.exam && <span className={styles.examLabel}>{userPkg.exam.name}</span>}
                      <h3>{userPkg.package?.name || 'Package'}</h3>
                      <p>{userPkg.package?.description || 'Test package'}</p>
                      <div className={styles.packageStats}>
                        <span>Tests Remaining: {userPkg.tests_remaining}</span>
                        <span>Total Tests: {userPkg.package?.test_count || 0}</span>
                        {userPkg.expires_at && (
                          <span>
                            {userPkg.is_expired ? 'Expired' : 'Expires'}:{' '}
                            {new Date(userPkg.expires_at).toLocaleDateString()}
                          </span>
                        )}
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
            {exams.length > 1 && (
              <div className={styles.examTabs} role="tablist">
                {exams.map((exam) => (
                  <button
                    key={exam.id}
                    role="tab"
                    aria-selected={exam.id === selectedExamId}
                    className={`${styles.examTab} ${exam.id === selectedExamId ? styles.examTabActive : ''}`}
                    onClick={() => setSelectedExamId(exam.id)}
                  >
                    {exam.name}
                  </button>
                ))}
              </div>
            )}
            {visiblePackages.length === 0 ? (
              <div className={styles.emptyState}>
                <p>No packages available at the moment.</p>
              </div>
            ) : (
              <div className={styles.packageList}>
                {visiblePackages.map((pkg) => (
                  <div key={pkg.id} className={styles.packageCard}>
                    <div className={styles.packageInfo}>
                      <h3>{pkg.name}</h3>
                      <p>{pkg.description || 'Test package'}</p>
                      <div className={styles.packageStats}>
                        <span className={styles.price}>${pkg.price.toFixed(2)}</span>
                        <span>{pkg.test_count} Tests</span>
                        {pkg.validity_days && <span>Valid {pkg.validity_days} days</span>}
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
