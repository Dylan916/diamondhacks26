import { useState, useMemo } from 'react'

// ── Type → color chip ─────────────────────────────────────────────────────────
const TYPE_COLOR = {
  exam:       { bg: 'bg-red-500',    text: 'text-white' },
  midterm:    { bg: 'bg-red-500',    text: 'text-white' },
  final:      { bg: 'bg-red-600',    text: 'text-white' },
  project:    { bg: 'bg-purple-500', text: 'text-white' },
  assignment: { bg: 'bg-blue-500',   text: 'text-white' },
  reading:    { bg: 'bg-green-500',  text: 'text-white' },
  other:      { bg: 'bg-gray-500',   text: 'text-white' },
}

function chipColors(type) {
  return TYPE_COLOR[type?.toLowerCase()] ?? TYPE_COLOR.other
}

const DAYS = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
const MONTHS = [
  'January', 'February', 'March', 'April', 'May', 'June',
  'July', 'August', 'September', 'October', 'November', 'December',
]

// ── CalendarGrid ──────────────────────────────────────────────────────────────

export default function CalendarGrid({ assignments, onSelect }) {
  const today = new Date()
  const [year, setYear]   = useState(today.getFullYear())
  const [month, setMonth] = useState(today.getMonth())

  // Build a map: "YYYY-MM-DD" → [assignment, ...]
  const byDay = useMemo(() => {
    const map = {}
    for (const a of assignments) {
      if (!a.due_date) continue
      try {
        const d = new Date(a.due_date)
        const key = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
        if (!map[key]) map[key] = []
        map[key].push(a)
      } catch {}
    }
    return map
  }, [assignments])

  // Calendar arithmetic
  const firstDay  = new Date(year, month, 1).getDay()   // weekday of 1st
  const daysInMonth = new Date(year, month + 1, 0).getDate()

  function prevMonth() {
    if (month === 0) { setYear(y => y - 1); setMonth(11) }
    else setMonth(m => m - 1)
  }
  function nextMonth() {
    if (month === 11) { setYear(y => y + 1); setMonth(0) }
    else setMonth(m => m + 1)
  }

  const todayKey = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}-${String(today.getDate()).padStart(2, '0')}`

  // Build cells array: nulls for leading blanks, then 1..daysInMonth
  const cells = [
    ...Array(firstDay).fill(null),
    ...Array.from({ length: daysInMonth }, (_, i) => i + 1),
  ]
  // Pad to complete last row
  while (cells.length % 7 !== 0) cells.push(null)

  return (
    <div className="bg-white/5 border border-white/10 rounded-2xl overflow-hidden">
      {/* Month navigation */}
      <div className="flex items-center justify-between px-5 py-4 border-b border-white/10">
        <button
          onClick={prevMonth}
          className="text-slate-400 hover:text-white transition-colors p-1 rounded hover:bg-white/10"
          aria-label="Previous month"
        >
          ‹
        </button>
        <h3 className="text-white font-semibold text-base">
          {MONTHS[month]} {year}
        </h3>
        <button
          onClick={nextMonth}
          className="text-slate-400 hover:text-white transition-colors p-1 rounded hover:bg-white/10"
          aria-label="Next month"
        >
          ›
        </button>
      </div>

      {/* Day-of-week header */}
      <div className="grid grid-cols-7 border-b border-white/10">
        {DAYS.map((d) => (
          <div key={d} className="text-center text-xs text-slate-500 font-semibold py-2 uppercase tracking-wider">
            {d}
          </div>
        ))}
      </div>

      {/* Day cells */}
      <div className="grid grid-cols-7">
        {cells.map((day, i) => {
          if (!day) {
            return <div key={`blank-${i}`} className="min-h-[90px] border-b border-r border-white/5" />
          }

          const key = `${year}-${String(month + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`
          const dayAssignments = byDay[key] || []
          const isToday = key === todayKey
          const visible = dayAssignments.slice(0, 2)
          const overflow = dayAssignments.length - visible.length

          return (
            <div
              key={key}
              className="min-h-[90px] border-b border-r border-white/5 p-1.5 flex flex-col gap-1"
            >
              {/* Day number */}
              <span
                className={`text-xs font-semibold w-6 h-6 flex items-center justify-center rounded-full self-start
                  ${isToday
                    ? 'bg-indigo-500 text-white'
                    : 'text-slate-400'
                  }`}
              >
                {day}
              </span>

              {/* Assignment chips */}
              {visible.map((a, idx) => {
                const { bg, text } = chipColors(a.type)
                return (
                  <button
                    key={idx}
                    onClick={() => onSelect(a)}
                    className={`w-full text-left text-[10px] font-medium px-1.5 py-0.5 rounded ${bg} ${text} truncate hover:opacity-90 transition-opacity`}
                    title={a.title}
                  >
                    {a.title}
                  </button>
                )
              })}

              {/* +X more */}
              {overflow > 0 && (
                <button
                  onClick={() => onSelect(dayAssignments[2])}
                  className="text-[10px] text-slate-400 hover:text-white transition-colors text-left pl-1"
                >
                  +{overflow} more
                </button>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}
