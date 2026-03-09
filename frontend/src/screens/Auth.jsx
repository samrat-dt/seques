import { useState } from 'react'
import { supabase } from '../supabase'

export default function Auth() {
  const [email, setEmail] = useState('')
  const [sent, setSent] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  async function handleSubmit(e) {
    e.preventDefault()
    if (!email.trim()) return
    setLoading(true)
    setError(null)
    const { error: err } = await supabase.auth.signInWithOtp({
      email: email.trim(),
      options: { emailRedirectTo: window.location.origin },
    })
    setLoading(false)
    if (err) {
      setError(err.message)
    } else {
      setSent(true)
    }
  }

  return (
    <div className="min-h-screen bg-base flex flex-col items-center justify-center px-6">
      <div className="w-full max-w-sm">
        {/* Wordmark */}
        <div className="text-center mb-10">
          <span className="text-2xl font-semibold text-primary tracking-tight">seques</span>
          <div className="h-0.5 w-6 bg-amber-400 mx-auto mt-1 rounded-full" />
        </div>

        {sent ? (
          <div className="bg-surface border border-subtle rounded-xl p-8 text-center">
            <div className="text-3xl mb-4">✉️</div>
            <h2 className="text-lg font-semibold text-primary mb-2">Check your email</h2>
            <p className="text-sm text-secondary leading-relaxed">
              We sent a magic link to <strong className="text-primary">{email}</strong>.
              Click it to sign in — no password needed.
            </p>
            <button
              onClick={() => { setSent(false); setEmail('') }}
              className="mt-6 text-xs text-muted hover:text-secondary transition-colors"
            >
              Use a different email
            </button>
          </div>
        ) : (
          <div className="bg-surface border border-subtle rounded-xl p-8">
            <h2 className="text-lg font-semibold text-primary mb-1">Sign in to Seques</h2>
            <p className="text-sm text-secondary mb-6">
              Enter your email and we'll send you a magic link.
            </p>
            <form onSubmit={handleSubmit} className="space-y-4">
              <input
                type="email"
                placeholder="you@company.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                autoFocus
                className="w-full bg-raised border border-mid rounded-lg px-4 py-2.5 text-sm text-primary placeholder:text-muted focus:outline-none focus:ring-2 focus:ring-amber-400/25 focus:border-amber-400/60 transition-all"
              />
              {error && (
                <p className="text-xs text-danger-text">{error}</p>
              )}
              <button
                type="submit"
                disabled={loading || !email.trim()}
                className="w-full bg-accent text-base font-semibold text-sm py-2.5 rounded-lg hover:bg-amber-300 disabled:opacity-50 transition-all shadow-btn-primary"
              >
                {loading ? 'Sending...' : 'Send magic link →'}
              </button>
            </form>
            <p className="text-xs text-muted text-center mt-5 leading-relaxed">
              Access is by invitation only during beta.
            </p>
          </div>
        )}
      </div>
    </div>
  )
}
