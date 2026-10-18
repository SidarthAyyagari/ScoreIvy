'use client'

import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { useCallback, useEffect, useState } from 'react'
import styles from '../../components/QuestionBank.module.css'
import { Question, useLookups } from '../../lib/questionBank'
import { apiDownload, apiJson } from '../../utils/api'

const PAGE_SIZE = 50
const EXAM_KEY = 'question_bank_exam'

type Status = 'active' | 'archived' | 'all'

export default function QuestionListPage() {
  const router = useRouter()
  const { exams, sections, error: lookupError } = useLookups()
  const [examId, setExamId] = useState<string>('')
  const [sectionId, setSectionId] = useState('')
  const [status, setStatus] = useState<Status>('active')
  const [search, setSearch] = useState('')
  const [query, setQuery] = useState('')
  const [tag, setTag] = useState('')
  const [page, setPage] = useState(0)
  const [items, setItems] = useState<Question[]>([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    setExamId(localStorage.getItem(EXAM_KEY) || '')
  }, [])

  useEffect(() => {
    const timer = setTimeout(() => setQuery(search), 300)
    return () => clearTimeout(timer)
  }, [search])

  useEffect(() => {
    setPage(0)
  }, [examId, sectionId, status, query, tag])

  const load = useCallback(async () => {
    const params = new URLSearchParams({ status, skip: String(page * PAGE_SIZE), limit: String(PAGE_SIZE) })
    if (examId) params.set('exam_id', examId)
    if (sectionId) params.set('section_id', sectionId)
    if (query.trim()) params.set('q', query.trim())
    if (tag.includes(':')) params.set('tag', tag.trim())
    setLoading(true)
    try {
      const data = await apiJson<{ items: Question[]; total: number }>(`/api/questions/?${params}`)
      setItems(data.items)
      setTotal(data.total)
      setError('')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load questions')
    } finally {
      setLoading(false)
    }
  }, [examId, sectionId, status, query, tag, page])

  useEffect(() => {
    load()
  }, [load])

  const chooseExam = (value: string) => {
    setExamId(value)
    setSectionId('')
    localStorage.setItem(EXAM_KEY, value)
  }

  const exportCsv = async () => {
    const params = new URLSearchParams({ status: 'all' })
    if (examId) params.set('exam_id', examId)
    try {
      await apiDownload(`/api/questions/export?${params}`, 'questions.csv')
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Export failed')
    }
  }

  const examName = (id: number | null) => exams.find((e) => e.id === id)?.name ?? '—'
  const sectionName = (id: number | null) => sections.find((s) => s.id === id)?.name ?? '—'
  const examSections = sections.filter((s) => !examId || s.exam_id === Number(examId))
  const lastPage = Math.max(0, Math.ceil(total / PAGE_SIZE) - 1)

  return (
    <div className={styles.container}>
      <header className={styles.header}>
        <div>
          <h1 className={styles.title}>Question Bank</h1>
          <p className={styles.subtitle}>
            Every change is saved in the question&apos;s history and can be reverted.
          </p>
        </div>
        <div className={styles.headerActions}>
          <button type="button" className={styles.secondaryBtn} onClick={exportCsv}>
            Export CSV
          </button>
          <Link href="/questions/import" className={styles.secondaryBtn}>
            Import CSV
          </Link>
          <Link href={examId ? `/questions/new?exam=${examId}` : '/questions/new'} className={styles.primaryBtn}>
            + New question
          </Link>
        </div>
      </header>

      {(error || lookupError) && <div className={styles.errorBanner}>{error || lookupError}</div>}

      <div className={styles.filters}>
        <select value={examId} onChange={(e) => chooseExam(e.target.value)} aria-label="Exam">
          <option value="">All exams</option>
          {exams.map((exam) => (
            <option key={exam.id} value={exam.id}>
              {exam.name}
            </option>
          ))}
        </select>
        <select value={sectionId} onChange={(e) => setSectionId(e.target.value)} aria-label="Section">
          <option value="">All sections</option>
          {examSections.map((section) => (
            <option key={section.id} value={section.id}>
              {section.name}
            </option>
          ))}
        </select>
        <input
          type="search"
          placeholder="Search question text or explanation, or enter an ID"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
        <input
          type="text"
          placeholder="Tag (category:name)"
          value={tag}
          onChange={(e) => setTag(e.target.value)}
        />
        <div className={styles.statusTabs} role="tablist">
          {(['active', 'archived', 'all'] as Status[]).map((value) => (
            <button
              key={value}
              type="button"
              className={status === value ? styles.tabActive : undefined}
              onClick={() => setStatus(value)}
            >
              {value === 'active' ? 'Active' : value === 'archived' ? 'Archived' : 'All'}
            </button>
          ))}
        </div>
      </div>

      <div className={styles.tableWrap}>
        <table className={styles.table}>
          <thead>
            <tr>
              <th>ID</th>
              <th>Question</th>
              <th>Exam</th>
              <th>Section</th>
              <th>Type</th>
              <th>Tags</th>
            </tr>
          </thead>
          <tbody>
            {loading && items.length === 0 ? (
              <tr>
                <td colSpan={6} className={styles.empty}>
                  Loading…
                </td>
              </tr>
            ) : items.length === 0 ? (
              <tr>
                <td colSpan={6} className={styles.empty}>
                  No questions match these filters.
                </td>
              </tr>
            ) : (
              items.map((question) => (
                <tr
                  key={question.id}
                  className={styles.clickRow}
                  onClick={() => router.push(`/questions/${question.id}`)}
                >
                  <td>{question.id}</td>
                  <td className={styles.stem}>
                    {!question.is_active && <span className={styles.badgeArchived}>Archived</span>}
                    {question.question_text}
                  </td>
                  <td>{examName(question.exam_id)}</td>
                  <td>{sectionName(question.section_id)}</td>
                  <td>{question.question_type === 'numeric_entry' ? 'Numeric' : 'Multiple choice'}</td>
                  <td>
                    {question.tags.map((t) => (
                      <span key={t} className={styles.tagChip}>
                        {t}
                      </span>
                    ))}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      <div className={styles.pager}>
        <span>
          {total === 0
            ? '0 questions'
            : `${page * PAGE_SIZE + 1}–${Math.min(total, (page + 1) * PAGE_SIZE)} of ${total} questions`}
        </span>
        <div>
          <button type="button" className={styles.secondaryBtn} disabled={page === 0} onClick={() => setPage(page - 1)}>
            Previous
          </button>
          <button
            type="button"
            className={styles.secondaryBtn}
            disabled={page >= lastPage}
            onClick={() => setPage(page + 1)}
          >
            Next
          </button>
        </div>
      </div>
    </div>
  )
}
