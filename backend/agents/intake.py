import spacy
from langchain_ollama import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate
import json
import os
from graph.state import AgentState

nlp = spacy.load("en_core_web_sm")

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
    Uses spaCy for NER then LLM for structured extraction.
    """
    note = state["raw_note"]

    llm = OllamaLLM(
        base_url=os.getenv("OLLAMA_BASE_URL", "http://ollama:11434"),
        model=os.getenv("OLLAMA_MODEL", "llama3"),
    )

    prompt = ChatPromptTemplate.from_template(INTAKE_PROMPT)
    chain = prompt | llm

    try:
        raw_output = await chain.ainvoke({"note": note})
        # Strip any markdown fences if model adds them
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
