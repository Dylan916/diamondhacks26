export default function SyncButton({ onClick, syncing }) {
  return (
    <button
      id="sync-button"
      className="btn-sync"
      onClick={onClick}
      disabled={syncing}
      aria-busy={syncing}
    >
      {syncing ? (
        <>
          <span className="spinner" aria-hidden="true" />
          Syncing…
        </>
      ) : (
        <>
          <span aria-hidden="true">⚡</span>
          Sync Canvas
        </>
      )}
    </button>
  )
}
