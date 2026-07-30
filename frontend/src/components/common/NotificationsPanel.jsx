import React, { useCallback, useEffect, useState } from "react";
import { Bell, Mail, Radio } from "lucide-react";
import { getNotifications } from "../../services/apiClient";
import { useLiveSocketContext } from "../../context/LiveSocketContext";

const eventLabel = {
  conflict_detected: "Conflict Detected",
  conflict_resolved: "Conflict Resolved",
  incident_created: "Incident Created",
};

const moduleAccent = {
  dev_collab: "text-accent-devcollab",
  aiops: "text-accent-aiops",
};

function channelIcon(channel) {
  if (channel === "websocket") return Radio;
  return Mail;
}

function channelLabel(channel) {
  if (channel === "websocket") return "Live";
  if (channel === "email") return "Email";
  return "Email (simulated)";
}

export default function NotificationsPanel() {
  const [entries, setEntries] = useState([]);
  const [error, setError] = useState(false);
  const { lastEvent } = useLiveSocketContext();

  const load = useCallback(() => {
    getNotifications()
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

  const visible = entries.filter((n) => n.channel !== "websocket").slice(0, 12);

  return (
    <div className="bg-base-surface border border-base-border rounded-xl p-4">
      <h2 className="text-sm font-semibold text-ink-primary mb-1 flex items-center gap-2">
        <Bell size={16} className="text-accent-warning" />
        Team Notifications
      </h2>
      <p className="text-xs text-ink-faint mb-3">
        Alerts delivered by the Notification Agent — WebSocket live updates plus email delivery
        records (real SMTP when configured, otherwise simulated in DB).
      </p>

      {error && (
        <p className="text-xs text-ink-muted">Backend not reachable — start the FastAPI server.</p>
      )}

      {!error && visible.length === 0 && (
        <p className="text-xs text-ink-muted">
          No team alerts yet — simulate a conflict or incident to see notifications here.
        </p>
      )}

      <div className="space-y-2">
        {visible.map((n) => {
          const Icon = channelIcon(n.channel);
          return (
            <div key={n.id} className="bg-base-bg border border-base-border rounded-lg px-3 py-2">
              <div className="flex items-center justify-between text-[11px] mb-1">
                <span className={`font-medium ${moduleAccent[n.module] || "text-ink-primary"}`}>
                  {eventLabel[n.event_type] || n.event_type}
                </span>
                <span className="flex items-center gap-1 text-ink-faint">
                  <Icon size={10} />
                  {channelLabel(n.channel)}
                </span>
              </div>
              <p className="text-xs text-ink-primary font-medium mb-0.5">{n.subject}</p>
              <p className="text-[11px] text-ink-muted truncate">{n.recipient}</p>
              <p className="text-[11px] text-ink-faint mt-1">
                {new Date(n.created_at).toLocaleString()}
              </p>
            </div>
          );
        })}
      </div>
    </div>
  );
}
