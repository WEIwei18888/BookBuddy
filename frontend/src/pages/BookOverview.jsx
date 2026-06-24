import { useEffect, useMemo, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import LoadingState from '../components/LoadingState.jsx'
import ProgressBar from '../components/ProgressBar.jsx'
import { extractErrorMessage, getBook } from '../api/client.js'
import { useStore } from '../stores/useStore.js'

export default function BookOverview() {
  const { bookId } = useParams()
  const navigate = useNavigate()
  const [book, setBook] = useState(null)
  const [loading, setLoading] = useState(true)
  const [openChapters, setOpenChapters] = useState({})
  const setToast = useStore((state) => state.setToast)

  const refresh = async () => {
    try {
      const data = await getBook(bookId)
      setBook(data)
      setOpenChapters((current) => {
        if (Object.keys(current).length) return current
        const first = data.chapters?.[0]?.id
        return first ? { [first]: true } : {}
      })
    } catch (error) {
      setToast(extractErrorMessage(error, '书籍加载失败'), 'error')
      navigate('/')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    refresh()
  }, [bookId])

  useEffect(() => {
    if (!book || book.status !== 'processing') return undefined
    const timer = window.setInterval(refresh, 3000)
    return () => window.clearInterval(timer)
  }, [book?.status, bookId])

  const progressValue = useMemo(() => {
    if (!book?.total_sections) return 0
    return (book.read_sections / book.total_sections) * 100
  }, [book])

  const continueSection = useMemo(() => {
    if (!book) return 0
    const current = book.progress?.current_section_index || 0
    const position = book.progress?.current_position || 'start'
    const next = position === 'complete' ? current + 1 : current
    return Math.max(0, Math.min(book.total_sections - 1, next))
  }, [book])

  if (loading || !book) {
    return <LoadingState title="正在读取书籍..." />
  }

  return (
    <main className="page-wrap max-w-4xl">
      <Link to="/" className="mb-5 inline-flex text-sm font-semibold text-primary hover:underline">
        ← 返回书架
      </Link>

      <section className="panel p-6 sm:p-8">
        <div className="flex flex-col gap-5 sm:flex-row sm:items-start">
          <div className="flex h-20 w-20 shrink-0 items-center justify-center rounded-lg bg-soft text-5xl">
            {book.cover_emoji || '📖'}
          </div>
          <div className="min-w-0 flex-1">
            <div className="mb-2 flex flex-wrap items-center gap-2">
              <h1 className="text-2xl font-semibold leading-8 text-ink">{book.title}</h1>
              <Status status={book.status} />
            </div>
            {book.author ? <p className="text-sm text-muted">{book.author}</p> : null}
            {book.description ? (
              <p className="mt-4 max-w-2xl text-base leading-7 text-muted">{book.description}</p>
            ) : null}

            <div className="mt-6 max-w-xl">
              <ProgressBar
                value={progressValue}
                label={`${book.read_sections}/${book.total_sections || 0} 节`}
              />
            </div>

            {book.status === 'ready' ? (
              <button
                type="button"
                className="btn-primary mt-6"
                onClick={() => navigate(`/book/${book.id}/read/${continueSection}`)}
              >
                继续阅读
              </button>
            ) : book.status === 'processing' ? (
              <div className="mt-6 rounded-md bg-[#FFF9F0] px-4 py-3 text-sm text-[#8A5B00]">
                正在解析书籍，完成前 3 节后就可以开始阅读。
              </div>
            ) : (
              <div className="mt-6 rounded-md bg-[#FFF5F5] px-4 py-3 text-sm text-danger">
                {book.error_message || '书籍处理失败'}
              </div>
            )}
          </div>
        </div>
      </section>

      <section className="mt-6">
        <h2 className="mb-3 text-lg font-semibold text-ink">章节目录</h2>
        <div className="panel divide-y divide-black/5">
          {book.chapters?.length ? (
            book.chapters.map((chapter) => {
              const open = openChapters[chapter.id]
              const done = chapter.sections.filter((section) => section.section_index < book.read_sections).length
              return (
                <div key={chapter.id}>
                  <button
                    type="button"
                    className="flex w-full items-center justify-between gap-4 px-5 py-4 text-left"
                    onClick={() =>
                      setOpenChapters((current) => ({ ...current, [chapter.id]: !open }))
                    }
                  >
                    <span className="font-semibold text-ink">
                      {open ? '▾' : '▸'} {chapter.title}
                    </span>
                    <span className="shrink-0 text-sm text-muted">
                      {done}/{chapter.section_count}
                    </span>
                  </button>
                  {open ? (
                    <div className="grid gap-2 px-5 pb-5 sm:grid-cols-2">
                      {chapter.sections.map((section) => (
                        <button
                          key={section.id}
                          type="button"
                          className="rounded-md border border-black/10 bg-white px-3 py-3 text-left text-sm transition hover:border-primary"
                          onClick={() => navigate(`/book/${book.id}/read/${section.section_index}`)}
                        >
                          <div className="flex items-center justify-between gap-3">
                            <span>第 {section.section_in_chapter + 1} 节</span>
                            <span className="text-xs text-muted">
                              {section.section_index < book.read_sections
                                ? '已读'
                                : section.status === 'ready'
                                  ? '可读'
                                  : section.status === 'processing'
                                    ? '处理中'
                                    : section.status === 'error'
                                      ? '失败'
                                      : '待生成'}
                            </span>
                          </div>
                        </button>
                      ))}
                    </div>
                  ) : null}
                </div>
              )
            })
          ) : (
            <div className="px-5 py-8 text-center text-sm text-muted">目录生成中...</div>
          )}
        </div>
      </section>
    </main>
  )
}

function Status({ status }) {
  const map = {
    ready: '可阅读',
    processing: '处理中',
    error: '失败',
  }
  return (
    <span className="rounded-full bg-soft px-2.5 py-1 text-xs font-semibold text-muted">
      {map[status] || status}
    </span>
  )
}

