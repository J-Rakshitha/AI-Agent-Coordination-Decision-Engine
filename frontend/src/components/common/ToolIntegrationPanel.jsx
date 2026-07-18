import React, { useCallback, useEffect, useState } from "react";
import { Wrench, Sparkles, Loader2, CheckCircle2, XCircle } from "lucide-react";
import { listTools, selectAndExecuteTool, getToolAccuracy } from "../../services/apiClient";
import { useLiveSocketContext } from "../../context/LiveSocketContext";

const PRESET_SITUATIONS = [
  "Database connection pool exhaustion causing timeouts",
  "Critical P1 outage, needs to escalate to the human team",
  "Check knowledge base for past history of this pattern",
];

export default function ToolIntegrationPanel() {
  const [tools, setTools] = useState([]);
  const [accuracy, setAccuracy] = useState(null);
  const [situation, setSituation] = useState(PRESET_SITUATIONS[0]);
  const [lastResult, setLastResult] = useState(null);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState(false);
  const { lastEvent } = useLiveSocketContext();

  const load = useCallback(() => {
    Promise.all([listTools(), getToolAccuracy()])
      .then(([toolsRes, accRes]) => {
        setTools(toolsRes.data);
        setAccuracy(accRes.data);
        setError(false);
      })
      .catch(() => setError(true));
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  useEffect(() => {
    if (lastEvent) load();
  }, [lastEvent, load]);

  async function handleTry() {
    setRunning(true);
    try {
      const res = await selectAndExecuteTool({ situation });
      setLastResult(res.data);
      load();
    } catch {
      setError(true);
    } finally {
      setRunning(false);
    }
  }

  return (
    <div className="bg-base-surface border border-base-border rounded-xl p-4">
      <h2 className="text-sm font-semibold text-ink-primary mb-1 flex items-center gap-2">
        <Wrench size={16} className="text-accent-devcollab" />
        Tool Integration & Intelligent Selection
      </h2>
      <p className="text-xs text-ink-faint mb-3">
        Custom enterprise tools/API connectors agents can invoke. Describe a situation below and the
        Tool Selector Agent will pick — and run — the best matching tool.
      </p>

      {error && <p className="text-xs text-ink-muted mb-3">Backend not reachable.</p>}

      {/* Registered tools */}
      <div className="flex flex-wrap gap-1.5 mb-3">
        {tools.map((t) => (
          <span
            key={t.name}
            title={t.description}
            className="text-[10px] font-mono px-2 py-1 rounded-md bg-base-bg border border-base-border text-ink-muted"
          >
            {t.name}
          </span>
        ))}
      </div>

      {/* Try it */}
      <div className="flex flex-col sm:flex-row gap-2 mb-3">
        <select
          value={situation}
          onChange={(e) => setSituation(e.target.value)}
          className="flex-1 text-xs bg-base-bg border border-base-border rounded-lg px-2 py-1.5 text-ink-secondary"
        >
          {PRESET_SITUATIONS.map((s) => (
            <option key={s} value={s}>{s}</option>
          ))}
        </select>
        <button
          onClick={handleTry}
          disabled={running}
          className="flex items-center justify-center gap-1.5 text-xs px-3 py-1.5 rounded-lg bg-accent-devcollab/15 text-accent-devcollab border border-accent-devcollab/30 hover:bg-accent-devcollab/25 transition-colors disabled:opacity-50"
        >
          {running ? <Loader2 size={13} className="animate-spin" /> : <Sparkles size={13} />}
          Try Tool Selection
        </button>
      </div>

      {lastResult && (
        <div className="bg-base-bg border border-base-border rounded-lg px-3 py-2 mb-3 text-xs">
          <div className="flex items-center gap-1.5 mb-1">
            {lastResult.success ? (
              <CheckCircle2 size={13} className="text-accent-success" />
            ) : (
              <XCircle size={13} className="text-accent-warning" />
            )}
            <span className="font-mono text-ink-primary">{lastResult.tool_name}</span>
            <span className="ml-auto text-[10px] text-ink-faint uppercase">
              {lastResult.used_llm_selection ? "LLM" : "Rule-based"}
            </span>
          </div>
          <p className="text-ink-secondary break-words">
            {typeof lastResult.output === "string" ? lastResult.output : JSON.stringify(lastResult.output)}
          </p>
        </div>
      )}

      {/* Accuracy */}
      {accuracy && accuracy.total_executions > 0 && (
        <div className="text-xs">
          <div className="flex items-center justify-between mb-1.5">
            <span className="text-ink-muted">Action Execution Accuracy</span>
            <span className="text-ink-primary font-semibold">{accuracy.overall_accuracy_pct}%</span>
          </div>
          <div className="space-y-1">
            {accuracy.per_tool.map((t) => (
              <div key={t.tool_name} className="flex items-center justify-between text-[11px] text-ink-faint">
                <span className="font-mono">{t.tool_name}</span>
                <span>{t.successes}/{t.total} ({t.accuracy_pct}%)</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
