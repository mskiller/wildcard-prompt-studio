import React, { useState } from 'react';
import { usePromptStore } from '../../store/usePromptStore';
import { useAppStore } from '../../store/useAppStore';
import { krea2ImprovePrompt, expandMatrixPrompt, Krea2Options } from '../../api';
import { DiffViewer } from './DiffViewer';
import { Wand2, Sparkles, Eraser, Quote, Grid, CheckCircle2, AlertCircle, ArrowRight, Scale } from 'lucide-react';
import { cleanPromptWeights } from '../../utils/promptCleaner';
import './Krea2StudioPanel.css';

export const Krea2StudioPanel: React.FC = () => {
  const { promptText, setPromptText } = usePromptStore();
  const { maxOutputTokens, enableThinkingTokenBoost } = useAppStore();

  const [originalPrompt, setOriginalPrompt] = useState<string>(promptText || '');
  const [optimizedPrompt, setOptimizedPrompt] = useState<string>(promptText || '');
  const [variant, setVariant] = useState<'turbo' | 'medium' | 'large'>('turbo');
  const [provider, setProvider] = useState<'kobold' | 'ollama' | 'gemini'>('kobold');
  const [cleanBuzzwords, setCleanBuzzwords] = useState<boolean>(true);
  const [useRAG, setUseRAG] = useState<boolean>(true);
  const [quoteTargetsInput, setQuoteTargetsInput] = useState<string>('');
  
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [toastMsg, setToastMsg] = useState<string | null>(null);
  const [matrixResults, setMatrixResults] = useState<string[]>([]);

  const showNotification = (msg: string) => {
    setToastMsg(msg);
    setTimeout(() => setToastMsg(null), 3000);
  };

  // 1-Click Action: Krea 2 Expand Prompt
  const handleKrea2Expand = async () => {
    if (!originalPrompt.trim()) return;
    setIsLoading(true);
    setErrorMsg(null);
    try {
      const quoteTargets = quoteTargetsInput
        .split(',')
        .map(s => s.trim())
        .filter(Boolean);

      const options: Krea2Options = {
        prompt: originalPrompt,
        variant,
        provider,
        clean_buzzwords: cleanBuzzwords,
        use_rag: useRAG,
        quote_targets: quoteTargets.length > 0 ? quoteTargets : undefined,
        max_tokens: enableThinkingTokenBoost ? maxOutputTokens : 512,
      };

      const result = await krea2ImprovePrompt(options);
      setOptimizedPrompt(result);
      showNotification('Prompt successfully expanded with Krea 2!');
    } catch (err: any) {
      console.error('Failed Krea 2 expansion:', err);
      setErrorMsg(err.message || 'Failed to improve prompt with Krea 2');
    } finally {
      setIsLoading(false);
    }
  };

  // 1-Click Action: Clean Buzzwords
  const handleCleanBuzzwords = () => {
    if (!originalPrompt.trim()) return;
    const buzzwordsRegex = /\b(8k|4k|masterpiece|hyperdetailed|photorealistic|trending on artstation|ultra detailed|high quality|best quality|hdr|unreal engine|8k resolution|4k resolution|absurdres|highres)\b/gi;
    let cleaned = originalPrompt.replace(buzzwordsRegex, '');
    // Clean trailing/multiple commas and whitespace
    cleaned = cleaned
      .replace(/,\s*,/g, ',')
      .replace(/^\s*,\s*|\s*,\s*$/g, '')
      .replace(/\s{2,}/g, ' ')
      .trim();

    setOptimizedPrompt(cleaned);
    showNotification('Buzzwords cleaned!');
  };

  // 1-Click Action: Remove Prompt Weights
  const handleRemoveWeights = () => {
    if (!originalPrompt.trim()) return;
    const cleaned = cleanPromptWeights(originalPrompt);
    setOptimizedPrompt(cleaned);
    showNotification('Prompt weights removed!');
  };

  // 1-Click Action: Quote Helper
  const handleQuoteHelper = () => {
    if (!originalPrompt.trim()) return;
    let quoted = originalPrompt;
    
    if (quoteTargetsInput.trim()) {
      const targets = quoteTargetsInput
        .split(',')
        .map(s => s.trim())
        .filter(Boolean);

      targets.forEach(target => {
        if (!target) return;
        const esc = target.replace(/[-[\]{}()*+?.,\\^$|#\s]/g, '\\$&');
        const regex = new RegExp(`(?<!")\\b(${esc})\\b(?!")`, 'gi');
        quoted = quoted.replace(regex, '"$1"');
      });
    } else {
      // If no target specified, automatically quote multi-word noun phrases or key descriptors
      const descriptors = originalPrompt.split(',').map(s => s.trim());
      const newDescriptors = descriptors.map(desc => {
        if (desc.includes(' ') && !desc.startsWith('"') && !desc.endsWith('"')) {
          return `"${desc}"`;
        }
        return desc;
      });
      quoted = newDescriptors.join(', ');
    }

    setOptimizedPrompt(quoted);
    showNotification('Applied quote helper!');
  };

  // 1-Click Action: Expand Matrix
  const handleExpandMatrix = async () => {
    if (!originalPrompt.trim()) return;
    setIsLoading(true);
    setErrorMsg(null);
    try {
      const results = await expandMatrixPrompt(originalPrompt, 10);
      setMatrixResults(results);
      if (results.length > 0) {
        setOptimizedPrompt(results[0]);
        showNotification(`Matrix expanded into ${results.length} permutations!`);
      }
    } catch (err: any) {
      console.error('Failed matrix expansion:', err);
      setErrorMsg(err.message || 'Failed to expand matrix prompt');
    } finally {
      setIsLoading(false);
    }
  };

  // Apply optimized prompt back to main editor store
  const handleApplyToEditor = () => {
    setPromptText(optimizedPrompt);
    showNotification('Applied optimized prompt to Main Editor!');
  };

  return (
    <div className="krea2-panel-container">
      {/* Header */}
      <div className="krea2-header">
        <div className="krea2-title-section">
          <h2>
            <Wand2 size={24} style={{ color: 'var(--accent-primary)' }} />
            Krea 2 Studio Panel
          </h2>
          <div className="krea2-subtitle">
            Next-gen AI prompt optimization, artistic style variants, buzzword stripping & matrix engine
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
      <div className="krea2-controls-grid">
        {/* Left Column: Variant & Provider */}
        <div className="krea2-card">
          <div className="card-title">
            <Sparkles size={16} style={{ color: 'var(--accent-primary)' }} />
            Krea 2 Style Variant
          </div>
          <div className="variant-buttons">
            <button
              className={`variant-btn ${variant === 'turbo' ? 'active' : ''}`}
              onClick={() => setVariant('turbo')}
            >
              <div className="variant-name">⚡ Turbo</div>
              <div className="variant-desc">2k fast ideation</div>
            </button>
            <button
              className={`variant-btn ${variant === 'medium' ? 'active' : ''}`}
              onClick={() => setVariant('medium')}
            >
              <div className="variant-name">🎨 Medium</div>
              <div className="variant-desc">Artistic / illustrations</div>
            </button>
            <button
              className={`variant-btn ${variant === 'large' ? 'active' : ''}`}
              onClick={() => setVariant('large')}
            >
              <div className="variant-name">📷 Large</div>
              <div className="variant-desc">Raw photorealism</div>
            </button>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', marginTop: '8px' }}>
            <div className="form-group">
              <label>AI Provider Backend</label>
              <select
                value={provider}
                onChange={e => setProvider(e.target.value as any)}
                style={{ width: '100%' }}
              >
                <option value="kobold">KoboldCpp</option>
                <option value="ollama">Ollama</option>
                <option value="gemini">Gemini</option>
              </select>
            </div>

            <div className="form-group">
              <label>Quote Targets (comma separated)</label>
              <input
                type="text"
                placeholder="e.g. red car, neon eyes"
                value={quoteTargetsInput}
                onChange={e => setQuoteTargetsInput(e.target.value)}
              />
            </div>
          </div>
        </div>

        {/* Right Column: Original Input Prompt */}
        <div className="krea2-card">
          <div className="card-title">Input Prompt</div>
          <textarea
            className="prompt-input-area"
            value={originalPrompt}
            onChange={e => setOriginalPrompt(e.target.value)}
            placeholder="Type or paste your prompt here..."
          />
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', marginTop: '4px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <input
                type="checkbox"
                id="clean-buzzwords-cb"
                checked={cleanBuzzwords}
                onChange={e => setCleanBuzzwords(e.target.checked)}
              />
              <label htmlFor="clean-buzzwords-cb" style={{ fontSize: '12px', cursor: 'pointer' }}>
                Auto Clean Buzzwords (8k, masterpiece, hyperdetailed)
              </label>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <input
                type="checkbox"
                id="krea2-use-rag-cb"
                checked={useRAG}
                onChange={e => setUseRAG(e.target.checked)}
              />
              <label htmlFor="krea2-use-rag-cb" style={{ fontSize: '12px', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '6px' }}>
                📚 Use RAG Optics & Guidelines
                {useRAG && <span className="rag-active-pill">RAG Active</span>}
              </label>
            </div>
          </div>
        </div>
      </div>

      {/* 1-Click Action Buttons */}
      <div className="krea2-actions">
        <button
          className="action-btn primary"
          onClick={handleKrea2Expand}
          disabled={isLoading || !originalPrompt.trim()}
        >
          <Sparkles size={16} />
          ✨ Krea 2 Expand Prompt
        </button>

        <button
          className="action-btn"
          onClick={handleCleanBuzzwords}
          disabled={isLoading || !originalPrompt.trim()}
        >
          <Eraser size={16} />
          🧹 Clean Buzzwords
        </button>

        <button
          className="action-btn"
          onClick={handleRemoveWeights}
          disabled={isLoading || !originalPrompt.trim()}
        >
          <Scale size={16} />
          ⚖️ Remove Weights
        </button>

        <button
          className="action-btn"
          onClick={handleQuoteHelper}
          disabled={isLoading || !originalPrompt.trim()}
        >
          <Quote size={16} />
          💬 Quote Helper
        </button>

        <button
          className="action-btn"
          onClick={handleExpandMatrix}
          disabled={isLoading || !originalPrompt.trim()}
        >
          <Grid size={16} />
          🔀 Expand Matrix
        </button>
      </div>

      {errorMsg && (
        <div className="toast-msg" style={{ background: 'rgba(239, 68, 68, 0.2)', color: 'var(--accent-danger)', border: '1px solid rgba(239, 68, 68, 0.4)' }}>
          <AlertCircle size={16} />
          {errorMsg}
        </div>
      )}

      {/* Matrix Permutation Samples */}
      {matrixResults.length > 0 && (
        <div className="krea2-card">
          <div className="card-title">
            <Grid size={16} /> Matrix Expansion Results ({matrixResults.length} variations)
          </div>
          <div className="matrix-samples">
            {matrixResults.map((item, idx) => (
              <div
                key={idx}
                className="matrix-item"
                style={{ cursor: 'pointer' }}
                onClick={() => setOptimizedPrompt(item)}
                title="Click to load into Diff Viewer"
              >
                {idx + 1}. {item}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Side-by-Side Diff Viewer */}
      <div className="diff-section">
        <div className="diff-header">
          <div className="card-title">Side-by-Side Diff / Preview Viewer (Original vs. Optimized)</div>
          <button
            className="action-btn primary"
            onClick={handleApplyToEditor}
            disabled={!optimizedPrompt.trim()}
          >
            <ArrowRight size={16} />
            Apply to Editor
          </button>
        </div>
        <div className="diff-container">
          <DiffViewer original={originalPrompt} modified={optimizedPrompt} />
        </div>
      </div>
    </div>
  );
};
