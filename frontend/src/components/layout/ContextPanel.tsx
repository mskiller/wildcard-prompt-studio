import React from 'react';
import { Bot } from 'lucide-react';
import './ContextPanel.css';

export const ContextPanel: React.FC = () => {
  return (
    <div className="context-panel">
      <div className="context-panel-header">
        <Bot size={16} />
        <span>AI Assistant</span>
      </div>
      <div className="context-panel-content">
        <div className="context-placeholder">
          AI Context & Simulation will appear here.
        </div>
      </div>
    </div>
  );
};
