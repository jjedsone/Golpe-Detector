import React from 'react'
import { Link, useLocation } from 'react-router-dom'
import './Layout.css'

function Layout({ children }) {
  const location = useLocation()

  return (
    <div className="layout">
      <nav className="sidebar">
        <div className="sidebar-header">
          <h1>🛡️ Golpe Detector</h1>
          <p>Painel Admin</p>
        </div>
        <ul className="nav-menu">
          <li>
            <Link 
              to="/" 
              className={location.pathname === '/' ? 'active' : ''}
            >
              📊 Dashboard
            </Link>
          </li>
          <li>
            <Link 
              to="/submissions" 
              className={location.pathname === '/submissions' ? 'active' : ''}
            >
              📋 Submissões
            </Link>
          </li>
          <li>
            <Link 
              to="/stats" 
              className={location.pathname === '/stats' ? 'active' : ''}
            >
              📈 Estatísticas
            </Link>
          </li>
        </ul>
      </nav>
      <main className="main-content">
        {children}
      </main>
    </div>
  )
}

export default Layout

