import axios from 'axios'

export const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
})

function errorMessage(error, fallback = '请求失败') {
  const detail = error?.response?.data?.detail
  if (typeof detail === 'string') return detail
  if (detail?.message) return detail.message
  return error?.message || fallback
}

export async function listBooks() {
  const { data } = await api.get('/books')
  return data
}

export async function uploadBook(file) {
  const formData = new FormData()
  formData.append('file', file)
  const { data } = await api.post('/books/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 120000,
  })
  return data
}

export async function getBook(bookId) {
  const { data } = await api.get(`/books/${bookId}`)
  return data
}

export async function deleteBook(bookId) {
  const { data } = await api.delete(`/books/${bookId}`)
  return data
}

export async function getSection(bookId, sectionIndex, force = false) {
  const response = await api.get(`/books/${bookId}/sections/${sectionIndex}`, {
    params: force ? { force: true } : {},
    validateStatus: (status) => (status >= 200 && status < 300) || status === 202,
    timeout: 120000,
  })
  return { statusCode: response.status, data: response.data }
}

export async function getSectionStatus(bookId, sectionIndex) {
  const { data } = await api.get(`/books/${bookId}/sections/${sectionIndex}/status`)
  return data
}

export async function getProgress(bookId) {
  const { data } = await api.get(`/progress/${bookId}`)
  return data
}

export async function updateProgress(bookId, sectionIndex, position) {
  const { data } = await api.put(`/progress/${bookId}`, {
    section_index: sectionIndex,
    position,
  })
  return data
}

export async function submitQuiz(sectionId, quizType, questionIndex, userAnswer) {
  const { data } = await api.post('/quiz/submit', {
    section_id: sectionId,
    quiz_type: quizType,
    question_index: questionIndex,
    user_answer: userAnswer,
  })
  return data
}

export function extractErrorMessage(error, fallback) {
  return errorMessage(error, fallback)
}
