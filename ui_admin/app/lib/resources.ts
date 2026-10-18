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
  readOnlyResource?: boolean
}

/** Purpose-built pages listed above the generic table editors. */
export const TOOLS = [
  { href: '/questions', label: 'Question Bank', description: 'Write, edit, archive, import, and export questions, with full history' },
  { href: '/test-builder', label: 'Test Builder', description: 'Build full-length tests (Step 1 blocks, SAT modules) from unused questions' },
]

export const RESOURCES: ResourceDef[] = [
  {
    key: 'exams',
    label: 'Exams',
    apiPath: 'exams',
    description: 'Exams students can choose from (USMLE, SAT, ...). Delete deactivates.',
    fields: [
      { name: 'id', label: 'ID', type: 'number', readOnly: true, hideOnCreate: true },
      { name: 'slug', label: 'Slug (lowercase, dashes)', type: 'string', required: true },
      { name: 'name', label: 'Name', type: 'string', required: true },
      { name: 'description', label: 'Description', type: 'text' },
      {
        name: 'tools',
        label: 'Tools (JSON list: "lab_values", "calculator", "reference_sheet", "notes")',
        type: 'json',
      },
      { name: 'display_order', label: 'Display Order', type: 'number' },
      { name: 'is_active', label: 'Active', type: 'boolean' },
    ],
  },
  {
    key: 'tags',
    label: 'Tags',
    apiPath: 'tags',
    description: 'Topic tags per exam (category + name, e.g. system / Cardiovascular)',
    fields: [
      { name: 'id', label: 'ID', type: 'number', readOnly: true, hideOnCreate: true },
      { name: 'exam_id', label: 'Exam ID', type: 'number' },
      { name: 'category', label: 'Category', type: 'string', required: true },
      { name: 'name', label: 'Name', type: 'string', required: true },
    ],
  },
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
      { name: 'exam_id', label: 'Exam ID', type: 'number' },
      { name: 'name', label: 'Name', type: 'string', required: true },
      { name: 'description', label: 'Description', type: 'text' },
      { name: 'test_count', label: 'Test Count', type: 'number', required: true },
      { name: 'price', label: 'Price', type: 'number', required: true },
      { name: 'validity_days', label: 'Credits Valid (days)', type: 'number' },
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
    key: 'orders',
    label: 'Orders',
    apiPath: 'orders',
    description: 'Stripe purchases (pending, paid, expired, refunded). Refund from the Stripe dashboard; credits are revoked automatically.',
    readOnlyResource: true,
    fields: [
      { name: 'id', label: 'ID', type: 'number', readOnly: true },
      { name: 'user_id', label: 'User ID', type: 'number', readOnly: true },
      { name: 'package_id', label: 'Package ID', type: 'number', readOnly: true },
      { name: 'status', label: 'Status', type: 'string', readOnly: true },
      { name: 'amount_cents', label: 'Amount (cents)', type: 'number', readOnly: true },
      { name: 'paid_at', label: 'Paid At', type: 'datetime', readOnly: true },
    ],
  },
  {
    key: 'sections',
    label: 'Sections',
    apiPath: 'sections',
    description: 'Subject areas used for score breakdowns (Physiology, SAT Math, ...)',
    fields: [
      { name: 'id', label: 'ID', type: 'number', readOnly: true, hideOnCreate: true },
      { name: 'exam_id', label: 'Exam ID', type: 'number' },
      { name: 'name', label: 'Name', type: 'string', required: true },
      { name: 'description', label: 'Description', type: 'text' },
    ],
  },
  {
    key: 'tests',
    label: 'Tests',
    apiPath: 'tests',
    description: 'Practice exams',
    fields: [
      { name: 'id', label: 'ID', type: 'number', readOnly: true, hideOnCreate: true },
      { name: 'exam_id', label: 'Exam ID', type: 'number' },
      { name: 'name', label: 'Name', type: 'string', required: true },
      { name: 'description', label: 'Description', type: 'text' },
      { name: 'time_limit_minutes', label: 'Time Limit (min, used when no timed sections)', type: 'number', required: true },
      { name: 'question_count', label: 'Question Count', type: 'number', required: true },
      { name: 'break_pool_minutes', label: 'Shared Break Budget (min; USMLE 45; empty = per-section breaks)', type: 'number' },
      {
        name: 'scoring',
        label:
          'Scaled Scoring (JSON raw-correct → scaled; keys under "sections" are Section IDs, e.g. {"sections": {"3": {"0": 200, "44": 800}}, "overall": {...}})',
        type: 'json',
      },
      { name: 'is_active', label: 'Active', type: 'boolean' },
    ],
  },
  {
    key: 'test-sections',
    label: 'Test Sections',
    apiPath: 'test-sections',
    description: 'Timed parts of a test (USMLE blocks, SAT modules), taken in order',
    fields: [
      { name: 'id', label: 'ID', type: 'number', readOnly: true, hideOnCreate: true },
      { name: 'test_id', label: 'Test ID', type: 'number', required: true },
      { name: 'section_id', label: 'Subject Section ID (empty = mixed)', type: 'number' },
      { name: 'section_order', label: 'Section Order', type: 'number', required: true },
      { name: 'name', label: 'Display Name (e.g. Block 1)', type: 'string' },
      { name: 'time_limit_minutes', label: 'Time Limit (min)', type: 'number' },
      { name: 'break_after_minutes', label: 'Break After (min; 0 = none; ignored with shared budget)', type: 'number' },
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
      { name: 'section_id', label: 'Subject Section ID', type: 'number' },
      { name: 'test_section_id', label: 'Test Section ID (timed part)', type: 'number' },
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
      { name: 'scaled_score', label: 'Scaled Score', type: 'number', readOnly: true, hideOnCreate: true },
      { name: 'section_scores', label: 'Section Scores', type: 'json', readOnly: true, hideOnCreate: true },
    ],
  },
  {
    key: 'attempt-sections',
    label: 'Attempt Sections',
    apiPath: 'attempt-sections',
    description: 'Per-section timing for each attempt (read-only)',
    readOnlyResource: true,
    fields: [
      { name: 'id', label: 'ID', type: 'number', readOnly: true },
      { name: 'test_attempt_id', label: 'Attempt ID', type: 'number', readOnly: true },
      { name: 'section_order', label: 'Order', type: 'number', readOnly: true },
      { name: 'name', label: 'Name', type: 'string', readOnly: true },
      { name: 'started_at', label: 'Started', type: 'datetime', readOnly: true },
      { name: 'completed_at', label: 'Completed', type: 'datetime', readOnly: true },
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
