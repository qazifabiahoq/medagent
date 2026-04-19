const SEVERITY_CONFIG = {
  critical: {
    badge: 'badge-critical',
    icon: (
      <svg width="10" height="10" viewBox="0 0 10 10" fill="none">
        <path d="M5 1.5L9 8.5H1L5 1.5Z" stroke="currentColor" strokeWidth="1.2" strokeLinejoin="round"/>
        <path d="M5 4.5v1.5M5 7.5v.2" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round"/>
      </svg>
    ),
  },
  moderate: {
    badge: 'badge-moderate',
    icon: (
      <svg width="10" height="10" viewBox="0 0 10 10" fill="none">
        <circle cx="5" cy="5" r="4" stroke="currentColor" strokeWidth="1.2"/>
        <path d="M5 3v2.5M5 7v.2" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round"/>
      </svg>
    ),
  },
  low: {
    badge: 'badge-low',
    icon: (
      <svg width="10" height="10" viewBox="0 0 10 10" fill="none">
        <circle cx="5" cy="5" r="4" stroke="currentColor" strokeWidth="1.2"/>
        <path d="M3.5 5h3" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round"/>
      </svg>
    ),
  },
}

function getConfStyle(conf) {
  if (conf >= 0.75) return { bar: 'linear-gradient(90deg,#059669,#10b981)', text: '#059669' }
  if (conf >= 0.5)  return { bar: 'linear-gradient(90deg,#2563eb,#3b82f6)', text: '#2563eb' }
  if (conf >= 0.3)  return { bar: 'linear-gradient(90deg,#d97706,#f59e0b)', text: '#d97706' }
  return              { bar: 'linear-gradient(90deg,#94a3b8,#cbd5e1)',       text: '#94a3b8' }
}

export default function DifferentialPanel({ differential, riskFlags }) {
  return (
    <div className="space-y-4 animate-slide-up">
      {/* Differential Diagnosis */}
      {differential?.length > 0 && (
        <div className="card overflow-hidden">
          <div className="card-header flex items-center justify-between">
            <div className="flex items-center gap-2.5">
              <div className="w-7 h-7 rounded-lg bg-blue-50 border border-blue-100 flex items-center justify-center">
                <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
                  <path d="M6 1v10M2 5h8M2 8h8" stroke="#2563eb" strokeWidth="1.3" strokeLinecap="round"/>
                </svg>
              </div>
              <p className="text-sm font-semibold text-slate-900">Differential Diagnosis</p>
            </div>
            <span className="text-xs text-slate-400">{differential.length} conditions</span>
          </div>

          <div className="p-4 space-y-3">
            {differential.map((d, i) => {
              const conf   = d.confidence ?? 0
              const pct    = Math.round(conf * 100)
              const style  = getConfStyle(conf)
              const rank   = i + 1

              return (
                <div key={i} className="group">
                  <div className="flex items-center gap-3 mb-1.5">
                    <span
                      className="w-6 h-6 rounded-lg flex items-center justify-center text-xs font-bold flex-shrink-0 transition-transform duration-150 group-hover:scale-105"
                      style={
                        rank === 1 ? { background: '#ecfdf5', color: '#059669', border: '1px solid #d1fae5' } :
                        rank === 2 ? { background: '#eff6ff', color: '#2563eb', border: '1px solid #dbeafe' } :
                                     { background: '#f8fafc', color: '#94a3b8', border: '1px solid #e2e8f0' }
                      }
                    >
                      {rank}
                    </span>

                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-slate-800 truncate">{d.diagnosis}</p>
                    </div>

                    <span className="text-xs font-bold flex-shrink-0" style={{ color: style.text }}>
                      {pct}%
                    </span>
                  </div>

                  <div className="ml-9 h-1.5 bg-slate-100 rounded-full overflow-hidden">
                    <div
                      className="h-full rounded-full conf-bar"
                      style={{ width: `${pct}%`, background: style.bar }}
                    />
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      )}

      {/* Risk Flags */}
      {riskFlags?.length > 0 && (
        <div className="card overflow-hidden">
          <div className="card-header flex items-center justify-between">
            <div className="flex items-center gap-2.5">
              <div className="w-7 h-7 rounded-lg bg-red-50 border border-red-100 flex items-center justify-center">
                <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
                  <path d="M6 1L11 10H1L6 1Z" stroke="#dc2626" strokeWidth="1.3" strokeLinejoin="round"/>
                  <path d="M6 4.5v2M6 8v.3" stroke="#dc2626" strokeWidth="1.3" strokeLinecap="round"/>
                </svg>
              </div>
              <p className="text-sm font-semibold text-slate-900">Risk Flags</p>
            </div>
            {riskFlags.some((f) => f.severity === 'critical') && (
              <span className="badge-critical">Critical</span>
            )}
          </div>

          <div className="p-4 space-y-2">
            {riskFlags.map((flag, i) => {
              const sev = flag.severity?.toLowerCase() || 'low'
              const cfg = SEVERITY_CONFIG[sev] || SEVERITY_CONFIG.low

              return (
                <div
                  key={i}
                  className={`flex items-start gap-3 p-3 rounded-xl border ${
                    sev === 'critical' ? 'bg-red-50 border-red-100' :
                    sev === 'moderate' ? 'bg-amber-50 border-amber-100' :
                                        'bg-slate-50 border-slate-100'
                  }`}
                >
                  <span className={`mt-0.5 flex-shrink-0 ${
                    sev === 'critical' ? 'text-red-500' :
                    sev === 'moderate' ? 'text-amber-500' :
                                        'text-slate-400'
                  }`}>
                    {cfg.icon}
                  </span>
                  <div className="min-w-0 flex-1">
                    <p className="text-sm text-slate-700">{flag.description}</p>
                    {flag.recommendation && (
                      <p className="text-xs text-slate-400 mt-0.5 leading-relaxed">{flag.recommendation}</p>
                    )}
                  </div>
                  <span className={`badge flex-shrink-0 ${cfg.badge}`}>{sev}</span>
                </div>
              )
            })}
          </div>
        </div>
      )}
    </div>
  )
}
