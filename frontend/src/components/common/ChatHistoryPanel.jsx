import React, { useCallback, useEffect, useState } from "react";
import { MessageSquare, Plus, Send, Loader2 } from "lucide-react";
import {
  listChatSessions,
  createChatSession,
  getChatMessages,
  askChatQuestion,
} from "../../services/apiClient";
import { useLiveSocketContext } from "../../context/LiveSocketContext";

export default function ChatHistoryPanel() {
  const [sessions, setSessions] = useState([]);
  const [activeId, setActiveId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [question, setQuestion] = useState("");
  const [asking, setAsking] = useState(false);
  const { lastEvent } = useLiveSocketContext();

  const loadSessions = useCallback(() => {
    listChatSessions()
      .then((res) => {
        setSessions(res.data);
        if (res.data.length && !activeId) setActiveId(res.data[0].id);
      })
      .catch(() => {});
  }, [activeId]);

  useEffect(() => { loadSessions(); }, [loadSessions]);
  useEffect(() => { if (lastEvent) loadSessions(); }, [lastEvent, loadSessions]);

  useEffect(() => {
    if (!activeId) { setMessages([]); return; }
    getChatMessages(activeId).then((res) => setMessages(res.data)).catch(() => {});
  }, [activeId]);

  async function handleNewSession() {
    const res = await createChatSession({ title: "New conversation" });
    setSessions((prev) => [res.data, ...prev]);
    setActiveId(res.data.id);
  }

  async function handleAsk(e) {
    e.preventDefault();
    if (!question.trim() || !activeId) return;
    setAsking(true);
    const q = question.trim();
    setQuestion("");
    setMessages((prev) => [...prev, { role: "user", content: q }]);
    try {
      const res = await askChatQuestion(activeId, q);
      setMessages((prev) => [...prev, { role: "assistant", content: res.data.answer }]);
      loadSessions();
    } catch {
      setMessages((prev) => [...prev, { role: "assistant", content: "Sorry, I could not answer that right now." }]);
    } finally {
      setAsking(false);
    }
  }

  return (
    <div className="bg-base-surface border border-base-border rounded-xl p-4">
      <div className="flex items-center justify-between mb-3">
        <h2 className="text-sm font-semibold text-ink-primary flex items-center gap-2">
          <MessageSquare size={16} className="text-accent-success" />
          Chat History & Long-Term Memory
        </h2>
        <button onClick={handleNewSession} className="flex items-center gap-1 text-xs px-2 py-1 rounded-lg border border-base-border">
          <Plus size={12} /> New
        </button>
      </div>
      <div className="flex gap-3 min-h-[220px]">
        <div className="w-36 shrink-0 space-y-1 overflow-y-auto">
          {sessions.map((s) => (
            <button key={s.id} onClick={() => setActiveId(s.id)} className={`w-full text-left text-[11px] px-2 py-1.5 rounded-lg truncate ${activeId === s.id ? "bg-accent-devcollab/15 text-accent-devcollab" : "text-ink-muted hover:bg-base-bg"}`}>
              {s.title}
            </button>
          ))}
        </div>
        <div className="flex-1 flex flex-col">
          <div className="flex-1 overflow-y-auto space-y-2 mb-2 pr-1">
            {messages.map((m, i) => (
              <div key={i} className={`text-xs px-3 py-2 rounded-lg max-w-[90%] ${m.role === "user" ? "ml-auto bg-accent-devcollab/15 text-ink-primary" : "bg-base-bg text-ink-secondary border border-base-border"}`}>
                {m.content}
              </div>
            ))}
          </div>
          <form onSubmit={handleAsk} className="flex gap-2">
            <input value={question} onChange={(e) => setQuestion(e.target.value)} placeholder="Ask a follow-up question..." className="flex-1 text-xs px-3 py-2 rounded-lg bg-base-bg border border-base-border" disabled={!activeId} />
            <button type="submit" disabled={asking || !activeId} className="px-3 py-2 rounded-lg bg-accent-devcollab/15 text-accent-devcollab disabled:opacity-50">
              {asking ? <Loader2 size={14} className="animate-spin" /> : <Send size={14} />}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
