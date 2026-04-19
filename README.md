# MedAgent
### AI-Powered Clinical Intelligence Platform. Structured SOAP Notes in Seconds.

**Live Demo:** *(deploying to Render + Vercel - link coming soon)*

---

## The Problem

A doctor sees twelve patients before lunch. For every one of them, she has to do the same mental work: read a messy handwritten note or listen to a rushed summary, recall whether this patient has been seen before, search her memory for the relevant clinical research, think through what conditions could explain the symptoms, check whether the medications are safe to combine, and then write a structured clinical note that goes into the record.

Every single time. For every patient.

This is not because the process is broken. It is because medicine is genuinely hard, and the cognitive load is enormous. A junior doctor seeing a complex case at 2am does not have the same depth of recall as a senior consultant who has seen a thousand similar patients. They both deserve the same support.

MedAgent was built to be that support. Not to replace clinical judgment. To give every clinician, regardless of experience or shift length, the same structured intelligence layer to work from.

---

## What MedAgent Does

You paste a clinical note - the kind a doctor would dictate or type during a busy shift. MedAgent reads it, thinks through it across six specialised AI agents, and hands back:

- A ranked list of possible diagnoses, each with a confidence score
- A summary of the patient's relevant prior history
- Flags for any safety concerns - drug interactions, allergies, emergency conditions
- A fully structured SOAP note ready for clinical review

Before any of that reaches the clinician, the system pauses. The clinician reviews the AI's findings and either approves or rejects. Only after that approval does the final note get generated. The AI never acts alone.

**SOAP Note** - the standard medical documentation format. Stands for Subjective (what the patient reports), Objective (what the clinician observes and measures), Assessment (the working diagnosis), and Plan (what happens next). Used in hospitals and clinics worldwide.

**Differential Diagnosis** - a ranked list of possible conditions that could explain a patient's symptoms. Standard clinical practice. MedAgent generates this list and scores each possibility.

---

## Three Demo Scenarios Built In

The frontend ships with three realistic clinical cases you can load and run immediately:

**Chest Pain / Inferior STEMI** - 62-year-old male, crushing central chest pain radiating to the left arm, diaphoresis, aspirin allergy, ST elevation on ECG. Tests the cardiac emergency detection and drug conflict flagging.

**Community-Acquired Pneumonia** - 45-year-old female, productive cough, fever, right lower lobe consolidation on CXR, documented penicillin anaphylaxis. Tests antibiotic allergy conflict detection.

**Pediatric Asthma Exacerbation** - 9-year-old male, SpO₂ 91%, salbutamol not working, peak flow 40% predicted. Tests pediatric-specific safety flags and age-appropriate dosing reminders.

These run through the full real AI pipeline - Groq, Qdrant, Redis, Postgres - not mocked data.

---

## Safety First - What Happens Before Any AI Runs

Every case submission goes through two layers of deterministic checks before a single AI agent is invoked. Deterministic means rule-based, not AI - these run in milliseconds and cannot be confused or manipulated.

**Input Validation Rules:**

| Rule | Detail |
|---|---|
| Patient ID format | 3–50 alphanumeric characters. Dashes allowed. |
| Note minimum length | 50 characters. Anything shorter cannot be meaningfully analysed. |
| Note maximum length | 10,000 characters. Prevents abuse and oversized prompt injection. |
| Trivial content | Repeated characters, test strings, and near-empty submissions are rejected. |
| Prompt injection | Known injection patterns ("ignore previous instructions", SQL commands, script tags) are blocked. |
| Rate limiting | 20 submissions per IP per hour on a rolling window. |

**Emergency Detection - before AI, every time:**

