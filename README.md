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

### Milestone 3 — Agent Coordination & Memory Systems (Weeks 5–6)
- **Specialized agents** with distinct business roles across Dev-Collaboration and AIOps
- **Code Review Agent** — flags code-quality/style risks when conflicts are predicted
- **Notification Agent** — team alerts via WebSocket + email (simulated or real SMTP)
- **Coordinator Agent** — explainable decision log + cross-module Dev→Production incident linking
- **Short-term memory** — recent agent decisions (`AgentDecisionLog`) fed as context to reasoning agents
- **Long-term memory** — persistent `KnowledgeEntry` store; agents recall past patterns before LLM/rules
- **Agent communication** — orchestrated pipelines, WebSocket broadcasts, REST APIs for memory/decisions
- Endpoints: `GET /api/system/decision-log`, `GET /api/system/knowledge-base`
- Dashboard: **Agent Decision Trail** + **Shared Knowledge Base** panels on Overview page

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
│   │   ├── mcp_server.py              # Phase D — MCP tool layer
│   │   ├── core/                        # config, database, security, deps
│   │   ├── models/                      # dev_collab, incident, user, monitoring
│   │   ├── agents/
│   │   │   ├── dev_collab/              # GitHub Integration Agent (Phase A)
│   │   │   ├── aiops/                   # Server Monitor Agent (Phase B)
│   │   │   └── tools/                   # Tool Registry + Selector + Executor
│   │   ├── routers/                     # auth, monitoring, incidents, dev-collab
│   │   └── services/                    # monitoring_scheduler, incident_pipeline
│   ├── run.ps1                          # Windows one-click backend start
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── pages/                       # Overview, DevCollab, AIOps
│   │   ├── context/AuthContext.jsx      # Phase C — login state
│   │   └── components/common/LoginModal.jsx
│   ├── run.ps1                          # Windows one-click frontend start
│   └── package.json
└── README.md
```

---

## Setup & Run (Local)

### 1. Backend (Port 8000)

```bash
cd backend
cp .env.example .env
# Edit .env — add GEMINI_API_KEY, GITHUB_TOKEN (optional)
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
python -m pytest -v
```

All tests use an isolated `test_coordination_engine.db` (separate from your
real dev database) and reset schema before every test, so they never
interfere with data you're using for a live demo.

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
| Multi-Agent Coordination Framework | Coordinator Agent + 10+ specialized agents |
| Intelligent Decision Support | Severity, Root-Cause, Remediation, Conflict-Risk agents |
| Tool & System Integration | External Lookup Agent, Tool Registry, MCP Layer (Phase D) |
| Shared Knowledge & Memory Management | MemoryAgent + KnowledgeEntry table |
| Workflow Automation Platform | End-to-end incident + conflict pipelines |
| Enterprise API Layer | FastAPI REST + WebSocket + MCP |
| Real-time Monitoring (Phase B) | Background scheduler + Server Monitor Agent |
| Multi-user Access (Phase C) | JWT auth with role-based demo users |
| LangChain configured | HybridAIClient via langchain_google_genai |
| Custom enterprise tools & API connectors | `tool_registry.py` — 5 registered tools |
| Intelligent tool selection | `ToolSelectorAgent` — LLM + keyword fallback |
| Testing | pytest suite — `python -m pytest -v` |

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
