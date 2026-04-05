import { useEffect, useRef } from 'react'

// ── Type badge colors ─────────────────────────────────────────────────────────
const TYPE_STYLE = {
  exam:       'bg-red-500/20 text-red-400 border border-red-500/30',
  midterm:    'bg-red-500/20 text-red-400 border border-red-500/30',
  final:      'bg-red-600/20 text-red-400 border border-red-600/30',
  project:    'bg-purple-500/20 text-purple-400 border border-purple-500/30',
  assignment: 'bg-blue-500/20 text-blue-400 border border-blue-500/30',
  reading:    'bg-green-500/20 text-green-400 border border-green-500/30',
  other:      'bg-gray-500/20 text-gray-400 border border-gray-500/30',
}

// ── Source badge colors ───────────────────────────────────────────────────────
const SOURCE_STYLE = {
  'Canvas Assignments':  'bg-blue-500/20 text-blue-400 border border-blue-500/30',
  'Canvas Syllabus':     'bg-yellow-500/20 text-yellow-400 border border-yellow-500/30',
  'Canvas Announcement': 'bg-orange-500/20 text-orange-400 border border-orange-500/30',
  'External Site':       'bg-pink-500/20 text-pink-400 border border-pink-500/30',
}

function formatDue(iso) {
  if (!iso) return 'No due date'
  try {
    return new Date(iso).toLocaleString('en-US', {
      weekday: 'long',
      month:   'long',
      day:     'numeric',
      year:    'numeric',
      hour:    'numeric',
      minute:  '2-digit',
      hour12:  true,
    })
  } catch {
    return iso
  }
}

// ── AssignmentDetailPanel ─────────────────────────────────────────────────────

export default function AssignmentDetailPanel({ assignment, onClose }) {
  const panelRef = useRef(null)

  // Close on Escape
  useEffect(() => {
    function onKey(e) {
      if (e.key === 'Escape') onClose()
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [onClose])

  const isOpen = !!assignment
  const typeStyle   = TYPE_STYLE[assignment?.type?.toLowerCase()]   ?? TYPE_STYLE.other
  const sourceStyle = SOURCE_STYLE[assignment?.source] ?? SOURCE_STYLE['Canvas Assignments']

  return (
    <>
      {/* Backdrop */}
      <div
        onClick={onClose}
        className={`fixed inset-0 bg-black/50 z-40 transition-opacity duration-300 ${isOpen ? 'opacity-100 pointer-events-auto' : 'opacity-0 pointer-events-none'}`}
        aria-hidden="true"
      />

      {/* Panel */}
      <div
        ref={panelRef}
        className={`fixed top-0 right-0 h-full w-full max-w-md bg-[#13162b] border-l border-white/10 shadow-2xl z-50
          flex flex-col transition-transform duration-300 ease-in-out
          ${isOpen ? 'translate-x-0' : 'translate-x-full'}`}
        role="dialog"
        aria-modal="true"
        aria-label="Assignment details"
      >
        {assignment && (
          <>
            {/* Header */}
            <div className="flex items-start justify-between gap-4 p-6 border-b border-white/10">
              <h2 className="text-white text-xl font-bold leading-tight flex-1">
                {assignment.title}
              </h2>
              <button
                onClick={onClose}
                className="text-slate-400 hover:text-white transition-colors mt-0.5 flex-shrink-0 text-2xl leading-none"
                aria-label="Close panel"
              >
                ×
              </button>
            </div>

            {/* Body */}
            <div className="flex-1 overflow-y-auto p-6 flex flex-col gap-5">
              {/* Course */}
              <div>
                <p className="text-xs text-slate-500 uppercase tracking-wider font-semibold mb-1">Course</p>
                <p className="text-white font-medium">{assignment.course || '—'}</p>
              </div>

              {/* Due date */}
              <div>
                <p className="text-xs text-slate-500 uppercase tracking-wider font-semibold mb-1">Due Date</p>
                <p className="text-white font-medium">{formatDue(assignment.due_date)}</p>
              </div>

              {/* Badges */}
              <div className="flex flex-wrap gap-2">
                <span className={`text-xs font-semibold px-2.5 py-1 rounded-full capitalize ${typeStyle}`}>
                  {assignment.type || 'other'}
                </span>
                <span className={`text-xs font-semibold px-2.5 py-1 rounded-full ${sourceStyle}`}>
                  {assignment.source || 'Canvas Assignments'}
                </span>
              </div>

              {/* Needs review warning */}
              {assignment.needs_review && (
                <div className="bg-yellow-500/15 border border-yellow-500/30 text-yellow-400 rounded-lg p-3 text-sm flex gap-2 items-start">
                  <span className="text-lg leading-none mt-0.5">⚠️</span>
                  <span>Date may need verification — check the original source</span>
                </div>
              )}

              {/* External URL */}
              {assignment.source_url && (
                <div>
                  <p className="text-xs text-slate-500 uppercase tracking-wider font-semibold mb-1">Source Link</p>
                  <a
                    href={assignment.source_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-indigo-400 hover:text-indigo-300 text-sm underline underline-offset-2 transition-colors break-all"
                  >
                    View original source ↗
                  </a>
                </div>
              )}
            </div>
          </>
        )}
      </div>
    </>
  )
}
