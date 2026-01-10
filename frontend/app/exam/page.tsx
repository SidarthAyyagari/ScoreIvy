'use client'

import { useEffect, useState, useRef } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import { useAuth } from '../contexts/AuthContext'
import { apiJson } from '../utils/api'
import styles from './page.module.css'

interface Question {
  id: number
  question_text: string
  answer_choices: { [key: string]: string }
  question_order: number
}

interface TestDetail {
  id: number
  name: string
  description: string | null
  time_limit_minutes: number
  questions: Question[]
}

export default function ExamPage() {
  const { isAuthenticated } = useAuth()
  const router = useRouter()
  const searchParams = useSearchParams()
  const testId = searchParams.get('testId')
  const userPackageId = searchParams.get('userPackageId')
  const attemptId = searchParams.get('attemptId')
  
  const [test, setTest] = useState<TestDetail | null>(null)
  const [questions, setQuestions] = useState<Question[]>([])
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0)
  const [selectedAnswer, setSelectedAnswer] = useState<string | null>(null)
  const [answers, setAnswers] = useState<{ [questionId: number]: string }>({})
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [startTime] = useState(Date.now())
  const [timeRemaining, setTimeRemaining] = useState<number>(0) // in seconds
  const [testStarted, setTestStarted] = useState(false)
  const answersRef = useRef<{ [questionId: number]: string }>({})

  useEffect(() => {
    if (!isAuthenticated) {
      router.push('/')
      return
    }

    if (!testId) {
      router.push('/dashboard')
      return
    }

    fetchTest()
  }, [isAuthenticated, testId, router])

  // Update selected answer when question changes
  useEffect(() => {
    if (questions.length > 0 && currentQuestionIndex < questions.length) {
      const currentQuestion = questions[currentQuestionIndex]
      setSelectedAnswer(answers[currentQuestion.id] || null)
    }
  }, [currentQuestionIndex, questions, answers])

  // Keep ref in sync with answers state
  useEffect(() => {
    answersRef.current = answers
  }, [answers])

  const fetchTest = async () => {
    try {
      setLoading(true)
      const testData = await apiJson<TestDetail>(`/api/tests/${testId}`)
      setTest(testData)
      setQuestions(testData.questions)
      // Initialize timer with test time limit
      const totalSeconds = testData.time_limit_minutes * 60
      setTimeRemaining(totalSeconds)
      setTestStarted(true)
    } catch (err) {
      console.error('Error fetching test:', err)
      alert('Failed to load test. Please try again.')
      router.push('/dashboard')
    } finally {
      setLoading(false)
    }
  }

  // Timer effect
  useEffect(() => {
    if (!testStarted || submitting || timeRemaining <= 0) return

    const interval = setInterval(() => {
      setTimeRemaining((prev) => {
        const newTime = prev - 1
        if (newTime <= 0) {
          // Time's up - submit with latest answers
          setTimeout(() => {
            submitTestAttempt(answersRef.current)
          }, 0)
          return 0
        }
        return newTime
      })
    }, 1000)

    return () => clearInterval(interval)
  }, [testStarted, submitting, timeRemaining])

  // Prevent navigation away during test
  useEffect(() => {
    if (!testStarted || submitting) return

    const handleBeforeUnload = (e: BeforeUnloadEvent) => {
      e.preventDefault()
      e.returnValue = 'Are you sure you want to leave? Your test progress will be lost.'
      return e.returnValue
    }

    window.addEventListener('beforeunload', handleBeforeUnload)

    return () => {
      window.removeEventListener('beforeunload', handleBeforeUnload)
    }
  }, [testStarted, submitting])

  const formatTime = (seconds: number): string => {
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${mins}:${secs.toString().padStart(2, '0')}`
  }

  if (loading) {
    return (
      <div className={styles.container}>
        <div className={styles.examCard}>
          <p>Loading test...</p>
        </div>
      </div>
    )
  }

  if (!test || questions.length === 0) {
    return (
      <div className={styles.container}>
        <div className={styles.examCard}>
          <p>No test found</p>
        </div>
      </div>
    )
  }

  const currentQuestion = questions[currentQuestionIndex]
  const isLastQuestion = currentQuestionIndex === questions.length - 1
  const answerChoices = Object.entries(currentQuestion.answer_choices).sort(([a], [b]) => a.localeCompare(b))

  const handleAnswerSelect = (answerKey: string) => {
    setSelectedAnswer(answerKey)
  }

  const handleNext = async () => {
    if (selectedAnswer === null) {
      alert('Please select an answer before proceeding')
      return
    }

    // Save the current answer
    const newAnswers = { ...answers }
    newAnswers[currentQuestion.id] = selectedAnswer
    setAnswers(newAnswers)

    if (isLastQuestion) {
      // Submit test attempt
      await submitTestAttempt(newAnswers)
    } else {
      setCurrentQuestionIndex(currentQuestionIndex + 1)
      setSelectedAnswer(answers[questions[currentQuestionIndex + 1]?.id] || null)
    }
  }

  const submitTestAttempt = async (finalAnswers: { [questionId: number]: string }) => {
    try {
      setSubmitting(true)
      const totalTime = Math.floor((Date.now() - startTime) / 1000)
      const avgTimePerQuestion = Math.floor(totalTime / questions.length)

      // Prepare question attempts
      const questionAttempts = questions.map((q) => ({
        question_id: q.id,
        selected_answer: finalAnswers[q.id] || null,
        time_spent_seconds: avgTimePerQuestion
      }))

      const payload = {
        test_id: parseInt(testId!),
        question_attempts: questionAttempts
      }

      const queryParams = new URLSearchParams()
      if (userPackageId) {
        queryParams.append('user_package_id', userPackageId)
      }

      const endpoint = `/api/tests/${testId}/attempt${queryParams.toString() ? '?' + queryParams.toString() : ''}`
      const attempt = await apiJson(endpoint, {
        method: 'POST',
        body: JSON.stringify(payload),
        headers: {
          'Content-Type': 'application/json'
        }
      })

      // Navigate to results page
      router.push(`/results/${attempt.id}`)
    } catch (err) {
      console.error('Error submitting test:', err)
      alert('Failed to submit test. Please try again.')
      setSubmitting(false)
    }
  }

  return (
    <div className={styles.container}>
      <div className={styles.examCard}>
        <div className={styles.header}>
          <div className={styles.headerTop}>
            <div className={styles.progress}>
              Question {currentQuestionIndex + 1} of {questions.length}
            </div>
            <div className={`${styles.timer} ${
              timeRemaining <= 60 ? styles.timerCritical : 
              timeRemaining <= 300 ? styles.timerWarning : ''
            }`}>
              Time Remaining: {formatTime(timeRemaining)}
            </div>
          </div>
          <div className={styles.progressBar}>
            <div 
              className={styles.progressFill}
              style={{ width: `${((currentQuestionIndex + 1) / questions.length) * 100}%` }}
            />
          </div>
        </div>

        <div className={styles.questionSection}>
          <h2 className={styles.questionText}>{currentQuestion.question_text}</h2>
          
          <div className={styles.options}>
            {answerChoices.map(([key, value]) => (
              <button
                key={key}
                onClick={() => handleAnswerSelect(key)}
                className={`${styles.option} ${
                  selectedAnswer === key ? styles.optionSelected : ''
                }`}
              >
                <span className={styles.optionKey}>{key}:</span> {value}
              </button>
            ))}
          </div>
        </div>

        <div className={styles.footer}>
          <button
            onClick={handleNext}
            className={styles.nextButton}
            disabled={selectedAnswer === null || submitting}
          >
            {submitting ? 'Submitting...' : isLastQuestion ? 'Finish Exam' : 'Next'}
          </button>
        </div>
      </div>
    </div>
  )
}

