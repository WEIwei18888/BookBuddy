import { useState } from 'react'
import { submitQuiz } from '../api/client.js'
import { useStore } from '../stores/useStore.js'

export default function QuizCard({ sectionId, quiz, quizType, questionIndex = 0, title = '想一想' }) {
  const [selected, setSelected] = useState(null)
  const [result, setResult] = useState(null)
  const [submitting, setSubmitting] = useState(false)
  const setToast = useStore((state) => state.setToast)

  const handleSubmit = async () => {
    if (selected === null || submitting || result) return
    setSubmitting(true)
    try {
      const data = await submitQuiz(sectionId, quizType, questionIndex, selected)
      setResult(data)
    } catch (error) {
      setToast('测验提交失败，请稍后重试', 'error')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <article
      className={`reader-card border-l-4 ${
        quizType === 'inline' ? 'border-l-amber bg-[#FFF9F0]' : 'border-l-primary bg-[#F0F4FF]'
      }`}
    >
      <div className="reader-card-title">
        <span>{quizType === 'inline' ? '🤔' : '📝'}</span>
        <span>{title}</span>
      </div>
      <div className="card-body font-medium">{quiz.question}</div>
      <div className="mt-4 space-y-2">
        {quiz.options.map((option, index) => {
          const isSelected = selected === index
          const isCorrect = result && result.correct_answer === index
          const isWrong = result && isSelected && !result.is_correct
          return (
            <button
              key={option + index}
              type="button"
              disabled={Boolean(result)}
              onClick={() => setSelected(index)}
              className={`flex w-full items-start gap-3 rounded-md border px-3 py-3 text-left text-sm leading-6 transition ${
                isCorrect
                  ? 'border-success bg-[#F0FFF4] text-ink'
                  : isWrong
                    ? 'border-danger bg-[#FFF5F5] text-ink'
                    : isSelected
                      ? 'border-primary bg-white text-ink'
                      : 'border-black/10 bg-white/80 text-ink hover:border-primary/50'
              }`}
            >
              <span className="mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full border border-current text-xs">
                {String.fromCharCode(65 + index)}
              </span>
              <span>{option}</span>
            </button>
          )
        })}
      </div>
      {result ? (
        <div
          className={`mt-4 rounded-md px-3 py-3 text-sm leading-6 ${
            result.is_correct ? 'bg-[#F0FFF4] text-[#1C6A41]' : 'bg-[#FFF5F5] text-danger'
          }`}
        >
          <div className="font-semibold">{result.is_correct ? '答对了！' : '先记住这个判断。'}</div>
          <div className="mt-1">{result.explanation}</div>
        </div>
      ) : (
        <button
          type="button"
          className="btn-primary mt-4"
          disabled={selected === null || submitting}
          onClick={handleSubmit}
        >
          {submitting ? '提交中...' : '确认'}
        </button>
      )}
    </article>
  )
}

