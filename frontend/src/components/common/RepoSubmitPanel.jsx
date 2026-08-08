import React, { useEffect, useState } from "react";
import { Github, Loader2, RefreshCw, Upload } from "lucide-react";
import { getMyRepo, submitRepo, recheckRepo } from "../../services/apiClient";
import { useAuth } from "../../context/AuthContext";

export default function RepoSubmitPanel({ onScanned }) {
  const { user } = useAuth();
  const [repoUrl, setRepoUrl] = useState("");
  const [mine, setMine] = useState(null);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");

  useEffect(() => {
    getMyRepo().then((res) => setMine(res.data)).catch(() => {});
  }, []);

  async function handleSubmit(e) {
    e.preventDefault();
    if (!repoUrl.trim()) return;
    setBusy(true);
    setMessage("");
    try {
      const res = await submitRepo(repoUrl.trim());
      setMine({ connected: true, ...res.data });
      setMessage(`Scanned ${res.data.repo_owner}/${res.data.repo_name} — ${res.data.symbols_indexed} symbols.`);
      onScanned?.(res.data);
    } catch (err) {
      setMessage(err.response?.data?.detail || "Could not submit repository.");
    } finally {
      setBusy(false);
    }
  }

  async function handleRecheck() {
    setBusy(true);
    try {
      const res = await recheckRepo();
      setMine((prev) => ({ ...prev, ...res.data, connected: true }));
      setMessage(`Rechecked — ${res.data.symbols_indexed} symbols.`);
      onScanned?.(res.data);
    } catch (err) {
      setMessage(err.response?.data?.detail || "Recheck failed.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="bg-base-surface border border-base-border rounded-xl p-4">
      <h2 className="text-sm font-semibold flex items-center gap-2 mb-2">
        <Github size={16} /> Connect Your GitHub Repository
      </h2>
      <p className="text-xs text-ink-faint mb-3">
        Signed in as <span className="text-ink-primary font-medium">{user?.full_name}</span>.
      </p>
      {mine?.connected && (
        <div className="text-xs rounded-lg px-3 py-2 mb-3 bg-accent-success/10 text-accent-success">
          Connected: <span className="font-mono">{mine.repo_owner}/{mine.repo_name}</span>
        </div>
      )}
      <form onSubmit={handleSubmit} className="flex flex-col sm:flex-row gap-2 mb-2">
        <input value={repoUrl} onChange={(e) => setRepoUrl(e.target.value)} placeholder="https://github.com/owner/repo" className="flex-1 text-xs px-3 py-2 rounded-lg bg-base-bg border border-base-border" />
        <button type="submit" disabled={busy} className="flex items-center justify-center gap-1 text-xs px-3 py-2 rounded-lg bg-accent-devcollab/15 text-accent-devcollab disabled:opacity-50">
          {busy ? <Loader2 size={13} className="animate-spin" /> : <Upload size={13} />} Submit & Scan
        </button>
        {mine?.connected && (
          <button type="button" onClick={handleRecheck} disabled={busy} className="flex items-center justify-center gap-1 text-xs px-3 py-2 rounded-lg border border-base-border disabled:opacity-50">
            <RefreshCw size={13} /> Recheck
          </button>
        )}
      </form>
      {message && <p className="text-xs text-ink-muted">{message}</p>}
    </div>
  );
}
