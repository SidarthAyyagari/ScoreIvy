'use client'

import { useEffect, useState } from 'react'
import { useRouter, useParams } from 'next/navigation'
import { useAuth } from '../../contexts/AuthContext'
import { apiJson } from '../../utils/api'
import styles from './page.module.css'

interface TestAttempt {
  id: number
  test_id: number
  score: number | null
  total_questions: number
  correct_answers: number | null
  completed_at: string | null
  test?: {
    id: number
    name: string
    description: string | null
  }
}

interface AvailableTest {
  id: number
  name: string
  description: string | null
  time_limit_minutes: number
  question_count: number
}

export default function PackageDetailPage() {
  const { isAuthenticated } = useAuth()
  const router = useRouter()
  const params = useParams()
  const packageId = params.id as string
  const [attempts, setAttempts] = useState<TestAttempt[]>([])
  const [availableTests, setAvailableTests] = useState<AvailableTest[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!isAuthenticated) {
      router.push('/')
      return
    }

    fetchAttempts()
  }, [isAuthenticated, router, packageId])

  const fetchAttempts = async () => {
    try {
      setLoading(true)
      const [attemptsData, availableTestsData] = await Promise.all([
        apiJson<TestAttempt[]>(`/api/tests/user-package/${packageId}/attempts`),
        apiJson<AvailableTest[]>(`/api/tests/user-package/${packageId}/available`)
      ])
      
      // Fetch test details for each attempt
      const attemptsWithTests = await Promise.all(
        attemptsData.map(async (attempt) => {
          try {
            const test = await apiJson(`/api/tests/${attempt.test_id}`)
            return { ...attempt, test }
          } catch {
            return attempt
          }
        })
      )
      
      setAttempts(attemptsWithTests)
      setAvailableTests(availableTestsData)
    } catch (err) {
      console.error('Error fetching attempts:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleViewResults = (attemptId: number) => {
    router.push(`/results/${attemptId}`)
  }

  const handleStartTest = (testId: number) => {
    router.push(`/exam?testId=${testId}&userPackageId=${packageId}`)
  }

  const completedAttempts = attempts.filter(a => a.completed_at)

  if (loading) {
    return (
      <div className={styles.container}>
        <div className={styles.card}>
          <p>Loading...</p>
        </div>
      </div>
    )
  }

  return (
    <div className={styles.container}>
      <div className={styles.card}>
        <div className={styles.header}>
          <button onClick={() => router.push('/dashboard')} className={styles.backButton}>
            ← Back to Dashboard
          </button>
          <h1 className={styles.title}>Package Tests</h1>
        </div>

        {/* Available Tests */}
        <div className={styles.section}>
          <h2 className={styles.sectionTitle}>Available Tests</h2>
          {availableTests.length === 0 ? (
            <div className={styles.emptyState}>No available tests</div>
          ) : (
            <div className={styles.attemptList}>
              {availableTests.map((test) => (
                <div key={test.id} className={styles.attemptCard}>
                  <div className={styles.attemptInfo}>
                    <h3>{test.name}</h3>
                    <p>{test.description || 'Test description'}</p>
                    <div className={styles.attemptStats}>
                      <span>{test.question_count} questions</span>
                      <span>Time limit: {test.time_limit_minutes} minutes</span>
                    </div>
                  </div>
                  <button
                    onClick={() => handleStartTest(test.id)}
                    className={styles.startButton}
                  >
                    Start Test
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Completed Tests */}
        <div className={styles.section}>
          <h2 className={styles.sectionTitle}>Completed Tests</h2>
          {completedAttempts.length === 0 ? (
            <div className={styles.emptyState}>No completed tests yet</div>
          ) : (
            <div className={styles.attemptList}>
              {completedAttempts.map((attempt) => (
                <div key={attempt.id} className={styles.attemptCard}>
                  <div className={styles.attemptInfo}>
                    <h3>{attempt.test?.name || 'Test'}</h3>
                    <p>{attempt.test?.description || 'Test description'}</p>
                    <div className={styles.attemptStats}>
                      <span>Score: {attempt.score?.toFixed(1) || 0}%</span>
                      <span>
                        {attempt.correct_answers || 0} / {attempt.total_questions} correct
                      </span>
                      {attempt.completed_at && (
                        <span>
                          Completed: {new Date(attempt.completed_at).toLocaleDateString()}
                        </span>
                      )}
                    </div>
                  </div>
                  <button
                    onClick={() => handleViewResults(attempt.id)}
                    className={styles.viewButton}
                  >
                    View Results
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

