import { useEffect, useState } from 'react'
import { apiJson } from '../utils/api'

export type QuestionType = 'multiple_choice' | 'numeric_entry'

export interface Question {
  id: number
  exam_id: number | null
  section_id: number | null
  question_type: QuestionType
  question_text: string
  image_url: string | null
  answer_choices: Record<string, string>
  correct_answer: string
  accepted_answers: string[] | null
  explanation: string | null
  difficulty: string
  created_at: string
  is_active: boolean
  tags: string[]
}

export interface QuestionDetail extends Question {
  usage: { tests: { id: number; name: string }[]; attempt_count: number }
}

export interface QuestionRevision {
  id: number
  question_id: number
  action: string
  snapshot: Partial<Question>
  note: string | null
  changed_by_email: string | null
  created_at: string
}

export interface Exam {
  id: number
  slug: string
  name: string
}

export interface Section {
  id: number
  exam_id: number | null
  name: string
}

export interface Tag {
  id: number
  exam_id: number | null
  category: string
  name: string
}

export const CHOICE_LETTERS = 'ABCDEFGHIJ'.split('')

/** Exams and sections for dropdowns; sections are filtered by exam where used. */
export function useLookups() {
  const [exams, setExams] = useState<Exam[]>([])
  const [sections, setSections] = useState<Section[]>([])
  const [error, setError] = useState('')

  useEffect(() => {
    Promise.all([apiJson<Exam[]>('/api/admin/exams'), apiJson<Section[]>('/api/admin/sections')])
      .then(([examList, sectionList]) => {
        setExams(examList)
        setSections(sectionList)
      })
      .catch((err) => setError(err instanceof Error ? err.message : 'Failed to load exams'))
  }, [])

  return { exams, sections, error }
}

export function useExamTags(examId: number | null) {
  const [tags, setTags] = useState<Tag[]>([])
  useEffect(() => {
    if (!examId) {
      setTags([])
      return
    }
    apiJson<Tag[]>(`/api/admin/tags?exam_id=${examId}`).then(setTags).catch(() => setTags([]))
  }, [examId])
  return tags
}

export function formatDateTime(value: string): string {
  return new Date(value).toLocaleString()
}
