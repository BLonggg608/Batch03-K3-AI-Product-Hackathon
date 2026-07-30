export function LoadingState({ label = "Đang tải..." }: { label?: string }) {
  return (
    <div className="state-card" role="status">
      <span className="spinner" aria-hidden="true" />
      <p>{label}</p>
    </div>
  );
}

export function ErrorState({
  message,
  retry,
}: {
  message: string;
  retry?: () => void;
}) {
  return (
    <div className="state-card error-card" role="alert">
      <strong>Chưa thể hoàn thành</strong>
      <p>{message}</p>
      {retry && (
        <button className="button secondary" onClick={retry}>
          Thử lại
        </button>
      )}
    </div>
  );
}
