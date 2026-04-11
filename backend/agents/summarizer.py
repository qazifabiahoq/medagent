from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from pydantic import BaseModel
import json
import os
from graph.state import AgentState


class SOAPNote(BaseModel):
    subjective: str
    objective: str
    assessment: str
    plan: str
    differential_summary: str
    risk_summary: str
    clinician_notes: str


SUMMARIZER_PROMPT = """You are a clinical documentation specialist. Generate a structured SOAP note.

Intake:
{intake}

Differential diagnosis:
{differential}

Risk flags:
{risk_flags}

Prior history context:
{history}

Return ONLY valid JSON matching this schema:
{{
  "subjective": "patient reported symptoms and history",
  "objective": "vitals and objective findings from intake",
  "assessment": "primary diagnosis with confidence, differential summary",
  "plan": "recommended next steps, tests, treatments",
  "differential_summary": "ranked differentials considered",
  "risk_summary": "drug interactions and flags identified",
  "clinician_notes": "additional notes for reviewing clinician"
}}
"""


async def summarizer_node(state: AgentState) -> AgentState:
    """
    Summarizer agent. Runs AFTER the HITL interrupt and clinician approval.
    Produces the final structured SOAP note from all prior agent outputs.
    """
    llm = ChatGroq(
        model=os.getenv("GROQ_MODEL", "llama-3.1-8b-instant"),
        api_key=os.getenv("GROQ_API_KEY"),
    )

    chain = ChatPromptTemplate.from_template(SUMMARIZER_PROMPT) | llm | StrOutputParser()

    try:
        raw_output = await chain.ainvoke({
            "intake": json.dumps(state.get("intake_payload", {}), indent=2),
            "differential": json.dumps(state.get("differential", []), indent=2),
            "risk_flags": json.dumps(state.get("risk_flags", []), indent=2),
            "history": json.dumps(state.get("prior_sessions", []), indent=2),
        })
        cleaned = raw_output.strip().replace("```json", "").replace("```", "").strip()
        soap_dict = json.loads(cleaned)
        soap_note = SOAPNote(**soap_dict).model_dump()
    except Exception as e:
        return {**state, "error": f"Summarizer agent failed: {str(e)}"}

    completed = state.get("completed_agents", [])
    return {
        **state,
        "soap_note": soap_note,
        "completed_agents": completed + ["summarizer"],
        "awaiting_approval": False,
    }
