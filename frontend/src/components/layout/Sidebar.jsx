import React from 'react';
import { Bot, Server, Settings, Zap, ChevronRight } from 'lucide-react';
import { cn } from '../../lib/utils';

const navItems = [
  { id: 'list', label: 'Mes Bots', icon: Server, description: 'Gérez vos assistants' },
  { id: 'settings', label: 'Paramètres', icon: Settings, description: 'Configuration système' },
];

export default function Sidebar({ currentView, setCurrentView, botsCount = 0 }) {
  return (
    <aside className="sidebar">
      {/* Logo & Branding */}
      <div className="sidebar-brand">
        <div className="sidebar-logo">
          <Bot size={22} color="white" />
        </div>
        <div className="sidebar-brand-text">
          <span className="sidebar-brand-name">BotBuilder</span>
          <span className="sidebar-brand-sub">Marsa Maroc Platform</span>
        </div>
      </div>

      {/* Status pill */}
      <div className="sidebar-status-pill">
        <Zap size={12} className="sidebar-status-icon" />
        <span>Système opérationnel</span>
      </div>

      {/* Navigation */}
      <nav className="sidebar-nav">
        <span className="sidebar-nav-label">Navigation</span>
        {navItems.map(({ id, label, icon: Icon, description }) => (
          <button
            key={id}
            className={cn('sidebar-nav-item', currentView === id && 'sidebar-nav-item--active')}
            onClick={() => setCurrentView(id)}
          >
            <div className="sidebar-nav-icon">
              <Icon size={18} />
            </div>
            <div className="sidebar-nav-text">
              <span className="sidebar-nav-item-label">{label}</span>
              <span className="sidebar-nav-item-desc">{description}</span>
            </div>
            {currentView === id && <ChevronRight size={14} className="sidebar-nav-chevron" />}
          </button>
        ))}
      </nav>

      {/* Footer stats */}
      <div className="sidebar-footer">
        <div className="sidebar-stat">
          <span className="sidebar-stat-value">{botsCount}</span>
          <span className="sidebar-stat-label">Bots actifs</span>
        </div>
        <div className="sidebar-stat-divider" />
        <div className="sidebar-stat">
          <span className="sidebar-stat-value" style={{ color: 'var(--success)' }}>Online</span>
          <span className="sidebar-stat-label">API Status</span>
        </div>
      </div>
    </aside>
  );
}
