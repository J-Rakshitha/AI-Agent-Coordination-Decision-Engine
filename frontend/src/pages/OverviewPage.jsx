import React, { useCallback, useEffect, useState } from "react";
import { GitBranch, ServerCog, Activity, Link2 } from "lucide-react";
import StatCard from "../components/common/StatCard";
import DecisionTrail from "../components/common/DecisionTrail";
import KnowledgeBasePanel from "../components/common/KnowledgeBasePanel";
import { getStats } from "../services/apiClient";
import { useLiveSocketContext } from "../context/LiveSocketContext";

export default function OverviewPage() {
  const [stats, setStats] = useState(null);
  const [error, setError] = useState(false);
  const { lastEvent } = useLiveSocketContext();

  const loadStats = useCallback(() => {
    getStats()
      .then((res) => {
        setStats(res.data);
        setError(false);
      })
      .catch(() => setError(true));
  }, []);

  useEffect(() => {
    loadStats();
  }, [loadStats]);

  // Any real-time event from either module means the counts may have
  // changed, so refresh the stat cards live without a manual refresh.
  useEffect(() => {
    if (lastEvent) loadStats();
  }, [lastEvent, loadStats]);

  const val = (n) => (error || stats === null ? "—" : n);

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 p-6">
      <div className="lg:col-span-2 space-y-4">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <StatCard label="Active Edit Sessions" value={val(stats?.active_edit_sessions)} accent="devcollab" icon={GitBranch} />
          <StatCard label="Conflicts Predicted" value={val(stats?.conflicts_predicted)} accent="warning" icon={Activity} />
          <StatCard label="Open Incidents" value={val(stats?.open_incidents)} accent="aiops" icon={ServerCog} />
          <StatCard label="Linked Incidents" value={val(stats?.linked_incidents)} accent="success" icon={Link2} />
        </div>

        <div className="bg-base-surface border border-base-border rounded-xl p-6">
          <h2 className="font-display text-base font-semibold text-ink-primary mb-2">
            Software Development Lifecycle — Unified Coordination
          </h2>
          <p className="text-sm text-ink-muted leading-relaxed">
            This engine coordinates two phases of the SDLC under one Decision Engine:{" "}
            <span className="text-accent-devcollab">Dev-Collaboration</span> during development
            (preventing merge conflicts before they happen) and{" "}
            <span className="text-accent-aiops">AIOps Incident Response</span> in production
            (detecting, diagnosing, and auto-resolving incidents). The Coordinator Agent links
            the two — tracing production incidents back to risky recent commits.
          </p>
          {error && (
            <p className="text-xs text-ink-faint mt-4">
              Backend not reachable yet — start the FastAPI server to see live counts here.
            </p>
          )}
        </div>

        <KnowledgeBasePanel />
      </div>

      <div className="lg:col-span-1">
        <DecisionTrail />
      </div>
    </div>
  );
}