| Condition | What triggers it |
|---|---|
| Acute Cardiac Event | Chest pain, STEMI, diaphoresis, troponin elevation, cardiac arrest |
| Stroke / Neurological | Facial droop, aphasia, sudden weakness, thunderclap headache |
| Sepsis | qSOFA indicators, multi-organ dysfunction, lactate elevation |
| Suicidality / Self-Harm | Suicidal ideation, self-harm language, intentional overdose |
| Anaphylaxis / Airway | Anaphylaxis, angioedema, stridor, airway obstruction |
| Severe Respiratory Distress | SpO₂ below 90%, cyanosis, respiratory failure |
| Pediatric Patient | Any note involving a patient under 18 - triggers dosing reminders |
| Pregnancy | Obstetric keywords - triggers medication safety review flags |

These flags appear in the UI before the AI pipeline has even finished running.

---

## The Six AI Agents

**Agent 1 - Intake Parser**
Reads the raw clinical note and extracts every structured field: chief complaint, symptoms, medications, allergies, vitals, and history keywords. Outputs a clean JSON object that every downstream agent reads from. If data is missing, it says so rather than guessing.

**Agent 2 - History Retrieval** *(runs in parallel with Agent 3)*
Searches the patient's prior session history using semantic similarity - not keyword matching. Finds cases where the patient's current symptoms are conceptually related to past sessions, even if the words used are different. Returns the most relevant prior diagnoses and SOAP notes.

**Agent 3 - Research RAG** *(runs in parallel with Agent 2)*
Searches a medical evidence store using the patient's current symptoms and chief complaint as the query. Returns ranked evidence chunks grounding the differential in retrieved clinical research, not just the model's training data.

**Agent 4 - Differential Diagnosis**
Takes the structured intake, the history context, and the retrieved evidence. Generates a ranked differential with confidence scores. Then runs a self-critique loop - it evaluates its own output against the evidence and revises. Up to three iterations.

**Agent 5 - Risk Assessment**
Reviews the differential and medication list. Uses tool-calling to check drug interactions and allergy conflicts. Merges with the deterministic emergency flags from the guardrail layer. Any critical flag forces the HITL approval gate.

**Agent 6 - SOAP Summariser**
Runs only after the clinician approves. Generates the final structured SOAP note. Cannot be triggered autonomously. This is enforced at the graph level, not just in the UI.

---

## Guardrails and Responsible AI

**Human-in-the-Loop on every case.** The SOAP note is generated only after the clinician explicitly approves. This is a hard technical constraint enforced by LangGraph's interrupt mechanism - not a policy or a UI checkbox that can be skipped.

**HITL (Human-in-the-Loop)** - an AI design pattern requiring a human to review and confirm output before any consequential action. In MedAgent this cannot be bypassed programmatically.

**Mandatory medical disclaimer on all AI output.** Every differential, risk summary, and SOAP note carries the same disclaimer: AI-generated output for clinical decision support only. Not a substitute for professional clinical judgment. This cannot be removed.

**Critical flags force review.** Any critical-severity flag - cardiac event, stroke, suicidality, sepsis, anaphylaxis - makes the approval gate mandatory regardless of pipeline state.

**PII-safe audit logging.** Every case submission, agent completion, and clinician decision is logged in structured JSON. Patient IDs are one-way hashed (SHA-256). Raw clinical note content is never logged.

**PII (Personally Identifiable Information)** - data that can identify a specific person. In healthcare this is called PHI (Protected Health Information). HIPAA (US) and GDPR (EU/UK) set legal requirements for how PHI must be handled.

**Low-confidence output flagging.** Top diagnosis below 30% confidence → warning surfaced to clinician. Diagnoses below 5% confidence → filtered from display entirely.

**No autonomous action.** MedAgent produces recommendations. It does not file notes, prescribe medications, order tests, or communicate with patients.

---

## Taking This to Production with a Real Clinic

MedAgent is a fully working implementation of the architecture. Here is exactly what would need to happen to deploy it in a real clinical environment.

**Patient Data - EHR Integration**

Real patient notes come from EHR systems (Electronic Health Records). The two standards to connect:

