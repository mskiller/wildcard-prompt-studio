import React, { useState } from 'react';
import { useAppStore } from '../../store/useAppStore';
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

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      setSelectedFile(file);
      setPreviewUrl(URL.createObjectURL(file));
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
      formData.append('index_rag', 'true');

      const response = await fetch('/api/v1/ai/vision/extract-style', {
        method: 'POST',
        body: formData
      });
      const data = await response.json();
      if (data.descriptors) {
        setExtractedStyle(data.descriptors);
        if (onIndexRAG) {
          onIndexRAG('Extracted Vision Style', JSON.stringify(data.descriptors));
        }
      }
    } catch (err) {
      console.error('Vision style extraction error:', err);
    } finally {
      setLoading(false);
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
          <h4>Extracted Style Descriptors:</h4>
          <pre>{JSON.stringify(extractedStyle, null, 2)}</pre>
        </div>
      )}
    </div>
  );
};
