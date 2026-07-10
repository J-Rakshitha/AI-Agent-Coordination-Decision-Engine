import React, { useCallback, useEffect, useState } from "react";
import { GitBranch, AlertTriangle, Sparkles, Loader2, RefreshCw, GitCommit } from "lucide-react";
import {
  getActiveSessions,
  listConflicts,
  simulateDemoConflict,
  suggestResolution,
  listCommits,
} from "../services/apiClient";
import { useLiveSocketContext } from "../context/LiveSocketContext";
import DecisionTrail from "../components/common/DecisionTrail";

const EVENTS_THAT_REFRESH = ["edit_session_started", "edit_session_ended", "conflict_detected", "conflict_resolved"];

function riskColor(score) {
  if (score >= 70) return "bg-red-500";
  if (score >= 40) return "bg-accent-warning";
  return "bg-accent-success";
}

export default function DevCollabPage() {
  const [sessions, setSessions] = useState([]);
  const [conflicts, setConflicts] = useState([]);
  const [commits, setCommits] = useState([]);
  const [error, setError] = useState(false);
  const [simulating, setSimulating] = useState(false);
  const [suggestingId, setSuggestingId] = useState(null);
  const { lastEvent } = useLiveSocketContext();

  const loadData = useCallback(() => {
    Promise.all([getActiveSessions(), listConflicts(), listCommits()])
      .then(([sessionsRes, conflictsRes, commitsRes]) => {
        setSessions(sessionsRes.data);
        setConflicts(conflictsRes.data);
        setCommits(commitsRes.data);
        setError(false);
      })
      .catch(() => setError(true));
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  useEffect(() => {
    if (lastEvent && EVENTS_THAT_REFRESH.includes(lastEvent.type)) {
      loadData();
    }
  }, [lastEvent, loadData]);

  async function handleSimulate() {
    setSimulating(true);
    try {
      await simulateDemoConflict();
      loadData();
    } catch {
      setError(true);
    } finally {
      setSimulating(false);
    }
  }

  async function handleSuggest(conflictId) {
    setSuggestingId(conflictId);
    try {
      await suggestResolution(conflictId);
      loadData();
    } catch {
      // Non-fatal: leave the conflict card as-is if the suggestion call fails.
    } finally {
      setSuggestingId(null);
    }
  }

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 p-6">
      <div className="lg:col-span-2 space-y-4">
        <div className="bg-base-surface border border-base-border rounded-xl p-4">
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-sm font-semibold text-ink-primary flex items-center gap-2">
              <GitBranch size={16} className="text-accent-devcollab" />
              Live Editing Map
            </h2>
            <div className="flex items-center gap-2">
              <button
                onClick={loadData}
                className="p-1.5 rounded-lg border border-base-border text-ink-muted hover:text-ink-primary transition-colors"
                title="Refresh"
              >
                <RefreshCw size={14} />
              </button>
              <button
                onClick={handleSimulate}
                disabled={simulating}
                className="flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-lg bg-accent-devcollab/15 text-accent-devcollab border border-accent-devcollab/30 hover:bg-accent-devcollab/25 transition-colors disabled:opacity-50"
              >
                {simulating ? <Loader2 size={13} className="animate-spin" /> : <Sparkles size={13} />}
                Simulate Conflict
              </button>
            </div>
          </div>

          {error && (
            <p className="text-xs text-ink-muted">
              Backend not reachable — make sure the FastAPI server is running on port 8000.
            </p>
          )}

          {!error && sessions.length === 0 && (
            <p className="text-xs text-ink-muted">
              No active edit sessions. Click <span className="text-accent-devcollab">Simulate Conflict</span> to
              generate a realistic two-developer overlap scenario.
            </p>
          )}

          <div className="space-y-2">
            {sessions.map((s) => (
              <div
                key={s.session_id}
                className="flex items-center justify-between text-xs bg-base-bg border border-base-border rounded-lg px-3 py-2"
              >
                <div className="flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full" style={{ backgroundColor: s.avatar_color }} />
                  <span className="text-ink-primary font-medium">{s.developer_name}</span>
                  <span className="text-ink-muted font-mono">{s.file_path} → {s.function_name}</span>
                </div>
                <span className="text-ink-faint">
                  {new Date(s.started_at).toLocaleTimeString()}
                </span>
              </div>
            ))}
          </div>
        </div>

        <div className="bg-base-surface border border-base-border rounded-xl p-4">
          <h2 className="text-sm font-semibold text-ink-primary mb-3 flex items-center gap-2">
            <AlertTriangle size={16} className="text-accent-warning" />
            Predicted Conflicts
          </h2>

          {!error && conflicts.length === 0 && (
            <p className="text-xs text-ink-muted">No conflicts predicted yet.</p>
          )}

          <div className="space-y-3">
            {conflicts.map((c) => (
              <div key={c.id} className="border border-base-border rounded-lg px-3 py-3 bg-base-bg">
                <div className="flex items-center justify-between text-xs mb-2">
                  <span className="text-ink-primary font-medium">
                    {c.dev_a} <span className="text-ink-faint">&</span> {c.dev_b}
                  </span>
                  <span
                    className={`uppercase tracking-wide text-[10px] px-2 py-0.5 rounded-full ${
                      c.status === "resolved" ? "bg-accent-success/15 text-accent-success" : "bg-accent-warning/15 text-accent-warning"
                    }`}
                  >
                    {c.status}
                  </span>
                </div>
                <p className="text-xs text-ink-muted font-mono mb-2">
                  {c.file_path} → {c.function_name}
                </p>

                <div className="flex items-center gap-2 mb-2">
                  <div className="flex-1 h-1.5 rounded-full bg-base-border overflow-hidden">
                    <div className={`h-full ${riskColor(c.risk_score)}`} style={{ width: `${c.risk_score}%` }} />
                  </div>
                  <span className="text-[10px] text-ink-muted w-10 text-right">{c.risk_score}%</span>
                </div>

                {c.ai_suggestion ? (
                  <p className="text-xs text-ink-secondary leading-relaxed border-l-2 border-accent-devcollab pl-2 mt-2">
                    {c.ai_suggestion}
                  </p>
                ) : (
                  <button
                    onClick={() => handleSuggest(c.id)}
                    disabled={suggestingId === c.id}
                    className="flex items-center gap-1.5 text-[11px] px-2.5 py-1 rounded-md bg-accent-devcollab/15 text-accent-devcollab hover:bg-accent-devcollab/25 transition-colors disabled:opacity-50"
                  >
                    {suggestingId === c.id ? <Loader2 size={12} className="animate-spin" /> : <Sparkles size={12} />}
                    Get AI Suggestion
                  </button>
                )}
              </div>
            ))}
          </div>
        </div>

        <div className="bg-base-surface border border-base-border rounded-xl p-4">
          <h2 className="text-sm font-semibold text-ink-primary mb-3 flex items-center gap-2">
            <GitCommit size={16} className="text-ink-muted" />
            Recent Commits
          </h2>
          <p className="text-xs text-ink-faint mb-3">
            Created automatically when a conflict is resolved — this history is what the
            AIOps module later searches to link production incidents back to risky merges.
          </p>

          {!error && commits.length === 0 && (
            <p className="text-xs text-ink-muted">No commits yet. Resolve a conflict above to create one.</p>
          )}

          <div className="space-y-1.5">
            {commits.map((c) => (
              <div key={c.id} className="flex items-center justify-between text-xs bg-base-bg border border-base-border rounded-lg px-3 py-2">
                <span className="font-mono text-ink-muted">{c.commit_hash}</span>
                <span className="text-ink-secondary flex-1 mx-3 truncate">{c.message}</span>
                <span className="text-ink-faint">{c.developer_name}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="lg:col-span-1">
        <DecisionTrail />
      </div>
    </div>
  );
}
