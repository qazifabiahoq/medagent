import json
import logging
import os
import re

from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from graph.state import AgentState

logger = logging.getLogger("medagent.differential")

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

_FALLBACK = [{"diagnosis": "Undifferentiated — manual review required",
              "confidence": 0.1, "supporting_evidence": [], "against_evidence": [],
              "needs_revision": False}]


def _extract_json(text: str) -> dict:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            return json.loads(match.group())
        raise ValueError("No JSON found")


async def differential_node(state: AgentState) -> AgentState:
    completed = state.get("completed_agents", [])
    reflection_count = state.get("reflection_count", 0) + 1

    try:
        llm = ChatGroq(
            model=os.getenv("GROQ_MODEL", "llama-3.1-8b-instant"),
            api_key=os.getenv("GROQ_API_KEY"),
        )
        chain = ChatPromptTemplate.from_template(DIFFERENTIAL_PROMPT) | llm | StrOutputParser()
        raw = await chain.ainvoke({
            "intake": json.dumps(state.get("intake_payload") or {}, indent=2),
            "history": json.dumps(state.get("prior_sessions") or [], indent=2),
            "evidence": json.dumps(state.get("evidence_chunks") or [], indent=2),
            "previous_differential": json.dumps(state.get("differential") or [], indent=2),
        })
        cleaned = raw.strip().replace("```json", "").replace("```", "").strip()
        result = _extract_json(cleaned)
        differentials = result.get("differentials", _FALLBACK)
    except Exception as e:
        logger.warning("Differential agent failed, using fallback: %s", e)
        differentials = _FALLBACK

    return {
        **state,
        "differential": differentials,
        "reflection_count": reflection_count,
        "completed_agents": list(set(completed + ["differential"])),
    }
