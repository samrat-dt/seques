import { useState, useEffect } from 'react'
import Upload from './screens/Upload'
import Processing from './screens/Processing'
import Review from './screens/Review'
import Export from './screens/Export'
import Landing from './screens/Landing'
import Auth from './screens/Auth'
import { getStatus, getAnswers, setAuthToken } from './api'
import { supabase } from './supabase'

const STEPS = ['upload', 'processing', 'review', 'export']
const STEP_LABELS = ['Upload', 'Processing', 'Review', 'Export']

function StepIndicator({ current }) {
  const idx = STEPS.indexOf(current)
  return (
    <div className="hidden sm:flex items-center gap-2">
      {STEPS.map((step, i) => {
        const isDone = i < idx
        const isActive = i === idx
        return (
          <div key={step} className="flex items-center gap-2">
            {i > 0 && <div className="w-6 h-px bg-white/[0.06]" />}
            <span className={`text-xs font-medium transition-colors ${isActive ? 'text-amber-400' : isDone ? 'text-secondary' : 'text-muted'}`}>
              {isActive ? '●' : isDone ? '✓' : '○'} {STEP_LABELS[i]}
            </span>
          </div>
        )
      })}
    </div>
  )
}

export default function App() {
  const [authReady, setAuthReady] = useState(!supabase) // true immediately if no supabase
  const [user, setUser] = useState(null)
  const [screen, setScreen] = useState('landing')
  const [sessionId, setSessionId] = useState(null)
  const [questions, setQuestions] = useState([])
  const [answers, setAnswers] = useState({})

  // Auth gate — only when Supabase is configured
  useEffect(() => {
    if (!supabase) return

    supabase.auth.getSession().then(({ data: { session } }) => {
      if (session) {
        setUser(session.user)
        setAuthToken(session.access_token)
      }
      setAuthReady(true)
    })

    const { data: { subscription } } = supabase.auth.onAuthStateChange((event, session) => {
      if (session) {
        setUser(session.user)
        setAuthToken(session.access_token)
        // After magic link click, take user straight to Upload instead of making
        // them click "Get started" on Landing again.
        if (event === 'SIGNED_IN') {
          setScreen('upload')
        }
      } else {
        setUser(null)
        setAuthToken(null)
      }
    })

    return () => subscription.unsubscribe()
  }, [])

  // Restore session from URL on mount (after auth ready)
  useEffect(() => {
    if (!authReady) return
    const params = new URLSearchParams(window.location.search)
    const sid = params.get('s')
    if (!sid) return
    getStatus(sid)
      .then((status) => {
        if (!status.processing && status.processed > 0) {
          return getAnswers(sid).then((data) => {
            setSessionId(sid)
            setQuestions(data.questions)
            setAnswers(data.answers)
            setScreen('review')
          })
        }
      })
      .catch(() => window.history.replaceState({}, '', window.location.pathname))
  }, [authReady])

  function handleProcessStart(sid) {
    setSessionId(sid)
    setScreen('processing')
    window.history.pushState({}, '', `?s=${sid}`)
  }

  function handleProcessingDone(data) {
    setQuestions(data.questions)
    setAnswers(data.answers)
    setScreen('review')
  }

  function handleAnswerUpdate(questionId, updated) {
    setAnswers((prev) => ({ ...prev, [questionId]: updated }))
  }

  function handleReset() {
    setScreen('landing')
    setSessionId(null)
    setQuestions([])
    setAnswers({})
    window.history.replaceState({}, '', window.location.pathname)
  }

  async function handleSignOut() {
    if (supabase) await supabase.auth.signOut()
    handleReset()
  }

  if (!authReady) return null
  if (screen === 'landing') return <Landing onStart={() => setScreen('upload')} />
  if (supabase && !user) return <Auth />

  return (
    <div className="min-h-screen bg-base">
      <nav className="sticky top-0 z-50 h-[52px] bg-base/95 backdrop-blur-sm border-b border-subtle flex items-center px-6">
        <div className="max-w-4xl mx-auto w-full flex items-center justify-between gap-4">
          <button onClick={handleReset} className="flex items-center gap-0 group">
            <span className="text-base font-semibold text-primary tracking-tight">seques</span>
            <span className="block h-0.5 w-full bg-amber-400 mt-px" />
          </button>
          <StepIndicator current={screen} />
          <div className="flex items-center gap-2">
            {screen !== 'upload' && (
              <button onClick={handleReset} className="text-xs font-medium text-muted hover:text-primary transition-colors px-3 py-1.5 rounded-lg hover:bg-raised">
                + New
              </button>
            )}
            {supabase && user && (
              <button onClick={handleSignOut} className="text-xs text-muted hover:text-primary transition-colors px-3 py-1.5 rounded-lg hover:bg-raised">
                Sign out
              </button>
            )}
          </div>
        </div>
      </nav>

      {screen === 'upload' && <Upload onStart={handleProcessStart} />}
      {screen === 'processing' && <Processing sessionId={sessionId} onDone={handleProcessingDone} />}
      {screen === 'review' && (
        <Review sessionId={sessionId} questions={questions} answers={answers}
          onAnswerUpdate={handleAnswerUpdate} onExport={() => setScreen('export')} />
      )}
      {screen === 'export' && (
        <Export sessionId={sessionId} questions={questions} answers={answers}
          onBack={() => setScreen('review')} />
      )}
    </div>
  )
}
