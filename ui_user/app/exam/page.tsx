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
  const [markedQuestions, setMarkedQuestions] = useState<Set<number>>(new Set())
  const [showLabValues, setShowLabValues] = useState(false)
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
    // Auto-save answer when selected
    const newAnswers = { ...answers, [currentQuestion.id]: answerKey }
    setAnswers(newAnswers)
    answersRef.current = newAnswers
  }

  const handleMarkQuestion = () => {
    const newMarked = new Set(markedQuestions)
    if (newMarked.has(currentQuestion.id)) {
      newMarked.delete(currentQuestion.id)
    } else {
      newMarked.add(currentQuestion.id)
    }
    setMarkedQuestions(newMarked)
  }

  const handleQuestionNavigation = (index: number) => {
    // Save current answer before navigating
    if (selectedAnswer !== null) {
      const newAnswers = { ...answers }
      newAnswers[currentQuestion.id] = selectedAnswer
      setAnswers(newAnswers)
    }
    setCurrentQuestionIndex(index)
  }

  const handlePrevious = () => {
    if (currentQuestionIndex > 0) {
      handleQuestionNavigation(currentQuestionIndex - 1)
    }
  }

  const handleNext = async () => {
    // Save current answer
    if (selectedAnswer !== null) {
      const newAnswers = { ...answers }
      newAnswers[currentQuestion.id] = selectedAnswer
      setAnswers(newAnswers)
    }

    if (isLastQuestion) {
      // Submit test attempt
      const finalAnswers = selectedAnswer !== null ? { ...answers, [currentQuestion.id]: selectedAnswer } : answers
      await submitTestAttempt(finalAnswers)
    } else {
      handleQuestionNavigation(currentQuestionIndex + 1)
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
      const attempt = await apiJson<{ id: number }>(endpoint, {
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
      {/* Top Navigation Bar */}
      <div className={styles.topNavBar}>
        <div className={styles.topNavLeft}>
          <span className={styles.itemInfo}>Item: {currentQuestionIndex + 1} of {questions.length}</span>
          <span className={styles.blockInfo}>Block: 1 of 1</span>
          <label className={styles.markCheckbox}>
            <input
              type="checkbox"
              checked={markedQuestions.has(currentQuestion.id)}
              onChange={handleMarkQuestion}
            />
            <span>Mark</span>
          </label>
        </div>
        
        <div className={styles.topNavCenter}>
          <button 
            onClick={handlePrevious}
            disabled={currentQuestionIndex === 0}
            className={styles.navButton}
          >
            Previous
          </button>
          <button 
            onClick={handleNext}
            disabled={submitting}
            className={styles.navButton}
          >
            Next
          </button>
        </div>

        <div className={styles.topNavRight}>
          <button
            onClick={() => setShowLabValues(!showLabValues)}
            className={`${styles.utilityButton} ${showLabValues ? styles.utilityButtonActive : ''}`}
          >
            Lab Values
          </button>
          <button className={styles.utilityButton}>Notes</button>
          <button className={styles.utilityButton}>Calculator</button>
          <button className={styles.utilityButton}>Reverse Color</button>
          <button className={styles.utilityButton}>Text Zoom</button>
        </div>
      </div>

      {/* Main Content Area */}
      <div className={styles.mainContent}>
        {/* Left Sidebar - Question Numbers */}
        <div className={styles.leftSidebar}>
          {questions.map((q, index) => (
            <button
              key={q.id}
              onClick={() => handleQuestionNavigation(index)}
              className={`${styles.questionNumber} ${
                index === currentQuestionIndex ? styles.questionNumberActive : ''
              } ${
                answers[q.id] ? styles.questionNumberAnswered : ''
              } ${
                markedQuestions.has(q.id) ? styles.questionNumberMarked : ''
              }`}
            >
              {index + 1}
            </button>
          ))}
          <div className={styles.keyLabel}>Key</div>
        </div>

        {/* Center Panel - Question and Options */}
        <div className={styles.questionPanel}>
          <div className={styles.questionHeader}>
            <span className={styles.itemInfoSmall}>Item: {currentQuestionIndex + 1} of {questions.length}</span>
            <span className={styles.blockInfoSmall}>Block: 1 of 1</span>
            <label className={styles.markCheckboxSmall}>
              <input
                type="checkbox"
                checked={markedQuestions.has(currentQuestion.id)}
                onChange={handleMarkQuestion}
              />
              <span>Mark</span>
            </label>
          </div>

          <div className={styles.questionContent}>
            <div className={styles.questionText}>{currentQuestion.question_text}</div>
            
            <div className={styles.options}>
              {answerChoices.map(([key, value]) => (
                <label
                  key={key}
                  className={`${styles.option} ${
                    selectedAnswer === key ? styles.optionSelected : ''
                  }`}
                >
                  <input
                    type="radio"
                    name={`question-${currentQuestion.id}`}
                    value={key}
                    checked={selectedAnswer === key}
                    onChange={() => handleAnswerSelect(key)}
                  />
                  <span className={styles.optionLabel}>
                    <span className={styles.optionKey}>{key}.</span> {value}
                  </span>
                </label>
              ))}
            </div>

            <div className={styles.questionActions}>
              <button className={styles.showAnswerButton}>Show Answer</button>
              <button
                onClick={handleNext}
                className={styles.proceedButton}
                disabled={submitting}
              >
                {submitting ? 'Submitting...' : isLastQuestion ? 'End Block' : 'Proceed to Next Item'}
              </button>
            </div>
          </div>
        </div>

        {/* Right Panel - Lab Values (Optional) */}
        {showLabValues && (
          <div className={styles.rightPanel}>
            <div className={styles.rightPanelHeader}>
              <button
                onClick={() => setShowLabValues(false)}
                className={styles.closePanelButton}
              >
                ×
              </button>
              <h3>Lab Values</h3>
            </div>
            <div className={styles.rightPanelContent}>
              <div className={styles.labValuesTabs}>
                <button className={styles.labTabActive}>Serum</button>
                <button className={styles.labTab}>Cerebrospinal</button>
                <button className={styles.labTab}>Blood</button>
                <button className={styles.labTab}>Urine and BMI</button>
              </div>
              <div className={styles.labValuesTable}>
                <p className={styles.labValuesNote}>Reference values available during exam</p>
                <p className={styles.labValuesInfo}>
                  Lab values reference table would be displayed here. This can be populated with actual medical reference ranges if needed.
                </p>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Bottom Bar */}
      <div className={styles.bottomBar}>
        <div className={styles.bottomBarLeft}>
          <span className={styles.timeRemaining}>
            Block Time Remaining: {timeRemaining > 0 ? formatTime(timeRemaining) : '00:00'}
          </span>
          <span className={styles.lockIcon}>🔒</span>
        </div>
        <div className={styles.bottomBarRight}>
          <button
            onClick={() => {
              if (confirm('Are you sure you want to end this block? You will not be able to return.')) {
                const finalAnswers = selectedAnswer !== null ? { ...answers, [currentQuestion.id]: selectedAnswer } : answers
                submitTestAttempt(finalAnswers)
              }
            }}
            className={styles.endBlockButton}
            disabled={submitting}
          >
            End Block
          </button>
        </div>
      </div>
    </div>
  )
}

