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

function getConfColor(conf) {
  if (conf >= 0.75) return ['#10b981', '#34d399']
  if (conf >= 0.5)  return ['#6366f1', '#818cf8']
  if (conf >= 0.3)  return ['#d97706', '#f59e0b']
  return ['#52525b', '#71717a']
}

function getConfTextColor(pct) {
  if (pct >= 75) return '#10b981'
  if (pct >= 50) return '#818cf8'
  if (pct >= 30) return '#f59e0b'
  return '#52525b'
}

export default function DifferentialPanel({ differential, riskFlags }) {
  return (
    <div className="space-y-4 animate-slide-up">
      {/* Differential Diagnosis */}
      {differential?.length > 0 && (
        <div className="card overflow-hidden">
          <div className="card-header flex items-center justify-between">
            <div className="flex items-center gap-2.5">
              <div className="w-7 h-7 rounded-lg bg-indigo-500/12 border border-indigo-500/18 flex items-center justify-center">
                <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
                  <path d="M6 1v10M2 5h8M2 8h8" stroke="#818cf8" strokeWidth="1.3" strokeLinecap="round"/>
                </svg>
              </div>
              <p className="text-sm font-semibold text-white">Differential Diagnosis</p>
            </div>
            <span className="text-xs text-zinc-500">{differential.length} conditions</span>
          </div>

          <div className="p-4 space-y-3">
            {differential.map((d, i) => {
              const conf = d.confidence ?? 0
              const pct = Math.round(conf * 100)
              const [from, to] = getConfColor(conf)
              const rank = i + 1

              return (
                <div key={i} className="group" style={{ animationDelay: `${i * 50}ms` }}>
                  <div className="flex items-center gap-3 mb-1.5">
                    {/* Rank badge */}
                    <span
                      className="w-6 h-6 rounded-lg flex items-center justify-center text-xs font-bold flex-shrink-0 transition-transform duration-150 group-hover:scale-110"
                      style={
                        rank === 1
                          ? { background: '#10b98118', color: '#10b981', border: '1px solid #10b98130' }
                          : rank === 2
                          ? { background: '#6366f115', color: '#818cf8', border: '1px solid #6366f125' }
                          : { background: '#27272a', color: '#71717a', border: '1px solid #3f3f46' }
                      }
                    >
                      {rank}
                    </span>

                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-zinc-200 truncate">{d.diagnosis}</p>
                    </div>

                    <span className="text-xs font-bold flex-shrink-0" style={{ color: getConfTextColor(pct) }}>
                      {pct}%
                    </span>
                  </div>

                  {/* Confidence bar */}
                  <div className="ml-9 h-1.5 bg-zinc-800 rounded-full overflow-hidden">
                    <div
                      className="h-full rounded-full conf-bar"
                      style={{
                        width: `${pct}%`,
                        background: `linear-gradient(90deg, ${from}, ${to})`,
                      }}
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
              <div className="w-7 h-7 rounded-lg bg-red-900/25 border border-red-800/35 flex items-center justify-center">
                <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
                  <path d="M6 1L11 10H1L6 1Z" stroke="#f87171" strokeWidth="1.3" strokeLinejoin="round"/>
                  <path d="M6 4.5v2M6 8v.3" stroke="#f87171" strokeWidth="1.3" strokeLinecap="round"/>
                </svg>
              </div>
              <p className="text-sm font-semibold text-white">Risk Flags</p>
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
                  className={`flex items-start gap-3 p-3 rounded-xl border transition-all duration-150 ${
                    sev === 'critical'
                      ? 'bg-red-950/35 border-red-900/45'
                      : sev === 'moderate'
                      ? 'bg-amber-950/25 border-amber-900/35'
                      : 'bg-zinc-800/35 border-zinc-700/45'
                  }`}
                  style={{ animationDelay: `${i * 60}ms` }}
                >
                  <span className={`mt-0.5 flex-shrink-0 ${
                    sev === 'critical' ? 'text-red-400' :
                    sev === 'moderate' ? 'text-amber-400' :
                    'text-zinc-400'
                  }`}>
                    {cfg.icon}
                  </span>
                  <div className="min-w-0 flex-1">
                    <p className="text-sm text-zinc-200">{flag.description}</p>
                    {flag.recommendation && (
                      <p className="text-xs text-zinc-500 mt-0.5 leading-relaxed">{flag.recommendation}</p>
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
