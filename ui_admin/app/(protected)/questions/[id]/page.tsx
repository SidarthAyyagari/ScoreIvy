'use client'

import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { useCallback, useEffect, useState } from 'react'
import styles from '../../../components/QuestionBank.module.css'
import { QuestionEditor } from '../../../components/QuestionEditor'
import { formatDateTime, Question, QuestionDetail, QuestionRevision } from '../../../lib/questionBank'
import { apiJson } from '../../../utils/api'

const FIELD_LABELS: Record<string, string> = {
  exam_id: 'exam',
  section_id: 'section',
  question_type: 'type',
  question_text: 'question text',
  image_url: 'image',
  answer_choices: 'choices',
  correct_answer: 'correct answer',
  accepted_answers: 'accepted answers',
  explanation: 'explanation',
  difficulty: 'difficulty',
  tags: 'tags',
  is_active: 'status',
}

function changedFields(revision: QuestionRevision, previous?: QuestionRevision): string {
  if (!previous) return ''
  const before = previous.snapshot as Record<string, unknown>
  const after = revision.snapshot as Record<string, unknown>
  const changed = Object.keys(FIELD_LABELS).filter(
    (key) => JSON.stringify(before[key] ?? null) !== JSON.stringify(after[key] ?? null)
  )
  return changed.length ? `Changed ${changed.map((key) => FIELD_LABELS[key]).join(', ')}` : 'No content changes'
}

export default function EditQuestionPage({ params }: { params: { id: string } }) {
  const router = useRouter()
  const questionId = Number(params.id)
  const [question, setQuestion] = useState<QuestionDetail | null>(null)
  const [history, setHistory] = useState<QuestionRevision[]>([])
  const [notice, setNotice] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  const loadHistory = useCallback(async () => {
    setHistory(await apiJson<QuestionRevision[]>(`/api/questions/${questionId}/history`))
  }, [questionId])

  useEffect(() => {
    apiJson<QuestionDetail>(`/api/questions/${questionId}`)
      .then(setQuestion)
      .catch((err) => setError(err instanceof Error ? err.message : 'Question not found'))
    loadHistory().catch(() => {})
  }, [questionId, loadHistory])

  const refreshDetail = async (message: string) => {
    setQuestion(await apiJson<QuestionDetail>(`/api/questions/${questionId}`))
    await loadHistory()
    setNotice(message)
    setError('')
  }

  const act = async (fn: () => Promise<void>) => {
    setBusy(true)
    try {
      await fn()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Something went wrong')
    } finally {
      setBusy(false)
    }
  }

  const onSaved = (_saved: Question) => {
    act(() => refreshDetail('Saved.'))
  }

  const setArchived = (archived: boolean) =>
    act(async () => {
      await apiJson(`/api/questions/${questionId}/${archived ? 'archive' : 'restore'}`, { method: 'POST' })
      await refreshDetail(archived ? 'Archived. It will not appear in tests students start from now on.' : 'Restored.')
    })

  const remove = () => {
    if (!question) return
    const served = question.usage.attempt_count > 0
    const message = served
      ? `Students have already been served this question, so it will be archived instead of deleted: ` +
        `it disappears from tests nobody has started, and past results keep it. Continue?`
      : 'Permanently delete this question? It has never been served to a student. Its history is kept.'
    if (!confirm(message)) return
    act(async () => {
      const { result } = await apiJson<{ result: string }>(`/api/questions/${questionId}`, { method: 'DELETE' })
      if (result === 'deleted') {
        router.push('/questions')
      } else {
        await refreshDetail('Archived instead of deleted, because students have already seen it.')
      }
    })
  }

  const revert = (revision: QuestionRevision) => {
    if (!confirm(`Revert this question's content to how it was on ${formatDateTime(revision.created_at)}?`)) return
    act(async () => {
      await apiJson(`/api/questions/${questionId}/revert/${revision.id}`, { method: 'POST' })
      await refreshDetail(`Reverted to the version from ${formatDateTime(revision.created_at)}.`)
    })
  }

  if (!question) {
    return (
      <div className={styles.container}>
        {error ? (
          <>
            <div className={styles.errorBanner}>{error}</div>
            {history.length > 0 && (
              <p className={styles.muted}>
                This question was deleted. Its last saved content is in the history below.
              </p>
            )}
            <HistoryList history={history} />
            <Link href="/questions">← Question Bank</Link>
          </>
        ) : (
          <p className={styles.muted}>Loading…</p>
        )}
      </div>
    )
  }

  return (
    <div className={styles.container}>
      <header className={styles.header}>
        <div>
          <h1 className={styles.title}>
            Question #{question.id}{' '}
            {question.is_active ? (
              <span className={styles.badge}>Active</span>
            ) : (
              <span className={styles.badgeArchived}>Archived</span>
            )}
          </h1>
          <p className={styles.subtitle}>
            <Link href="/questions">← Question Bank</Link>
          </p>
        </div>
      </header>

      {notice && <div className={styles.successBanner}>{notice}</div>}
      {error && <div className={styles.errorBanner}>{error}</div>}
      {!question.is_active && (
        <div className={styles.infoBanner}>
          This question is archived. It is not served in tests that students start, but past results still show it.
        </div>
      )}

      <div className={styles.editorLayout}>
        <QuestionEditor question={question} onSaved={onSaved} />

        <aside>
          <div className={styles.card}>
            <h2>Usage</h2>
            {question.usage.tests.length === 0 ? (
              <p className={styles.muted}>Not in any test yet.</p>
            ) : (
              <p className={styles.muted}>In {question.usage.tests.map((t) => t.name).join(', ')}.</p>
            )}
            <p className={styles.muted}>
              {question.usage.attempt_count
                ? `Served to ${question.usage.attempt_count} attempt${question.usage.attempt_count === 1 ? '' : 's'}. Edits change what future students see and how results display.`
                : 'No student has seen it yet.'}
            </p>
            <div className={styles.formActions}>
              {question.is_active ? (
                <button type="button" className={styles.secondaryBtn} disabled={busy} onClick={() => setArchived(true)}>
                  Archive
                </button>
              ) : (
                <button type="button" className={styles.secondaryBtn} disabled={busy} onClick={() => setArchived(false)}>
                  Restore
                </button>
              )}
              <button type="button" className={styles.dangerBtn} disabled={busy} onClick={remove}>
                Delete
              </button>
            </div>
          </div>

          <div className={styles.card}>
            <h2>History</h2>
            <HistoryList history={history} onRevert={busy ? undefined : revert} />
          </div>
        </aside>
      </div>
    </div>
  )
}

function HistoryList({
  history,
  onRevert,
}: {
  history: QuestionRevision[]
  onRevert?: (revision: QuestionRevision) => void
}) {
  if (history.length === 0) return <p className={styles.muted}>No history yet.</p>
  return (
    <ul className={styles.historyList}>
      {history.map((revision, index) => (
        <li key={revision.id}>
          <div className={styles.historyAction}>{revision.action}</div>
          <div className={styles.historyMeta}>
            {formatDateTime(revision.created_at)} · {revision.changed_by_email || 'unknown'}
          </div>
          <div className={styles.historyChanges}>
            {revision.note || changedFields(revision, history[index + 1])}
          </div>
          {onRevert && index > 0 && revision.action !== 'deleted' && (
            <button type="button" className={styles.linkBtn} onClick={() => onRevert(revision)}>
              Revert to this version
            </button>
          )}
        </li>
      ))}
    </ul>
  )
}
