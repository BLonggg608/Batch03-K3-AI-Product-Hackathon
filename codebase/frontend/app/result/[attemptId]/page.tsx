"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useParams, useRouter, useSearchParams } from "next/navigation";

import { CitationLink } from "@/components/CitationLink";
import { ErrorState, LoadingState } from "@/components/LoadingState";
import { getJson, postJson } from "@/lib/api";
import type { Attempt, Progress, Review } from "@/lib/types";

export default function ResultPage() {
  const params = useParams<{ attemptId: string }>();
  const searchParams = useSearchParams();
  const router = useRouter();
  const [attempt, setAttempt] = useState<Attempt | null>(null);
  const [comparison, setComparison] = useState<Progress | null>(null);
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState("");
  const shouldCompare = searchParams.get("compare") === "1";

  const load = async () => {
    setLoading(true);
    setError("");
    try {
      const current = await getJson<Attempt>(`/api/attempts/${params.attemptId}`);
      setAttempt(current);
      if (shouldCompare) {
        setComparison(
          await getJson<Progress>(`/api/progress/${params.attemptId}`),
        );
      }
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Không tải được kết quả.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void load();
  }, [params.attemptId, shouldCompare]);

  const openReview = async () => {
    if (!attempt) return;
    setCreating(true);
    setError("");
    try {
      await postJson<Review>("/api/reviews/generate", {
        attempt_id: attempt.attempt_id,
      });
      router.push(`/review/${attempt.attempt_id}`);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Không tạo được gói ôn.");
      setCreating(false);
    }
  };

  if (loading) return <LoadingState label="Đang phân tích kết quả..." />;
  if (error && !attempt) {
    return <ErrorState message={error} retry={() => void load()} />;
  }
  if (!attempt) return null;

  return (
    <div className="content-narrow stack-lg">
      <section className="score-card">
        <div className="score-ring">
          <strong>{attempt.score}/{attempt.total}</strong>
          <span>{attempt.percentage}%</span>
        </div>
        <div>
          <span className="eyebrow">
            {attempt.document_id === "day01" ? "Ngày 1" : "Ngày 2"} · Kết quả tổng hợp
          </span>
          <h1>
            {attempt.mastery_status === "passed"
              ? "Bạn đã đạt ngưỡng"
              : "Bạn chưa đạt ngưỡng"}
          </h1>
          <p>
            Đây là chẩn đoán từ các câu trả lời, không phải kết luận cố định về năng
            lực của bạn.
          </p>
        </div>
      </section>

      {comparison && (
        <section className="comparison-card">
          <div>
            <span>Trước ôn tập</span>
            <strong>{comparison.before_percentage}%</strong>
          </div>
          <span className="comparison-arrow">→</span>
          <div>
            <span>Sau ôn tập</span>
            <strong>{comparison.after_percentage}%</strong>
          </div>
          <p>{comparison.message}</p>
        </section>
      )}

      <section>
        <div className="section-heading">
          <div>
            <span className="eyebrow">Giải thích từng câu</span>
            <h2>Đối chiếu đáp án</h2>
          </div>
        </div>
        <div className="answer-list">
          {attempt.answers.map((answer, index) => (
            <article
              className={answer.is_correct ? "answer-card correct" : "answer-card wrong"}
              key={answer.question_id}
            >
              <div className="answer-heading">
                <span>{answer.is_correct ? "Đúng" : "Chưa đúng"}</span>
                <strong>Câu {index + 1}</strong>
              </div>
              <h3>{answer.question || answer.question_id}</h3>
              <p>
                Bạn chọn <b>{answer.selected_answer}</b> · Đáp án đúng{" "}
                <b>{answer.correct_answer}</b>
              </p>
              {!answer.is_correct && answer.misconception && (
                <div className="gap-hint">
                  <strong>Điểm có thể đang nhầm</strong>
                  <span>{answer.misconception}</span>
                </div>
              )}
              <p className="explanation">{answer.explanation}</p>
              <blockquote className="evidence-quote">
                <strong>Evidence trên slide</strong>
                <span>“{answer.evidence_quote}”</span>
              </blockquote>
              <div className="source-list">
                <CitationLink
                  documentId={attempt.document_id}
                  page={answer.source_page}
                />
              </div>
            </article>
          ))}
        </div>
      </section>

      {error && <ErrorState message={error} />}

      <div className="actions-row">
        <Link href="/" className="button secondary">
          Chọn bộ slide khác
        </Link>
        {!shouldCompare && (
          <button className="button" onClick={() => void openReview()} disabled={creating}>
            {creating ? "Đang tạo..." : "Tạo gói ôn tập cá nhân"}
          </button>
        )}
        {shouldCompare && (
          <button className="button" onClick={() => void openReview()} disabled={creating}>
            {creating ? "Đang tạo..." : "Ôn lại phần còn sai"}
          </button>
        )}
      </div>
    </div>
  );
}
