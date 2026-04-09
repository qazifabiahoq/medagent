from langchain_ollama import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate
import json
import os
from graph.state import AgentState

DIFFERENTIAL_PROMPT = """You are a senior clinician generating a differential diagnosis.

Patient intake:
{intake}

Prior history:
{history}

Supporting evidence:
{evidence}

Previous differential (if any):
{previous_differential}

Generate a ranked differential diagnosis list. Return ONLY valid JSON:
{{
  "differentials": [
    {{
      "diagnosis": "string",
      "confidence": 0.0-1.0,
      "supporting_evidence": ["list"],
      "against_evidence": ["list"],
      "needs_revision": false
    }}
  ],
  "overall_quality": "high|medium|low",
  "revision_rationale": "string or empty"
}}

If overall_quality is not high, set needs_revision to true on entries that need work.
"""


async def differential_node(state: AgentState) -> AgentState:
    """
    Differential agent. Generates ranked differential diagnosis with a self-critique reflection loop.
    On each pass it evaluates its own output and sets needs_revision flags.
    The edge router decides whether to loop back or proceed to risk agent.
    """
    llm = OllamaLLM(
        base_url=os.getenv("OLLAMA_BASE_URL", "http://ollama:11434"),
        model=os.getenv("OLLAMA_MODEL", "llama3"),
    )

    prompt = ChatPromptTemplate.from_template(DIFFERENTIAL_PROMPT)
    chain = prompt | llm

    intake = json.dumps(state.get("intake_payload", {}), indent=2)
    history = json.dumps(state.get("prior_sessions", []), indent=2)
    evidence = json.dumps(state.get("evidence_chunks", []), indent=2)
    previous = json.dumps(state.get("differential", []), indent=2)

    try:
        raw_output = await chain.ainvoke({
            "intake": intake,
            "history": history,
            "evidence": evidence,
            "previous_differential": previous,
        })
        cleaned = raw_output.strip().replace("```json", "").replace("```", "").strip()
        result = json.loads(cleaned)
        differentials = result.get("differentials", [])
    except Exception as e:
        return {**state, "error": f"Differential agent failed: {str(e)}"}

    reflection_count = state.get("reflection_count", 0) + 1
    completed = state.get("completed_agents", [])

    return {
        **state,
        "differential": differentials,
        "reflection_count": reflection_count,
        "completed_agents": list(set(completed + ["differential"])),
    }
