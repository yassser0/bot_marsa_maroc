import React, { useState } from 'react';
import { Bot, MessageSquare, Settings, Plus, Play, Cpu, Server, X } from 'lucide-react';
import './index.css';

// BotList Component (Mock Data)
const BotList = ({ onSelectBot, onCreateNew }) => {
  const bots = [
    { id: 1, name: 'Maroc-Assistant', status: 'online', api: 'https://api.openai.com/v1', model: 'GPT-4' },
    { id: 2, name: 'Support-Client', status: 'offline', api: 'https://api.anthropic.com/v1', model: 'Claude 3' },
    { id: 3, name: 'Data-Analyzer', status: 'online', api: 'http://localhost:8000/api/custom', model: 'Custom Model' },
  ];

  return (
    <div className="animate-fade-in">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '32px' }}>
        <div>
          <h2>Mes Bots</h2>
          <p style={{ color: 'var(--text-muted)' }}>Gérez vos assistants d'intelligence artificielle</p>
        </div>
        <button className="btn-primary" onClick={onCreateNew}>
          <Plus size={18} />
          Créer un Bot
        </button>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: '24px' }}>
        {bots.map((bot) => (
          <div key={bot.id} className="glass-panel glass-card-hover" style={{ padding: '24px', cursor: 'pointer' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '16px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                <div style={{ padding: '10px', background: 'rgba(59, 130, 246, 0.2)', borderRadius: '12px', color: 'var(--accent-primary)' }}>
                  <Bot size={24} />
                </div>
                <div>
                  <h3 style={{ margin: 0, fontSize: '18px' }}>{bot.name}</h3>
                  <span style={{ fontSize: '12px', color: bot.status === 'online' ? 'var(--success)' : 'var(--danger)', display: 'flex', alignItems: 'center', gap: '4px', marginTop: '4px' }}>
                    <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: bot.status === 'online' ? 'var(--success)' : 'var(--danger)' }}></span>
                    {bot.status === 'online' ? 'En ligne' : 'Hors ligne'}
                  </span>
                </div>
              </div>
            </div>
            
            <div style={{ marginBottom: '20px', fontSize: '14px', color: 'var(--text-muted)' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
                <Server size={14} /> {bot.api}
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Cpu size={14} /> {bot.model}
              </div>
            </div>

            <div style={{ display: 'flex', gap: '12px' }}>
              <button 
                className="btn-outline" 
                style={{ flex: 1, justifyContent: 'center' }}
                onClick={() => onSelectBot(bot)}
              >
                <MessageSquare size={16} /> Tester
              </button>
              <button className="btn-outline" style={{ padding: '10px' }}>
                <Settings size={16} />
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

// Formulaire de Création de Bot
const BotForm = ({ onCancel }) => {
  return (
    <div className="animate-fade-in glass-panel" style={{ padding: '32px', maxWidth: '600px', margin: '0 auto' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
        <h2>Créer un nouveau Bot</h2>
        <button style={{ background: 'transparent', border: 'none', color: 'var(--text-muted)', cursor: 'pointer' }} onClick={onCancel}>
          <X size={24} />
        </button>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
        <div>
          <label style={{ display: 'block', marginBottom: '8px', fontSize: '14px', fontWeight: 500, color: 'var(--text-muted)' }}>Nom du bot</label>
          <input type="text" className="glass-input" placeholder="Ex: Assistant RH" />
        </div>
        
        <div>
          <label style={{ display: 'block', marginBottom: '8px', fontSize: '14px', fontWeight: 500, color: 'var(--text-muted)' }}>URL de l'API Externe</label>
          <input type="text" className="glass-input" placeholder="https://api.openai.com/v1/chat/completions" />
        </div>

        <div>
          <label style={{ display: 'block', marginBottom: '8px', fontSize: '14px', fontWeight: 500, color: 'var(--text-muted)' }}>Clé d'authentification (Bearer Token)</label>
          <input type="password" className="glass-input" placeholder="sk-..." />
        </div>

        <div>
          <label style={{ display: 'block', marginBottom: '8px', fontSize: '14px', fontWeight: 500, color: 'var(--text-muted)' }}>Prompt Système (Instruction initiale)</label>
          <textarea className="glass-input" rows="4" placeholder="Tu es un assistant utile..."></textarea>
        </div>

        <div style={{ display: 'flex', gap: '16px', marginTop: '16px' }}>
          <button className="btn-primary" style={{ flex: 1, justifyContent: 'center' }} onClick={onCancel}>Enregistrer le Bot</button>
          <button className="btn-outline" onClick={onCancel}>Annuler</button>
        </div>
      </div>
    </div>
  );
}

// Composant Principal App
function App() {
  const [currentView, setCurrentView] = useState('list'); // 'list', 'create', 'chat'
  const [activeBot, setActiveBot] = useState(null);

  const handleSelectBot = (bot) => {
    setActiveBot(bot);
    setCurrentView('chat');
  };

  return (
    <div className="app-container">
      {/* Sidebar */}
      <aside className="sidebar glass-panel" style={{ margin: '16px', borderRadius: '16px', borderLeft: '1px solid var(--border-color)' }}>
        <div style={{ padding: '24px', borderBottom: '1px solid var(--border-color)' }}>
          <h1 style={{ fontSize: '20px', display: 'flex', alignItems: 'center', gap: '12px', color: 'var(--text-main)' }}>
            <span style={{ background: 'var(--accent-primary)', padding: '8px', borderRadius: '8px', display: 'flex' }}>
              <Bot size={20} color="white" />
            </span>
            Bot Builder
          </h1>
        </div>
        <nav style={{ padding: '24px 16px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
          <button 
            className="btn-outline" 
            style={{ width: '100%', justifyContent: 'flex-start', border: currentView === 'list' ? '1px solid var(--accent-primary)' : '1px solid transparent' }}
            onClick={() => setCurrentView('list')}
          >
            <Server size={18} /> Mes Bots
          </button>
          <button 
            className="btn-outline" 
            style={{ width: '100%', justifyContent: 'flex-start' }}
          >
            <Settings size={18} /> Paramètres
          </button>
        </nav>
      </aside>

      {/* Main Content */}
      <main className="main-content">
        {currentView === 'list' && (
          <BotList 
            onSelectBot={handleSelectBot} 
            onCreateNew={() => setCurrentView('create')} 
          />
        )}
        
        {currentView === 'create' && (
          <BotForm onCancel={() => setCurrentView('list')} />
        )}

        {currentView === 'chat' && (
          <div className="animate-fade-in glass-panel" style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
            <div style={{ padding: '20px', borderBottom: '1px solid var(--border-color)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                <div style={{ padding: '8px', background: 'rgba(59, 130, 246, 0.2)', borderRadius: '50%' }}>
                  <Bot size={24} color="var(--accent-primary)" />
                </div>
                <div>
                  <h2 style={{ margin: 0, fontSize: '18px' }}>{activeBot?.name}</h2>
                  <span style={{ fontSize: '12px', color: 'var(--success)' }}>Connecté à l'API</span>
                </div>
              </div>
              <button className="btn-outline" onClick={() => setCurrentView('list')}>
                <X size={16} /> Fermer
              </button>
            </div>
            
            <div style={{ flex: 1, padding: '24px', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '16px' }}>
              <div style={{ alignSelf: 'flex-start', background: 'var(--bg-panel)', padding: '12px 16px', borderRadius: '16px 16px 16px 0', border: '1px solid var(--border-color)', maxWidth: '80%' }}>
                Bonjour ! Je suis {activeBot?.name}. Comment puis-je vous aider aujourd'hui ?
              </div>
              {/* Future messages will be listed here */}
            </div>

            <div style={{ padding: '20px', borderTop: '1px solid var(--border-color)', display: 'flex', gap: '12px' }}>
              <input 
                type="text" 
                className="glass-input" 
                placeholder="Tapez votre message ici..." 
                style={{ flex: 1 }}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') {
                    // Logic to send message
                    e.currentTarget.value = '';
                  }
                }}
              />
              <button className="btn-primary">
                Envoyer
              </button>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

export default App;
