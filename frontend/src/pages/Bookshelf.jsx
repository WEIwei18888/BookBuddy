import { useEffect, useMemo, useState } from 'react'
import BookCard from '../components/BookCard.jsx'
import LoadingState from '../components/LoadingState.jsx'
import UploadArea from '../components/UploadArea.jsx'
import { deleteBook, extractErrorMessage, listBooks, uploadBook } from '../api/client.js'
import { useStore } from '../stores/useStore.js'

export default function Bookshelf() {
  const [books, setBooks] = useState([])
  const [loading, setLoading] = useState(true)
  const [uploading, setUploading] = useState(false)
  const setToast = useStore((state) => state.setToast)

  const hasProcessing = useMemo(
    () => books.some((book) => book.status === 'processing'),
    [books],
  )

  const refresh = async () => {
    try {
      const data = await listBooks()
      setBooks(data)
    } catch (error) {
      setToast(extractErrorMessage(error, '书架加载失败'), 'error')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    refresh()
  }, [])

  useEffect(() => {
    if (!hasProcessing) return undefined
    const timer = window.setInterval(refresh, 3000)
    return () => window.clearInterval(timer)
  }, [hasProcessing])

  const handleUpload = async (file) => {
    if (!file.name.toLowerCase().endsWith('.pdf')) {
      setToast('请选择 PDF 文件', 'error')
      return
    }
    setUploading(true)
    try {
      await uploadBook(file)
      setToast('已开始解析书籍')
      await refresh()
    } catch (error) {
      setToast(extractErrorMessage(error, '上传失败'), 'error')
    } finally {
      setUploading(false)
    }
  }

  const handleDelete = async (book) => {
    const ok = window.confirm(`删除《${book.title}》？这会同时删除阅读进度。`)
    if (!ok) return
    try {
      await deleteBook(book.id)
      setBooks((current) => current.filter((item) => item.id !== book.id))
      setToast('已删除书籍')
    } catch (error) {
      setToast(extractErrorMessage(error, '删除失败'), 'error')
    }
  }

  if (loading) {
    return <LoadingState title="正在打开书架..." />
  }

  return (
    <main className="page-wrap">
      <header className="mb-8 flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <div className="mb-2 flex items-center gap-3">
            <div className="flex h-11 w-11 items-center justify-center rounded-lg bg-primary text-2xl text-white">
              📚
            </div>
            <h1 className="text-2xl font-semibold tracking-normal text-ink">读伴 BookBuddy</h1>
          </div>
          <p className="text-sm leading-6 text-muted">
            上传一本 PDF，把它变成有节奏、有互动、记得住的阅读旅程。
          </p>
        </div>
      </header>

      {books.length === 0 ? (
        <section className="grid gap-5 lg:grid-cols-[1fr_320px]">
          <div className="panel flex min-h-[260px] items-center justify-center p-8 text-center">
            <div>
              <div className="mb-4 text-5xl">📖</div>
              <h2 className="text-xl font-semibold text-ink">上传你的第一本书</h2>
              <p className="mt-2 max-w-md text-sm leading-6 text-muted">
                当前使用 Mock AI 模式也能完整跑通阅读流程；切换 DeepSeek 后会生成真实内容。
              </p>
            </div>
          </div>
          <UploadArea onUpload={handleUpload} disabled={uploading} />
        </section>
      ) : (
        <section className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
          {books.map((book) => (
            <BookCard key={book.id} book={book} onDelete={handleDelete} />
          ))}
          <UploadArea onUpload={handleUpload} disabled={uploading} />
        </section>
      )}
    </main>
  )
}

