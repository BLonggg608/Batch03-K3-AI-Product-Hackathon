from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


DocumentId = Literal["day01", "day02"]


class DocumentSummary(BaseModel):
    document_id: DocumentId
    document_name: str
    title: str
    description: str
    page_count: int
    word_count: int


class PageSummary(BaseModel):
    page_number: int
    title: str
    preview: str
    word_count: int
    is_instructional: bool
    topics: list[str] = Field(default_factory=list)


class DocumentOutline(DocumentSummary):
    pages: list[PageSummary]


class Choice(BaseModel):
    id: str
    text: str
    misconception: str | None = None


class ChoicePublic(BaseModel):
    id: str
    text: str


class QuizQuestion(BaseModel):
    question_id: str
    question: str
    choices: list[Choice]
    correct_answer: str
    explanation: str
    evidence_quote: str
    source_page: int


class QuizQuestionPublic(BaseModel):
    question_id: str
    question: str
    choices: list[ChoicePublic]
    source_page: int


class Quiz(BaseModel):
    quiz_id: str
    document_id: DocumentId
    mode: Literal["diagnostic", "reinforcement"]
    questions: list[QuizQuestion]
    generated_by: Literal["gemini", "fallback"]
    validation_trace: list[dict] = Field(default_factory=list)


class QuizPublic(BaseModel):
    quiz_id: str
    document: DocumentSummary
    mode: Literal["diagnostic", "reinforcement"]
    questions: list[QuizQuestionPublic]
    generated_by: Literal["gemini", "fallback"]


class GenerateQuizRequest(BaseModel):
    document_id: DocumentId
    question_count: Literal[5, 10, 20] = 10


class AnswerSubmission(BaseModel):
    question_id: str
    selected_answer: str


class GradeAttemptRequest(BaseModel):
    quiz_id: str
    learner_id: str = "demo-learner"
    answers: list[AnswerSubmission]
    parent_attempt_id: str | None = None


class AnswerResult(BaseModel):
    question_id: str
    question: str
    selected_answer: str
    correct_answer: str
    is_correct: bool
    explanation: str
    misconception: str | None = None
    evidence_quote: str
    source_page: int


class AttemptResult(BaseModel):
    attempt_id: str
    quiz_id: str
    learner_id: str
    document_id: DocumentId
    mode: Literal["diagnostic", "reinforcement"]
    score: int
    total: int
    percentage: int
    mastery_status: Literal["passed", "not_yet"]
    answers: list[AnswerResult]
    parent_attempt_id: str | None = None


class GenerateReviewRequest(BaseModel):
    attempt_id: str


class KeyPoint(BaseModel):
    text: str
    evidence_quote: str
    source_page: int


class ReviewPackage(BaseModel):
    review_id: str
    attempt_id: str
    document_id: DocumentId
    document_title: str
    possible_gap: str
    key_points: list[KeyPoint]
    wrong_answer_explanation: str
    generated_by: Literal["gemini", "fallback"]
    tool_trace: list[dict] = Field(default_factory=list)


class GenerateReinforcementRequest(BaseModel):
    attempt_id: str


class ProgressComparison(BaseModel):
    document_id: DocumentId
    diagnostic_attempt_id: str
    reinforcement_attempt_id: str
    before_percentage: int
    after_percentage: int
    delta_percentage_points: int
    message: str


class QuizValidationResult(BaseModel):
    valid: bool
    errors: list[dict] = Field(default_factory=list)
    warnings: list[dict] = Field(default_factory=list)
