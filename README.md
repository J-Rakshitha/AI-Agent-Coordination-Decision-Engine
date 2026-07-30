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

**GitHub:** [J-Rakshitha/AI-Agent-Coordination-Decision-Engine](https://github.com/J-Rakshitha/AI-Agent-Coordination-Decision-Engine)

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

**Hybrid AI strategy**: every "thinking" agent calls the Gemini API first.
If the API key is missing, times out, or errors — it automatically falls back
to rule-based logic. The demo NEVER crashes.

---

## Implementation Phases (A–D)

| Phase | Feature | Status |
|-------|---------|--------|
| **A** | Real GitHub Integration — live PR conflict detection | ✅ Complete |
| **B** | Real Server Monitoring — background HTTP probes (own backend + external API) | ✅ Complete |
| **C** | Multi-user Login — JWT auth with demo users | ✅ Complete |
| **D** | MCP Layer — industry-standard tool exposure via Model Context Protocol | ✅ Complete |
| **M3** | Agent Coordination & Memory — specialized agents, shared memory, cross-module linking | ✅ Complete |

### Milestone 3 — Agent Coordination & Memory Systems (Weeks 5–6) ✅

Milestone 3 delivers a **multi-agent coordination engine** where specialized agents
collaborate through pipelines, shared memory, and a central Coordinator — not isolated
single-purpose scripts.

#### Agent Role Matrix

| Agent | Module | Business Role |
|-------|--------|---------------|
| **Overlap Detection Agent** | Dev-Collab | Finds developers editing the same file/function |
| **Conflict Prediction Agent** | Dev-Collab | Scores merge-conflict risk (0–100%) |
| **Code Review Agent** | Dev-Collab | Flags code-quality/style issues before merge |
| **Resolution Suggestion Agent** | Dev-Collab | Recommends how developers should coordinate |
| **GitHub Integration Agent** | Dev-Collab | Syncs live PR conflicts from a real GitHub repo |
| **Code Watch Agent** | Dev-Collab | Tracks live developer edit sessions |
| **Monitoring Agent** | AIOps | Detects metric anomalies (threshold-based) |
| **Root-Cause Analysis Agent** | AIOps | Diagnoses why an incident happened (LLM + memory) |
| **Severity Agent** | AIOps | Classifies P1 / P2 / P3 with SLA deadlines |
| **Tool Selector Agent** | AIOps | Picks the best remediation tool for the situation |
| **Tool Executor Agent** | AIOps | Invokes tools with exception-safe execution |
| **External Lookup Agent** | AIOps | Searches GitHub public issues for known patterns |
| **Notification Agent** | Both | Delivers team alerts (WebSocket + email) |
| **Coordinator Agent** | Both | Logs all decisions + links Dev conflicts → Production incidents |
| **Memory Agent** | Both | Manages short-term and long-term shared memory |

#### Agent Communication Patterns

```
Orchestrator:  CoordinatorAgent — logs every decision, cross-module linking
Pipeline:      Detect → Code Review → Notify → Resolve → Notify  (Dev-Collab)
               Monitor → Root Cause → Severity → Tool → Link → Notify  (AIOps)
Shared State:  SQLite DB — ConflictEvent, CommitLog, KnowledgeEntry, AgentDecisionLog, TeamNotification
Real-time:     WebSocket /ws/live — live dashboard updates without page refresh
```

#### Memory Architecture

| Type | Storage | Used By | Purpose |
|------|---------|---------|---------|
| **Short-term** | `AgentDecisionLog` table | RootCause, Resolution, ToolSelector agents | Recent situational context within a session |
| **Long-term** | `KnowledgeEntry` table | RootCause, Resolution, CodeReview agents | Persistent patterns — system gets sharper over time |

Agents call `MemoryAgent.recall_knowledge()` **before** falling back to generic rules.
Repeated patterns reinforce entries (`success_count` increments).

#### Milestone 3 API Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/system/decision-log` | Explainable-AI trail (all agent decisions) |
| GET | `/api/system/knowledge-base` | Long-term memory entries |
| GET | `/api/system/notifications` | Team notification delivery log |

#### Dashboard Panels (Overview page)

- **Agent Decision Trail** — every agent action with LLM vs Rule-based badge
- **Shared Knowledge Base** — long-term memory visualized with `seen N×` counts
- **Stat cards** — Active Sessions, Conflicts, Open Incidents, **Linked Incidents**

### 5-Minute Live Demo Script (Milestone 3)

| Step | Page | Action | What to show |
|------|------|--------|--------------|
| 1 | Overview | Open dashboard | Stat cards + Knowledge Base + Decision Trail |
| 2 | Dev-Collaboration | **Simulate Conflict** | Conflict Prediction → Code Review → Notification agents |
| 3 | Dev-Collaboration | **Get AI Suggestion** | Conflict RESOLVED + commit created |
| 4 | AIOps | **Simulate Incident** | Monitoring → Root Cause → Severity → Tool → Notification |
| 5 | Overview | Refresh | **Linked Incidents > 0** + Knowledge Base entries growing |
| 6 | Header | Toggle **Simulate API Failure** ON → repeat Step 2 | Proves Rule-based fallback — system never crashes |

**Talking point for evaluators:**
> "A Dev-Collab conflict on `payment_service.py` was later linked to a P1 production
> incident on `checkout-service` — the Coordinator Agent traced it back to the risky merge."

### What's Real vs Demo (Honest Architecture Notes)

| Component | Real / Live | Demo / Simulated |
|-----------|-------------|------------------|
| SQLite database persistence | ✅ Real | |
| WebSocket live updates | ✅ Real-time | |
| GitHub PR conflict sync | ✅ Real API | |
| Background server monitoring | ✅ Real HTTP probes | |
| JWT authentication | ✅ Real | |
| MCP tool layer | ✅ Industry standard | |
| Hybrid LLM (Gemini) | ✅ Real when API key set | Rule-based fallback always available |
| Short/long-term memory | ✅ Real DB-backed | |
| Cross-module incident linking | ✅ Real correlation logic | |
| **Simulate Conflict** button | | ⚠️ Demo trigger (random file/function) |
| **Simulate Incident** button | | ⚠️ Demo trigger (random metrics) |
| Email notifications | ✅ Real if SMTP configured | Simulated log in DB by default |
| Runbook tools (restart/clear cache) | | ⚠️ Simulated actions (safe for demo) |

Demo buttons exist so the presentation never depends on external uptime.
In production, replace them with real metric pipelines and GitHub webhooks.

### Phase A — Real GitHub Integration
- Connects to a real GitHub repo via REST API
- Detects **confirmed** conflicts (`mergeable_state: dirty`) and **predicted** conflicts (2+ PRs touching same file)
- Endpoint: `POST /api/dev-collab/github/sync`

### Phase B — Real Server Monitoring
- Background scheduler probes every 30 seconds:
  - **Own backend:** `http://127.0.0.1:8000/api/system/health`
  - **External service:** `https://api.github.com`
- Stores real health snapshots in DB; broadcasts via WebSocket
- Auto-triggers incident pipeline on anomalies
- Endpoints: `GET /api/monitoring/status`, `GET /api/monitoring/history/{service_name}`

### Phase C — Multi-user Login
- JWT-based authentication (register, login, profile)
- Demo users seeded on startup:

| Email | Password | Role |
|-------|----------|------|
| `priya@infosys.com` | `demo123` | developer |
| `arjun@infosys.com` | `demo123` | developer |
| `admin@infosys.com` | `admin123` | admin |

- Endpoints: `POST /api/auth/login`, `GET /api/auth/me`, `GET /api/auth/users`
- UI: optional Sign In modal in header (app works without login too)

### Phase D — MCP Layer
- Exposes all enterprise tools via [Model Context Protocol](https://modelcontextprotocol.io)
- Run: `cd backend && python -m app.mcp_server`
- Tools: `github_issue_lookup`, `restart_service`, `clear_cache`, `check_service_health`, `sync_github_conflicts`, `select_and_execute_tool`, etc.

---

## Tech Stack

| Layer | Tech |
|---|---|
| Backend | Python 3.11+, FastAPI, SQLAlchemy (async), SQLite (dev) |
| Real-time | Native FastAPI WebSockets |
| Auth | JWT (python-jose) + bcrypt |
| Monitoring | Background asyncio scheduler + httpx probes |
| MCP | `mcp` Python SDK (FastMCP) |
| LLM | Google Gemini API (free tier) + rule-based fallback |
| Frontend | React 18 + Vite, Tailwind CSS, React Router, lucide-react |
| Deployment | Backend → Render, Frontend → Vercel |

---

## Ports

| Port | Service |
|------|---------|
| **8000** | Backend API + WebSocket (`ws://localhost:8000/ws/live`) |
| **5173** | Frontend UI (dashboard) |

---

## Project Structure

```
ai-agent-coordination-engine/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── mcp_server.py                 # Phase D — MCP tool layer
│   │   ├── core/                           # config, database, security, deps
│   │   ├── models/                         # dev_collab, incident, memory, notification, user
│   │   ├── agents/
│   │   │   ├── coordinator_agent.py        # M3 — orchestrator + cross-module linking
│   │   │   ├── memory_agent.py             # M3 — short/long-term memory
│   │   │   ├── notification_agent.py       # M3 — WebSocket + email alerts
│   │   │   ├── dev_collab/                 # Conflict, Code Review, GitHub, Resolution agents
│   │   │   ├── aiops/                      # Monitoring, Root Cause, Severity, Escalation agents
│   │   │   └── tools/                      # Tool Registry + Selector + Executor (M2)
│   │   ├── routers/                        # auth, monitoring, incidents, dev-collab, system
│   │   └── services/                       # monitoring_scheduler, incident_pipeline
│   ├── tests/
│   │   ├── test_milestone3.py              # M3 — coordination, memory, notifications
│   │   └── ...                             # 32 tests total
│   ├── run.ps1                             # Windows one-click backend start
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── pages/                          # Overview, DevCollab, AIOps
│   │   ├── components/common/              # DecisionTrail, KnowledgeBasePanel, LoginModal
│   │   └── context/                        # AuthContext, LiveSocketContext
│   ├── run.ps1                             # Windows one-click frontend start
│   └── package.json
└── README.md
```

---

## Setup & Run (Local)

### 1. Backend (Port 8000)

```bash
cd backend
cp .env.example .env
```

Edit `backend/.env` — set your Gemini key on **line 17**:

```env
GEMINI_API_KEY=your_actual_key_here   # Get free key: https://aistudio.google.com/app/apikey
LLM_ENABLED=True
```

> **Never commit `.env`** — it is gitignored. Only commit `.env.example`.

```bash
pip install -r requirements.txt
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

**Windows (recommended):**
```powershell
cd backend
.\run.ps1
```

Visit **http://localhost:8000/docs** for interactive API docs.

### 2. Frontend (Port 5173)

```bash
cd frontend
npm install
npm run dev
```

**Windows:**
```powershell
cd frontend
.\run.ps1
```

Visit **http://localhost:5173**.

### 3. MCP Server (Phase D — optional)

```bash
cd backend
python -m app.mcp_server
```

### Running Tests

```bash
cd backend
python -m pytest -v                  # Full suite — 32 tests
python -m pytest tests/test_milestone3.py -v   # Milestone 3 only — 6 tests
```

All tests use an isolated `test_coordination_engine.db` (separate from your
real dev database) and reset schema before every test, so they never
interfere with data you're using for a live demo.

### Database Schema Note

If you pull new code that adds DB columns/tables and see a `500` error like
`no such column`, delete the old database and restart the backend:

```powershell
cd backend
del coordination_engine.db
.\run.ps1
```

The backend recreates all tables automatically on startup.

---

## API Endpoints

### System
| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/system/health` | Health check (also monitored by Phase B) |
| GET | `/api/system/stats` | Dashboard stat cards |
| GET | `/api/system/decision-log` | Explainable-AI trail |
| GET | `/api/system/knowledge-base` | Long-term agent memory |
| GET | `/api/system/notifications` | Team notification delivery log |
| POST | `/api/system/toggle-llm-failure` | Force rule-based fallback |

### Phase A — GitHub
| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/dev-collab/github/status` | GitHub connection status |
| POST | `/api/dev-collab/github/sync` | Sync live PR conflicts from real repo |

### Phase B — Monitoring
| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/monitoring/status` | Latest health snapshot per service |
| GET | `/api/monitoring/history/{service_name}` | Probe history |

### Phase C — Auth
| Method | Path | Purpose |
|--------|------|---------|
| POST | `/api/auth/login` | Login → JWT token |
| POST | `/api/auth/register` | Register new user |
| GET | `/api/auth/me` | Current user profile |
| GET | `/api/auth/users` | List demo users |

### Dev-Collaboration
| Method | Path | Purpose |
|--------|------|---------|
| POST | `/api/dev-collab/edit-session/start` | Register a developer editing a file/function |
| GET | `/api/dev-collab/active-sessions` | List live edit sessions |
| POST | `/api/dev-collab/check-conflicts` | Run overlap + conflict-risk detection |
| POST | `/api/dev-collab/simulate-demo-conflict` | One-click demo conflict scenario |
| POST | `/api/dev-collab/conflicts/{id}/suggest-resolution` | Hybrid-AI resolution suggestion |

### AIOps & Tools
| Method | Path | Purpose |
|--------|------|---------|
| POST | `/api/incidents/ingest-metrics` | Feed metrics through agent pipeline |
| POST | `/api/incidents/simulate` | Demo one-click incident |
| GET | `/api/incidents/` | List incidents |
| GET | `/api/tools/` | List registered enterprise tools |
| POST | `/api/tools/select-and-execute` | Intelligent tool selection |
| GET | `/api/tools/accuracy` | Tool execution accuracy stats |
| WS | `/ws/live` | Real-time event stream |

---

## Alignment with Infosys Springboard Project Brief

| Required Outcome | Where it's implemented |
|---|---|
| Multi-Agent Coordination Framework | Coordinator Agent + **15 specialized agents** |
| Intelligent Decision Support | Severity, Root-Cause, Code Review, Conflict-Risk, Tool Selector agents |
| Tool & System Integration | External Lookup Agent, Tool Registry, MCP Layer (Phase D) |
| Shared Knowledge & Memory Management | MemoryAgent — short-term (`AgentDecisionLog`) + long-term (`KnowledgeEntry`) |
| Workflow Automation Platform | Dev-Collab + AIOps end-to-end pipelines with Notification Agent |
| Enterprise API Layer | FastAPI REST + WebSocket + MCP |
| Agent Communication | Orchestrator + Pipeline + Shared DB blackboard (Milestone 3) |
| Real-time Monitoring (Phase B) | Background scheduler + Server Monitor Agent |
| Multi-user Access (Phase C) | JWT auth with role-based demo users |
| LangChain configured | HybridAIClient via langchain_google_genai |
| Custom enterprise tools & API connectors | `tool_registry.py` — 5 registered tools |
| Intelligent tool selection | `ToolSelectorAgent` — LLM + keyword fallback + short-term memory |
| Testing | **32 pytest tests** — `python -m pytest -v` |

---

## Build Plan

- [x] Phase 1 — Project Setup
- [x] **Phase A — Real GitHub Integration**
- [x] **Phase B — Real Server Monitoring (background probes)**
- [x] **Phase C — Multi-user Login (JWT)**
- [x] **Phase D — MCP Tool Layer**
- [x] Tool Integration (Milestone 2) — 5 enterprise tools + intelligent selection
- [x] **Milestone 3 — Agent Coordination & Memory Systems**
- [x] GitHub push — [repo live](https://github.com/J-Rakshitha/AI-Agent-Coordination-Decision-Engine)
- [ ] Render/Vercel deployment
- [ ] Final demo rehearsal

---

## License

Built for educational/internship purposes (Infosys Springboard Virtual Internship 7.0).
