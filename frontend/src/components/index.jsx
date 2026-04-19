// ─── Demo scenarios ───────────────────────────────────────────────────────────
const DEMO_CASES = [
  {
    label: 'Chest Pain',
    patient_id: 'PT-DEMO-001',
    note: `62-year-old male presenting to ED with 45-minute history of central chest pain radiating to left arm and jaw. Pain is pressure-like, 8/10 severity. Associated with diaphoresis and nausea. No vomiting. PMH: hypertension, type 2 diabetes mellitus (on metformin 1g BD, lisinopril 10mg OD). Smokes 20 cigarettes/day for 35 years. FH: father died of MI aged 58.

Vitals on arrival: BP 158/94 mmHg, HR 98 bpm, RR 18/min, Temp 36.8°C, SpO2 97% on room air.

ECG: ST elevation in leads II, III, aVF consistent with inferior STEMI. Troponin I pending.

Allergies: Aspirin (rash — given in 2019, developed urticaria). No known drug allergies otherwise.

Current medications: Metformin 1g BD, Lisinopril 10mg OD, Atorvastatin 40mg nocte.`,
  },
  {
    label: 'Pneumonia',
    patient_id: 'PT-DEMO-002',
    note: `45-year-old female presenting with 5-day history of productive cough with yellow-green sputum, fever up to 39.2°C, right-sided pleuritic chest pain, and progressive dyspnea. Reports rigors on day 2. No hemoptysis.

PMH: Type 2 diabetes (HbA1c 8.9% last month), no prior respiratory admissions.
Medications: Metformin 500mg BD, Glipizide 5mg OD.
Allergies: Penicillin (anaphylaxis — documented in 2018).

Vitals: Temp 38.9°C, BP 122/78 mmHg, HR 104 bpm, RR 24/min, SpO2 94% on room air.

Examination: Dull to percussion right lower zone, bronchial breath sounds right base, increased vocal fremitus.

CXR: Right lower lobe consolidation. WBC 16.2 × 10⁹/L with left shift. CRP 187 mg/L.`,
  },
  {
    label: 'Pediatric Asthma',
    patient_id: 'PT-DEMO-003',
    note: `9-year-old male brought in by mother with 2-day history of worsening shortness of breath, wheeze, and dry cough. Symptoms started after visiting a friend's house with cats. Using salbutamol inhaler (prescribed 6 months ago) 6 times today with minimal relief.

PMH: Asthma diagnosed age 5, eczema. No prior hospital admissions for asthma. No ICU history.
Medications: Salbutamol 100mcg PRN (MDI), Fluticasone 50mcg BD (MDI).
Allergies: None known.

Vitals: Temp 37.1°C, HR 118 bpm, RR 32/min, SpO2 91% on room air.

Examination: Audible wheeze bilaterally, accessory muscle use, subcostal recession, speaking in short sentences. Peak flow 40% predicted. No cyanosis.`,
  },
]

// ─── CaseInput ───────────────────────────────────────────────────────────────
export function CaseInput({ onSubmit, loading }) {
  const handleSubmit = (e) => {
    e.preventDefault()
    const form = e.target
    onSubmit({
      patient_id: form.patient_id.value,
      raw_note: form.raw_note.value,
    })
  }

  const loadDemo = (demo, e) => {
    // Walk up to the parent form and set uncontrolled input values
    const form = e.currentTarget.closest('form')
    form.querySelector('input[name="patient_id"]').value = demo.patient_id
    form.querySelector('textarea[name="raw_note"]').value = demo.note
  }

  return (
    <form onSubmit={handleSubmit} className="card p-6 space-y-5">
      <div className="flex items-center gap-3 mb-1">
        <div className="w-8 h-8 rounded-lg bg-clinical-blue/15 border border-clinical-blue/20 flex items-center justify-center">
          <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
            <rect x="1" y="1" width="12" height="12" rx="2" stroke="#3b82f6" strokeWidth="1.3"/>
            <path d="M4 5h6M4 7.5h6M4 10h4" stroke="#3b82f6" strokeWidth="1.3" strokeLinecap="round"/>
          </svg>
        </div>
        <div>
          <p className="text-sm font-semibold text-white">Patient intake</p>
          <p className="text-xs text-slate-500">Enter patient details and clinical note</p>
        </div>
      </div>

      {/* Demo scenario loader */}
      <div>
        <p className="text-xs font-semibold text-slate-500 mb-2">Load demo scenario</p>
        <div className="flex gap-2 flex-wrap">
          {DEMO_CASES.map((demo) => (
            <button
              key={demo.label}
              type="button"
              onClick={(e) => loadDemo(demo, e)}
              className="px-3 py-1.5 rounded-lg text-xs font-medium bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white border border-slate-700 hover:border-slate-600 transition-all"
            >
              {demo.label}
            </button>
          ))}
        </div>
        <p className="text-xs text-slate-700 mt-1.5">
          Click a scenario to pre-fill the form with a realistic clinical note
        </p>
      </div>

      <div className="space-y-4">
        <div>
          <label className="block text-xs font-semibold text-slate-400 mb-2">
            Patient ID <span className="text-red-500">*</span>
          </label>
          <input
            name="patient_id"
            required
            className="input-field"
            placeholder="e.g. PT-00123"
          />
        </div>

        <div>
          <label className="block text-xs font-semibold text-slate-400 mb-2">
            Unstructured clinical note <span className="text-red-500">*</span>
          </label>
          <textarea
            name="raw_note"
            required
            rows={9}
            className="input-field resize-none leading-relaxed"
            placeholder="Paste the raw clinical note here… or load a demo scenario above."
          />
          <p className="text-xs text-slate-700 mt-1.5">Free text, structured notes, or discharge summaries — any format accepted</p>
        </div>
      </div>

      <button type="submit" disabled={loading} className="btn-primary w-full">
        {loading ? (
          <>
            <svg className="animate-spin w-4 h-4" viewBox="0 0 16 16" fill="none">
              <circle cx="8" cy="8" r="6" stroke="currentColor" strokeWidth="2" strokeDasharray="30 10"/>
            </svg>
            Submitting…
          </>
        ) : (
          <>
            <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
              <path d="M7 1v12M1 7h12" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
            </svg>
            Start AI Analysis
          </>
        )}
      </button>
    </form>
  )
}

