const AGENTS = [
  { id: 'intake', label: 'Intake Parser', desc: 'Extracts patient demographics & chief complaint' },
  { id: 'history', label: 'History Retrieval', desc: 'Pulls prior session records from memory' },
  { id: 'research', label: 'Research RAG', desc: 'Searches clinical evidence database' },
  { id: 'differential', label: 'Differential Dx', desc: 'Generates ranked diagnoses with confidence' },
  { id: 'risk', label: 'Risk Assessment', desc: 'Flags critical patient risks' },
  { id: 'summarizer', label: 'SOAP Summarizer', desc: 'Produces final structured SOAP note' },
]

export default function AgentStatusPanel({ agentEvents }) {
  const getStatus = (agent) => {
    const events = agentEvents.filter((e) => e.agent === agent)
    if (events.some((e) => e.type === 'done')) return 'done'
    if (events.some((e) => e.type === 'start')) return 'running'
    return 'waiting'
  }

  const doneCount = AGENTS.filter((a) => getStatus(a.id) === 'done').length
  const progress = Math.round((doneCount / AGENTS.length) * 100)

  return (
    <div className="card overflow-hidden">
      <div className="card-header">
        <div className="flex items-center justify-between mb-3">
          <p className="label-xs">Agent Pipeline</p>
          <span className="text-xs font-semibold text-slate-400">{doneCount}/{AGENTS.length}</span>
        </div>
        {/* Progress bar */}
        <div className="h-1.5 bg-slate-800 rounded-full overflow-hidden">
          <div
            className="h-full bg-gradient-to-r from-clinical-blue to-clinical-teal rounded-full transition-all duration-500"
            style={{ width: `${progress}%` }}
          />
        </div>
      </div>

      <div className="p-4 space-y-1">
        {AGENTS.map((agent, idx) => {
          const status = getStatus(agent.id)
          const isLast = idx === AGENTS.length - 1

          return (
            <div key={agent.id} className="relative">
              {/* Connector line */}
              {!isLast && (
                <div className={`absolute left-[11px] top-[26px] w-0.5 h-[calc(100%+4px)] rounded-full ${
                  status === 'done' ? 'bg-clinical-teal/50' : 'bg-slate-800'
                }`} />
              )}

              <div className={`relative flex items-start gap-3 px-3 py-2.5 rounded-xl transition-all duration-200 ${
                status === 'running' ? 'bg-clinical-blue/8 border border-clinical-blue/15' :
                status === 'done' ? 'opacity-100' : 'opacity-50'
              }`}>
                {/* Status dot */}
                <div className={`mt-0.5 w-5 h-5 rounded-full flex-shrink-0 flex items-center justify-center border-2 transition-all ${
                  status === 'done'
                    ? 'bg-clinical-teal border-clinical-teal shadow-sm shadow-teal-900/50'
                    : status === 'running'
                    ? 'bg-clinical-blue/20 border-clinical-blue animate-pulse-slow'
                    : 'bg-navy-900 border-slate-700'
                }`}>
                  {status === 'done' && (
                    <svg width="10" height="10" viewBox="0 0 10 10" fill="none">
                      <path d="M2 5l2.5 2.5L8 3" stroke="white" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
                    </svg>
                  )}
                  {status === 'running' && (
                    <span className="w-1.5 h-1.5 rounded-full bg-clinical-blue" />
                  )}
                </div>

                <div className="min-w-0">
                  <p className={`text-sm font-medium leading-none mb-0.5 ${
                    status === 'done' ? 'text-slate-200' :
                    status === 'running' ? 'text-white' :
                    'text-slate-600'
                  }`}>
                    {agent.label}
                  </p>
                  <p className={`text-xs leading-relaxed ${
                    status === 'running' ? 'text-slate-400' : 'text-slate-700'
                  }`}>
                    {status === 'running' ? 'Running…' : agent.desc}
                  </p>
                </div>

                {status === 'done' && (
                  <span className="ml-auto text-xs text-clinical-teal font-medium flex-shrink-0">✓</span>
                )}
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
