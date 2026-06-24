import { Link } from 'react-router-dom'
import ProgressBar from './ProgressBar.jsx'

export default function BookCard({ book, onDelete }) {
  const progress =
    book.total_sections > 0 ? (book.read_sections / book.total_sections) * 100 : 0
  const isProcessing = book.status === 'processing'
  const isError = book.status === 'error'

  return (
    <div className="panel flex min-h-[220px] flex-col p-5 transition hover:-translate-y-0.5 hover:shadow-soft">
      <Link to={`/book/${book.id}`} className="flex flex-1 flex-col">
        <div className="mb-4 flex items-start justify-between gap-3">
          <div className="flex h-16 w-16 shrink-0 items-center justify-center rounded-lg bg-soft text-4xl">
            {book.cover_emoji || '📖'}
          </div>
          <StatusBadge status={book.status} />
        </div>
        <h2 className="line-clamp-2 text-lg font-semibold leading-7 text-ink">{book.title}</h2>
        {book.author ? <p className="mt-1 text-sm text-muted">{book.author}</p> : null}
        {book.description ? (
          <p className="mt-3 line-clamp-2 text-sm leading-6 text-muted">{book.description}</p>
        ) : null}
        <div className="mt-auto pt-5">
          {isProcessing ? (
            <div className="rounded-md bg-[#FFF9F0] px-3 py-2 text-sm text-[#8A5B00]">
              正在解析书籍...
            </div>
          ) : isError ? (
            <div className="rounded-md bg-[#FFF5F5] px-3 py-2 text-sm text-danger">
              {book.error_message || '处理失败'}
            </div>
          ) : (
            <ProgressBar value={progress} compact label={`${book.read_sections}/${book.total_sections} 节`} />
          )}
        </div>
      </Link>
      <button
        type="button"
        onClick={(event) => {
          event.preventDefault()
          onDelete(book)
        }}
        className="mt-4 self-start text-sm font-medium text-muted hover:text-danger"
      >
        删除
      </button>
    </div>
  )
}

function StatusBadge({ status }) {
  const styles = {
    ready: 'bg-[#F0FFF4] text-success',
    processing: 'bg-[#FFF9F0] text-[#8A5B00]',
    error: 'bg-[#FFF5F5] text-danger',
  }
  const text = {
    ready: '可阅读',
    processing: '处理中',
    error: '失败',
  }
  return (
    <span className={`rounded-full px-2.5 py-1 text-xs font-semibold ${styles[status] || styles.ready}`}>
      {text[status] || '可阅读'}
    </span>
  )
}

