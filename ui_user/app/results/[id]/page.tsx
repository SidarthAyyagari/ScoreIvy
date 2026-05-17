'use client'

import { useEffect, useState } from 'react'
import { useRouter, useParams } from 'next/navigation'
import { useAuth } from '../../contexts/AuthContext'
import { apiJson } from '../../utils/api'
import styles from './page.module.css'

interface QuestionData {
  id: number
  question_text: string
  image_url: string | null
  answer_choices: { [key: string]: string }
  correct_answer: string
  explanation: string | null
  selected_answer: string | null
  is_correct: boolean | null
  time_spent_seconds: number | null
}

interface AttemptData {
  id: number
  test_id: number
  score: number | null
  total_questions: number
  correct_answers: number | null
  completed_at: string | null
}

export default function ResultsPage() {
  const { isAuthenticated } = useAuth()
  const router = useRouter()
  const params = useParams()
  const attemptId = params.id as string
  
  const [attempt, setAttempt] = useState<AttemptData | null>(null)
  const [questions, setQuestions] = useState<QuestionData[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!isAuthenticated) {
      router.push('/')
      return
    }

    fetchResults()
  }, [isAuthenticated, router, attemptId])

  const fetchResults = async () => {
    try {
      setLoading(true)
      const data = await apiJson<{
        attempt: AttemptData
        questions: QuestionData[]
      }>(`/api/test-results/attempts/${attemptId}/results`)
      
      setAttempt(data.attempt)
      setQuestions(data.questions)
    } catch (err) {
      console.error('Error fetching results:', err)
      router.push('/dashboard')
    } finally {
      setLoading(false)
    }
  }

  const handleBackToDashboard = () => {
    router.push('/dashboard')
  }

  if (loading) {
    return (
      <div className={styles.container}>
        <div className={styles.resultsCard}>
          <p>Loading...</p>
        </div>
      </div>
    )
  }

  if (!attempt) {
    return null
  }

  const score = attempt.score || 0
  const correctCount = attempt.correct_answers || 0
  const percentage = Math.round(score)

  const getScoreWheelSegments = () => {
    if (questions.length === 0) return []
    
    const correctCount = questions.filter(q => q.is_correct).length
    const wrongCount = questions.length - correctCount
    
    const correctPercentage = correctCount / questions.length
    const wrongPercentage = wrongCount / questions.length
    
    const segments: Array<{ color: string; percentage: number; angle: number }> = []
    let currentAngle = -90
    
    if (correctCount > 0) {
      segments.push({ color: '#10b981', percentage: correctPercentage, angle: currentAngle })
      currentAngle += correctPercentage * 360
    }
    
    if (wrongCount > 0) {
      segments.push({ color: '#ef4444', percentage: wrongPercentage, angle: currentAngle })
    }
    
    return segments
  }

  return (
    <div className={styles.container}>
      <div className={styles.resultsCard}>
        <h1 className={styles.title}>Test Results</h1>
        
        <div className={styles.scoreSection}>
          <div className={styles.wheelContainer}>
            <svg width="240" height="240" viewBox="0 0 240 240" className={styles.wheel}>
              <circle
                cx="120"
                cy="120"
                r="100"
                fill="none"
                stroke="#e5e7eb"
                strokeWidth="40"
              />
              {getScoreWheelSegments().map((segment, index) => {
                const radius = 100
                const angle = segment.percentage * 360
                const startAngle = segment.angle
                const endAngle = startAngle + angle
                const largeArcFlag = segment.percentage > 0.5 ? 1 : 0
                
                const x1 = 120 + radius * Math.cos((startAngle * Math.PI) / 180)
                const y1 = 120 + radius * Math.sin((startAngle * Math.PI) / 180)
                const x2 = 120 + radius * Math.cos((endAngle * Math.PI) / 180)
                const y2 = 120 + radius * Math.sin((endAngle * Math.PI) / 180)
                
                return (
                  <path
                    key={index}
                    d={`M 120 120 L ${x1} ${y1} A ${radius} ${radius} 0 ${largeArcFlag} 1 ${x2} ${y2} Z`}
                    fill={segment.color}
                  />
                )
              })}
            </svg>
            <div className={styles.percentageText}>
              {percentage}%
            </div>
          </div>
          <div className={styles.scoreText}>
            {correctCount} out of {attempt.total_questions} correct
          </div>
        </div>

        <div className={styles.questionsSection}>
          <h2 className={styles.questionsTitle}>Question Review</h2>
          {questions.map((question, questionIndex) => {
            const correct = question.is_correct || false
            const selectedAnswer = question.selected_answer
            const correctAnswer = question.correct_answer
            
            // Convert answer choices object to array
            const answerChoicesArray = Object.entries(question.answer_choices).map(([key, value]) => ({
              choice: key,
              text: value
            }))
            
            return (
              <div key={question.id} className={styles.questionCard}>
                <div className={styles.questionHeader}>
                  <span className={styles.questionNumber}>Question {questionIndex + 1}</span>
                  {correct ? (
                    <span className={styles.correctBadge}>✓ Correct</span>
                  ) : (
                    <span className={styles.incorrectBadge}>✗ Incorrect</span>
                  )}
                </div>
                <p className={styles.questionText}>{question.question_text}</p>
                <div className={styles.options}>
                  {answerChoicesArray.map((option) => {
                    const isUserAnswer = selectedAnswer === option.choice
                    const isCorrectAnswer = correctAnswer === option.choice
                    const isWrong = !correct && isUserAnswer
                    
                    let optionClass = styles.option
                    if (isCorrectAnswer) {
                      optionClass += ` ${styles.correctAnswer}`
                    }
                    if (isWrong) {
                      optionClass += ` ${styles.wrongAnswer}`
                    }
                    if (correct && isUserAnswer) {
                      optionClass += ` ${styles.correctSelected}`
                    }
                    
                    return (
                      <div key={option.choice} className={optionClass}>
                        {option.text}
                        {isCorrectAnswer && !correct && (
                          <span className={styles.checkmark}>✓</span>
                        )}
                        {isWrong && (
                          <span className={styles.cross}>✗</span>
                        )}
                      </div>
                    )
                  })}
                </div>
                {!correct && question.explanation && (
                  <div className={styles.explanation}>
                    <strong>Explanation:</strong>
                    <p>{question.explanation}</p>
                  </div>
                )}
              </div>
            )
          })}
        </div>

        <button onClick={handleBackToDashboard} className={styles.backButton}>
          Back to Dashboard
        </button>
      </div>
    </div>
  )
}

