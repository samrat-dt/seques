import { useState, useEffect, useRef } from 'react'
import { getAnswers } from '../api'

function ProgressBar({ label, pct, done, active }) {
  const width = done ? 100 : active ? pct : 0
  const barColor = done ? 'bg-green-500' : 'bg-blue-500'

  return (
    <div>
      <div className="flex justify-between text-sm mb-1.5">
        <span className={done ? 'text-green-700 font-medium' : active ? 'text-slate-700' : 'text-slate-400'}>
          {label}
        </span>
        <span className="text-slate-400 tabular-nums">{width > 0 ? `${Math.round(width)}%` : ''}</span>
      </div>
      <div className="h-2 bg-slate-100 rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full transition-all duration-700 ${barColor}`}
          style={{ width: `${width}%` }}
        />
      </div>
    </div>
  )
}

export default function Processing({ sessionId, onDone }) {
  const [answered, setAnswered] = useState(0)
  const [total, setTotal] = useState(0)
  const [error, setError] = useState(null)
  const esRef = useRef(null)

  useEffect(() => {
    const apiBase = import.meta.env.VITE_API_URL || 'http://localhost:8000'
    const es = new EventSource(`${apiBase}/api/sessions/${sessionId}/stream`)
    esRef.current = es

    es.onmessage = async (event) => {
      if (event.data === '[DONE]') {
        es.close()
        try {
          const data = await getAnswers(sessionId)
          setTotal(data.questions.length)
          onDone(data)
        } catch (err) {
          setError(err.message)
        }
        return
      }
      try {
        JSON.parse(event.data) // validate answer payload
        setAnswered((n) => {
          const next = n + 1
          return next
        })
        setTotal((t) => (t === 0 ? 1 : t)) // will be updated properly on DONE
      } catch {
        // malformed SSE message — ignore
      }
    }

    es.onerror = () => {
      es.close()
      setError('Connection to server lost. Please refresh and try again.')
    }

    return () => es.close()
  }, [sessionId, onDone])

  const answerPct = total > 0 ? (answered / total) * 100 : answered > 0 ? 50 : 0
  const docsReady = answered > 0 || total > 0

  return (
    <div className="max-w-lg mx-auto px-6 py-20">
      <div className="bg-white rounded-2xl shadow-sm border border-slate-100 p-8">
        <h2 className="text-xl font-bold text-slate-900 mb-1">Processing your questionnaire</h2>
        <p className="text-slate-500 text-sm mb-8">
          AI is reading your compliance docs and drafting answers...
        </p>

        {error ? (
          <div className="bg-red-50 border border-red-200 rounded-xl p-4 text-red-700 text-sm">
            <strong>Error:</strong> {error}
          </div>
        ) : (
          <div className="space-y-5">
            <ProgressBar label="Parsed compliance documents" done={docsReady} active={true} pct={100} />
            <ProgressBar
              label="Extracted questions"
              done={answered > 0}
              active={answered > 0}
              pct={100}
            />
            <ProgressBar
              label={
                answered > 0
                  ? `Answered ${answered}${total > 0 ? ` of ${total}` : ''} questions`
                  : 'Generating answers...'
              }
              done={total > 0 && answered >= total}
              active={answered > 0 || total > 0}
              pct={answerPct}
            />
          </div>
        )}

        <p className="text-slate-400 text-xs text-center mt-8">
          Typically under 30 seconds with parallel processing
        </p>
      </div>
    </div>
  )
}
