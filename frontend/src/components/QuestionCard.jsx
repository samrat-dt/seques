import { useState } from 'react'

const COVERAGE = {
  covered: {
    emoji: '🟢',
    label: 'Covered',
    pill: 'bg-green-50 text-green-700 border-green-200',
  },
  partial: {
    emoji: '🟡',
    label: 'Partial',
    pill: 'bg-amber-50 text-amber-700 border-amber-200',
  },
  none: {
    emoji: '🔴',
    label: 'No Evidence',
    pill: 'bg-red-50 text-red-700 border-red-200',
  },
}

export default function QuestionCard({ question, answer, onUpdate }) {
  const [editing, setEditing] = useState(false)
  const [draftText, setDraftText] = useState(answer?.draft_answer || '')
  const [saving, setSaving] = useState(false)

  if (!answer) return null

  const coverage = COVERAGE[answer.evidence_coverage] || COVERAGE.none

  const certaintyColor =
    answer.ai_certainty > 80
      ? 'text-green-600'
      : answer.ai_certainty > 50
      ? 'text-amber-600'
      : 'text-red-600'

  const borderColor =
    answer.status === 'approved'
      ? 'border-l-green-500'
      : answer.status === 'edited'
      ? 'border-l-blue-500'
      : answer.needs_review
      ? 'border-l-amber-400'
      : 'border-l-slate-200'

  async function handleSave() {
    setSaving(true)
    await onUpdate({ draft_answer: draftText, status: 'edited' })
    setEditing(false)
    setSaving(false)
  }

  async function handleApprove() {
    await onUpdate({ status: 'approved' })
  }

  return (
    <div className={`bg-white rounded-xl shadow-sm border border-slate-100 border-l-4 ${borderColor} p-6`}>
      {/* Header row */}
      <div className="flex items-start justify-between mb-3 gap-3">
        <div className="flex items-center gap-2 flex-wrap">
          <span className="font-mono text-xs bg-slate-100 text-slate-500 px-2 py-0.5 rounded">
            {question.id.toUpperCase()}
          </span>
          {answer.needs_review && answer.status !== 'approved' && (
            <span className="text-xs bg-amber-100 text-amber-700 px-2 py-0.5 rounded font-medium">
              ⚠ REVIEW
            </span>
          )}
          {answer.status === 'approved' && (
            <span className="text-xs bg-green-100 text-green-700 px-2 py-0.5 rounded font-medium">
              ✅ APPROVED
            </span>
          )}
          {answer.status === 'edited' && (
            <span className="text-xs bg-blue-100 text-blue-700 px-2 py-0.5 rounded font-medium">
              EDITED
            </span>
          )}
        </div>

        <div className="flex items-center gap-2 flex-shrink-0">
          {!editing && (
            <button
              onClick={() => {
                setDraftText(answer.draft_answer)
                setEditing(true)
              }}
              className="text-xs text-slate-500 hover:text-blue-600 border border-slate-200 hover:border-blue-300 px-3 py-1 rounded-lg transition"
            >
              Edit
            </button>
          )}
          {answer.status !== 'approved' && !editing && (
            <button
              onClick={handleApprove}
              className="text-xs text-white bg-green-600 hover:bg-green-700 px-3 py-1 rounded-lg transition"
            >
              ✅ Approve
            </button>
          )}
        </div>
      </div>

      {/* Question text */}
      <p className="text-slate-900 font-medium mb-3 leading-relaxed">{question.text}</p>

      {/* Answer */}
      {editing ? (
        <div className="mb-3">
          <textarea
            className="w-full border border-blue-300 rounded-lg p-3 text-sm text-slate-700 resize-none focus:outline-none focus:ring-2 focus:ring-blue-200 focus:border-blue-400"
            rows={5}
            value={draftText}
            onChange={(e) => setDraftText(e.target.value)}
            autoFocus
          />
          <div className="flex gap-2 mt-2">
            <button
              onClick={handleSave}
              disabled={saving}
              className="text-xs bg-blue-600 text-white px-4 py-1.5 rounded-lg hover:bg-blue-700 disabled:opacity-60 transition"
            >
              {saving ? 'Saving...' : 'Save'}
            </button>
            <button
              onClick={() => setEditing(false)}
              className="text-xs text-slate-500 px-4 py-1.5 rounded-lg border border-slate-200 hover:bg-slate-50 transition"
            >
              Cancel
            </button>
          </div>
        </div>
      ) : (
        <div className="bg-slate-50 rounded-lg p-4 mb-3 text-sm text-slate-700 leading-relaxed whitespace-pre-wrap">
          {answer.draft_answer}
        </div>
      )}

      {/* Evidence sources */}
      {answer.evidence_sources?.length > 0 && (
        <div className="flex items-center gap-1.5 flex-wrap text-xs text-slate-500 mb-3">
          <span>📄</span>
          {answer.evidence_sources.map((s, i) => (
            <span key={i} className="bg-slate-100 px-2 py-0.5 rounded">
              {s}
            </span>
          ))}
        </div>
      )}

      {/* Scores */}
      <div className="flex items-center gap-3 flex-wrap">
        <span
          className={`text-xs px-2.5 py-1 rounded-full border font-medium ${coverage.pill}`}
        >
          {coverage.emoji} {coverage.label}
        </span>
        <span className={`text-xs font-medium ${certaintyColor}`}>
          Certainty {answer.ai_certainty}%
        </span>
        {answer.coverage_reason && (
          <span className="text-xs text-slate-400 italic">{answer.coverage_reason}</span>
        )}
      </div>

      {/* Suggested addition */}
      {answer.suggested_addition && (
        <div className="mt-3 bg-blue-50 border border-blue-100 rounded-lg px-3 py-2 text-xs text-blue-700">
          💡 {answer.suggested_addition}
        </div>
      )}

      {/* Certainty reason (when low) */}
      {answer.certainty_reason && (
        <div className="mt-2 text-xs text-slate-400 italic">{answer.certainty_reason}</div>
      )}
    </div>
  )
}
