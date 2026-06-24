import { BrowserRouter, Route, Routes } from 'react-router-dom'
import Bookshelf from './pages/Bookshelf.jsx'
import BookOverview from './pages/BookOverview.jsx'
import Reader from './pages/Reader.jsx'
import { useStore } from './stores/useStore.js'

function Toast() {
  const toast = useStore((state) => state.toast)
  const clearToast = useStore((state) => state.clearToast)

  if (!toast) return null

  return (
    <button
      type="button"
      onClick={clearToast}
      className={`fixed bottom-5 left-1/2 z-50 max-w-[92vw] -translate-x-1/2 rounded-md px-4 py-3 text-sm font-medium shadow-soft ${
        toast.type === 'error' ? 'bg-danger text-white' : 'bg-primary text-white'
      }`}
    >
      {toast.message}
    </button>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <div className="app-shell">
        <Routes>
          <Route path="/" element={<Bookshelf />} />
          <Route path="/book/:bookId" element={<BookOverview />} />
          <Route path="/book/:bookId/read/:sectionIndex" element={<Reader />} />
          <Route path="*" element={<Bookshelf />} />
        </Routes>
        <Toast />
      </div>
    </BrowserRouter>
  )
}

