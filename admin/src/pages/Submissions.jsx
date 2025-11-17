import React, { useState, useEffect } from 'react'
import { getSubmissions, getSubmission } from '../services/api'
import './Submissions.css'

function Submissions() {
  const [submissions, setSubmissions] = useState([])
  const [loading, setLoading] = useState(true)
  const [selectedSubmission, setSelectedSubmission] = useState(null)
  const [filter, setFilter] = useState('all')
  const [searchTerm, setSearchTerm] = useState('')
  const [currentPage, setCurrentPage] = useState(1)
  const [total, setTotal] = useState(0)
  const [limit] = useState(20)

  useEffect(() => {
    loadSubmissions()
    const interval = setInterval(loadSubmissions, 5000)
    return () => clearInterval(interval)
  }, [filter, currentPage])

  const loadSubmissions = async () => {
    try {
      const offset = (currentPage - 1) * limit
      const response = await fetch(
        `${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/submissions?limit=${limit}&offset=${offset}${filter !== 'all' ? `&status=${filter}` : ''}`
      )
      const data = await response.json()
      
      if (data.submissions) {
        setSubmissions(data.submissions)
        setTotal(data.total || 0)
      } else if (Array.isArray(data)) {
        setSubmissions(data)
        setTotal(data.length)
      } else {
        setSubmissions([])
        setTotal(0)
      }
      setLoading(false)
    } catch (error) {
      console.error('Erro ao carregar submissões:', error)
      setLoading(false)
    }
  }

  const handleViewDetails = async (jobId) => {
    const submission = await getSubmission(jobId)
    setSelectedSubmission(submission)
  }

  const filteredSubmissions = searchTerm
    ? submissions.filter(s => 
        s.url.toLowerCase().includes(searchTerm.toLowerCase()) ||
        (s.job_id && s.job_id.toLowerCase().includes(searchTerm.toLowerCase()))
      )
    : submissions

  const getLevelColor = (level) => {
    switch (level) {
      case 'alto': return '#FF3B30'
      case 'médio': return '#FF9500'
      case 'baixo': return '#34C759'
      default: return '#8E8E93'
    }
  }

  const getStatusColor = (status) => {
    switch (status) {
      case 'done': return '#34C759'
      case 'processing': return '#007AFF'
      case 'queued': return '#FF9500'
      case 'failed': return '#FF3B30'
      default: return '#8E8E93'
    }
  }

  if (loading) {
    return <div className="loading">Carregando...</div>
  }

  return (
    <div className="submissions-page">
      <div className="page-header">
        <h1>Submissões</h1>
        <div className="header-controls">
          <input
            type="text"
            placeholder="Buscar por URL ou Job ID..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="search-input"
          />
          <div className="filters">
          <button 
            className={filter === 'all' ? 'active' : ''}
            onClick={() => setFilter('all')}
          >
            Todas
          </button>
          <button 
            className={filter === 'queued' ? 'active' : ''}
            onClick={() => setFilter('queued')}
          >
            Na Fila
          </button>
          <button 
            className={filter === 'processing' ? 'active' : ''}
            onClick={() => setFilter('processing')}
          >
            Processando
          </button>
          <button 
            className={filter === 'done' ? 'active' : ''}
            onClick={() => setFilter('done')}
          >
            Concluídas
          </button>
        </div>
        </div>
      </div>

      {total > limit && (
        <div className="pagination">
          <button 
            disabled={currentPage === 1}
            onClick={() => setCurrentPage(currentPage - 1)}
          >
            Anterior
          </button>
          <span>Página {currentPage} de {Math.ceil(total / limit)}</span>
          <button 
            disabled={currentPage >= Math.ceil(total / limit)}
            onClick={() => setCurrentPage(currentPage + 1)}
          >
            Próxima
          </button>
        </div>
      )}

      <div className="submissions-list">
        {filteredSubmissions.length === 0 ? (
          <div className="empty-state">
            <p>Nenhuma submissão encontrada</p>
          </div>
        ) : (
          filteredSubmissions.map((sub) => (
            <div key={sub.id} className="submission-card">
              <div className="submission-header">
                <div className="submission-url">
                  <a href={sub.url} target="_blank" rel="noopener noreferrer">
                    {sub.url}
                  </a>
                </div>
                <div className="submission-badges">
                  <span 
                    className="status-badge"
                    style={{ backgroundColor: getStatusColor(sub.status) }}
                  >
                    {sub.status}
                  </span>
                  {sub.result && sub.result.level && (
                    <span 
                      className="risk-badge"
                      style={{ color: getLevelColor(sub.result.level) }}
                    >
                      Risco {sub.result.level}
                    </span>
                  )}
                </div>
              </div>
              
              <div className="submission-info">
                <div className="info-item">
                  <span className="info-label">ID:</span>
                  <span className="info-value">{sub.job_id}</span>
                </div>
                <div className="info-item">
                  <span className="info-label">Criado em:</span>
                  <span className="info-value">
                    {new Date(sub.created_at).toLocaleString('pt-BR')}
                  </span>
                </div>
                {sub.processed_at && (
                  <div className="info-item">
                    <span className="info-label">Processado em:</span>
                    <span className="info-value">
                      {new Date(sub.processed_at).toLocaleString('pt-BR')}
                    </span>
                  </div>
                )}
              </div>

              {sub.result && (
                <div className="submission-result">
                  <h4>Resultado da Análise</h4>
                  <div className="result-details">
                    <div className="result-item">
                      <span className="result-label">Score:</span>
                      <span className="result-value">{sub.result.score}/100</span>
                    </div>
                    {sub.result.checks && sub.result.checks.length > 0 && (
                      <div className="result-checks">
                        <strong>Sinais Detectados:</strong>
                        <ul>
                          {sub.result.checks.map((check, idx) => (
                            <li key={idx}>
                              <strong>{check.name}:</strong> {check.reason}
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                    {sub.result.tips && sub.result.tips.length > 0 && (
                      <div className="result-tips">
                        <strong>Dicas Pedagógicas:</strong>
                        <ul>
                          {sub.result.tips.map((tip, idx) => (
                            <li key={idx}>{tip}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                </div>
              )}

              <button 
                className="view-details-btn"
                onClick={() => handleViewDetails(sub.job_id)}
              >
                Ver Detalhes Completos
              </button>
            </div>
          ))
        )}
      </div>

      {selectedSubmission && (
        <div className="modal-overlay" onClick={() => setSelectedSubmission(null)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>Detalhes da Submissão</h2>
              <button onClick={() => setSelectedSubmission(null)}>✕</button>
            </div>
            <div className="modal-body">
              <pre>{JSON.stringify(selectedSubmission, null, 2)}</pre>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default Submissions

