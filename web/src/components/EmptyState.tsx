type Props = {
  title: string;
  message: string;
};

export function EmptyState({ title, message }: Props) {
  return (
    <div className="rounded-xl border border-dashed border-line bg-panel/80 p-5 text-center shadow-soft">
      <p className="text-sm font-semibold text-ink">{title}</p>
      <p className="mt-2 text-sm text-muted">{message}</p>
    </div>
  );
}
