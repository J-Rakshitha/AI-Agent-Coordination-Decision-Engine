import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  LogIn, UserPlus, Loader2, GitBranch, ServerCog, Shield, Sparkles, Moon, Sun,
} from "lucide-react";
import { useAuth } from "../context/AuthContext";
import { useTheme } from "../context/ThemeContext";
import { register as apiRegister } from "../services/apiClient";

const DEMO_ACCOUNTS = [
  { email: "priya@infosys.com", password: "demo123", label: "Priya Sharma (Developer)" },
  { email: "arjun@infosys.com", password: "demo123", label: "Arjun Mehta (Developer)" },
  { email: "admin@infosys.com", password: "admin123", label: "Admin User" },
];

export default function LoginPage() {
  const { login } = useAuth();
  const { theme, toggleTheme } = useTheme();
  const navigate = useNavigate();
  const [mode, setMode] = useState("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    setSubmitting(true);
    setError("");
    try {
      if (mode === "login") {
        await login(email, password);
      } else {
        await apiRegister({ email, password, full_name: fullName, role: "developer" });
        await login(email, password);
      }
      navigate("/", { replace: true });
    } catch {
      setError(mode === "login" ? "Invalid email or password." : "Registration failed — email may already exist.");
    } finally {
      setSubmitting(false);
    }
  }

  function quickLogin(account) {
    setEmail(account.email);
    setPassword(account.password);
    setMode("login");
    setError("");
  }

  return (
    <div className="min-h-screen flex flex-col lg:flex-row bg-base-bg text-ink-primary overflow-hidden">
      <div className="relative flex-1 flex flex-col justify-center px-8 py-12 lg:px-14 min-h-[40vh] lg:min-h-screen">
        <div className="absolute inset-0 bg-gradient-to-br from-accent-devcollab/20 via-base-bg to-accent-aiops/20" />
        <div className="relative z-10 max-w-xl">
          <div className="flex items-center gap-4 mb-8">
            <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-accent-devcollab to-accent-aiops flex items-center justify-center shadow-lg">
              <Sparkles size={28} className="text-white" />
            </div>
            <div>
              <p className="text-[10px] uppercase tracking-[0.2em] text-accent-devcollab font-medium mb-1">
                Infosys Springboard Internship
              </p>
              <h1 className="font-display text-xl lg:text-2xl font-bold">Enterprise Workflow Platform</h1>
            </div>
          </div>
          <h2 className="text-lg font-semibold mb-2">Decision Automation System</h2>
          <p className="text-sm text-ink-muted mb-6">
            Dev-Collaboration + AIOps with 23 AI agents, human approval workflows, and real-time coordination.
          </p>
          <ul className="space-y-2 text-sm text-ink-secondary">
            <li className="flex items-center gap-2"><GitBranch size={14} className="text-accent-devcollab" /> Dev-Collab conflict prediction</li>
            <li className="flex items-center gap-2"><ServerCog size={14} className="text-accent-aiops" /> AIOps incident response</li>
            <li className="flex items-center gap-2"><Shield size={14} className="text-accent-success" /> Human-in-the-Loop approvals</li>
          </ul>
        </div>
      </div>

      <div className="flex-1 flex items-center justify-center px-6 py-10 lg:border-l border-base-border bg-base-surface/50">
        <div className="w-full max-w-md">
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-lg font-semibold">Welcome back</h3>
            <button type="button" onClick={toggleTheme} className="p-2 rounded-lg border border-base-border">
              {theme === "dark" ? <Sun size={16} /> : <Moon size={16} />}
            </button>
          </div>
          <div className="bg-base-surface border border-base-border rounded-2xl p-6 shadow-xl">
            <div className="flex gap-2 mb-5 p-1 bg-base-bg rounded-xl">
              <button type="button" onClick={() => setMode("login")} className={`flex-1 text-xs py-2 rounded-lg ${mode === "login" ? "bg-base-surface text-accent-devcollab" : "text-ink-muted"}`}>Sign In</button>
              <button type="button" onClick={() => setMode("register")} className={`flex-1 text-xs py-2 rounded-lg ${mode === "register" ? "bg-base-surface text-accent-devcollab" : "text-ink-muted"}`}>Sign Up</button>
            </div>
            <form onSubmit={handleSubmit} className="space-y-3">
              {mode === "register" && (
                <input type="text" placeholder="Full name" value={fullName} onChange={(e) => setFullName(e.target.value)} className="w-full text-sm px-4 py-2.5 rounded-xl bg-base-bg border border-base-border" required />
              )}
              <input type="email" placeholder="Email" value={email} onChange={(e) => setEmail(e.target.value)} className="w-full text-sm px-4 py-2.5 rounded-xl bg-base-bg border border-base-border" required />
              <input type="password" placeholder="Password" value={password} onChange={(e) => setPassword(e.target.value)} className="w-full text-sm px-4 py-2.5 rounded-xl bg-base-bg border border-base-border" required />
              {error && <p className="text-xs text-red-400">{error}</p>}
              <button type="submit" disabled={submitting} className="w-full flex items-center justify-center gap-2 text-sm py-2.5 rounded-xl bg-gradient-to-r from-accent-devcollab to-accent-aiops text-white font-medium disabled:opacity-50">
                {submitting ? <Loader2 size={16} className="animate-spin" /> : mode === "login" ? <LogIn size={16} /> : <UserPlus size={16} />}
                {mode === "login" ? "Sign In to Dashboard" : "Create Account"}
              </button>
            </form>
            <div className="mt-5 pt-4 border-t border-base-border">
              <p className="text-[10px] uppercase text-ink-faint mb-2">Quick demo login</p>
              {DEMO_ACCOUNTS.map((a) => (
                <button key={a.email} type="button" onClick={() => quickLogin(a)} className="w-full text-left text-xs px-3 py-2 rounded-lg text-ink-muted hover:bg-base-bg">{a.label}</button>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
