'use client'

import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { useEffect, useState } from 'react'
import styles from '../../../components/QuestionBank.module.css'
import { QuestionEditor } from '../../../components/QuestionEditor'
import { Question } from '../../../lib/questionBank'

export default function NewQuestionPage() {
  const router = useRouter()
  const [examId, setExamId] = useState<string | undefined>(undefined)
  const [lastSaved, setLastSaved] = useState<Question | null>(null)

  useEffect(() => {
    setExamId(new URLSearchParams(window.location.search).get('exam') || undefined)
  }, [])

  const onSaved = (question: Question, addAnother: boolean) => {
    if (addAnother) {
      setLastSaved(question)
      window.scrollTo({ top: 0 })
    } else {
      router.push(`/questions/${question.id}`)
    }
  }

  return (
    <div className={styles.container}>
      <header className={styles.header}>
        <div>
          <h1 className={styles.title}>New question</h1>
          <p className={styles.subtitle}>
            <Link href="/questions">← Question Bank</Link>
          </p>
        </div>
      </header>
      {lastSaved && (
        <div className={styles.successBanner}>
          Saved question <Link href={`/questions/${lastSaved.id}`}>#{lastSaved.id}</Link>. Exam, section, type, and
          tags were kept for the next one.
        </div>
      )}
      <QuestionEditor defaultExamId={examId} onSaved={onSaved} />
    </div>
  )
}
