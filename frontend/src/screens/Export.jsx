import { getExcelUrl, getPdfUrl } from '../api'

export default function Export({ sessionId, questions, answers, onBack }) {
  const total = questions.length
  const approved = Object.values(answers).filter(
    (a) => a.status === 'approved' || a.status === 'edited'
  ).length
  const flagged = total - approved
  const gaps = Object.values(answers).filter((a) => a.evidence_coverage === 'none').length

  return (
    <div className="max-w-lg mx-auto px-6 py-20">
      <div className="bg-white rounded-2xl shadow-sm border border-slate-100 p-8 text-center">
        <div className="text-5xl mb-4">📤</div>
        <h2 className="text-2xl font-bold text-slate-900 mb-2">Export your response</h2>

        <div className="flex items-center justify-center gap-6 my-4 text-sm">
          <div>
            <span className="text-2xl font-bold text-green-600">{approved}</span>
            <p className="text-slate-400 text-xs mt-0.5">approved</p>
          </div>
          <div className="w-px h-8 bg-slate-200" />
          <div>
            <span className="text-2xl font-bold text-slate-700">{total}</span>
            <p className="text-slate-400 text-xs mt-0.5">total</p>
          </div>
          {gaps > 0 && (
            <>
              <div className="w-px h-8 bg-slate-200" />
              <div>
                <span className="text-2xl font-bold text-red-500">{gaps}</span>
                <p className="text-slate-400 text-xs mt-0.5">gaps</p>
              </div>
            </>
          )}
        </div>

        {flagged > 0 && (
          <p className="text-amber-600 text-sm mb-2">
            {flagged} question{flagged > 1 ? 's' : ''} still flagged — you can export anyway or go
            back to review.
          </p>
        )}

        {gaps > 0 && (
          <p className="text-red-600 text-sm mb-2">
            {gaps} question{gaps > 1 ? 's' : ''} have no evidence in your docs — consider adding a
            note or leaving blank.
          </p>
        )}

        <div className="flex flex-col gap-3 mt-6">
          <a
            href={getExcelUrl(sessionId)}
            download
            className="flex items-center justify-center gap-2 px-6 py-3.5 bg-green-600 text-white rounded-xl font-semibold hover:bg-green-700 transition shadow-sm"
          >
            ⬇ Download Excel
          </a>
          <a
            href={getPdfUrl(sessionId)}
            download
            className="flex items-center justify-center gap-2 px-6 py-3.5 bg-blue-600 text-white rounded-xl font-semibold hover:bg-blue-700 transition shadow-sm"
          >
            ⬇ Download PDF
          </a>
          <button
            onClick={onBack}
            className="px-6 py-3 text-slate-600 border border-slate-200 rounded-xl font-medium hover:bg-slate-50 transition"
          >
            ← Back to Review
          </button>
        </div>
      </div>
    </div>
  )
}
