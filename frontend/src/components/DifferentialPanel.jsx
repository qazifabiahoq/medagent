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

// Color scale for confidence bars
function getConfColor(conf) {
  if (conf >= 0.75) return 'from-clinical-teal to-clinical-teal-light'
  if (conf >= 0.5) return 'from-clinical-blue to-clinical-blue-light'
  if (conf >= 0.3) return 'from-amber-600 to-amber-500'
  return 'from-slate-600 to-slate-500'
}

export default function DifferentialPanel({ differential, riskFlags }) {
  return (
    <div className="space-y-4 animate-slide-up">
      {/* Differential Diagnosis */}
      {differential?.length > 0 && (
        <div className="card overflow-hidden">
          <div className="card-header flex items-center justify-between">
            <div className="flex items-center gap-2.5">
              <div className="w-7 h-7 rounded-lg bg-clinical-blue/15 border border-clinical-blue/20 flex items-center justify-center">
                <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
                  <path d="M6 1v10M2 5h8M2 8h8" stroke="#3b82f6" strokeWidth="1.3" strokeLinecap="round"/>
                </svg>
              </div>
              <p className="text-sm font-semibold text-white">Differential Diagnosis</p>
            </div>
            <span className="text-xs text-slate-500">{differential.length} conditions</span>
          </div>

          <div className="p-4 space-y-3">
            {differential.map((d, i) => {
              const conf = d.confidence ?? 0
              const pct = Math.round(conf * 100)
              const barColor = getConfColor(conf)
              const rank = i + 1

              return (
                <div key={i} className="group">
                  <div className="flex items-center gap-3 mb-1.5">
                    {/* Rank badge */}
                    <span className={`w-6 h-6 rounded-lg flex items-center justify-center text-xs font-bold flex-shrink-0 ${
                      rank === 1
                        ? 'bg-clinical-teal/20 text-clinical-teal border border-clinical-teal/30'
                        : rank === 2
                        ? 'bg-clinical-blue/15 text-clinical-blue-light border border-clinical-blue/20'
                        : 'bg-slate-800 text-slate-500 border border-slate-700'
                    }`}>
                      {rank}
                    </span>

                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-slate-200 truncate">
                        {d.diagnosis}
                      </p>
                    </div>

                    <span className={`text-xs font-bold flex-shrink-0 ${
                      pct >= 75 ? 'text-clinical-teal' :
                      pct >= 50 ? 'text-clinical-blue-light' :
                      pct >= 30 ? 'text-amber-400' :
                      'text-slate-500'
                    }`}>
                      {pct}%
                    </span>
                  </div>

                  {/* Confidence bar */}
                  <div className="ml-9 h-1.5 bg-slate-800 rounded-full overflow-hidden">
                    <div
                      className={`h-full bg-gradient-to-r ${barColor} rounded-full conf-bar`}
                      style={{ width: `${pct}%` }}
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
              <div className="w-7 h-7 rounded-lg bg-red-900/30 border border-red-800/40 flex items-center justify-center">
                <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
                  <path d="M6 1L11 10H1L6 1Z" stroke="#f87171" strokeWidth="1.3" strokeLinejoin="round"/>
                  <path d="M6 4.5v2M6 8v.3" stroke="#f87171" strokeWidth="1.3" strokeLinecap="round"/>
                </svg>
              </div>
              <p className="text-sm font-semibold text-white">Risk Flags</p>
            </div>
            {riskFlags.some((f) => f.severity === 'critical') && (
              <span className="badge-critical text-xs">
                Critical
              </span>
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
                    sev === 'critical'
                      ? 'bg-red-950/40 border-red-900/50'
                      : sev === 'moderate'
                      ? 'bg-amber-950/30 border-amber-900/40'
                      : 'bg-slate-800/40 border-slate-700/50'
                  }`}
                >
                  <span className={`mt-0.5 flex-shrink-0 ${cfg.badge.includes('critical') ? 'text-red-400' : cfg.badge.includes('moderate') ? 'text-amber-400' : 'text-slate-400'}`}>
                    {cfg.icon}
                  </span>
                  <div className="min-w-0 flex-1">
                    <p className="text-sm text-slate-200">{flag.description}</p>
                    {flag.recommendation && (
                      <p className="text-xs text-slate-500 mt-0.5 leading-relaxed">{flag.recommendation}</p>
                    )}
                  </div>
                  <span className={`badge flex-shrink-0 ${cfg.badge}`}>
                    {sev}
                  </span>
                </div>
              )
            })}
          </div>
        </div>
      )}
    </div>
  )
}
