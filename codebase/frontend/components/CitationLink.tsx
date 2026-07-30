import { citationUrl } from "@/lib/api";

export function CitationLink({
  documentId,
  page,
}: {
  documentId: string;
  page: number;
}) {
  return (
    <a
      className="citation"
      href={citationUrl(documentId, page)}
      target="_blank"
      rel="noreferrer"
      title={`Mở tài liệu nguồn tại trang ${page}`}
    >
      Trang {page}
    </a>
  );
}
