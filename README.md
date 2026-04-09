# MedAgent

A self-hosted, production-grade clinical intelligence platform built on a deployed multi-agent architecture with long-term and short-term memory, conversational checkpoints, and agentic orchestration patterns.

---

## What This Project Is

MedAgent is a clinical AI platform where a patient case enters the system and a supervisor agent decomposes it, routes it, and dispatches specialized sub-agents to handle every layer of reasoning in parallel or sequence. Every agent has a single job. No overlapping responsibilities. The system never loses state, never forgets prior sessions, and never lets output leave without a human confirming it.

This is not a chatbot. It is a full agentic orchestration system designed for clinical, legal, and high-stakes environments where accuracy, traceability, and data sovereignty are non-negotiable.

---

## Core Architecture Patterns Implemented

### 1. Multi-Agent Orchestration (LangGraph Supervisor Pattern)

The system uses a LangGraph supervisor graph. One supervisor agent receives the input and decides which sub-agents to invoke, in what order, and whether they run in parallel or sequentially. Each sub-agent is a node in the graph. Edges between nodes are conditional, meaning the supervisor re-evaluates routing after each agent completes.

Agents in the system:

- **Intake Agent** - Parses unstructured clinical notes. Extracts named entities: symptoms, medications, allergies, patient history references, dates. Outputs a structured JSON payload for downstream agents.
- **History Agent** - Queries the long-term vector memory store (Weaviate) for prior patient sessions, past diagnoses, and institutional case history. Uses role-scoped retrieval so it only surfaces records it is authorized to see.
- **Research Agent** - RAG pipeline over a local medical knowledge base (PubMed abstracts, clinical guidelines, drug reference sheets). Uses hybrid search: semantic similarity plus keyword BM25. Returns ranked evidence chunks with source citations.
- **Differential Agent** - Takes structured intake output plus retrieved evidence and generates a ranked differential diagnosis list. Runs a self-critique reflection loop: it generates an initial differential, then critiques its own output against the evidence, then revises. Loops up to 3 times.
- **Risk Agent** - Checks proposed treatments and medications against a drug interaction database tool. Flags contraindications, dosage concerns, and allergy conflicts. Runs as a tool-calling agent with structured output.
- **Summarizer Agent** - Produces the final structured SOAP note (Subjective, Objective, Assessment, Plan) formatted for clinical record entry. This output is held at a human-in-the-loop gate before it is written anywhere.
- **Supervisor Agent** - Orchestrates all of the above. Maintains the working memory object. Decides routing. Handles retries. Triggers the human gate before final output.

### 2. Long-Term Memory (Weaviate Vector Store)

Every completed case is embedded and stored in Weaviate after clinician approval. The History Agent queries this store at the start of every new session. Memory is patient-scoped and role-scoped. The embedding model runs locally via Ollama (no data leaves the machine).

What gets stored:
- Completed SOAP notes (approved by clinician)
- Extracted entity payloads from prior intake runs
- Research evidence chunks with source metadata
- Session summaries with timestamps and agent trace IDs

Retrieval uses hybrid search: cosine similarity on dense embeddings plus BM25 sparse search, combined with a reciprocal rank fusion score.

### 3. Short-Term Memory (Redis In-Session State)

Within a single active session, all agents share a working memory object stored in Redis. This object is passed between agents via the LangGraph state schema. It contains:
- The current patient context object
- Intermediate agent outputs (intake payload, retrieved evidence, draft differential)
- Agent status flags (which nodes have completed)
- The current reflection loop iteration count for the Differential Agent
- Any flags raised by the Risk Agent

Redis is also used for session caching: if a user reconnects mid-session, their in-progress graph state is restored from Redis before falling back to the PostgreSQL checkpoint.

### 4. Conversational Checkpoints (LangGraph Checkpointer on PostgreSQL)

Every node execution in the LangGraph graph writes a checkpoint to PostgreSQL via LangGraph's built-in SqliteSaver (development) or AsyncPostgresSaver (production). This means:

- If the server crashes mid-graph, the run resumes from the last completed node, not from scratch
- Every agent step is auditable: you can replay the exact sequence of decisions
- Checkpoint records include: thread ID, node name, input state, output state, timestamp
- The human-in-the-loop gate is implemented as a LangGraph interrupt: the graph pauses, writes a checkpoint, and waits for clinician confirmation before the Summarizer Agent runs

### 5. Agentic Orchestration Patterns Used

