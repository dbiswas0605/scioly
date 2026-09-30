// TypeScript interfaces matching the backend API contract.
// See CLAUDE.md at the repo root for the full product context.

export interface Subject {
  id: string;
  name: string;
  created_at: string;
}

export type QuestionPaperStatus =
  | "draft"
  | "pending_review"
  | "published"
  | "archived";

export interface QuestionPaper {
  id: string;
  subject_id: string;
  title: string;
  description: string | null;
  source_filename: string | null;
  source_content_type: string | null;
  source_file_size_bytes: number | null;
  status: QuestionPaperStatus;
  // Only present on GET /api/papers (list), not the single-paper GET.
  subject_name?: string;
  default_duration_minutes: number | null;
  total_questions: number | null;
  created_by: string | null;
  created_at: string;
  updated_at: string;
}

export interface Student {
  id: string;
  display_name: string;
  created_at: string;
}

export type QuestionType = "mcq" | "short_answer";

export interface QuestionOption {
  id: string;
  question_id: string;
  option_label: string;
  option_text: string | null;
  has_image: boolean;
  is_correct: boolean;
  display_order: number;
}

export interface Question {
  id: string;
  paper_id: string;
  question_number: number;
  question_type: QuestionType;
  prompt_text: string;
  explanation_text: string | null;
  short_answer_expected: string | null;
  points: number;
  llm_suggested_answer: string | null;
  is_reviewed: boolean;
  created_at: string;
  updated_at: string;
  options: QuestionOption[];
}

export interface QuestionOptionInput {
  option_label: string;
  option_text: string | null;
  is_correct: boolean;
  display_order: number;
}

export interface QuestionUpdateInput {
  question_type: QuestionType;
  prompt_text: string;
  explanation_text: string | null;
  short_answer_expected: string | null;
  points: number;
  options: QuestionOptionInput[];
}

export type LlmProviderKey = "anthropic" | "openai" | "ollama" | "mlx";

export interface LlmProvider {
  id: string;
  provider_key: LlmProviderKey;
  display_name: string;
  has_api_key: boolean;
  base_url: string | null;
  model_name: string;
  is_enabled: boolean;
  priority: number;
  extra_config: Record<string, unknown> | null;
  created_at: string;
  updated_at: string;
}

export interface LlmProviderUpdateInput {
  display_name?: string;
  api_key?: string;
  base_url?: string | null;
  model_name?: string;
  is_enabled?: boolean;
  priority?: number;
}

export interface LlmProviderTestResult {
  ok: boolean;
  message: string;
  model_checked: string | null;
  model_available: boolean | null;
}

export type AppSettingValueType = "string" | "integer" | "boolean" | "json";

export interface AppSetting {
  key: string;
  value: string | null;
  value_type: AppSettingValueType;
  description: string | null;
  updated_at: string;
}

export interface AppSettingUpdateInput {
  value?: string | null;
  value_type?: AppSettingValueType;
  description?: string | null;
}

// --- Exam-taking (student side) ---

export type AttemptStatus = "in_progress" | "submitted" | "timed_out" | "abandoned";

export interface ExamAttemptSummary {
  id: string;
  student_id: string;
  paper_id: string;
  attempt_number: number;
  status: AttemptStatus;
  started_at: string;
  submitted_at: string | null;
  duration_minutes_snapshot: number;
  score: number | null;
  max_score: number | null;
  correct_count: number | null;
  total_questions: number | null;
  created_at: string;
}

export interface ExamQuestionOption {
  id: string;
  option_label: string;
  option_text: string | null;
  has_image: boolean;
  display_order: number;
}

export interface ExamQuestion {
  id: string;
  question_number: number;
  question_type: QuestionType;
  prompt_text: string;
  has_prompt_image: boolean;
  points: number;
  options: ExamQuestionOption[];
}

export interface ExamSession extends ExamAttemptSummary {
  paper_title: string;
  questions: ExamQuestion[];
}

export interface AnswerInput {
  question_id: string;
  selected_option_id?: string | null;
  short_answer_text?: string | null;
}

export interface AnswerReview {
  question_id: string;
  question_number: number;
  question_type: QuestionType;
  prompt_text: string;
  explanation_text: string | null;
  points: number;
  options: QuestionOption[];
  selected_option_id: string | null;
  short_answer_text: string | null;
  short_answer_expected: string | null;
  is_correct: boolean | null;
}

export interface AttemptReview extends ExamAttemptSummary {
  paper_title: string;
  answers: AnswerReview[];
}

// --- Parent/Teacher reports dashboard ---

export interface AttemptPoint {
  attempt_id: string;
  attempt_number: number;
  status: AttemptStatus;
  score: number | null;
  max_score: number | null;
  percent: number | null;
  started_at: string;
  submitted_at: string | null;
}

export interface StudentPaperReport {
  student_id: string;
  student_name: string;
  paper_id: string;
  paper_title: string;
  subject_name: string;
  attempts: AttemptPoint[];
}

export interface StudentOverview {
  student_id: string;
  student_name: string;
  total_attempts: number;
  papers_attempted: number;
  average_percent: number | null;
  last_activity: string | null;
}
