import React, { useState, useEffect } from 'react';
import { Bot, MessageSquare, Settings, Plus, Play, Cpu, Server, X, Send, Loader2, Trash2 } from 'lucide-react';
import axios from 'axios';
import './index.css';

const API_BASE_URL = 'http://127.0.0.1:8000';

// BotList Component
const BotList = ({ bots, onSelectBot, onCreateNew, loading, onDeleteBot }) => {
  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '200px' }}>
        <Loader2 className="animate-spin" size={32} color="var(--accent-primary)" />
      </div>
    );
  }

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
        {bots.length === 0 ? (
          <div className="glass-panel" style={{ padding: '40px', textAlign: 'center', gridColumn: '1 / -1' }}>
            <p style={{ color: 'var(--text-muted)' }}>Vous n'avez pas encore de bot. Créez-en un pour commencer !</p>
          </div>
        ) : (
          bots.map((bot) => (
            <div key={bot.id} className="glass-panel glass-card-hover" style={{ padding: '24px', cursor: 'pointer' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '16px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                  <div style={{ padding: '10px', background: 'rgba(59, 130, 246, 0.2)', borderRadius: '12px', color: 'var(--accent-primary)' }}>
                    <Bot size={24} />
                  </div>
                  <div>
                    <h3 style={{ margin: 0, fontSize: '18px' }}>{bot.name}</h3>
                    <span style={{ fontSize: '12px', color: 'var(--success)', display: 'flex', alignItems: 'center', gap: '4px', marginTop: '4px' }}>
                      <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: 'var(--success)' }}></span>
                      Prêt
                    </span>
                  </div>
                </div>
              </div>
              
              <div style={{ marginBottom: '20px', fontSize: '14px', color: 'var(--text-muted)' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                  <Server size={14} /> {bot.url}
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <Cpu size={14} /> {bot.prompt ? (bot.prompt.substring(0, 30) + '...') : 'Pas d\'instruction'}
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
                <button 
                  className="btn-outline" 
                  style={{ padding: '10px', color: 'var(--danger)', borderColor: 'rgba(239, 68, 68, 0.2)' }}
                  onClick={(e) => {
                    e.stopPropagation();
                    if(confirm("Voulez-vous vraiment supprimer ce bot ?")) {
                      onDeleteBot(bot.id);
                    }
                  }}
                >
                  <Trash2 size={16} />
                </button>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};

// Formulaire de Création de Bot
const BotForm = ({ onCancel, onSave }) => {
  const [formData, setFormData] = useState({
    name: '',
    url: 'https://api.groq.com/openai/v1/chat/completions',
    api_key: '',
    model_name: 'llama-3.1-8b-instant',
    prompt: ''
  });
  const [loading, setLoading] = useState(false);

  const handleSubmit = async () => {
    if (!formData.name || !formData.url) return;
    setLoading(true);
    try {
      await onSave(formData);
    } finally {
      setLoading(false);
    }
  };

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
          <input 
            type="text" 
            className="glass-input" 
            placeholder="Ex: Assistant RH" 
            value={formData.name}
            onChange={(e) => setFormData({...formData, name: e.target.value})}
          />
        </div>
        
        <div>
          <label style={{ display: 'block', marginBottom: '8px', fontSize: '14px', fontWeight: 500, color: 'var(--text-muted)' }}>URL de l'API Externe</label>
          <input 
            type="text" 
            className="glass-input" 
            placeholder="https://api.openai.com/v1/chat/completions" 
            value={formData.url}
            onChange={(e) => setFormData({...formData, url: e.target.value})}
          />
          <span style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '4px', display: 'block' }}>Utilisez 'mock_api' pour tester sans clé d'API.</span>
        </div>

        <div>
          <label style={{ display: 'block', marginBottom: '8px', fontSize: '14px', fontWeight: 500, color: 'var(--text-muted)' }}>Clé d'authentification (Optionnel)</label>
          <input 
            type="password" 
            className="glass-input" 
            placeholder="sk-..." 
            value={formData.api_key}
            onChange={(e) => setFormData({...formData, api_key: e.target.value})}
          />
        </div>

        <div>
          <label style={{ display: 'block', marginBottom: '8px', fontSize: '14px', fontWeight: 500, color: 'var(--text-muted)' }}>Nom du modèle (Model Name)</label>
          <input 
            type="text" 
            className="glass-input" 
            placeholder="Ex: llama3-8b-8192" 
            value={formData.model_name}
            onChange={(e) => setFormData({...formData, model_name: e.target.value})}
          />
          <span style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '4px', display: 'block' }}>Ex: llama3-8b-8192 (pour Groq), gpt-4o (pour OpenAI)...</span>
        </div>

        <div>
          <label style={{ display: 'block', marginBottom: '8px', fontSize: '14px', fontWeight: 500, color: 'var(--text-muted)' }}>Instructions (System Prompt)</label>
          <textarea 
            className="glass-input" 
            rows="4" 
            placeholder="Ex: Tu es un assistant spécialisé dans le domaine maritime..."
            value={formData.prompt}
            onChange={(e) => setFormData({...formData, prompt: e.target.value})}
          ></textarea>
        </div>

        <div style={{ display: 'flex', gap: '16px', marginTop: '16px' }}>
          <button 
            className="btn-primary" 
            style={{ flex: 1, justifyContent: 'center' }} 
            onClick={handleSubmit}
            disabled={loading}
          >
            {loading ? <Loader2 className="animate-spin" size={18} /> : 'Enregistrer le Bot'}
          </button>
          <button className="btn-outline" onClick={onCancel}>Annuler</button>
        </div>
      </div>
    </div>
  );
}

