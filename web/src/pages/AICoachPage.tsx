import { Bot, Send } from "lucide-react";
import { FormEvent, useState } from "react";
import { EmptyState } from "../components/EmptyState";
import { LoadingBlock } from "../components/LoadingBlock";
import { useAppData } from "../state/AppDataContext";
import type { AiReport } from "../types/api";

type Props = {
  apiBaseUrl: string;
};

export function AICoachPage({ apiBaseUrl }: Props) {
  const { cache, loading, error, askAi } = useAppData();
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState<AiReport | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function ask(event: FormEvent) {
    event.preventDefault();
    if (!question.trim()) return;
    setSubmitting(true);
    try {
      const report = await askAi(question.trim());
      setAnswer(report);
      setQuestion("");
    } finally {
      setSubmitting(false);
    }
  }

  const report = answer || cache.latestAi || cache.today?.ai_report;
  return (
    <section className="space-y-4">
      <div className="flex items-center gap-2">
        <Bot className="text-pine" />
        <h2 className="text-2xl font-semibold">AI Coach</h2>
      </div>
      <form className="rounded-2xl border border-line bg-panel/90 p-3 shadow-soft" onSubmit={ask}>
        <label className="text-sm font-medium text-muted" htmlFor="question">
          Natural language query
        </label>
        <div className="mt-2 flex gap-2">
          <input
            id="question"
            className="h-11 min-w-0 flex-1 rounded-xl border border-line bg-panel2 px-3 text-sm text-ink outline-none focus:border-pine"
            placeholder="最近 14 天我的恢復狀態如何？"
            value={question}
            onChange={(event) => setQuestion(event.target.value)}
          />
          <button className="inline-flex h-11 items-center gap-2 rounded-xl bg-pine px-4 text-sm font-semibold text-surface" disabled={submitting} type="submit">
            <Send size={16} /> Ask
          </button>
        </div>
      </form>
      {loading ? <LoadingBlock /> : null}
      {error ? <EmptyState title="AI unavailable" message={error} /> : null}
      {report ? (
        <div className="space-y-3">
          <div className="rounded-2xl border border-line bg-panel/90 p-4 shadow-soft">
            <div className="text-xs font-semibold uppercase text-pine">{report.report_type}</div>
            <p className="mt-3 whitespace-pre-line text-sm leading-6">{report.answer}</p>
            <p className="mt-3 text-xs text-muted">Model: {report.model}</p>
          </div>
          <details className="rounded-2xl border border-line bg-panel/90 p-4 text-sm shadow-soft">
            <summary className="cursor-pointer font-semibold">Evidence JSON</summary>
            <pre className="mt-3 max-h-96 overflow-auto rounded-xl bg-surface p-3 text-xs text-ink">
              {JSON.stringify(report.evidence_json, null, 2)}
            </pre>
          </details>
        </div>
      ) : (
        !loading && <EmptyState title="No AI report yet" message="Run analysis from Today, or ask a question after syncing data." />
      )}
    </section>
  );
}
