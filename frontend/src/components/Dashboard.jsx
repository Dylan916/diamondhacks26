import { useState } from 'react'
import CalendarGrid from './CalendarGrid'
import AssignmentDetailPanel from './AssignmentDetailPanel'

// ── Helpers ──────────────────────────────────────────────────────────────────

function daysUntil(isoDate) {
  if (!isoDate) return null
  const now = new Date()
  now.setHours(0, 0, 0, 0)
  const due = new Date(isoDate)
  due.setHours(0, 0, 0, 0)
  return Math.round((due - now) / (1000 * 60 * 60 * 24))
}

function isExam(type) {
  return ['exam', 'midterm', 'final'].includes(type?.toLowerCase())
}

// ── SummaryBar ────────────────────────────────────────────────────────────────

function SummaryBar({ assignments }) {
  const total = assignments.length
  const exams = assignments.filter((a) => isExam(a.type)).length
  const projects = assignments.filter(
    (a) => a.type?.toLowerCase() === 'project'
  ).length

  const upcoming = assignments
    .filter((a) => a.due_date)
    .sort((a, b) => new Date(a.due_date) - new Date(b.due_date))
    .find((a) => daysUntil(a.due_date) >= 0)

  const nextLabel = upcoming
    ? `${upcoming.title} in ${daysUntil(upcoming.due_date)} day${daysUntil(upcoming.due_date) === 1 ? '' : 's'}`
    : 'Nothing upcoming'

  const stats = [
    { label: 'Total', value: total, icon: '📚' },
    { label: 'Exams', value: exams, icon: '📝' },
    { label: 'Projects', value: projects, icon: '🛠️' },
    { label: 'Next due', value: nextLabel, icon: '⏰', wide: true },
  ]

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-6">
      {stats.map((s) => (
        <div
          key={s.label}
          className={`bg-white/5 border border-white/10 rounded-xl p-4 flex flex-col gap-1 ${s.wide ? 'col-span-2 md:col-span-1' : ''}`}
        >
          <div className="text-xs text-slate-400 uppercase tracking-wider font-semibold flex items-center gap-1">
            <span>{s.icon}</span>
            {s.label}
          </div>
          <div className="text-white font-bold text-lg leading-tight truncate">
            {s.value}
          </div>
        </div>
      ))}
    </div>
  )
}

// ── ExportButton ──────────────────────────────────────────────────────────────

function ExportButton() {
  const handleExport = () => {
    window.location.href = '/api/assignments/export/ics'
  }

  return (
    <div className="flex flex-col items-end gap-1">
      <button
        onClick={handleExport}
        className="flex items-center gap-2 bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-semibold px-4 py-2 rounded-lg transition-colors duration-150 shadow-md"
      >
        <span>📅</span>
        Export to Google Calendar
      </button>
      <p className="text-xs text-slate-500">
        Opens in Google Calendar, Apple Calendar, or Outlook
      </p>
    </div>
  )
}

// ── Dashboard ─────────────────────────────────────────────────────────────────

export default function Dashboard({ assignments }) {
  const [selected, setSelected] = useState(null)

  return (
    <section className="mt-10">
      {/* Title row */}
      <div className="flex items-start justify-between mb-6 gap-4 flex-wrap">
        <div>
          <h2 className="text-white text-2xl font-bold tracking-tight">
            ✨ Your Dashboard
          </h2>
          <p className="text-slate-400 text-sm mt-1">
            {assignments.length} assignment{assignments.length !== 1 ? 's' : ''} synced from Canvas
          </p>
        </div>
        <ExportButton />
      </div>

      {/* Summary stats */}
      <SummaryBar assignments={assignments} />

      {/* Calendar */}
      <CalendarGrid assignments={assignments} onSelect={setSelected} />

      {/* Detail panel */}
      <AssignmentDetailPanel
        assignment={selected}
        onClose={() => setSelected(null)}
      />
    </section>
  )
}
