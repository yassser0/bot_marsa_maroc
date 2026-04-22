import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Toaster } from 'react-hot-toast';
import toast from 'react-hot-toast';
import { TooltipProvider } from './components/ui/Tooltip';
import Sidebar from './components/layout/Sidebar';
import BotList from './components/BotList';
import ChatView from './components/ChatView';
import SettingsView from './components/SettingsView';
import './index.css';

const API_BASE_URL = 'http://127.0.0.1:8001';

export default function App() {
  const [currentView, setCurrentView] = useState('list');
  const [bots, setBots] = useState([]);
  const [activeBot, setActiveBot] = useState(null);
  const [loading, setLoading] = useState(true);

  const fetchBots = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${API_BASE_URL}/bots`);
      setBots(response.data);
    } catch {
      toast.error('Impossible de récupérer les bots. Vérifiez que le backend est démarré.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchBots();
  }, []);

  const handleCreateBot = async (botData) => {
    await axios.post(`${API_BASE_URL}/bots/`, botData);
    await fetchBots();
  };

  const handleUpdateBot = async (botId, botData) => {
    await axios.put(`${API_BASE_URL}/bots/${botId}`, botData);
    await fetchBots();
  };

  const handleDeleteBot = async (botId) => {
    const toastId = toast.loading('Suppression en cours…');
    try {
      await axios.delete(`${API_BASE_URL}/bots/${botId}`);
      await fetchBots();
      toast.success('Bot supprimé avec succès.', { id: toastId });
    } catch {
      toast.error('Erreur lors de la suppression du bot.', { id: toastId });
    }
  };

  return (
    <TooltipProvider>
      <div className="app-shell">
        {/* Global toast notifications */}
        <Toaster
          position="top-right"
          toastOptions={{
            duration: 4000,
            style: {
              background: 'rgba(15, 23, 42, 0.95)',
              color: '#f8fafc',
              border: '1px solid rgba(255,255,255,0.1)',
              backdropFilter: 'blur(12px)',
              borderRadius: '12px',
              fontSize: '14px',
              padding: '12px 16px',
            },
            success: {
              iconTheme: { primary: '#10b981', secondary: '#fff' },
            },
            error: {
              iconTheme: { primary: '#ef4444', secondary: '#fff' },
            },
          }}
        />

        {/* Sidebar */}
        <Sidebar
          currentView={currentView === 'chat' ? 'list' : currentView}
          setCurrentView={(v) => {
            setActiveBot(null);
            setCurrentView(v);
          }}
          botsCount={bots.length}
        />

        {/* Main content */}
        <main className="app-main">
          {currentView === 'list' && (
            <BotList
              bots={bots}
              loading={loading}
              onSelectBot={(bot) => {
                setActiveBot(bot);
                setCurrentView('chat');
              }}
              onDeleteBot={handleDeleteBot}
              onBotCreated={handleCreateBot}
              onBotUpdated={handleUpdateBot}
            />
          )}

          {currentView === 'chat' && activeBot && (
            <ChatView
              bot={activeBot}
              onBack={() => setCurrentView('list')}
            />
          )}

          {currentView === 'settings' && <SettingsView />}
        </main>
      </div>
    </TooltipProvider>
  );
}
