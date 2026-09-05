import React from 'react';
import './CanvasNodes.css';

export interface CanvasTextNodeProps {
  text: string;
  onChange: (text: string) => void;
  readOnly?: boolean;
}

export const CanvasTextNode: React.FC<CanvasTextNodeProps> = ({
  text = '',
  onChange,
  readOnly = false
}) => {
  const safeText = text || '';
  const trimmed = safeText.trim();
  const wordCount = trimmed ? trimmed.split(/\s+/).filter(Boolean).length : 0;
  const estimatedTokens = Math.ceil(wordCount * 1.3);
  const charCount = safeText.length;

  return (
    <div className="canvas-subnode canvas-text-node">
      <textarea
        className="text-node-textarea"
        value={safeText}
        onChange={e => onChange(e.target.value)}
        placeholder="Enter prompt phrase..."
        disabled={readOnly}
        readOnly={readOnly}
        rows={3}
        onMouseDown={e => e.stopPropagation()}
        aria-label="Prompt text"
      />

      <div className="text-node-meta">
        <span className="text-char-badge" title="Character count">
          {charCount} chars
        </span>
        <span className="text-token-badge" title="Estimated CLIP token count">
          ~{estimatedTokens} tokens
        </span>
      </div>
    </div>
  );
};
