import React, { useEffect, useState } from 'react';
import { Folder, FileText, Settings, Sparkles, UploadCloud, Tag, Search, Wand2, Grid, Activity, Award, Database, Eye, Cpu, Plus, RefreshCw, Download } from 'lucide-react';
import { useAppStore, ViewType } from '../../store/useAppStore';
import { getPrompts, getWildcards, getTags, searchPrompts, createPrompt, createWildcard } from '../../api';
import { useDeviceDetect } from '../../store/useDeviceDetect';
import { BottomSheet } from '../common/BottomSheet';
import { exportAsTxtFile } from '../../utils/fileExporter';
import './Sidebar.css';

const SIDEBAR_VIEWS: ViewType[] = ['explorer', 'prompts', 'wildcards', 'tags'];

export const Sidebar: React.FC = () => {
  const { 
    activeView, 
    setActiveView, 
    activeDocument, 
    setActiveDocument, 
    refreshKey, 
    triggerRefresh,
    isMobileMenuOpen,
    setMobileMenuOpen
  } = useAppStore();
  const { isMobile } = useDeviceDetect();
  const showSubSidebar = SIDEBAR_VIEWS.includes(activeView);

  const [prompts, setPrompts] = useState<any[]>([]);
  const [wildcards, setWildcards] = useState<any[]>([]);
  const [tags, setTags] = useState<any[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [isSearching, setIsSearching] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  const handleQuickExport = (e: React.MouseEvent, name: string, content: string) => {
    e.stopPropagation();
    exportAsTxtFile(name, content || '');
  };

  useEffect(() => {
    let retryTimer: ReturnType<typeof setTimeout> | null = null;
    let attempts = 0;

    const loadData = async () => {
      setIsLoading(true);
      try {
        const [pRes, wRes, tRes] = await Promise.allSettled([getPrompts(), getWildcards(), getTags()]);
        let loadedSuccess = false;

        if (pRes.status === 'fulfilled' && Array.isArray(pRes.value)) {
          setPrompts(pRes.value);
          if (pRes.value.length > 0) loadedSuccess = true;
        }
        if (wRes.status === 'fulfilled' && Array.isArray(wRes.value)) {
          setWildcards(wRes.value);
          if (wRes.value.length > 0) loadedSuccess = true;
        }
        if (tRes.status === 'fulfilled' && Array.isArray(tRes.value)) {
          setTags(tRes.value);
        }

        // If backend was still starting up during initial load, retry automatically
        if (!loadedSuccess && attempts < 3) {
          attempts += 1;
          retryTimer = setTimeout(loadData, 2000);
        }
      } catch (err) {
        console.error("Failed to load sidebar data", err);
        if (attempts < 3) {
          attempts += 1;
          retryTimer = setTimeout(loadData, 2000);
        }
      } finally {
        setIsLoading(false);
      }
    };

    if (!searchQuery) {
      loadData();
    }

    return () => {
      if (retryTimer) clearTimeout(retryTimer);
    };
  }, [activeView, searchQuery, refreshKey]); // Reload data when switching views or on refresh trigger

  useEffect(() => {
    if (!searchQuery) return;
    const timeoutId = setTimeout(async () => {
      if (activeView === 'prompts') {
        setIsSearching(true);
        try {
          const results = await searchPrompts(searchQuery);
          setPrompts(results);
        } catch (e) {
          console.error("Search failed", e);
        } finally {
          setIsSearching(false);
        }
      }
    }, 500); // Debounce search
    return () => clearTimeout(timeoutId);
  }, [searchQuery, activeView]);

  const handleIconClick = (view: ViewType) => {
    setActiveView(view);
  };

  const handleItemClick = (type: 'prompt' | 'wildcard', item: any) => {
    setActiveDocument({
      type,
      id: item.id,
      name: item.name || item.filename,
      content: item.content || ''
    });
    if (isMobile) {
      setMobileMenuOpen(false);
    }
  };

  const handleNewPrompt = async () => {
    const name = prompt("Enter prompt name:", "New Prompt");
    if (!name) return;
    try {
      const created = await createPrompt({ name, content: "" });
      triggerRefresh();
      handleItemClick('prompt', created);
    } catch (err: any) {
      alert(err.message || "Failed to create prompt");
    }
  };

  const handleNewWildcard = async () => {
    const filename = prompt("Enter wildcard filename (e.g. colors.txt):", "new_wildcard.txt");
    if (!filename) return;
    try {
      const created = await createWildcard({ filename, content: "" });
      triggerRefresh();
      handleItemClick('wildcard', created);
    } catch (err: any) {
      alert(err.message || "Failed to create wildcard");
    }
  };

  const renderSidebarContent = () => (
    <>
      <div className="sidebar-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <span>{activeView.toUpperCase()}</span>
        <button 
          className="icon-action-btn" 
          onClick={triggerRefresh} 
          title="Refresh Explorer Data"
          style={{ background: 'transparent', border: 'none', color: 'var(--fg-muted)', cursor: 'pointer', padding: '2px 4px' }}
        >
          <RefreshCw size={14} className={isLoading ? 'spin' : ''} />
        </button>
      </div>
      {activeView === 'prompts' && (
        <div className="sidebar-search">
          <Search size={16} className={`search-icon ${isSearching ? 'spin' : ''}`} />
          <input 
            type="text" 
            placeholder="Semantic Search..." 
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="search-input"
          />
        </div>
      )}
      <div className="sidebar-content">
        {activeView === 'prompts' && (
          <>
            <div style={{ display: 'flex', justifyContent: 'flex-end', padding: '4px 16px' }}>
              <button className="sidebar-add-btn" onClick={handleNewPrompt} title="New Prompt">
                <Plus size={14} /> New Prompt
              </button>
            </div>
            {prompts.map(p => (
              <div 
                key={p.id} 
                className={`sidebar-tree-item ${activeDocument?.type === 'prompt' && activeDocument?.id === p.id ? 'active' : ''}`} 
                onClick={() => handleItemClick('prompt', p)}
              >
                <FileText size={16} className="tree-icon" />
                <span>{p.name?.trim() || p.filename?.trim() || (p.content ? p.content.slice(0, 24) + '...' : 'Untitled Prompt')}</span>
                <button 
                  className="icon-action-btn" 
                  onClick={(e) => handleQuickExport(e, p.name || p.filename, p.content)} 
                  title={`Export ${p.name || p.filename} as .txt`}
                  style={{ background: 'transparent', border: 'none', color: 'var(--fg-muted)', cursor: 'pointer', padding: '2px 4px', marginLeft: 'auto' }}
                >
                  <Download size={13} />
                </button>
              </div>
            ))}
          </>
        )}
        {activeView === 'wildcards' && (
          <>
            <div style={{ display: 'flex', justifyContent: 'flex-end', padding: '4px 16px' }}>
              <button className="sidebar-add-btn" onClick={handleNewWildcard} title="New Wildcard">
                <Plus size={14} /> New Wildcard
              </button>
            </div>
            {wildcards.map(w => (
              <div 
                key={w.id} 
                className={`sidebar-tree-item ${activeDocument?.type === 'wildcard' && activeDocument?.id === w.id ? 'active' : ''}`} 
                onClick={() => handleItemClick('wildcard', w)}
              >
                <Sparkles size={16} className="tree-icon" />
                <span>{w.filename || w.name}</span>
                <button 
                  className="icon-action-btn" 
                  onClick={(e) => handleQuickExport(e, w.name || w.filename, w.content)} 
                  title={`Export ${w.name || w.filename} as .txt`}
                  style={{ background: 'transparent', border: 'none', color: 'var(--fg-muted)', cursor: 'pointer', padding: '2px 4px', marginLeft: 'auto' }}
                >
                  <Download size={13} />
                </button>
              </div>
            ))}
          </>
        )}
        {activeView === 'tags' && tags.map(t => (
          <div key={t.id} className="sidebar-tree-item">
            <Tag size={16} className="tree-icon" />
            <span>{t.name}</span>
          </div>
        ))}
        {activeView === 'explorer' && (
          <>
            <div className="sidebar-tree-folder" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span>Prompts</span>
              <button className="icon-action-btn" onClick={handleNewPrompt} title="New Prompt">
                <Plus size={14} />
              </button>
            </div>
            {prompts.map(p => (
              <div 
                key={`exp-p-${p.id}`} 
                className={`sidebar-tree-item nested ${activeDocument?.type === 'prompt' && activeDocument?.id === p.id ? 'active' : ''}`} 
                onClick={() => handleItemClick('prompt', p)}
              >
                <FileText size={16} className="tree-icon" />
                <span>{p.name?.trim() || p.filename?.trim() || (p.content ? p.content.slice(0, 24) + '...' : 'Untitled Prompt')}</span>
                <button 
                  className="icon-action-btn" 
                  onClick={(e) => handleQuickExport(e, p.name || p.filename, p.content)} 
                  title={`Export ${p.name || p.filename} as .txt`}
                  style={{ background: 'transparent', border: 'none', color: 'var(--fg-muted)', cursor: 'pointer', padding: '2px 4px', marginLeft: 'auto' }}
                >
                  <Download size={13} />
                </button>
              </div>
            ))}
            <div className="sidebar-tree-folder" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '12px' }}>
              <span>Wildcards</span>
              <button className="icon-action-btn" onClick={handleNewWildcard} title="New Wildcard">
                <Plus size={14} />
              </button>
            </div>
            {wildcards.map(w => (
              <div 
                key={`exp-w-${w.id}`} 
                className={`sidebar-tree-item nested ${activeDocument?.type === 'wildcard' && activeDocument?.id === w.id ? 'active' : ''}`} 
                onClick={() => handleItemClick('wildcard', w)}
              >
                <Sparkles size={16} className="tree-icon" />
                <span>{w.filename || w.name}</span>
                <button 
                  className="icon-action-btn" 
                  onClick={(e) => handleQuickExport(e, w.name || w.filename, w.content)} 
                  title={`Export ${w.name || w.filename} as .txt`}
                  style={{ background: 'transparent', border: 'none', color: 'var(--fg-muted)', cursor: 'pointer', padding: '2px 4px', marginLeft: 'auto' }}
                >
                  <Download size={13} />
                </button>
              </div>
            ))}
          </>
        )}
      </div>
    </>
  );

  if (isMobile) {
    return (
      <BottomSheet isOpen={isMobileMenuOpen} onClose={() => setMobileMenuOpen(false)} title="Explorer & Documents">
        <div className="mobile-sidebar-inner">
          {renderSidebarContent()}
        </div>
      </BottomSheet>
    );
  }

  return (
    <div className="sidebar-container">
      <div className="activity-bar">
        <div 
          className={`activity-item ${activeView === 'explorer' ? 'active' : ''}`} 
          title="Explorer"
          onClick={() => handleIconClick('explorer')}
        >
          <Folder size={24} strokeWidth={1.5} />
        </div>
        <div 
          className={`activity-item ${activeView === 'prompts' ? 'active' : ''}`} 
          title="Prompts"
          onClick={() => handleIconClick('prompts')}
        >
          <FileText size={24} strokeWidth={1.5} />
        </div>
        <div 
          className={`activity-item ${activeView === 'wildcards' ? 'active' : ''}`} 
          title="Wildcards"
          onClick={() => handleIconClick('wildcards')}
        >
          <Sparkles size={24} strokeWidth={1.5} />
        </div>
        <div 
          className={`activity-item ${activeView === 'tags' ? 'active' : ''}`} 
          title="Tags"
          onClick={() => handleIconClick('tags')}
        >
          <Tag size={24} strokeWidth={1.5} />
        </div>
        <div 
          className={`activity-item ${activeView === 'krea2' ? 'active' : ''}`} 
          title="Krea 2 Studio"
          onClick={() => handleIconClick('krea2')}
        >
          <Wand2 size={24} strokeWidth={1.5} />
        </div>
        <div 
          className={`activity-item ${activeView === 'anima' ? 'active' : ''}`} 
          title="ANIMA Studio Engine"
          onClick={() => handleIconClick('anima')}
        >
          <Sparkles size={24} strokeWidth={1.5} style={{ color: '#ec4899' }} />
        </div>
        <div 
          className={`activity-item ${activeView === 'vision' ? 'active' : ''}`} 
          title="Vision Feedback & Image-to-Prompt"
          onClick={() => handleIconClick('vision')}
        >
          <Eye size={24} strokeWidth={1.5} />
        </div>
        <div 
          className={`activity-item ${activeView === 'comfyui' ? 'active' : ''}`} 
          title="Live ComfyUI Stream & Controller"
          onClick={() => handleIconClick('comfyui')}
        >
          <Cpu size={24} strokeWidth={1.5} />
        </div>
        <div 
          className={`activity-item ${activeView === 'gallery' ? 'active' : ''}`} 
          title="Generated Images Gallery"
          onClick={() => handleIconClick('gallery')}
        >
          <Folder size={24} strokeWidth={1.5} style={{ color: '#fab387' }} />
        </div>
        <div 
          className={`activity-item ${activeView === 'matrix' ? 'active' : ''}`} 
          title="Matrix Sweep"
          onClick={() => handleIconClick('matrix')}
        >
          <Grid size={24} strokeWidth={1.5} />
        </div>
        <div 
          className={`activity-item ${activeView === 'simulator' ? 'active' : ''}`} 
          title="AST Graph Simulator"
          onClick={() => handleIconClick('simulator')}
        >
          <Activity size={24} strokeWidth={1.5} />
        </div>
        <div 
          className={`activity-item ${activeView === 'aesthetic' ? 'active' : ''}`} 
          title="Aesthetic Ranker & Hub"
          onClick={() => handleIconClick('aesthetic')}
        >
          <Award size={24} strokeWidth={1.5} />
        </div>
        <div 
          className={`activity-item ${activeView === 'rag' ? 'active' : ''}`} 
          title="RAG Vector Knowledge Base"
          onClick={() => handleIconClick('rag')}
        >
          <Database size={24} strokeWidth={1.5} />
        </div>
        <div 
          className={`activity-item ${activeView === 'import' ? 'active' : ''}`} 
          title="Import"
          onClick={() => handleIconClick('import')}
        >
          <UploadCloud size={24} strokeWidth={1.5} />
        </div>

        <div className="spacer"></div>

        <div 
          className={`activity-item ${activeView === 'settings' ? 'active' : ''}`} 
          title="Settings"
          onClick={() => handleIconClick('settings')}
        >
          <Settings size={24} strokeWidth={1.5} />
        </div>
      </div>
      {showSubSidebar && (
        <div className="sidebar">
          {renderSidebarContent()}
        </div>
      )}
    </div>
  );
};

