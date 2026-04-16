import React, { useState } from 'react';
import { Plus, Bot, Search, SlidersHorizontal, Loader2 } from 'lucide-react';
import { Button } from './ui/Button';
import { Input } from './ui/Input';
import BotCard from './BotCard';
import BotForm from './BotForm';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from './ui/Dialog';

export default function BotList({ bots, onSelectBot, onDeleteBot, onBotCreated, onBotUpdated, loading }) {
  const [createOpen, setCreateOpen] = useState(false);
  const [editingBot, setEditingBot] = useState(null);
  const [search, setSearch] = useState('');

  const filtered = bots.filter(
    (b) =>
      b.name?.toLowerCase().includes(search.toLowerCase()) ||
      b.url?.toLowerCase().includes(search.toLowerCase())
  );

  const handleEditClick = (bot) => {
    setEditingBot(bot);
    setCreateOpen(true);
  };

  const handleClose = () => {
    setCreateOpen(false);
    setEditingBot(null);
  };

  if (loading) {
    return (
      <div className="loading-state">
        <Loader2 className="animate-spin" size={36} />
        <p>Chargement des bots…</p>
      </div>
    );
  }

  return (
    <div className="animate-fade-in page-section">
      {/* Page Header */}
      <div className="page-header">
        <div>
          <h2 className="page-title">Mes Bots</h2>
          <p className="page-subtitle">
            {bots.length} assistant{bots.length !== 1 ? 's' : ''} configuré{bots.length !== 1 ? 's' : ''}
          </p>
        </div>
        <div className="page-header-actions">
          <div className="search-wrapper">
            <Search size={15} className="search-icon" />
            <Input
              placeholder="Rechercher un bot…"
              className="search-input"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>
          <Button onClick={() => setCreateOpen(true)}>
            <Plus size={17} />
            Nouveau Bot
          </Button>
        </div>
      </div>

      {/* Grid */}
      {filtered.length === 0 ? (
        <div className="empty-state glass-panel">
          <div className="empty-state-icon">
            <Bot size={40} />
          </div>
          <h3>Aucun bot trouvé</h3>
          <p>
            {search
              ? 'Aucun bot ne correspond à votre recherche.'
              : 'Créez votre premier bot pour commencer.'}
          </p>
          {!search && (
            <Button onClick={() => setCreateOpen(true)}>
              <Plus size={17} />
              Créer un Bot
            </Button>
          )}
        </div>
      ) : (
        <div className="bot-grid">
          {filtered.map((bot) => (
            <BotCard
              key={bot.id}
              bot={bot}
              onSelectBot={onSelectBot}
              onDeleteBot={onDeleteBot}
              onEditBot={handleEditClick}
            />
          ))}
        </div>
      )}

      {/* Create/Edit Bot Dialog */}
      <Dialog open={createOpen} onOpenChange={(open) => !open && handleClose()}>
        <DialogContent className="dialog-content-lg">
          <DialogHeader>
            <DialogTitle>{editingBot ? 'Modifier le Bot' : 'Créer un nouveau Bot'}</DialogTitle>
            <DialogDescription>
              {editingBot 
                ? 'Mettez à jour la configuration et les outils de votre assistant.' 
                : 'Configurez votre assistant IA avec une URL d\'API et un prompt système.'}
            </DialogDescription>
          </DialogHeader>
          <BotForm
            initialData={editingBot}
            onCancel={handleClose}
            onSave={async (id_or_data, data) => {
              if (editingBot) {
                await onBotUpdated(id_or_data, data);
              } else {
                await onBotCreated(id_or_data);
              }
              handleClose();
            }}
          />
        </DialogContent>
      </Dialog>
    </div>
  );
}
