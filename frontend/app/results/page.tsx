'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import styles from './page.module.css'

interface Question {
  id: number
  question: string
  options: string[]
  correctAnswer: number
  explanation?: string
}

export default function ResultsPage() {
  const [questions, setQuestions] = useState<Question[]>([])
  const [answers, setAnswers] = useState<number[]>([])
  const [score, setScore] = useState(0)
  const [percentage, setPercentage] = useState(0)
  const router = useRouter()

  useEffect(() => {
    // Check if user is logged in
    const isLoggedIn = sessionStorage.getItem('isLoggedIn')
    if (!isLoggedIn) {
      router.push('/')
      return
    }

    // Get exam data from sessionStorage
    const storedAnswers = sessionStorage.getItem('examAnswers')
    const storedQuestions = sessionStorage.getItem('examQuestions')

    if (!storedAnswers || !storedQuestions) {
      router.push('/dashboard')
      return
    }

    const parsedAnswers = JSON.parse(storedAnswers)
    const parsedQuestions = JSON.parse(storedQuestions)

    setAnswers(parsedAnswers)
    setQuestions(parsedQuestions)

    // Calculate score
    let correctCount = 0
    parsedQuestions.forEach((q: Question, index: number) => {
      if (parsedAnswers[index] === q.correctAnswer) {
        correctCount++
      }
    })

    const calculatedScore = correctCount
    const calculatedPercentage = Math.round((correctCount / parsedQuestions.length) * 100)

    setScore(calculatedScore)
    setPercentage(calculatedPercentage)
  }, [router])

  const handleBackToDashboard = () => {
    sessionStorage.removeItem('examAnswers')
    sessionStorage.removeItem('examQuestions')
    router.push('/dashboard')
  }

  const getScoreWheelPath = () => {
    if (questions.length === 0) return ''
    
    const radius = 100
    const circumference = 2 * Math.PI * radius
    const correctCount = score
    const wrongCount = questions.length - correctCount
    
    const correctPercentage = correctCount / questions.length
    const wrongPercentage = wrongCount / questions.length
    
    const correctArcLength = correctPercentage * circumference
    const wrongArcLength = wrongPercentage * circumference
    
    // Start at top (12 o'clock)
    let currentAngle = -90 // Start at top
    
    const paths: string[] = []
    
    // Green arc for correct answers
    if (correctCount > 0) {
      const correctAngle = correctPercentage * 360
      const endAngle = currentAngle + correctAngle
      const largeArcFlag = correctPercentage > 0.5 ? 1 : 0
      
      const x1 = 120 + radius * Math.cos((currentAngle * Math.PI) / 180)
      const y1 = 120 + radius * Math.sin((currentAngle * Math.PI) / 180)
      const x2 = 120 + radius * Math.cos((endAngle * Math.PI) / 180)
      const y2 = 120 + radius * Math.sin((endAngle * Math.PI) / 180)
      
      paths.push(
        `M 120 120 L ${x1} ${y1} A ${radius} ${radius} 0 ${largeArcFlag} 1 ${x2} ${y2} Z`
      )
      
      currentAngle = endAngle
    }
    
    // Red arc for wrong answers
    if (wrongCount > 0) {
      const wrongAngle = wrongPercentage * 360
      const endAngle = currentAngle + wrongAngle
      const largeArcFlag = wrongPercentage > 0.5 ? 1 : 0
      
      const x1 = 120 + radius * Math.cos((currentAngle * Math.PI) / 180)
      const y1 = 120 + radius * Math.sin((currentAngle * Math.PI) / 180)
      const x2 = 120 + radius * Math.cos((endAngle * Math.PI) / 180)
      const y2 = 120 + radius * Math.sin((endAngle * Math.PI) / 180)
      
      paths.push(
        `M 120 120 L ${x1} ${y1} A ${radius} ${radius} 0 ${largeArcFlag} 1 ${x2} ${y2} Z`
      )
    }
    
    return paths.join(' ')
  }

  const getScoreWheelSegments = () => {
    if (questions.length === 0) return []
    
    const radius = 100
    const correctCount = score
    const wrongCount = questions.length - correctCount
    
    const correctPercentage = correctCount / questions.length
    const wrongPercentage = wrongCount / questions.length
    
    const segments: Array<{ color: string; percentage: number; angle: number }> = []
    let currentAngle = -90
    
    if (correctCount > 0) {
      const angle = correctPercentage * 360
      segments.push({ color: '#10b981', percentage: correctPercentage, angle: currentAngle })
      currentAngle += angle
    }
    
    if (wrongCount > 0) {
      segments.push({ color: '#ef4444', percentage: wrongPercentage, angle: currentAngle })
    }
    
    return segments
  }

  const isCorrect = (questionIndex: number) => {
    return answers[questionIndex] === questions[questionIndex]?.correctAnswer
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
            {score} out of {questions.length} correct
          </div>
        </div>

        <div className={styles.questionsSection}>
          <h2 className={styles.questionsTitle}>Question Review</h2>
          {questions.map((question, questionIndex) => {
            const userAnswer = answers[questionIndex]
            const correct = isCorrect(questionIndex)
            
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
                <p className={styles.questionText}>{question.question}</p>
                <div className={styles.options}>
                  {question.options.map((option, optionIndex) => {
                    const isUserAnswer = userAnswer === optionIndex
                    const isCorrectAnswer = question.correctAnswer === optionIndex
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
                      <div key={optionIndex} className={optionClass}>
                        {option}
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
