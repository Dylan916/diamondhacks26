// Type badge CSS class mapping
const TYPE_CLASS = {
  exam:       'badge-type-exam',
  midterm:    'badge-type-midterm',
  final:      'badge-type-final',
  project:    'badge-type-project',
  assignment: 'badge-type-assignment',
  reading:    'badge-type-reading',
  other:      'badge-type-other',
}

// Source badge CSS class mapping
const SOURCE_CLASS = {
  'Assignments':   'badge-src-assignments',
  'Syllabus':      'badge-src-syllabus',
  'Announcement':  'badge-src-announcement',
  'External Site': 'badge-src-external',
}

function formatDate(iso) {
  if (!iso) return 'No due date'
  try {
    return new Date(iso).toLocaleString('en-US', {
      month:  'short',
      day:    'numeric',
      year:   'numeric',
      hour:   'numeric',
      minute: '2-digit',
      hour12: true,
    })
  } catch {
    return iso
  }
}

export default function AssignmentCard({ assignment }) {
  const {
    title,
    course,
    due_date,
    type,
    source,
    needs_review,
  } = assignment

  const typeClass  = TYPE_CLASS[type?.toLowerCase()]  || TYPE_CLASS.other
  const srcClass   = SOURCE_CLASS[source] || SOURCE_CLASS['Assignments']

  return (
    <article className="card">
      <div className="card-title">{title}</div>
      <div className="card-course">{course}</div>

      <div className="card-due">
        <span className="due-icon">📅</span>
        {formatDate(due_date)}
      </div>

      <div className="card-badges">
        <span className={`badge ${typeClass}`}>
          {type || 'other'}
        </span>
        <span className={`badge ${srcClass}`}>
          {source || 'Assignments'}
        </span>
        {needs_review && (
          <span className="badge badge-review">⚠ Check source</span>
        )}
      </div>
    </article>
  )
}
