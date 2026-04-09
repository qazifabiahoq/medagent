from langchain_ollama import OllamaLLM
from langchain_core.tools import tool
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate
import json
import os
from graph.state import AgentState


# Drug interaction tool - Claude Code will expand this with a real DB
@tool
def check_drug_interactions(medications: list[str]) -> dict:
    """
    Check for known drug interactions and contraindications.
    Returns a list of flagged interactions with severity levels.
    """
    # Stub - Claude Code replaces this with real drug interaction DB calls
    # e.g. OpenFDA API, RxNorm, or a local drug interaction dataset
    return {
        "interactions": [],
        "contraindications": [],
        "warnings": [],
    }


@tool
def check_allergy_conflicts(medications: list[str], allergies: list[str]) -> dict:
    """
    Check if any proposed medications conflict with known patient allergies.
    """
    # Stub - Claude Code expands with real allergy cross-reference logic
    return {
        "conflicts": [],
        "warnings": [],
    }


RISK_SYSTEM_PROMPT = """You are a clinical safety agent. Your job is to check the proposed differential diagnosis
for drug interactions, contraindications, and allergy conflicts. Use the tools provided.
Always use check_drug_interactions and check_allergy_conflicts before concluding.
Return a JSON summary of all risk flags with severity: critical, moderate, or low."""

tools = [check_drug_interactions, check_allergy_conflicts]


async def risk_node(state: AgentState) -> AgentState:
    """
    Risk agent. Tool-calling agent that checks drug interactions and allergy conflicts.
    Uses LangChain tool-calling agent pattern with structured tool outputs.
    Critical flags cause the graph to loop back to the differential agent.
    """
    intake_payload = state.get("intake_payload", {})
    medications = intake_payload.get("medications", [])
    allergies = intake_payload.get("allergies", [])

    if not medications:
        completed = state.get("completed_agents", [])
        return {
            **state,
            "risk_flags": [],
            "completed_agents": completed + ["risk"],
        }

    llm = OllamaLLM(
        base_url=os.getenv("OLLAMA_BASE_URL", "http://ollama:11434"),
        model=os.getenv("OLLAMA_MODEL", "llama3"),
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
        # Parse risk flags from agent output
        output = result.get("output", "{}")
        cleaned = output.strip().replace("```json", "").replace("```", "").strip()
        risk_data = json.loads(cleaned) if cleaned.startswith("{") else {}
        risk_flags = risk_data.get("flags", [])
    except Exception:
        risk_flags = []

    completed = state.get("completed_agents", [])
    return {
        **state,
        "risk_flags": risk_flags,
        "completed_agents": completed + ["risk"],
    }
