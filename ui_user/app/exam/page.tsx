'use client'

import { Suspense, useCallback, useEffect, useRef, useState } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import { useAuth } from '../contexts/AuthContext'
import { apiJson } from '../utils/api'
import { DesmosCalculator } from '../components/DesmosCalculator'
import styles from './page.module.css'

type Tool = 'lab_values' | 'calculator' | 'reference_sheet' | 'notes'

interface Question {
  id: number
  question_type: 'multiple_choice' | 'numeric_entry'
  question_text: string
  image_url: string | null
  answer_choices: { [key: string]: string }
  question_order: number
}

interface SectionSummary {
  order: number
  name: string
  question_count: number
  time_limit_minutes: number
  status: 'pending' | 'active' | 'completed'
}

interface ExamSession {
  attempt_id: number
  status: 'in_section' | 'between_sections' | 'completed'
  test: {
    id: number
    name: string
    exam: { slug: string; name: string; tools: Tool[] } | null
  }
  sections: SectionSummary[]
  current_section: {
    order: number
    name: string
    seconds_remaining: number
    questions: Question[]
    saved_answers: { [questionId: string]: string }
  } | null
  next_section: (SectionSummary & { break_seconds_remaining: number; break_kind: 'pool' | 'scheduled' }) | null
}

const TOOL_LABELS: Record<Tool, string> = {
  lab_values: 'Lab Values',
  calculator: 'Calculator',
  reference_sheet: 'Reference',
  notes: 'Notes',
}

const formatTime = (seconds: number): string => {
  const safe = Math.max(0, seconds)
  const hours = Math.floor(safe / 3600)
  const mins = Math.floor((safe % 3600) / 60)
  const secs = safe % 60
  const mm = `${mins}`.padStart(hours ? 2 : 1, '0')
  return `${hours ? `${hours}:` : ''}${mm}:${secs.toString().padStart(2, '0')}`
}

export default function ExamPage() {
  return (
    <Suspense fallback={null}>
      <ExamScreen />
    </Suspense>
  )
}

