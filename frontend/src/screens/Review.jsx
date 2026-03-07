import { useState } from 'react'
import { updateAnswer } from '../api'
import QuestionCard from '../components/QuestionCard'

export default function Review({ sessionId, questions, answers, onAnswerUpdate, onExport }) {
  const [filter, setFilter] = useState('all')

  const answerList = Object.values(answers)

  const counts = {
    total: questions.length,
    ready: answerList.filter((a) => !a.needs_review && a.evidence_coverage !== 'none').length,
    review: answerList.filter((a) => a.needs_review).length,
    gaps: answerList.filter((a) => a.evidence_coverage === 'none').length,
    approved: answerList.filter((a) => a.status === 'approved').length,
  }

  const filtered = questions.filter((q) => {
    const a = answers[q.id]
    if (!a) return false
    if (filter === 'ready') return !a.needs_review && a.evidence_coverage !== 'none'
    if (filter === 'review') return a.needs_review
    if (filter === 'gaps') return a.evidence_coverage === 'none'
    return true
  })

  async function handleUpdate(questionId, fields) {
    const updated = await updateAnswer(sessionId, questionId, fields)
    onAnswerUpdate(questionId, updated)
  }

  const tabs = [
    { key: 'all', label: `All (${counts.total})` },
    { key: 'ready', label: `✅ Ready (${counts.ready})` },
    { key: 'review', label: `⚠️ Review (${counts.review})` },
    { key: 'gaps', label: `🔴 Gaps (${counts.gaps})` },
  ]

  return (
    <div className="max-w-4xl mx-auto px-6 py-8">
      {/* Page header */}
      <div className="flex items-start justify-between mb-6 gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Review Answers</h1>
          <p className="text-slate-500 mt-1 text-sm">
            {counts.total} questions &nbsp;&middot;&nbsp;
            <span className="text-green-600">{counts.ready} ready</span>
            &nbsp;&middot;&nbsp;
            <span className="text-amber-600">{counts.review} need review</span>
            &nbsp;&middot;&nbsp;
            <span className="text-red-600">{counts.gaps} gaps</span>
          </p>
        </div>
        <div className="flex items-center gap-3 flex-shrink-0">
          <span className="text-sm text-slate-400">
            {counts.approved}/{counts.total} approved
          </span>
          <button
            onClick={onExport}
            className="px-5 py-2.5 bg-blue-600 text-white rounded-xl font-semibold hover:bg-blue-700 transition shadow-sm"
          >
            Export →
          </button>
        </div>
      </div>

      {/* Filter tabs */}
      <div className="flex gap-2 mb-6 flex-wrap">
        {tabs.map((tab) => (
          <button
            key={tab.key}
            onClick={() => setFilter(tab.key)}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition ${
              filter === tab.key
                ? 'bg-blue-600 text-white shadow-sm'
                : 'bg-white text-slate-600 border border-slate-200 hover:border-blue-300 hover:text-blue-600'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Question cards */}
      {filtered.length === 0 ? (
        <div className="text-center py-16 text-slate-400">
          No questions in this category.
        </div>
      ) : (
        <div className="space-y-4">
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
