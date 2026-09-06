import React, { useState, useEffect, useRef } from 'react';
import { usePromptStore } from '../../store/usePromptStore';
import { useAppStore } from '../../store/useAppStore';
import { MonacoPromptEditor } from './MonacoPromptEditor';
import { VisualBuilder } from './VisualBuilder';
import { GalleryView } from '../gallery/GalleryView';
import { GenerationSettings } from './GenerationSettings';
import { generateImage, createImage, updatePrompt, updateWildcard, createPrompt, createWildcard, deleteWildcard, deletePrompt, GenerationSettings as ISettings } from '../../api';
import { Code, LayoutTemplate, FileText, Sparkles, Image as ImageIcon, SlidersHorizontal, Wand2, Save, MessageSquare, Download, Trash2 } from 'lucide-react';
import { exportAsTxtFile } from '../../utils/fileExporter';
import { useDeviceDetect } from '../../store/useDeviceDetect';
import { MobilePromptToolbar } from './MobilePromptToolbar';
import './PromptEditor.css';

export const PromptEditor: React.FC = () => {
  const { isMobile } = useDeviceDetect();
  const { promptText, setPromptText } = usePromptStore();
  const { activeDocument, comfyUIUrl, setActiveView, setActiveDocument, triggerRefresh, rightPanelTab, setRightPanelTab } = useAppStore();
  const [viewMode, setViewMode] = useState<'code' | 'visual' | 'gallery'>('code');
  const [showSettings, setShowSettings] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);
  const [isSaving, setIsSaving] = useState(false);

  const handleInsertText = (text: string) => {
    setPromptText(
      promptText
        ? promptText.endsWith(' ') || promptText.endsWith(',')
          ? `${promptText}${text}`
          : `${promptText}, ${text}`
        : text
    );
  };
  
  // Non-blocking toast state
  const [toast, setToast] = useState<{ message: string; type: 'success' | 'error' | 'info' } | null>(null);
  const toastTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Non-blocking save modal state (used when saving an untitled document)
  const [isSaveModalOpen, setIsSaveModalOpen] = useState(false);
  const [newDocType, setNewDocType] = useState<'prompt' | 'wildcard'>('prompt');
  const [newDocName, setNewDocName] = useState('New Prompt');

  const showToast = (message: string, type: 'success' | 'error' | 'info' = 'info') => {
    if (toastTimerRef.current) clearTimeout(toastTimerRef.current);
    setToast({ message, type });
    toastTimerRef.current = setTimeout(() => {
      setToast(null);
    }, 3500);
  };

  useEffect(() => {
    return () => {
      if (toastTimerRef.current) clearTimeout(toastTimerRef.current);
    };
  }, []);

  const [genSettings, setGenSettings] = useState<ISettings>({
    model: 'v1-5-pruned-emaonly.safetensors',
    sampler: 'euler',
    scheduler: 'normal',
    steps: 20,
    cfg: 7.0,
    width: 1024,
    height: 1024
  });

  useEffect(() => {
    if (activeDocument) {
      setPromptText(activeDocument.content || '');
    }
  }, [activeDocument, setPromptText]);

  const handleEditorChange = (value: string | undefined) => {
    if (value !== undefined) {
      setPromptText(value);
    }
  };

  const handleSave = async () => {
    if (!activeDocument) {
      // Open non-blocking save modal for untitled documents
      setNewDocType('prompt');
      setNewDocName('New Prompt');
      setIsSaveModalOpen(true);
      return;
    }

    setIsSaving(true);
    try {
      if (activeDocument.type === 'prompt') {
        await updatePrompt(activeDocument.id, { content: promptText });
      } else if (activeDocument.type === 'wildcard') {
        await updateWildcard(activeDocument.id, { content: promptText });
      }
      setActiveDocument({
        ...activeDocument,
        content: promptText
      });
      showToast(`Saved ${activeDocument.name}!`, 'success');
      triggerRefresh();
    } catch (err: unknown) {
      console.error(err);
      const errorMsg = err instanceof Error ? err.message : 'Unknown error';
      showToast(`Save failed: ${errorMsg}`, 'error');
    } finally {
      setIsSaving(false);
    }
  };

  const handleConfirmCreateSave = async () => {
    if (!newDocName.trim()) return;
    setIsSaving(true);
    try {
      if (newDocType === 'prompt') {
        const created = await createPrompt({ name: newDocName.trim(), content: promptText });
        setActiveDocument({ type: 'prompt', id: created.id, name: created.name, content: created.content });
        showToast(`Created prompt "${created.name}"!`, 'success');
      } else {
        const filename = newDocName.trim().endsWith('.txt') ? newDocName.trim() : `${newDocName.trim()}.txt`;
        const created = await createWildcard({ filename, content: promptText });
        setActiveDocument({ type: 'wildcard', id: created.id, name: created.filename, content: created.content });
        showToast(`Created wildcard "${created.filename}"!`, 'success');
      }
      triggerRefresh();
      setIsSaveModalOpen(false);
    } catch (err: unknown) {
      console.error(err);
      const errorMsg = err instanceof Error ? err.message : 'Unknown error';
      showToast(`Save failed: ${errorMsg}`, 'error');
    } finally {
      setIsSaving(false);
    }
  };

  const handleExportTxt = () => {
    if (!promptText) return;
    const defaultName = activeDocument ? activeDocument.name : 'prompt_export.txt';
    exportAsTxtFile(defaultName, promptText);
    showToast(`Exported ${defaultName.endsWith('.txt') ? defaultName : defaultName + '.txt'}!`, 'success');
  };

  const handleGenerate = async () => {
    if (!promptText) return;
    setIsGenerating(true);
    try {
      const response = await generateImage(promptText, comfyUIUrl, genSettings);
      showToast(`Prompt queued! Prompt ID: ${response.prompt_id}`, 'success');
      
      if (activeDocument && activeDocument.type === 'prompt') {
        await createImage({
          filename: `WildcardStudio_${response.prompt_id}_00001_.png`,
          prompt_id: activeDocument.id,
          seed: genSettings.seed,
          cfg_scale: genSettings.cfg,
          steps: genSettings.steps,
          sampler_name: genSettings.sampler,
          width: genSettings.width,
          height: genSettings.height,
          comfy_workflow_id: response.prompt_id
        });
      }
      
      setViewMode('gallery');
    } catch (err: unknown) {
      console.error(err);
      const errorMsg = err instanceof Error ? err.message : 'Unknown error';
      showToast(`Failed to generate image: ${errorMsg}`, 'error');
    } finally {
      setIsGenerating(false);
    }
  };

  const handleDeleteActiveDoc = async () => {
    if (!activeDocument) return;
    const docTypeLabel = activeDocument.type === 'wildcard' ? 'wildcard' : 'prompt';
    if (window.confirm(`Are you sure you want to delete ${docTypeLabel} "${activeDocument.name}"? This cannot be undone.`)) {
      try {
        if (activeDocument.type === 'wildcard') {
          await deleteWildcard(activeDocument.id);
        } else if (activeDocument.type === 'prompt') {
          await deletePrompt(activeDocument.id);
        }
        showToast(`Deleted ${activeDocument.name}!`, 'success');
        setActiveDocument(null);
        setPromptText('');
        triggerRefresh();
      } catch (err: unknown) {
        const errorMsg = err instanceof Error ? err.message : 'Delete failed';
        showToast(`Failed to delete: ${errorMsg}`, 'error');
      }
    }
  };

  return (
    <div className="prompt-editor-container" style={{ display: 'flex', height: '100%', position: 'relative' }}>
      {toast && (
        <div className={`editor-toast toast-${toast.type}`}>
          <span>{toast.message}</span>
        </div>
      )}

      <div style={{ flexGrow: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
        <div className="editor-toolbar glass-panel">
          <div className="active-doc-indicator" style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--fg-primary)', fontWeight: 600, padding: '0 12px' }}>
            {activeDocument?.type === 'prompt' ? <FileText size={16} /> : activeDocument?.type === 'wildcard' ? <Sparkles size={16} /> : null}
            <span>{activeDocument?.name || 'Untitled Prompt'}</span>
          </div>
          <div className="spacer" style={{ flexGrow: 1 }}></div>
          <div className="toolbar-tabs">
            <button 
              className="tab-btn"
              onClick={handleSave}
              disabled={isSaving}
              style={{ color: 'var(--accent-success, #10b981)', fontWeight: 600 }}
              title="Save document changes"
            >
              <Save size={16} /> {isSaving ? 'Saving...' : 'Save'}
            </button>
            <button 
              className="tab-btn"
              onClick={handleExportTxt}
              disabled={!promptText.trim()}
              style={{ color: 'var(--accent-primary, #6366f1)', fontWeight: 600 }}
              title="Export working text as .txt file"
            >
              <Download size={16} /> Export .txt
            </button>
            {activeDocument && (
              <button 
                className="tab-btn"
                onClick={handleDeleteActiveDoc}
                style={{ color: '#ef4444' }}
                title={`Delete current ${activeDocument.type}`}
              >
                <Trash2 size={16} /> Delete
              </button>
            )}
            <button 
              className={`tab-btn ${viewMode === 'code' ? 'active' : ''}`}
              onClick={() => setViewMode('code')}
            >
              <Code size={16} /> Code View
            </button>
            <button 
              className={`tab-btn ${viewMode === 'visual' ? 'active' : ''}`}
              onClick={() => setViewMode('visual')}
            >
              <LayoutTemplate size={16} /> Visual Builder
            </button>
            <button 
              className={`tab-btn ${viewMode === 'gallery' ? 'active' : ''}`}
              onClick={() => setViewMode('gallery')}
            >
              <ImageIcon size={16} /> Image Gallery
            </button>
            <button 
              className="tab-btn"
              onClick={() => setActiveView('krea2')}
              title="Open Krea 2 Studio"
            >
              <Wand2 size={16} style={{ color: 'var(--accent-primary)' }} /> Krea 2 Studio
            </button>
            <button 
              className="tab-btn"
              onClick={() => setActiveView('anima')}
              title="Open ANIMA Studio"
            >
              <Sparkles size={16} style={{ color: '#ec4899' }} /> ANIMA Studio
            </button>
            <button
              className={`tab-btn ${rightPanelTab === 'chat' ? 'active' : ''}`}
              onClick={() => setRightPanelTab('chat')}
              style={{ background: 'rgba(99, 102, 241, 0.15)', borderColor: 'rgba(99, 102, 241, 0.4)', color: '#a5b4fc', fontWeight: 600 }}
              title="Open AI Prompt Refinement Assistant in Right Panel"
            >
              <MessageSquare size={16} style={{ color: '#c084fc' }} /> AI Chat
            </button>
            <button 
              className={`tab-btn ${showSettings ? 'active' : ''}`}
              onClick={() => setShowSettings(!showSettings)}
              style={{ marginLeft: '12px', borderLeft: '1px solid var(--glass-border)' }}
            >
              <SlidersHorizontal size={16} /> Settings
            </button>
          </div>
        </div>

        
        <div className="editor-content">
          {viewMode === 'code' && <MonacoPromptEditor value={promptText} onChange={handleEditorChange} />}
          {viewMode === 'visual' && <VisualBuilder value={promptText} onChange={handleEditorChange} />}
          {viewMode === 'gallery' && <GalleryView />}
        </div>
        {isMobile && <MobilePromptToolbar onInsertText={handleInsertText} />}
      </div>
      
      {showSettings && (
        <GenerationSettings 
          settings={genSettings} 
          setSettings={setGenSettings} 
          onGenerate={handleGenerate}
          isGenerating={isGenerating}
        />
      )}

      {isSaveModalOpen && (
        <div className="save-modal-backdrop" onClick={() => setIsSaveModalOpen(false)}>
          <div className="save-modal glass-panel" onClick={e => e.stopPropagation()}>
            <h3>Save New Document</h3>
            <div className="save-modal-field">
              <label>Document Type:</label>
              <div className="doc-type-selector">
                <button
                  type="button"
                  className={`type-btn ${newDocType === 'prompt' ? 'active' : ''}`}
                  onClick={() => {
                    setNewDocType('prompt');
                    setNewDocName('New Prompt');
                  }}
                >
                  Prompt
                </button>
                <button
                  type="button"
                  className={`type-btn ${newDocType === 'wildcard' ? 'active' : ''}`}
                  onClick={() => {
                    setNewDocType('wildcard');
                    setNewDocName('new_wildcard.txt');
                  }}
                >
                  Wildcard
                </button>
              </div>
            </div>
            <div className="save-modal-field">
              <label>{newDocType === 'prompt' ? 'Prompt Name:' : 'Wildcard Filename:'}</label>
              <input
                type="text"
                className="modal-input"
                value={newDocName}
                onChange={e => setNewDocName(e.target.value)}
                onKeyDown={e => {
                  if (e.key === 'Enter') handleConfirmCreateSave();
                  if (e.key === 'Escape') setIsSaveModalOpen(false);
                }}
                autoFocus
              />
            </div>
            <div className="modal-actions">
              <button className="secondary-button" onClick={() => setIsSaveModalOpen(false)}>
                Cancel
              </button>
              <button className="primary-button" onClick={handleConfirmCreateSave} disabled={isSaving}>
                {isSaving ? 'Saving...' : 'Save Document'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};


