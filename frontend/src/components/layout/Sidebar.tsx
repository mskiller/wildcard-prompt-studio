import React, { useEffect, useState } from 'react';
import { Folder, FileText, Settings, Sparkles, UploadCloud, Tag, Search, Wand2, Grid, Activity, Award, Database, Eye, Cpu, Plus, RefreshCw, Download, Trash2 } from 'lucide-react';
import { useAppStore, ViewType } from '../../store/useAppStore';
import { usePromptStore } from '../../store/usePromptStore';
import { getPrompts, getWildcards, getTags, searchPrompts, createPrompt, createWildcard, deleteWildcard, deletePrompt } from '../../api';
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
  const appendTag = usePromptStore(state => state.appendTag);
  const showSubSidebar = SIDEBAR_VIEWS.includes(activeView);

  const [prompts, setPrompts] = useState<any[]>([]);
  const [wildcards, setWildcards] = useState<any[]>([]);
  const [tags, setTags] = useState<any[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [isSearching, setIsSearching] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  const handleQuickExport = (e: React.MouseEvent, name: string, content: string) => {
    e.stopPropagation();
    exportAsTxtFile(name || 'prompt', content || '');
  };

  useEffect(() => {
    let retryTimer: ReturnType<typeof setTimeout> | null = null;
    const loadData = async () => {
      setIsLoading(true);
      try {
        const [pRes, wRes, tRes] = await Promise.allSettled([
          getPrompts(), 
          getWildcards(), 
          getTags({ limit: 100 })
        ]);
        if (pRes.status === 'fulfilled') setPrompts(pRes.value);
        if (wRes.status === 'fulfilled') setWildcards(wRes.value);
        if (tRes.status === 'fulfilled') setTags(tRes.value);
      } catch (e) {
        console.error("Failed to fetch sidebar items", e);
      } finally {
        setIsLoading(false);
      }
    };
    loadData();

    return () => {
      if (retryTimer) clearTimeout(retryTimer);
    };
  }, [activeView, refreshKey]); // Reload data when switching views or on refresh trigger

  useEffect(() => {
    if (!searchQuery) {
      if (activeView === 'tags') {
        getTags({ limit: 100 }).then(setTags).catch(console.error);
      }
      return;
    }
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
      } else if (activeView === 'tags') {
        setIsSearching(true);
        try {
          const results = await getTags({ q: searchQuery, limit: 100 });
          setTags(results);
        } catch (e) {
          console.error("Tag search failed", e);
        } finally {
          setIsSearching(false);
        }
      }
    }, 400); // Debounce search
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

  const handleDeleteWildcard = async (e: React.MouseEvent, id: number, name: string) => {
    e.stopPropagation();
    if (window.confirm(`Delete wildcard "${name}"? This cannot be undone.`)) {
      try {
        await deleteWildcard(id);
        if (activeDocument?.type === 'wildcard' && activeDocument?.id === id) {
          setActiveDocument(null);
        }
        triggerRefresh();
      } catch (err: any) {
        alert(err.message || "Failed to delete wildcard");
      }
    }
  };

  const handleDeletePrompt = async (e: React.MouseEvent, id: number, name: string) => {
    e.stopPropagation();
    if (window.confirm(`Delete prompt "${name}"? This cannot be undone.`)) {
      try {
        await deletePrompt(id);
        if (activeDocument?.type === 'prompt' && activeDocument?.id === id) {
          setActiveDocument(null);
        }
        triggerRefresh();
      } catch (err: any) {
        alert(err.message || "Failed to delete prompt");
      }
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
                <span style={{ flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                  {p.name?.trim() || p.filename?.trim() || (p.content ? p.content.slice(0, 24) + '...' : 'Untitled Prompt')}
                </span>
                <div className="sidebar-item-actions">
                  <button 
                    className="icon-action-btn" 
                    onClick={(e) => handleQuickExport(e, p.name || p.filename, p.content)} 
                    title={`Export ${p.name || p.filename} as .txt`}
                  >
                    <Download size={13} />
                  </button>
                  <button 
                    className="icon-action-btn delete-btn" 
                    onClick={(e) => handleDeletePrompt(e, p.id, p.name || p.filename || 'Untitled Prompt')} 
                    title="Delete prompt"
                  >
                    <Trash2 size={13} />
                  </button>
                </div>
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
                <span style={{ flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                  {w.filename || w.name}
                </span>
                <div className="sidebar-item-actions">
                  <button 
                    className="icon-action-btn" 
                    onClick={(e) => handleQuickExport(e, w.name || w.filename, w.content)} 
                    title={`Export ${w.name || w.filename || 'wildcard'} as .txt`}
                  >
                    <Download size={13} />
                  </button>
                  <button 
                    className="icon-action-btn delete-btn" 
                    onClick={(e) => handleDeleteWildcard(e, w.id, w.filename || w.name || 'Wildcard')} 
                    title="Delete wildcard"
                  >
                    <Trash2 size={13} />
                  </button>
                </div>
              </div>
            ))}
          </>
        )}
        {activeView === 'tags' && tags.map(t => (
          <div 
            key={t.id} 
            className="sidebar-tree-item"
            onClick={() => appendTag(t.name)}
            title={`Click to insert "${t.name}" into active prompt`}
            style={{ cursor: 'pointer' }}
          >
            <Tag size={16} className="tree-icon" />
            <span style={{ flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{t.name}</span>
            {t.category && t.category !== 'General' && (
              <span style={{ fontSize: '10px', padding: '1px 6px', borderRadius: '4px', background: 'rgba(255,255,255,0.08)', color: 'var(--fg-muted)', marginLeft: 'auto' }}>
                {t.category}
              </span>
            )}
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
                <span style={{ flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                  {p.name?.trim() || p.filename?.trim() || (p.content ? p.content.slice(0, 24) + '...' : 'Untitled Prompt')}
                </span>
                <div className="sidebar-item-actions">
                  <button 
                    className="icon-action-btn" 
                    onClick={(e) => handleQuickExport(e, p.name || p.filename, p.content)} 
                    title={`Export ${p.name || p.filename || 'prompt'} as .txt`}
                  >
                    <Download size={13} />
                  </button>
                  <button 
                    className="icon-action-btn delete-btn" 
                    onClick={(e) => handleDeletePrompt(e, p.id, p.name || p.filename || 'Untitled Prompt')} 
                    title="Delete prompt"
                  >
                    <Trash2 size={13} />
                  </button>
                </div>
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
                <span style={{ flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                  {w.filename || w.name}
                </span>
                <div className="sidebar-item-actions">
                  <button 
                    className="icon-action-btn" 
                    onClick={(e) => handleQuickExport(e, w.name || w.filename, w.content)} 
                    title={`Export ${w.name || w.filename || 'wildcard'} as .txt`}
                  >
                    <Download size={13} />
                  </button>
                  <button 
                    className="icon-action-btn delete-btn" 
                    onClick={(e) => handleDeleteWildcard(e, w.id, w.filename || w.name || 'Wildcard')} 
                    title="Delete wildcard"
                  >
                    <Trash2 size={13} />
                  </button>
                </div>
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

