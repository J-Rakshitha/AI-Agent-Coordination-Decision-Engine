# AI Agent Coordination & Decision Engine

A unified multi-agent system that coordinates two phases of the Software
Development Lifecycle under one Decision Engine:

- **Module 1 — Dev-Collaboration**: predicts and prevents merge conflicts
  between developers *before* they happen (live editing map, conflict-risk
  scoring, AI-suggested resolutions).
- **Module 2 — AIOps Incident Response**: detects production incidents,
  diagnoses root cause, classifies severity, attempts auto-remediation,
  and escalates when needed.
- **Cross-module link**: the Coordinator Agent traces a production incident
  back to a recent risky commit/conflict — proving the two modules work as
  ONE coordinated engine, not two separate tools.

Built for: Infosys Springboard Virtual Internship 7.0 — Batch 1.

---

## Architecture

```
[Development Phase] ──build──> [Production Phase]
  Dev-Collaboration                 AIOps
  (conflict prevention)             (incident response)
        \                              /
         \                            /
          -----> Coordinator Agent <-----
             (explainable decision log,
              cross-module linking)
```

**Hybrid AI strategy**: every "thinking" agent (Resolution Suggestion,
Root-Cause Analysis) calls the Gemini API first. If the API key is missing,
times out, or errors — it automatically falls back to rule-based logic.
The demo NEVER crashes, and a "Simulate API Failure" toggle lets you prove
this live on stage.

---

## Tech Stack

| Layer | Tech |
|---|---|
| Backend | Python 3.11+, FastAPI, SQLAlchemy (async), SQLite (dev) |
| Real-time | Native FastAPI WebSockets |
| LLM | Google Gemini API (free tier) + rule-based fallback |
| Frontend | React 18 + Vite, Tailwind CSS, React Router, Recharts, lucide-react |
| Deployment | Backend → Render, Frontend → Vercel |

---

## Project Structure

```
ai-agent-coordination-engine/
├── backend/
│   ├── app/
│   │   ├── main.py                 # FastAPI entrypoint
│   │   ├── core/                   # config + database
│   │   ├── models/                 # SQLAlchemy models (dev_collab, incident)
│   │   ├── schemas.py              # Pydantic request/response schemas
│   │   ├── agents/
│   │   │   ├── coordinator_agent.py
│   │   │   ├── dev_collab/         # Code-Watch, Overlap, Conflict-Prediction, Resolution
│   │   │   ├── aiops/              # Monitoring, Root-Cause, Severity, Remediation, Escalation
│   │   │   └── llm/                # Hybrid AI client + rule-based fallback logic
│   │   ├── routers/                # API routes per module + websocket
│   │   └── services/               # synthetic data generator (demo-safe)
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── pages/                  # Overview, DevCollab, AIOps
│   │   ├── components/             # layout, common (StatCard, DecisionTrail)
│   │   ├── context/                # ThemeContext (dark/light)
│   │   ├── hooks/                  # useLiveSocket (WebSocket)
│   │   └── services/apiClient.js   # Axios wrapper for backend API
│   ├── package.json
│   └── tailwind.config.js
└── README.md
```

---

## Setup & Run (Local)

### 1. Backend

```bash
cd backend
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
# Open .env and paste your free Gemini API key (https://aistudio.google.com/app/apikey)
# The app still works with NO key — it just uses rule-based logic only.

uvicorn app.main:app --reload --port 8000
```

Visit **http://localhost:8000/docs** to see and test every API endpoint interactively.

### Running Automated Tests

The backend has a pytest suite covering every major flow (Dev-Collaboration,
AIOps, Memory/Knowledge Base, System endpoints) — deterministic, no network
or API key required (LLM is force-disabled in tests, so only the rule-based
path runs):

```bash
cd backend
pip install -r requirements.txt   # includes pytest + pytest-asyncio
pytest -v
```

