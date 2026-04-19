import { useState } from 'react'
import { CaseInput, ApprovalGate, SOAPOutput } from '../components/index.jsx'
import AgentStatusPanel from '../components/AgentStatusPanel.jsx'
import DifferentialPanel from '../components/DifferentialPanel.jsx'
import { useAgentStream } from '../hooks/useAgentStream.js'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const NAV_ITEMS = [
  { id: 'cases',     label: 'Cases',          icon: CasesIcon },
  { id: 'history',   label: 'Patient History', icon: HistoryIcon },
  { id: 'analytics', label: 'Analytics',       icon: AnalyticsIcon },
]

export default function Dashboard() {
  const [threadId, setThreadId]       = useState(null)
  const [loading, setLoading]         = useState(false)
  const [submitError, setSubmitError] = useState(null)
  const [activeNav, setActiveNav]     = useState('cases')
  const [sidebarOpen, setSidebarOpen] = useState(true)

  const { agentEvents, awaitingApproval, done, error, approve } = useAgentStream(threadId)

  const getDoneOutput = (agent) => {
    const ev = agentEvents.find((e) => e.agent === agent && e.type === 'done')
    return ev?.output || null
  }

  const handleSubmit = async (body) => {
    setLoading(true)
    setSubmitError(null)
    try {
      const res = await fetch(`${API_URL}/cases/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      })
      if (!res.ok) {
        const err = await res.json().catch(() => ({}))
        throw new Error(err.detail || `Server error ${res.status}`)
      }
      const data = await res.json()
      setThreadId(data.thread_id)
    } catch (e) {
      setSubmitError(e.message)
    } finally {
      setLoading(false)
    }
  }

  const handleNewCase = () => setThreadId(null)

  const differential = getDoneOutput('differential')?.differential
  const riskFlags    = getDoneOutput('risk')?.risk_flags
  const soapNote     = getDoneOutput('summarizer')?.soap_note
  const isProcessing = threadId && !done && !awaitingApproval

  return (
    <div className="flex h-screen overflow-hidden bg-slate-100">
      {/* Sidebar */}
      <aside className={`flex flex-col bg-white border-r border-slate-200 transition-all duration-300 shadow-sm ${sidebarOpen ? 'w-60' : 'w-16'}`}>
        {/* Logo */}
        <div className={`flex items-center gap-3 px-4 py-5 border-b border-slate-100 ${!sidebarOpen && 'justify-center'}`}>
          <div className="w-8 h-8 rounded-xl bg-blue-600 flex items-center justify-center flex-shrink-0 shadow-sm">
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
              <path d="M8 2V14M2 8H14" stroke="white" strokeWidth="2.5" strokeLinecap="round"/>
              <path d="M4.5 4.5L11.5 11.5M11.5 4.5L4.5 11.5" stroke="white" strokeWidth="1.2" strokeLinecap="round" opacity="0.5"/>
            </svg>
          </div>
          {sidebarOpen && (
            <div>
              <p className="text-sm font-bold text-slate-900 leading-none tracking-tight">MedAgent</p>
              <p className="text-xs text-slate-400 mt-0.5">Clinical Intelligence</p>
            </div>
          )}
        </div>

        {/* Nav */}
        <nav className="flex-1 px-2 py-4 space-y-0.5">
          {NAV_ITEMS.map(({ id, label, icon: Icon }) => (
            <button
              key={id}
              onClick={() => setActiveNav(id)}
              className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all duration-150
                ${activeNav === id
                  ? 'bg-blue-50 text-blue-700 border border-blue-100'
                  : 'text-slate-500 hover:text-slate-800 hover:bg-slate-50'
                } ${!sidebarOpen && 'justify-center'}`}
            >
              <Icon className="w-4 h-4 flex-shrink-0" />
              {sidebarOpen && <span>{label}</span>}
            </button>
          ))}
        </nav>

        {/* Collapse toggle */}
        <button
          onClick={() => setSidebarOpen(!sidebarOpen)}
          className="mx-2 mb-4 flex items-center justify-center gap-2 px-3 py-2 rounded-xl text-slate-400 hover:text-slate-600 hover:bg-slate-50 transition-all text-xs"
        >
          <svg width="14" height="14" viewBox="0 0 14 14" fill="currentColor">
            <path d={sidebarOpen ? 'M9 7L5 3M9 7L5 11' : 'M5 7L9 3M5 7L9 11'} stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" fill="none"/>
          </svg>
          {sidebarOpen && <span>Collapse</span>}
        </button>
      </aside>

      {/* Main content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Top bar */}
        <header className="flex items-center justify-between px-6 py-4 bg-white border-b border-slate-200 flex-shrink-0 shadow-sm">
          <div>
            <h1 className="text-base font-semibold text-slate-900 tracking-tight">
              {activeNav === 'cases' ? 'Clinical Cases' : activeNav === 'history' ? 'Patient History' : 'Analytics'}
            </h1>
            <p className="text-xs text-slate-400 mt-0.5">
              {threadId ? `Thread: ${threadId.slice(0, 8)}…` : 'Submit a clinical note to begin AI analysis'}
            </p>
          </div>

          <div className="flex items-center gap-3">
            {threadId && (
              <button
                onClick={handleNewCase}
                className="flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-medium text-slate-600 hover:text-slate-900 hover:bg-slate-100 border border-slate-200 transition-all duration-150"
              >
                <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
                  <path d="M6 1v10M1 6h10" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
                </svg>
                New case
              </button>
            )}
            {/* Status badge */}
            <div className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-semibold border transition-all duration-300 ${
              done            ? 'bg-emerald-50 text-emerald-700 border-emerald-200' :
              isProcessing    ? 'bg-blue-50 text-blue-700 border-blue-200' :
              awaitingApproval? 'bg-amber-50 text-amber-700 border-amber-200' :
                                'bg-slate-50 text-slate-400 border-slate-200'
            }`}>
              <span className={`w-1.5 h-1.5 rounded-full ${
                done            ? 'bg-emerald-500' :
                isProcessing    ? 'bg-blue-500 animate-pulse' :
                awaitingApproval? 'bg-amber-500 animate-pulse' :
                                  'bg-slate-300'
              }`} />
              {done ? 'Complete' : isProcessing ? 'Processing' : awaitingApproval ? 'Awaiting approval' : 'Idle'}
            </div>
          </div>
        </header>

        {/* Content area */}
        <main className="flex-1 overflow-auto p-6">
          {!threadId ? (
            <div className="max-w-2xl mx-auto animate-slide-up">
              <div className="mb-8 text-center">
                <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-blue-600 shadow-md mb-4">
                  <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
                    <path d="M12 3v18M3 12h18" stroke="white" strokeWidth="2.5" strokeLinecap="round"/>
                  </svg>
                </div>
                <h2 className="text-xl font-bold text-slate-900 tracking-tight">New Clinical Case</h2>
                <p className="text-sm text-slate-500 mt-1">Paste an unstructured clinical note and let the AI agents analyse it end-to-end</p>
              </div>

              <CaseInput onSubmit={handleSubmit} loading={loading} />

              {submitError && (
                <div className="mt-3 flex items-start gap-2 px-4 py-3 rounded-xl bg-red-50 border border-red-100 text-red-600 text-xs">
                  <span className="font-semibold">Error:</span> {submitError}
                </div>
              )}

              {/* How it works */}
              <div className="mt-8 grid grid-cols-3 gap-4">
                {[
                  { step: '01', title: 'Parse & Structure', desc: 'Intake agent extracts demographics and chief complaint', dot: 'bg-blue-600' },
                  { step: '02', title: 'Research & History', desc: 'Parallel RAG agents pull evidence and patient records', dot: 'bg-violet-600' },
                  { step: '03', title: 'Review & Approve', desc: 'Clinician reviews differential before SOAP is generated', dot: 'bg-emerald-600' },
                ].map(({ step, title, desc, dot }) => (
                  <div key={step} className="card p-4 hover:shadow-md transition-shadow duration-200">
                    <div className={`w-6 h-6 rounded-lg ${dot} flex items-center justify-center mb-3`}>
                      <span className="text-white text-xs font-bold">{step}</span>
                    </div>
                    <p className="text-sm font-semibold text-slate-800 mb-1">{title}</p>
                    <p className="text-xs text-slate-500 leading-relaxed">{desc}</p>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <div className="grid grid-cols-12 gap-5 h-full animate-fade-in">
              {/* Left: Pipeline */}
              <div className="col-span-3 space-y-5">
                <AgentStatusPanel agentEvents={agentEvents} />
                {error && (
                  <div className="card p-4 border-red-200">
                    <div className="flex items-start gap-3">
                      <span className="text-red-500 mt-0.5 text-base">⚠</span>
                      <div>
                        <p className="text-xs font-semibold text-red-600 mb-1">Stream error</p>
                        <p className="text-xs text-slate-500">{error}</p>
                      </div>
                    </div>
                  </div>
                )}
              </div>

              {/* Center: Differential + Approval */}
              <div className="col-span-5 space-y-5 overflow-auto">
                {differential && (
                  <DifferentialPanel differential={differential} riskFlags={riskFlags} />
                )}
                {awaitingApproval && (
                  <ApprovalGate onApprove={approve} differential={differential} riskFlags={riskFlags} />
                )}
                {!differential && !awaitingApproval && (
                  <div className="card p-8 text-center">
                    <div className="w-10 h-10 rounded-full bg-slate-100 flex items-center justify-center mx-auto mb-3">
                      <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
                        <circle cx="9" cy="9" r="7" stroke="#94a3b8" strokeWidth="1.5"/>
                        <path d="M9 6v4M9 12v.5" stroke="#94a3b8" strokeWidth="1.5" strokeLinecap="round"/>
                      </svg>
                    </div>
                    <p className="text-sm font-medium text-slate-500">Analysing clinical data…</p>
                    <p className="text-xs text-slate-400 mt-1">Differential diagnosis will appear here</p>
                  </div>
                )}
              </div>

              {/* Right: SOAP Note */}
              <div className="col-span-4 overflow-auto">
                {soapNote ? (
                  <SOAPOutput soapNote={soapNote} />
                ) : (
                  <div className="card p-8 text-center h-full flex flex-col items-center justify-center">
                    <div className="w-12 h-12 rounded-2xl bg-slate-100 flex items-center justify-center mx-auto mb-3">
                      <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                        <rect x="3" y="2" width="14" height="16" rx="2" stroke="#cbd5e1" strokeWidth="1.5"/>
                        <path d="M7 7h6M7 10h6M7 13h4" stroke="#cbd5e1" strokeWidth="1.5" strokeLinecap="round"/>
                      </svg>
                    </div>
                    <p className="text-sm font-medium text-slate-400">SOAP note</p>
                    <p className="text-xs text-slate-300 mt-1">Generated after clinician approval</p>
                  </div>
                )}
              </div>
            </div>
          )}
        </main>
      </div>
    </div>
  )
}

function CasesIcon({ className }) {
  return (
    <svg className={className} viewBox="0 0 16 16" fill="none">
      <rect x="2" y="1" width="12" height="14" rx="2" stroke="currentColor" strokeWidth="1.4"/>
      <path d="M5 5h6M5 8h6M5 11h4" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round"/>
    </svg>
  )
}

function HistoryIcon({ className }) {
  return (
    <svg className={className} viewBox="0 0 16 16" fill="none">
      <circle cx="8" cy="8" r="6" stroke="currentColor" strokeWidth="1.4"/>
      <path d="M8 5v3.5l2.5 1.5" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round"/>
    </svg>
  )
}

function AnalyticsIcon({ className }) {
  return (
    <svg className={className} viewBox="0 0 16 16" fill="none">
      <path d="M2 13L6 9l3 3 5-6" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round"/>
    </svg>
  )
}
