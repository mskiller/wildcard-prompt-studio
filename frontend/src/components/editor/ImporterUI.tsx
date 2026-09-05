import React, { useState, useRef } from 'react';
import { UploadCloud, CheckCircle } from 'lucide-react';
import { importWildcards } from '../../api';
import { useAppStore } from '../../store/useAppStore';
import './ImporterUI.css';

export const ImporterUI: React.FC = () => {
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [result, setResult] = useState<{ imported: number, tags: number } | null>(null);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const triggerRefresh = useAppStore(state => state.triggerRefresh);

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const uploadFiles = async (files: FileList | File[]) => {
    if (!files || files.length === 0) return;
    setIsUploading(true);
    setError(null);
    setResult(null);

    const formData = new FormData();
    for (let i = 0; i < files.length; i++) {
      formData.append('files', files[i]);
    }

    try {
      const data = await importWildcards(formData);
      setResult({ imported: data.imported_wildcards, tags: data.extracted_tags });
      triggerRefresh();
    } catch (err: any) {
      setError(err.message || 'Upload failed');
    } finally {
      setIsUploading(false);
      setIsDragging(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    uploadFiles(e.dataTransfer.files);
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      uploadFiles(e.target.files);
    }
  };

  return (
    <div className="importer-container glass-panel">
      <h2>Import External Wildcards</h2>
      <p className="importer-desc">Drag and drop ComfyUI Impact Pack <code>.txt</code> or <code>.yaml</code> files here.</p>
      
      <div 
        className={`dropzone ${isDragging ? 'dragging' : ''} ${isUploading ? 'uploading' : ''}`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
      >
        <input 
          type="file" 
          multiple 
          accept=".txt,.yaml,.yml" 
          ref={fileInputRef} 
          style={{ display: 'none' }} 
          onChange={handleFileChange}
        />
        
        {isUploading ? (
          <div className="dropzone-content">
            <div className="spinner"></div>
            <span>Uploading & Parsing...</span>
          </div>
        ) : result ? (
          <div className="dropzone-content success">
            <CheckCircle size={32} color="var(--accent-success)" />
            <span>Success! Imported {result.imported} wildcards and {result.tags} tags.</span>
          </div>
        ) : (
          <div className="dropzone-content">
            <UploadCloud size={48} color="var(--accent-primary)" />
            <span>Drop files here or click to browse</span>
          </div>
        )}
      </div>

      {error && <div className="error-message" style={{ marginTop: '16px' }}>{error}</div>}
    </div>
  );
};
