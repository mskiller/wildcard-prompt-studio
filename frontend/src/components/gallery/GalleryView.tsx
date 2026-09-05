import React, { useEffect, useState } from 'react';
import { getGalleryImages, syncRecentComfyOutputs } from '../../api';
import './GalleryView.css';
import { useAppStore } from '../../store/useAppStore';
import { usePromptStore } from '../../store/usePromptStore';
import { Download, X, RefreshCw, Folder, Copy, Check, Sparkles } from 'lucide-react';

export const GalleryView: React.FC = () => {
  const [images, setImages] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [lightboxImg, setLightboxImg] = useState<any | null>(null);
  const [copied, setCopied] = useState(false);
  const { comfyUIUrl, setActiveView } = useAppStore();
  const { setPromptText } = usePromptStore();

  useEffect(() => {
    loadImages();
  }, []);

  const loadImages = async () => {
    setLoading(true);
    try {
      const data = await getGalleryImages();
      setImages(Array.isArray(data) ? data : []);
    } catch (err) {
      console.error('Failed to load gallery images:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSyncFromComfy = async () => {
    setSyncing(true);
    try {
      await syncRecentComfyOutputs('MatrixSweep', 50, comfyUIUrl);
      await loadImages();
    } catch (err) {
      console.error('Failed to sync from ComfyUI:', err);
    } finally {
      setSyncing(false);
    }
  };

  const getImgSrc = (img: any) => {
    if (!img || !img.filename) return '';
    return `/api/v1/images/file/${encodeURIComponent(img.filename)}`;
  };

  const handleFallbackSrc = (e: React.SyntheticEvent<HTMLImageElement, Event>, img: any) => {
    const target = e.currentTarget;
    const fallbackUrl = `/api/v1/comfyui/view?filename=${encodeURIComponent(img.filename)}${
      comfyUIUrl ? `&base_url=${encodeURIComponent(comfyUIUrl)}` : ''
    }`;
    if (target.src !== window.location.origin + fallbackUrl) {
      target.src = fallbackUrl;
    }
  };

  const handleCopyPrompt = async (text: string) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 1800);
    } catch {
      // Fallback
    }
  };

  const handleUseInEditor = (promptText: string) => {
    setPromptText(promptText);
    setActiveView('explorer');
  };

  if (loading) {
    return (
      <div className="gallery-loading">
        <RefreshCw size={24} className="spin" />
        <span>Loading Gallery Images...</span>
      </div>
    );
  }

  return (
    <div className="gallery-container">
      <div className="gallery-header-bar">
        <div className="title-area">
          <Folder size={20} style={{ color: '#fab387' }} />
          <h3>Generated Images Gallery ({images.length})</h3>
        </div>
        <div className="header-actions">
          <button
            className="refresh-gallery-btn"
            onClick={handleSyncFromComfy}
            disabled={syncing}
            title="Scan ComfyUI and import recent generations"
          >
            <RefreshCw size={14} className={syncing ? 'spin' : ''} />
            {syncing ? 'Syncing...' : 'Sync from ComfyUI'}
          </button>
          <button className="refresh-gallery-btn" onClick={loadImages} title="Refresh Gallery">
            <RefreshCw size={14} /> Refresh
          </button>
        </div>
      </div>

      {images.length === 0 ? (
        <div className="gallery-empty">
          <p>No generated images saved in database yet.</p>
          <p className="sub">Generate images in Live ComfyUI Stream, Matrix Studio, or click "Sync from ComfyUI" to import recent renders!</p>
        </div>
      ) : (
        <div className="gallery-grid">
          {images.map((img) => (
            <div key={img.id} className="gallery-item glass-panel" onClick={() => setLightboxImg(img)}>
              <img
                src={getImgSrc(img)}
                alt={`Generated render #${img.id}`}
                className="gallery-image"
                loading="lazy"
                onError={(e) => handleFallbackSrc(e, img)}
              />
              <div className="gallery-item-overlay">
                <div className="gallery-item-meta">
                  {img.seed && <span>Seed: {img.seed}</span>}
                  {img.cfg_scale && <span>CFG: {img.cfg_scale}</span>}
                  {img.sampler_name && <span>Sampler: {img.sampler_name}</span>}
                  {img.steps && <span>Steps: {img.steps}</span>}
                </div>
                {img.prompt_content && <div className="gallery-item-prompt">{img.prompt_content}</div>}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Lightbox Modal (Enlarged view with prompt below) */}
      {lightboxImg && (
        <div className="lightbox-overlay" onClick={() => setLightboxImg(null)}>
          <div className="lightbox-modal" onClick={(e) => e.stopPropagation()}>
            <div className="lightbox-modal-header">
              <span className="lightbox-filename">{lightboxImg.filename}</span>
              <button className="lightbox-close" onClick={() => setLightboxImg(null)}>
                <X size={18} />
              </button>
            </div>
            
            <div className="lightbox-image-area">
              <img
                src={getImgSrc(lightboxImg)}
                alt="Fullscreen Gallery Render"
                className="lightbox-img"
                onError={(e) => handleFallbackSrc(e, lightboxImg)}
              />
            </div>

            <div className="lightbox-prompt-area">
              <div className="lightbox-prompt-meta">
                <span className="prompt-title">Prompt:</span>
                <div className="lightbox-badges">
                  {lightboxImg.seed && <span>Seed: {lightboxImg.seed}</span>}
                  {lightboxImg.sampler_name && <span>Sampler: {lightboxImg.sampler_name}</span>}
                  {lightboxImg.steps && <span>Steps: {lightboxImg.steps}</span>}
                  {lightboxImg.cfg_scale && <span>CFG: {lightboxImg.cfg_scale}</span>}
                </div>
              </div>
              <div className="lightbox-prompt-text">
                {lightboxImg.prompt_content || 'No prompt recorded for this image.'}
              </div>
              <div className="lightbox-actions">
                {lightboxImg.prompt_content && (
                  <button
                    className="lightbox-btn"
                    onClick={() => handleCopyPrompt(lightboxImg.prompt_content)}
                  >
                    {copied ? <Check size={14} /> : <Copy size={14} />}
                    {copied ? 'Copied Prompt' : 'Copy Prompt'}
                  </button>
                )}
                {lightboxImg.prompt_content && (
                  <button
                    className="lightbox-btn"
                    onClick={() => handleUseInEditor(lightboxImg.prompt_content)}
                    title="Open this prompt in the Editor"
                  >
                    <Sparkles size={14} /> Use in Editor
                  </button>
                )}
                <a
                  href={getImgSrc(lightboxImg)}
                  download={lightboxImg.filename || 'render.png'}
                  target="_blank"
                  rel="noreferrer"
                  className="lightbox-btn primary"
                >
                  <Download size={14} /> Download PNG
                </a>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