// ─── ApprovalGate ─────────────────────────────────────────────────────────────
export function ApprovalGate({ onApprove }) {
  return (
    <div className="card border-amber-800/50 overflow-hidden animate-slide-up">
      <div className="h-1 bg-gradient-to-r from-amber-500 to-amber-600" />

      <div className="p-6">
        <div className="flex items-start gap-3 mb-5">
          <div className="w-9 h-9 rounded-xl bg-amber-900/40 border border-amber-800/50 flex items-center justify-center flex-shrink-0">
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
              <path d="M8 2L14.5 13H1.5L8 2Z" stroke="#f59e0b" strokeWidth="1.4" strokeLinejoin="round"/>
              <path d="M8 6.5v3M8 11v.5" stroke="#f59e0b" strokeWidth="1.4" strokeLinecap="round"/>
            </svg>
          </div>
          <div>
            <p className="text-sm font-bold text-amber-400">Clinician Review Required</p>
            <p className="text-xs text-slate-400 mt-0.5 leading-relaxed">
              The AI has completed its analysis. Please review the differential diagnosis and risk flags before authorising the final SOAP note. No note is generated without your approval.
            </p>
          </div>
        </div>

        <button onClick={onApprove} className="btn-approve w-full">
          <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
            <path d="M2.5 7.5L5.5 10.5L11.5 4" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
          </svg>
          Approve & Generate SOAP Note
        </button>
      </div>
    </div>
  )
}

// ─── SOAPOutput ───────────────────────────────────────────────────────────────
const SOAP_SECTIONS = [
  {
    key: 'subjective',
    label: 'Subjective',
    abbr: 'S',
    color: 'text-clinical-blue-light',
    bg: 'bg-clinical-blue/10',
    border: 'border-clinical-blue/20',
  },
  {
    key: 'objective',
    label: 'Objective',
    abbr: 'O',
    color: 'text-purple-400',
    bg: 'bg-purple-900/20',
    border: 'border-purple-800/30',
  },
  {
    key: 'assessment',
    label: 'Assessment',
    abbr: 'A',
    color: 'text-amber-400',
    bg: 'bg-amber-900/20',
    border: 'border-amber-800/30',
  },
  {
    key: 'plan',
    label: 'Plan',
    abbr: 'P',
    color: 'text-clinical-teal',
    bg: 'bg-clinical-teal/10',
    border: 'border-clinical-teal/20',
  },
]

export function SOAPOutput({ soapNote }) {
  if (!soapNote) return null

  return (
    <div className="card overflow-hidden animate-slide-up">
      <div className="h-1 bg-gradient-to-r from-clinical-teal to-clinical-blue" />

      <div className="card-header flex items-center justify-between">
        <div className="flex items-center gap-2.5">
          <div className="w-7 h-7 rounded-lg bg-clinical-teal/15 border border-clinical-teal/20 flex items-center justify-center">
            <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
              <rect x="1" y="1" width="10" height="10" rx="1.5" stroke="#0d9488" strokeWidth="1.2"/>
              <path d="M3 4h6M3 6h6M3 8h4" stroke="#0d9488" strokeWidth="1.2" strokeLinecap="round"/>
            </svg>
          </div>
          <p className="text-sm font-semibold text-white">SOAP Note</p>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="w-2 h-2 rounded-full bg-clinical-teal" />
          <span className="text-xs text-clinical-teal font-medium">AI Generated</span>
        </div>
      </div>

      <div className="p-5 space-y-4">
        {SOAP_SECTIONS.map(({ key, label, abbr, color, bg, border }) => {
          const content = soapNote[key]
          if (!content) return null
          return (
            <div key={key} className={`rounded-xl border p-4 ${bg} ${border}`}>
              <div className="flex items-center gap-2 mb-2">
                <span className={`text-xs font-bold ${color} w-5 h-5 rounded flex items-center justify-center ${bg} border ${border}`}>
                  {abbr}
                </span>
                <p className={`text-xs font-semibold uppercase tracking-wider ${color}`}>{label}</p>
              </div>
              <p className="text-sm text-slate-200 leading-relaxed">{content}</p>
            </div>
          )
        })}
      </div>

      {/* Mandatory AI disclaimer */}
      <div className="px-5 pb-5">
        <div className="rounded-lg bg-slate-800/60 border border-slate-700/60 p-3">
          <p className="text-xs text-slate-500 leading-relaxed">
            <span className="text-amber-500 font-semibold">⚠ Advisory only.</span>{' '}
            AI-generated output for clinical decision support. Not a substitute for professional clinical judgment.
            Must be reviewed and validated by a licensed clinician before any action is taken.
          </p>
        </div>
      </div>
    </div>
  )
}
