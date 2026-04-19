from langchain_groq import ChatGroq
from langchain_core.tools import tool
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate
import json
import os
from graph.state import AgentState
from guardrails.output_validator import validate_risk_flags


@tool
def check_drug_interactions(medications: list[str]) -> dict:
    """
    Check for known drug interactions and contraindications.
    Returns a list of flagged interactions with severity levels.
    """
    # Production: wire to OpenFDA API or RxNorm for real interaction data
    return {"interactions": [], "contraindications": [], "warnings": []}


@tool
def check_allergy_conflicts(medications: list[str], allergies: list[str]) -> dict:
    """
    Check if any proposed medications conflict with known patient allergies.
    """
    # Production: wire to patient allergy record from EHR FHIR API
    return {"conflicts": [], "warnings": []}


RISK_SYSTEM_PROMPT = """You are a clinical safety agent. Your job is to review the proposed
differential diagnosis for drug interactions, contraindications, allergy conflicts, and
any patient safety concerns.

Always call check_drug_interactions and check_allergy_conflicts before concluding.

Return a JSON object with this exact structure:
{
  "flags": [
    {
      "name": "short flag name",
      "description": "clear description of the risk",
      "severity": "critical | moderate | low",
      "action": "recommended clinical action",
      "source": "ai_risk_agent"
    }
  ]
}

If no risks are found, return {"flags": []}.
Do not include any text outside the JSON."""

tools = [check_drug_interactions, check_allergy_conflicts]


async def risk_node(state: AgentState) -> AgentState:
    """
    Risk agent. Tool-calling agent that checks drug interactions and allergy conflicts.
    Merges deterministic emergency_flags (already in state) with AI-detected flags.
    Critical flags force the HITL approval gate.
    """
    intake_payload = state.get("intake_payload", {}) or {}
    medications = intake_payload.get("medications", [])
    allergies = intake_payload.get("allergies", [])

    # Always start with the deterministic emergency flags from the guardrail
    pre_flags = state.get("emergency_flags", []) or []
    ai_flags = []

    if medications:
        llm = ChatGroq(
            model=os.getenv("GROQ_MODEL", "llama-3.1-8b-instant"),
            api_key=os.getenv("GROQ_API_KEY"),
        )

        prompt = ChatPromptTemplate.from_messages([
            ("system", RISK_SYSTEM_PROMPT),
            ("human", "Medications: {medications}\nAllergies: {allergies}\nDifferential: {differential}"),
            ("placeholder", "{agent_scratchpad}"),
        ])

        agent = create_tool_calling_agent(llm, tools, prompt)
        executor = AgentExecutor(agent=agent, tools=tools, verbose=False)

        try:
            result = await executor.ainvoke({
                "medications": json.dumps(medications),
                "allergies": json.dumps(allergies),
                "differential": json.dumps(state.get("differential", [])),
            })
            output = result.get("output", "{}")
            cleaned = output.strip().replace("```json", "").replace("```", "").strip()
            risk_data = json.loads(cleaned) if cleaned.startswith("{") else {}
            ai_flags = risk_data.get("flags", [])
        except Exception:
            ai_flags = []

    # Merge: deterministic guardrail flags come first (most critical)
    all_flags = pre_flags + ai_flags

    # Output validation: determine if mandatory review is required
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
