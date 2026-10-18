'use client'

import Link from 'next/link'
import { useEffect, useMemo, useState } from 'react'
import styles from '../../components/QuestionBank.module.css'
import { Section, useLookups } from '../../lib/questionBank'
import { apiJson } from '../../utils/api'

interface PartForm {
  name: string
  questionCount: number
  minutes: number
  sectionIds: number[]
  breakAfter: string
}

interface BuildResult {
  test_id: number | null
  parts: { name: string; question_count: number; available: number; by_section: Record<string, number> }[]
  pool_size: number
  pool_remaining: number
  problems: string[]
}

interface Pool {
  total: number
  by_section: { section_id: number | null; name: string; count: number }[]
}

interface Package {
  id: number
  exam_id: number | null
  name: string
}

type BreakMode = 'pool' | 'scheduled'

const isMath = (s: Section) => /math/i.test(s.name)

function usmlePreset(): { parts: PartForm[]; breakMode: BreakMode; pool: number } {
  return {
    parts: Array.from({ length: 7 }, (_, i) => ({
      name: `Block ${i + 1}`, questionCount: 40, minutes: 60, sectionIds: [], breakAfter: '',
    })),
    breakMode: 'pool',
    pool: 45,
  }
}

function satPreset(sections: Section[]): { parts: PartForm[]; breakMode: BreakMode; pool: number } {
  const readingWriting = sections.filter((s) => !isMath(s)).map((s) => s.id)
  const math = sections.filter(isMath).map((s) => s.id)
  return {
    parts: [
      { name: 'Reading and Writing — Module 1', questionCount: 27, minutes: 32, sectionIds: readingWriting, breakAfter: '0' },
      { name: 'Reading and Writing — Module 2', questionCount: 27, minutes: 32, sectionIds: readingWriting, breakAfter: '10' },
      { name: 'Math — Module 1', questionCount: 22, minutes: 35, sectionIds: math, breakAfter: '0' },
      { name: 'Math — Module 2', questionCount: 22, minutes: 35, sectionIds: math, breakAfter: '' },
    ],
    breakMode: 'scheduled',
    pool: 45,
  }
}

