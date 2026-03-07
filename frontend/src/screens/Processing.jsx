import { useState, useEffect } from 'react'
import { getStatus, getAnswers } from '../api'

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
  const [status, setStatus] = useState({ processing: true, processed: 0, total: 0 })
  const [error, setError] = useState(null)

  useEffect(() => {
    const poll = setInterval(async () => {
      try {
        const s = await getStatus(sessionId)
        setStatus(s)

        const isDone = !s.processing && s.total > 0 && s.processed >= s.total
        if (isDone) {
          clearInterval(poll)
          const data = await getAnswers(sessionId)
          onDone(data)
        }
      } catch (err) {
        setError(err.message)
        clearInterval(poll)
      }
    }, 1500)

    return () => clearInterval(poll)
  }, [sessionId, onDone])

  const answerPct = status.total > 0 ? (status.processed / status.total) * 100 : 0
  const docsReady = status.total > 0 || status.processed > 0
  const parsingDone = docsReady

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
            <ProgressBar label="Parsed compliance documents" done={parsingDone} active={true} pct={100} />
            <ProgressBar
              label={`Extracted ${status.total} questions`}
              done={status.total > 0}
              active={status.total > 0}
              pct={100}
            />
            <ProgressBar
              label={
                status.total > 0
                  ? `Answering question ${status.processed} of ${status.total}`
                  : 'Generating answers...'
              }
              done={status.processed > 0 && status.processed >= status.total}
              active={status.total > 0}
              pct={answerPct}
            />
          </div>
        )}

        <p className="text-slate-400 text-xs text-center mt-8">
          Typically 1–3 minutes depending on questionnaire size
        </p>
      </div>
    </div>
  )
}
