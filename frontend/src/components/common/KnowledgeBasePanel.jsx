import React, { useCallback, useEffect, useState } from "react";
import { BrainCircuit } from "lucide-react";
import { getKnowledgeBase } from "../../services/apiClient";
import { useLiveSocketContext } from "../../context/LiveSocketContext";

const categoryLabel = {
  incident_resolution: "Incident Pattern",
  conflict_pattern: "Conflict Pattern",
};

/**
 * Long-term memory, visualized: every entry here is something the system
 * has "learned" from a past incident or conflict, and will reuse before
 * reasoning from scratch next time the same pattern appears.
 */
export default function KnowledgeBasePanel() {
  const [entries, setEntries] = useState([]);
  const [error, setError] = useState(false);
  const { lastEvent } = useLiveSocketContext();

  const load = useCallback(() => {
    getKnowledgeBase()
      .then((res) => {
        setEntries(res.data);
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
    <div className="bg-base-surface border border-base-border rounded-xl p-4">
      <h2 className="text-sm font-semibold text-ink-primary mb-1 flex items-center gap-2">
        <BrainCircuit size={16} className="text-accent-success" />
        Shared Knowledge Base (Long-Term Memory)
      </h2>
      <p className="text-xs text-ink-faint mb-3">
        Insights the agents have learned from past incidents and conflicts — reused instead of
        reasoning from scratch each time the same pattern appears.
      </p>

      {!error && entries.length === 0 && (
        <p className="text-xs text-ink-muted">
          No knowledge recorded yet — it builds up as incidents and conflicts get resolved.
        </p>
      )}

      <div className="space-y-2">
        {entries.map((e) => (
          <div key={e.id} className="bg-base-bg border border-base-border rounded-lg px-3 py-2">
            <div className="flex items-center justify-between text-[11px] mb-1">
              <span className="text-accent-success font-medium">{categoryLabel[e.category] || e.category}</span>
              <span className="text-ink-faint">seen {e.success_count}×</span>
            </div>
            <p className="text-[11px] text-ink-faint font-mono mb-1">{e.key_signature}</p>
            <p className="text-xs text-ink-secondary leading-relaxed">{e.insight}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
