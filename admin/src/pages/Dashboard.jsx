import React, { useState, useEffect } from 'react'
import { getSubmissions, getStats } from '../services/api'
import './Dashboard.css'

function Dashboard() {
  const [stats, setStats] = useState({
    total: 0,
    queued: 0,
    processing: 0,
    done: 0,
    failed: 0,
    alto: 0,
    medio: 0,
    baixo: 0,
  })
  const [recentSubmissions, setRecentSubmissions] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadData()
    const interval = setInterval(loadData, 5000) // Atualizar a cada 5 segundos
    return () => clearInterval(interval)
  }, [])

  const loadData = async () => {
    try {
      const submissions = await getSubmissions()
      const statsData = await getStats()
      
      if (statsData) {
        setStats(statsData)
      } else {
        // Calcular stats localmente se API não retornar
        const calculated = calculateStats(submissions)
        setStats(calculated)
      }
      
      setRecentSubmissions(submissions.slice(0, 10))
      setLoading(false)
    } catch (error) {
      console.error('Erro ao carregar dados:', error)
      setLoading(false)
    }
  }

  const calculateStats = (submissions) => {
    const stats = {
      total: submissions.length,
      queued: 0,
      processing: 0,
      done: 0,
      failed: 0,
      alto: 0,
      medio: 0,
      baixo: 0,
    }

    submissions.forEach(sub => {
      stats[sub.status] = (stats[sub.status] || 0) + 1
      
      if (sub.result && sub.result.level) {
        stats[sub.result.level] = (stats[sub.result.level] || 0) + 1
      }
    })

    return stats
  }

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
    <div className="dashboard">
      <h1>Dashboard</h1>
      
      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-icon">📊</div>
          <div className="stat-info">
            <h3>Total de Análises</h3>
            <p className="stat-value">{stats.total}</p>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon">✅</div>
          <div className="stat-info">
            <h3>Concluídas</h3>
            <p className="stat-value" style={{ color: getStatusColor('done') }}>
              {stats.done}
            </p>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon">⏳</div>
          <div className="stat-info">
            <h3>Em Processamento</h3>
            <p className="stat-value" style={{ color: getStatusColor('processing') }}>
              {stats.processing}
            </p>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon">⏰</div>
          <div className="stat-info">
            <h3>Na Fila</h3>
            <p className="stat-value" style={{ color: getStatusColor('queued') }}>
              {stats.queued}
            </p>
          </div>
        </div>
      </div>

      <div className="risk-grid">
        <h2>Distribuição de Risco</h2>
        <div className="risk-cards">
          <div className="risk-card" style={{ borderLeft: `4px solid ${getLevelColor('alto')}` }}>
            <h3>🔴 Risco Alto</h3>
            <p className="risk-value">{stats.alto}</p>
          </div>
          <div className="risk-card" style={{ borderLeft: `4px solid ${getLevelColor('médio')}` }}>
            <h3>🟠 Risco Médio</h3>
            <p className="risk-value">{stats.medio}</p>
          </div>
          <div className="risk-card" style={{ borderLeft: `4px solid ${getLevelColor('baixo')}` }}>
            <h3>🟢 Risco Baixo</h3>
            <p className="risk-value">{stats.baixo}</p>
          </div>
        </div>
      </div>

      <div className="recent-submissions">
        <h2>Submissões Recentes</h2>
        <table className="submissions-table">
          <thead>
            <tr>
              <th>URL</th>
              <th>Status</th>
              <th>Nível de Risco</th>
              <th>Data</th>
            </tr>
          </thead>
          <tbody>
            {recentSubmissions.length === 0 ? (
              <tr>
                <td colSpan="4" style={{ textAlign: 'center', padding: '20px' }}>
                  Nenhuma submissão encontrada
                </td>
              </tr>
            ) : (
              recentSubmissions.map((sub) => (
                <tr key={sub.id}>
                  <td>
                    <a href={sub.url} target="_blank" rel="noopener noreferrer">
                      {sub.url.length > 50 ? `${sub.url.substring(0, 50)}...` : sub.url}
                    </a>
                  </td>
                  <td>
                    <span 
                      className="status-badge"
                      style={{ backgroundColor: getStatusColor(sub.status) }}
                    >
                      {sub.status}
                    </span>
                  </td>
                  <td>
                    {sub.result && sub.result.level ? (
                      <span 
                        className="risk-badge"
                        style={{ color: getLevelColor(sub.result.level) }}
                      >
                        {sub.result.level}
                      </span>
                    ) : (
                      <span>-</span>
                    )}
                  </td>
                  <td>
                    {new Date(sub.created_at).toLocaleString('pt-BR')}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}

export default Dashboard