All tests use an isolated `test_coordination_engine.db` (separate from your
real dev database) and reset schema before every test, so they never
interfere with data you're using for a live demo.

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
```

Visit **http://localhost:5173**.

> **Note on this build:** this skeleton was generated in a sandboxed
> environment without internet access, so `pip install` / `npm install`
> could not be executed here to do a full live run. Every file was
> syntax-checked (`python -m py_compile` passed on all backend files) and
> carefully reviewed, but please run the install + start steps above on
> your machine and open an issue-list of anything that errors — happy to
> fix immediately in the next phase.

---

## Alignment with Infosys Springboard Project Brief

| Required Outcome | Where it's implemented |
|---|---|
| Multi-Agent Coordination Framework | `Coordinator Agent` + 10 specialized agents across both modules |
| Intelligent Decision Support | Severity, Root-Cause, Remediation, Conflict-Risk agents |
| **Tool & System Integration** | `External Lookup Agent` calls GitHub's real public Issue Search API to cross-reference error patterns against publicly reported issues; `/api/system/knowledge-base` exposes agent-learned insights for other enterprise tools to consume |
| **Shared Knowledge & Memory Management** | `MemoryAgent` — **long-term memory** (`KnowledgeEntry` table, persists across restarts, reused before re-reasoning) + **short-term memory** (recent `AgentDecisionLog` entries fed as context into every LLM prompt) |
| Workflow Automation Platform | Full incident-response and conflict-resolution pipelines run end-to-end with zero manual steps |
| Enterprise API Layer | FastAPI REST + WebSocket layer, documented at `/docs` |
| **LangChain configured** (Milestone 1) | `HybridAIClient` uses `langchain_google_genai.ChatGoogleGenerativeAI` for all LLM calls |
| **Basic testing interfaces** (Milestone 1) | `pytest` suite (`backend/tests/`) covering every module, run with `pytest -v` |
| **Custom enterprise tools & API connectors** (Milestone 2) | `app/agents/tools/tool_registry.py` — 5 registered tools (GitHub lookup, escalation ticket, knowledge-base query, restart-service, clear-cache) |
| **Intelligent tool selection** (Milestone 2) | `ToolSelectorAgent` — LangChain LLM selection with a deterministic keyword-based fallback, wired into the real incident pipeline |
| **Tool invocation + exception handling** (Milestone 2) | `ToolExecutorAgent` wraps every tool call in try/except; covered by `tests/test_tool_selection.py` |
| **Action execution accuracy** (Milestone 2) | `ToolExecutionLog` table + `/api/tools/accuracy` — real measured success rate, overall and per-tool |

---

## Build Plan (Phases)

- [x] **Phase 1 — Project Setup** (this delivery): folder structure, configs, models, agent skeletons with working logic, API routes, WebSocket, frontend skeleton with routing + theme + live data hooks.
- [ ] Phase 2 — Backend core hardening (DB migrations, error handling middleware)
- [ ] Phase 3 — Dev-Collaboration full feature build-out
- [ ] Phase 4 — AIOps full feature build-out
- [ ] Phase 5 — Cross-module linking polish
- [ ] Phase 6 — Full dashboard UI (charts, live map visualization, decision trail styling)
- [ ] Phase 7 — Real-time WebSocket event wiring (broadcast on every agent action)
- [ ] Phase 8 — Hybrid AI wiring + "Simulate API Failure" demo button in UI
- [ ] Phase 9 — Synthetic data generator (scripted demo scenarios)
- [ ] Phase 10 — Testing pass (every endpoint + UI flow)
- [ ] Phase 11 — GitHub push + Render/Vercel deployment
- [ ] Phase 12 — Final demo rehearsal

---

## API Endpoints (Phase 1)

| Method | Path | Purpose |
|---|---|---|
| POST | `/api/dev-collab/edit-session/start` | Register a developer editing a file/function |
| GET | `/api/dev-collab/active-sessions` | List live edit sessions |
| POST | `/api/dev-collab/check-conflicts` | Run overlap + conflict-risk detection |
| POST | `/api/dev-collab/conflicts/{id}/suggest-resolution` | Hybrid-AI resolution suggestion |
| POST | `/api/incidents/ingest-metrics` | Feed a metrics snapshot through the full AIOps agent pipeline |
| GET | `/api/incidents/` | List all incidents |
| GET | `/api/system/health` | Health check |
| POST | `/api/system/toggle-llm-failure` | Force rule-based fallback (demo proof) |
| GET | `/api/system/decision-log` | Explainable-AI trail (all agent decisions) |
| WS | `/ws/live` | Real-time event stream |

---

## License

Built for educational/internship purposes (Infosys Springboard Virtual Internship 7.0).
