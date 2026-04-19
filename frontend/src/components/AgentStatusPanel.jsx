const AGENTS = [
  { id: 'intake',       label: 'Intake Parser',     desc: 'Extracts patient demographics & chief complaint' },
  { id: 'history',      label: 'History Retrieval', desc: 'Pulls prior session records from memory' },
  { id: 'research',     label: 'Research RAG',       desc: 'Searches clinical evidence database' },
  { id: 'differential', label: 'Differential Dx',   desc: 'Generates ranked diagnoses with confidence' },
  { id: 'risk',         label: 'Risk Assessment',   desc: 'Flags critical patient risks' },
  { id: 'summarizer',   label: 'SOAP Summarizer',   desc: 'Produces final structured SOAP note' },
]

export default function AgentStatusPanel({ agentEvents }) {
  const getStatus = (agent) => {
    const events = agentEvents.filter((e) => e.agent === agent)
    if (events.some((e) => e.type === 'done'))  return 'done'
    if (events.some((e) => e.type === 'start')) return 'running'
    return 'waiting'
  }

  const doneCount = AGENTS.filter((a) => getStatus(a.id) === 'done').length
  const progress  = Math.round((doneCount / AGENTS.length) * 100)

  return (
    <div className="card overflow-hidden">
      <div className="card-header">
        <div className="flex items-center justify-between mb-3">
          <p className="label-xs">Agent Pipeline</p>
          <span className="text-xs font-semibold tabular-nums text-slate-500">
            {doneCount}/{AGENTS.length}
          </span>
        </div>
        {/* Progress bar */}
        <div className="h-1.5 bg-slate-100 rounded-full overflow-hidden">
          <div
            className="h-full rounded-full transition-all duration-700"
            style={{
              width: `${progress}%`,
              background: progress === 100
                ? 'linear-gradient(90deg, #059669, #10b981)'
                : 'linear-gradient(90deg, #2563eb, #3b82f6)',
            }}
          />
        </div>
      </div>

      <div className="p-4 space-y-1">
        {AGENTS.map((agent, idx) => {
          const status = getStatus(agent.id)
          const isLast = idx === AGENTS.length - 1

          return (
            <div key={agent.id} className="relative">
              {!isLast && (
                <div
                  className="absolute left-[11px] top-[26px] w-0.5 h-[calc(100%+4px)] rounded-full transition-colors duration-500"
                  style={{ background: status === 'done' ? '#bbf7d0' : '#e2e8f0' }}
                />
              )}

              <div className={`relative flex items-start gap-3 px-3 py-2.5 rounded-xl transition-all duration-200 ${
                status === 'running'
                  ? 'bg-blue-50 border border-blue-100'
                  : status === 'done'
                  ? ''
                  : 'opacity-40'
              }`}>
                {/* Status dot */}
                <div className={`mt-0.5 w-5 h-5 rounded-full flex-shrink-0 flex items-center justify-center border-2 transition-all duration-300 ${
                  status === 'done'    ? 'bg-emerald-500 border-emerald-500' :
                  status === 'running' ? 'bg-white border-blue-500' :
                                        'bg-white border-slate-300'
                }`}>
                  {status === 'done' && (
                    <svg width="10" height="10" viewBox="0 0 10 10" fill="none">
                      <path d="M2 5l2.5 2.5L8 3" stroke="white" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
                    </svg>
                  )}
                  {status === 'running' && (
                    <span className="w-2 h-2 rounded-full bg-blue-500 animate-pulse" />
                  )}
                </div>

                <div className="min-w-0 flex-1">
                  <p className={`text-sm font-medium leading-none mb-0.5 ${
                    status === 'done'    ? 'text-slate-700' :
                    status === 'running' ? 'text-slate-900' :
                                          'text-slate-400'
                  }`}>
                    {agent.label}
                  </p>
                  <p className={`text-xs leading-relaxed ${
                    status === 'running' ? 'text-blue-600' : 'text-slate-400'
                  }`}>
                    {status === 'running' ? 'Running…' : agent.desc}
                  </p>
                </div>

                {status === 'done' && (
                  <span className="ml-auto text-xs text-emerald-600 font-bold flex-shrink-0">✓</span>
                )}
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