- **Supervisor pattern**: central router agent with conditional edge routing
- **Reflection loop**: Differential Agent critiques and revises its own output up to N iterations
- **Tool-calling agent**: Risk Agent uses structured tool calls against a drug interaction database
- **Human-in-the-loop (HITL)**: hard interrupt before final output leaves the system
- **Parallel fan-out**: History Agent and Research Agent run in parallel after Intake completes
- **RAG agent**: Research Agent with hybrid retrieval and reranking
- **Retry with backoff**: supervisor retries failed agent nodes up to 2 times before escalating

---

## Tech Stack

| Layer | Technology |
|---|---|
| Agent framework | LangGraph + LangChain |
| LLM inference | Ollama (local) with Llama 3 or Mistral |
| Long-term memory | Weaviate (local Docker) |
| Short-term memory | Redis |
| Checkpoint store | PostgreSQL |
| Backend API | FastAPI with SSE streaming |
| Frontend | React + Vite + Tailwind CSS |
| Containerization | Docker Compose |
| Frontend deploy | Vercel (free Hobby tier) |
| Backend deploy | Render (free web service) |

---

## Repo Structure

```
medagent/
├── backend/
│   ├── agents/
│   │   ├── supervisor.py         # Supervisor agent and routing logic
│   │   ├── intake.py             # Intake agent - entity extraction
│   │   ├── history.py            # History agent - long-term memory retrieval
│   │   ├── research.py           # Research agent - RAG pipeline
│   │   ├── differential.py       # Differential agent - reflection loop
│   │   ├── risk.py               # Risk agent - tool-calling drug checker
│   │   └── summarizer.py         # Summarizer agent - SOAP note output
│   ├── memory/
│   │   ├── long_term.py          # Weaviate client, embed, store, retrieve
│   │   ├── short_term.py         # Redis session state manager
│   │   └── schemas.py            # Weaviate collection schemas
│   ├── graph/
│   │   ├── builder.py            # LangGraph graph construction
│   │   ├── state.py              # Shared state schema (TypedDict)
│   │   ├── checkpointer.py       # PostgreSQL checkpoint setup
│   │   └── edges.py              # Conditional edge routing functions
│   ├── api/
│   │   ├── main.py               # FastAPI app entry point
│   │   ├── routes/
│   │   │   ├── cases.py          # POST /cases - submit a case
│   │   │   ├── stream.py         # GET /stream/{thread_id} - SSE agent stream
│   │   │   ├── approve.py        # POST /approve/{thread_id} - HITL gate
│   │   │   └── history.py        # GET /history/{patient_id} - past sessions
│   │   └── middleware.py         # CORS, auth headers
│   ├── tools/
│   │   ├── drug_checker.py       # Drug interaction tool for Risk Agent
│   │   └── pubmed_loader.py      # Script to load PubMed data into Weaviate
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── AgentStatusPanel.jsx   # Live agent progress stream
│   │   │   ├── CaseInput.jsx          # Case submission form
│   │   │   ├── SOAPOutput.jsx         # Final SOAP note display
│   │   │   ├── MemoryPanel.jsx        # Long-term memory hits display
│   │   │   ├── ApprovalGate.jsx       # HITL confirmation UI
│   │   │   └── CheckpointLog.jsx      # Audit trail display
│   │   ├── pages/
│   │   │   ├── Dashboard.jsx          # Main clinician dashboard
│   │   │   └── History.jsx            # Past sessions browser
│   │   ├── hooks/
│   │   │   └── useAgentStream.js      # SSE hook for live agent updates
│   │   ├── App.jsx
│   │   └── main.jsx
│   ├── index.html
│   ├── vite.config.js
│   ├── tailwind.config.js
│   ├── package.json
│   └── Dockerfile
├── docs/
│   ├── architecture.md           # Full architecture deep-dive
│   ├── memory-design.md          # Memory layer design decisions
│   ├── agent-prompts.md          # System prompts for each agent
│   └── deployment.md             # Render + Vercel deploy guide
├── docker-compose.yml            # Full local stack
├── docker-compose.prod.yml       # Production overrides
├── .env.example
├── .gitignore
└── README.md
```

---

## What Claude Code Needs To Build

When you hand this to Claude Code, tell it to build in this exact order:

### Phase 1 - Graph skeleton and state (start here)
- Build `backend/graph/state.py` - the TypedDict shared state schema that all agents read and write
- Build `backend/graph/checkpointer.py` - PostgreSQL checkpoint setup using LangGraph AsyncPostgresSaver
- Build `backend/graph/builder.py` - the full LangGraph graph with all 6 agent nodes and conditional edges
- Build `backend/graph/edges.py` - the routing functions the supervisor uses to decide next node
- Build stub versions of all 6 agents that just pass state through (no real logic yet)
- Wire FastAPI in `backend/api/main.py` with a single POST /cases endpoint
- Confirm the graph runs end to end with stubs before moving to Phase 2

