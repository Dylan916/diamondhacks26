import { useEffect, useRef } from 'react'

function timestamp() {
  const now = new Date()
  return now.toLocaleTimeString('en-US', {
    hour12: false,
    hour:   '2-digit',
    minute: '2-digit',
    second: '2-digit',
  })
}

export default function ActivityLog({ logs }) {
  const bottomRef = useRef(null)

  // Auto-scroll to bottom whenever a new log line arrives
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [logs])

  return (
    <section className="log-section">
      <h3>Activity Log</h3>
      <div className="log-box" role="log" aria-live="polite" aria-label="Sync activity log">
        {logs.map((line, i) => (
          <div key={i} className="log-line">
            <span className="log-ts">{timestamp()}</span>
            <span className="log-msg">{line}</span>
          </div>
        ))}
        <div ref={bottomRef} />
      </div>
    </section>
  )
}
