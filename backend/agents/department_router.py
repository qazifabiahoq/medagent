from graph.state import AgentState

# Maps emergency/risk flag names to hospital department routing
_DEPARTMENT_RULES = [
    {
        "flag": "Acute Cardiac Event",
        "department": "Cardiology",
        "ward": "Cardiac Care Unit (CCU)",
        "priority": "CRITICAL",
        "team": ["On-call Cardiologist", "Cardiac Nurse Specialist", "ECG Technician"],
        "escalation": "Emergency Department → CCU",
    },
    {
        "flag": "Stroke / Neurological Emergency",
        "department": "Neurology",
        "ward": "Stroke Unit",
        "priority": "CRITICAL",
        "team": ["Neurologist", "Stroke Nurse Specialist", "CT Radiologist"],
        "escalation": "Emergency Department → Stroke Unit",
    },
    {
        "flag": "Sepsis / Septic Shock",
        "department": "Critical Care",
        "ward": "Intensive Care Unit (ICU)",
        "priority": "CRITICAL",
        "team": ["Intensivist", "Infectious Disease Consultant", "Critical Care Nurse"],
        "escalation": "Emergency Department → ICU",
    },
    {
        "flag": "Suicidality / Self-Harm",
        "department": "Psychiatry",
        "ward": "Psychiatric Emergency Unit",
        "priority": "CRITICAL",
        "team": ["Consultant Psychiatrist", "Mental Health Nurse", "Social Worker"],
        "escalation": "Psychiatric Emergency Services",
    },
    {
        "flag": "Anaphylaxis / Airway Emergency",
        "department": "Emergency Medicine",
        "ward": "Resuscitation Bay",
        "priority": "CRITICAL",
        "team": ["Emergency Physician", "Anaesthetist", "Emergency Nurse"],
        "escalation": "Code Team / Rapid Response",
    },
    {
        "flag": "Severe Respiratory Distress",
        "department": "Pulmonology",
        "ward": "Respiratory High Dependency Unit",
        "priority": "CRITICAL",
        "team": ["Pulmonologist", "Respiratory Therapist", "ICU Nurse"],
        "escalation": "ICU",
    },
    {
        "flag": "Pediatric Patient",
        "department": "Pediatrics",
        "ward": "General Pediatric Ward",
        "priority": "HIGH",
        "team": ["Pediatrician", "Pediatric Nurse"],
        "escalation": "Pediatric Emergency Department",
    },
    {
        "flag": "Pregnancy",
        "department": "Obstetrics & Gynaecology",
        "ward": "Antenatal Ward",
        "priority": "HIGH",
        "team": ["Obstetrician", "Midwife", "Neonatal Specialist"],
        "escalation": "Labour & Delivery Unit",
    },
]

_PRIORITY_ORDER = {"CRITICAL": 0, "HIGH": 1, "MODERATE": 2, "ROUTINE": 3}


async def department_router_node(state: AgentState) -> AgentState:
    """
    Deterministic department routing — no LLM, runs in microseconds.
    Reads risk_flags + emergency_flags and assigns the patient to the
    correct hospital department, ward, and clinical team.
    Multiple flags are ranked by severity; all relevant departments are listed.
    """
    all_flags = (state.get("emergency_flags") or []) + (state.get("risk_flags") or [])
    flag_names = {f["name"] for f in all_flags}

    matched = []
    for rule in _DEPARTMENT_RULES:
        if rule["flag"] in flag_names:
            matched.append(rule)

    matched.sort(key=lambda r: _PRIORITY_ORDER.get(r["priority"], 99))

    if matched:
        primary = matched[0]
        routing = {
            "primary_department": primary["department"],
            "ward": primary["ward"],
            "priority": primary["priority"],
            "team": primary["team"],
            "escalation_path": primary["escalation"],
            "all_departments": [m["department"] for m in matched],
            "routing_reason": [
                f"{r['flag']} → {r['department']} ({r['priority']})"
                for r in matched
            ],
        }
    else:
        routing = {
            "primary_department": "General Medicine",
            "ward": "General Medical Ward",
            "priority": "ROUTINE",
            "team": ["General Practitioner", "Ward Nurse"],
            "escalation_path": "Specialist referral if needed",
            "all_departments": ["General Medicine"],
            "routing_reason": ["No critical or high-priority flags — routine admission"],
        }

    completed = state.get("completed_agents", [])
    return {
        **state,
        "department_routing": routing,
        "completed_agents": completed + ["department_router"],
    }
