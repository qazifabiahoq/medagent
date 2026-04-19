from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
import json
import os
from graph.state import AgentState
from guardrails.output_validator import validate_risk_flags

RISK_PROMPT = """You are a clinical safety agent. Review the patient's medication list, allergies,
and proposed differential diagnosis for drug interactions, contraindications, and safety concerns.

Patient medications: {medications}
Patient allergies: {allergies}
Differential diagnosis: {differential}

Return ONLY valid JSON with this exact structure:
{{
  "flags": [
    {{
      "name": "short flag name",
      "description": "clear description of the risk",
      "severity": "critical | moderate | low",
      "action": "recommended clinical action",
      "source": "ai_risk_agent"
    }}
  ]
}}

If no risks are found, return {{"flags": []}}.
Do not include any text outside the JSON."""


async def risk_node(state: AgentState) -> AgentState:
    """
    Risk agent. Reviews medications, allergies, and differential for safety concerns.
    Merges deterministic emergency_flags (from guardrail) with AI-detected flags.
    """
    intake_payload = state.get("intake_payload", {}) or {}
    medications = intake_payload.get("medications", [])
    allergies = intake_payload.get("allergies", [])

    pre_flags = state.get("emergency_flags", []) or []
    ai_flags = []

    if medications or allergies:
        llm = ChatGroq(
            model=os.getenv("GROQ_MODEL", "llama-3.1-8b-instant"),
            api_key=os.getenv("GROQ_API_KEY"),
        )

        chain = ChatPromptTemplate.from_template(RISK_PROMPT) | llm | StrOutputParser()

        try:
            raw = await chain.ainvoke({
                "medications": json.dumps(medications),
                "allergies": json.dumps(allergies),
                "differential": json.dumps(state.get("differential", [])),
            })
            cleaned = raw.strip().replace("```json", "").replace("```", "").strip()
            risk_data = json.loads(cleaned) if cleaned.startswith("{") else {}
            ai_flags = risk_data.get("flags", [])
        except Exception:
            ai_flags = []

    all_flags = pre_flags + ai_flags
    validation = validate_risk_flags(all_flags)

    completed = state.get("completed_agents", [])
    return {
        **state,
        "risk_flags": validation["flags"],
        "guardrail_warnings": (state.get("guardrail_warnings") or []) + (
            [validation["review_reason"]] if validation.get("review_reason") else []
        ),
        "completed_agents": completed + ["risk"],
    }