- **HL7 FHIR R4** - the current international interoperability standard. Epic, Cerner, and most major EHR vendors expose FHIR-compliant APIs. MedAgent's Intake and History agents would query these directly to pull medication lists, allergy records, prior encounters, and demographics.
- **SMART on FHIR** - the OAuth2-based authentication layer that allows third-party apps to access EHR data securely with clinician or patient consent.

**Real Drug Interaction Database**

Replace the current tool stubs with:
- **OpenFDA API** (free, US government) - drug interactions, adverse event reports, labelling data
- **RxNorm API** (free, US National Library of Medicine) - drug name normalisation and interaction lookup
- **DrugBank** (licensed, comprehensive) - the gold standard for pharmaceutical interaction data

**Medical Evidence Store**

Load real clinical evidence into Qdrant:
- **PubMed / MEDLINE** - 35 million citations, free bulk download via FTP from the National Library of Medicine
- **NICE / CDC / WHO guidelines** - publicly available, can be chunked, embedded, and indexed
- **UpToDate** (licensed) - the clinical decision support reference used in most teaching hospitals

**Compliance**

Before handling real patient data:

- All cloud services touching PHI must sign a **BAA (Business Associate Agreement)** - a HIPAA-required contract between a healthcare entity and its vendors
- Patient data must be **de-identified** before reaching any external AI API. Tools: Microsoft Presidio (open source), AWS Comprehend Medical (managed)
- Audit logs must be retained for the legally required period (6–10 years depending on jurisdiction) in a tamper-evident system
- EU / UK deployments require **GDPR compliance** - data residency in the EU, data processing agreements with all vendors, and right-to-erasure workflows

**Clinical Validation Before Go-Live**

The pipeline should be evaluated against a held-out set of de-identified cases with known correct diagnoses. Metrics to measure: top-1 accuracy, top-3 accuracy, false-negative rate on emergency detection, and confidence calibration.

---

## Technical Stack

This section is for engineers who want to understand every architectural decision in detail.

### Agent Orchestration - LangGraph

LangGraph is an open-source framework from LangChain for building stateful, multi-step AI applications as directed graphs. Each node in the graph is an agent function. Edges between nodes are conditional - the graph evaluates the current state after each node and decides where to route next.

Why LangGraph over a custom agent loop:
- **Checkpointing is first-class.** After every node execution, the full graph state is persisted to Postgres via `AsyncPostgresSaver`. Server crash mid-pipeline → the run resumes from the last checkpoint, not from scratch.
- **HITL interrupts are native.** LangGraph's `interrupt_before` mechanism pauses the graph, writes a checkpoint, and waits for an external signal (the clinician's approval API call) before resuming. This is enforced at the execution layer, not the application layer.
- **Parallel fan-out is declarative.** The History and Research agents run concurrently as a native LangGraph pattern - no threading or asyncio management needed.
- **State reducers handle write conflicts.** Both parallel agents write to the same `completed_agents` list. LangGraph's `Annotated[list, reducer]` pattern merges these writes safely without race conditions.

**Graph configuration used:**
```python
# Parallel fan-out: both branches run concurrently
builder.add_edge("intake", "history")
builder.add_edge("intake", "research")
# Natural join: both edges point to differential - LangGraph waits for both
builder.add_edge("history", "differential")
builder.add_edge("research", "differential")
# Conditional routing after each key node
builder.add_conditional_edges("differential", route_after_differential)
builder.add_conditional_edges("risk", route_after_risk)
# HITL interrupt before summariser
builder.compile(checkpointer=checkpointer, interrupt_before=["summarizer"])
```

### LLM Inference - Groq API

All six agents use `ChatGroq` with `llama-3.1-8b-instant`. Groq runs LLMs on custom LPU (Language Processing Unit) silicon - inference is significantly faster than GPU-based providers at the same model size.

Why Groq over OpenAI/Anthropic for this project:
- Free tier with no credit card required - zero infrastructure cost
- `llama-3.1-8b-instant` is fast enough for multi-agent sequential pipelines
- `ChatGroq` implements the LangChain `BaseChatModel` interface - swappable with any other provider without changing agent code

