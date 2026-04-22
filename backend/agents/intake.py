import json
import logging
import os
import re

from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from graph.state import AgentState

logger = logging.getLogger("medagent.intake")

INTAKE_PROMPT = """You are a clinical intake parser. Extract structured information from the clinical note below.

Return ONLY valid JSON with this exact schema:
{{
  "chief_complaint": "string",
  "symptoms": ["list of symptoms"],
  "medications": ["list of current medications"],
  "allergies": ["list of allergies"],
  "vitals": {{"bp": "string", "hr": "string", "temp": "string", "spo2": "string"}},
  "history_flags": ["relevant past history keywords to search memory for"],
  "assessment_hints": ["preliminary clinical observations"]
}}

Clinical note:
{note}
"""

_FALLBACK_PAYLOAD = {
    "chief_complaint": "See raw note — automated parsing unavailable",
    "symptoms": [],
    "medications": [],
    "allergies": [],
    "vitals": {"bp": "", "hr": "", "temp": "", "spo2": ""},
    "history_flags": [],
    "assessment_hints": [],
}


def _extract_json(text: str) -> dict:
    """Try multiple strategies to pull valid JSON out of LLM output."""
    # Direct parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    # Find first {...} block
    match = re.search(r'\{.*\}', text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass
    raise ValueError("No valid JSON found in LLM output")


async def intake_node(state: AgentState) -> AgentState:
    note = state["raw_note"]
    completed = state.get("completed_agents", [])

    llm = ChatGroq(
        model=os.getenv("GROQ_MODEL", "llama-3.1-8b-instant"),
        api_key=os.getenv("GROQ_API_KEY"),
    )
    chain = ChatPromptTemplate.from_template(INTAKE_PROMPT) | llm | StrOutputParser()

    try:
        raw_output = await chain.ainvoke({"note": note})
        cleaned = raw_output.strip().replace("```json", "").replace("```", "").strip()
        intake_payload = _extract_json(cleaned)
    except Exception as e:
        logger.warning("Intake parsing failed, using fallback: %s", e)
        intake_payload = _FALLBACK_PAYLOAD.copy()

    return {
        **state,
        "intake_payload": intake_payload,
        "completed_agents": completed + ["intake"],
    }
