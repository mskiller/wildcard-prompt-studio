import React, { useEffect, useState, useMemo, useCallback } from 'react';
import {
  getGalleryImages,
  toggleImageFavorite,
  setImageRating,
  scoreImageAesthetic,
  batchDeleteImages,
  batchIndexImagesToRAG,
  getSimilarImages,
  syncRecentComfyOutputs,
  GalleryItem,
  GalleryQueryParams,
} from '../../api';
import './GalleryView.css';
import { useAppStore } from '../../store/useAppStore';
import { usePromptStore } from '../../store/usePromptStore';
import {
  Download,
  X,
  RefreshCw,
  Folder,
  Copy,
  Check,
  Sparkles,
  Heart,
  Star,
  Sliders,
  Search,
  Trash2,
  BookOpen,
  ChevronLeft,
  ChevronRight,
  Filter,
  CheckSquare,
  Square,
  Zap,
  Maximize2,
  Layers,
  Eye,
  AlertCircle,
  ZoomIn,
  ZoomOut,
} from 'lucide-react';

export const GalleryView: React.FC = () => {
  // Store hooks
  const { comfyUIUrl, setActiveView, setComfySettings, setActiveDocument } = useAppStore();
  const { setPromptText } = usePromptStore();

  // Primary image states
  const [images, setImages] = useState<GalleryItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [syncing, setSyncing] = useState<boolean>(false);

  // Filters & Sorting state
  const [searchTerm, setSearchTerm] = useState<string>('');
  const [debouncedSearch, setDebouncedSearch] = useState<string>('');
  const [selectedSampler, setSelectedSampler] = useState<string>('all');
  const [onlyFavorites, setOnlyFavorites] = useState<boolean>(false);
  const [minRating, setMinRating] = useState<number>(0);
  const [sortBy, setSortBy] = useState<'newest' | 'oldest' | 'rating' | 'aesthetic_score'>('newest');
  const [thumbnailSize, setThumbnailSize] = useState<number>(240); // px width

  // Multi-Select state
  const [isSelectMode, setIsSelectMode] = useState<boolean>(false);
  const [selectedIds, setSelectedIds] = useState<Set<number>>(new Set());
  const [batchLoading, setBatchLoading] = useState<boolean>(false);

  // Lightbox Modal state
  const [lightboxImg, setLightboxImg] = useState<GalleryItem | null>(null);
  const [lightboxZoom, setLightboxZoom] = useState<boolean>(false);
  const [similarImages, setSimilarImages] = useState<GalleryItem[]>([]);
  const [loadingSimilar, setLoadingSimilar] = useState<boolean>(false);
  const [scoringId, setScoringId] = useState<number | null>(null);
  const [copiedLightbox, setCopiedLightbox] = useState<boolean>(false);
  const [copiedCardId, setCopiedCardId] = useState<number | null>(null);

  // Side-by-Side (A/B) Compare Modal state
  const [isCompareOpen, setIsCompareOpen] = useState<boolean>(false);
  const [comparePair, setComparePair] = useState<[GalleryItem, GalleryItem] | null>(null);

  // Notification / Feedback banner state
  const [toastMessage, setToastMessage] = useState<{ text: string; type: 'info' | 'success' | 'error' } | null>(null);
  const toastTimeoutRef = React.useRef<any>(null);

  const showToast = (text: string, type: 'info' | 'success' | 'error' = 'info') => {
    if (toastTimeoutRef.current) clearTimeout(toastTimeoutRef.current);
    setToastMessage({ text, type });
    toastTimeoutRef.current = setTimeout(() => {
      setToastMessage(null);
    }, 3200);
  };

  // Debounce search input
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedSearch(searchTerm);
    }, 300);
    return () => clearTimeout(timer);
  }, [searchTerm]);

  // Load gallery images whenever filter criteria change
  const loadImages = useCallback(async () => {
    setLoading(true);
    try {
      const params: GalleryQueryParams = {
        sort_by: sortBy,
      };
      if (debouncedSearch.trim()) {
        params.search = debouncedSearch.trim();
      }
      if (selectedSampler !== 'all') {
        params.sampler = selectedSampler;
      }
      if (onlyFavorites) {
        params.is_favorite = true;
      }
      if (minRating > 0) {
        params.min_rating = minRating;
      }

      const data = await getGalleryImages(params);
      setImages(Array.isArray(data) ? data : []);
    } catch (err) {
      console.error('Failed to load gallery images:', err);
      showToast('Failed to load gallery images', 'error');
    } finally {
      setLoading(false);
    }
  }, [debouncedSearch, selectedSampler, onlyFavorites, minRating, sortBy]);

  useEffect(() => {
    loadImages();
  }, [loadImages]);

  // Extract unique samplers from current image collection
  const availableSamplers = useMemo(() => {
    const list = ['all', 'Euler a', 'Euler', 'DPM++ 2M Karras', 'DPM++ SDE Karras', 'DDIM', 'UniPC'];
    images.forEach((img) => {
      if (img.sampler_name && !list.includes(img.sampler_name)) {
        list.push(img.sampler_name);
      }
    });
    return list;
  }, [images]);

  // ComfyUI Sync
  const handleSyncFromComfy = async () => {
    setSyncing(true);
    try {
      await syncRecentComfyOutputs('MatrixSweep', 50, comfyUIUrl);
      showToast('Synced recent generations from ComfyUI', 'success');
      await loadImages();
    } catch (err) {
      console.error('Failed to sync from ComfyUI:', err);
      showToast('Sync from ComfyUI failed', 'error');
    } finally {
      setSyncing(false);
    }
  };

  // Safe Image URL helper
  const getImgSrc = (img: GalleryItem) => {
    if (!img || !img.filename) return '';
    return `/api/v1/images/file/${encodeURIComponent(img.filename)}`;
  };

  const handleFallbackSrc = (e: React.SyntheticEvent<HTMLImageElement, Event>, img: GalleryItem) => {
    const target = e.currentTarget;
    const fallbackUrl = `/api/v1/comfyui/view?filename=${encodeURIComponent(img.filename)}${
      comfyUIUrl ? `&base_url=${encodeURIComponent(comfyUIUrl)}` : ''
    }`;
    if (target.src !== window.location.origin + fallbackUrl) {
      target.src = fallbackUrl;
    }
  };

  // Copy Prompt
  const handleCopyPrompt = async (text?: string | null, cardId?: number) => {
    if (!text) return;
    try {
      await navigator.clipboard.writeText(text);
      if (cardId) {
        setCopiedCardId(cardId);
        setTimeout(() => setCopiedCardId(null), 1800);
      } else {
        setCopiedLightbox(true);
        setTimeout(() => setCopiedLightbox(false), 1800);
      }
    } catch {
      showToast('Could not copy to clipboard', 'error');
    }
  };

  // Toggle Favorite
  const handleToggleFavorite = async (id: number, e?: React.MouseEvent) => {
    if (e) e.stopPropagation();
    try {
      const updated = await toggleImageFavorite(id);
      setImages((prev) =>
        prev.map((img) => (img.id === id ? { ...img, is_favorite: updated.is_favorite } : img))
      );
      if (lightboxImg && lightboxImg.id === id) {
        setLightboxImg((prev) => (prev ? { ...prev, is_favorite: updated.is_favorite } : null));
      }
    } catch (err) {
      console.error('Failed to toggle favorite:', err);
      showToast('Failed to update favorite', 'error');
    }
  };

  // Set Star Rating
  const handleSetRating = async (id: number, rating: number, e?: React.MouseEvent) => {
    if (e) e.stopPropagation();
    try {
      const updated = await setImageRating(id, rating);
      setImages((prev) =>
        prev.map((img) => (img.id === id ? { ...img, rating: updated.rating } : img))
      );
      if (lightboxImg && lightboxImg.id === id) {
        setLightboxImg((prev) => (prev ? { ...prev, rating: updated.rating } : null));
      }
    } catch (err) {
      console.error('Failed to set rating:', err);
      showToast('Failed to update rating', 'error');
    }
  };

  // Compute Aesthetic Score on-demand
  const handleScoreAesthetic = async (id: number, e?: React.MouseEvent) => {
    if (e) e.stopPropagation();
    setScoringId(id);
    try {
      const updated = await scoreImageAesthetic(id);
      setImages((prev) =>
        prev.map((img) => (img.id === id ? { ...img, aesthetic_score: updated.aesthetic_score } : img))
      );
      if (lightboxImg && lightboxImg.id === id) {
        setLightboxImg((prev) => (prev ? { ...prev, aesthetic_score: updated.aesthetic_score } : null));
      }
      showToast(`Aesthetic Score: ${updated.aesthetic_score?.toFixed(1) ?? 'N/A'}`, 'success');
    } catch (err) {
      console.error('Failed to score aesthetic:', err);
      showToast('Aesthetic scoring failed', 'error');
    } finally {
      setScoringId(null);
    }
  };

  // Load Similar Renders
  const handleLoadSimilar = async (id: number) => {
    setLoadingSimilar(true);
    try {
      const res = await getSimilarImages(id, 8);
      setSimilarImages(res.filter((item) => item.id !== id));
    } catch (err) {
      console.error('Failed to fetch similar images:', err);
      showToast('Failed to find similar generations', 'error');
    } finally {
      setLoadingSimilar(false);
    }
  };

  // Open Lightbox
  const handleOpenLightbox = (img: GalleryItem) => {
    if (isSelectMode) {
      handleToggleSelect(img.id);
      return;
    }
    setLightboxImg(img);
    setLightboxZoom(false);
    setSimilarImages([]);
  };

  // Navigate lightbox next/previous
  const handleNavigateLightbox = (direction: 'prev' | 'next') => {
    if (!lightboxImg || images.length === 0) return;
    const currentIndex = images.findIndex((img) => img.id === lightboxImg.id);
    if (currentIndex === -1) {
      setLightboxImg(images[0]);
      setLightboxZoom(false);
      setSimilarImages([]);
      return;
    }

    let nextIndex = direction === 'next' ? currentIndex + 1 : currentIndex - 1;
    if (nextIndex < 0) nextIndex = images.length - 1;
    if (nextIndex >= images.length) nextIndex = 0;

    const nextImg = images[nextIndex];
    setLightboxImg(nextImg);
    setLightboxZoom(false);
    setSimilarImages([]);
  };

  // Keyboard navigation for Lightbox
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (isCompareOpen) {
        if (e.key === 'Escape') setIsCompareOpen(false);
        return;
      }
      if (!lightboxImg) return;
      if (e.key === 'Escape') {
        setLightboxImg(null);
      } else if (e.key === 'ArrowLeft') {
        handleNavigateLightbox('prev');
      } else if (e.key === 'ArrowRight') {
        handleNavigateLightbox('next');
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [lightboxImg, isCompareOpen, images]);

  // Selection handlers
  const handleToggleSelect = (id: number) => {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  };

  const handleSelectAll = () => {
    if (selectedIds.size === images.length) {
      setSelectedIds(new Set());
    } else {
      setSelectedIds(new Set(images.map((img) => img.id)));
    }
  };

  // Batch Delete
  const handleBatchDelete = async () => {
    if (selectedIds.size === 0) return;
    const count = selectedIds.size;
    if (!window.confirm(`Are you sure you want to permanently delete ${count} image(s)?`)) return;

    setBatchLoading(true);
    try {
      const res = await batchDeleteImages(Array.from(selectedIds));
      showToast(`Deleted ${res.deleted_count} image(s)`, 'success');
      setSelectedIds(new Set());
      await loadImages();
    } catch (err) {
      console.error('Batch delete failed:', err);
      showToast('Batch delete failed', 'error');
    } finally {
      setBatchLoading(false);
    }
  };

  // Batch RAG Index
  const handleBatchIndexRAG = async () => {
    if (selectedIds.size === 0) return;
    setBatchLoading(true);
    try {
      const res = await batchIndexImagesToRAG(Array.from(selectedIds), 'gallery_vault', ['batch', 'render']);
      showToast(`Indexed ${res.indexed_count} image(s) to RAG Knowledge Base!`, 'success');
      setSelectedIds(new Set());
    } catch (err) {
      console.error('Batch RAG index failed:', err);
      showToast('Batch RAG index failed', 'error');
    } finally {
      setBatchLoading(false);
    }
  };

  // Open A/B Compare Modal
  const handleOpenCompare = () => {
    if (selectedIds.size !== 2) return;
    const pairIds = Array.from(selectedIds);
    const itemA = images.find((img) => img.id === pairIds[0]);
    const itemB = images.find((img) => img.id === pairIds[1]);
    if (itemA && itemB) {
      setComparePair([itemA, itemB]);
      setIsCompareOpen(true);
    }
  };

  // Single-image Index to RAG from Lightbox
  const handleIndexLightboxImageToRAG = async () => {
    if (!lightboxImg) return;
    try {
      const tags = ['gallery', lightboxImg.sampler_name || 'render'];
      await batchIndexImagesToRAG([lightboxImg.id], 'gallery_curated', tags);
      showToast(`Indexed #${lightboxImg.id} to RAG Knowledge!`, 'success');
    } catch (err) {
      console.error('Failed to index to RAG:', err);
      showToast('Failed to index image to RAG', 'error');
    }
  };

  // 1-Click Studio Roundtrip Dispatches
  const handleDispatchToEditor = (prompt?: string | null) => {
    if (!prompt) return;
    setPromptText(prompt);
    setActiveDocument({
      type: 'prompt',
      id: Date.now(),
      name: 'Gallery Prompt',
      content: prompt,
    });
    setActiveView('explorer');
    showToast('Prompt loaded into Editor!', 'success');
  };

  const handleDispatchToKrea2 = (prompt?: string | null) => {
    if (!prompt) return;
    setPromptText(prompt);
    setActiveView('krea2');
    showToast('Sent prompt to Krea 2 Studio!', 'success');
  };

  const handleDispatchToAnima = (prompt?: string | null) => {
    if (!prompt) return;
    setPromptText(prompt);
    setActiveView('anima');
    showToast('Sent prompt to Anima Studio!', 'success');
  };

  const handleDispatchToVision = () => {
    setActiveView('vision');
    showToast('Switched to Vision Inspector', 'info');
  };

  const handleRequeueInComfyUI = (img: GalleryItem) => {
    if (!img.prompt_content) return;
    setComfySettings({
      singlePrompt: img.prompt_content,
      steps: img.steps || 20,
      cfg: img.cfg_scale || 7.0,
      selectedSampler: img.sampler_name || 'euler',
      width: img.width || 512,
      height: img.height || 512,
    });
    setActiveView('comfyui');
    showToast('Loaded prompt and parameters into Live ComfyUI Stream!', 'success');
  };

  // Aesthetic badge helper
  const renderAestheticBadge = (img: GalleryItem) => {
    const score = img.aesthetic_score;
    const isScoring = scoringId === img.id;

    if (score !== null && score !== undefined) {
      const colorClass = score >= 8.0 ? 'score-high' : score >= 6.5 ? 'score-med' : 'score-low';
      return (
        <span className={`aesthetic-score-badge ${colorClass}`} title={`Aesthetic Quality Score: ${score}`}>
          ✨ {score.toFixed(1)}
        </span>
      );
    }

    return (
      <button
        className="card-score-action-btn"
        onClick={(e) => handleScoreAesthetic(img.id, e)}
        disabled={isScoring}
        title="Compute aesthetic score"
      >
        <Sparkles size={11} className={isScoring ? 'spin' : ''} />
        {isScoring ? 'Scoring...' : 'Score'}
      </button>
    );
  };

  return (
    <div className="gallery-studio-container">
      {/* Toast Notification */}
      {toastMessage && (
        <div className={`gallery-toast toast-${toastMessage.type}`}>
          {toastMessage.type === 'error' ? <AlertCircle size={16} /> : <Check size={16} />}
          <span>{toastMessage.text}</span>
        </div>
      )}

      {/* Main Toolbar */}
      <div className="gallery-toolbar glass-panel">
        <div className="toolbar-top-row">
          <div className="title-area">
            <Folder size={22} className="title-icon" />
            <div>
              <h3 className="gallery-title">Generated Images Gallery</h3>
              <span className="gallery-subtitle">
                {images.length} {images.length === 1 ? 'generation' : 'generations'} cataloged
              </span>
            </div>
          </div>

          <div className="toolbar-actions">
            <button
              className="action-btn sync-btn"
              onClick={handleSyncFromComfy}
              disabled={syncing}
              title="Scan ComfyUI output directory and import recent renders"
            >
              <RefreshCw size={14} className={syncing ? 'spin' : ''} />
              {syncing ? 'Syncing...' : 'Sync ComfyUI'}
            </button>

            <button
              className={`action-btn select-mode-btn ${isSelectMode ? 'active' : ''}`}
              onClick={() => {
                setIsSelectMode(!isSelectMode);
                if (isSelectMode) setSelectedIds(new Set());
              }}
              title="Toggle multi-selection mode"
            >
              {isSelectMode ? <CheckSquare size={14} /> : <Square size={14} />}
              {isSelectMode ? 'Exit Select' : 'Select'}
            </button>

            <button className="action-btn refresh-btn" onClick={loadImages} title="Reload gallery">
              <RefreshCw size={14} /> Refresh
            </button>
          </div>
        </div>

        {/* Filter and Control Row */}
        <div className="toolbar-filters-row">
          {/* Search Input */}
          <div className="filter-search-box">
            <Search size={15} className="search-icon" />
            <input
              type="text"
              placeholder="Search prompts, filenames..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="gallery-search-input"
            />
            {searchTerm && (
              <button className="search-clear-btn" onClick={() => setSearchTerm('')}>
                <X size={13} />
              </button>
            )}
          </div>

          {/* Sampler Selector */}
          <div className="filter-item">
            <Sliders size={14} className="filter-item-icon" />
            <select
              value={selectedSampler}
              onChange={(e) => setSelectedSampler(e.target.value)}
              className="gallery-select"
            >
              {availableSamplers.map((s) => (
                <option key={s} value={s}>
                  {s === 'all' ? 'All Samplers' : s}
                </option>
              ))}
            </select>
          </div>

          {/* Rating Filter */}
          <div className="filter-item">
            <Star size={14} className="filter-item-icon" />
            <select
              value={minRating}
              onChange={(e) => setMinRating(Number(e.target.value))}
              className="gallery-select"
            >
              <option value={0}>All Ratings</option>
              <option value={1}>1+ ★ & Up</option>
              <option value={2}>2+ ★ & Up</option>
              <option value={3}>3+ ★ & Up</option>
              <option value={4}>4+ ★ & Up</option>
              <option value={5}>5 ★ Only</option>
            </select>
          </div>

          {/* Favorites Filter Toggle */}
          <button
            className={`filter-toggle-btn ${onlyFavorites ? 'active' : ''}`}
            onClick={() => setOnlyFavorites(!onlyFavorites)}
            title="Filter by Favorites"
          >
            <Heart size={14} className={onlyFavorites ? 'heart-filled' : ''} />
            Favorites
          </button>

          {/* Sort By Dropdown */}
          <div className="filter-item">
            <Filter size={14} className="filter-item-icon" />
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value as any)}
              className="gallery-select"
            >
              <option value="newest">Newest First</option>
              <option value="oldest">Oldest First</option>
              <option value="rating">Highest Rated</option>
              <option value="aesthetic_score">Aesthetic Quality</option>
            </select>
          </div>

          {/* Thumbnail Size Slider */}
          <div className="zoom-slider-container" title={`Thumbnail Size: ${thumbnailSize}px`}>
            <ZoomOut size={13} />
            <input
              type="range"
              min={160}
              max={360}
              step={20}
              value={thumbnailSize}
              onChange={(e) => setThumbnailSize(Number(e.target.value))}
              className="zoom-slider"
            />
            <ZoomIn size={13} />
          </div>
        </div>
      </div>

      {/* Floating Batch Actions Bar */}
      {selectedIds.size > 0 && (
        <div className="floating-batch-bar glass-panel animate-fade-in">
          <div className="batch-info">
            <span className="batch-count">{selectedIds.size}</span>
            <span>selected</span>
          </div>

          <div className="batch-actions-group">
            <button className="batch-btn select-all-btn" onClick={handleSelectAll}>
              {selectedIds.size === images.length ? 'Deselect All' : 'Select All'}
            </button>

            {/* Compare A/B Button - enabled when exactly 2 selected */}
            <button
              className={`batch-btn compare-btn ${selectedIds.size === 2 ? 'primary' : 'disabled'}`}
              disabled={selectedIds.size !== 2}
              onClick={handleOpenCompare}
              title={selectedIds.size === 2 ? 'Compare 2 renders side-by-side' : 'Select exactly 2 images to compare'}
            >
              <Layers size={14} />
              Compare A/B {selectedIds.size === 2 ? '✨' : '(Pick 2)'}
            </button>

            {/* Batch RAG Index */}
            <button
              className="batch-btn rag-btn"
              onClick={handleBatchIndexRAG}
              disabled={batchLoading}
              title="Index selected generation prompts and metadata into RAG knowledge"
            >
              <BookOpen size={14} />
              {batchLoading ? 'Indexing...' : 'Index to RAG'}
            </button>

            {/* Batch Delete */}
            <button
              className="batch-btn delete-btn"
              onClick={handleBatchDelete}
              disabled={batchLoading}
              title="Permanently delete selected images"
            >
              <Trash2 size={14} />
              Delete ({selectedIds.size})
            </button>

            <button
              className="batch-btn close-btn"
              onClick={() => setSelectedIds(new Set())}
              title="Clear selection"
            >
              <X size={14} />
            </button>
          </div>
        </div>
      )}

      {/* Image Grid */}
      {loading ? (
        <div className="gallery-loading">
          <RefreshCw size={28} className="spin" />
          <span>Loading Gallery Images...</span>
        </div>
      ) : images.length === 0 ? (
        <div className="gallery-empty glass-panel">
          <Folder size={48} className="empty-icon" />
          <p className="empty-title">No images found matching your filters</p>
          <p className="empty-sub">
            Try adjusting your search query, clearing filters, or syncing recent generations from ComfyUI.
          </p>
          {(searchTerm || onlyFavorites || minRating > 0 || selectedSampler !== 'all') && (
            <button
              className="clear-filters-btn"
              onClick={() => {
                setSearchTerm('');
                setSelectedSampler('all');
                setOnlyFavorites(false);
                setMinRating(0);
              }}
            >
              Clear All Filters
            </button>
          )}
        </div>
      ) : (
        <div
          className="gallery-studio-grid"
          style={{ gridTemplateColumns: `repeat(auto-fill, minmax(${thumbnailSize}px, 1fr))` }}
        >
          {images.map((img) => {
            const isSelected = selectedIds.has(img.id);
            return (
              <div
                key={img.id}
                className={`gallery-studio-card glass-panel ${isSelected ? 'selected' : ''}`}
                onClick={() => handleOpenLightbox(img)}
              >
                {/* Selection Checkbox */}
                {(isSelectMode || isSelected) && (
                  <button
                    className={`card-select-btn ${isSelected ? 'checked' : ''}`}
                    onClick={(e) => {
                      e.stopPropagation();
                      handleToggleSelect(img.id);
                    }}
                    title={isSelected ? 'Deselect' : 'Select'}
                  >
                    {isSelected ? <CheckSquare size={16} /> : <Square size={16} />}
                  </button>
                )}

                {/* Top Action Floating Bar (Favorites & Rating) */}
                <div className="card-top-bar">
                  <button
                    className={`card-fav-btn ${img.is_favorite ? 'favorited' : ''}`}
                    onClick={(e) => handleToggleFavorite(img.id, e)}
                    title={img.is_favorite ? 'Remove Favorite' : 'Add to Favorites'}
                  >
                    <Heart size={14} className={img.is_favorite ? 'heart-filled' : ''} />
                  </button>

                  {/* 5-Star Rating Overlay */}
                  <div className="card-rating-group" title={`Rating: ${img.rating || 0} / 5`}>
                    {[1, 2, 3, 4, 5].map((star) => (
                      <Star
                        key={star}
                        size={12}
                        className={`star-icon ${star <= (img.rating || 0) ? 'star-filled' : 'star-empty'}`}
                        onClick={(e) => handleSetRating(img.id, star === img.rating ? 0 : star, e)}
                      />
                    ))}
                  </div>
                </div>

                {/* Main Render Image */}
                <div
                  className="card-image-wrapper"
                  onClick={(e) => {
                    e.stopPropagation();
                    handleOpenLightbox(img);
                  }}
                >
                  <img
                    src={getImgSrc(img)}
                    alt={img.filename || `Render #${img.id}`}
                    className="card-image"
                    loading="lazy"
                    onError={(e) => handleFallbackSrc(e, img)}
                  />
                </div>

                {/* Bottom Overlay & Metadata */}
                <div className="card-bottom-bar" onClick={() => handleOpenLightbox(img)}>
                  {/* Quality Score & Parameter Badges */}
                  <div className="card-badges-row">
                    {renderAestheticBadge(img)}

                    <div className="card-param-chips">
                      {img.seed && <span className="param-chip">Seed: {img.seed}</span>}
                      {img.sampler_name && <span className="param-chip">{img.sampler_name}</span>}
                      {img.steps && <span className="param-chip">{img.steps} steps</span>}
                      {img.cfg_scale && <span className="param-chip">CFG {img.cfg_scale}</span>}
                    </div>
                  </div>

                  {/* Prompt Text Preview & 1-Click Copy */}
                  {img.prompt_content && (
                    <div className="card-prompt-row">
                      <p className="card-prompt-text" title={img.prompt_content}>
                        {img.prompt_content}
                      </p>
                      <button
                        className="card-copy-btn"
                        onClick={(e) => {
                          e.stopPropagation();
                          handleCopyPrompt(img.prompt_content, img.id);
                        }}
                        title="Copy prompt"
                      >
                        {copiedCardId === img.id ? <Check size={13} className="text-success" /> : <Copy size={13} />}
                      </button>
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Comprehensive Lightbox Modal */}
      {lightboxImg && (
        <div className="lightbox-overlay" onClick={() => setLightboxImg(null)}>
          <div
            className="lightbox-modal glass-panel"
            role="dialog"
            aria-modal="true"
            aria-label="Image Details"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Modal Header */}
            <div className="lightbox-modal-header">
              <div className="lightbox-header-title">
                <span className="lightbox-filename">{lightboxImg.filename}</span>
                {lightboxImg.width && lightboxImg.height && (
                  <span className="lightbox-res-badge">
                    {lightboxImg.width} × {lightboxImg.height}
                  </span>
                )}
              </div>

              <div className="lightbox-header-controls">
                <button
                  className={`lightbox-tool-btn ${lightboxZoom ? 'active' : ''}`}
                  onClick={() => setLightboxZoom(!lightboxZoom)}
                  title={lightboxZoom ? 'Fit to Screen' : '100% Zoom'}
                >
                  <Maximize2 size={16} />
                </button>
                <button className="lightbox-close" onClick={() => setLightboxImg(null)}>
                  <X size={18} />
                </button>
              </div>
            </div>

            {/* Modal Image Area */}
            <div className={`lightbox-image-viewport ${lightboxZoom ? 'zoomed' : ''}`}>
              <button
                className="lightbox-nav-btn prev"
                onClick={() => handleNavigateLightbox('prev')}
                title="Previous Image (← Left Arrow)"
              >
                <ChevronLeft size={24} />
              </button>

              <img
                src={getImgSrc(lightboxImg)}
                alt={lightboxImg.filename}
                className="lightbox-display-img"
                onError={(e) => handleFallbackSrc(e, lightboxImg)}
              />

              <button
                className="lightbox-nav-btn next"
                onClick={() => handleNavigateLightbox('next')}
                title="Next Image (→ Right Arrow)"
              >
                <ChevronRight size={24} />
              </button>
            </div>

            {/* Lightbox Details & Action Hub */}
            <div className="lightbox-details-panel">
              {/* Metadata Badges & Rating Bar */}
              <div className="lightbox-meta-row">
                <div className="lightbox-rating-fav-group">
                  <button
                    className={`lightbox-fav-btn ${lightboxImg.is_favorite ? 'active' : ''}`}
                    onClick={() => handleToggleFavorite(lightboxImg.id)}
                    title={lightboxImg.is_favorite ? 'Favorited' : 'Add to Favorites'}
                  >
                    <Heart size={16} className={lightboxImg.is_favorite ? 'heart-filled' : ''} />
                  </button>

                  <div className="lightbox-stars">
                    {[1, 2, 3, 4, 5].map((star) => (
                      <Star
                        key={star}
                        size={15}
                        className={`star-icon ${star <= (lightboxImg.rating || 0) ? 'star-filled' : 'star-empty'}`}
                        onClick={() =>
                          handleSetRating(lightboxImg.id, star === lightboxImg.rating ? 0 : star)
                        }
                      />
                    ))}
                  </div>

                  {renderAestheticBadge(lightboxImg)}
                </div>

                <div className="lightbox-tech-chips">
                  {lightboxImg.seed && <span>Seed: {lightboxImg.seed}</span>}
                  {lightboxImg.sampler_name && <span>Sampler: {lightboxImg.sampler_name}</span>}
                  {lightboxImg.steps && <span>Steps: {lightboxImg.steps}</span>}
                  {lightboxImg.cfg_scale && <span>CFG: {lightboxImg.cfg_scale}</span>}
                  {lightboxImg.comfy_workflow_id && <span>Workflow: {lightboxImg.comfy_workflow_id}</span>}
                </div>
              </div>

              {/* Full Prompt Box */}
              <div className="lightbox-prompt-box">
                <div className="lightbox-prompt-box-header">
                  <span className="prompt-label">Prompt Content</span>
                  <button
                    className="copy-prompt-btn"
                    onClick={() => handleCopyPrompt(lightboxImg.prompt_content)}
                  >
                    {copiedLightbox ? <Check size={14} /> : <Copy size={14} />}
                    {copiedLightbox ? 'Copied' : 'Copy'}
                  </button>
                </div>
                <div className="lightbox-prompt-text">
                  {lightboxImg.prompt_content || 'No prompt recorded for this generation.'}
                </div>
              </div>

              {/* 1-Click Studio Roundtrip Dispatch Bar */}
              <div className="lightbox-dispatch-bar">
                <button
                  className="dispatch-btn editor-btn"
                  onClick={() => handleDispatchToEditor(lightboxImg.prompt_content)}
                  title="Open this prompt in the Prompt Editor"
                >
                  <Sparkles size={14} />
                  Prompt Editor
                </button>

                <button
                  className="dispatch-btn krea2-btn"
                  onClick={() => handleDispatchToKrea2(lightboxImg.prompt_content)}
                  title="Optimize prompt with Krea 2 Engine"
                >
                  ✨ Krea 2 Studio
                </button>

                <button
                  className="dispatch-btn anima-btn"
                  onClick={() => handleDispatchToAnima(lightboxImg.prompt_content)}
                  title="Optimize prompt with ANIMA Anime Engine"
                >
                  🎨 Anima Studio
                </button>

                <button
                  className="dispatch-btn comfy-btn"
                  onClick={() => handleRequeueInComfyUI(lightboxImg)}
                  title="Configure and run workflow in ComfyUI"
                >
                  <Zap size={14} />
                  Re-queue ComfyUI
                </button>

                <button
                  className="dispatch-btn vision-btn"
                  onClick={handleDispatchToVision}
                  title="Inspect visual components in Vision Studio"
                >
                  <Eye size={14} />
                  Vision Inspector
                </button>

                <button
                  className="dispatch-btn rag-btn"
                  onClick={handleIndexLightboxImageToRAG}
                  title="Index this generation into RAG domain knowledge"
                >
                  <BookOpen size={14} />
                  Index to RAG
                </button>

                <button
                  className="dispatch-btn similar-btn"
                  onClick={() => handleLoadSimilar(lightboxImg.id)}
                  disabled={loadingSimilar}
                  title="Find visually & semantically similar renders"
                >
                  <Search size={14} className={loadingSimilar ? 'spin' : ''} />
                  {loadingSimilar ? 'Finding...' : 'Similar Renders'}
                </button>

                <a
                  href={getImgSrc(lightboxImg)}
                  download={lightboxImg.filename || 'render.png'}
                  target="_blank"
                  rel="noreferrer"
                  className="dispatch-btn download-btn"
                  title="Download PNG file"
                >
                  <Download size={14} />
                  Download
                </a>
              </div>

              {/* Similar Renders Carousel / Grid */}
              {similarImages.length > 0 && (
                <div className="lightbox-similar-section">
                  <div className="similar-header">
                    <span className="similar-title">Similar Generations ({similarImages.length})</span>
                    <button className="similar-close" onClick={() => setSimilarImages([])}>
                      <X size={13} />
                    </button>
                  </div>
                  <div className="similar-grid">
                    {similarImages.map((sim) => (
                      <div
                        key={sim.id}
                        className="similar-card"
                        onClick={() => {
                          setLightboxImg(sim);
                          setSimilarImages([]);
                        }}
                        title={`Click to load #${sim.id}\n${sim.prompt_content?.slice(0, 80)}...`}
                      >
                        <img
                          src={getImgSrc(sim)}
                          alt={`Similar #${sim.id}`}
                          className="similar-thumb"
                          onError={(e) => handleFallbackSrc(e, sim)}
                        />
                        <div className="similar-card-meta">
                          <span>#{sim.id}</span>
                          {sim.aesthetic_score && <span>✨{sim.aesthetic_score.toFixed(1)}</span>}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Side-by-Side (A/B) Compare Modal */}
      {isCompareOpen && comparePair && (
        <div className="lightbox-overlay compare-overlay" onClick={() => setIsCompareOpen(false)}>
          <div
            className="compare-modal glass-panel"
            role="dialog"
            aria-modal="true"
            aria-label="Side-by-side Image Comparison"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="lightbox-modal-header">
              <div className="lightbox-header-title">
                <Layers size={18} className="text-accent" />
                <span className="lightbox-filename">
                  A/B Render Comparison: #{comparePair[0].id} vs #{comparePair[1].id}
                </span>
              </div>
              <button className="lightbox-close" onClick={() => setIsCompareOpen(false)}>
                <X size={18} />
              </button>
            </div>

            {/* Split Image Viewers */}
            <div className="compare-split-viewport">
              <div className="compare-pane">
                <div className="compare-pane-header">
                  <span className="pane-badge badge-a">Render A (#{comparePair[0].id})</span>
                  <span className="pane-filename">{comparePair[0].filename}</span>
                </div>
                <div className="compare-image-box">
                  <img
                    src={getImgSrc(comparePair[0])}
                    alt="Render A"
                    className="compare-img"
                    onError={(e) => handleFallbackSrc(e, comparePair[0])}
                  />
                </div>
              </div>

              <div className="compare-pane">
                <div className="compare-pane-header">
                  <span className="pane-badge badge-b">Render B (#{comparePair[1].id})</span>
                  <span className="pane-filename">{comparePair[1].filename}</span>
                </div>
                <div className="compare-image-box">
                  <img
                    src={getImgSrc(comparePair[1])}
                    alt="Render B"
                    className="compare-img"
                    onError={(e) => handleFallbackSrc(e, comparePair[1])}
                  />
                </div>
              </div>
            </div>

            {/* Diff Comparison Table */}
            <div className="compare-diff-container">
              <table className="compare-diff-table">
                <thead>
                  <tr>
                    <th style={{ width: '15%' }}>Parameter</th>
                    <th style={{ width: '42.5%' }}>Render A (#{comparePair[0].id})</th>
                    <th style={{ width: '42.5%' }}>Render B (#{comparePair[1].id})</th>
                  </tr>
                </thead>
                <tbody>
                  <tr>
                    <td className="param-name">Prompt</td>
                    <td className="prompt-diff-cell">
                      <div className="diff-prompt-text">{comparePair[0].prompt_content || 'N/A'}</div>
                      <button
                        className="diff-action-btn"
                        onClick={() => handleDispatchToEditor(comparePair[0].prompt_content)}
                      >
                        <Sparkles size={12} /> Use Prompt A
                      </button>
                    </td>
                    <td className="prompt-diff-cell">
                      <div className="diff-prompt-text">{comparePair[1].prompt_content || 'N/A'}</div>
                      <button
                        className="diff-action-btn"
                        onClick={() => handleDispatchToEditor(comparePair[1].prompt_content)}
                      >
                        <Sparkles size={12} /> Use Prompt B
                      </button>
                    </td>
                  </tr>
                  <tr>
                    <td className="param-name">Seed</td>
                    <td className={comparePair[0].seed !== comparePair[1].seed ? 'diff-highlight' : ''}>
                      {comparePair[0].seed ?? 'N/A'}
                    </td>
                    <td className={comparePair[0].seed !== comparePair[1].seed ? 'diff-highlight' : ''}>
                      {comparePair[1].seed ?? 'N/A'}
                    </td>
                  </tr>
                  <tr>
                    <td className="param-name">Sampler</td>
                    <td className={comparePair[0].sampler_name !== comparePair[1].sampler_name ? 'diff-highlight' : ''}>
                      {comparePair[0].sampler_name ?? 'N/A'}
                    </td>
                    <td className={comparePair[0].sampler_name !== comparePair[1].sampler_name ? 'diff-highlight' : ''}>
                      {comparePair[1].sampler_name ?? 'N/A'}
                    </td>
                  </tr>
                  <tr>
                    <td className="param-name">Steps</td>
                    <td className={comparePair[0].steps !== comparePair[1].steps ? 'diff-highlight' : ''}>
                      {comparePair[0].steps ?? 'N/A'}
                    </td>
                    <td className={comparePair[0].steps !== comparePair[1].steps ? 'diff-highlight' : ''}>
                      {comparePair[1].steps ?? 'N/A'}
                    </td>
                  </tr>
                  <tr>
                    <td className="param-name">CFG Scale</td>
                    <td className={comparePair[0].cfg_scale !== comparePair[1].cfg_scale ? 'diff-highlight' : ''}>
                      {comparePair[0].cfg_scale ?? 'N/A'}
                    </td>
                    <td className={comparePair[0].cfg_scale !== comparePair[1].cfg_scale ? 'diff-highlight' : ''}>
                      {comparePair[1].cfg_scale ?? 'N/A'}
                    </td>
                  </tr>
                  <tr>
                    <td className="param-name">Dimensions</td>
                    <td>
                      {comparePair[0].width && comparePair[0].height
                        ? `${comparePair[0].width} × ${comparePair[0].height}`
                        : 'N/A'}
                    </td>
                    <td>
                      {comparePair[1].width && comparePair[1].height
                        ? `${comparePair[1].width} × ${comparePair[1].height}`
                        : 'N/A'}
                    </td>
                  </tr>
                  <tr>
                    <td className="param-name">Star Rating</td>
                    <td>{comparePair[0].rating ? `${comparePair[0].rating} ★` : '0 ★'}</td>
                    <td>{comparePair[1].rating ? `${comparePair[1].rating} ★` : '0 ★'}</td>
                  </tr>
                  <tr>
                    <td className="param-name">Aesthetic Quality</td>
                    <td>
                      {comparePair[0].aesthetic_score !== null && comparePair[0].aesthetic_score !== undefined
                        ? `✨ ${comparePair[0].aesthetic_score.toFixed(1)} / 10`
                        : 'Unscored'}
                    </td>
                    <td>
                      {comparePair[1].aesthetic_score !== null && comparePair[1].aesthetic_score !== undefined
                        ? `✨ ${comparePair[1].aesthetic_score.toFixed(1)} / 10`
                        : 'Unscored'}
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
