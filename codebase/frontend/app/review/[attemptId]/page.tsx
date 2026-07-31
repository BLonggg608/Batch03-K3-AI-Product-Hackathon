"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";

import { CitationLink } from "@/components/CitationLink";
import { ErrorState, LoadingState } from "@/components/LoadingState";
import { getJson, postJson } from "@/lib/api";
import type { Quiz, Review } from "@/lib/types";

export default function ReviewPage() {
  const params = useParams<{ attemptId: string }>();
  const router = useRouter();
  const [review, setReview] = useState<Review | null>(null);
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState("");

  const load = async () => {
    setLoading(true);
    setError("");
    try {
      setReview(await getJson<Review>(`/api/reviews/${params.attemptId}`));
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Không tải được gói ôn tập.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void load();
  }, [params.attemptId]);

  const createReinforcement = async () => {
    setCreating(true);
    setError("");
    try {
      const quiz = await postJson<Quiz>("/api/reinforcement/generate", {
        attempt_id: params.attemptId,
      });
      router.push(`/quiz/${quiz.quiz_id}?parent=${params.attemptId}`);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Không tạo được quiz củng cố.");
      setCreating(false);
    }
  };

  if (loading) return <LoadingState label="Đang chuẩn bị gói ôn tập..." />;
  if (error && !review) {
    return <ErrorState message={error} retry={() => void load()} />;
  }
  if (!review) return null;

  return (
    <div className="content-narrow stack-lg">
      <section className="page-title">
        <span className="eyebrow">
          Gói ôn tập · {review.document_id === "day01" ? "Ngày 1" : "Ngày 2"}
        </span>
        <h1>{review.document_title}</h1>
        <p>
          Xem lại các ý liên quan đến những câu bạn trả lời chưa đúng trước khi
          làm quiz củng cố.
        </p>
      </section>

      <section className="review-block diagnosis">
        <span className="block-number">01</span>
        <div className="grow">
          <span className="eyebrow">Chẩn đoán thận trọng</span>
          <h2>Điểm có thể đang nhầm</h2>
          <p>{review.possible_gap}</p>
        </div>
      </section>

      <section className="review-block">
        <span className="block-number">02</span>
        <div className="grow">
          <span className="eyebrow">Ôn đúng nội dung nguồn</span>
          <h2>Điểm cần xem lại</h2>
          <div className="key-point-list">
            {review.key_points.map((point, index) => (
              <article key={`${point.evidence_quote}-${index}`}>
                <b>{index + 1}</b>
                <div className="key-point-content">
                  <p>{point.text}</p>
                  <blockquote className="evidence-quote compact">
                    <strong>Evidence</strong>
                    <span>“{point.evidence_quote}”</span>
                  </blockquote>
                  <CitationLink
                    documentId={review.document_id}
                    page={point.source_page}
                  />
                </div>
              </article>
            ))}
          </div>
        </div>
      </section>

      <section className="review-block">
        <span className="block-number">03</span>
        <div className="grow">
          <span className="eyebrow">Giải thích đáp án sai</span>
          <h2>Vì sao cần xem lại?</h2>
          <p>{review.wrong_answer_explanation}</p>
        </div>
      </section>

      <div className="source-panel">
        <div>
          <strong>Tài liệu nguồn</strong>
          <span>
            {review.document_id === "day01"
              ? "d1-slide-hackathon.pdf"
              : "d2-slide-hackathon.pdf"}
          </span>
        </div>
        <span>{review.key_points.length} nội dung cần xem lại</span>
      </div>

      {error && <ErrorState message={error} />}

      <div className="actions-row">
        <Link href={`/result/${params.attemptId}`} className="button secondary">
          Xem lại kết quả
        </Link>
        <button
          className="button"
          onClick={() => void createReinforcement()}
          disabled={creating}
        >
          {creating ? "Đang tạo..." : "Làm quiz củng cố"}
        </button>
      </div>
    </div>
  );
}
