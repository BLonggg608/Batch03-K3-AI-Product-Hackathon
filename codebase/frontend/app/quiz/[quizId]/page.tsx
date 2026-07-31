"use client";

import { useEffect, useMemo, useState } from "react";
import { useParams, useRouter, useSearchParams } from "next/navigation";

import { ErrorState, LoadingState } from "@/components/LoadingState";
import { getJson, postJson } from "@/lib/api";
import type { Attempt, Quiz } from "@/lib/types";

export default function QuizPage() {
  const params = useParams<{ quizId: string }>();
  const searchParams = useSearchParams();
  const router = useRouter();
  const [quiz, setQuiz] = useState<Quiz | null>(null);
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");
  const parentAttemptId = searchParams.get("parent");

  const load = async () => {
    setLoading(true);
    setError("");
    try {
      setQuiz(await getJson<Quiz>(`/api/quizzes/${params.quizId}`));
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Không tải được quiz.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void load();
  }, [params.quizId]);

  const answeredCount = useMemo(() => Object.keys(answers).length, [answers]);
  const totalQuestions = quiz?.questions.length ?? 0;
  const progress = totalQuestions ? (answeredCount / totalQuestions) * 100 : 0;

  const submit = async () => {
    if (!quiz || answeredCount !== quiz.questions.length) {
      setError("Bạn cần chọn đáp án cho tất cả câu hỏi.");
      return;
    }
    setSubmitting(true);
    setError("");
    try {
      const attempt = await postJson<Attempt>("/api/attempts/grade", {
        quiz_id: quiz.quiz_id,
        learner_id: "demo-learner",
        parent_attempt_id: parentAttemptId,
        answers: quiz.questions.map((question) => ({
          question_id: question.question_id,
          selected_answer: answers[question.question_id],
        })),
      });
      router.push(
        `/result/${attempt.attempt_id}${parentAttemptId ? "?compare=1" : ""}`,
      );
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Không chấm được quiz.");
      setSubmitting(false);
    }
  };

  if (loading) {
    return <LoadingState label="Đang chuẩn bị câu hỏi..." />;
  }
  if (error && !quiz) {
    return <ErrorState message={error} retry={() => void load()} />;
  }
  if (!quiz) {
    return null;
  }

  return (
    <div className="content-narrow stack-lg">
      <section className="page-title quiz-title">
        <span className="eyebrow">
          {quiz.mode === "diagnostic" ? "Quiz chẩn đoán" : "Quiz củng cố"} ·{" "}
          {quiz.document.document_id === "day01" ? "Ngày 1" : "Ngày 2"}
        </span>
        <h1>{quiz.document.title}</h1>
        <p>Chọn một đáp án cho mỗi câu rồi nộp bài để xem kết quả.</p>
        <div className="quiz-meta">
          <span>{quiz.questions.length} câu hỏi</span>
          <span>
            Nguồn tạo: {quiz.generated_by === "gemini" ? "Gemini" : "Fallback"}
          </span>
        </div>
      </section>

      <section className="quiz-progress" aria-label="Tiến độ làm bài">
        <div className="progress-heading">
          <strong>Tiến độ</strong>
          <span>
            {answeredCount}/{quiz.questions.length} câu
          </span>
        </div>
        <div className="progress-line">
          <span style={{ width: `${progress}%` }} />
        </div>
      </section>

      <div className="question-list">
        {quiz.questions.map((question, index) => {
          const titleId = `question-${question.question_id}`;
          return (
            <section
              className="question-card"
              role="group"
              aria-labelledby={titleId}
              key={question.question_id}
            >
              <div className="question-number">Câu {index + 1}</div>
              <h2 className="question-title" id={titleId}>
                {question.question}
              </h2>
              <div className="choice-list">
                {question.choices.map((choice) => {
                  const checked = answers[question.question_id] === choice.id;
                  return (
                    <label
                      className={checked ? "choice selected" : "choice"}
                      key={choice.id}
                    >
                      <input
                        type="radio"
                        name={question.question_id}
                        value={choice.id}
                        checked={checked}
                        onChange={() =>
                          setAnswers((current) => ({
                            ...current,
                            [question.question_id]: choice.id,
                          }))
                        }
                      />
                      <b aria-hidden="true">{choice.id}</b>
                      <span>{choice.text}</span>
                    </label>
                  );
                })}
              </div>
            </section>
          );
        })}
      </div>

      {error && <ErrorState message={error} />}

      <div className="sticky-actions">
        <span>
          {answeredCount === quiz.questions.length
            ? "Bạn đã trả lời đủ và có thể nộp bài."
            : `Còn ${quiz.questions.length - answeredCount} câu chưa trả lời.`}
        </span>
        <button
          className="button"
          disabled={submitting || answeredCount !== quiz.questions.length}
          onClick={() => void submit()}
        >
          {submitting ? "Đang chấm..." : "Nộp bài"}
        </button>
      </div>
    </div>
  );
}
