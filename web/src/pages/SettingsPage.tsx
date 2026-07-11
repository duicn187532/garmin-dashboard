import { CheckCircle2, Save } from "lucide-react";
import { useState } from "react";
import { api, getAppAccessToken, getSyncToken, setApiBaseUrl, setAppAccessToken, setSyncToken } from "../api/client";
import { useAppData } from "../state/AppDataContext";

type Props = {
  apiBaseUrl: string;
  onApiBaseUrlChange: (value: string) => void;
};

export function SettingsPage({ apiBaseUrl, onApiBaseUrlChange }: Props) {
  const { clearCache, refreshFromBackend } = useAppData();
  const [baseUrl, setBaseUrl] = useState(apiBaseUrl);
  const [appToken, setAppToken] = useState(getAppAccessToken());
  const [token, setToken] = useState(getSyncToken());
  const [status, setStatus] = useState<string | null>(null);

  function save() {
    setApiBaseUrl(baseUrl);
    setAppAccessToken(appToken);
    setSyncToken(token);
    onApiBaseUrlChange(baseUrl.replace(/\/$/, ""));
    setStatus("Saved locally");
  }

  async function test() {
    const result = await api.status(baseUrl.replace(/\/$/, ""));
    setStatus(`Backend ${result.status}`);
  }

  return (
    <section className="space-y-4">
      <h2 className="text-2xl font-semibold">Settings</h2>
      <div className="rounded-2xl border border-line bg-panel/90 p-4 shadow-soft">
        <label className="block">
          <span className="text-sm font-medium text-muted">API Base URL</span>
          <input
            className="mt-2 h-11 w-full rounded-xl border border-line bg-panel2 px-3 text-sm text-ink outline-none focus:border-pine"
            value={baseUrl}
            onChange={(event) => setBaseUrl(event.target.value)}
          />
        </label>
        <label className="mt-4 block">
          <span className="text-sm font-medium text-muted">App access token</span>
          <input
            className="mt-2 h-11 w-full rounded-xl border border-line bg-panel2 px-3 text-sm text-ink outline-none focus:border-pine"
            value={appToken}
            onChange={(event) => setAppToken(event.target.value)}
            type="password"
          />
        </label>
        <label className="mt-4 block">
          <span className="text-sm font-medium text-muted">Sync token</span>
          <input
            className="mt-2 h-11 w-full rounded-xl border border-line bg-panel2 px-3 text-sm text-ink outline-none focus:border-pine"
            value={token}
            onChange={(event) => setToken(event.target.value)}
            type="password"
          />
        </label>
        <div className="mt-4 flex flex-wrap gap-2">
          <button className="inline-flex h-10 items-center gap-2 rounded-xl bg-pine px-4 text-sm font-semibold text-surface" onClick={save} type="button">
            <Save size={16} /> Save
          </button>
          <button className="inline-flex h-10 items-center gap-2 rounded-xl border border-line bg-panel2 px-4 text-sm font-semibold text-ink" onClick={test} type="button">
            <CheckCircle2 size={16} /> Test
          </button>
          <button className="inline-flex h-10 items-center gap-2 rounded-xl border border-line bg-panel2 px-4 text-sm font-semibold text-ink" onClick={clearCache} type="button">
            Clear cache
          </button>
          <button className="inline-flex h-10 items-center gap-2 rounded-xl border border-line bg-panel2 px-4 text-sm font-semibold text-ink" onClick={() => refreshFromBackend({ sync: false })} type="button">
            Refresh cache
          </button>
        </div>
        {status ? <p className="mt-3 text-sm text-pine">{status}</p> : null}
      </div>
    </section>
  );
}
