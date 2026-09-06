import React, { useState } from 'react';
import { usePromptStore } from '../../store/usePromptStore';
import { useAppStore } from '../../store/useAppStore';
import { animaImprovePrompt, AnimaOptions } from '../../api';
import { DiffViewer } from './DiffViewer';
import { Sparkles, Eraser, Copy, Check, Send, AlertCircle, CheckCircle2, Cpu, Tag, Layers, FileText } from 'lucide-react';
import './AnimaStudioPanel.css';

export const AnimaStudioPanel: React.FC = () => {
  const { promptText, setPromptText } = usePromptStore();
  const { setActiveView, setComfySettings } = useAppStore();

  const [rawPrompt, setRawPrompt] = useState<string>(promptText || '');
  const [variant, setVariant] = useState<'hybrid' | 'tag_focused' | 'natural_language'>('hybrid');
  const [addQualityTags, setAddQualityTags] = useState<boolean>(true);
  const [cleanWeights, setCleanWeights] = useState<boolean>(true);
  const [useRAG, setUseRAG] = useState<boolean>(true);
  const [negativePrompt, setNegativePrompt] = useState<string>(
    'worst quality, low quality, score_1, score_2, score_3, artist name, blurry, bad anatomy, extra fingers'
  );
  const [improvedPrompt, setImprovedPrompt] = useState<string>('');
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [copied, setCopied] = useState<boolean>(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [toastMsg, setToastMsg] = useState<string | null>(null);

  const showNotification = (msg: string) => {
    setToastMsg(msg);
    setTimeout(() => setToastMsg(null), 3000);
  };

  // Client-side action button: Clean SD weights
  const handleCleanWeightsAction = () => {
    const target = rawPrompt || promptText;
    if (!target.trim()) return;

    const cleaned = target
      .replace(/\(([^:()]+):[\d.]+\)/g, '$1') // (tag:1.2) -> tag
      .replace(/\(([^()]+)\)/g, '$1')         // (tag) -> tag
      .replace(/\[([^[\]]+)\]/g, '$1')        // [tag] -> tag
      .replace(/,\s*,/g, ',')
      .replace(/^\s*,\s*|\s*,\s*$/g, '')
      .replace(/\s{2,}/g, ' ')
      .trim();

    setRawPrompt(cleaned);
    if (improvedPrompt) {
      const cleanedImproved = improvedPrompt
        .replace(/\(([^:()]+):[\d.]+\)/g, '$1')
        .replace(/\(([^()]+)\)/g, '$1')
        .replace(/\[([^[\]]+)\]/g, '$1')
        .replace(/,\s*,/g, ',')
        .replace(/^\s*,\s*|\s*,\s*$/g, '')
        .replace(/\s{2,}/g, ' ')
        .trim();
      setImprovedPrompt(cleanedImproved);
    }
    showNotification('Cleaned SD weights from prompt!');
  };

  // Action button: Improve Prompt for ANIMA
  const handleImprovePrompt = async () => {
    if (!rawPrompt.trim()) return;
    setIsLoading(true);
    setErrorMsg(null);
    try {
      const options: AnimaOptions = {
        prompt: rawPrompt,
        variant,
        add_quality_tags: addQualityTags,
        clean_weights: cleanWeights,
        negative_prompt: negativePrompt,
        use_rag: useRAG,
      };

      const result = await animaImprovePrompt(options);
      setImprovedPrompt(result);
      showNotification('Prompt successfully improved for ANIMA!');
    } catch (err: any) {
      console.error('Failed to improve prompt with ANIMA:', err);
      setErrorMsg(err.message || 'Failed to improve prompt for ANIMA');
    } finally {
      setIsLoading(false);
    }
  };

  // Output action: Copy Prompt
  const handleCopyPrompt = () => {
    const textToCopy = improvedPrompt || rawPrompt;
    if (!textToCopy) return;
    navigator.clipboard.writeText(textToCopy);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
    showNotification('Prompt copied to clipboard!');
  };

  // Output action: Send to Prompt Editor
  const handleSendToPromptEditor = () => {
    const textToSend = improvedPrompt || rawPrompt;
    if (!textToSend) return;
    setPromptText(textToSend);
    setActiveView('prompts');
    showNotification('Sent prompt to Prompt Editor!');
  };

  // Output action: Dispatch to ComfyUI
  const handleDispatchToComfyUI = () => {
    const textToDispatch = improvedPrompt || rawPrompt;
    if (!textToDispatch) return;
    setComfySettings({ singlePrompt: textToDispatch });
    setActiveView('comfyui');
    showNotification('Dispatched prompt to ComfyUI!');
  };

  return (
    <div className="anima-panel-container">
      {/* Header */}
      <div className="anima-header">
        <div className="anima-title-section">
          <h2>
            <Sparkles size={24} style={{ color: '#ec4899' }} />
            ANIMA Studio Panel
            <span className="anima-badge">ANIMA Qwen Hybrid Prompt Engine</span>
          </h2>
          <div className="anima-subtitle">
            Next-generation Anime & Hybrid AI prompt generator powered by ANIMA 8B Qwen2.5 base architecture
          </div>
        </div>
        {toastMsg && (
          <div className="toast-msg">
            <CheckCircle2 size={16} />
            {toastMsg}
          </div>
        )}
      </div>

      {/* Controls Grid */}
      <div className="anima-controls-grid">
        {/* Left Column: Preset Mode Cards & Options */}
        <div className="anima-card">
          <div className="card-title">
            <Layers size={16} style={{ color: '#ec4899' }} />
            ANIMA Optimization Variant
          </div>

          <div className="variant-buttons">
            <button
              className={`variant-btn ${variant === 'hybrid' ? 'active' : ''}`}
              onClick={() => setVariant('hybrid')}
            >
              <div className="variant-name">
                <Sparkles size={14} /> Hybrid
              </div>
              <div className="variant-desc">Danbooru tags + natural language</div>
            </button>

            <button
              className={`variant-btn ${variant === 'tag_focused' ? 'active' : ''}`}
              onClick={() => setVariant('tag_focused')}
            >
              <div className="variant-name">
                <Tag size={14} /> Tag Focused
              </div>
              <div className="variant-desc">Comma-separated anime tag structure</div>
            </button>

            <button
              className={`variant-btn ${variant === 'natural_language' ? 'active' : ''}`}
              onClick={() => setVariant('natural_language')}
            >
              <div className="variant-name">
                <FileText size={14} /> Natural Lang
              </div>
              <div className="variant-desc">Flowing descriptive narrative prose</div>
            </button>
          </div>

          <div className="toggle-group" style={{ marginTop: '8px' }}>
            <label className="toggle-label">
              <input
                type="checkbox"
                checked={addQualityTags}
                onChange={(e) => setAddQualityTags(e.target.checked)}
              />
              Add ANIMA Quality Tags (masterpiece, score_9, best quality)
            </label>

            <label className="toggle-label">
              <input
                type="checkbox"
                checked={cleanWeights}
                onChange={(e) => setCleanWeights(e.target.checked)}
              />
              Clean SD Weights (strip (tag:1.2) syntax)
            </label>

            <label className="toggle-label" style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <input
                type="checkbox"
                checked={useRAG}
                onChange={(e) => setUseRAG(e.target.checked)}
              />
              📚 Use RAG Anime Tag Rules
              {useRAG && <span className="rag-active-pill">RAG Active</span>}
            </label>
          </div>

          <div className="form-group" style={{ marginTop: '4px' }}>
            <label>Negative Prompt Generator</label>
            <textarea
              className="prompt-input-area"
              style={{ minHeight: '60px' }}
              value={negativePrompt}
              onChange={(e) => setNegativePrompt(e.target.value)}
              placeholder="Negative prompt tags..."
            />
          </div>
        </div>

        {/* Right Column: Prompt Input Textarea */}
        <div className="anima-card">
          <div className="card-title">
            <FileText size={16} style={{ color: '#ec4899' }} />
            Raw Input Prompt
          </div>
          <textarea
            className="prompt-input-area"
            style={{ flex: 1, minHeight: '160px' }}
            value={rawPrompt}
            onChange={(e) => setRawPrompt(e.target.value)}
            placeholder="Enter raw anime, character, scene or art prompt here..."
          />
        </div>
      </div>

      {/* Action Buttons */}
      <div className="anima-actions">
        <button
          className="action-btn primary"
          onClick={handleImprovePrompt}
          disabled={isLoading || !rawPrompt.trim()}
        >
          <Sparkles size={16} />
          {isLoading ? 'Improving Prompt...' : '✨ Improve Prompt for ANIMA'}
        </button>

        <button
          className="action-btn"
          onClick={handleCleanWeightsAction}
          disabled={isLoading || (!rawPrompt.trim() && !improvedPrompt.trim())}
        >
          <Eraser size={16} />
          🧹 Clean SD Weights
        </button>
      </div>

      {errorMsg && (
        <div
          className="toast-msg"
          style={{
            background: 'rgba(239, 68, 68, 0.2)',
            color: 'var(--accent-danger)',
            border: '1px solid rgba(239, 68, 68, 0.4)',
          }}
        >
          <AlertCircle size={16} />
          {errorMsg}
        </div>
      )}

      {/* Output Preview Card */}
      <div className="output-card">
        <div className="output-header">
          <div className="card-title">
            <Sparkles size={16} style={{ color: '#ec4899' }} />
            Output Preview (Original vs Improved ANIMA Prompt)
          </div>
          <div className="output-actions">
            <button
              className="action-btn"
              onClick={handleCopyPrompt}
              disabled={!improvedPrompt && !rawPrompt}
              title="Copy prompt to clipboard"
            >
              {copied ? <Check size={16} style={{ color: 'var(--accent-success)' }} /> : <Copy size={16} />}
              {copied ? 'Copied!' : 'Copy Prompt'}
            </button>

            <button
              className="action-btn"
              onClick={handleSendToPromptEditor}
              disabled={!improvedPrompt && !rawPrompt}
              title="Open prompt in main editor"
            >
              <Send size={16} />
              Send to Prompt Editor
            </button>

            <button
              className="action-btn primary"
              onClick={handleDispatchToComfyUI}
              disabled={!improvedPrompt && !rawPrompt}
              title="Send prompt directly to ComfyUI live stream"
            >
              <Cpu size={16} />
              Dispatch to ComfyUI
            </button>
          </div>
        </div>

        <div className="output-preview-container">
          <DiffViewer original={rawPrompt} modified={improvedPrompt || rawPrompt} />
        </div>
      </div>
    </div>
  );
};
