export default function CredentialsForm({ values, onChange, disabled }) {
  return (
    <div className="credentials-card">
      <h3>Canvas Credentials</h3>

      <div className="field">
        <label htmlFor="canvas-url">Canvas URL</label>
        <input
          id="canvas-url"
          type="url"
          placeholder="https://canvas.youruniversity.edu"
          value={values.canvas_url}
          onChange={(e) => onChange('canvas_url', e.target.value)}
          disabled={disabled}
          autoComplete="url"
        />
      </div>

      <div className="field">
        <label htmlFor="canvas-username">Username</label>
        <input
          id="canvas-username"
          type="text"
          placeholder="student@university.edu"
          value={values.username}
          onChange={(e) => onChange('username', e.target.value)}
          disabled={disabled}
          autoComplete="username"
        />
      </div>

      <div className="field">
        <label htmlFor="canvas-password">Password</label>
        <input
          id="canvas-password"
          type="password"
          placeholder="••••••••"
          value={values.password}
          onChange={(e) => onChange('password', e.target.value)}
          disabled={disabled}
          autoComplete="current-password"
        />
      </div>
    </div>
  )
}
