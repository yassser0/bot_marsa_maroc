import React, { useState } from 'react';
import { Server, Cpu, CheckCircle2, Link, Database, ShieldCheck, RefreshCw } from 'lucide-react';
import axios from 'axios';
import toast from 'react-hot-toast';
import { Button } from './ui/Button';
import { Badge } from './ui/Badge';

const API_BASE_URL = 'http://127.0.0.1:8000';

function StatCard({ icon: Icon, label, value, valueColor }) {
  return (
    <div className="stat-card glass-panel">
      <div className="stat-card-icon">
        <Icon size={18} />
      </div>
      <div className="stat-card-content">
        <span className="stat-card-label">{label}</span>
        <span className="stat-card-value" style={valueColor ? { color: valueColor } : {}}>
          {value}
        </span>
      </div>
    </div>
  );
}

export default function SettingsView() {
  const [apiStatus, setApiStatus] = useState(null);
  const [checking, setChecking] = useState(false);

  const checkApiStatus = async () => {
    setChecking(true);
    try {
      await axios.get(`${API_BASE_URL}/bots`);
      setApiStatus('online');
      toast.success('Backend API est en ligne !');
    } catch {
      setApiStatus('offline');
      toast.error('Impossible de joindre le backend API.');
    } finally {
      setChecking(false);
    }
  };

  return (
    <div className="animate-fade-in page-section">
      {/* Page Header */}
      <div className="page-header">
        <div>
          <h2 className="page-title">Paramètres</h2>
          <p className="page-subtitle">Configuration et état de la plateforme.</p>
        </div>
      </div>

      {/* Stats row */}
      <div className="settings-stats-grid">
        <StatCard icon={Cpu} label="Version Frontend" value="1.2.0-stable" />
        <StatCard icon={Database} label="Base de données" value="MongoDB" valueColor="var(--success)" />
        <StatCard icon={ShieldCheck} label="Authentification" value="JWT Bearer" />
        <StatCard
          icon={Server}
          label="API Backend"
          value={
            apiStatus === 'online' ? 'En ligne' : apiStatus === 'offline' ? 'Hors ligne' : 'Inconnu'
          }
          valueColor={
            apiStatus === 'online'
              ? 'var(--success)'
              : apiStatus === 'offline'
              ? 'var(--danger)'
              : 'var(--text-muted)'
          }
        />
      </div>

      {/* Backend config */}
      <div className="settings-section glass-panel">
        <div className="settings-section-header">
          <div className="settings-section-icon">
            <Server size={18} />
          </div>
          <div>
            <h3>Configuration Backend</h3>
            <p className="settings-section-desc">URL de l'API et connectivité</p>
          </div>
        </div>

        <div className="settings-field-group">
          <label className="input-label">URL de l'API de base</label>
          <div className="settings-url-row">
            <div className="input-icon-wrapper" style={{ flex: 1 }}>
              <Link size={14} className="input-icon" />
              <input
                type="text"
                className="glass-input input-with-icon"
                value={API_BASE_URL}
                readOnly
                style={{ opacity: 0.7, cursor: 'not-allowed' }}
              />
            </div>
            <Button variant="outline" size="sm" onClick={checkApiStatus} disabled={checking}>
              {checking ? <RefreshCw size={15} className="animate-spin" /> : <RefreshCw size={15} />}
              Tester
            </Button>
          </div>
          <span className="input-hint">
            Géré par les variables d'environnement. Configurez VITE_API_URL pour modifier.
          </span>
          {apiStatus && (
            <Badge variant={apiStatus === 'online' ? 'success' : 'danger'} style={{ marginTop: '8px' }}>
              <CheckCircle2 size={12} />
              {apiStatus === 'online' ? 'Connexion réussie' : 'Connexion échouée'}
            </Badge>
          )}
        </div>
      </div>

      {/* About section */}
      <div className="settings-section glass-panel">
        <div className="settings-section-header">
          <div className="settings-section-icon">
            <Cpu size={18} />
          </div>
          <div>
            <h3>À propos de la plateforme</h3>
            <p className="settings-section-desc">Informations techniques</p>
          </div>
        </div>
        <div className="settings-about-grid">
          {[
            { label: 'Framework Frontend', value: 'React 19 + Vite' },
            { label: 'UI Components', value: 'Radix UI + Custom' },
            { label: 'State Management', value: 'React Hooks' },
            { label: 'HTTP Client', value: 'Axios' },
            { label: 'Backend', value: 'FastAPI (Python)' },
            { label: 'Base de données', value: 'MongoDB Atlas' },
          ].map(({ label, value }) => (
            <div key={label} className="settings-about-item">
              <span className="settings-about-label">{label}</span>
              <span className="settings-about-value">{value}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
