import React, { useEffect, useState } from "react";
import { Clock, AlertTriangle, CheckCircle2 } from "lucide-react";

function formatDuration(totalSeconds) {
  const abs = Math.abs(totalSeconds);
  const h = Math.floor(abs / 3600);
  const m = Math.floor((abs % 3600) / 60);
  const s = abs % 60;
  if (h > 0) return `${h}h ${m}m ${s}s`;
  if (m > 0) return `${m}m ${s}s`;
  return `${s}s`;
}

export default function SlaCountdown({ slaDeadline, slaMinutes, status, resolvedAt, detectedAt, escalatedTo }) {
  const [now, setNow] = useState(() => Date.now());

  useEffect(() => {
    const timer = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(timer);
  }, []);

  if (!slaDeadline && !slaMinutes) return null;

  const deadlineMs = slaDeadline ? new Date(slaDeadline).getTime() : null;
  const remainingSec = deadlineMs ? Math.floor((deadlineMs - now) / 1000) : null;
  const isResolved = status === "auto_resolved" || status === "closed";
  const isEscalated = status === "escalated" || Boolean(escalatedTo);

  if (isResolved && resolvedAt && deadlineMs) {
    const resolvedMs = new Date(resolvedAt).getTime();
    const metSla = resolvedMs <= deadlineMs;
    return (
      <div
        className={`flex items-center gap-1.5 mt-2 text-[11px] rounded-md px-2 py-1 ${
          metSla ? "text-accent-success bg-accent-success/10" : "text-accent-warning bg-accent-warning/10"
        }`}
      >
        {metSla ? <CheckCircle2 size={12} /> : <AlertTriangle size={12} />}
        <span>
          {metSla ? "SLA met" : "SLA breached"} — resolved in{" "}
          {formatDuration(Math.floor((resolvedMs - new Date(detectedAt).getTime()) / 1000))}
          {slaMinutes ? ` (target: ${slaMinutes} min)` : ""}
        </span>
      </div>
    );
  }

  if (remainingSec == null) return null;

  const breached = remainingSec <= 0;

  return (
    <div className="mt-2 space-y-1">
      <div
        className={`flex items-center gap-1.5 text-[11px] rounded-md px-2 py-1 ${
          breached
            ? "text-red-400 bg-red-500/10 border border-red-500/30"
            : isEscalated
              ? "text-accent-warning bg-accent-warning/10"
              : "text-accent-aiops bg-accent-aiops/10"
        }`}
      >
        <Clock size={12} className={breached ? "animate-pulse" : ""} />
        <span>
          {breached ? "SLA breached" : "SLA countdown"}:{" "}
          {breached ? `over by ${formatDuration(remainingSec)}` : `${formatDuration(remainingSec)} remaining`}
          {slaMinutes ? ` (${slaMinutes} min SLA)` : ""}
        </span>
      </div>
      {escalatedTo && (
        <p className="text-[10px] text-ink-muted px-2">Escalated to: {escalatedTo}</p>
      )}
    </div>
  );
}
