'use client'

import { FormEvent, useEffect, useState } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { useAuth } from '../../../contexts/AuthContext'
import { apiJson } from '../../../utils/api'
import styles from './page.module.css'

interface Section {
  id: number
  name: string
  description: string | null
}

interface AnswerChoiceRow {
  key: string
  text: string
}

interface QuestionCreatePayload {
  section_id?: number
  question_text: string
  image_url?: string
  answer_choices: Record<string, string>
  correct_answer: string
  explanation?: string
  difficulty: string
}

interface QuestionResponse {
  id: number
  question_text: string
  correct_answer: string
  difficulty: string
}

const DIFFICULTY_OPTIONS = ['easy', 'medium', 'hard'] as const
const DEFAULT_CHOICE_KEYS = ['A', 'B', 'C', 'D']

function nextChoiceKey(existingKeys: string[]): string {
  const alphabet = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
  for (const letter of alphabet) {
    if (!existingKeys.includes(letter)) {
      return letter
    }
  }
  return `Choice${existingKeys.length + 1}`
}

function buildInitialChoices(): AnswerChoiceRow[] {
  return DEFAULT_CHOICE_KEYS.map((key) => ({ key, text: '' }))
}

export default function AdminCreateQuestionPage() {
  const { isAuthenticated } = useAuth()
  const router = useRouter()

  const [sections, setSections] = useState<Section[]>([])
  const [loadingSections, setLoadingSections] = useState(true)

  const [sectionId, setSectionId] = useState('')
  const [questionText, setQuestionText] = useState('')
  const [imageUrl, setImageUrl] = useState('')
  const [explanation, setExplanation] = useState('')
  const [difficulty, setDifficulty] = useState<string>('medium')
  const [choices, setChoices] = useState<AnswerChoiceRow[]>(buildInitialChoices)
  const [correctAnswer, setCorrectAnswer] = useState('')

  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({})
  const [submitError, setSubmitError] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [createdQuestion, setCreatedQuestion] = useState<QuestionResponse | null>(null)

  useEffect(() => {
    if (!isAuthenticated) {
      router.push('/')
      return
    }

    const loadSections = async () => {
      try {
        setLoadingSections(true)
        const data = await apiJson<Section[]>('/api/sections/')
        setSections(data)
      } catch (err) {
        console.error('Failed to load sections:', err)
      } finally {
        setLoadingSections(false)
      }
    }

    loadSections()
  }, [isAuthenticated, router])

  const resetForm = () => {
    setSectionId('')
    setQuestionText('')
    setImageUrl('')
    setExplanation('')
    setDifficulty('medium')
    setChoices(buildInitialChoices())
    setCorrectAnswer('')
    setFieldErrors({})
    setSubmitError('')
    setCreatedQuestion(null)
  }

  const validateForm = (): boolean => {
    const errors: Record<string, string> = {}
    const trimmedQuestion = questionText.trim()

    if (!trimmedQuestion) {
      errors.questionText = 'Question text is required.'
    }

    const filledChoices = choices.filter((c) => c.text.trim())
    if (filledChoices.length < 2) {
      errors.choices = 'At least two answer choices with text are required.'
    }

    const duplicateKeys = choices
      .map((c) => c.key.trim().toUpperCase())
      .filter((key, index, arr) => key && arr.indexOf(key) !== index)
    if (duplicateKeys.length > 0) {
      errors.choices = 'Answer choice keys must be unique.'
    }

    const emptyKey = choices.find((c) => !c.key.trim())
    if (emptyKey) {
      errors.choices = 'Each answer choice needs a key (A, B, C, …).'
    }

    if (!correctAnswer) {
      errors.correctAnswer = 'Select the correct answer.'
    } else if (!filledChoices.some((c) => c.key === correctAnswer)) {
      errors.correctAnswer = 'Correct answer must match a filled choice.'
    }

    if (imageUrl.trim()) {
      try {
        new URL(imageUrl.trim())
      } catch {
        errors.imageUrl = 'Enter a valid image URL or leave blank.'
      }
    }

    setFieldErrors(errors)
    return Object.keys(errors).length === 0
  }

  const handleAddChoice = () => {
    const existingKeys = choices.map((c) => c.key)
    const newKey = nextChoiceKey(existingKeys)
    setChoices([...choices, { key: newKey, text: '' }])
  }

  const handleRemoveChoice = (index: number) => {
    if (choices.length <= 2) return
    const removed = choices[index]
    const nextChoices = choices.filter((_, i) => i !== index)
    setChoices(nextChoices)
    if (correctAnswer === removed.key) {
      setCorrectAnswer('')
    }
  }

  const handleChoiceKeyChange = (index: number, newKey: string) => {
    const normalized = newKey.trim().toUpperCase().slice(0, 1)
    const previousKey = choices[index].key
    const updated = choices.map((choice, i) =>
      i === index ? { ...choice, key: normalized || choice.key } : choice
    )
    setChoices(updated)
    if (correctAnswer === previousKey) {
      setCorrectAnswer(normalized || previousKey)
    }
  }

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault()
    setSubmitError('')
    setCreatedQuestion(null)

    if (!validateForm()) {
      return
    }

    const answer_choices: Record<string, string> = {}
    for (const choice of choices) {
      const text = choice.text.trim()
      if (text) {
        answer_choices[choice.key] = text
      }
    }

    const payload: QuestionCreatePayload = {
      question_text: questionText.trim(),
      answer_choices,
      correct_answer: correctAnswer,
      difficulty,
    }

    if (sectionId) {
      payload.section_id = Number(sectionId)
    }
    if (imageUrl.trim()) {
      payload.image_url = imageUrl.trim()
    }
    if (explanation.trim()) {
      payload.explanation = explanation.trim()
    }

    try {
      setSubmitting(true)
      const created = await apiJson<QuestionResponse>('/api/questions/', {
        method: 'POST',
        body: JSON.stringify(payload),
      })
      setCreatedQuestion(created)
      window.scrollTo({ top: 0, behavior: 'smooth' })
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Failed to create question'
      setSubmitError(message)
    } finally {
      setSubmitting(false)
    }
  }

  const filledChoiceKeys = choices
    .filter((c) => c.text.trim())
    .map((c) => c.key)

  if (!isAuthenticated) {
    return null
  }

  return (
    <div className={styles.container}>
      <div className={styles.card}>
        <header className={styles.header}>
          <div>
            <h1 className={styles.title}>Create Question</h1>
            <p className={styles.subtitle}>Add a new question to the question bank</p>
          </div>
          <Link href="/dashboard" className={styles.backLink}>
            Back to Dashboard
          </Link>
        </header>

        {createdQuestion && (
          <div className={styles.successBanner} role="status">
            Question #{createdQuestion.id} created successfully.
            <div className={styles.successActions}>
              <button type="button" className={styles.submitButton} onClick={resetForm}>
                Create Another
              </button>
            </div>
          </div>
        )}

        {submitError && (
          <div className={styles.errorBanner} role="alert">
            {submitError}
          </div>
        )}

        <form className={styles.form} onSubmit={handleSubmit} noValidate>
          <div className={styles.fieldGroup}>
            <label htmlFor="section" className={styles.label}>
              Section (optional)
            </label>
            <select
              id="section"
              className={styles.select}
              value={sectionId}
              onChange={(e) => setSectionId(e.target.value)}
              disabled={loadingSections}
            >
              <option value="">No section</option>
              {sections.map((section) => (
                <option key={section.id} value={section.id}>
                  {section.name}
                </option>
              ))}
            </select>
            {loadingSections && (
              <span className={styles.hint}>Loading sections…</span>
            )}
          </div>

          <div className={styles.fieldGroup}>
            <label htmlFor="questionText" className={styles.label}>
              Question text *
            </label>
            <textarea
              id="questionText"
              className={`${styles.textarea} ${fieldErrors.questionText ? styles.inputError : ''}`}
              value={questionText}
              onChange={(e) => setQuestionText(e.target.value)}
              placeholder="Enter the question stem…"
              required
            />
            {fieldErrors.questionText && (
              <span className={styles.fieldError}>{fieldErrors.questionText}</span>
            )}
          </div>

          <div className={styles.fieldGroup}>
            <label htmlFor="imageUrl" className={styles.label}>
              Image URL (optional)
            </label>
            <input
              id="imageUrl"
              type="url"
              className={`${styles.input} ${fieldErrors.imageUrl ? styles.inputError : ''}`}
              value={imageUrl}
              onChange={(e) => setImageUrl(e.target.value)}
              placeholder="https://example.com/image.png"
            />
            {fieldErrors.imageUrl && (
              <span className={styles.fieldError}>{fieldErrors.imageUrl}</span>
            )}
          </div>

          <section className={styles.choicesSection} aria-labelledby="choices-heading">
            <div className={styles.choicesHeader}>
              <h2 id="choices-heading" className={styles.choicesTitle}>
                Answer choices *
              </h2>
              <button
                type="button"
                className={styles.addChoiceButton}
                onClick={handleAddChoice}
              >
                + Add choice
              </button>
            </div>

            {choices.map((choice, index) => (
              <div key={`${choice.key}-${index}`} className={styles.choiceRow}>
                <input
                  type="text"
                  className={styles.choiceKeyInput}
                  value={choice.key}
                  onChange={(e) => handleChoiceKeyChange(index, e.target.value)}
                  maxLength={1}
                  aria-label={`Choice ${choice.key} key`}
                />
                <input
                  type="text"
                  className={`${styles.input} ${styles.choiceInput}`}
                  value={choice.text}
                  onChange={(e) => {
                    const updated = [...choices]
                    updated[index] = { ...choice, text: e.target.value }
                    setChoices(updated)
                  }}
                  placeholder={`Choice ${choice.key} text`}
                  aria-label={`Choice ${choice.key} text`}
                />
                <button
                  type="button"
                  className={styles.removeChoiceButton}
                  onClick={() => handleRemoveChoice(index)}
                  disabled={choices.length <= 2}
                  aria-label={`Remove choice ${choice.key}`}
                >
                  Remove
                </button>
              </div>
            ))}

            {fieldErrors.choices && (
              <span className={styles.fieldError}>{fieldErrors.choices}</span>
            )}
          </section>

          <div className={styles.fieldGroup}>
            <label htmlFor="correctAnswer" className={styles.label}>
              Correct answer *
            </label>
            <select
              id="correctAnswer"
              className={`${styles.select} ${fieldErrors.correctAnswer ? styles.inputError : ''}`}
              value={correctAnswer}
              onChange={(e) => setCorrectAnswer(e.target.value)}
              required
            >
              <option value="">Select correct answer</option>
              {filledChoiceKeys.map((key) => (
                <option key={key} value={key}>
                  {key}
                </option>
              ))}
            </select>
            {fieldErrors.correctAnswer && (
              <span className={styles.fieldError}>{fieldErrors.correctAnswer}</span>
            )}
          </div>

          <div className={styles.fieldGroup}>
            <label htmlFor="explanation" className={styles.label}>
              Explanation (optional)
            </label>
            <textarea
              id="explanation"
              className={styles.textarea}
              value={explanation}
              onChange={(e) => setExplanation(e.target.value)}
              placeholder="Explain why the correct answer is right…"
            />
          </div>

          <div className={styles.fieldGroup}>
            <label htmlFor="difficulty" className={styles.label}>
              Difficulty
            </label>
            <select
              id="difficulty"
              className={styles.select}
              value={difficulty}
              onChange={(e) => setDifficulty(e.target.value)}
            >
              {DIFFICULTY_OPTIONS.map((level) => (
                <option key={level} value={level}>
                  {level.charAt(0).toUpperCase() + level.slice(1)}
                </option>
              ))}
            </select>
          </div>

          <div className={styles.formActions}>
            <button
              type="submit"
              className={styles.submitButton}
              disabled={submitting}
            >
              {submitting ? 'Creating…' : 'Create Question'}
            </button>
            <button
              type="button"
              className={styles.resetButton}
              onClick={resetForm}
              disabled={submitting}
            >
              Reset
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