function ExamScreen() {
  const { isAuthenticated } = useAuth()
  const router = useRouter()
  const searchParams = useSearchParams()
  const testId = searchParams.get('testId')
  const userPackageId = searchParams.get('userPackageId')

  const [session, setSession] = useState<ExamSession | null>(null)
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0)
  const [answers, setAnswers] = useState<{ [questionId: number]: string }>({})
  const [markedQuestions, setMarkedQuestions] = useState<Set<number>>(new Set())
  const [timeRemaining, setTimeRemaining] = useState(0)
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [openTool, setOpenTool] = useState<Tool | null>(null)
  const [notes, setNotes] = useState('')
  const answersRef = useRef<{ [questionId: number]: string }>({})
  const timeSpentRef = useRef<{ [questionId: number]: number }>({})
  const questionEnteredAtRef = useRef<number>(Date.now())
  const numericSaveTimers = useRef<{ [questionId: number]: ReturnType<typeof setTimeout> }>({})

  const section = session?.current_section ?? null
  const questions = section?.questions ?? []
  const currentQuestion = questions[currentQuestionIndex]
  const tools = session?.test.exam?.tools ?? []

  const applySession = useCallback((next: ExamSession) => {
    if (next.status === 'completed') {
      router.push(`/results/${next.attempt_id}`)
      return
    }
    setSession(next)
    setSubmitting(false)
    if (next.status === 'in_section' && next.current_section) {
      const saved: { [questionId: number]: string } = {}
      Object.entries(next.current_section.saved_answers).forEach(([id, answer]) => {
        saved[Number(id)] = answer
      })
      setAnswers(saved)
      answersRef.current = saved
      setCurrentQuestionIndex(0)
      setMarkedQuestions(new Set())
      timeSpentRef.current = {}
      questionEnteredAtRef.current = Date.now()
      setTimeRemaining(next.current_section.seconds_remaining)
    } else if (next.next_section) {
      setTimeRemaining(next.next_section.break_seconds_remaining)
    }
  }, [router])

  const refreshSession = useCallback(async (attemptId: number) => {
    applySession(await apiJson<ExamSession>(`/api/tests/attempts/${attemptId}/session`))
  }, [applySession])

  useEffect(() => {
    if (!isAuthenticated) {
      router.push('/')
      return
    }
    if (!testId || !userPackageId) {
      router.push('/dashboard')
      return
    }

    apiJson<ExamSession>(
      `/api/tests/${testId}/start?user_package_id=${encodeURIComponent(userPackageId)}`,
      { method: 'POST' }
    )
      .then(applySession)
      .catch((err) => {
        alert(err instanceof Error ? err.message : 'Failed to load test. Please try again.')
        router.push(`/package/${userPackageId}`)
      })
      .finally(() => setLoading(false))
  }, [isAuthenticated, testId, userPackageId, router, applySession])

  const recordTimeOnCurrentQuestion = () => {
    if (!currentQuestion) return
    const now = Date.now()
    const elapsed = Math.round((now - questionEnteredAtRef.current) / 1000)
    timeSpentRef.current[currentQuestion.id] = (timeSpentRef.current[currentQuestion.id] || 0) + elapsed
    questionEnteredAtRef.current = now
  }

  const autosaveAnswer = (questionId: number, answer: string) => {
    if (!session) return
    apiJson(`/api/tests/attempts/${session.attempt_id}/answers`, {
      method: 'PUT',
      body: JSON.stringify({
        question_id: questionId,
        selected_answer: answer || null,
        time_spent_seconds: timeSpentRef.current[questionId],
      }),
    }).catch((err) => console.error('Autosave failed:', err))
  }

  const setAnswer = (questionId: number, answer: string, saveImmediately: boolean) => {
    const next = { ...answersRef.current, [questionId]: answer }
    answersRef.current = next
    setAnswers(next)
    clearTimeout(numericSaveTimers.current[questionId])
    if (saveImmediately) {
      autosaveAnswer(questionId, answer)
    } else {
      numericSaveTimers.current[questionId] = setTimeout(() => autosaveAnswer(questionId, answer), 800)
    }
  }

  const submitSection = async () => {
    if (!session || !section || submitting) return
    setSubmitting(true)
    recordTimeOnCurrentQuestion()
    const finalAnswers = answersRef.current
    try {
      const next = await apiJson<ExamSession>(
        `/api/tests/attempts/${session.attempt_id}/sections/${section.order}/submit`,
        {
          method: 'POST',
          body: JSON.stringify({
            question_attempts: questions.map((q) => ({
              question_id: q.id,
              selected_answer: finalAnswers[q.id] || null,
              time_spent_seconds: timeSpentRef.current[q.id] || 0,
            })),
          }),
        }
      )
      applySession(next)
    } catch (err) {
      console.error('Error submitting section:', err)
      try {
        await refreshSession(session.attempt_id)
      } catch {
        alert('Failed to submit. Please check your connection and try again.')
        setSubmitting(false)
      }
    }
  }

  const startNextSection = async () => {
    if (!session?.next_section || submitting) return
    setSubmitting(true)
    try {
      applySession(await apiJson<ExamSession>(
        `/api/tests/attempts/${session.attempt_id}/sections/${session.next_section.order}/start`,
        { method: 'POST' }
      ))
    } catch {
      await refreshSession(session.attempt_id).catch(() => setSubmitting(false))
    }
  }

  // One tick per second; when the section (or break) runs out, let the server decide what's next.
  useEffect(() => {
    if (!session || submitting) return
    if (timeRemaining <= 0) {
      if (session.status === 'in_section') {
        submitSection()
      } else {
        refreshSession(session.attempt_id).catch(console.error)
      }
      return
    }
    const timeout = setTimeout(() => setTimeRemaining((prev) => Math.max(0, prev - 1)), 1000)
    return () => clearTimeout(timeout)
  }, [session, submitting, timeRemaining])

  useEffect(() => {
    if (!session || session.status !== 'in_section' || submitting) return
    const handleBeforeUnload = (e: BeforeUnloadEvent) => {
      e.preventDefault()
      e.returnValue = 'Your timer keeps running if you leave. Answers are saved.'
      return e.returnValue
    }
    window.addEventListener('beforeunload', handleBeforeUnload)
    return () => window.removeEventListener('beforeunload', handleBeforeUnload)
  }, [session, submitting])

  const goToQuestion = (index: number) => {
    recordTimeOnCurrentQuestion()
    setCurrentQuestionIndex(index)
  }

  const toggleMark = () => {
    if (!currentQuestion) return
    const next = new Set(markedQuestions)
    if (next.has(currentQuestion.id)) {
      next.delete(currentQuestion.id)
    } else {
      next.add(currentQuestion.id)
    }
    setMarkedQuestions(next)
  }

  const confirmEndSection = () => {
    const isLast = session ? section?.order === session.sections.length : true
    const message = isLast
      ? 'End this section and submit the test? You will not be able to return.'
      : 'End this section? You will not be able to return to it.'
    if (confirm(message)) submitSection()
  }

  if (loading || !session) {
    return (
      <div className={styles.container}>
        <div className={styles.centerCard}><p>Loading test...</p></div>
      </div>
    )
  }

  if (session.status === 'between_sections' && session.next_section) {
    const next = session.next_section
    return (
      <div className={styles.container}>
        <div className={styles.centerCard}>
          <h2>{session.test.name}</h2>
          <p>Section complete. You are on a break.</p>
          <ul className={styles.sectionList}>
            {session.sections.map((s) => (
              <li key={s.order} className={s.status === 'completed' ? styles.sectionDone : undefined}>
                {s.name} — {s.question_count} questions, {s.time_limit_minutes} min
                {s.status === 'completed' ? ' ✓' : ''}
              </li>
            ))}
          </ul>
          <p>
            Next: <strong>{next.name}</strong> ({next.question_count} questions, {next.time_limit_minutes} minutes)
          </p>
          <p className={styles.breakTimer}>
            {next.break_kind === 'pool'
              ? `Total break time left for this test: ${formatTime(timeRemaining)}. Time you don't use now stays available for later breaks.`
              : `Break time remaining: ${formatTime(timeRemaining)}.`}{' '}
            {next.name} starts automatically when it runs out.
          </p>
          <button className={styles.proceedButton} onClick={startNextSection} disabled={submitting}>
            {submitting ? 'Starting…' : `Start ${next.name}`}
          </button>
        </div>
      </div>
    )
  }

  if (!section || !currentQuestion) {
    return (
      <div className={styles.container}>
        <div className={styles.centerCard}><p>No questions in this section.</p></div>
      </div>
    )
  }

  const isLastQuestion = currentQuestionIndex === questions.length - 1
  const answerChoices = Object.entries(currentQuestion.answer_choices).sort(([a], [b]) => a.localeCompare(b))
  const selectedAnswer = answers[currentQuestion.id] || ''

  return (
    <div className={styles.container}>
      <div className={styles.topNavBar}>
        <div className={styles.topNavLeft}>
          <span className={styles.itemInfo}>Item: {currentQuestionIndex + 1} of {questions.length}</span>
          <span className={styles.blockInfo}>
            {section.name} ({section.order} of {session.sections.length})
          </span>
          <label className={styles.markCheckbox}>
            <input type="checkbox" checked={markedQuestions.has(currentQuestion.id)} onChange={toggleMark} />
            <span>Mark</span>
          </label>
        </div>

        <div className={styles.topNavCenter}>
          <button
            onClick={() => goToQuestion(currentQuestionIndex - 1)}
            disabled={currentQuestionIndex === 0}
            className={styles.navButton}
          >
            Previous
          </button>
          <button
            onClick={() => goToQuestion(currentQuestionIndex + 1)}
            disabled={isLastQuestion}
            className={styles.navButton}
          >
            Next
          </button>
        </div>

        <div className={styles.topNavRight}>
          {tools.map((tool) => (
            <button
              key={tool}
              onClick={() => setOpenTool(openTool === tool ? null : tool)}
              className={`${styles.utilityButton} ${openTool === tool ? styles.utilityButtonActive : ''}`}
            >
              {TOOL_LABELS[tool] ?? tool}
            </button>
          ))}
        </div>
      </div>

      <div className={styles.mainContent}>
        <div className={styles.leftSidebar}>
          {questions.map((q, index) => (
            <button
              key={q.id}
              onClick={() => goToQuestion(index)}
              className={`${styles.questionNumber} ${
                index === currentQuestionIndex ? styles.questionNumberActive : ''
              } ${answers[q.id] ? styles.questionNumberAnswered : ''} ${
                markedQuestions.has(q.id) ? styles.questionNumberMarked : ''
              }`}
            >
              {index + 1}
            </button>
          ))}
        </div>

        <div className={styles.questionPanel}>
          <div className={styles.questionContent}>
            {currentQuestion.image_url && (
              // eslint-disable-next-line @next/next/no-img-element
              <img src={currentQuestion.image_url} alt="" className={styles.questionImage} />
            )}
            <div className={styles.questionText}>{currentQuestion.question_text}</div>

            {currentQuestion.question_type === 'numeric_entry' ? (
              <div className={styles.numericEntry}>
                <label htmlFor={`answer-${currentQuestion.id}`}>Your answer</label>
                <input
                  id={`answer-${currentQuestion.id}`}
                  type="text"
                  inputMode="decimal"
                  maxLength={7}
                  autoComplete="off"
                  value={selectedAnswer}
                  onChange={(e) => setAnswer(currentQuestion.id, e.target.value.replace(/[^0-9./-]/g, ''), false)}
                  className={styles.numericInput}
                />
                <p className={styles.numericHint}>Enter a whole number, decimal, or fraction (for example 12, .75, or 3/4).</p>
              </div>
            ) : (
              <div className={styles.options}>
                {answerChoices.map(([key, value]) => (
                  <label
                    key={key}
                    className={`${styles.option} ${selectedAnswer === key ? styles.optionSelected : ''}`}
                  >
                    <input
                      type="radio"
                      name={`question-${currentQuestion.id}`}
                      value={key}
                      checked={selectedAnswer === key}
                      onChange={() => setAnswer(currentQuestion.id, key, true)}
                    />
                    <span className={styles.optionLabel}>
                      <span className={styles.optionKey}>{key}.</span> {value}
                    </span>
                  </label>
                ))}
              </div>
            )}

            <div className={styles.questionActions}>
              <span />
              <button
                onClick={isLastQuestion ? confirmEndSection : () => goToQuestion(currentQuestionIndex + 1)}
                className={styles.proceedButton}
                disabled={submitting}
              >
                {submitting ? 'Submitting...' : isLastQuestion ? 'End Section' : 'Proceed to Next Item'}
              </button>
            </div>
          </div>
        </div>

        {openTool && (
          <div className={styles.rightPanel}>
            <div className={styles.rightPanelHeader}>
              <h3>{TOOL_LABELS[openTool]}</h3>
              <button onClick={() => setOpenTool(null)} className={styles.closePanelButton}>×</button>
            </div>
            <div className={styles.rightPanelContent}>
              {openTool === 'lab_values' && (
                <p className={styles.labValuesInfo}>Lab reference values will be shown here.</p>
              )}
              {openTool === 'calculator' && <DesmosCalculator />}
              {openTool === 'reference_sheet' && <ReferenceSheet />}
              {openTool === 'notes' && (
                <textarea
                  className={styles.notesArea}
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  placeholder="Scratch notes (not saved or graded)"
                />
              )}
            </div>
          </div>
        )}
      </div>

      <div className={styles.bottomBar}>
        <div className={styles.bottomBarLeft}>
          <span className={styles.timeRemaining}>Section Time Remaining: {formatTime(timeRemaining)}</span>
        </div>
        <div className={styles.bottomBarRight}>
          <button onClick={confirmEndSection} className={styles.endBlockButton} disabled={submitting}>
            End Section
          </button>
        </div>
      </div>
    </div>
  )
}

function ReferenceSheet() {
  return (
    <ul className={styles.referenceList}>
      <li>Circle: A = πr², C = 2πr</li>
      <li>Rectangle: A = ℓw</li>
      <li>Triangle: A = ½bh</li>
      <li>Pythagorean theorem: c² = a² + b²</li>
      <li>Special right triangles: 30°-60°-90° sides x, x√3, 2x; 45°-45°-90° sides s, s, s√2</li>
      <li>Rectangular prism: V = ℓwh</li>
      <li>Cylinder: V = πr²h</li>
      <li>Sphere: V = (4/3)πr³</li>
      <li>Cone: V = (1/3)πr²h</li>
      <li>Pyramid: V = (1/3)ℓwh</li>
      <li>A circle has 360° (2π radians) of arc.</li>
      <li>The angles of a triangle sum to 180°.</li>
    </ul>
  )
}
