import React from "react";

// NOTE: Tailwind scans source files statically for class NAMES, so classes
// built with string interpolation (e.g. `bg-accent-${accent}`) never get
// generated. Using a full, literal class map here avoids that trap.
const ACCENT_CLASSES = {
  devcollab: "bg-accent-devcollab/15 text-accent-devcollab",
  aiops: "bg-accent-aiops/15 text-accent-aiops",
  success: "bg-accent-success/15 text-accent-success",
  warning: "bg-accent-warning/15 text-accent-warning",
};

export default function StatCard({ label, value, accent = "devcollab", icon: Icon }) {
  const accentClass = ACCENT_CLASSES[accent] || ACCENT_CLASSES.devcollab;

  return (
    <div className="bg-base-surface border border-base-border rounded-xl p-4 flex items-center justify-between">
      <div>
        <p className="text-xs text-ink-muted mb-1">{label}</p>
        <p className="text-2xl font-display font-semibold text-ink-primary">{value}</p>
      </div>
      {Icon && (
        <div className={`w-9 h-9 rounded-lg flex items-center justify-center ${accentClass}`}>
          <Icon size={18} />
        </div>
      )}
    </div>
  );
}
