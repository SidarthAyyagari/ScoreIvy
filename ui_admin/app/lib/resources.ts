export type FieldType = 'string' | 'number' | 'boolean' | 'text' | 'json' | 'datetime' | 'email'

export interface FieldDef {
  name: string
  label: string
  type: FieldType
  required?: boolean
  readOnly?: boolean
  hideOnCreate?: boolean
}

export interface ResourceDef {
  key: string
  label: string
  apiPath: string
  description: string
  fields: FieldDef[]
}

export const RESOURCES: ResourceDef[] = [
  {
    key: 'users',
    label: 'Users',
    apiPath: 'users',
    description: 'OAuth users and admin flags',
    fields: [
      { name: 'id', label: 'ID', type: 'number', readOnly: true, hideOnCreate: true },
      { name: 'email', label: 'Email', type: 'email', required: true },
      { name: 'name', label: 'Name', type: 'string' },
      { name: 'picture', label: 'Picture URL', type: 'string' },
      { name: 'oauth_provider', label: 'OAuth Provider', type: 'string' },
      { name: 'oauth_id', label: 'OAuth ID', type: 'string' },
      { name: 'is_active', label: 'Active', type: 'boolean' },
      { name: 'is_admin', label: 'Admin', type: 'boolean' },
      { name: 'created_at', label: 'Created', type: 'datetime', readOnly: true, hideOnCreate: true },
    ],
  },
  {
    key: 'packages',
    label: 'Packages',
    apiPath: 'packages',
    description: 'Purchasable test bundles',
    fields: [
      { name: 'id', label: 'ID', type: 'number', readOnly: true, hideOnCreate: true },
      { name: 'name', label: 'Name', type: 'string', required: true },
      { name: 'description', label: 'Description', type: 'text' },
      { name: 'test_count', label: 'Test Count', type: 'number', required: true },
      { name: 'price', label: 'Price', type: 'number', required: true },
      { name: 'is_active', label: 'Active', type: 'boolean' },
    ],
  },
  {
    key: 'package-tests',
    label: 'Package Tests',
    apiPath: 'package-tests',
    description: 'Tests included in each package',
    fields: [
      { name: 'id', label: 'ID', type: 'number', readOnly: true, hideOnCreate: true },
      { name: 'package_id', label: 'Package ID', type: 'number', required: true },
      { name: 'test_id', label: 'Test ID', type: 'number', required: true },
      { name: 'test_order', label: 'Order', type: 'number', required: true },
    ],
  },
  {
    key: 'user-packages',
    label: 'User Packages',
    apiPath: 'user-packages',
    description: 'Purchased packages per user',
    fields: [
      { name: 'id', label: 'ID', type: 'number', readOnly: true, hideOnCreate: true },
      { name: 'user_id', label: 'User ID', type: 'number', required: true },
      { name: 'package_id', label: 'Package ID', type: 'number', required: true },
      { name: 'tests_remaining', label: 'Tests Remaining', type: 'number', required: true },
      { name: 'expires_at', label: 'Expires At', type: 'datetime' },
    ],
  },
  {
    key: 'sections',
    label: 'Sections',
    apiPath: 'sections',
    description: 'Question categories (Math, Reading, etc.)',
    fields: [
      { name: 'id', label: 'ID', type: 'number', readOnly: true, hideOnCreate: true },
      { name: 'name', label: 'Name', type: 'string', required: true },
      { name: 'description', label: 'Description', type: 'text' },
    ],
  },
  {
    key: 'questions',
    label: 'Questions',
    apiPath: 'questions',
    description: 'MCQ question bank',
    fields: [
      { name: 'id', label: 'ID', type: 'number', readOnly: true, hideOnCreate: true },
      { name: 'section_id', label: 'Section ID', type: 'number' },
      { name: 'question_text', label: 'Question Text', type: 'text', required: true },
      { name: 'image_url', label: 'Image URL', type: 'string' },
      { name: 'answer_choices', label: 'Answer Choices (JSON)', type: 'json', required: true },
      { name: 'correct_answer', label: 'Correct Answer', type: 'string', required: true },
      { name: 'explanation', label: 'Explanation', type: 'text' },
      { name: 'difficulty', label: 'Difficulty', type: 'string' },
      { name: 'is_active', label: 'Active', type: 'boolean' },
    ],
  },
  {
    key: 'tests',
    label: 'Tests',
    apiPath: 'tests',
    description: 'Practice exams',
    fields: [
      { name: 'id', label: 'ID', type: 'number', readOnly: true, hideOnCreate: true },
      { name: 'name', label: 'Name', type: 'string', required: true },
      { name: 'description', label: 'Description', type: 'text' },
      { name: 'time_limit_minutes', label: 'Time Limit (min)', type: 'number', required: true },
      { name: 'question_count', label: 'Question Count', type: 'number', required: true },
      { name: 'is_active', label: 'Active', type: 'boolean' },
    ],
  },
  {
    key: 'test-sections',
    label: 'Test Sections',
    apiPath: 'test-sections',
    description: 'Sections within a test',
    fields: [
      { name: 'id', label: 'ID', type: 'number', readOnly: true, hideOnCreate: true },
      { name: 'test_id', label: 'Test ID', type: 'number', required: true },
      { name: 'section_id', label: 'Section ID', type: 'number', required: true },
      { name: 'section_order', label: 'Section Order', type: 'number', required: true },
      { name: 'question_count', label: 'Question Count', type: 'number', required: true },
    ],
  },
  {
    key: 'test-questions',
    label: 'Test Questions',
    apiPath: 'test-questions',
    description: 'Questions assigned to tests',
    fields: [
      { name: 'id', label: 'ID', type: 'number', readOnly: true, hideOnCreate: true },
      { name: 'test_id', label: 'Test ID', type: 'number', required: true },
      { name: 'question_id', label: 'Question ID', type: 'number', required: true },
      { name: 'section_id', label: 'Section ID', type: 'number', required: true },
      { name: 'question_order', label: 'Question Order', type: 'number', required: true },
      { name: 'section_question_order', label: 'Section Question Order', type: 'number', required: true },
    ],
  },
  {
    key: 'test-attempts',
    label: 'Test Attempts',
    apiPath: 'test-attempts',
    description: 'Student exam attempts',
    fields: [
      { name: 'id', label: 'ID', type: 'number', readOnly: true, hideOnCreate: true },
      { name: 'user_id', label: 'User ID', type: 'number', required: true },
      { name: 'test_id', label: 'Test ID', type: 'number', required: true },
      { name: 'user_package_id', label: 'User Package ID', type: 'number' },
      { name: 'total_questions', label: 'Total Questions', type: 'number', required: true },
      { name: 'score', label: 'Score', type: 'number' },
      { name: 'correct_answers', label: 'Correct Answers', type: 'number' },
      { name: 'completed_at', label: 'Completed At', type: 'datetime' },
    ],
  },
  {
    key: 'question-attempts',
    label: 'Question Attempts',
    apiPath: 'question-attempts',
    description: 'Per-question answers in an attempt',
    fields: [
      { name: 'id', label: 'ID', type: 'number', readOnly: true, hideOnCreate: true },
      { name: 'test_attempt_id', label: 'Test Attempt ID', type: 'number', required: true },
      { name: 'question_id', label: 'Question ID', type: 'number', required: true },
      { name: 'selected_answer', label: 'Selected Answer', type: 'string' },
      { name: 'is_correct', label: 'Correct', type: 'boolean' },
      { name: 'time_spent_seconds', label: 'Time Spent (s)', type: 'number' },
    ],
  },
]

export function getResource(key: string): ResourceDef | undefined {
  return RESOURCES.find((r) => r.key === key)
}
