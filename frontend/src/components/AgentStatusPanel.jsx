const AGENTS = ['intake', 'history', 'research', 'differential', 'risk', 'summarizer']

const AGENT_LABELS = {
  intake: 'Intake Parser',
  history: 'History Retrieval',
  research: 'Research RAG',
  differential: 'Differential Dx',
  risk: 'Risk Checker',
  summarizer: 'SOAP Summarizer',
}

export default function AgentStatusPanel({ agentEvents }) {
  const getStatus = (agent) => {
    const events = agentEvents.filter((e) => e.agent === agent)
    if (events.some((e) => e.type === 'done')) return 'done'
    if (events.some((e) => e.type === 'start')) return 'running'
    return 'waiting'
  }

  return (
    <div className="bg-slate-900 border border-slate-700 rounded-xl p-5">
      <p className="text-xs uppercase tracking-widest text-teal-500 mb-4">Agent pipeline</p>
      <div className="space-y-3">
        {AGENTS.map((agent) => {
          const status = getStatus(agent)
          return (
            <div key={agent} className="flex items-center gap-3">
              <div className={`w-2 h-2 rounded-full flex-shrink-0 ${
                status === 'done' ? 'bg-teal-500' :
                status === 'running' ? 'bg-teal-400 animate-pulse' :
                'bg-slate-600'
              }`} />
              <span className={`text-sm ${
                status === 'done' ? 'text-slate-200' :
                status === 'running' ? 'text-teal-400' :
                'text-slate-500'
              }`}>
                {AGENT_LABELS[agent]}
              </span>
              <span className="ml-auto text-xs text-slate-600">
                {status === 'done' ? 'complete' : status === 'running' ? 'running...' : ''}
              </span>
            </div>
          )
        })}
      </div>
    </div>
  )
}
