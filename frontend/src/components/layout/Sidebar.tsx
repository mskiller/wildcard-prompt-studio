import React from 'react';
import { Folder, FileText, Settings, Sparkles } from 'lucide-react';
import './Sidebar.css';

export const Sidebar: React.FC = () => {
  return (
    <div className="sidebar-container">
      <div className="activity-bar">
        <div className="activity-item active" title="Explorer">
          <Folder size={24} strokeWidth={1.5} />
        </div>
        <div className="activity-item" title="Prompts">
          <FileText size={24} strokeWidth={1.5} />
        </div>
        <div className="activity-item" title="Wildcards">
          <Sparkles size={24} strokeWidth={1.5} />
        </div>
        <div className="spacer"></div>
        <div className="activity-item" title="Settings">
          <Settings size={24} strokeWidth={1.5} />
        </div>
      </div>
      <div className="sidebar">
        <div className="sidebar-header">
          EXPLORER
        </div>
        <div className="sidebar-content">
          <div className="sidebar-tree-item">
            <Folder size={16} className="tree-icon" />
            <span>Prompts</span>
          </div>
          <div className="sidebar-tree-item">
            <Folder size={16} className="tree-icon" />
            <span>Wildcards</span>
          </div>
        </div>
      </div>
    </div>
  );
};