export default function TestBuilderPage() {
  const { exams, sections } = useLookups()
  const [examId, setExamId] = useState('')
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [parts, setParts] = useState<PartForm[]>([])
  const [breakMode, setBreakMode] = useState<BreakMode>('pool')
  const [breakPool, setBreakPool] = useState(45)
  const [excludeUsed, setExcludeUsed] = useState(true)
  const [packageId, setPackageId] = useState('')
  const [packages, setPackages] = useState<Package[]>([])
  const [pool, setPool] = useState<Pool | null>(null)
  const [preview, setPreview] = useState<BuildResult | null>(null)
  const [built, setBuilt] = useState<BuildResult | null>(null)
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  const exam = exams.find((e) => e.id === Number(examId))
  const examSections = useMemo(() => sections.filter((s) => s.exam_id === Number(examId)), [sections, examId])

  useEffect(() => {
    apiJson<Package[]>('/api/admin/packages').then(setPackages).catch(() => setPackages([]))
  }, [])

  useEffect(() => {
    setPreview(null)
    if (!examId) {
      setPool(null)
      return
    }
    apiJson<Pool>(`/api/admin/test-builder/pool?exam_id=${examId}&exclude_used=${excludeUsed}`)
      .then(setPool)
      .catch(() => setPool(null))
  }, [examId, excludeUsed, built])

  const applyPreset = (preset: { parts: PartForm[]; breakMode: BreakMode; pool: number }) => {
    setParts(preset.parts)
    setBreakMode(preset.breakMode)
    setBreakPool(preset.pool)
    setPreview(null)
  }

  const chooseExam = (value: string) => {
    setExamId(value)
    setPackageId('')
    setBuilt(null)
    const chosen = exams.find((e) => e.id === Number(value))
    const chosenSections = sections.filter((s) => s.exam_id === Number(value))
    if (chosen?.slug.startsWith('usmle')) applyPreset(usmlePreset())
    else if (chosen?.slug === 'sat') applyPreset(satPreset(chosenSections))
    else setParts([])
  }

  const updatePart = (index: number, patch: Partial<PartForm>) => {
    setParts((prev) => prev.map((p, i) => (i === index ? { ...p, ...patch } : p)))
    setPreview(null)
  }

  const toggleSection = (index: number, sectionId: number) => {
    const current = parts[index].sectionIds
    updatePart(index, {
      sectionIds: current.includes(sectionId) ? current.filter((id) => id !== sectionId) : [...current, sectionId],
    })
  }

  const request = (dryRun: boolean) => ({
    exam_id: Number(examId),
    name: name.trim(),
    description: description.trim() || null,
    parts: parts.map((p) => ({
      name: p.name.trim(),
      question_count: p.questionCount,
      time_limit_minutes: p.minutes,
      section_ids: p.sectionIds.length ? p.sectionIds : null,
      break_after_minutes: breakMode === 'scheduled' && p.breakAfter !== '' ? Number(p.breakAfter) : null,
    })),
    break_pool_minutes: breakMode === 'pool' ? breakPool : null,
    exclude_used: excludeUsed,
    package_id: packageId ? Number(packageId) : null,
    dry_run: dryRun,
  })

  const run = async (dryRun: boolean) => {
    if (!examId || !name.trim() || parts.length === 0) {
      setError('Choose an exam, name the test, and add at least one part')
      return
    }
    setBusy(true)
    setError('')
    try {
      const result = await apiJson<BuildResult>('/api/admin/test-builder', {
        method: 'POST',
        body: JSON.stringify(request(dryRun)),
      })
      if (dryRun) setPreview(result)
      else {
        setBuilt(result)
        setPreview(null)
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Build failed')
    } finally {
      setBusy(false)
    }
  }

  const totalQuestions = parts.reduce((sum, p) => sum + p.questionCount, 0)
  const totalMinutes = parts.reduce((sum, p) => sum + p.minutes, 0)

  return (
    <div className={styles.container}>
      <header className={styles.header}>
        <div>
          <h1 className={styles.title}>Test Builder</h1>
          <p className={styles.subtitle}>
            Build a full-length test from questions in the bank. By default only questions that aren&apos;t in any
            other test are used, so students never see a repeat across tests.
          </p>
        </div>
      </header>

      {error && <div className={styles.errorBanner}>{error}</div>}
      {built?.test_id && (
        <div className={styles.successBanner}>
          Built test #{built.test_id} with {built.parts.reduce((s, p) => s + p.question_count, 0)} questions.{' '}
          {packageId ? 'It was added to the package.' : (
            <>Add it to a package under <Link href="/resources/package-tests">Package Tests</Link> to sell it.</>
          )}{' '}
          {built.pool_remaining} unused questions are left for this exam.
        </div>
      )}

      <div className={styles.card}>
        <div className={styles.row}>
          <label className={styles.field}>
            <span>Exam *</span>
            <select value={examId} onChange={(e) => chooseExam(e.target.value)}>
              <option value="">Choose…</option>
              {exams.map((e) => (
                <option key={e.id} value={e.id}>
                  {e.name}
                </option>
              ))}
            </select>
          </label>
          <label className={styles.field}>
            <span>Test name *</span>
            <input value={name} onChange={(e) => setName(e.target.value)} placeholder="Full-Length Practice Test 1" />
          </label>
          <label className={styles.field}>
            <span>Add to package</span>
            <select value={packageId} onChange={(e) => setPackageId(e.target.value)}>
              <option value="">Don&apos;t add yet</option>
              {packages
                .filter((p) => p.exam_id === Number(examId))
                .map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.name}
                  </option>
                ))}
            </select>
          </label>
        </div>
        <label className={styles.field}>
          <span>Description</span>
          <input value={description} onChange={(e) => setDescription(e.target.value)} />
        </label>
        {pool && (
          <p className={styles.muted}>
            {pool.total} {excludeUsed ? 'unused ' : ''}questions available:{' '}
            {pool.by_section.map((s) => `${s.name} ${s.count}`).join(', ') || 'none'}.{' '}
            {exam && totalQuestions > pool.total && (
              <strong>This layout needs {totalQuestions}, so add more questions first.</strong>
            )}
          </p>
        )}
        <label className={styles.muted}>
          <input type="checkbox" checked={excludeUsed} onChange={(e) => setExcludeUsed(e.target.checked)} /> Only use
          questions that aren&apos;t in another test
        </label>
      </div>

      {examId && (
        <div className={styles.card}>
          <h2>Layout</h2>
          <div className={styles.formActions} style={{ marginBottom: '0.75rem' }}>
            <button type="button" className={styles.secondaryBtn} onClick={() => applyPreset(usmlePreset())}>
              USMLE Step 1 preset (7 × 40 questions, 60 min, 45 min breaks)
            </button>
            <button type="button" className={styles.secondaryBtn} onClick={() => applyPreset(satPreset(examSections))}>
              SAT preset (2 Reading and Writing + 2 Math modules)
            </button>
          </div>

          <div className={styles.field}>
            <span>Breaks</span>
            <label className={styles.muted}>
              <input type="radio" checked={breakMode === 'pool'} onChange={() => setBreakMode('pool')} /> Shared break
              budget for the whole test (USMLE):{' '}
              <input
                type="number"
                min={0}
                value={breakPool}
                onChange={(e) => setBreakPool(Number(e.target.value))}
                style={{ width: '5rem' }}
                disabled={breakMode !== 'pool'}
              />{' '}
              minutes
            </label>
            <label className={styles.muted}>
              <input type="radio" checked={breakMode === 'scheduled'} onChange={() => setBreakMode('scheduled')} />{' '}
              Fixed break after each part (SAT; 0 = next part starts immediately)
            </label>
          </div>

          <div className={styles.tableWrap}>
            <table className={styles.table}>
              <thead>
                <tr>
                  <th>Part</th>
                  <th>Questions</th>
                  <th>Minutes</th>
                  <th>Subjects (none checked = any)</th>
                  {breakMode === 'scheduled' && <th>Break after (min)</th>}
                  <th />
                </tr>
              </thead>
              <tbody>
                {parts.map((part, index) => (
                  <tr key={index}>
                    <td>
                      <input value={part.name} onChange={(e) => updatePart(index, { name: e.target.value })} />
                    </td>
                    <td>
                      <input
                        type="number"
                        min={1}
                        value={part.questionCount}
                        onChange={(e) => updatePart(index, { questionCount: Number(e.target.value) })}
                        style={{ width: '5rem' }}
                      />
                    </td>
                    <td>
                      <input
                        type="number"
                        min={1}
                        value={part.minutes}
                        onChange={(e) => updatePart(index, { minutes: Number(e.target.value) })}
                        style={{ width: '5rem' }}
                      />
                    </td>
                    <td>
                      {examSections.length === 0 && <span className={styles.muted}>No sections</span>}
                      {examSections.map((section) => (
                        <label key={section.id} className={styles.muted} style={{ marginRight: '0.6rem' }}>
                          <input
                            type="checkbox"
                            checked={part.sectionIds.includes(section.id)}
                            onChange={() => toggleSection(index, section.id)}
                          />{' '}
                          {section.name}
                        </label>
                      ))}
                    </td>
                    {breakMode === 'scheduled' && (
                      <td>
                        {index < parts.length - 1 && (
                          <input
                            type="number"
                            min={0}
                            value={part.breakAfter}
                            placeholder="60"
                            onChange={(e) => updatePart(index, { breakAfter: e.target.value })}
                            style={{ width: '5rem' }}
                          />
                        )}
                      </td>
                    )}
                    <td>
                      <button
                        type="button"
                        className={styles.iconBtn}
                        onClick={() => setParts(parts.filter((_, i) => i !== index))}
                        aria-label={`Remove ${part.name}`}
                      >
                        ×
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className={styles.formActions}>
            <button
              type="button"
              className={styles.secondaryBtn}
              onClick={() =>
                setParts([
                  ...parts,
                  { name: `Part ${parts.length + 1}`, questionCount: 40, minutes: 60, sectionIds: [], breakAfter: '' },
                ])
              }
            >
              + Add part
            </button>
            <span className={styles.muted}>
              {parts.length} parts · {totalQuestions} questions · {Math.floor(totalMinutes / 60)}h {totalMinutes % 60}m
              of testing
            </span>
          </div>
        </div>
      )}

      {preview && (
        <div className={styles.card}>
          <h2>Preview</h2>
          {preview.problems.length > 0 && (
            <div className={styles.errorBanner}>
              {preview.problems.map((p) => (
                <div key={p}>{p}</div>
              ))}
            </div>
          )}
          <table className={styles.table}>
            <thead>
              <tr>
                <th>Part</th>
                <th>Questions</th>
                <th>By section</th>
              </tr>
            </thead>
            <tbody>
              {preview.parts.map((part) => (
                <tr key={part.name}>
                  <td>{part.name}</td>
                  <td>
                    {part.question_count} (of {part.available} available)
                  </td>
                  <td>
                    {Object.entries(part.by_section)
                      .map(([section, count]) => `${section} ${count}`)
                      .join(', ')}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          <p className={styles.muted}>
            {preview.pool_remaining} of {preview.pool_size} available questions would be left afterwards. Questions are
            picked at random, so the final test may differ slightly from this preview.
          </p>
        </div>
      )}

      {examId && (
        <div className={styles.formActions}>
          <button type="button" className={styles.secondaryBtn} disabled={busy} onClick={() => run(true)}>
            Preview
          </button>
          <button
            type="button"
            className={styles.primaryBtn}
            disabled={busy || !preview || preview.problems.length > 0}
            onClick={() => run(false)}
          >
            {busy ? 'Working…' : 'Build test'}
          </button>
          {!preview && <span className={styles.muted}>Preview first to check there are enough questions.</span>}
        </div>
      )}
    </div>
  )
}
