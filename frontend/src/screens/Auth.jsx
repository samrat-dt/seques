import { useState } from 'react'

const ACCESS_CODE = import.meta.env.VITE_ACCESS_CODE || 'seques2026'

export default function Auth({ onUnlock }) {
  const [code, setCode] = useState('')
  const [error, setError] = useState(false)

  function handleSubmit(e) {
    e.preventDefault()
    if (code.trim() === ACCESS_CODE) {
      localStorage.setItem('seques_auth', '1')
      onUnlock()
    } else {
      setError(true)
      setCode('')
    }
  }

  return (
    <div className="min-h-screen bg-base flex flex-col items-center justify-center px-6">
      <div className="w-full max-w-sm">
        <div className="text-center mb-10">
          <span className="text-2xl font-semibold text-primary tracking-tight">seques</span>
          <div className="h-0.5 w-6 bg-amber-400 mx-auto mt-1 rounded-full" />
        </div>
        <div className="bg-surface border border-subtle rounded-xl p-8">
          <h2 className="text-lg font-semibold text-primary mb-1">Enter access code</h2>
          <p className="text-sm text-secondary mb-6">Beta access only.</p>
          <form onSubmit={handleSubmit} className="space-y-4">
            <input
              type="password"
              placeholder="Access code"
              value={code}
              onChange={(e) => { setCode(e.target.value); setError(false) }}
              required
              autoFocus
              className="w-full bg-raised border border-mid rounded-lg px-4 py-2.5 text-sm text-primary placeholder:text-muted focus:outline-none focus:ring-2 focus:ring-amber-400/25 focus:border-amber-400/60 transition-all"
            />
            {error && <p className="text-xs text-danger-text">Incorrect code.</p>}
            <button
              type="submit"
              disabled={!code.trim()}
              className="w-full bg-accent text-base font-semibold text-sm py-2.5 rounded-lg hover:bg-amber-300 disabled:opacity-50 transition-all shadow-btn-primary"
            >
              Continue →
            </button>
          </form>
        </div>
      </div>
    </div>
  )
}
