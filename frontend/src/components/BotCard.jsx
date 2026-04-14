import React, { useState } from 'react';
import { Bot, Server, Cpu, Trash2, MessageSquare, MoreVertical, ExternalLink } from 'lucide-react';
import { Badge } from './ui/Badge';
import { Button } from './ui/Button';
import { Tooltip, TooltipContent, TooltipTrigger, TooltipProvider } from './ui/Tooltip';
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

export default function BotCard({ bot, onSelectBot, onDeleteBot }) {
  const modelShort = bot.model_name?.split('-').slice(0, 2).join('-') || 'N/A';
  const promptPreview = bot.prompt
    ? bot.prompt.length > 55
      ? bot.prompt.substring(0, 55) + '…'
      : bot.prompt
    : 'Aucune instruction définie';

  const urlShort = bot.url?.replace(/^https?:\/\//, '').split('/')[0] || bot.url;

  return (
    <TooltipProvider>
      <div className="bot-card glass-panel glass-card-hover">
        {/* Card Header */}
        <div className="bot-card-header">
          <div className="bot-card-avatar">
            <Bot size={22} />
          </div>
          <div className="bot-card-info">
            <h3 className="bot-card-name">{bot.name}</h3>
            <Badge variant="success">
              <span className="badge-dot" />
              Prêt
            </Badge>
          </div>
        </div>

        {/* Card Meta */}
        <div className="bot-card-meta">
          <div className="bot-card-meta-item">
            <Server size={13} />
            <Tooltip>
              <TooltipTrigger asChild>
                <span className="bot-card-meta-text truncate">{urlShort}</span>
              </TooltipTrigger>
              <TooltipContent>{bot.url}</TooltipContent>
            </Tooltip>
          </div>
          <div className="bot-card-meta-item">
            <Cpu size={13} />
            <span className="bot-card-meta-text">{modelShort}</span>
          </div>
        </div>

        {/* Prompt Preview */}
        <p className="bot-card-prompt">{promptPreview}</p>

        {/* Divider */}
        <div className="bot-card-divider" />

        {/* Actions */}
        <div className="bot-card-actions">
          <Button
            variant="primary"
            size="sm"
            className="bot-card-btn-chat"
            onClick={() => onSelectBot(bot)}
          >
            <MessageSquare size={15} />
            Tester
          </Button>

          {/* Delete Confirm AlertDialog */}
          <AlertDialogRoot>
            <AlertDialogTrigger asChild>
              <Button variant="ghost" size="icon" className="bot-card-btn-delete">
                <Trash2 size={15} />
              </Button>
            </AlertDialogTrigger>
            <AlertDialogContent>
              <AlertDialogHeader>
                <AlertDialogTitle>Supprimer ce bot ?</AlertDialogTitle>
                <AlertDialogDescription>
                  Cette action est irréversible. Le bot <strong>{bot.name}</strong> et tout son
                  historique de conversation seront définitivement supprimés.
                </AlertDialogDescription>
              </AlertDialogHeader>
              <AlertDialogFooter>
                <AlertDialogCancel>Annuler</AlertDialogCancel>
                <AlertDialogAction onClick={() => onDeleteBot(bot.id)}>
                  <Trash2 size={15} />
                  Supprimer
                </AlertDialogAction>
              </AlertDialogFooter>
            </AlertDialogContent>
          </AlertDialogRoot>
        </div>
      </div>
    </TooltipProvider>
  );
}
