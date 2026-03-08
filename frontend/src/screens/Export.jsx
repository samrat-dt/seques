import { getExcelUrl, getPdfUrl } from '../api'

const TableIcon = () => (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <rect x="3" y="3" width="18" height="18" rx="2" />
    <line x1="3" y1="9" x2="21" y2="9" />
    <line x1="3" y1="15" x2="21" y2="15" />
    <line x1="9" y1="9" x2="9" y2="21" />
  </svg>
)

const FileTextIcon = () => (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
    <polyline points="14 2 14 8 20 8" />
    <line x1="16" y1="13" x2="8" y2="13" />
    <line x1="16" y1="17" x2="8" y2="17" />
    <polyline points="10 9 9 9 8 9" />
  </svg>
)

const WarnIcon = () => (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
    <line x1="12" y1="9" x2="12" y2="13" />
    <line x1="12" y1="17" x2="12.01" y2="17" />
  </svg>
)

export default function Export({ sessionId, questions, answers, onBack }) {
  const total    = questions.length
  const approved = Object.values(answers).filter((a) => a.status === 'approved' || a.status === 'edited').length
  const flagged  = total - approved
  const gaps     = Object.values(answers).filter((a) => a.evidence_coverage === 'none').length
  const hasIssues = gaps > 0

  return (
    <div className="max-w-2xl mx-auto px-6 py-12">
      {/* Heading */}
      <h1 className="font-serif text-3xl text-primary">
        {hasIssues ? 'Almost. Check your gaps.' : 'Done. Export your response.'}
      </h1>
      <p className="text-secondary text-sm mt-2">
        {hasIssues
          ? `${gaps} question${gaps > 1 ? 's' : ''} couldn't be answered from your docs. Export anyway or go back.`
          : 'Everything\'s drafted. Download and send.'}
      </p>

      {/* Stats */}
      <div className="flex items-center justify-center gap-0 mt-8 mb-6">
        <div className="text-center px-8">
          <p className={`text-2xl font-bold font-mono ${approved === total ? 'text-success-text' : 'text-primary'}`}>
            {approved}
          </p>
          <p className="text-xs text-muted uppercase tracking-wider mt-0.5">approved</p>
        </div>
        <div className="w-px h-10 bg-white/[0.08]" />
        <div className="text-center px-8">
          <p className="text-2xl font-bold font-mono text-primary">{total}</p>
          <p className="text-xs text-muted uppercase tracking-wider mt-0.5">total questions</p>
        </div>
        {gaps > 0 && (
          <>
            <div className="w-px h-10 bg-white/[0.08]" />
            <div className="text-center px-8">
              <p className="text-2xl font-bold font-mono text-danger-text">{gaps}</p>
              <p className="text-xs text-muted uppercase tracking-wider mt-0.5">gaps</p>
            </div>
          </>
        )}
      </div>

      {/* Warning callouts */}
      {flagged > 0 && (
        <div className="bg-warning-bg border border-warning-border/60 rounded-lg px-4 py-3 mb-3 flex items-start gap-2.5">
          <span className="text-warning-text mt-0.5 flex-shrink-0"><WarnIcon /></span>
          <p className="text-sm text-warning-text">
            {flagged} answer{flagged > 1 ? 's' : ''} not approved yet — exported as drafted. Review them before sending.
          </p>
        </div>
      )}
      {gaps > 0 && (
        <div className="bg-danger-bg border border-danger-border/60 rounded-lg px-4 py-3 mb-3 flex items-start gap-2.5">
          <span className="text-danger-text mt-0.5 flex-shrink-0"><WarnIcon /></span>
          <p className="text-sm text-danger-text">
            {gaps} question{gaps > 1 ? 's' : ''} have no evidence. They'll export as blank. Consider adding a note or uploading more docs.
          </p>
        </div>
      )}

      {/* Download buttons */}
      <div className="flex flex-col gap-3 mt-8 max-w-xs mx-auto">
        <a
          href={getExcelUrl(sessionId)}
          download
          className="flex items-center justify-center gap-2 px-6 py-2.5 bg-accent text-base rounded-lg font-medium text-sm hover:bg-amber-300 shadow-btn-primary transition-all"
        >
          <TableIcon />
          Download Excel
        </a>
        <a
          href={getPdfUrl(sessionId)}
          download
          className="flex items-center justify-center gap-2 px-6 py-2.5 bg-surface border border-mid text-primary rounded-lg font-medium text-sm hover:bg-raised hover:border-strong transition-all"
        >
          <FileTextIcon />
          Download PDF
        </a>
        <button
          onClick={onBack}
          className="px-6 py-2.5 text-muted hover:text-secondary text-sm font-medium transition-colors"
        >
          ← Back to review
        </button>
      </div>

      <p className="text-xs text-muted text-center mt-10">
        Your session data stays until you close this tab.
      </p>
    </div>
  )
}
