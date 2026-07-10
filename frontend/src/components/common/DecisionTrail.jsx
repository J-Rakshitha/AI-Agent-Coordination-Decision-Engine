import React, { useCallback, useEffect, useState } from "react";
import { Bot, Cpu } from "lucide-react";
import { getDecisionLog } from "../../services/apiClient";
import { useLiveSocketContext } from "../../context/LiveSocketContext";

/**
 * Explainable-AI panel: shows every decision an agent has made, and whether
 * it came from the real LLM or the rule-based fallback. This is the feature
 * that visually proves the Hybrid AI strategy is working. Refreshes live
 * whenever any agent event comes in over the WebSocket.
 */
export default function DecisionTrail() {
  const [logs, setLogs] = useState([]);
  const [error, setError] = useState(false);
  const { lastEvent } = useLiveSocketContext();

  const load = useCallback(() => {
    getDecisionLog()
      .then((res) => {
        setLogs(res.data);
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

  return (
    <div className="bg-base-surface border border-base-border rounded-xl p-4 h-full flex flex-col">
      <h3 className="text-sm font-semibold text-ink-primary mb-3">Agent Decision Trail</h3>

      {error && (
        <p className="text-xs text-ink-muted">
          Backend not reachable yet — start the FastAPI server to see live agent decisions here.
        </p>
      )}

      {!error && logs.length === 0 && (
        <p className="text-xs text-ink-muted">No agent decisions logged yet.</p>
      )}

      <div className="space-y-3 overflow-y-auto pr-1">
        {logs.map((log) => (
          <div key={log.id} className="border-l-2 border-base-border pl-3 py-1">
            <div className="flex items-center gap-1.5 text-xs text-ink-muted mb-1">
              {log.used_llm ? <Bot size={12} className="text-accent-devcollab" /> : <Cpu size={12} className="text-accent-warning" />}
              <span>{log.agent_name}</span>
              <span className="ml-auto uppercase tracking-wide text-[10px]">
                {log.used_llm ? "LLM" : "Rule-based"}
              </span>
            </div>
            <p className="text-xs text-ink-secondary leading-relaxed">{log.decision_summary}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
