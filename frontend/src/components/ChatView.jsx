import React, { useState, useEffect, useRef } from 'react';
import { Bot, X, Trash2, Send, Loader2, ArrowLeft, Clock, RotateCcw } from 'lucide-react';
import axios from 'axios';
import toast from 'react-hot-toast';
import { Button } from './ui/Button';
import { Badge } from './ui/Badge';
import {
  AlertDialogRoot,
  AlertDialogTrigger,
  AlertDialogContent,
  AlertDialogHeader,
  AlertDialogFooter,
  AlertDialogTitle,
  AlertDialogDescription,
  AlertDialogAction,
  AlertDialogCancel,
} from './ui/AlertDialog';

const API_BASE_URL = 'http://127.0.0.1:8000';

function formatTime(dateStr) {
  if (!dateStr) return '';
  try {
    return new Date(dateStr).toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' });
  } catch {
    return '';
  }
}

function TypingIndicator() {
  return (
    <div className="chat-bubble chat-bubble--bot">
      <div className="typing-indicator">
        <span />
        <span />
        <span />
      </div>
    </div>
  );
}

export default function ChatView({ bot, onBack }) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [initialLoading, setInitialLoading] = useState(true);
  const bottomRef = useRef(null);

  useEffect(() => {
    const loadHistory = async () => {
      try {
        const response = await axios.get(`${API_BASE_URL}/bots/${bot.id}/messages`);
        if (response.data.length > 0) {
          setMessages(response.data);
        } else {
          setMessages([
            {
              role: 'bot',
              content: `Bonjour ! Je suis **${bot.name}**. Comment puis-je vous aider aujourd'hui ?`,
              timestamp: new Date().toISOString(),
            },
          ]);
        }
      } catch {
        toast.error("Impossible de charger l'historique de conversation.");
        setMessages([
          {
            role: 'bot',
            content: "Bonjour ! Je suis prêt à vous aider.",
            timestamp: new Date().toISOString(),
          },
        ]);
      } finally {
        setInitialLoading(false);
      }
    };
    loadHistory();
  }, [bot.id, bot.name]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  const clearChat = async () => {
    try {
      await axios.delete(`${API_BASE_URL}/bots/${bot.id}/messages`);
      setMessages([
        {
          role: 'bot',
          content: 'Historique effacé. Nouvelle conversation démarrée !',
          timestamp: new Date().toISOString(),
        },
      ]);
      toast.success('Historique effacé avec succès.');
    } catch {
      toast.error("Erreur lors de la suppression de l'historique.");
    }
  };

  const sendMessage = async () => {
    if (!input.trim() || loading) return;
    const userMsg = {
      role: 'user',
      content: input,
      timestamp: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, userMsg]);
    const sentText = input;
    setInput('');
    setLoading(true);

    try {
      const response = await axios.post(`${API_BASE_URL}/chat`, {
        bot_id: bot.id,
        message: sentText,
      });
      const botMsg = {
        role: 'bot',
        content: response.data.reply,
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, botMsg]);
    } catch {
      toast.error("Erreur de communication avec l'API bot.");
      setMessages((prev) => [
        ...prev,
        {
          role: 'bot',
          content: "⚠️ Désolé, j'ai rencontré une erreur. Veuillez réessayer.",
          timestamp: new Date().toISOString(),
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const urlShort = bot.url?.replace(/^https?:\/\//, '').split('/')[0] || bot.url;

  return (
    <div className="chat-view animate-fade-in">
      {/* Chat Header */}
      <div className="chat-header glass-panel">
        <div className="chat-header-left">
          <Button variant="ghost" size="icon" onClick={onBack} className="chat-back-btn">
            <ArrowLeft size={18} />
          </Button>
          <div className="chat-header-avatar">
            <Bot size={20} />
          </div>
          <div className="chat-header-info">
            <h2 className="chat-header-name">{bot.name}</h2>
            <span className="chat-header-url">
              <Badge variant="success">
                <span className="badge-dot" />
                Connecté
              </Badge>
              <span className="chat-header-url-text">{urlShort}</span>
            </span>
          </div>
        </div>
        <div className="chat-header-actions">
          <AlertDialogRoot>
            <AlertDialogTrigger asChild>
              <Button variant="ghost" size="sm" className="btn-danger-ghost">
                <RotateCcw size={15} />
                Effacer
              </Button>
            </AlertDialogTrigger>
            <AlertDialogContent>
              <AlertDialogHeader>
                <AlertDialogTitle>Effacer la conversation ?</AlertDialogTitle>
                <AlertDialogDescription>
                  Tout l'historique de conversation avec <strong>{bot.name}</strong> sera
                  définitivement supprimé. Cette action est irréversible.
                </AlertDialogDescription>
              </AlertDialogHeader>
              <AlertDialogFooter>
                <AlertDialogCancel>Annuler</AlertDialogCancel>
                <AlertDialogAction onClick={clearChat}>
                  <Trash2 size={15} />
                  Effacer
                </AlertDialogAction>
              </AlertDialogFooter>
            </AlertDialogContent>
          </AlertDialogRoot>
        </div>
      </div>

      {/* Messages */}
      <div className="chat-messages">
        {initialLoading ? (
          <div className="loading-state">
            <Loader2 className="animate-spin" size={32} />
            <p>Chargement de l'historique…</p>
          </div>
        ) : (
          <>
            {messages.map((msg, i) => (
              <div
                key={i}
                className={`chat-message-row chat-message-row--${msg.role}`}
              >
                {msg.role === 'bot' && (
                  <div className="chat-avatar chat-avatar--bot">
                    <Bot size={14} />
                  </div>
                )}
                <div className={`chat-bubble chat-bubble--${msg.role}`}>
                  <p>{msg.content}</p>
                  {msg.timestamp && (
                    <span className="chat-bubble-time">
                      <Clock size={10} />
                      {formatTime(msg.timestamp)}
                    </span>
                  )}
                </div>
              </div>
            ))}
            {loading && (
              <div className="chat-message-row chat-message-row--bot">
                <div className="chat-avatar chat-avatar--bot">
                  <Bot size={14} />
                </div>
                <TypingIndicator />
              </div>
            )}
          </>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div className="chat-input-bar glass-panel">
        <input
          type="text"
          className="chat-input"
          placeholder="Tapez votre message…"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && sendMessage()}
          disabled={loading || initialLoading}
        />
        <Button
          onClick={sendMessage}
          disabled={loading || !input.trim() || initialLoading}
          className="chat-send-btn"
        >
          {loading ? <Loader2 size={18} className="animate-spin" /> : <Send size={18} />}
        </Button>
      </div>
    </div>
  );
}
