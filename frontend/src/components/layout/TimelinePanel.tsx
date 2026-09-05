import React from 'react';
import { History, GitCommit } from 'lucide-react';
import { usePromptStore } from '../../store/usePromptStore';
import './TimelinePanel.css';

export const TimelinePanel: React.FC = () => {
  const { currentPrompt } = usePromptStore();

  if (!currentPrompt) return null;

  return (
    <div className="timeline-panel glass-panel">
      <div className="timeline-header">
        <History size={16} />
        <span>Version History</span>
      </div>
      
      <div className="timeline-content">
        {currentPrompt.versions?.map((version: any, idx: number) => (
          <div key={version.version_id || idx} className="timeline-item">
            <div className="timeline-node">
              <GitCommit size={14} />
            </div>
            <div className="timeline-details">
              <div className="timeline-title">Version {version.version_number || idx + 1}</div>
              <div className="timeline-message">{version.commit_message || "Auto-saved version"}</div>
              <div className="timeline-date">
                {new Date(version.created_at || Date.now()).toLocaleString()}
              </div>
            </div>
          </div>
        ))}
        {(!currentPrompt.versions || currentPrompt.versions.length === 0) && (
          <div className="timeline-empty">No versions found</div>
        )}
      </div>
    </div>
  );
};
