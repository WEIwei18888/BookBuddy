import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import BridgeCard from '../components/BridgeCard.jsx'
import ContentCard from '../components/ContentCard.jsx'
import HookCard from '../components/HookCard.jsx'
import InsightCard from '../components/InsightCard.jsx'
import LoadingState from '../components/LoadingState.jsx'
import ProgressBar from '../components/ProgressBar.jsx'
import QuizCard from '../components/QuizCard.jsx'
import ReflectionCard from '../components/ReflectionCard.jsx'
import {
  extractErrorMessage,
  getProgress,
  getSection,
  getSectionStatus,
  updateProgress,
} from '../api/client.js'
import { useStore } from '../stores/useStore.js'

export default function Reader() {
  const { bookId, sectionIndex } = useParams()
  const numericSectionIndex = Number(sectionIndex)
  const navigate = useNavigate()
  const [section, setSection] = useState(null)
  const [loadingState, setLoadingState] = useState('loading')
  const [error, setError] = useState('')
  const [progress, setProgress] = useState(null)
  const [activePosition, setActivePosition] = useState('start')
  const observerRef = useRef(null)
  const setToast = useStore((state) => state.setToast)

  const loadSection = useCallback(
    async (force = false) => {
      setError('')
      try {
        const result = await getSection(bookId, numericSectionIndex, force)
        if (result.statusCode === 202) {
          setLoadingState('processing')
          return
        }
        setSection(result.data)
        setLoadingState('ready')
      } catch (requestError) {
        setError(extractErrorMessage(requestError, '小节加载失败'))
        setLoadingState('error')
      }
    },
    [bookId, numericSectionIndex],
  )

  const finishSection = useCallback(
    async (goNext) => {
      try {
        await updateProgress(bookId, numericSectionIndex, 'complete')
        if (goNext && section?.has_next) {
          navigate(`/book/${bookId}/read/${numericSectionIndex + 1}`)
        } else {
          navigate(`/book/${bookId}`)
        }
      } catch (requestError) {
        setToast('进度保存失败，请稍后重试', 'error')
      }
    },
    [bookId, navigate, numericSectionIndex, section?.has_next, setToast],
  )

  useEffect(() => {
    setSection(null)
    setLoadingState('loading')
    setActivePosition('start')
    loadSection()
    getProgress(bookId)
      .then(setProgress)
      .catch(() => null)
  }, [bookId, numericSectionIndex, loadSection])

  useEffect(() => {
    if (loadingState !== 'processing') return undefined
    const timer = window.setInterval(async () => {
      try {
        const status = await getSectionStatus(bookId, numericSectionIndex)
        if (status.status === 'ready') {
          window.clearInterval(timer)
          loadSection()
        } else if (status.status === 'error') {
          window.clearInterval(timer)
          setError(status.message || '这一节处理失败')
          setLoadingState('error')
        }
      } catch (requestError) {
        window.clearInterval(timer)
        setError(extractErrorMessage(requestError, '状态查询失败'))
        setLoadingState('error')
      }
    }, 2000)
    return () => window.clearInterval(timer)
  }, [loadingState, bookId, numericSectionIndex, loadSection])

  const cards = useMemo(() => {
    if (!section?.content_json) return []
    const content = section.content_json
    const flow = [{ key: 'hook', position: 'start', node: <HookCard text={content.hook} /> }]
    content.content_cards?.forEach((card, index) => {
      flow.push({
        key: `card-${index}`,
        position: `card:${index}`,
        node: <ContentCard card={card} />,
      })
      if (content.inline_quiz && content.inline_quiz.position === index + 1) {
        flow.push({
          key: 'inline-quiz',
          position: 'quiz:inline',
          node: (
            <QuizCard
              sectionId={section.id}
              quiz={content.inline_quiz}
              quizType="inline"
              questionIndex={0}
              title="想一想"
            />
          ),
        })
      }
    })
    content.section_quiz?.forEach((quiz, index) => {
      flow.push({
        key: `section-quiz-${index}`,
        position: `quiz:section:${index}`,
        node: (
          <QuizCard
            sectionId={section.id}
            quiz={quiz}
            quizType="section"
            questionIndex={index}
            title={`小测验 ${index + 1}/${content.section_quiz.length}`}
          />
        ),
      })
    })
    flow.push({
      key: 'reflection',
      position: 'reflection',
      node: <ReflectionCard text={content.reflection} />,
    })
    flow.push({
      key: 'insights',
      position: 'insights',
      node: <InsightCard cards={content.insight_cards} />,
    })
    flow.push({
      key: 'bridge',
      position: 'bridge',
      node: (
        <BridgeCard
          text={content.bridge}
          hasNext={section.has_next}
          onNext={() => finishSection(true)}
          onFinish={() => finishSection(false)}
        />
      ),
    })
    return flow.filter((item) => item.node)
  }, [section, finishSection])

  const savePosition = useCallback(
    (position) => {
      setActivePosition(position)
      updateProgress(bookId, numericSectionIndex, position).catch(() => null)
    },
    [bookId, numericSectionIndex],
  )

  useEffect(() => {
    if (!cards.length) return undefined
    observerRef.current?.disconnect()
    observerRef.current = new IntersectionObserver(
      (entries) => {
        const visible = entries
          .filter((entry) => entry.isIntersecting)
          .sort((a, b) => b.intersectionRatio - a.intersectionRatio)[0]
        const position = visible?.target?.getAttribute('data-position')
        if (position) savePosition(position)
      },
      { threshold: [0.45, 0.7] },
    )

    const nodes = document.querySelectorAll('[data-reader-card="true"]')
    nodes.forEach((node) => observerRef.current.observe(node))
    return () => observerRef.current?.disconnect()
  }, [cards, savePosition])

  useEffect(() => {
    if (!section || !progress) return
    if (progress.current_section_index !== numericSectionIndex) return
    const target = progress.current_position || 'start'
    window.setTimeout(() => {
      const node = document.querySelector(`[data-position="${CSS.escape(target)}"]`)
      node?.scrollIntoView({ behavior: 'smooth', block: 'start' })
    }, 250)
  }, [section, progress, numericSectionIndex])

  useEffect(() => {
    const handleBeforeUnload = () => {
      fetch(`/api/progress/${bookId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          section_index: numericSectionIndex,
          position: activePosition,
        }),
        keepalive: true,
      }).catch(() => null)
    }
    window.addEventListener('beforeunload', handleBeforeUnload)
    return () => window.removeEventListener('beforeunload', handleBeforeUnload)
  }, [bookId, numericSectionIndex, activePosition])

  if (loadingState === 'loading') {
    return <LoadingState title="正在打开这一节..." />
  }

  if (loadingState === 'processing') {
    return (
      <LoadingState
        title="正在为你准备这一节的阅读体验..."
        description="通常只需要几秒钟，完成后会自动显示。"
      />
    )
  }

  if (loadingState === 'error') {
    return (
      <main className="reader-wrap">
        <Link to={`/book/${bookId}`} className="mb-5 inline-flex text-sm font-semibold text-primary">
          ← 返回总览
        </Link>
        <section className="panel p-6 text-center">
          <div className="mb-3 text-4xl">⚠️</div>
          <h1 className="text-xl font-semibold text-ink">这一节处理失败了</h1>
          <p className="mt-2 text-sm leading-6 text-muted">{error}</p>
          <button type="button" className="btn-primary mt-5" onClick={() => loadSection(true)}>
            重试
          </button>
        </section>
      </main>
    )
  }

  const progressValue =
    section?.total_sections > 0 ? ((section.section_index + 1) / section.total_sections) * 100 : 0

  return (
    <main className="reader-wrap">
      <header className="sticky top-0 z-20 -mx-4 mb-5 border-b border-black/5 bg-paper/95 px-4 py-3 backdrop-blur sm:-mx-6 sm:px-6">
        <div className="mb-3 flex items-center justify-between gap-3">
          <Link to={`/book/${bookId}`} className="text-sm font-semibold text-primary hover:underline">
            ← {section.chapter_title}
          </Link>
          <span className="text-sm text-muted">
            {section.section_index + 1}/{section.total_sections}
          </span>
        </div>
        <ProgressBar value={progressValue} compact label={`第 ${section.section_index + 1} 节`} />
      </header>

      <div className="space-y-4">
        {cards.map((item) => (
          <div
            key={item.key}
            data-reader-card="true"
            data-position={item.position}
            className="scroll-mt-28"
          >
            {item.node}
          </div>
        ))}
      </div>
    </main>
  )
}
