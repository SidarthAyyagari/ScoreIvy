'use client'

import { FormEvent, KeyboardEvent, useEffect, useMemo, useState } from 'react'
import styles from './QuestionBank.module.css'
import { CHOICE_LETTERS, Question, QuestionType, useExamTags, useLookups } from '../lib/questionBank'
import { apiJson } from '../utils/api'

interface FormState {
  examId: string
  sectionId: string
  type: QuestionType
  text: string
  imageUrl: string
  choices: string[]
  correct: string
  accepted: string
  explanation: string
  difficulty: string
  tags: string[]
}

function toForm(question?: Partial<Question>, defaults: Partial<FormState> = {}): FormState {
  const choices = question?.answer_choices
    ? CHOICE_LETTERS.map((letter) => question.answer_choices?.[letter]).filter((c): c is string => c !== undefined)
    : []
  return {
    examId: question?.exam_id ? String(question.exam_id) : defaults.examId ?? '',
    sectionId: question?.section_id ? String(question.section_id) : defaults.sectionId ?? '',
    type: question?.question_type ?? defaults.type ?? 'multiple_choice',
    text: question?.question_text ?? '',
    imageUrl: question?.image_url ?? '',
    choices: choices.length >= 2 ? choices : ['', '', '', '', ''],
    correct: question?.correct_answer ?? '',
    accepted: (question?.accepted_answers ?? []).join(', '),
    explanation: question?.explanation ?? '',
    difficulty: question?.difficulty ?? 'medium',
    tags: question?.tags ?? defaults.tags ?? [],
  }
}

function toPayload(form: FormState): { payload?: Record<string, unknown>; error?: string } {
  if (!form.examId) return { error: 'Choose an exam' }
  if (!form.text.trim()) return { error: 'Question text is required' }

  let answerChoices: Record<string, string> = {}
  let accepted: string[] | null = null
  const correct = form.correct.trim()
  if (form.type === 'multiple_choice') {
    const blank = form.choices.findIndex((c) => !c.trim())
    if (blank !== -1) return { error: `Choice ${CHOICE_LETTERS[blank]} is empty. Fill it in or remove it.` }
    answerChoices = Object.fromEntries(form.choices.map((c, i) => [CHOICE_LETTERS[i], c.trim()]))
    if (!answerChoices[correct]) return { error: 'Mark which choice is correct' }
  } else {
    if (!correct) return { error: 'Enter the correct numeric answer' }
    const extra = form.accepted.split(/[,;]/).map((a) => a.trim()).filter(Boolean)
    accepted = extra.length ? extra : null
  }

  return {
    payload: {
      exam_id: Number(form.examId),
      section_id: form.sectionId ? Number(form.sectionId) : null,
      question_type: form.type,
      question_text: form.text.trim(),
      image_url: form.imageUrl.trim() || null,
      answer_choices: answerChoices,
      correct_answer: correct,
      accepted_answers: accepted,
      explanation: form.explanation.trim() || null,
      difficulty: form.difficulty,
      tags: form.tags,
    },
  }
}

interface Props {
  question?: Question
  defaultExamId?: string
  onSaved: (question: Question, addAnother: boolean) => void
}