// Chat Interface
const ChatView = ({ bot, onBack }) => {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [initialLoading, setInitialLoading] = useState(true);

  // Load History from MongoDB
  useEffect(() => {
    const loadHistory = async () => {
      try {
        const response = await axios.get(`${API_BASE_URL}/bots/${bot.id}/messages`);
        if (response.data.length > 0) {
          setMessages(response.data);
        } else {
          setMessages([{ role: 'bot', content: `Bonjour ! Je suis ${bot.name}. Comment puis-je vous aider ?` }]);
        }
      } catch (error) {
        console.error("Failed to load history", error);
        setMessages([{ role: 'bot', content: "Désolé, je n'ai pas pu charger notre historique." }]);
      } finally {
        setInitialLoading(false);
      }
    };
    loadHistory();
  }, [bot.id, bot.name]);

  const sendMessage = async () => {
    if (!input.trim() || loading) return;
    
    const userMsg = { role: 'user', content: input };
    setMessages(prev => [...prev, userMsg]);
    setInput('');
    setLoading(true);

    try {
      const response = await axios.post(`${API_BASE_URL}/chat`, {
        bot_id: bot.id,
        message: input
      });
      
      const botMsg = { role: 'bot', content: response.data.reply };
      setMessages(prev => [...prev, botMsg]);
    } catch (error) {
      setMessages(prev => [...prev, { role: 'bot', content: "Désolé, j'ai rencontré une erreur lors de la communication avec mon cerveau API." }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="animate-fade-in glass-panel" style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <div style={{ padding: '20px', borderBottom: '1px solid var(--border-color)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div style={{ padding: '8px', background: 'rgba(59, 130, 246, 0.2)', borderRadius: '50%' }}>
            <Bot size={24} color="var(--accent-primary)" />
          </div>
          <div>
            <h2 style={{ margin: 0, fontSize: '18px' }}>{bot.name}</h2>
            <span style={{ fontSize: '12px', color: 'var(--success)' }}>Connecté à {bot.url}</span>
          </div>
        </div>
        <button className="btn-outline" onClick={onBack}>
          <X size={16} /> Fermer
        </button>
      </div>
      
      <div style={{ flex: 1, padding: '24px', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '16px' }}>
        {initialLoading ? (
            <div style={{ display: 'flex', justifyContent: 'center', padding: '40px' }}>
              <Loader2 className="animate-spin" size={32} color="var(--accent-primary)" />
            </div>
          ) : (
            <>
              {messages.map((msg, i) => (
                <div 
                  key={i} 
                  className="animate-fade-in"
                  style={{ 
                    alignSelf: msg.role === 'user' ? 'flex-end' : 'flex-start',
                    background: msg.role === 'user' ? 'var(--accent-primary)' : 'var(--bg-panel)',
                    padding: '12px 16px',
                    borderRadius: msg.role === 'user' ? '16px 16px 0 16px' : '16px 16px 16px 0',
                    border: '1px solid var(--border-color)',
                    maxWidth: '80%',
                    fontSize: '15px',
                    color: msg.role === 'user' ? 'white' : 'inherit'
                  }}
                >
                  {msg.content}
                </div>
              ))}
            </>
        )}
        {loading && (
          <div style={{ alignSelf: 'flex-start', background: 'var(--bg-panel)', padding: '12px 16px', borderRadius: '16px 16px 16px 0', border: '1px solid var(--border-color)' }}>
            <Loader2 className="animate-spin" size={18} />
          </div>
        )}
        <div ref={(el) => el && el.scrollIntoView({ behavior: 'smooth' })}></div>
      </div>

      <div style={{ padding: '20px', borderTop: '1px solid var(--border-color)', display: 'flex', gap: '12px' }}>
        <input 
          type="text" 
          className="glass-input" 
          placeholder="Tapez votre message..." 
          style={{ flex: 1 }}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && sendMessage()}
        />
        <button className="btn-primary" onClick={sendMessage} disabled={loading}>
          <Send size={18} />
        </button>
      </div>
    </div>
  );
};

// Settings View Component
const SettingsView = () => {
  return (
    <div className="animate-fade-in">
      <div style={{ marginBottom: '32px' }}>
        <h2>Paramètres du Système</h2>
        <p style={{ color: 'var(--text-muted)' }}>Configurez les options globales de votre plateforme de bots.</p>
      </div>

      <div className="glass-panel" style={{ padding: '32px', display: 'flex', flexDirection: 'column', gap: '24px' }}>
        <section>
          <h3 style={{ marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Server size={18} color="var(--accent-primary)" /> Configuration Backend
          </h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            <label style={{ fontSize: '14px', color: 'var(--text-muted)' }}>URL de l'API de base</label>
            <input 
              type="text" 
              className="glass-input" 
              value="http://127.0.0.1:8000" 
              readOnly 
              style={{ opacity: 0.7, cursor: 'not-allowed' }}
            />
            <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>L'URL est actuellement gérée par les variables d'environnement.</span>
          </div>
        </section>

        <section style={{ borderTop: '1px solid var(--border-color)', paddingTop: '24px' }}>
          <h3 style={{ marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Cpu size={18} color="var(--accent-primary)" /> État du Système
          </h3>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
            <div className="glass-panel" style={{ padding: '16px', background: 'rgba(255,255,255,0.02)' }}>
              <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Version Frontend</span>
              <p style={{ margin: '4px 0 0 0', fontWeight: 'bold' }}>1.2.0-stable</p>
            </div>
            <div className="glass-panel" style={{ padding: '16px', background: 'rgba(255,255,255,0.02)' }}>
              <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Mode de Données</span>
              <p style={{ margin: '4px 0 0 0', fontWeight: 'bold', color: 'var(--success)' }}>MongoDB Connected</p>
            </div>
          </div>
        </section>
      </div>
    </div>
  );
};

// Main App Component
function App() {
  const [currentView, setCurrentView] = useState('list');
  const [bots, setBots] = useState([]);
  const [activeBot, setActiveBot] = useState(null);
  const [loading, setLoading] = useState(true);

  const fetchBots = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${API_BASE_URL}/bots`);
      setBots(response.data);
    } catch (error) {
      console.error("Erreur lors de la récupération des bots", error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchBots();
  }, []);

  const handleCreateBot = async (botData) => {
    try {
      await axios.post(`${API_BASE_URL}/bots/`, botData);
      await fetchBots();
      setCurrentView('list');
    } catch (error) {
      alert("Erreur lors de l'enregistrement du bot.");
    }
  };

  const handleDeleteBot = async (botId) => {
    try {
      await axios.delete(`${API_BASE_URL}/bots/${botId}`);
      await fetchBots();
    } catch (error) {
      alert("Erreur lors de la suppression du bot.");
    }
  };

  return (
    <div className="app-container">
      <aside className="sidebar glass-panel" style={{ margin: '16px', borderRadius: '16px' }}>
        <div style={{ padding: '24px', borderBottom: '1px solid var(--border-color)' }}>
          <h1 style={{ fontSize: '20px', display: 'flex', alignItems: 'center', gap: '12px' }}>
            <span style={{ background: 'var(--accent-primary)', padding: '8px', borderRadius: '8px', display: 'flex' }}>
              <Bot size={20} color="white" />
            </span>
            Bot Builder
          </h1>
        </div>
        <nav style={{ padding: '24px 16px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
          <button 
            className="btn-outline" 
            style={{ 
              width: '100%', 
              justifyContent: 'flex-start', 
              borderColor: currentView === 'list' ? 'var(--accent-primary)' : 'transparent',
              background: currentView === 'list' ? 'rgba(59, 130, 246, 0.1)' : 'transparent'
            }}
            onClick={() => setCurrentView('list')}
          >
            <Server size={18} /> Mes Bots
          </button>
          <button 
            className="btn-outline" 
            style={{ 
              width: '100%', 
              justifyContent: 'flex-start',
              borderColor: currentView === 'settings' ? 'var(--accent-primary)' : 'transparent',
              background: currentView === 'settings' ? 'rgba(59, 130, 246, 0.1)' : 'transparent'
            }}
            onClick={() => setCurrentView('settings')}
          >
            <Settings size={18} /> Paramètres
          </button>
        </nav>
      </aside>

      <main className="main-content">
        {currentView === 'list' && (
          <BotList 
            bots={bots} 
            loading={loading}
            onSelectBot={(bot) => { setActiveBot(bot); setCurrentView('chat'); }} 
            onCreateNew={() => setCurrentView('create')} 
            onDeleteBot={handleDeleteBot}
          />
        )}
        
        {currentView === 'create' && (
          <BotForm 
            onCancel={() => setCurrentView('list')} 
            onSave={handleCreateBot}
          />
        )}

        {currentView === 'chat' && activeBot && (
          <ChatView 
            bot={activeBot} 
            onBack={() => setCurrentView('list')} 
          />
        )}

        {currentView === 'settings' && (
          <SettingsView />
        )}
      </main>
    </div>
  );
}

export default App;
