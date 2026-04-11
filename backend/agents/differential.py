from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
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
      "confidence": 0.0,
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
    Differential agent. Generates ranked differential diagnosis with a self-critique
    reflection loop. Sets needs_revision flags; the edge router decides whether to loop.
    """
    llm = ChatGroq(
        model=os.getenv("GROQ_MODEL", "llama-3.1-8b-instant"),
        api_key=os.getenv("GROQ_API_KEY"),
    )

    chain = ChatPromptTemplate.from_template(DIFFERENTIAL_PROMPT) | llm | StrOutputParser()

    try:
        raw_output = await chain.ainvoke({
            "intake": json.dumps(state.get("intake_payload", {}), indent=2),
            "history": json.dumps(state.get("prior_sessions", []), indent=2),
            "evidence": json.dumps(state.get("evidence_chunks", []), indent=2),
            "previous_differential": json.dumps(state.get("differential", []), indent=2),
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
