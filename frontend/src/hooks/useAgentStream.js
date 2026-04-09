import { useState, useEffect, useCallback } from 'react'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export function useAgentStream(threadId) {
  const [agentEvents, setAgentEvents] = useState([])
  const [awaitingApproval, setAwaitingApproval] = useState(false)
  const [done, setDone] = useState(false)
  const [error, setError] = useState(null)

  useEffect(() => {
    if (!threadId) return

    const es = new EventSource(`${API_URL}/stream/${threadId}`)

    es.addEventListener('agent_start', (e) => {
      const data = JSON.parse(e.data)
      setAgentEvents((prev) => [...prev, { type: 'start', agent: data.agent, ts: Date.now() }])
    })

    es.addEventListener('agent_done', (e) => {
      const data = JSON.parse(e.data)
      setAgentEvents((prev) => [...prev, { type: 'done', agent: data.agent, output: data.output, ts: Date.now() }])
    })

    es.addEventListener('awaiting_approval', () => {
      setAwaitingApproval(true)
      es.close()
    })

    es.addEventListener('done', () => {
      setDone(true)
      es.close()
    })

    es.onerror = () => {
      setError('Stream connection lost')
      es.close()
    }

    return () => es.close()
  }, [threadId])

  const approve = useCallback(async () => {
    if (!threadId) return
    await fetch(`${API_URL}/approve/${threadId}`, { method: 'POST' })
    setAwaitingApproval(false)
  }, [threadId])

  return { agentEvents, awaitingApproval, done, error, approve }
}