For production, the swap to a larger model (`llama-3.1-70b` or a fine-tuned clinical model) requires changing one environment variable.

**Risk Agent specifically uses tool-calling:**
```python
llm = ChatGroq(model=..., api_key=...)
agent = create_tool_calling_agent(llm, [check_drug_interactions, check_allergy_conflicts], prompt)
executor = AgentExecutor(agent=agent, tools=tools)
```

### Embeddings - HuggingFace Inference API

`sentence-transformers/all-MiniLM-L6-v2` via `HuggingFaceEndpointEmbeddings`. Produces 384-dimensional dense vectors. Used by the History and Research agents to embed queries before searching Qdrant.

Why 384 dimensions: sufficient semantic resolution for clinical text retrieval at lower storage and compute cost than 768 or 1536-dimensional models. The tradeoff is acceptable for a RAG pipeline over clinical notes.

Free tier on HuggingFace Inference API - no cost.

### Long-Term Memory - Qdrant Cloud

Qdrant stores two collections:
- `PatientSession` - completed SOAP notes and session summaries, indexed by patient ID
- `EvidenceChunk` - medical knowledge base chunks for RAG

Vector search configuration:
- Distance metric: **cosine similarity** - appropriate for normalised sentence embeddings
- Filter: `patient_id` field condition on `PatientSession` queries - each patient's history is scoped to their own records
- Limit: top-5 patient sessions, top-8 evidence chunks per query

```python
results = self.client.search(
    collection_name=PATIENT_SESSION_COLLECTION,
    query_vector=query_embedding,
    query_filter=Filter(must=[FieldCondition(key="patient_id", match=MatchValue(value=patient_id))]),
    limit=5,
)
```

Free tier on Qdrant Cloud: 1GB storage, 1 node. Suspends after inactivity - reactivate via dashboard.

### Short-Term Memory - Upstash Redis

Every agent node writes the updated graph state to Redis keyed by `thread_id`. This serves two purposes:
1. **Session restore** - if a user reconnects mid-session, the frontend can poll `/cases/{thread_id}/state` to restore the current view
2. **Cross-agent state sharing** - all agents read from and write to the same Redis working object within a session

`redis.asyncio` client with `rediss://` (TLS) connection string required for Upstash.

### Checkpoint Store - Neon Postgres

LangGraph's `AsyncPostgresSaver` writes a full checkpoint after every node. The schema includes: thread ID, node name, input state snapshot, output state snapshot, and timestamp.

Connection requirements: `psycopg[binary]>=3.1.19` (psycopg3, not psycopg2 - the checkpoint library requires the newer async-native driver). The `+asyncpg` prefix from SQLAlchemy URLs is stripped before passing to psycopg3.

```python
def _normalize_postgres_url(url: str) -> str:
    return url.replace("postgresql+asyncpg://", "postgresql://")
```

Free tier on Neon: 0.5GB storage, autoscales to zero when idle.

### Real-Time Streaming - SSE

The frontend connects to `GET /stream/{thread_id}` immediately after case submission. The backend uses `sse-starlette` to emit events as each agent node completes:

```
event: agent_start
data: {"agent": "intake"}

event: agent_done
data: {"agent": "intake", "output": {...}}

event: awaiting_approval
data: {}

event: done
data: {}
```

The `useAgentStream` React hook maintains an `EventSource` connection and appends events to state. The `AgentStatusPanel` component derives display state from the event list - no polling, no websocket handshake overhead.

### Guardrail Layer Architecture

The guardrail layer sits between the API route and the LangGraph graph invocation. It is intentionally separate from the AI pipeline:

```
POST /cases
  │
  ├─ check_rate_limit()           ← in-memory, ~0.01ms
  ├─ validate_case_input()        ← regex + length, ~0.1ms
  ├─ detect_emergencies()         ← keyword scan, ~0.5ms
  ├─ log_case_submitted()         ← structured JSON to stdout
  │
  └─ graph.ainvoke(initial_state) ← AI pipeline starts here
```

