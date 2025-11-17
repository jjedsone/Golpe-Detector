import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

export const getSubmissions = async (limit = 100, offset = 0, status = null) => {
  try {
    const params = { limit, offset }
    if (status) params.status = status
    const response = await api.get('/submissions', { params })
    return response.data.submissions || response.data || []
  } catch (error) {
    console.error('Erro ao buscar submissões:', error)
    return []
  }
}

export const getSubmission = async (jobId) => {
  try {
    const response = await api.get(`/submission/${jobId}`)
    return response.data
  } catch (error) {
    console.error('Erro ao buscar submissão:', error)
    return null
  }
}

export const getStats = async () => {
  try {
    const response = await api.get('/stats')
    return response.data
  } catch (error) {
    console.error('Erro ao buscar estatísticas:', error)
    return null
  }
}

export default api

