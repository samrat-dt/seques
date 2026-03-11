export default function Landing({ onStart }) {
  return (
    <div className="min-h-screen bg-base">
      {/* Nav */}
      <nav className="sticky top-0 z-50 h-[52px] bg-base/95 backdrop-blur-sm border-b border-subtle flex items-center px-6">
        <div className="max-w-3xl mx-auto w-full flex items-center justify-between">
          <div className="flex items-center">
            <span className="text-base font-semibold text-primary tracking-tight">seques</span>
            <span className="inline-block w-1 h-1 rounded-full bg-amber-400 ml-0.5 mb-px" />
          </div>
          <button
            onClick={onStart}
            className="text-xs font-semibold text-base bg-accent px-4 py-1.5 rounded-lg hover:bg-amber-300 transition-all"
          >
            Get started
          </button>
        </div>
      </nav>

      <div className="max-w-3xl mx-auto px-6">
        {/* Hero */}
        <div className="pt-20 pb-14 border-b border-subtle">
          <div className="inline-flex items-center gap-2 text-[11px] font-mono text-amber-400 bg-amber-400/10 border border-amber-400/25 px-3 py-1 rounded-full mb-8 tracking-wide">
            v1.0.0 — Live · Simple auth · Groq + Anthropic
          </div>
          <h1 className="text-5xl font-bold tracking-tight leading-[1.12] text-primary mb-5">
            AI drafts every answer<br />to security questionnaires.<br />
            <span className="text-amber-400">You review and ship.</span>
          </h1>
          <p className="text-lg text-secondary leading-relaxed max-w-xl mb-8">
            Upload your SOC 2 report, ISO 27001 cert, or policy docs. Add the prospect's
            questionnaire. The AI reads the evidence and drafts every answer.
            You edit, approve, and export. No blank fields, no starting from scratch.
          </p>
          <button
            onClick={onStart}
            className="inline-flex items-center gap-2 bg-accent text-base font-semibold px-6 py-3 rounded-xl hover:bg-amber-300 transition-all shadow-btn-primary text-sm"
          >
            Get started →
          </button>

          {/* v1.0.0 highlights */}
          <div className="mt-12 pt-8 border-t border-subtle">
            <p className="text-[11px] font-mono text-muted uppercase tracking-widest mb-4">What shipped in v1.0.0</p>
            <div className="grid gap-2.5">
              {[
                ['Access-code protected', 'Simple access-code gate — no account required. Enter the code, get straight to work. Overridable per deployment.'],
                ['Supabase persistence', 'Sessions, questions, answers, and audit events are written to Supabase. Your work survives server restarts.'],
                ['Security middleware active', 'SecurityHeadersMiddleware and RateLimitMiddleware running on every request — CSP, HSTS, X-Frame-Options, 30 req/min per IP.'],
                ['Two LLM providers configured', 'Groq (llama-3.3-70b-versatile, default) and Anthropic (claude-haiku-4-5) both configured and working in production.'],
                ['Authenticated exports', 'Excel and PDF downloads use fetch+blob with auth headers — no broken download links.'],
              ].map(([title, detail]) => (
                <div key={title} className="flex items-baseline gap-3 text-sm text-secondary">
                  <span className="text-success-text text-xs flex-shrink-0 mt-px">✓</span>
                  <span><strong className="text-primary font-medium">{title}</strong> — {detail}</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Where we stand */}
        <div className="py-14 border-b border-subtle">
          <p className="text-[11px] font-mono text-muted uppercase tracking-widest mb-2">Honest state of things</p>
          <h2 className="text-2xl font-bold tracking-tight text-primary mb-2">Where we are today</h2>
          <p className="text-sm text-muted mb-8">
            These are the decisions we made and the trade-offs we accepted. No hiding the rough edges.
          </p>
          <div className="grid gap-6">
            {[
              {
                title: 'Sequential processing by default — reliable, not fast',
                body: 'Each question is answered one at a time with a 1.5s pause between LLM calls. A 30-question session takes around 60-90 seconds. Parallel mode (6-8× faster) exists in the codebase and activates via ANSWER_CONCURRENCY env var — but it hit ordering anomalies under Groq rate limits, so sequential is the reliability default.',
              },
              {
                title: 'Draft-first answers — you always get something',
                body: 'The engine never says "I can\'t answer this." Every question gets a professional draft — assertive when your docs support it, hedged when they don\'t. Hedged answers include a note on exactly what to verify before sending.',
              },
              {
                title: '32KB of compliance docs per session',
                body: 'Up to 32KB of text across all uploaded docs (16KB per doc). Covers most policy documents and shorter SOC 2 summaries well. Large SOC 2 reports (50-120KB) get truncated. Phase 2 adds RAG — the engine will retrieve only the sections relevant to each question.',
              },
              {
                title: 'Sessions persist to Supabase',
                body: 'Sessions are written to Supabase on creation and restored automatically on server restart. Your work survives beyond the current server process.',
              },
              {
                title: 'Two LLM providers — Groq is default',
                body: 'Groq (llama-3.3-70b-versatile, free tier) and Anthropic (claude-haiku-4-5) are both configured in production. Switch with one LLM_PROVIDER env var. Anthropic produces the best structured JSON quality. Groq is fastest and free.',
              },
            ].map(({ title, body }) => (
              <div key={title} className="flex gap-4">
                <div className="flex-shrink-0 w-7 h-7 rounded-lg bg-success-bg border border-success-border flex items-center justify-center text-success-text text-xs mt-0.5">
                  →
                </div>
                <div>
                  <h3 className="text-sm font-semibold text-primary mb-1">{title}</h3>
                  <p className="text-sm text-secondary leading-relaxed">{body}</p>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* What's next */}
        <div className="py-14 border-b border-subtle">
          <p className="text-[11px] font-mono text-muted uppercase tracking-widest mb-2">What's next</p>
          <h2 className="text-2xl font-bold tracking-tight text-primary mb-2">Coming up</h2>
          <p className="text-sm text-muted mb-8">
            Foundation is solid. Now making answers smarter and the system faster.
          </p>
          <div className="grid gap-6">
            {[
              {
                title: 'RAG for large compliance docs',
                body: 'Chunk your compliance documents, embed them with a small model, store vectors in Supabase pgvector. At query time, retrieve only the sections relevant to each question. Removes the 32KB ceiling — full SOC 2 reports, no truncation.',
              },
              {
                title: 'True parallel processing with safety guarantees',
                body: 'Revisiting concurrency with async LLM clients and a Redis-backed rate-limit budget tracker. The goal is ANSWER_CONCURRENCY=10 as the reliable default — 6-8× faster than today without the ordering anomalies that pushed us to sequential.',
              },
              {
                title: 'Redis rate limiter',
                body: 'Replace the in-memory rate limiter with Redis. Required before horizontal scaling — the current limiter resets on each process restart and doesn\'t share state across workers.',
              },
              {
                title: 'Session history',
                body: 'List past sessions and re-open them from a dashboard. Right now every session starts fresh. Phase 3 adds a history view so you can pick up where you left off.',
              },
              {
                title: 'Answer templates',
                body: 'Pre-load standard approved language per control domain. Stop rewriting the same MFA policy answer every quarter — approve it once, pull it in on demand.',
              },
            ].map(({ title, body }) => (
              <div key={title} className="flex gap-4">
                <div className="flex-shrink-0 w-7 h-7 rounded-lg bg-info-bg border border-info-border flex items-center justify-center text-info-text text-xs mt-0.5">
                  ⚡
                </div>
                <div>
                  <h3 className="text-sm font-semibold text-primary mb-1">{title}</h3>
                  <p className="text-sm text-secondary leading-relaxed">{body}</p>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* CTA */}
        <div className="py-20 text-center">
          <h2 className="text-3xl font-bold tracking-tight text-primary mb-3">
            Stop filling out questionnaires by hand.
          </h2>
          <p className="text-secondary text-base mb-8 max-w-md mx-auto leading-relaxed">
            Upload your docs and a questionnaire. See draft answers in under 90 seconds.
          </p>
          <button
            onClick={onStart}
            className="inline-flex items-center gap-2 bg-accent text-base font-semibold px-8 py-3.5 rounded-xl hover:bg-amber-300 transition-all shadow-btn-primary text-sm"
          >
            Get started
          </button>
        </div>
      </div>

      {/* Footer */}
      <div className="border-t border-subtle px-6 py-6">
        <div className="max-w-3xl mx-auto flex items-center justify-between">
          <p className="text-xs text-muted">© 2026 Seques. Built for security teams who have better things to do.</p>
          <a href="mailto:access@seques.ai" className="text-xs text-muted hover:text-secondary transition-colors">
            access@seques.ai
          </a>
        </div>
      </div>
    </div>
  )
}