export function QuestionEditor({ question, defaultExamId, onSaved }: Props) {
  const { exams, sections } = useLookups()
  const [form, setForm] = useState<FormState>(() => toForm(question, { examId: defaultExamId }))
  const [saved, setSaved] = useState<FormState>(form)
  const [tagDraft, setTagDraft] = useState('')
  const [error, setError] = useState('')
  const [saving, setSaving] = useState(false)
  const examTags = useExamTags(form.examId ? Number(form.examId) : null)

  useEffect(() => {
    const next = toForm(question, { examId: defaultExamId })
    setForm(next)
    setSaved(next)
  }, [question, defaultExamId])

  const dirty = useMemo(() => JSON.stringify(form) !== JSON.stringify(saved), [form, saved])

  useEffect(() => {
    if (!dirty) return
    const warn = (e: BeforeUnloadEvent) => {
      e.preventDefault()
      e.returnValue = ''
    }
    window.addEventListener('beforeunload', warn)
    return () => window.removeEventListener('beforeunload', warn)
  }, [dirty])

  const set = <K extends keyof FormState>(key: K, value: FormState[K]) =>
    setForm((prev) => ({ ...prev, [key]: value }))

  const examSections = sections.filter((s) => s.exam_id === Number(form.examId))

  const setChoice = (index: number, value: string) =>
    set('choices', form.choices.map((c, i) => (i === index ? value : c)))

  const removeChoice = (index: number) => {
    const removedLetter = CHOICE_LETTERS[index]
    const choices = form.choices.filter((_, i) => i !== index)
    let correct = form.correct
    if (correct === removedLetter) correct = ''
    else if (correct && CHOICE_LETTERS.indexOf(correct) > index) correct = CHOICE_LETTERS[CHOICE_LETTERS.indexOf(correct) - 1]
    setForm((prev) => ({ ...prev, choices, correct }))
  }

  const switchType = (type: QuestionType) => {
    if (type === form.type) return
    setForm((prev) => ({ ...prev, type, correct: '', accepted: '' }))
  }

  const addTag = (raw: string) => {
    const value = raw.trim().replace(/\s*:\s*/, ':')
    if (!value) return
    if (!/^[^:]+:[^:]+$/.test(value)) {
      setError('Tags look like category:name, for example system:Cardiovascular')
      return
    }
    if (!form.tags.includes(value)) set('tags', [...form.tags, value])
    setTagDraft('')
    setError('')
  }

  const onTagKey = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' || e.key === ',') {
      e.preventDefault()
      addTag(tagDraft)
    } else if (e.key === 'Backspace' && !tagDraft && form.tags.length) {
      set('tags', form.tags.slice(0, -1))
    }
  }

  const submit = async (addAnother: boolean) => {
    const { payload, error: formError } = toPayload(form)
    if (!payload) {
      setError(formError || 'Check the form')
      return
    }
    setSaving(true)
    setError('')
    try {
      const result = question
        ? await apiJson<Question>(`/api/questions/${question.id}`, { method: 'PUT', body: JSON.stringify(payload) })
        : await apiJson<Question>('/api/questions/', { method: 'POST', body: JSON.stringify(payload) })
      setSaved(form)
      onSaved(result, addAnother)
      if (addAnother) {
        const next = toForm(undefined, {
          examId: form.examId, sectionId: form.sectionId, type: form.type, tags: form.tags,
        })
        setForm(next)
        setSaved(next)
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Save failed')
    } finally {
      setSaving(false)
    }
  }

  const onSubmit = (e: FormEvent) => {
    e.preventDefault()
    submit(false)
  }

  return (
    <form onSubmit={onSubmit}>
      {error && <div className={styles.errorBanner}>{error}</div>}

      <div className={styles.card}>
        <div className={styles.row}>
          <label className={styles.field}>
            <span>Exam *</span>
            <select
              value={form.examId}
              onChange={(e) => setForm((prev) => ({ ...prev, examId: e.target.value, sectionId: '' }))}
              required
            >
              <option value="">Choose…</option>
              {exams.map((exam) => (
                <option key={exam.id} value={exam.id}>
                  {exam.name}
                </option>
              ))}
            </select>
          </label>
          <label className={styles.field}>
            <span>Section</span>
            <select value={form.sectionId} onChange={(e) => set('sectionId', e.target.value)}>
              <option value="">None</option>
              {examSections.map((section) => (
                <option key={section.id} value={section.id}>
                  {section.name}
                </option>
              ))}
            </select>
          </label>
          <label className={styles.field}>
            <span>Difficulty</span>
            <select value={form.difficulty} onChange={(e) => set('difficulty', e.target.value)}>
              <option value="easy">Easy</option>
              <option value="medium">Medium</option>
              <option value="hard">Hard</option>
            </select>
          </label>
        </div>

        <div className={styles.typeToggle} role="tablist" aria-label="Question type">
          <button
            type="button"
            className={form.type === 'multiple_choice' ? styles.tabActive : undefined}
            onClick={() => switchType('multiple_choice')}
          >
            Multiple choice
          </button>
          <button
            type="button"
            className={form.type === 'numeric_entry' ? styles.tabActive : undefined}
            onClick={() => switchType('numeric_entry')}
          >
            Numeric entry
          </button>
        </div>

        <label className={styles.field}>
          <span>Question *</span>
          <textarea rows={8} value={form.text} onChange={(e) => set('text', e.target.value)} required />
        </label>

        <label className={styles.field}>
          <span>
            Image URL <span className={styles.hint}>(optional; for figures, ECGs, images)</span>
          </span>
          <input type="url" value={form.imageUrl} onChange={(e) => set('imageUrl', e.target.value)} />
          {/* eslint-disable-next-line @next/next/no-img-element */}
          {form.imageUrl.trim() && <img src={form.imageUrl} alt="Question figure preview" className={styles.imagePreview} />}
        </label>
      </div>

      <div className={styles.card}>
        {form.type === 'multiple_choice' ? (
          <>
            <h2>Answer choices</h2>
            <p className={styles.muted}>Select the circle next to the correct answer.</p>
            {form.choices.map((choice, index) => {
              const letter = CHOICE_LETTERS[index]
              return (
                <div
                  key={letter}
                  className={`${styles.choiceRow} ${form.correct === letter ? styles.choiceCorrect : ''}`}
                >
                  <span className={styles.choiceLetter}>{letter}</span>
                  <input
                    type="radio"
                    name="correct"
                    checked={form.correct === letter}
                    onChange={() => set('correct', letter)}
                    aria-label={`${letter} is correct`}
                  />
                  <input
                    type="text"
                    value={choice}
                    onChange={(e) => setChoice(index, e.target.value)}
                    placeholder={`Choice ${letter}`}
                  />
                  <button
                    type="button"
                    className={styles.iconBtn}
                    onClick={() => removeChoice(index)}
                    disabled={form.choices.length <= 2}
                    aria-label={`Remove choice ${letter}`}
                  >
                    ×
                  </button>
                </div>
              )
            })}
            {form.choices.length < CHOICE_LETTERS.length && (
              <button type="button" className={styles.secondaryBtn} onClick={() => set('choices', [...form.choices, ''])}>
                + Add choice
              </button>
            )}
          </>
        ) : (
          <>
            <h2>Answer</h2>
            <div className={styles.row}>
              <label className={styles.field}>
                <span>Correct answer *</span>
                <input
                  type="text"
                  value={form.correct}
                  onChange={(e) => set('correct', e.target.value)}
                  placeholder="e.g. 3/4 or 0.75 or -2"
                />
              </label>
              <label className={styles.field} style={{ gridColumn: 'span 2' }}>
                <span>
                  Other accepted forms <span className={styles.hint}>(comma-separated)</span>
                </span>
                <input
                  type="text"
                  value={form.accepted}
                  onChange={(e) => set('accepted', e.target.value)}
                  placeholder=".75, .7500"
                />
              </label>
            </div>
            <p className={styles.muted}>
              Equivalent values are matched exactly, so 3/4 already accepts .75 and 0.75.
            </p>
          </>
        )}
      </div>

      <div className={styles.card}>
        <label className={styles.field}>
          <span>Explanation</span>
          <textarea rows={6} value={form.explanation} onChange={(e) => set('explanation', e.target.value)} />
        </label>

        <div className={styles.field}>
          <span>
            Tags <span className={styles.hint}>(category:name, press Enter to add)</span>
          </span>
          <div className={styles.tagInput}>
            {form.tags.map((tag) => (
              <span key={tag} className={styles.tagChip}>
                {tag}
                <button type="button" onClick={() => set('tags', form.tags.filter((t) => t !== tag))} aria-label={`Remove ${tag}`}>
                  ×
                </button>
              </span>
            ))}
            <input
              list="exam-tags"
              value={tagDraft}
              onChange={(e) => setTagDraft(e.target.value)}
              onKeyDown={onTagKey}
              onBlur={() => tagDraft && addTag(tagDraft)}
              placeholder="system:Cardiovascular"
            />
            <datalist id="exam-tags">
              {examTags.map((tag) => (
                <option key={tag.id} value={`${tag.category}:${tag.name}`} />
              ))}
            </datalist>
          </div>
        </div>

        <div className={styles.formActions}>
          <button type="submit" className={styles.primaryBtn} disabled={saving}>
            {saving ? 'Saving…' : question ? 'Save changes' : 'Save'}
          </button>
          {!question && (
            <button type="button" className={styles.secondaryBtn} disabled={saving} onClick={() => submit(true)}>
              Save and add another
            </button>
          )}
          {dirty && <span className={styles.muted}>Unsaved changes</span>}
        </div>
      </div>
    </form>
  )
}
