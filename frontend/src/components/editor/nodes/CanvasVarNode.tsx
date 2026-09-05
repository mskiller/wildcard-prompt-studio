import React from 'react';
import './CanvasNodes.css';

export interface CanvasVarNodeProps {
  varName: string;
  value?: string;
  onChange: (varName: string, value?: string) => void;
  readOnly?: boolean;
}

export const CanvasVarNode: React.FC<CanvasVarNodeProps> = ({
  varName = '',
  value,
  onChange,
  readOnly = false
}) => {
  const handleNameChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    onChange(e.target.value, value);
  };

  const handleNameBlur = () => {
    if (varName && !varName.startsWith('$')) {
      onChange(`$${varName}`, value);
    }
  };

  const handleValueChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    onChange(varName, e.target.value);
  };

  return (
    <div className="canvas-subnode canvas-var-node">
      <div className="var-field-group">
        <label className="var-field-label">Variable Name ($name)</label>
        <div className="var-input-wrapper">
          <input
            type="text"
            className="var-name-input"
            value={varName}
            onChange={handleNameChange}
            onBlur={handleNameBlur}
            placeholder="$name"
            disabled={readOnly}
            readOnly={readOnly}
            onMouseDown={e => e.stopPropagation()}
            aria-label="Variable name"
          />
        </div>
      </div>

      <div className="var-field-group">
        <label className="var-field-label">Value (optional)</label>
        <input
          type="text"
          className="var-value-input"
          value={value ?? ''}
          onChange={handleValueChange}
          placeholder="Optional variable value..."
          disabled={readOnly}
          readOnly={readOnly}
          onMouseDown={e => e.stopPropagation()}
          aria-label="Variable value"
        />
      </div>
    </div>
  );
};
