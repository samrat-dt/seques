import { useState } from 'react'

const COVERAGE = {
  covered: { dot: 'bg-success-text', text: 'text-success-text', bg: 'bg-success-bg', border: 'border-success-border', label: 'Covered' },
  partial:  { dot: 'bg-warning-text', text: 'text-warning-text', bg: 'bg-warning-bg', border: 'border-warning-border', label: 'Partial' },
  none:     { dot: 'bg-danger-text',  text: 'text-danger-text',  bg: 'bg-danger-bg',  border: 'border-danger-border',  label: 'No evidence' },
}

const FileSmIcon = () => (
  <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
    <polyline points="14 2 14 8 20 8" />
  </svg>
)

const BulbIcon = () => (
  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <line x1="9" y1="18" x2="15" y2="18" />
    <line x1="10" y1="22" x2="14" y2="22" />
    <path d="M12 2a7 7 0 0 1 7 7c0 2.5-1.5 4.5-3 6l-1 2H9l-1-2C6.5 13.5 5 11.5 5 9a7 7 0 0 1 7-7z" />
  </svg>
)

export default function QuestionCard({ question, answer, onUpdate }) {
  const [editing, setEditing] = useState(false)
  const [draftText, setDraftText] = useState(answer?.draft_answer || '')
  const [saving, setSaving] = useState(false)

  if (!answer) return null

  const coverage = COVERAGE[answer.evidence_coverage] || COVERAGE.none

  const certaintyColor =
    answer.ai_certainty > 80
      ? 'text-success-text'
      : answer.ai_certainty > 50
      ? 'text-warning-text'
      : 'text-danger-text'

  const borderAccent =
    answer.status === 'approved'
      ? 'border-l-success-text'
      : answer.status === 'edited'
      ? 'border-l-info-text'
      : answer.needs_review
      ? 'border-l-warning-text'
      : 'border-l-mid'

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
    <div
      className={`bg-surface rounded-xl border border-subtle border-l-3 ${borderAccent} p-5 transition-all hover:border-mid hover:shadow-card-hover group`}
    >
      {/* Row 1: header */}
      <div className="flex items-start justify-between mb-2 gap-3">
        <div className="flex items-center gap-2 flex-wrap">
          <span className="font-mono text-[10px] bg-raised text-muted px-2 py-0.5 rounded tracking-wide">
            {question.id.toUpperCase()}
          </span>
          {answer.status === 'approved' && (
            <span className="font-mono text-[10px] tracking-wide font-semibold px-2 py-0.5 rounded bg-success-bg text-success-text border border-success-border">
              APPROVED
            </span>
          )}
          {answer.status === 'edited' && answer.status !== 'approved' && (
            <span className="font-mono text-[10px] tracking-wide font-semibold px-2 py-0.5 rounded bg-info-bg text-info-text border border-info-border">
              EDITED
            </span>
          )}
          {answer.needs_review && answer.status !== 'approved' && (
            <span className="font-mono text-[10px] tracking-wide font-semibold px-2 py-0.5 rounded bg-warning-bg text-warning-text border border-warning-border">
              REVIEW
            </span>
          )}
        </div>

        <div className="flex items-center gap-2 flex-shrink-0">
          {!editing && (
            <button
              onClick={() => { setDraftText(answer.draft_answer); setEditing(true) }}
              className="text-xs text-muted hover:text-primary px-3 py-1 rounded-lg hover:bg-raised transition-all"
            >
              Edit
            </button>
          )}
          {answer.status !== 'approved' && !editing && (
            <button
              onClick={handleApprove}
              className="text-xs font-medium text-secondary hover:text-primary bg-raised hover:bg-overlay border border-mid hover:border-strong px-3 py-1 rounded-lg transition-all"
            >
              Approve
            </button>
          )}
        </div>
      </div>

      {/* Row 2: question */}
      <p className="text-sm text-primary font-medium leading-relaxed mt-2 mb-3">{question.text}</p>

      {/* Row 3: answer */}
      {editing ? (
        <div className="mb-3">
          <textarea
            className="w-full bg-raised border border-amber-400/40 rounded-md p-4 text-sm text-primary resize-none focus:outline-none focus:ring-2 focus:ring-amber-400/25 focus:border-amber-400/60 transition-all"
            rows={5}
            value={draftText}
            onChange={(e) => setDraftText(e.target.value)}
            autoFocus
          />
          <div className="flex gap-2 mt-2">
            <button
              onClick={handleSave}
              disabled={saving}
              className="text-xs font-medium bg-accent text-base px-4 py-1.5 rounded-lg hover:bg-amber-300 disabled:opacity-60 transition-all shadow-btn-primary"
            >
              {saving ? 'Saving...' : 'Save'}
            </button>
            <button
              onClick={() => setEditing(false)}
              className="text-xs text-muted px-4 py-1.5 rounded-lg hover:bg-raised hover:text-primary transition-all"
            >
              Cancel
            </button>
          </div>
        </div>
      ) : (
        <div className="bg-raised rounded-md p-4 mb-3 text-sm text-secondary leading-relaxed whitespace-pre-wrap border-t-2 border-amber-400/20">
          {answer.draft_answer}
        </div>
      )}

      {/* Row 4: metadata footer */}
      <div className="flex items-center gap-2 flex-wrap">
        {/* Evidence sources */}
        {answer.evidence_sources?.length > 0 && (
          <div className="flex items-center gap-1.5 flex-wrap">
            {answer.evidence_sources.map((s, i) => (
              <span
                key={i}
                className="flex items-center gap-1 bg-overlay border border-subtle text-muted text-[10px] px-2 py-0.5 rounded font-mono"
              >
                <FileSmIcon />
                {s}
              </span>
            ))}
          </div>
        )}

        {/* Coverage + certainty — pushed right */}
        <div className="flex items-center gap-3 ml-auto">
          <span
            className={`flex items-center gap-1.5 text-xs px-2 py-0.5 rounded border ${coverage.bg} ${coverage.text} ${coverage.border}`}
          >
            <span className={`w-1.5 h-1.5 rounded-full inline-block ${coverage.dot}`} />
            {coverage.label}
          </span>
          <span className={`font-mono text-xs ${certaintyColor}`}>
            {answer.ai_certainty}%
          </span>
        </div>
      </div>

      {/* Coverage reason */}
      {answer.coverage_reason && (
        <p className="text-[10px] text-muted italic mt-1.5">{answer.coverage_reason}</p>
      )}

      {/* Row 5: suggested addition */}
      {answer.suggested_addition && (
        <div className="mt-3 bg-info-bg border border-info-border/50 rounded-md px-3 py-2 flex items-start gap-2">
          <span className="text-info-text mt-0.5 flex-shrink-0"><BulbIcon /></span>
          <p className="text-xs text-info-text">{answer.suggested_addition}</p>
        </div>
      )}

      {/* Certainty reason */}
      {answer.certainty_reason && (
        <p className="text-[10px] text-muted italic mt-2">{answer.certainty_reason}</p>
      )}
    </div>
  )
}
