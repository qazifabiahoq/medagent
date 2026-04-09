export function ApprovalGate({ onApprove, differential, riskFlags }) {
  return (
    <div className="bg-slate-900 border border-teal-700 rounded-xl p-6">
      <p className="text-xs uppercase tracking-widest text-teal-500 mb-2">Awaiting clinician approval</p>
      <p className="text-sm text-slate-400 mb-5">
        Review the differential diagnosis and risk flags below before the final SOAP note is generated.
      </p>

      {differential?.length > 0 && (
        <div className="mb-4">
          <p className="text-xs text-slate-500 mb-2 uppercase tracking-wide">Differential</p>
          {differential.map((d, i) => (
            <div key={i} className="flex items-center gap-3 py-1">
              <span className="text-teal-400 text-sm font-medium">{i + 1}.</span>
              <span className="text-slate-200 text-sm">{d.diagnosis}</span>
              <span className="ml-auto text-xs text-slate-500">{Math.round(d.confidence * 100)}%</span>
            </div>
          ))}
        </div>
      )}

      {riskFlags?.length > 0 && (
        <div className="mb-5">
          <p className="text-xs text-slate-500 mb-2 uppercase tracking-wide">Risk flags</p>
          {riskFlags.map((f, i) => (
            <div key={i} className={`text-xs px-3 py-1 rounded-full inline-block mr-2 mb-1 ${
              f.severity === 'critical' ? 'bg-red-900 text-red-300' :
              f.severity === 'moderate' ? 'bg-yellow-900 text-yellow-300' :
              'bg-slate-700 text-slate-300'
            }`}>
              {f.description}
            </div>
          ))}
        </div>
      )}

      <button
        onClick={onApprove}
        className="w-full bg-teal-600 hover:bg-teal-500 text-white text-sm font-medium py-2.5 rounded-lg transition-colors"
      >
        Approve and generate SOAP note
      </button>
    </div>
  )
}

export function SOAPOutput({ soapNote }) {
  if (!soapNote) return null
  const sections = ['subjective', 'objective', 'assessment', 'plan']

  return (
    <div className="bg-slate-900 border border-slate-700 rounded-xl p-6">
      <p className="text-xs uppercase tracking-widest text-teal-500 mb-4">SOAP note</p>
      {sections.map((section) => (
        <div key={section} className="mb-4">
          <p className="text-xs uppercase tracking-wide text-slate-500 mb-1">{section}</p>
          <p className="text-sm text-slate-200 leading-relaxed">{soapNote[section]}</p>
        </div>
      ))}
    </div>
  )
}

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
    <form onSubmit={handleSubmit} className="bg-slate-900 border border-slate-700 rounded-xl p-6 space-y-4">
      <p className="text-xs uppercase tracking-widest text-teal-500">New case</p>
      <div>
        <label className="text-xs text-slate-500 block mb-1">Patient ID</label>
        <input
          name="patient_id"
          required
          className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-200 outline-none focus:border-teal-600"
          placeholder="e.g. PT-00123"
        />
      </div>
      <div>
        <label className="text-xs text-slate-500 block mb-1">Clinical note</label>
        <textarea
          name="raw_note"
          required
          rows={6}
          className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-200 outline-none focus:border-teal-600 resize-none"
          placeholder="Paste unstructured clinical note here..."
        />
      </div>
      <button
        type="submit"
        disabled={loading}
        className="w-full bg-teal-600 hover:bg-teal-500 disabled:opacity-50 text-white text-sm font-medium py-2.5 rounded-lg transition-colors"
      >
        {loading ? 'Submitting...' : 'Submit case'}
      </button>
    </form>
  )
}
