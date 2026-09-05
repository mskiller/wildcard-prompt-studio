import React from 'react';
import { X, Plus, Sparkles } from 'lucide-react';
import './CanvasNodes.css';

export interface ChoiceOptionItem {
  id: string;
  text: string;
  weight: number;
}

export interface CanvasChoiceNodeProps {
  options: ChoiceOptionItem[];
  onChange: (options: ChoiceOptionItem[]) => void;
  readOnly?: boolean;
}

const generateOptionId = (): string => {
  return `opt_${Date.now().toString(36)}_${Math.random().toString(36).substring(2, 9)}`;
};

export const CanvasChoiceNode: React.FC<CanvasChoiceNodeProps> = ({
  options = [],
  onChange,
  readOnly = false
}) => {
  const handleTextChange = (id: string, newText: string) => {
    onChange(options.map(opt => (opt.id === id ? { ...opt, text: newText } : opt)));
  };

  const handleWeightChange = (id: string, rawWeight: number) => {
    const rounded = Math.round(rawWeight * 10) / 10;
    onChange(options.map(opt => (opt.id === id ? { ...opt, weight: rounded } : opt)));
  };

  const handleRemoveOption = (id: string) => {
    onChange(options.filter(opt => opt.id !== id));
  };

  const handleAddOption = () => {
    const newOption: ChoiceOptionItem = {
      id: generateOptionId(),
      text: 'new option',
      weight: 1.0
    };
    onChange([...options, newOption]);
  };

  return (
    <div className="canvas-subnode canvas-choice-node">
      <div className="choice-options-list">
        {options.map(opt => {
          const formattedWeight = `${Math.round(opt.weight * 10) / 10}×`;

          const wildcards = Array.from(opt.text.matchAll(/__([a-zA-Z0-9_\-/\\]+)__/g)).map(m => m[1]);

          return (
            <div key={opt.id} className="choice-option-row">
              <div className="choice-option-header">
                <input
                  type="text"
                  className="choice-option-input"
                  value={opt.text}
                  onChange={e => handleTextChange(opt.id, e.target.value)}
                  placeholder="Option text..."
                  disabled={readOnly}
                  readOnly={readOnly}
                  onMouseDown={e => e.stopPropagation()}
                />
                <button
                  type="button"
                  className="choice-remove-btn"
                  onClick={() => handleRemoveOption(opt.id)}
                  disabled={readOnly}
                  title="Remove option"
                  aria-label="Remove option"
                  onMouseDown={e => e.stopPropagation()}
                >
                  <X size={13} />
                </button>
              </div>

              {wildcards.length > 0 && (
                <div className="choice-option-wildcard-tags">
                  {wildcards.map((wc, wIdx) => (
                    <span key={wIdx} className="choice-wildcard-badge" title={`Parsed wildcard: __${wc}__`}>
                      <Sparkles size={10} /> __{wc}__
                    </span>
                  ))}
                </div>
              )}

              <div className="choice-weight-row">
                <span className="choice-weight-label">Weight</span>
                <input
                  type="range"
                  className="choice-weight-slider"
                  min="0.1"
                  max="3.0"
                  step="0.1"
                  value={opt.weight}
                  onChange={e => handleWeightChange(opt.id, parseFloat(e.target.value))}
                  disabled={readOnly}
                  onMouseDown={e => e.stopPropagation()}
                />
                <span className="choice-weight-badge">{formattedWeight}</span>
              </div>
            </div>
          );
        })}

        {options.length === 0 && (
          <div className="choice-empty-state">No choice options defined yet.</div>
        )}
      </div>

      <button
        type="button"
        className="choice-add-btn"
        onClick={handleAddOption}
        disabled={readOnly}
        onMouseDown={e => e.stopPropagation()}
      >
        <Plus size={13} />
        <span>+ Add Option</span>
      </button>
    </div>
  );
};
