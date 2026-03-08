import { useState, useEffect } from 'react'
import { getProviders, createSession, uploadDocs, uploadQuestionnaire, processQuestionnaire } from '../api'

const PROVIDER_LABELS = {
  anthropic: 'Anthropic',
  groq: 'Groq',
  google: 'Google',
}

const FileIcon = ({ size = 32 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
    <polyline points="14 2 14 8 20 8" />
  </svg>
)

const GridIcon = ({ size = 32 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
    <rect x="3" y="3" width="18" height="18" rx="2" />
    <line x1="3" y1="9" x2="21" y2="9" />
    <line x1="3" y1="15" x2="21" y2="15" />
    <line x1="9" y1="9" x2="9" y2="21" />
  </svg>
)

const XIcon = () => (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
    <line x1="18" y1="6" x2="6" y2="18" />
    <line x1="6" y1="6" x2="18" y2="18" />
  </svg>
)

const DOT_GRID_STYLE = {
  backgroundImage: 'radial-gradient(circle, rgba(255,255,255,0.04) 1px, transparent 1px)',
  backgroundSize: '20px 20px',
}

export default function Upload({ onStart }) {
  const [complianceDocs, setComplianceDocs] = useState([])
  const [qFile, setQFile] = useState(null)
  const [qText, setQText] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [dragOverDocs, setDragOverDocs] = useState(false)
  const [dragOverQ, setDragOverQ] = useState(false)
  const [providers, setProviders] = useState([])
  const [selectedProvider, setSelectedProvider] = useState(null)

  useEffect(() => {
    getProviders()
      .then(({ providers }) => {
        setProviders(providers)
        const def = providers.find((p) => p.default) || providers[0]
        if (def) setSelectedProvider(def.id)
      })
      .catch(() => {})
  }, [])

  function addComplianceDocs(files) {
    const supported = Array.from(files).filter((f) => {
      const name = f.name.toLowerCase()
      return (
        f.type === 'application/pdf' ||
        f.type === 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' ||
        name.endsWith('.pdf') ||
        name.endsWith('.docx')
      )
    })
    setComplianceDocs((prev) => {
      const existing = new Set(prev.map((f) => f.name))
      return [...prev, ...supported.filter((f) => !existing.has(f.name))]
    })
  }

  function removeDoc(index) {
    setComplianceDocs((prev) => prev.filter((_, i) => i !== index))
  }

  function handleQFile(file) {
    setQFile(file)
    setQText('')
  }

  const canProcess = complianceDocs.length > 0 && (qFile !== null || qText.trim().length > 0)

  function statusText() {
    if (complianceDocs.length === 0) return 'Add evidence docs to continue.'
    if (!qFile && !qText.trim())
      return `${complianceDocs.length} doc${complianceDocs.length > 1 ? 's' : ''} ready — now add their questionnaire.`
    return `${complianceDocs.length} doc${complianceDocs.length > 1 ? 's' : ''} + questionnaire loaded.`
  }

  async function handleProcess() {
    if (!canProcess || loading) return
    setLoading(true)
    setError(null)
    try {
      const { session_id } = await createSession(selectedProvider)
      await uploadDocs(session_id, complianceDocs)
      await uploadQuestionnaire(session_id, qFile, qText.trim() || null)
      await processQuestionnaire(session_id)
      onStart(session_id)
    } catch (err) {
      setError(err.message || 'Something went wrong — is the backend running?')
      setLoading(false)
    }
  }

  return (
    <div className="max-w-3xl mx-auto px-6 py-10">
      {/* Hero */}
      <div className="mb-8">
        <h1 className="font-serif text-3xl text-primary">Drop in your evidence.</h1>
        <p className="text-secondary text-sm mt-2">
          Seques reads your compliance docs and drafts every answer. You review and ship.
        </p>
      </div>

      {/* Provider selector */}
      {providers.length > 0 && (
        <div className="mb-6 flex items-center gap-3 flex-wrap">
          <span className="text-xs text-muted uppercase tracking-widest font-medium">via</span>
          <div className="flex gap-2 flex-wrap">
            {providers.map((p) => {
              const isSelected = selectedProvider === p.id
              const isUnconfigured = !p.configured
              return (
                <button
                  key={p.id}
                  onClick={() => !isUnconfigured && setSelectedProvider(p.id)}
                  title={isUnconfigured ? `${p.id.toUpperCase()}_API_KEY not set` : p.model}
                  disabled={isUnconfigured}
                  className={`px-3 py-1 rounded-lg border text-xs font-medium transition-all ${
                    isSelected
                      ? 'bg-raised border-amber-400/50 text-amber-400'
                      : isUnconfigured
                      ? 'bg-surface border-subtle text-muted opacity-30 cursor-not-allowed'
                      : 'bg-surface border-mid text-secondary hover:border-strong hover:text-primary'
                  }`}
                >
                  {PROVIDER_LABELS[p.id] ?? p.id}
                </button>
              )
            })}
          </div>
          {selectedProvider && (
            <span className="text-xs text-muted font-mono">
              {providers.find((p) => p.id === selectedProvider)?.model}
            </span>
          )}
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        {/* Compliance docs */}
        <div>
          <p className="text-xs font-medium text-secondary mb-2 uppercase tracking-widest">Evidence docs</p>
          <div
            className={`rounded-xl border min-h-[240px] p-5 transition-all duration-200 ${
              dragOverDocs
                ? 'border-amber-400/50'
                : 'border-subtle'
            }`}
            style={{
              backgroundColor: dragOverDocs ? 'rgba(245,158,11,0.05)' : '#141416',
              ...DOT_GRID_STYLE,
            }}
            onDrop={(e) => {
              e.preventDefault()
              setDragOverDocs(false)
              addComplianceDocs(e.dataTransfer.files)
            }}
            onDragOver={(e) => { e.preventDefault(); setDragOverDocs(true) }}
            onDragLeave={() => setDragOverDocs(false)}
          >
            {complianceDocs.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-full min-h-[180px] text-center">
                <span className={`mb-3 ${dragOverDocs ? 'text-amber-400' : 'text-muted'}`}>
                  <FileIcon size={30} />
                </span>
                <p className="text-sm text-secondary font-medium mb-1">
                  {dragOverDocs ? 'Drop to add' : 'SOC 2, ISO 27001, policies — PDF or Word'}
                </p>
                <label className="cursor-pointer">
                  <span className="text-xs text-amber-400 hover:text-amber-300 underline-offset-2 hover:underline font-medium">
                    Drop files here or browse
                  </span>
                  <input
                    type="file"
                    accept=".pdf,.docx"
                    multiple
                    className="hidden"
                    onChange={(e) => addComplianceDocs(e.target.files)}
                  />
                </label>
                <p className="text-xs text-muted mt-2">Ctrl+click (⌘ on Mac) to select multiple</p>
              </div>
            ) : (
              <div>
                <p className="text-xs text-muted mb-3">{complianceDocs.length} doc{complianceDocs.length > 1 ? 's' : ''} loaded</p>
                <div className="space-y-2 mb-3">
                  {complianceDocs.map((doc, i) => (
                    <div
                      key={i}
                      className="flex items-center justify-between bg-raised rounded-lg px-3 py-2 border border-subtle"
                    >
                      <div className="flex items-center gap-2 min-w-0">
                        <span className="text-muted flex-shrink-0">
                          <FileIcon size={14} />
                        </span>
                        <span className="text-xs text-secondary truncate">{doc.name}</span>
                        <span className="text-xs text-muted font-mono flex-shrink-0">
                          {(doc.size / 1024).toFixed(0)}KB
                        </span>
                      </div>
                      <button
                        onClick={() => removeDoc(i)}
                        className="text-muted hover:text-danger-text ml-2 flex-shrink-0 transition-colors"
                      >
                        <XIcon />
                      </button>
                    </div>
                  ))}
                </div>
                <label className="cursor-pointer">
                  <span className="text-xs text-amber-400 hover:text-amber-300 underline-offset-2 hover:underline font-medium">
                    + Add more
                  </span>
                  <input
                    type="file"
                    accept=".pdf,.docx"
                    multiple
                    className="hidden"
                    onChange={(e) => addComplianceDocs(e.target.files)}
                  />
                </label>
              </div>
            )}
          </div>
        </div>

        {/* Questionnaire */}
        <div>
          <p className="text-xs font-medium text-secondary mb-2 uppercase tracking-widest">Their questionnaire</p>
          <div
            className={`rounded-xl border min-h-[240px] p-5 transition-all duration-200 ${
              dragOverQ ? 'border-amber-400/50' : 'border-subtle'
            }`}
            style={{
              backgroundColor: dragOverQ ? 'rgba(245,158,11,0.05)' : '#141416',
              ...DOT_GRID_STYLE,
            }}
            onDrop={(e) => {
              e.preventDefault()
              setDragOverQ(false)
              if (e.dataTransfer.files[0]) handleQFile(e.dataTransfer.files[0])
            }}
            onDragOver={(e) => { e.preventDefault(); setDragOverQ(true) }}
            onDragLeave={() => setDragOverQ(false)}
          >
            {qFile ? (
              <div className="flex flex-col items-center justify-center h-full min-h-[180px] text-center">
                <span className="text-muted mb-3"><FileIcon size={30} /></span>
                <p className="text-sm text-primary font-medium">{qFile.name}</p>
                <p className="text-xs text-muted font-mono mt-1">{(qFile.size / 1024).toFixed(0)} KB</p>
                <button
                  onClick={() => setQFile(null)}
                  className="mt-4 text-xs text-muted hover:text-danger-text transition-colors"
                >
                  Remove
                </button>
              </div>
            ) : (
              <div className="flex flex-col h-full min-h-[180px]">
                <div className="flex flex-col items-center text-center mb-4">
                  <span className={`mb-3 ${dragOverQ ? 'text-amber-400' : 'text-muted'}`}>
                    <GridIcon size={30} />
                  </span>
                  <p className="text-sm text-secondary font-medium mb-1">
                    {dragOverQ ? 'Drop to load' : 'The prospect\'s questionnaire'}
                  </p>
                  <label className="cursor-pointer">
                    <span className="text-xs text-amber-400 hover:text-amber-300 underline-offset-2 hover:underline font-medium">
                      PDF, Excel, or browse
                    </span>
                    <input
                      type="file"
                      accept=".pdf,.xlsx,.xls"
                      className="hidden"
                      onChange={(e) => e.target.files[0] && handleQFile(e.target.files[0])}
                    />
                  </label>
                </div>
                <div className="flex items-center gap-3 mb-3">
                  <div className="flex-1 h-px bg-white/[0.08]" />
                  <span className="text-xs text-muted">or paste</span>
                  <div className="flex-1 h-px bg-white/[0.08]" />
                </div>
                <textarea
                  className="flex-1 bg-raised border border-mid rounded-md p-3 text-xs text-primary font-mono placeholder:text-muted resize-none focus:outline-none focus:ring-2 focus:ring-amber-400/25 focus:border-strong"
                  rows={5}
                  placeholder={`1. Do you have MFA enforced for all users?\n2. How is data encrypted at rest?\n3. Do you hold a current SOC 2 Type II report?`}
                  value={qText}
                  onChange={(e) => setQText(e.target.value)}
                />
              </div>
            )}
          </div>
        </div>
      </div>

      {error && (
        <div className="mt-5 bg-danger-bg border border-danger-border rounded-lg p-4 text-danger-text text-xs">
          Something went wrong — is the backend running? ({error})
        </div>
      )}

      <div className="mt-8 flex items-center justify-between">
        <p className="text-xs text-muted">{statusText()}</p>
        <button
          onClick={handleProcess}
          disabled={!canProcess || loading}
          className="px-5 py-2 rounded-lg font-medium text-sm text-base bg-accent hover:bg-amber-300 shadow-btn-primary transition-all disabled:opacity-40 disabled:cursor-not-allowed"
        >
          {loading ? 'Starting...' : 'Run it →'}
        </button>
      </div>
    </div>
  )
}
