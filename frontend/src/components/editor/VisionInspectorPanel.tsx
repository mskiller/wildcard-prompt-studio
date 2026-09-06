import React, { useState } from 'react';
import { useAppStore } from '../../store/useAppStore';
import { indexRAGKnowledge } from '../../api';
import { BookOpen, Check, X, BookmarkPlus } from 'lucide-react';
import './VisionInspectorPanel.css';

interface VisionInspectorPanelProps {
  onInsertPrompt: (prompt: string) => void;
  onIndexRAG?: (title: string, content: string) => void;
}

export const VisionInspectorPanel: React.FC<VisionInspectorPanelProps> = ({
  onInsertPrompt,
  onIndexRAG
}) => {
  const { maxOutputTokens, enableThinkingTokenBoost } = useAppStore();
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [variant, setVariant] = useState<string>('turbo');
  const [provider, setProvider] = useState<string>('koboldcpp');
  const [loading, setLoading] = useState<boolean>(false);
  const [resultPrompt, setResultPrompt] = useState<string>('');
  const [extractedStyle, setExtractedStyle] = useState<any>(null);

  // RAG Save Modal state
  const [showRAGModal, setShowRAGModal] = useState<boolean>(false);
  const [ragTitle, setRagTitle] = useState<string>('Vision Reference Style');
  const [ragCategory, setRagCategory] = useState<string>('optics');
  const [ragTags, setRagTags] = useState<string>('vision, reference, style');
  const [isSavingRAG, setIsSavingRAG] = useState<boolean>(false);
  const [ragStatusMsg, setRagStatusMsg] = useState<string | null>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      setSelectedFile(file);
      setPreviewUrl(URL.createObjectURL(file));
      const baseName = file.name.replace(/\.[^/.]+$/, '').replace(/[-_]/g, ' ');
      setRagTitle(`Style: ${baseName}`);
    }
  };

  const handleDescribe = async () => {
    if (!selectedFile) return;
    setLoading(true);
    try {
      const formData = new FormData();
      formData.append('file', selectedFile);
      formData.append('variant', variant);
      formData.append('provider', provider);
      formData.append('max_tokens', String(enableThinkingTokenBoost ? maxOutputTokens : 512));

      const response = await fetch('/api/v1/ai/vision/describe', {
        method: 'POST',
        body: formData
      });
      const data = await response.json();
      if (data.prompt) {
        setResultPrompt(data.prompt);
      }
    } catch (err) {
      console.error('Vision describe error:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleExtractStyle = async () => {
    if (!selectedFile) return;
    setLoading(true);
    try {
      const formData = new FormData();
      formData.append('file', selectedFile);
      formData.append('provider', provider);
      formData.append('index_rag', 'false'); // Let user review before indexing

      const response = await fetch('/api/v1/ai/vision/extract-style', {
        method: 'POST',
        body: formData
      });
      const data = await response.json();
      if (data.descriptors) {
        setExtractedStyle(data.descriptors);
        setShowRAGModal(true);
      }
    } catch (err) {
      console.error('Vision style extraction error:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleConfirmSaveRAG = async () => {
    if (!extractedStyle) return;
    setIsSavingRAG(true);
    setRagStatusMsg(null);
    try {
      const tagsArray = ragTags
        .split(',')
        .map(t => t.trim())
        .filter(Boolean);

      const content = typeof extractedStyle === 'string'
        ? extractedStyle
        : JSON.stringify(extractedStyle, null, 2);

      await indexRAGKnowledge(ragTitle.trim(), content, ragCategory, tagsArray);
      if (onIndexRAG) {
        onIndexRAG(ragTitle.trim(), content);
      }
      setRagStatusMsg('Saved to persistent RAG knowledge base!');
      setTimeout(() => {
        setRagStatusMsg(null);
        setShowRAGModal(false);
      }, 2000);
    } catch (err: any) {
      console.error('Failed to save to RAG:', err);
      setRagStatusMsg(`Error: ${err.message || 'Save failed'}`);
    } finally {
      setIsSavingRAG(false);
    }
  };

  return (
    <div className="vision-inspector-panel">
      <h3>👁️ Vision Feedback Loop & Image-to-Prompt</h3>
      
      <div className="upload-area">
        <input type="file" accept="image/*" onChange={handleFileChange} id="vision-file-input" />
        <label htmlFor="vision-file-input" className="upload-label">
          {previewUrl ? (
            <img src={previewUrl} alt="Preview" className="image-preview" />
          ) : (
            <span>📸 Click or Drop Reference Image Here</span>
          )}
        </label>
      </div>

      <div className="vision-controls">
        <div className="control-group">
          <label>Vision Backend:</label>
          <select value={provider} onChange={(e) => setProvider(e.target.value)}>
            <option value="koboldcpp">KoboldCpp Multi-Modal</option>
            <option value="ollama">Ollama (LLaVA / Qwen-VL)</option>
            <option value="gemini">Google Gemini 1.5 Flash</option>
            <option value="auto">Auto Select</option>
          </select>
        </div>

        <div className="control-group">
          <label>Target Krea 2 Variant:</label>
          <select value={variant} onChange={(e) => setVariant(e.target.value)}>
            <option value="turbo">⚡ Turbo (Direct & Fast)</option>
            <option value="medium">🎨 Medium (Artistic & Expressive)</option>
            <option value="large">📷 Large (Photorealistic & Optics)</option>
          </select>
        </div>
      </div>

      <div className="action-buttons">
        <button onClick={handleDescribe} disabled={!selectedFile || loading} className="primary-btn">
          {loading ? 'Analyzing...' : 'Reverse Engineer Prompt'}
        </button>
        <button onClick={handleExtractStyle} disabled={!selectedFile || loading} className="secondary-btn">
          Extract Style to RAG
        </button>
      </div>

      {resultPrompt && (
        <div className="result-box">
          <h4>Generated Krea 2 Prompt:</h4>
          <p>{resultPrompt}</p>
          <button onClick={() => onInsertPrompt(resultPrompt)} className="apply-btn">
            Apply to Monaco Editor
          </button>
        </div>
      )}

      {extractedStyle && (
        <div className="style-box">
          <div className="style-box-header">
            <h4>Extracted Style Descriptors:</h4>
            <button
              className="save-rag-open-btn"
              onClick={() => setShowRAGModal(true)}
            >
              <BookmarkPlus size={14} />
              <span>Save to RAG Knowledge Vault</span>
            </button>
          </div>
          <pre>{JSON.stringify(extractedStyle, null, 2)}</pre>
        </div>
      )}

      {/* RAG Save Dialog / Modal */}
      {showRAGModal && (
        <div className="rag-save-modal-overlay" onClick={() => setShowRAGModal(false)}>
          <div className="rag-save-modal" onClick={e => e.stopPropagation()}>
            <div className="rag-modal-header">
              <div className="rag-modal-title">
                <BookOpen size={18} color="var(--accent-primary)" />
                <span>Save Style to RAG Knowledge Vault</span>
              </div>
              <button className="rag-modal-close" onClick={() => setShowRAGModal(false)}>
                <X size={16} />
              </button>
            </div>

            <div className="rag-modal-body">
              <div className="form-group">
                <label>Document Title</label>
                <input
                  type="text"
                  value={ragTitle}
                  onChange={e => setRagTitle(e.target.value)}
                  placeholder="e.g. Cyberpunk Rainy Neon Style"
                />
              </div>

              <div className="form-group">
                <label>Category</label>
                <select value={ragCategory} onChange={e => setRagCategory(e.target.value)}>
                  <option value="optics">Optics & Lenses</option>
                  <option value="lighting">Lighting & Mood</option>
                  <option value="palette">Color Palette</option>
                  <option value="model_guide">Model Guide</option>
                  <option value="anime_style">Anime Style</option>
                  <option value="general">General Aesthetics</option>
                </select>
              </div>

              <div className="form-group">
                <label>Tags (comma separated)</label>
                <input
                  type="text"
                  value={ragTags}
                  onChange={e => setRagTags(e.target.value)}
                  placeholder="e.g. lighting, volumetric, 85mm, cyber"
                />
              </div>

              {ragStatusMsg && (
                <div className={`rag-modal-status ${ragStatusMsg.startsWith('Error') ? 'error' : 'success'}`}>
                  {ragStatusMsg.startsWith('Error') ? null : <Check size={14} />}
                  <span>{ragStatusMsg}</span>
                </div>
              )}
            </div>

            <div className="rag-modal-actions">
              <button
                className="rag-modal-cancel"
                onClick={() => setShowRAGModal(false)}
                disabled={isSavingRAG}
              >
                Cancel
              </button>
              <button
                className="rag-modal-confirm"
                onClick={handleConfirmSaveRAG}
                disabled={isSavingRAG || !ragTitle.trim()}
              >
                {isSavingRAG ? 'Indexing...' : 'Save & Index Vector'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
