from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
import json
import os
from graph.state import AgentState

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


async def intake_node(state: AgentState) -> AgentState:
    """
    Intake agent. Parses unstructured clinical note into a structured payload.
    """
    note = state["raw_note"]

    llm = ChatGroq(
        model=os.getenv("GROQ_MODEL", "llama-3.1-8b-instant"),
        api_key=os.getenv("GROQ_API_KEY"),
    )

    chain = ChatPromptTemplate.from_template(INTAKE_PROMPT) | llm | StrOutputParser()

    try:
        raw_output = await chain.ainvoke({"note": note})
        cleaned = raw_output.strip().replace("```json", "").replace("```", "").strip()
        intake_payload = json.loads(cleaned)
    except Exception as e:
        return {**state, "error": f"Intake agent failed: {str(e)}"}

    completed = state.get("completed_agents", [])
    return {
        **state,
        "intake_payload": intake_payload,
        "completed_agents": completed + ["intake"],
    }
