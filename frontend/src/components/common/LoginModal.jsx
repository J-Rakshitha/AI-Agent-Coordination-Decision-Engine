import React, { useState } from "react";
import { X, LogIn, Loader2 } from "lucide-react";
import { useAuth } from "../../context/AuthContext";

const DEMO_ACCOUNTS = [
  { email: "priya@infosys.com", password: "demo123", label: "Priya Sharma (Developer)" },
  { email: "arjun@infosys.com", password: "demo123", label: "Arjun Mehta (Developer)" },
  { email: "admin@infosys.com", password: "admin123", label: "Admin User" },
];

export default function LoginModal({ open, onClose }) {
  const { login } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  if (!open) return null;

  async function handleSubmit(e) {
    e.preventDefault();
    setSubmitting(true);
    setError("");
    try {
      await login(email, password);
      onClose();
    } catch {
      setError("Invalid email or password.");
    } finally {
      setSubmitting(false);
    }
  }

  function quickLogin(account) {
    setEmail(account.email);
    setPassword(account.password);
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50" onClick={onClose}>
      <div
        className="bg-base-surface border border-base-border rounded-xl p-5 w-full max-w-sm shadow-xl"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-sm font-semibold text-ink-primary flex items-center gap-2">
            <LogIn size={16} />
            Sign In
          </h2>
          <button onClick={onClose} className="text-ink-muted hover:text-ink-primary">
            <X size={16} />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-3">
          <input
            type="email"
            placeholder="Email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="w-full text-xs bg-base-bg border border-base-border rounded-lg px-3 py-2 text-ink-primary"
            required
          />
          <input
            type="password"
            placeholder="Password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="w-full text-xs bg-base-bg border border-base-border rounded-lg px-3 py-2 text-ink-primary"
            required
          />
          {error && <p className="text-xs text-accent-aiops">{error}</p>}
          <button
            type="submit"
            disabled={submitting}
            className="w-full flex items-center justify-center gap-2 text-xs py-2 rounded-lg bg-accent-devcollab/15 text-accent-devcollab border border-accent-devcollab/30 hover:bg-accent-devcollab/25 disabled:opacity-50"
          >
            {submitting ? <Loader2 size={14} className="animate-spin" /> : <LogIn size={14} />}
            Sign In
          </button>
        </form>

        <div className="mt-4 pt-3 border-t border-base-border">
          <p className="text-[10px] text-ink-faint mb-2">Demo accounts (optional — app works without login):</p>
          <div className="space-y-1">
            {DEMO_ACCOUNTS.map((a) => (
              <button
                key={a.email}
                type="button"
                onClick={() => quickLogin(a)}
                className="w-full text-left text-[11px] px-2 py-1 rounded-md text-ink-muted hover:bg-base-bg hover:text-ink-primary transition-colors"
              >
                {a.label}
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
