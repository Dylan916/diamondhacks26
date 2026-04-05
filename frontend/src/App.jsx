import { useState, useRef, useCallback } from 'react'
import CredentialsForm from './components/CredentialsForm'
import SyncButton from './components/SyncButton'
import ActivityLog from './components/ActivityLog'
import AssignmentCard from './components/AssignmentCard'
import './index.css'

export default function App() {
  const [credentials, setCredentials] = useState({
    canvas_url: '',
    username: '',
    password: '',
  })
  const [syncing, setSyncing] = useState(false)
  const [logs, setLogs] = useState([])
  const [assignments, setAssignments] = useState([])
  const [hasSynced, setHasSynced] = useState(false)
  const abortRef = useRef(null)

  const addLog = useCallback((msg) => {
    setLogs((prev) => [...prev, msg])
  }, [])

  const loadAssignments = useCallback(async () => {
    try {
      const res = await fetch('/api/assignments')
      const data = await res.json()
      setAssignments(data)
    } catch (e) {
      console.error('Failed to load assignments', e)
    }
  }, [])

  const handleSync = useCallback(async () => {
    const { canvas_url, username, password } = credentials
    if (!canvas_url || !username || !password) {
      alert('Please fill in all three fields before syncing.')
      return
    }

    setSyncing(true)
    setLogs([])
    setHasSynced(false)

    try {
      const controller = new AbortController()
      abortRef.current = controller

      const res = await fetch('/api/sync', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ canvas_url, username, password }),
        signal: controller.signal,
      })

      if (!res.ok) {
        addLog(`❌ Server error: ${res.status} ${res.statusText}`)
        setSyncing(false)
        return
      }

      // Read the SSE stream from a POST response via ReadableStream
      const reader = res.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const parts = buffer.split('\n\n')
        buffer = parts.pop() // keep incomplete chunk

        for (const part of parts) {
          const line = part.trim()
          if (!line.startsWith('data:')) continue
          const msg = line.slice(5).trim()

          if (msg === '__DONE__') {
            await loadAssignments()
            setHasSynced(true)
            setSyncing(false)
            return
          }

          addLog(msg)
        }
      }
    } catch (err) {
      if (err.name !== 'AbortError') {
        addLog(`❌ Connection error: ${err.message}`)
      }
    } finally {
      setSyncing(false)
    }
  }, [credentials, addLog, loadAssignments])

  return (
    <div className="app">
      {/* ── Header ── */}
      <header className="header">
        <span className="header-logo">🎓</span>
        <h1>Student Life Autopilot</h1>
        <span className="header-sub">Powered by Browser Use · Gemini Flash · Notion</span>
      </header>

      <main className="main">
        {/* ── Hero ── */}
        <section className="hero">
          <h2>
            Sync Canvas into<br />
            <span>Notion Calendar</span>
          </h2>
          <p>
            Enter your Canvas credentials, click Sync, and the AI agent will
            scrape all your assignments, exams, and deadlines — then push them
            into your Notion database, ready for calendar view.
          </p>
        </section>

        {/* ── Credentials + Sync ── */}
        <CredentialsForm
          values={credentials}
          onChange={(field, val) =>
            setCredentials((prev) => ({ ...prev, [field]: val }))
          }
          disabled={syncing}
        />

        <div className="sync-wrap">
          <SyncButton onClick={handleSync} syncing={syncing} />
        </div>

        {/* ── Activity log ── */}
        {(syncing || logs.length > 0) && <ActivityLog logs={logs} />}

        {/* ── Assignments grid ── */}
        {hasSynced && (
          <>
            <div className="section-title">
              ✨ Assignments
              <span className="count">{assignments.length}</span>
            </div>

            {assignments.length === 0 ? (
              <div className="empty-state">
                <span className="empty-icon">🗂️</span>
                <p>
                  No assignments found.
                  <small>
                    The agent may have encountered MFA — try syncing again after
                    completing it.
                  </small>
                </p>
              </div>
            ) : (
              <div className="assignments-grid">
                {assignments.map((a) => (
                  <AssignmentCard key={a.id} assignment={a} />
                ))}
              </div>
            )}
          </>
        )}
      </main>
    </div>
  )
}
