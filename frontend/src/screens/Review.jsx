import { useState } from 'react'
import { updateAnswer } from '../api'
import QuestionCard from '../components/QuestionCard'

const EMPTY_STATES = {
  all:      'Nothing to review. Something\'s off.',
  answered: 'No answered questions yet — might need more docs.',
  flagged:  'No flagged answers. You\'re in good shape.',
  gaps:     'No gaps found. Either your docs are thorough or the questions were easy.',
}

export default function Review({ sessionId, questions, answers, onAnswerUpdate, onExport }) {
  const [filter, setFilter] = useState('all')

  const answerList = Object.values(answers)

  const counts = {
    total:    questions.length,
    answered: answerList.filter((a) => !a.needs_review && a.evidence_coverage !== 'none').length,
    flagged:  answerList.filter((a) => a.needs_review).length,
    gaps:     answerList.filter((a) => a.evidence_coverage === 'none').length,
    approved: answerList.filter((a) => a.status === 'approved').length,
  }

  const filtered = questions.filter((q) => {
    const a = answers[q.id]
    if (!a) return false
    if (filter === 'answered') return !a.needs_review && a.evidence_coverage !== 'none'
    if (filter === 'flagged')  return a.needs_review
    if (filter === 'gaps')     return a.evidence_coverage === 'none'
    return true
  })

  const tabs = [
    { key: 'all',      label: 'All',      count: counts.total },
    { key: 'answered', label: 'Answered', count: counts.answered },
    { key: 'flagged',  label: 'Flagged',  count: counts.flagged },
    { key: 'gaps',     label: 'Gaps',     count: counts.gaps },
  ]

  async function handleUpdate(questionId, fields) {
    const updated = await updateAnswer(sessionId, questionId, fields)
    onAnswerUpdate(questionId, updated)
  }

  return (
    <div className="max-w-4xl mx-auto px-6 py-8">
      {/* Header */}
      <div className="flex items-start justify-between mb-6 gap-4">
        <div>
          <h1 className="font-serif text-3xl text-primary">Review & approve.</h1>
          <p className="text-secondary text-sm mt-1.5">
            {counts.total} questions
            <span className="mx-2 text-muted">·</span>
            <span className="text-success-text">{counts.answered} answered</span>
            <span className="mx-2 text-muted">·</span>
            <span className="text-warning-text">{counts.flagged} flagged</span>
            <span className="mx-2 text-muted">·</span>
            <span className="text-danger-text">{counts.gaps} gaps</span>
          </p>
        </div>
        <div className="flex items-center gap-3 flex-shrink-0">
          <span className="text-xs text-muted font-mono">
            {counts.approved}/{counts.total} approved
          </span>
          <button
            onClick={onExport}
            className="px-5 py-2 bg-accent text-base rounded-lg font-medium text-sm hover:bg-amber-300 shadow-btn-primary transition-all"
          >
            Export →
          </button>
        </div>
      </div>

      {/* Filter tabs — underline style */}
      <div className="flex border-b border-subtle mb-6">
        {tabs.map((tab) => (
          <button
            key={tab.key}
            onClick={() => setFilter(tab.key)}
            className={`relative px-4 py-2.5 text-sm font-medium transition-colors ${
              filter === tab.key ? 'text-primary' : 'text-muted hover:text-secondary'
            }`}
          >
            {tab.label}
            <span className={`ml-1.5 text-xs ${filter === tab.key ? 'text-secondary' : 'text-muted'}`}>
              {tab.count}
            </span>
            {filter === tab.key && (
              <span className="absolute bottom-0 left-0 right-0 h-0.5 bg-amber-400 rounded-full" />
            )}
          </button>
        ))}
      </div>

      {/* Cards */}
      {filtered.length === 0 ? (
        <div className="text-center py-16 text-muted text-sm">
          {EMPTY_STATES[filter]}
        </div>
      ) : (
        <div className="space-y-3">
          {filtered.map((q) => (
            <QuestionCard
              key={q.id}
              question={q}
              answer={answers[q.id]}
              onUpdate={(fields) => handleUpdate(q.id, fields)}
            />
          ))}
        </div>
      )}
    </div>
  )
}
