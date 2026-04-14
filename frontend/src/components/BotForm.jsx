import React, { useState } from 'react';
import { Bot, Link2, Key, Cpu, FileText, Loader2, Save } from 'lucide-react';
import { Button } from './ui/Button';
import { Input, Textarea, FormField } from './ui/Input';
import toast from 'react-hot-toast';

const GROQ_MODELS = [
  'llama-3.1-8b-instant',
  'llama3-8b-8192',
  'llama3-70b-8192',
  'mixtral-8x7b-32768',
  'gemma2-9b-it',
];

export default function BotForm({ onCancel, onSave }) {
  const [formData, setFormData] = useState({
    name: '',
    url: 'https://api.groq.com/openai/v1/chat/completions',
    api_key: '',
    model_name: 'llama-3.1-8b-instant',
    prompt: '',
  });
  const [loading, setLoading] = useState(false);

  const set = (key, val) => setFormData((prev) => ({ ...prev, [key]: val }));

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!formData.name.trim()) {
      toast.error('Le nom du bot est obligatoire.');
      return;
    }
    if (!formData.url.trim()) {
      toast.error("L'URL de l'API est obligatoire.");
      return;
    }
    setLoading(true);
    try {
      await onSave(formData);
      toast.success(`Bot "${formData.name}" créé avec succès !`);
    } catch {
      toast.error("Erreur lors de la création du bot. Vérifiez vos paramètres.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <form className="bot-form" onSubmit={handleSubmit}>
      <FormField
        label="Nom du bot"
        hint="Donnez un nom distinctif à votre assistant."
      >
        <div className="input-icon-wrapper">
          <Bot size={15} className="input-icon" />
          <Input
            placeholder="Ex: Assistant RH Maritime"
            value={formData.name}
            onChange={(e) => set('name', e.target.value)}
            className="input-with-icon"
          />
        </div>
      </FormField>

      <FormField
        label="URL de l'API externe"
        hint="Utilisez 'mock_api' pour tester sans clé."
      >
        <div className="input-icon-wrapper">
          <Link2 size={15} className="input-icon" />
          <Input
            placeholder="https://api.openai.com/v1/chat/completions"
            value={formData.url}
            onChange={(e) => set('url', e.target.value)}
            className="input-with-icon"
          />
        </div>
      </FormField>

      <FormField label="Clé d'authentification (optionnel)">
        <div className="input-icon-wrapper">
          <Key size={15} className="input-icon" />
          <Input
            type="password"
            placeholder="sk-..."
            value={formData.api_key}
            onChange={(e) => set('api_key', e.target.value)}
            className="input-with-icon"
          />
        </div>
      </FormField>

      <FormField
        label="Modèle"
        hint="Ex: llama3-8b-8192 (Groq), gpt-4o (OpenAI)"
      >
        <div className="input-icon-wrapper">
          <Cpu size={15} className="input-icon" />
          <Input
            placeholder="llama-3.1-8b-instant"
            value={formData.model_name}
            onChange={(e) => set('model_name', e.target.value)}
            className="input-with-icon"
            list="model-suggestions"
          />
          <datalist id="model-suggestions">
            {GROQ_MODELS.map((m) => (
              <option key={m} value={m} />
            ))}
          </datalist>
        </div>
      </FormField>

      <FormField label="Instructions système (System Prompt)">
        <div className="input-icon-wrapper input-icon-wrapper--textarea">
          <FileText size={15} className="input-icon input-icon--top" />
          <Textarea
            rows={4}
            placeholder="Tu es un assistant spécialisé dans les opérations portuaires de Marsa Maroc…"
            value={formData.prompt}
            onChange={(e) => set('prompt', e.target.value)}
            className="input-with-icon"
          />
        </div>
      </FormField>

      <div className="bot-form-actions">
        <Button type="button" variant="ghost" onClick={onCancel} disabled={loading}>
          Annuler
        </Button>
        <Button type="submit" disabled={loading}>
          {loading ? <Loader2 size={16} className="animate-spin" /> : <Save size={16} />}
          {loading ? 'Enregistrement…' : 'Créer le Bot'}
        </Button>
      </div>
    </form>
  );
}
