import React, { useState, useEffect } from 'react';
import { Bot, Play, Sparkles, Image as ImageIcon } from 'lucide-react';
import './ContextPanel.css';
import { usePromptStore } from '../../store/usePromptStore';
import { useAppStore } from '../../store/useAppStore';
import { expandPrompt, improvePrompt, generateImage, getProfiles } from '../../api';
import { TimelinePanel } from './TimelinePanel';
import { PromptChatDrawer } from '../editor/PromptChatDrawer';

export const ContextPanel: React.FC = () => {
  const { promptText, setPromptText, expandedPromptText, setExpandedPromptText } = usePromptStore();
  const { koboldCppUrl, comfyUIUrl, rightPanelTab, setRightPanelTab, refreshKey } = useAppStore();
  const [loading, setLoading] = useState(false);
  const [aiLoading, setAiLoading] = useState(false);
  const [genLoading, setGenLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [targetModel, setTargetModel] = useState('Krea 2');
  const [profiles, setProfiles] = useState<any[]>([]);
  const [genStatus, setGenStatus] = useState<string | null>(null);
  const [useRag, setUseRag] = useState(false);

  useEffect(() => {
    loadProfiles();
  }, [refreshKey]);

  const loadProfiles = async () => {
    try {
      const data = await getProfiles();
      const defaultOptions = [
        { id: 'krea2', name: 'Krea 2' },
        { id: 'sdxl', name: 'SDXL' },
        { id: 'illustrious', name: 'Illustrious' },
        { id: 'noobai', name: 'NoobAI' },
        { id: 'ideogram', name: 'Ideogram' },
        { id: 'anima', name: 'ANIMA AI' },
      ];
      if (data && data.length > 0) {
        // Merge DB profiles with default fallback models
        const names = new Set(data.map((p: any) => p.name));
        const merged = [...data];
        for (const opt of defaultOptions) {
          if (!names.has(opt.name)) {
            merged.push(opt);
          }
        }
        setProfiles(merged);
      } else {
        setProfiles(defaultOptions);
      }
    } catch (err) {
      console.error(err);
      setProfiles([
        { id: 'krea2', name: 'Krea 2' },
        { id: 'sdxl', name: 'SDXL' },
        { id: 'illustrious', name: 'Illustrious' },
        { id: 'noobai', name: 'NoobAI' },
        { id: 'ideogram', name: 'Ideogram' },
        { id: 'anima', name: 'ANIMA AI' },
      ]);
    }
  };

  const handleSimulate = async () => {
    if (!promptText.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const expanded = await expandPrompt(promptText);
      setExpandedPromptText(expanded);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleImprove = async () => {
    if (!promptText.trim()) return;
    setAiLoading(true);
    setError(null);
    try {
      const improved = await improvePrompt(promptText, targetModel, koboldCppUrl, useRag);
      setPromptText(improved);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setAiLoading(false);
    }
  };

  const handleGenerate = async () => {
    const textToGen = expandedPromptText || promptText;
    if (!textToGen.trim()) return;
    setGenLoading(true);
    setError(null);
    setGenStatus('Submitting to ComfyUI...');
    try {
      const result = await generateImage(textToGen, comfyUIUrl);
      setGenStatus(`Prompt queued! ID: ${result.prompt_id}`);
    } catch (err: any) {
      setError(err.message);
      setGenStatus(null);
    } finally {
      setGenLoading(false);
    }
  };

  return (
    <div className="context-panel glass-panel">
      <div className="context-panel-header">
        <button
          className={`panel-tab-btn ${rightPanelTab === 'chat' ? 'active' : ''}`}
          onClick={() => setRightPanelTab('chat')}
        >
          <Sparkles size={14} /> AI Chat
        </button>
        <button
          className={`panel-tab-btn ${rightPanelTab === 'tools' ? 'active' : ''}`}
          onClick={() => setRightPanelTab('tools')}
        >
          <Bot size={14} /> Quick Tools
        </button>
      </div>

      {rightPanelTab === 'chat' ? (
        <PromptChatDrawer embedded={true} profiles={profiles} />
      ) : (
        <div className="context-panel-content">
          <div style={{ marginBottom: '16px' }}>
            <button 
              className="simulate-btn" 
              onClick={handleSimulate}
              disabled={loading || !promptText.trim()}
            >
              <Play size={14} />
              {loading ? 'Simulating...' : 'Simulate / Expand'}
            </button>
          </div>

          <div className="glass-panel" style={{ padding: '16px', marginBottom: '16px', background: 'var(--bg-panel)' }}>
            <div style={{ marginBottom: '12px', fontSize: '13px', fontWeight: 'bold', color: 'var(--fg-primary)' }}>AI Prompt Optimization</div>
            <select 
              value={targetModel}
              onChange={(e) => setTargetModel(e.target.value)}
              style={{ width: '100%', marginBottom: '12px' }}
            >
              {profiles.map((p: any) => (
                <option key={p.id || p.name} value={p.name}>{p.name}</option>
              ))}
            </select>

            <div style={{ display: 'flex', alignItems: 'center', marginBottom: '12px', fontSize: '13px', color: 'var(--fg-secondary)' }}>
              <input 
                type="checkbox" 
                checked={useRag} 
                onChange={(e) => setUseRag(e.target.checked)} 
                id="use-rag"
                style={{ marginRight: '8px' }}
              />
              <label htmlFor="use-rag" style={{ cursor: 'pointer' }}>Use RAG (Learn from past prompts)</label>
            </div>
            <button 
              className="simulate-btn" 
              onClick={handleImprove}
              disabled={aiLoading || !promptText.trim() || !koboldCppUrl}
              style={{ background: 'var(--bg-hover)', border: '1px solid var(--accent-primary)', boxShadow: 'none' }}
            >
              <Sparkles size={14} color="var(--accent-primary)" />
              {aiLoading ? 'Improving...' : 'Improve Prompt'}
            </button>
          </div>

          <div className="glass-panel" style={{ padding: '16px', background: 'var(--bg-panel)' }}>
            <div style={{ marginBottom: '12px', fontSize: '13px', fontWeight: 'bold', color: 'var(--fg-primary)' }}>Generation</div>
            <button 
              className="simulate-btn" 
              onClick={handleGenerate}
              disabled={genLoading || !promptText.trim() || !comfyUIUrl}
              style={{ background: 'var(--bg-hover)', border: '1px solid var(--accent-success)', boxShadow: 'none' }}
            >
              <ImageIcon size={14} color="var(--accent-success)" />
              {genLoading ? 'Sending...' : 'Send to ComfyUI'}
            </button>
            {genStatus && <div style={{ marginTop: '8px', fontSize: '12px', color: 'var(--accent-success)' }}>{genStatus}</div>}
          </div>

          {error && (
            <div className="error-message" style={{ marginTop: '16px' }}>
              {error}
            </div>
          )}

          {expandedPromptText ? (
            <div className="expanded-result" style={{ marginTop: '16px' }}>
              <div className="expanded-result-title">Expanded Prompt</div>
              <div className="expanded-result-content">
                {expandedPromptText}
              </div>
            </div>
          ) : null}

          <TimelinePanel />
        </div>
      )}
    </div>
  );
};
