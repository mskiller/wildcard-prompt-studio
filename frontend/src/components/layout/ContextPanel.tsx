import React, { useState } from 'react';
import { Bot, Play } from 'lucide-react';
import './ContextPanel.css';
import { usePromptStore } from '../../store/usePromptStore';
import { expandPrompt } from '../../api';

export const ContextPanel: React.FC = () => {
  const { promptText, expandedPromptText, setExpandedPromptText } = usePromptStore();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

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

  return (
    <div className="context-panel">
      <div className="context-panel-header">
        <Bot size={16} />
        <span>AI Assistant</span>
      </div>
      <div className="context-panel-content">
        <button 
          className="simulate-btn" 
          onClick={handleSimulate}
          disabled={loading || !promptText.trim()}
        >
          <Play size={14} />
          {loading ? 'Simulating...' : 'Simulate / Expand'}
        </button>

        {error && (
          <div className="error-message">
            {error}
          </div>
        )}

        {expandedPromptText ? (
          <div className="expanded-result">
            <div className="expanded-result-title">Expanded Prompt</div>
            <div className="expanded-result-content">
              {expandedPromptText}
            </div>
          </div>
        ) : (
          <div className="context-placeholder">
            AI Context & Simulation will appear here.
          </div>
        )}
      </div>
    </div>
  );
};
