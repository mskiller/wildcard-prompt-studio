import React from 'react';
import { ExternalLink } from 'lucide-react';
import { WildcardSearchPicker } from '../WildcardSearchPicker';
import './CanvasNodes.css';

export interface CanvasWildcardNodeProps {
  name: string;
  availableWildcards?: string[];
  sampleValues?: string[];
  onChange: (name: string) => void;
  onInspect?: (name: string) => void;
  readOnly?: boolean;
}

export const CanvasWildcardNode: React.FC<CanvasWildcardNodeProps> = ({
  name,
  availableWildcards = [],
  sampleValues,
  onChange,
  onInspect,
  readOnly = false
}) => {
  const hasAvailable = availableWildcards && availableWildcards.length > 0;

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    onChange(e.target.value);
  };

  const handleInspect = () => {
    if (onInspect && name.trim()) {
      onInspect(name);
    }
  };

  return (
    <div className="canvas-subnode canvas-wildcard-node">
      {hasAvailable && (
        <div className="wildcard-select-container">
          <WildcardSearchPicker
            variant="inspector"
            value={name}
            availableWildcards={availableWildcards}
            placeholder="-- Search & choose wildcard --"
            onSelect={onChange}
            readOnly={readOnly}
          />
        </div>
      )}

      <div className="wildcard-input-row">
        <div className="wildcard-input-wrapper">
          <input
            type="text"
            className="wildcard-text-input"
            value={name}
            onChange={handleInputChange}
            placeholder="Wildcard file (e.g. colors/warm)..."
            disabled={readOnly}
            readOnly={readOnly}
            onMouseDown={e => e.stopPropagation()}
            aria-label="Wildcard name"
          />
        </div>

        {onInspect && (
          <button
            type="button"
            className="wildcard-inspect-btn"
            onClick={handleInspect}
            disabled={readOnly || !name.trim()}
            title={name.trim() ? `Inspect wildcard "${name}"` : 'Enter wildcard name to inspect'}
            aria-label="Inspect wildcard"
            onMouseDown={e => e.stopPropagation()}
          >
            <ExternalLink size={13} />
            <span>Inspect</span>
          </button>
        )}
      </div>

      {sampleValues && sampleValues.length > 0 && (
        <div className="wildcard-samples-container">
          <span className="wildcard-samples-label">Sample Values:</span>
          <div className="wildcard-samples-list">
            {sampleValues.map((sample, idx) => (
              <span
                key={`${sample}-${idx}`}
                className="wildcard-sample-pill"
                title={`Sample: ${sample}`}
                onMouseDown={e => e.stopPropagation()}
              >
                {sample}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