### Phase 2 - Memory layers
- Build `backend/memory/short_term.py` - Redis session state manager with get, set, clear, and restore methods
- Build `backend/memory/schemas.py` - Weaviate collection schemas for PatientSession and EvidenceChunk
- Build `backend/memory/long_term.py` - Weaviate client with embed, upsert, hybrid search, and delete methods
- Connect History Agent to long-term memory retrieval
- Connect short-term memory to graph state so all agents share the Redis working object

### Phase 3 - Real agent logic
- Intake Agent: use spaCy or the LLM to extract entities from clinical notes
- History Agent: real Weaviate hybrid search queries with patient scoping
- Research Agent: RAG pipeline with chunk retrieval, reranking, and citation metadata
- Differential Agent: full reflection loop (generate, critique, revise, repeat up to 3 times)
- Risk Agent: tool-calling agent with drug interaction checker tool
- Summarizer Agent: structured SOAP note generation with Pydantic output schema

### Phase 4 - Streaming API and frontend
- Add SSE streaming endpoint in `backend/api/routes/stream.py` that emits agent node completion events
- Add HITL interrupt endpoint in `backend/api/routes/approve.py`
- Build React frontend with `useAgentStream` SSE hook
- Build AgentStatusPanel that shows which agent is running, completed, or waiting
- Build ApprovalGate component that renders when graph is paused at HITL interrupt
- Build SOAPOutput component for the final approved note

### Phase 5 - Fine-tuning and hardening
- Fine-tune Llama 3 or Mistral on de-identified clinical note examples using LoRA
- Swap Ollama model in agents to the fine-tuned adapter
- Add audit logging middleware: every agent call logged to PostgreSQL with thread ID, input hash, output hash, timestamp
- Add retry logic in supervisor for failed agent nodes
- Write integration tests for the full graph run using pytest + LangGraph test utilities

---

## Environment Variables

```
# LLM
OLLAMA_BASE_URL=http://ollama:11434
OLLAMA_MODEL=llama3

# Memory
WEAVIATE_URL=http://weaviate:8080
REDIS_URL=redis://redis:6379/0
POSTGRES_URL=postgresql+asyncpg://medagent:medagent@postgres:5432/medagent

# API
API_SECRET_KEY=changeme
CORS_ORIGINS=http://localhost:5173

# Render (production)
PORT=8000
```

---

## Local Development Setup

```bash
# Clone the repo
git clone https://github.com/YOUR_USERNAME/medagent.git
cd medagent

# Copy env
cp .env.example .env

# Start all services
docker compose up

# Backend runs at http://localhost:8000
# Frontend runs at http://localhost:5173
# Weaviate at http://localhost:8080
# Redis at localhost:6379
# Postgres at localhost:5432
```

---

## Deploy

**Frontend (Vercel)**
- Connect GitHub repo to Vercel
- Set root directory to `frontend`
- Add env var: `VITE_API_URL=https://your-render-url.onrender.com`
- Deploy

**Backend (Render)**
- Create new Web Service on Render
- Connect GitHub repo, set root to `backend`
- Set build command: `pip install -r requirements.txt`
- Set start command: `uvicorn api.main:app --host 0.0.0.0 --port $PORT`
- Add all env vars from `.env.example`
- Add a Render Postgres database and copy the connection string to `POSTGRES_URL`
- Add a Render Key Value (Redis) instance and copy URL to `REDIS_URL`

---

## Key Design Decisions and Why

**Why LangGraph over a custom agent loop**
LangGraph gives you checkpointing, conditional routing, and HITL interrupts as first-class primitives. Building this from scratch would take weeks and be less reliable.

**Why Weaviate for long-term memory**
Weaviate supports hybrid search (dense + sparse) natively and runs fully local via Docker. No API keys, no data leaving the machine.

**Why Redis for short-term memory instead of just passing state in the graph**
Redis lets agents share state across concurrent requests and allows session restore without replaying the full graph. It also gives you a fast pub/sub layer for the SSE stream.

**Why PostgreSQL for checkpoints instead of SQLite**
SQLite works for development but does not support concurrent writes from multiple workers. PostgreSQL scales to production without changing the checkpointer interface.

**Why SSE instead of WebSockets for the frontend stream**
SSE is unidirectional and much simpler to implement on both sides. The frontend only needs to receive agent events, not send them. WebSockets would add complexity with no benefit here.

**Why a hard HITL gate before Summarizer runs**
This is a clinical system. No AI output should enter a patient record without a human reviewing it. The LangGraph interrupt ensures this is enforced at the graph level, not just at the UI level.
