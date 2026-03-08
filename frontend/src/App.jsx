import { useState } from 'react'
import Upload from './screens/Upload'
import Processing from './screens/Processing'
import Review from './screens/Review'
import Export from './screens/Export'

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
            <span
              className={`text-xs font-medium transition-colors ${
                isActive
                  ? 'text-amber-400'
                  : isDone
                  ? 'text-secondary'
                  : 'text-muted'
              }`}
            >
              {isActive ? '●' : isDone ? '✓' : '○'} {STEP_LABELS[i]}
            </span>
          </div>
        )
      })}
    </div>
  )
}

export default function App() {
  const [screen, setScreen] = useState('upload')
  const [sessionId, setSessionId] = useState(null)
  const [questions, setQuestions] = useState([])
  const [answers, setAnswers] = useState({})

  function handleProcessStart(sid) {
    setSessionId(sid)
    setScreen('processing')
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
    setScreen('upload')
    setSessionId(null)
    setQuestions([])
    setAnswers({})
  }

  return (
    <div className="min-h-screen bg-base">
      <nav className="sticky top-0 z-50 h-[52px] bg-base/95 backdrop-blur-sm border-b border-subtle flex items-center px-6">
        <div className="max-w-4xl mx-auto w-full flex items-center justify-between gap-4">
          {/* Wordmark */}
          <button
            onClick={handleReset}
            className="flex items-center gap-0 group"
          >
            <span className="text-base font-semibold text-primary tracking-tight">
              seques
            </span>
            <span className="block h-0.5 w-full bg-amber-400 mt-px" />
          </button>

          {/* Step indicator — centered */}
          <StepIndicator current={screen} />

          {/* Right action */}
          {screen !== 'upload' ? (
            <button
              onClick={handleReset}
              className="text-xs font-medium text-muted hover:text-primary transition-colors px-3 py-1.5 rounded-lg hover:bg-raised"
            >
              + New
            </button>
          ) : (
            <div className="w-16" />
          )}
        </div>
      </nav>

      {screen === 'upload' && <Upload onStart={handleProcessStart} />}
      {screen === 'processing' && (
        <Processing sessionId={sessionId} onDone={handleProcessingDone} />
      )}
      {screen === 'review' && (
        <Review
          sessionId={sessionId}
          questions={questions}
          answers={answers}
          onAnswerUpdate={handleAnswerUpdate}
          onExport={() => setScreen('export')}
        />
      )}
      {screen === 'export' && (
        <Export
          sessionId={sessionId}
          questions={questions}
          answers={answers}
          onBack={() => setScreen('review')}
        />
      )}
    </div>
  )
}
