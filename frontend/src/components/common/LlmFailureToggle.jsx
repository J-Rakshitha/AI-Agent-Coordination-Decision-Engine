import React, { useEffect, useState } from "react";
import { ShieldAlert, ShieldCheck } from "lucide-react";
import { getLlmFailureStatus, toggleLlmFailure } from "../../services/apiClient";

export default function LlmFailureToggle() {
  const [simulating, setSimulating] = useState(false);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    getLlmFailureStatus()
      .then((res) => {
        setSimulating(res.data.simulated_llm_failure);
        setReady(true);
      })
      .catch(() => setReady(false));
  }, []);

  async function handleToggle() {
    const next = !simulating;
    try {
      await toggleLlmFailure(next);
      setSimulating(next);
    } catch {
      // Backend unreachable — leave state unchanged rather than lie about it.
    }
  }

  if (!ready) return null;

  return (
    <button
      onClick={handleToggle}
      title="Force every agent to use the rule-based fallback (proves the demo never crashes even if the LLM API is down)"
      className={`flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg border text-xs transition-colors ${
        simulating
          ? "bg-accent-warning/15 border-accent-warning/40 text-accent-warning"
          : "border-base-border text-ink-muted hover:text-ink-primary"
      }`}
    >
      {simulating ? <ShieldAlert size={13} /> : <ShieldCheck size={13} />}
      {simulating ? "LLM Failure Simulated" : "Simulate API Failure"}
    </button>
  );
}
