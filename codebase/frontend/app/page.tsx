"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import { ErrorState, LoadingState } from "@/components/LoadingState";
import { getJson, postJson } from "@/lib/api";
import type { DocumentSummary, Quiz } from "@/lib/types";

type Health = {
  gemini_enabled: boolean;
  gemini_model: string;
};

export default function HomePage() {
  const router = useRouter();
  const [documents, setDocuments] = useState<DocumentSummary[]>([]);
  const [health, setHealth] = useState<Health | null>(null);
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState("");
  const [creatingCount, setCreatingCount] = useState<number | null>(null);
  const [elapsedSeconds, setElapsedSeconds] = useState(0);
  const [choosingCount, setChoosingCount] = useState("");
  const [error, setError] = useState("");

  const load = async () => {
    setLoading(true);
    setError("");
    try {
      const [items, status] = await Promise.all([
        getJson<DocumentSummary[]>("/api/documents"),
        getJson<Health>("/api/health"),
      ]);
      setDocuments(items);
      setHealth(status);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Không tải được tài liệu.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void load();
  }, []);

  useEffect(() => {
    if (!creating) {
      setElapsedSeconds(0);
      return;
    }
    const startedAt = Date.now();
    const timer = window.setInterval(() => {
      setElapsedSeconds(Math.floor((Date.now() - startedAt) / 1000));
    }, 1000);
    return () => window.clearInterval(timer);
  }, [creating]);

  const createQuiz = async (
    document: DocumentSummary,
    questionCount: 5 | 10,
  ) => {
    setCreating(document.document_id);
    setCreatingCount(questionCount);
    setError("");
    try {
      const quiz = await postJson<Quiz>("/api/quizzes/generate", {
        document_id: document.document_id,
        question_count: questionCount,
      });
      router.push(`/quiz/${quiz.quiz_id}`);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Không tạo được quiz.");
      setCreating("");
      setCreatingCount(null);
    }
  };

  if (loading) {
    return <LoadingState label="Đang đọc hai bộ slide..." />;
  }

  return (
    <div className="stack-lg">
      <section className="hero">
        <div>
          <span className="eyebrow">Kiểm tra kiến thức theo ngày học</span>
          <h1>Chọn bộ slide muốn tạo quiz</h1>
        </div>
        {health && (
          <div className="mode-note">
            <span className={health.gemini_enabled ? "dot online" : "dot"} />
            {health.gemini_enabled
              ? `Gemini đã cấu hình · ${health.gemini_model}`
              : "Gemini chưa cấu hình · dùng fallback grounded"}
          </div>
        )}
      </section>

      {error && <ErrorState message={error} />}

      <section>
        <div className="section-heading">
          <div>
            <span className="eyebrow">Tài liệu chính thức</span>
            {/* <h2>2 lựa chọn</h2> */}
          </div>
          {/* <span className="muted">Mỗi lựa chọn là một file PDF hoàn chỉnh</span> */}
        </div>

        <div className="deck-grid">
          {documents.map((document) => (
            <article className="deck-card" key={document.document_id}>
              <div className="deck-index">
                {document.document_id === "day01" ? "01" : "02"}
              </div>
              <span className="eyebrow">
                {document.document_id === "day01" ? "Ngày 1" : "Ngày 2"}
              </span>
              <h2>{document.title}</h2>
              <p>{document.description}</p>
              <div className="deck-actions">
                <button
                  className="button"
                  disabled={Boolean(creating)}
                  onClick={() =>
                    setChoosingCount((current) =>
                      current === document.document_id ? "" : document.document_id,
                    )
                  }
                >
                  {creating === document.document_id
                    ? `Đang tạo · ${elapsedSeconds}s`
                    : "Tạo quiz"}
                </button>
              </div>
              {creating === document.document_id && (
                <div className="generation-progress" role="status">
                  <span className="spinner" />
                  <div>
                    <strong>Đang tạo quiz {creatingCount} câu</strong>
                    <small>Vui lòng chờ trong giây lát.</small>
                  </div>
                </div>
              )}
              {choosingCount === document.document_id && !creating && (
                <div
                  className="question-count-picker"
                  aria-label="Chọn số lượng câu hỏi"
                >
                  <span>Chọn số câu:</span>
                  {[5, 10].map((count) => (
                    <button
                      className="count-option"
                      key={count}
                      onClick={() =>
                        void createQuiz(document, count as 5 | 10)
                      }
                    >
                      {count} câu
                    </button>
                  ))}
                </div>
              )}
            </article>
          ))}
        </div>
      </section>
    </div>
  );
}
