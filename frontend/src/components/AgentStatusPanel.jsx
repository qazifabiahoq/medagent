const AGENTS = [
  { id: 'intake',       label: 'Intake Parser',      desc: 'Extracts patient demographics & chief complaint' },
  { id: 'history',      label: 'History Retrieval',  desc: 'Pulls prior session records from memory' },
  { id: 'research',     label: 'Research RAG',        desc: 'Searches clinical evidence database' },
  { id: 'differential', label: 'Differential Dx',    desc: 'Generates ranked diagnoses with confidence' },
  { id: 'risk',         label: 'Risk Assessment',    desc: 'Flags critical patient risks' },
  { id: 'summarizer',   label: 'SOAP Summarizer',    desc: 'Produces final structured SOAP note' },
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
          <span className="text-xs font-semibold tabular-nums" style={{ color: doneCount > 0 ? '#818cf8' : '#52525b' }}>
            {doneCount}/{AGENTS.length}
          </span>
        </div>
        {/* Progress bar */}
        <div className="h-1.5 bg-zinc-800 rounded-full overflow-hidden">
          <div
            className="h-full rounded-full transition-all duration-700"
            style={{
              width: `${progress}%`,
              background: progress === 100
                ? 'linear-gradient(90deg, #10b981, #34d399)'
                : 'linear-gradient(90deg, #6366f1, #818cf8)',
            }}
          />
        </div>
      </div>

      <div className="p-4 space-y-1">
        {AGENTS.map((agent, idx) => {
          const status = getStatus(agent.id)
          const isLast = idx === AGENTS.length - 1

          return (
            <div key={agent.id} className="relative" style={{ animationDelay: `${idx * 60}ms` }}>
              {/* Connector line */}
              {!isLast && (
                <div
                  className="absolute left-[11px] top-[26px] w-0.5 h-[calc(100%+4px)] rounded-full transition-colors duration-500"
                  style={{ background: status === 'done' ? '#10b98133' : '#27272a' }}
                />
              )}

              <div className={`relative flex items-start gap-3 px-3 py-2.5 rounded-xl transition-all duration-200 ${
                status === 'running' ? 'bg-indigo-500/8 border border-indigo-500/15' :
                status === 'done' ? '' : 'opacity-40'
              }`}>
                {/* Status dot */}
                <div className={`mt-0.5 w-5 h-5 rounded-full flex-shrink-0 flex items-center justify-center border-2 transition-all duration-300 ${
                  status === 'done'
                    ? 'border-emerald-500 bg-emerald-500 shadow-[0_0_8px_#10b98140]'
                    : status === 'running'
                    ? 'border-indigo-400 bg-indigo-400/20'
                    : 'border-zinc-700 bg-zinc-900'
                }`}>
                  {status === 'done' && (
                    <svg width="10" height="10" viewBox="0 0 10 10" fill="none">
                      <path d="M2 5l2.5 2.5L8 3" stroke="white" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
                    </svg>
                  )}
                  {status === 'running' && (
                    <span className="w-1.5 h-1.5 rounded-full bg-indigo-400 animate-pulse" />
                  )}
                </div>

                <div className="min-w-0 flex-1">
                  <p className={`text-sm font-medium leading-none mb-0.5 ${
                    status === 'done' ? 'text-zinc-200' :
                    status === 'running' ? 'text-white' :
                    'text-zinc-600'
                  }`}>
                    {agent.label}
                  </p>
                  <p className={`text-xs leading-relaxed ${
                    status === 'running' ? 'text-indigo-400/70' : 'text-zinc-700'
                  }`}>
                    {status === 'running' ? 'Running…' : agent.desc}
                  </p>
                </div>

                {status === 'done' && (
                  <span className="ml-auto text-xs text-emerald-500 font-bold flex-shrink-0">✓</span>
                )}
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
