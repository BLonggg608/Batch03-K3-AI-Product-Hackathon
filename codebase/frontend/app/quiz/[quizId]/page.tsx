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
      <section className="page-title">
        <span className="eyebrow">
          {quiz.mode === "diagnostic" ? "Quiz tổng hợp" : "Quiz củng cố"} ·{" "}
          {quiz.document.document_id === "day01" ? "Ngày 1" : "Ngày 2"}
        </span>
        <h1>{quiz.document.title}</h1>
        <p>{quiz.document.description}</p>
        <div className="quiz-meta">
          <span>{quiz.questions.length} câu</span>
          <span>{quiz.document.page_count} trang nguồn</span>
          <span>
            Nguồn tạo: {quiz.generated_by === "gemini" ? "Gemini" : "Fallback"}
          </span>
        </div>
      </section>

      <div className="progress-line">
        <span style={{ width: `${(answeredCount / quiz.questions.length) * 100}%` }} />
      </div>
      <p className="progress-copy">
        Đã trả lời {answeredCount}/{quiz.questions.length} câu
      </p>

      <div className="question-list">
        {quiz.questions.map((question, index) => (
          <fieldset className="question-card" key={question.question_id}>
            <legend>
              <span>Câu {index + 1}</span>
              {question.question}
            </legend>
            <div className="choice-list">
              {question.choices.map((choice) => {
                const checked = answers[question.question_id] === choice.id;
                return (
                  <label className={checked ? "choice selected" : "choice"} key={choice.id}>
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
                    <b>{choice.id}</b>
                    <span>{choice.text}</span>
                  </label>
                );
              })}
            </div>
          </fieldset>
        ))}
      </div>

      {error && <ErrorState message={error} />}

      <div className="sticky-actions">
        <span>
          {answeredCount === quiz.questions.length
            ? "Đã sẵn sàng chấm"
            : "Hãy trả lời đủ các câu"}
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
