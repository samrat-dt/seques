import { useState, useEffect } from 'react'
import { getProviders, createSession, uploadDocs, uploadQuestionnaire, processQuestionnaire } from '../api'

const DOC_TYPE_LABELS = {
  '.pdf': 'PDF',
}

const PROVIDER_LABELS = {
  anthropic: 'Anthropic',
  groq: 'Groq',
  google: 'Google',
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
      .catch(() => {
        // backend not running yet — silently ignore
      })
  }, [])

  function addComplianceDocs(files) {
    const pdfs = Array.from(files).filter(
      (f) => f.type === 'application/pdf' || f.name.toLowerCase().endsWith('.pdf')
    )
    setComplianceDocs((prev) => {
      const existing = new Set(prev.map((f) => f.name))
      return [...prev, ...pdfs.filter((f) => !existing.has(f.name))]
    })
  }

  function removeDoc(index) {
    setComplianceDocs((prev) => prev.filter((_, i) => i !== index))
  }

  function handleQFile(file) {
    setQFile(file)
    setQText('')
  }

  const canProcess =
    complianceDocs.length > 0 && (qFile !== null || qText.trim().length > 0)

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
      setError(err.message || 'Something went wrong. Is the backend running?')
      setLoading(false)
    }
  }

  return (
    <div className="max-w-5xl mx-auto px-6 py-10">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-slate-900">New Questionnaire</h1>
        <p className="text-slate-500 mt-1">
          Upload your compliance docs and the prospect's questionnaire. AI will draft every answer.
        </p>
      </div>

      {providers.length > 0 && (
        <div className="mb-6 flex items-center gap-3">
          <span className="text-sm font-medium text-slate-600 whitespace-nowrap">AI model:</span>
          <div className="flex gap-2 flex-wrap">
            {providers.map((p) => {
              const isSelected = selectedProvider === p.id
              const isUnconfigured = !p.configured
              return (
                <button
                  key={p.id}
                  onClick={() => !isUnconfigured && setSelectedProvider(p.id)}
                  title={isUnconfigured ? `${p.id.toUpperCase()}_API_KEY not set in .env` : p.model}
                  className={`px-3 py-1.5 rounded-lg text-sm font-medium border transition-all ${
                    isSelected
                      ? 'bg-blue-600 border-blue-600 text-white shadow-sm'
                      : isUnconfigured
                      ? 'border-slate-200 text-slate-300 cursor-not-allowed bg-white'
                      : 'border-slate-300 text-slate-600 bg-white hover:border-blue-400 hover:text-blue-600'
                  }`}
                >
                  {PROVIDER_LABELS[p.id] ?? p.id}
                  {isUnconfigured && (
                    <span className="ml-1.5 text-xs font-normal opacity-60">no key</span>
                  )}
                </button>
              )
            })}
          </div>
          {selectedProvider && (
            <span className="text-xs text-slate-400 hidden sm:block">
              {providers.find((p) => p.id === selectedProvider)?.model}
            </span>
          )}
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Left: Compliance Docs */}
        <div>
          <h2 className="font-semibold text-slate-700 mb-1">Your Compliance Docs</h2>
          <p className="text-xs text-slate-400 mb-3">SOC 2, ISO 27001, security policies — PDF only</p>
          <div
            className={`border-2 border-dashed rounded-xl p-6 transition-colors min-h-[220px] ${
              dragOverDocs
                ? 'border-blue-400 bg-blue-50'
                : 'border-slate-300 bg-white hover:border-slate-400'
            }`}
            onDrop={(e) => {
              e.preventDefault()
              setDragOverDocs(false)
              addComplianceDocs(e.dataTransfer.files)
            }}
            onDragOver={(e) => {
              e.preventDefault()
              setDragOverDocs(true)
            }}
            onDragLeave={() => setDragOverDocs(false)}
          >
            <div className="text-center mb-4">
              <div className="text-3xl mb-2">📋</div>
              <p className="text-slate-500 text-sm">Drop PDF files here</p>
            </div>
            <label className="block text-center cursor-pointer mb-4">
              <span className="text-blue-600 text-sm font-medium hover:underline">
                Browse files
              </span>
              <input
                type="file"
                accept=".pdf"
                multiple
                className="hidden"
                onChange={(e) => addComplianceDocs(e.target.files)}
              />
            </label>

            {complianceDocs.length > 0 && (
              <div className="space-y-2">
                {complianceDocs.map((doc, i) => (
                  <div
                    key={i}
                    className="flex items-center justify-between bg-green-50 border border-green-100 rounded-lg px-3 py-2"
                  >
                    <div className="flex items-center gap-2 min-w-0">
                      <span className="text-green-600 flex-shrink-0">✅</span>
                      <span className="text-sm text-slate-700 truncate">{doc.name}</span>
                    </div>
                    <button
                      onClick={() => removeDoc(i)}
                      className="text-slate-300 hover:text-red-400 ml-2 flex-shrink-0 transition"
                    >
                      ✕
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Right: Questionnaire */}
        <div>
          <h2 className="font-semibold text-slate-700 mb-1">Their Questionnaire</h2>
          <p className="text-xs text-slate-400 mb-3">Upload PDF or Excel, or paste questions below</p>
          <div
            className={`border-2 border-dashed rounded-xl p-6 transition-colors min-h-[220px] ${
              dragOverQ
                ? 'border-blue-400 bg-blue-50'
                : 'border-slate-300 bg-white hover:border-slate-400'
            }`}
            onDrop={(e) => {
              e.preventDefault()
              setDragOverQ(false)
              if (e.dataTransfer.files[0]) handleQFile(e.dataTransfer.files[0])
            }}
            onDragOver={(e) => {
              e.preventDefault()
              setDragOverQ(true)
            }}
            onDragLeave={() => setDragOverQ(false)}
          >
            {qFile ? (
              <div className="text-center">
                <div className="text-3xl mb-2">📄</div>
                <p className="text-slate-800 font-medium text-sm">{qFile.name}</p>
                <p className="text-slate-400 text-xs mt-1">
                  {(qFile.size / 1024).toFixed(0)} KB
                </p>
                <button
                  onClick={() => setQFile(null)}
                  className="mt-3 text-xs text-slate-400 hover:text-red-500 transition"
                >
                  Remove
                </button>
              </div>
            ) : (
              <>
                <div className="text-center mb-3">
                  <div className="text-3xl mb-2">📝</div>
                  <p className="text-slate-500 text-sm">Drop PDF or Excel here</p>
                </div>
                <label className="block text-center cursor-pointer mb-4">
                  <span className="text-blue-600 text-sm font-medium hover:underline">
                    Browse files
                  </span>
                  <input
                    type="file"
                    accept=".pdf,.xlsx,.xls"
                    className="hidden"
                    onChange={(e) => e.target.files[0] && handleQFile(e.target.files[0])}
                  />
                </label>
                <div className="flex items-center gap-3 mb-4">
                  <div className="flex-1 h-px bg-slate-200" />
                  <span className="text-slate-400 text-xs">or paste questions</span>
                  <div className="flex-1 h-px bg-slate-200" />
                </div>
                <textarea
                  className="w-full border border-slate-200 rounded-lg p-3 text-sm text-slate-700 resize-none focus:outline-none focus:ring-2 focus:ring-blue-300 focus:border-transparent"
                  rows={5}
                  placeholder={`1. Do you have MFA enabled?\n2. How do you encrypt data at rest?\n3. Do you have a SOC 2 report?`}
                  value={qText}
                  onChange={(e) => setQText(e.target.value)}
                />
              </>
            )}
          </div>
        </div>
      </div>

      {error && (
        <div className="mt-5 bg-red-50 border border-red-200 rounded-xl p-4 text-red-700 text-sm">
          <strong>Error:</strong> {error}
        </div>
      )}

      <div className="mt-8 flex items-center justify-between">
        <p className="text-slate-400 text-sm">
          {complianceDocs.length > 0
            ? `${complianceDocs.length} compliance doc${complianceDocs.length > 1 ? 's' : ''} ready`
            : 'Upload your compliance docs to get started'}
        </p>
        <button
          onClick={handleProcess}
          disabled={!canProcess || loading}
          className={`px-8 py-3 rounded-xl font-semibold text-white transition-all shadow-sm ${
            canProcess && !loading
              ? 'bg-blue-600 hover:bg-blue-700 hover:shadow-md'
              : 'bg-slate-300 cursor-not-allowed'
          }`}
        >
          {loading ? 'Starting...' : 'Process Questionnaire →'}
        </button>
      </div>
    </div>
  )
}
