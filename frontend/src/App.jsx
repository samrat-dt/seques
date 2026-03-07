import { useState } from 'react'
import Upload from './screens/Upload'
import Processing from './screens/Processing'
import Review from './screens/Review'
import Export from './screens/Export'

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

  return (
    <div className="min-h-screen bg-slate-50">
      <nav className="bg-white border-b border-slate-200 px-6 py-4 sticky top-0 z-10">
        <div className="max-w-5xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className="text-xl font-bold text-blue-700 tracking-tight">seques</span>
            <span className="hidden sm:inline text-slate-400 text-sm">
              AI Security Questionnaire Co-Pilot
            </span>
          </div>
          {screen !== 'upload' && (
            <button
              onClick={() => {
                setScreen('upload')
                setSessionId(null)
                setQuestions([])
                setAnswers({})
              }}
              className="text-sm text-slate-500 hover:text-slate-800 transition"
            >
              + New Questionnaire
            </button>
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
