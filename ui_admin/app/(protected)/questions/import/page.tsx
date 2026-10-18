'use client'

import Link from 'next/link'
import { FormEvent, useState } from 'react'
import styles from '../../../components/QuestionBank.module.css'
import { useLookups } from '../../../lib/questionBank'
import { ApiError, apiJson } from '../../../utils/api'

interface RowError {
  row: number
  message: string
  column?: string
}

const TEMPLATE_HEADER =
  'exam,section_id,question_type,question_text,choice_a,choice_b,choice_c,choice_d,choice_e,' +
  'correct_answer,accepted_answers,tags,image_url,explanation,difficulty\n'
const TEMPLATE_ROWS =
  'usmle-step-1,,multiple_choice,"A 45-year-old man presents with...",Option A,Option B,Option C,Option D,Option E,' +
  'C,,system:Cardiovascular;discipline:Physiology,,"Explanation of why C is correct",medium\n' +
  'sat,,numeric_entry,"If 4x = 3, what is x?",,,,,,3/4,.75,domain:Algebra,,"Divide both sides by 4",easy\n'

function downloadTemplate() {
  const url = URL.createObjectURL(new Blob([TEMPLATE_HEADER + TEMPLATE_ROWS], { type: 'text/csv' }))
  const link = document.createElement('a')
  link.href = url
  link.download = 'scoreivy-questions-template.csv'
  link.click()
  URL.revokeObjectURL(url)
}

export default function ImportQuestionsPage() {
  const { exams } = useLookups()
  const [examId, setExamId] = useState('')
  const [file, setFile] = useState<File | null>(null)
  const [uploading, setUploading] = useState(false)
  const [rowErrors, setRowErrors] = useState<RowError[]>([])
  const [error, setError] = useState('')
  const [imported, setImported] = useState<number | null>(null)

  const onSubmit = async (e: FormEvent) => {
    e.preventDefault()
    if (!file) return
    setUploading(true)
    setRowErrors([])
    setError('')
    setImported(null)
    const body = new FormData()
    body.append('file', file)
    try {
      const query = examId ? `?exam_id=${examId}` : ''
      const result = await apiJson<{ imported_count: number }>(`/api/questions/upload-csv${query}`, {
        method: 'POST',
        body,
      })
      setImported(result.imported_count)
    } catch (err) {
      const errors = err instanceof ApiError ? (err.body as { errors?: RowError[] })?.errors : undefined
      if (errors?.length) setRowErrors(errors)
      else setError(err instanceof Error ? err.message : 'Upload failed')
    } finally {
      setUploading(false)
    }
  }

  return (
    <div className={styles.container}>
      <header className={styles.header}>
        <div>
          <h1 className={styles.title}>Import questions from CSV</h1>
          <p className={styles.subtitle}>
            <Link href="/questions">← Question Bank</Link>
          </p>
        </div>
        <button type="button" className={styles.secondaryBtn} onClick={downloadTemplate}>
          Download template
        </button>
      </header>

      <div className={styles.card}>
        <p className={styles.muted}>
          The whole file is checked first. If any row has a problem, nothing is imported and every problem is listed
          below. Choices go in <code>choice_a</code>…<code>choice_j</code>; lists like tags are separated with{' '}
          <code>;</code>. An exported CSV can be imported again to restore questions (they are added as new questions).
        </p>
        <form onSubmit={onSubmit}>
          <div className={styles.row}>
            <label className={styles.field}>
              <span>Default exam</span>
              <select value={examId} onChange={(e) => setExamId(e.target.value)}>
                <option value="">Use the exam column</option>
                {exams.map((exam) => (
                  <option key={exam.id} value={exam.id}>
                    {exam.name}
                  </option>
                ))}
              </select>
            </label>
            <label className={styles.field} style={{ gridColumn: 'span 2' }}>
              <span>CSV file</span>
              <input type="file" accept=".csv,text/csv" onChange={(e) => setFile(e.target.files?.[0] ?? null)} />
            </label>
          </div>
          <button type="submit" className={styles.primaryBtn} disabled={!file || uploading}>
            {uploading ? 'Checking and importing…' : 'Import'}
          </button>
        </form>
      </div>

      {imported !== null && (
        <div className={styles.successBanner}>
          Imported {imported} question{imported === 1 ? '' : 's'}. <Link href="/questions">View the question bank</Link>
        </div>
      )}
      {error && <div className={styles.errorBanner}>{error}</div>}
      {rowErrors.length > 0 && (
        <>
          <div className={styles.errorBanner}>
            Nothing was imported. Fix these {rowErrors.length} problem{rowErrors.length === 1 ? '' : 's'} and upload
            again.
          </div>
          <div className={styles.tableWrap}>
            <table className={`${styles.table} ${styles.errorTable}`}>
              <thead>
                <tr>
                  <th>Row</th>
                  <th>Column</th>
                  <th>Problem</th>
                </tr>
              </thead>
              <tbody>
                {rowErrors.map((item, index) => (
                  <tr key={index}>
                    <td>{item.row || '—'}</td>
                    <td>{item.column || '—'}</td>
                    <td>{item.message}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </div>
  )
}
