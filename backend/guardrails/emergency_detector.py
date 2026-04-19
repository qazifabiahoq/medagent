"""
Emergency condition detector — deterministic keyword scan on the raw clinical note.
Runs BEFORE the AI pipeline. Flags life-threatening or high-risk conditions immediately
so the clinician is alerted without waiting for the full agent pipeline to complete.

These flags are merged into the final risk output and shown prominently in the UI.
"""

EMERGENCY_PATTERNS = [
    {
        "name": "Acute Cardiac Event",
        "keywords": [
            "chest pain", "crushing chest", "cardiac arrest", "stemi",
            "ventricular fibrillation", "vfib", "heart attack", "mi ", " mi,",
            "myocardial infarction", "diaphoresis", "troponin elevated",
        ],
        "description": "Possible acute cardiac event detected in clinical note.",
        "severity": "critical",
        "action": (
            "Immediate cardiology consultation required. "
            "ECG and troponin levels should be obtained without delay. "
            "Do not hold the patient in primary care."
        ),
    },
    {
        "name": "Stroke / Neurological Emergency",
        "keywords": [
            "sudden onset weakness", "facial droop", "slurred speech", "dysarthria",
            "aphasia", "stroke", " cva", "cerebrovascular", "sudden vision loss",
            "worst headache of my life", "thunderclap headache", "subarachnoid",
        ],
        "description": "Possible acute neurological emergency (stroke/CVA) detected.",
        "severity": "critical",
        "action": (
            "Activate stroke protocol immediately. Time is brain — every minute matters. "
            "CT head without contrast is the first step. "
            "Note time of symptom onset for thrombolysis eligibility window."
        ),
    },
    {
        "name": "Sepsis / Septic Shock",
        "keywords": [
            "sepsis", "septic shock", "qsofa", "sofa score",
            "multi-organ failure", "organ dysfunction",
            "hypotension with fever", "lactate elevated", "blood culture",
        ],
        "description": "Sepsis criteria may be met based on clinical note.",
        "severity": "critical",
        "action": (
            "Initiate sepsis bundle within one hour: blood cultures × 2, "
            "IV broad-spectrum antibiotics, fluid resuscitation, lactate measurement. "
            "Escalate to ICU if haemodynamically unstable."
        ),
    },
    {
        "name": "Suicidality / Self-Harm",
        "keywords": [
            "suicidal", "suicide", "self-harm", "self harm", "selfharm",
            "wants to die", "kill himself", "kill herself", "kill themselves",
            "intentional overdose", "cutting himself", "cutting herself",
            "active suicidal ideation", "plan to harm",
        ],
        "description": "Suicidality or self-harm indicators detected in clinical note.",
        "severity": "critical",
        "action": (
            "Immediate psychiatric assessment required. "
            "Do not leave the patient unattended. "
            "Follow institutional safeguarding and duty-of-care protocols. "
            "Remove access to means where possible."
        ),
    },
    {
        "name": "Anaphylaxis / Airway Emergency",
        "keywords": [
            "anaphylaxis", "anaphylactic", "angioedema", "airway obstruction",
            "stridor", "respiratory arrest", "unable to breathe",
            "severe allergic reaction", "epipen", "adrenaline injection",
        ],
        "description": "Possible anaphylaxis or airway emergency detected.",
        "severity": "critical",
        "action": (
            "Administer intramuscular adrenaline (epinephrine) immediately if anaphylaxis confirmed. "
            "Ensure patent airway. Prepare for intubation. "
            "Call emergency response team."
        ),
    },
    {
        "name": "Severe Respiratory Distress",
        "keywords": [
            "spo2 8", "spo2 7", "o2 sat 8", "o2 sat 7",
            "oxygen saturation below 90", "respiratory failure",
            "severe dyspnea", "can't breathe", "cannot breathe",
            "cyanosis", "cyanotic",
        ],
        "description": "Severe hypoxia or respiratory distress detected.",
        "severity": "critical",
        "action": (
            "Immediate supplemental oxygen. Target SpO₂ ≥ 94%. "
            "Assess for need for non-invasive or invasive ventilation. "
            "Urgent respiratory/ICU review."
        ),
    },
    {
        "name": "Pediatric Patient",
        "keywords": [
            "newborn", "neonate", "neonatal", "infant", "toddler",
            "2-year-old", "3-year-old", "4-year-old", "5-year-old",
            "6-year-old", "7-year-old", "8-year-old", "9-year-old",
            "10-year-old", "11-year-old", "12-year-old", "13-year-old",
            "14-year-old", "15-year-old", "16-year-old", "17-year-old",
            "pediatric", "paediatric", "child patient", "years old child",
        ],
        "description": "Pediatric patient identified.",
        "severity": "moderate",
        "action": (
            "Apply age-appropriate and weight-based dosing throughout. "
            "Reference pediatric-specific normal ranges for vitals and labs. "
            "Pediatric specialist review is recommended before final treatment plan."
        ),
    },
    {
        "name": "Pregnancy",
        "keywords": [
            "pregnant", "pregnancy", "gravida", "first trimester", "second trimester",
            "third trimester", "gestational", "obstetric", "prenatal", "antenatal",
            "eclampsia", "preeclampsia", "weeks gestation", "fetal",
        ],
        "description": "Pregnancy indicated in clinical note.",
        "severity": "moderate",
        "action": (
            "All medications, imaging, and interventions must be reviewed for safety in pregnancy. "
            "Obstetric / maternal-fetal medicine review recommended. "
            "Check category ratings for any proposed pharmaceuticals."
        ),
    },
]


def detect_emergencies(raw_note: str) -> list[dict]:
    """
    Scans the raw clinical note for emergency conditions.
    Returns a list of risk-flag-shaped dicts, ready to be merged with
    the AI risk agent output.
    """
    note_lower = raw_note.lower()
    flags: list[dict] = []
    seen: set[str] = set()

    for pattern in EMERGENCY_PATTERNS:
        if pattern["name"] in seen:
            continue
        for keyword in pattern["keywords"]:
            if keyword in note_lower:
                flags.append({
                    "name": pattern["name"],
                    "description": pattern["description"],
                    "severity": pattern["severity"],
                    "action": pattern["action"],
                    "source": "deterministic_guardrail",
                })
                seen.add(pattern["name"])
                break

    return flags
