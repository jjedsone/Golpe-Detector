import React, { useState, useEffect } from 'react'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, PieChart, Pie, Cell } from 'recharts'
import { getSubmissions, getStats } from '../services/api'
import './Stats.css'

function Stats() {
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadStats()
    const interval = setInterval(loadStats, 10000)
    return () => clearInterval(interval)
  }, [])

  const loadStats = async () => {
    try {
      const submissions = await getSubmissions()
      const statsData = await getStats()
      
      if (statsData) {
        setStats(statsData)
      } else {
        // Calcular stats localmente
        const calculated = calculateStats(submissions)
        setStats(calculated)
      }
      
      setLoading(false)
    } catch (error) {
      console.error('Erro ao carregar estatísticas:', error)
      setLoading(false)
    }
  }

  const calculateStats = (submissions) => {
    const stats = {
      byStatus: {
        queued: 0,
        processing: 0,
        done: 0,
        failed: 0,
      },
      byRisk: {
        alto: 0,
        médio: 0,
        baixo: 0,
      },
      byHour: {},
      total: submissions.length,
    }

    submissions.forEach(sub => {
      // Por status
      stats.byStatus[sub.status] = (stats.byStatus[sub.status] || 0) + 1
      
      // Por risco
      if (sub.result && sub.result.level) {
        stats.byRisk[sub.result.level] = (stats.byRisk[sub.result.level] || 0) + 1
      }
      
      // Por hora
      if (sub.created_at) {
        const hour = new Date(sub.created_at).getHours()
        stats.byHour[hour] = (stats.byHour[hour] || 0) + 1
      }
    })

    // Converter byHour para array
    stats.byHourArray = Object.entries(stats.byHour)
      .map(([hour, count]) => ({ hour: `${hour}h`, count }))
      .sort((a, b) => parseInt(a.hour) - parseInt(b.hour))

    return stats
  }

  const statusData = stats ? [
    { name: 'Na Fila', value: stats.byStatus.queued },
    { name: 'Processando', value: stats.byStatus.processing },
    { name: 'Concluídas', value: stats.byStatus.done },
    { name: 'Falhadas', value: stats.byStatus.failed },
  ] : []

  const riskData = stats ? [
    { name: 'Alto', value: stats.byRisk.alto },
    { name: 'Médio', value: stats.byRisk.medio || stats.byRisk.médio },
    { name: 'Baixo', value: stats.byRisk.baixo },
  ] : []

  const COLORS = ['#FF3B30', '#FF9500', '#34C759', '#007AFF']
  const RISK_COLORS = ['#FF3B30', '#FF9500', '#34C759']

  if (loading) {
    return <div className="loading">Carregando estatísticas...</div>
  }

  if (!stats) {
    return <div className="error">Erro ao carregar estatísticas</div>
  }

  return (
    <div className="stats-page">
      <h1>Estatísticas</h1>

      <div className="stats-overview">
        <div className="stat-box">
          <h3>Total de Análises</h3>
          <p className="stat-number">{stats.total}</p>
        </div>
        <div className="stat-box">
          <h3>Concluídas</h3>
          <p className="stat-number">{stats.byStatus.done}</p>
        </div>
        <div className="stat-box">
          <h3>Em Processamento</h3>
          <p className="stat-number">{stats.byStatus.processing}</p>
        </div>
        <div className="stat-box">
          <h3>Na Fila</h3>
          <p className="stat-number">{stats.byStatus.queued}</p>
        </div>
      </div>

      <div className="charts-grid">
        <div className="chart-card">
          <h2>Distribuição por Status</h2>
          <PieChart width={400} height={300}>
            <Pie
              data={statusData}
              cx={200}
              cy={150}
              labelLine={false}
              label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
              outerRadius={80}
              fill="#8884d8"
              dataKey="value"
            >
              {statusData.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
              ))}
            </Pie>
            <Tooltip />
          </PieChart>
        </div>

        <div className="chart-card">
          <h2>Distribuição por Risco</h2>
          <PieChart width={400} height={300}>
            <Pie
              data={riskData}
              cx={200}
              cy={150}
              labelLine={false}
              label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
              outerRadius={80}
              fill="#8884d8"
              dataKey="value"
            >
              {riskData.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={RISK_COLORS[index % RISK_COLORS.length]} />
              ))}
            </Pie>
            <Tooltip />
          </PieChart>
        </div>
      </div>

      {stats.byHourArray && stats.byHourArray.length > 0 && (
        <div className="chart-card">
          <h2>Análises por Hora do Dia</h2>
          <BarChart width={800} height={300} data={stats.byHourArray}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="hour" />
            <YAxis />
            <Tooltip />
            <Legend />
            <Bar dataKey="count" fill="#1e40af" />
          </BarChart>
        </div>
      )}
    </div>
  )
}

export default Stats

