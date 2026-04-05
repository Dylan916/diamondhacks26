import { useEffect, useRef } from 'react'

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
        {logs.map((log, i) => {
          // Detect URLs in log.text
          const urlRegex = /(https?:\/\/[^\s]+)/g;
          const parts = log.text.split(urlRegex);
          
          return (
            <div key={i} className="log-line">
              <span className="log-ts">{log.ts}</span>
              <span className="log-msg">
                {parts.map((part, index) => 
                  urlRegex.test(part) ? (
                    <a key={index} href={part} target="_blank" rel="noopener noreferrer" className="log-link">
                      {part}
                    </a>
                  ) : (
                    part
                  )
                )}
              </span>
            </div>
          );
        })}
        <div ref={bottomRef} />
      </div>
    </section>
  )
}
