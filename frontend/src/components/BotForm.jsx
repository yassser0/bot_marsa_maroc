import React, { useState } from 'react';
import { Bot, Cpu, FileText, Loader2, Save, Plus, Trash2, Settings2 } from 'lucide-react';
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
    tools: []
  });
  const [loading, setLoading] = useState(false);

  const set = (key, val) => setFormData((prev) => ({ ...prev, [key]: val }));

  const addTool = () => {
    set('tools', [...formData.tools, { name: '', description: '', url: '', method: 'GET' }]);
  };

  const removeTool = (index) => {
    const newTools = [...formData.tools];
    newTools.splice(index, 1);
    set('tools', newTools);
  };

  const updateTool = (index, field, value) => {
    const newTools = [...formData.tools];
    newTools[index] = { ...newTools[index], [field]: value };
    set('tools', newTools);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!formData.name.trim()) {
      toast.error('Le nom du bot est obligatoire.');
      return;
    }
    setLoading(true);
    try {
      await onSave(formData);
      toast.success(`Bot "${formData.name}" créé avec succès !`);
    } catch {
      toast.error("Erreur lors de la création du bot.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <form className="bot-form" onSubmit={handleSubmit}>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="space-y-5">
          <FormField label="Nom du bot" hint="Ex: Expert Logistique Marsa">
            <div className="input-icon-wrapper">
              <Bot size={15} className="input-icon" />
              <Input
                value={formData.name}
                onChange={(e) => set('name', e.target.value)}
                className="input-with-icon"
              />
            </div>
          </FormField>

          <FormField label="Modèle" hint="Groq ou OpenAI">
            <div className="input-icon-wrapper">
              <Cpu size={15} className="input-icon" />
              <Input
                placeholder="llama-3.1-8b-instant"
                value={formData.model_name}
                onChange={(e) => set('model_name', e.target.value)}
                className="input-with-icon"
              />
            </div>
          </FormField>

          <FormField label="Instructions (System Prompt)">
            <Textarea
              rows={5}
              placeholder="Tu es un assistant spécialisé..."
              value={formData.prompt}
              onChange={(e) => set('prompt', e.target.value)}
            />
          </FormField>
        </div>

        <div className="space-y-5">
          <FormField label="URL de l'API AI">
            <Input value={formData.url} onChange={(e) => set('url', e.target.value)} />
          </FormField>

          <FormField label="Clé API">
            <Input type="password" value={formData.api_key} onChange={(e) => set('api_key', e.target.value)} />
          </FormField>

          {/* Tools Section */}
          <div className="tools-manager glass-panel p-4">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-sm font-semibold flex items-center gap-2">
                <Settings2 size={16} className="text-accent-400" />
                Outils REST Externes
              </h3>
              <Button type="button" variant="ghost" size="sm" onClick={addTool} className="text-accent-400">
                <Plus size={14} /> Ajouter
              </Button>
            </div>

            <div className="space-y-4 max-h-[300px] overflow-y-auto pr-2 custom-scrollbar">
              {formData.tools.length === 0 && (
                <p className="text-xs text-muted text-center py-4 italic">
                  Aucun outil configuré. L'IA n'aura accès qu'à ses connaissances de base.
                </p>
              )}
              {formData.tools.map((tool, idx) => (
                <div key={idx} className="tool-item glass-panel p-3 bg-white/5 border-dashed">
                  <div className="flex justify-between items-start mb-2">
                    <span className="text-[10px] font-bold text-muted uppercase">Outil #{idx + 1}</span>
                    <button type="button" onClick={() => removeTool(idx)} className="text-danger hover:opacity-70">
                      <Trash2 size={14} />
                    </button>
                  </div>
                  <div className="space-y-3">
                    <Input 
                      placeholder="Nom (ex: get_container_info)" 
                      size="sm"
                      value={tool.name}
                      onChange={(e) => updateTool(idx, 'name', e.target.value)}
                    />
                    <Input 
                      placeholder="Description (ex: Récupère le statut du conteneur)" 
                      size="sm"
                      value={tool.description}
                      onChange={(e) => updateTool(idx, 'description', e.target.value)}
                    />
                    <Input 
                      placeholder="URL REST (ex: http://votre-systeme.com/api/{id})" 
                      size="sm"
                      value={tool.url}
                      onChange={(e) => updateTool(idx, 'url', e.target.value)}
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      <div className="bot-form-actions">
        <Button type="button" variant="ghost" onClick={onCancel}>Annuler</Button>
        <Button type="submit" disabled={loading}>
          {loading ? <Loader2 size={16} className="animate-spin" /> : <Save size={16} />}
          Sauvegarder le Bot
        </Button>
      </div>
    </form>
  );
}
