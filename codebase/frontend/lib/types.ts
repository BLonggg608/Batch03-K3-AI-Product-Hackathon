export type DocumentSummary = {
  document_id: "day01" | "day02";
  document_name: string;
  title: string;
  description: string;
  page_count: number;
  word_count: number;
};

export type Choice = {
  id: string;
  text: string;
};

export type Quiz = {
  quiz_id: string;
  document: DocumentSummary;
  mode: "diagnostic" | "reinforcement";
  generated_by: "gemini" | "fallback";
  questions: Array<{
    question_id: string;
    question: string;
    choices: Choice[];
    source_page: number;
  }>;
};

export type AnswerResult = {
  question_id: string;
  question: string;
  selected_answer: string;
  correct_answer: string;
  is_correct: boolean;
  explanation: string;
  misconception?: string | null;
  evidence_quote: string;
  source_page: number;
};

export type Attempt = {
  attempt_id: string;
  quiz_id: string;
  learner_id: string;
  document_id: "day01" | "day02";
  mode: "diagnostic" | "reinforcement";
  score: number;
  total: number;
  percentage: number;
  mastery_status: "passed" | "not_yet";
  answers: AnswerResult[];
  parent_attempt_id?: string | null;
};

export type Review = {
  review_id: string;
  attempt_id: string;
  document_id: "day01" | "day02";
  document_title: string;
  possible_gap: string;
  key_points: Array<{
    text: string;
    evidence_quote: string;
    source_page: number;
  }>;
  wrong_answer_explanation: string;
  generated_by: "gemini" | "fallback";
};

export type Progress = {
  document_id: "day01" | "day02";
  diagnostic_attempt_id: string;
  reinforcement_attempt_id: string;
  before_percentage: number;
  after_percentage: number;
  delta_percentage_points: number;
  message: string;
};
