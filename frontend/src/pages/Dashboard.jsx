import { useState } from 'react'
import { CaseInput, ApprovalGate, SOAPOutput } from '../components/index.jsx'
import AgentStatusPanel from '../components/AgentStatusPanel.jsx'
import { useAgentStream } from '../hooks/useAgentStream.js'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export default function Dashboard() {
  const [threadId, setThreadId] = useState(null)
  const [loading, setLoading] = useState(false)
  const { agentEvents, awaitingApproval, done, error, approve } = useAgentStream(threadId)

  const getDoneOutput = (agent) => {
    const ev = agentEvents.find((e) => e.agent === agent && e.type === 'done')
    return ev?.output || null
  }

  const handleSubmit = async (body) => {
    setLoading(true)
    try {
      const res = await fetch(`${API_URL}/cases/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      })
      const data = await res.json()
      setThreadId(data.thread_id)
    } finally {
      setLoading(false)
    }
  }

  const differential = getDoneOutput('differential')?.differential
  const riskFlags = getDoneOutput('risk')?.risk_flags
  const soapNote = getDoneOutput('summarizer')?.soap_note

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      <nav className="border-b border-slate-800 px-8 py-4 flex items-center gap-3">
        <div className="w-7 h-7 bg-teal-600 rounded-lg flex items-center justify-center">
          <span className="text-white text-xs font-bold">M</span>
        </div>
        <span className="text-sm font-medium text-slate-200">MedAgent</span>
        <span className="ml-auto text-xs text-slate-600">Clinical Intelligence Platform</span>
      </nav>

      <div className="max-w-5xl mx-auto px-8 py-8 grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="space-y-6">
          {!threadId && <CaseInput onSubmit={handleSubmit} loading={loading} />}
          {threadId && <AgentStatusPanel agentEvents={agentEvents} />}
          {awaitingApproval && (
            <ApprovalGate
              onApprove={approve}
              differential={differential}
              riskFlags={riskFlags}
            />
          )}
          {error && (
            <div className="bg-red-950 border border-red-800 rounded-xl p-4 text-sm text-red-300">
              {error}
            </div>
          )}
        </div>

        <div className="space-y-6">
          {soapNote && <SOAPOutput soapNote={soapNote} />}
          {!soapNote && threadId && (
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 text-center">
              <p className="text-sm text-slate-500">SOAP note will appear here after approval</p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
