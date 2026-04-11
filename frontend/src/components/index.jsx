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
            rows={8}
            className="input-field resize-none leading-relaxed"
            placeholder="Paste the raw clinical note here…&#10;&#10;Example: 45-year-old male presenting with 3-day history of productive cough, fever 38.9°C, and right-sided chest pain. Hx of type 2 diabetes. SpO2 94% on room air…"
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
      {/* Amber top strip */}
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
              The AI has completed its analysis. Please review the differential diagnosis and risk flags before authorising the final SOAP note.
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
      {/* Teal top strip */}
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

      {/* Footer */}
      <div className="px-5 pb-4 flex items-center justify-between">
        <p className="text-xs text-slate-700">Generated by MedAgent AI · For clinical review only</p>
        <button className="text-xs text-slate-500 hover:text-slate-300 transition-colors flex items-center gap-1">
          <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
            <path d="M2 2h8v8H2zM4 5h4M4 7h2" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round"/>
          </svg>
          Export
        </button>
      </div>
    </div>
  )
}
