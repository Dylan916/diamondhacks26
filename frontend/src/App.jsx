import { useState, useRef, useCallback } from 'react'
import SyncButton from './components/SyncButton'
import ActivityLog from './components/ActivityLog'
import Dashboard from './components/Dashboard'
import UrlInputList from './components/UrlInputList'
import './index.css'

export default function App() {
  const [syncing, setSyncing] = useState(false)
  const [logs, setLogs] = useState([])
  const [assignments, setAssignments] = useState([])
  const [hasSynced, setHasSynced] = useState(false)
  const [externalUrls, setExternalUrls] = useState([''])
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
    setSyncing(true)
    setLogs([])
    setHasSynced(false)

    try {
      const controller = new AbortController()
      abortRef.current = controller

      const res = await fetch('/api/sync', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ external_urls: externalUrls.filter(u => u.trim() !== '') }),
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
  }, [addLog, loadAssignments])

  return (
    <div className="app">
      {/* ── Header ── */}
      <header className="header">
        <span className="header-logo">🎓</span>
        <h1>Student Life Autopilot</h1>
        <span className="header-sub">Powered by Browser Use · Gemini Flash</span>
      </header>

      <main className="main">
        {/* ── Hero ── */}
        <section className="hero">
          <h2>
            Sync Canvas into<br />
            <span>Your Calendar</span>
          </h2>
          <p>
            Paste your external course websites below. We'll automatically fetch your 
            Canvas data using your Chrome profile, scrape everything, and build your calendar.
          </p>
        </section>

        {!hasSynced && !syncing && (
          <div className="credentials-card text-left mb-8 px-6 pt-6 pb-2">
            <UrlInputList 
              externalUrls={externalUrls} 
              setExternalUrls={setExternalUrls} 
            />
          </div>
        )}

        {/* ── Sync ── */}
        <div className="sync-wrap">
          <SyncButton onClick={handleSync} syncing={syncing} />
        </div>

        {/* ── Activity log ── */}
        {(syncing || logs.length > 0) && <ActivityLog logs={logs} />}

        {/* ── Dashboard (calendar + export) ── */}
        {hasSynced && assignments.length > 0 && (
          <Dashboard assignments={assignments} />
        )}

        {hasSynced && assignments.length === 0 && (
          <div className="empty-state">
            <span className="empty-icon">🗂️</span>
            <p>
              No assignments found.
              <small>
                The agent may have encountered an issue — try syncing again.
              </small>
            </p>
          </div>
        )}
      </main>
    </div>
  )
}
