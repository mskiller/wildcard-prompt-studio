import React, { useState } from 'react';
import { FileText, Sparkles, Cpu, Folder, MoreHorizontal, Wand2, Tag, Grid, Activity, Award, Database, Eye, Settings, UploadCloud } from 'lucide-react';
import { useAppStore, ViewType } from '../../store/useAppStore';
import { BottomSheet } from '../common/BottomSheet';
import './MobileBottomNav.css';

export const MobileBottomNav: React.FC = () => {
  const { activeView, setActiveView } = useAppStore();
  const [isMoreOpen, setIsMoreOpen] = useState(false);

  const primaryItems: { view: ViewType; label: string; icon: React.ReactNode }[] = [
    { view: 'prompts', label: 'Prompts', icon: <FileText size={20} /> },
    { view: 'anima', label: 'ANIMA', icon: <Sparkles size={20} style={{ color: '#ec4899' }} /> },
    { view: 'comfyui', label: 'ComfyUI', icon: <Cpu size={20} /> },
    { view: 'gallery', label: 'Gallery', icon: <Folder size={20} style={{ color: '#fab387' }} /> },
  ];

  const moreItems: { view: ViewType; label: string; icon: React.ReactNode }[] = [
    { view: 'explorer', label: 'Explorer', icon: <Folder size={22} /> },
    { view: 'wildcards', label: 'Wildcards', icon: <Sparkles size={22} /> },
    { view: 'tags', label: 'Tags', icon: <Tag size={22} /> },
    { view: 'krea2', label: 'Krea 2', icon: <Wand2 size={22} /> },
    { view: 'vision', label: 'Vision', icon: <Eye size={22} /> },
    { view: 'matrix', label: 'Matrix', icon: <Grid size={22} /> },
    { view: 'simulator', label: 'Simulator', icon: <Activity size={22} /> },
    { view: 'aesthetic', label: 'Aesthetic', icon: <Award size={22} /> },
    { view: 'rag', label: 'RAG Knowledge', icon: <Database size={22} /> },
    { view: 'import', label: 'Import', icon: <UploadCloud size={22} /> },
    { view: 'settings', label: 'Settings', icon: <Settings size={22} /> },
  ];

  const handleSelectView = (view: ViewType) => {
    setActiveView(view);
    setIsMoreOpen(false);
  };

  return (
    <>
      <nav className="mobile-bottom-nav">
        {primaryItems.map((item) => (
          <button
            key={item.view}
            className={`mobile-nav-item ${activeView === item.view ? 'active' : ''}`}
            onClick={() => handleSelectView(item.view)}
          >
            {item.icon}
            <span>{item.label}</span>
          </button>
        ))}
        <button
          className={`mobile-nav-item ${isMoreOpen ? 'active' : ''}`}
          onClick={() => setIsMoreOpen(true)}
        >
          <MoreHorizontal size={20} />
          <span>More</span>
        </button>
      </nav>

      <BottomSheet isOpen={isMoreOpen} onClose={() => setIsMoreOpen(false)} title="Studio Tools">
        <div className="more-tools-grid">
          {moreItems.map((item) => (
            <button
              key={item.view}
              className="more-tool-card"
              onClick={() => handleSelectView(item.view)}
            >
              {item.icon}
              <span>{item.label}</span>
            </button>
          ))}
        </div>
      </BottomSheet>
    </>
  );
};
