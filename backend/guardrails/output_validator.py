"""
Output validation — runs after each AI agent produces its result.
Enforces mandatory disclaimers, confidence floors, and safety constraints
so that AI output never reaches the clinician without appropriate context.
"""

MEDICAL_DISCLAIMER = (
    "AI-generated output for clinical decision support only. "
    "This is NOT a substitute for professional clinical judgment. "
    "All findings must be reviewed and validated by a licensed clinician "
    "before any clinical action is taken."
)

ADVISORY_NOTE = (
    "For clinical review only. "
    "MedAgent does not prescribe, diagnose, or initiate treatment autonomously."
)

# Differential diagnosis below this confidence is flagged for low-confidence review
CONFIDENCE_WARNING_THRESHOLD = 0.30
MIN_CONFIDENCE_TO_SHOW = 0.05


def validate_differential(differential: list) -> dict:
    """
    Validates the AI-generated differential diagnosis list.
    Filters out sub-threshold items and attaches relevant warnings.
    """
    if not differential:
        return {
            "valid": False,
            "filtered_differential": [],
            "warnings": [
                "No differential diagnoses were generated. "
                "Manual clinical review is required — do not rely on AI output for this case."
            ],
            "disclaimer": MEDICAL_DISCLAIMER,
        }

    filtered = [d for d in differential if d.get("confidence", 0) >= MIN_CONFIDENCE_TO_SHOW]

    warnings = []

    top_confidence = filtered[0].get("confidence", 0) if filtered else 0
    if top_confidence < CONFIDENCE_WARNING_THRESHOLD:
        warnings.append(
            f"Model confidence is low (top diagnosis: {round(top_confidence * 100)}%). "
            "Additional diagnostic workup is strongly recommended before clinical decisions are made."
        )

    if len(filtered) == 1:
        warnings.append(
            "Only one diagnosis meets the confidence threshold. "
            "Consider whether additional conditions should be ruled out clinically."
        )

    return {
        "valid": True,
        "filtered_differential": filtered,
        "warnings": warnings,
        "disclaimer": MEDICAL_DISCLAIMER,
    }


def validate_soap_note(soap_note: dict) -> dict:
    """
    Attaches mandatory disclaimer and advisory to every generated SOAP note.
    The SOAP note is advisory only — it must not be filed without clinician review.
    """
    if not soap_note:
        return soap_note

    return {
        **soap_note,
        "_disclaimer": MEDICAL_DISCLAIMER,
        "_advisory": ADVISORY_NOTE,
    }


def validate_risk_flags(risk_flags: list) -> dict:
    """
    Validates risk flag output and determines whether mandatory human review applies.
    Any critical flag forces the HITL gate — this cannot be bypassed.
    """
    critical_flags = [f for f in risk_flags if f.get("severity") == "critical"]
    moderate_flags = [f for f in risk_flags if f.get("severity") == "moderate"]

    return {
        "flags": risk_flags,
        "critical_count": len(critical_flags),
        "moderate_count": len(moderate_flags),
        "requires_mandatory_review": len(critical_flags) > 0,
        "review_reason": (
            f"{len(critical_flags)} critical risk flag(s) detected. "
            "Clinician review is mandatory before proceeding."
        ) if critical_flags else None,
    }
