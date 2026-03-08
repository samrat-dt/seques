import { useState, useEffect, useRef } from 'react'
import { getStatus, getAnswers } from '../api'

function now() {
  return new Date().toLocaleTimeString('en-US', { hour12: false })
}

export default function Processing({ sessionId, onDone }) {
  const [logLines, setLogLines] = useState([
    { time: now(), glyph: '▶', glyphColor: 'text-amber-400', text: 'Connecting to backend...' },
  ])
  const [error, setError] = useState(null)
  const bottomRef = useRef(null)
  const esRef = useRef(null)

  function appendLine(glyph, glyphColor, text) {
    setLogLines((prev) => [...prev, { time: now(), glyph, glyphColor, text }])
  }

  function updateLastLine(glyph, glyphColor, text) {
    setLogLines((prev) => {
      const next = [...prev]
      next[next.length - 1] = { ...next[next.length - 1], glyph, glyphColor, text }
      return next
    })
  }

  // Fetch total upfront so we can show "X of Y" immediately
  useEffect(() => {
    getStatus(sessionId).catch(() => {})
  }, [sessionId])

  useEffect(() => {
    const apiBase = import.meta.env.VITE_API_URL || 'http://localhost:8000'
    let answeredCount = 0
    let totalCount = 0
    let questionsLogged = false

    const es = new EventSource(`${apiBase}/api/sessions/${sessionId}/stream`)
    esRef.current = es

    es.onmessage = async (event) => {
      if (event.data === '[DONE]') {
        es.close()
        updateLastLine('✓', 'text-success-text', `Done. ${answeredCount} answer${answeredCount !== 1 ? 's' : ''} drafted.`)
        try {
          const data = await getAnswers(sessionId)
          onDone(data)
        } catch (err) {
          setError(err.message)
        }
        return
      }
      try {
        JSON.parse(event.data)
        answeredCount += 1

        if (!questionsLogged) {
          // First answer arrived — docs must be parsed and questions extracted
          updateLastLine('✓', 'text-success-text', 'Docs parsed')
          appendLine('▶', 'text-amber-400', `Answering ${answeredCount}${totalCount > 0 ? ` of ${totalCount}` : ''}...`)
          questionsLogged = true
        } else {
          setLogLines((prev) => {
            const next = [...prev]
            const last = next[next.length - 1]
            next[next.length - 1] = {
              ...last,
              text: `Answering ${answeredCount}${totalCount > 0 ? ` of ${totalCount}` : ''}...`,
            }
            return next
          })
        }
      } catch {
        // malformed SSE message — ignore
      }
    }

    es.onerror = () => {
      es.close()
      appendLine('✗', 'text-danger-text', 'Connection lost. Please refresh and try again.')
      setError('Connection to server lost.')
    }

    // Poll status once to get the total question count for display
    const statusPoll = setInterval(async () => {
      try {
        const s = await getStatus(sessionId)
        if (s.total > 0) {
          totalCount = s.total
          if (!questionsLogged) {
            updateLastLine('✓', 'text-success-text', `${s.total} question${s.total !== 1 ? 's' : ''} extracted`)
            appendLine('▶', 'text-amber-400', `Answering 0 of ${s.total}...`)
            questionsLogged = true
          }
          clearInterval(statusPoll)
        }
      } catch {
        clearInterval(statusPoll)
      }
    }, 800)

    return () => {
      es.close()
      clearInterval(statusPoll)
    }
  }, [sessionId, onDone])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [logLines])

  const lastLine = logLines[logLines.length - 1]
  const isActiveGlyph = lastLine?.glyph === '▶' && !error

  return (
    <div className="max-w-2xl mx-auto px-6 py-12">
      <div className="bg-surface rounded-xl border border-subtle overflow-hidden shadow-card">
        {/* Terminal chrome */}
        <div className="h-8 bg-raised border-b border-subtle flex items-center px-4 justify-between">
          <div className="flex items-center gap-1.5">
            <div className="w-2.5 h-2.5 rounded-full bg-[#ff5f57]" />
            <div className="w-2.5 h-2.5 rounded-full bg-[#ffbd2e]" />
            <div className="w-2.5 h-2.5 rounded-full bg-[#27c93f]" />
          </div>
          <span className="text-xs text-muted font-mono">seques — processing</span>
          <div className="w-12" />
        </div>

        {/* Log content */}
        <div className="p-5 font-mono text-xs space-y-1.5 min-h-[200px] max-h-[360px] overflow-y-auto">
          {logLines.map((line, i) => {
            const isLast = i === logLines.length - 1
            const isActive = isLast && isActiveGlyph
            return (
              <div key={i} className="flex items-start gap-3 animate-fade-in">
                <span className="text-muted flex-shrink-0 w-16">{line.time}</span>
                <span className={`flex-shrink-0 ${isActive ? 'animate-pulse' : ''} ${line.glyphColor}`}>
                  {line.glyph}
                </span>
                <span className={isLast && !error ? 'text-primary' : 'text-secondary'}>
                  {line.text}
                  {isLast && !error && (
                    <span className="ml-1 text-amber-400 animate-cursor-blink">▋</span>
                  )}
                </span>
              </div>
            )
          })}
          <div ref={bottomRef} />
        </div>
      </div>

      {error ? (
        <div className="mt-4 bg-danger-bg border border-danger-border rounded-lg px-4 py-3 text-xs text-danger-text">
          Something broke.{' '}
          <button
            onClick={() => window.location.reload()}
            className="underline underline-offset-2 hover:text-primary transition-colors"
          >
            Try again →
          </button>
        </div>
      ) : (
        <p className="text-xs text-muted text-center mt-5">
          Usually under 30 seconds with parallel processing.
        </p>
      )}
    </div>
  )
}
