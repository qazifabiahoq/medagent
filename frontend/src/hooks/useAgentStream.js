import { useState, useEffect, useCallback, useRef } from 'react'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export function useAgentStream(threadId) {
  const [agentEvents, setAgentEvents]       = useState([])
  const [awaitingApproval, setAwaitingApproval] = useState(false)
  const [done, setDone]                     = useState(false)
  const [error, setError]                   = useState(null)
  // Incrementing this triggers SSE reconnect (used after approval)
  const [streamEpoch, setStreamEpoch]       = useState(0)
  const esRef = useRef(null)

  useEffect(() => {
    if (!threadId) return

    // Close any previous connection before opening a new one
    if (esRef.current) esRef.current.close()

    const es = new EventSource(`${API_URL}/stream/${threadId}`)
    esRef.current = es

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

    es.addEventListener('error', (e) => {
      try {
        const data = JSON.parse(e.data)
        setError(data.error || 'Agent pipeline error')
      } catch {
        setError('Agent pipeline error')
      }
      es.close()
    })

    es.onerror = () => {
      setError('Stream connection lost')
      es.close()
    }

    return () => es.close()
  }, [threadId, streamEpoch])

  const approve = useCallback(async () => {
    if (!threadId) return
    await fetch(`${API_URL}/approve/${threadId}`, { method: 'POST' })
    setAwaitingApproval(false)
    // Reconnect SSE so the summarizer events stream through
    setStreamEpoch((n) => n + 1)
  }, [threadId])

  return { agentEvents, awaitingApproval, done, error, approve }
}