Emergency flags detected before the graph runs are stored in `state["emergency_flags"]`. The Risk Agent reads this field and merges it with AI-detected flags before writing `state["risk_flags"]`. This means critical flags are available in the API response immediately, before the full pipeline completes.

### Testing Strategy

Integration tests use FastAPI's `TestClient` from Starlette - no external test server needed. External services (Postgres, Redis, Qdrant, Groq) are mocked via `unittest.mock.patch` so tests run without live credentials in CI.

Test coverage:
- `/health` - response shape, HTTP 200, ISO 8601 timestamp format
- `POST /cases` - valid submission returns thread_id, emergency flag detection (cardiac, suicidality, pediatric), six input validation rejection cases
- `/history/{patient_id}` - endpoint existence and response shape

```bash
pytest backend/tests/ -v
```

### Frontend Architecture

- **React 18** with Vite - no CRA, fast HMR
- **Tailwind CSS v3** with custom design tokens (navy palette, clinical colour system)
- **No state management library** - component-local state + the `useAgentStream` SSE hook covers all requirements
- **Uncontrolled forms** - demo scenario loading uses direct DOM value assignment on the nearest form ancestor, avoiding controlled input complexity for a non-interactive field

Component hierarchy:
```
Dashboard
├── Sidebar (collapsible nav)
├── Header (status badge, thread ID, new case button)
└── Main (conditional on threadId)
    ├── [no threadId] CaseInput + HowItWorks cards
    └── [threadId]
        ├── AgentStatusPanel (col 3) - pipeline with connector lines, progress bar
        ├── DifferentialPanel + ApprovalGate (col 5) - confidence bars, risk flags
        └── SOAPOutput (col 4) - colour-coded S/O/A/P sections
```

### Why This Stack Costs $0

| Service | Free Tier Limits | Used For |
|---|---|---|
| Groq | 30 req/min, 6k tokens/min on free | All LLM inference |
| HuggingFace Inference API | Rate-limited, free | Sentence embeddings |
| Qdrant Cloud | 1GB, 1 node | Vector memory store |
| Upstash Redis | 10k commands/day, 256MB | Session state |
| Neon Postgres | 0.5GB, autoscales to zero | Graph checkpoints |
| Render | 750hrs/month, spins down after inactivity | Backend API |
| Vercel | Unlimited for hobby projects | Frontend |

The architecture was designed specifically around this constraint - every service selected has a genuinely usable free tier, not just a trial period.

---

## Repo Structure

```
medagent/
├── backend/
│   ├── agents/            # Six AI agent implementations
│   │   ├── intake.py
│   │   ├── history.py
│   │   ├── research.py
│   │   ├── differential.py
│   │   ├── risk.py
│   │   └── summarizer.py
│   ├── guardrails/        # Deterministic safety layer (runs before AI)
│   │   ├── input_validator.py
│   │   ├── emergency_detector.py
│   │   ├── output_validator.py
│   │   ├── audit_logger.py
│   │   └── rate_limiter.py
│   ├── memory/            # Long-term (Qdrant) and short-term (Redis) memory
│   ├── graph/             # LangGraph builder, state schema, edges, checkpointer
│   ├── api/               # FastAPI app, routes, middleware
│   └── tests/             # Integration tests (pytest + TestClient)
├── frontend/
│   └── src/
│       ├── components/    # AgentStatusPanel, DifferentialPanel, CaseInput, SOAPOutput
│       ├── pages/         # Dashboard (sidebar + 3-column layout)
│       └── hooks/         # useAgentStream (SSE)
├── .env.example
└── README.md
```

---

## Built By

**Qazi Fabia Hoq**

Built with Claude Code · LangGraph · Groq · Qdrant · Neon · Upstash Redis · FastAPI · React · Vercel · Render
