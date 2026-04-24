import json
import logging
import os
import re

from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from pydantic import BaseModel
from graph.state import AgentState

logger = logging.getLogger("medagent.summarizer")


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

Department routing:
{department}

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


def _extract_json(text: str) -> dict:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            return json.loads(match.group())
        raise ValueError("No JSON found")


async def summarizer_node(state: AgentState) -> AgentState:
    completed = state.get("completed_agents", [])

    try:
        llm = ChatGroq(
            model=os.getenv("GROQ_MODEL", "llama-3.1-8b-instant"),
            api_key=os.getenv("GROQ_API_KEY"),
        )
        chain = ChatPromptTemplate.from_template(SUMMARIZER_PROMPT) | llm | StrOutputParser()
        raw = await chain.ainvoke({
            "intake": json.dumps(state.get("intake_payload") or {}, indent=2),
            "differential": json.dumps(state.get("differential") or [], indent=2),
            "risk_flags": json.dumps(state.get("risk_flags") or [], indent=2),
            "department": json.dumps(state.get("department_routing") or {}, indent=2),
        })
        cleaned = raw.strip().replace("```json", "").replace("```", "").strip()
        soap_dict = _extract_json(cleaned)
        soap_note = SOAPNote(**soap_dict).model_dump()
    except Exception as e:
        logger.warning("Summarizer failed, using fallback: %s", e)
        soap_note = {
            "subjective": "See raw clinical note",
            "objective": "Automated extraction failed — manual review required",
            "assessment": str(state.get("differential", [{}])[0].get("diagnosis", "Undetermined") if state.get("differential") else "Undetermined"),
            "plan": "Clinical review required",
            "differential_summary": json.dumps(state.get("differential") or []),
            "risk_summary": json.dumps(state.get("risk_flags") or []),
            "clinician_notes": f"AI pipeline completed with warnings. Department: {state.get('department_routing', {}).get('primary_department', 'General Medicine')}",
        }

    return {
        **state,
        "soap_note": soap_note,
        "completed_agents": completed + ["summarizer"],
        "awaiting_approval": False,
    }
