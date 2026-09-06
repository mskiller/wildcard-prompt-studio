import React, { useEffect, useState, useRef, useCallback } from 'react';
import { 
  Tag, Search, Sparkles, RefreshCw, Copy, Check, Plus, 
  Layers, ShieldCheck, X, GitFork, ArrowDownToLine
} from 'lucide-react';
import { 
  getTags, getTagCategories, sanitizeTags, resyncWildcardTags, TagItem,
  getDanbooruTags, getDanbooruStats, getDanbooruCooccurrences, importDanbooruToTags,
  DanbooruTagItem, DanbooruStats, DanbooruCooccurrence
} from '../../api';
import { usePromptStore } from '../../store/usePromptStore';
import { useAppStore } from '../../store/useAppStore';
import './TagsView.css';

interface CategoryStats {
  name: string;
  count: number;
}

const CATEGORY_COLORS: Record<string, { bg: string; text: string; border: string }> = {
  'Character': { bg: 'rgba(236, 72, 153, 0.15)', text: '#f472b6', border: 'rgba(236, 72, 153, 0.3)' },
  'character': { bg: 'rgba(236, 72, 153, 0.15)', text: '#f472b6', border: 'rgba(236, 72, 153, 0.3)' },
  'Clothing': { bg: 'rgba(168, 85, 247, 0.15)', text: '#c084fc', border: 'rgba(168, 85, 247, 0.3)' },
  'Lighting': { bg: 'rgba(234, 179, 8, 0.15)', text: '#facc15', border: 'rgba(234, 179, 8, 0.3)' },
  'Style': { bg: 'rgba(59, 130, 246, 0.15)', text: '#60a5fa', border: 'rgba(59, 130, 246, 0.3)' },
  'Camera': { bg: 'rgba(20, 184, 166, 0.15)', text: '#2dd4bf', border: 'rgba(20, 184, 166, 0.3)' },
  'Quality / Score': { bg: 'rgba(34, 197, 94, 0.15)', text: '#4ade80', border: 'rgba(34, 197, 94, 0.3)' },
  'meta': { bg: 'rgba(34, 197, 94, 0.15)', text: '#4ade80', border: 'rgba(34, 197, 94, 0.3)' },
  'Artist': { bg: 'rgba(249, 115, 22, 0.15)', text: '#fb923c', border: 'rgba(249, 115, 22, 0.3)' },
  'artist': { bg: 'rgba(249, 115, 22, 0.15)', text: '#fb923c', border: 'rgba(249, 115, 22, 0.3)' },
  'copyright': { bg: 'rgba(168, 85, 247, 0.15)', text: '#c084fc', border: 'rgba(168, 85, 247, 0.3)' },
  'General': { bg: 'rgba(255, 255, 255, 0.08)', text: 'var(--fg-secondary)', border: 'var(--glass-border)' },
  'general': { bg: 'rgba(255, 255, 255, 0.08)', text: 'var(--fg-secondary)', border: 'var(--glass-border)' },
};

function formatCount(num: number): string {
  if (!num) return '0';
  if (num >= 1_000_000) return (num / 1_000_000).toFixed(1) + 'M';
  if (num >= 1_000) return (num / 1_000).toFixed(1) + 'k';
  return num.toString();
}

export const TagsView: React.FC = () => {
  // Mode: Library Tags vs Danbooru Lexicon
  const [viewMode, setViewMode] = useState<'library' | 'danbooru'>('library');

  // Library Tags state
  const [tags, setTags] = useState<TagItem[]>([]);
  const [categories, setCategories] = useState<CategoryStats[]>([]);
  const [totalCount, setTotalCount] = useState<number>(0);

  // Danbooru state
  const [danbooruTags, setDanbooruTags] = useState<DanbooruTagItem[]>([]);
  const [danbooruStats, setDanbooruStats] = useState<DanbooruStats | null>(null);
  const [expandedDanbooruTag, setExpandedDanbooruTag] = useState<string | null>(null);
  const [cooccurrences, setCooccurrences] = useState<Record<string, DanbooruCooccurrence[]>>({});
  const [loadingCooc, setLoadingCooc] = useState<boolean>(false);

  // Shared state
  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [actionLoading, setActionLoading] = useState<string | null>(null);

  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string>('All');
  const [copiedKey, setCopiedKey] = useState<string | null>(null);
  const [insertedKey, setInsertedKey] = useState<string | null>(null);
  const [toastMessage, setToastMessage] = useState<string | null>(null);

  const appendTag = usePromptStore(state => state.appendTag);
  const triggerRefresh = useAppStore(state => state.triggerRefresh);
  const searchTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const toastTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const showToast = (msg: string) => {
    if (toastTimeoutRef.current) clearTimeout(toastTimeoutRef.current);
    setToastMessage(msg);
    toastTimeoutRef.current = setTimeout(() => setToastMessage(null), 3500);
  };

  const fetchCategories = async () => {
    try {
      const data = await getTagCategories();
      setTotalCount(data.total);
      setCategories(data.categories || []);
    } catch (e) {
      console.error('Failed to load categories', e);
    }
  };

  const fetchDanbooruStatsData = async () => {
    try {
      const stats = await getDanbooruStats();
      setDanbooruStats(stats);
    } catch (e) {
      console.error('Failed to load Danbooru stats', e);
    }
  };

  const fetchTagsList = useCallback(async (q: string, category: string, reset: boolean = true) => {
    if (reset) {
      setLoading(true);
    } else {
      setLoadingMore(true);
    }

    try {
      if (viewMode === 'library') {
        const skip = reset ? 0 : tags.length;
        const fetched = await getTags({
          q: q.trim() || undefined,
          category: category !== 'All' ? category : undefined,
          skip,
          limit: 100
        });

        if (reset) {
          setTags(fetched);
        } else {
          setTags(prev => [...prev, ...fetched]);
        }
      } else {
        const skip = reset ? 0 : danbooruTags.length;
        const fetched = await getDanbooruTags({
          q: q.trim() || undefined,
          category: category !== 'All' ? category.toLowerCase() : undefined,
          skip,
          limit: 100
        });

        if (reset) {
          setDanbooruTags(fetched);
        } else {
          setDanbooruTags(prev => [...prev, ...fetched]);
        }
      }
    } catch (err) {
      console.error('Failed to fetch tags', err);
    } finally {
      setLoading(false);
      setLoadingMore(false);
    }
  }, [viewMode, tags.length, danbooruTags.length]);

  // Initial load
  useEffect(() => {
    fetchCategories();
    fetchDanbooruStatsData();
    fetchTagsList('', 'All', true);
  }, [viewMode]);

  // Debounced search
  useEffect(() => {
    if (searchTimeoutRef.current) clearTimeout(searchTimeoutRef.current);
    searchTimeoutRef.current = setTimeout(() => {
      fetchTagsList(searchQuery, selectedCategory, true);
    }, 300);

    return () => {
      if (searchTimeoutRef.current) clearTimeout(searchTimeoutRef.current);
    };
  }, [searchQuery, selectedCategory, viewMode]);

  const handleCategorySelect = (category: string) => {
    setSelectedCategory(category);
  };

  const handleInsertTag = (tagName: string, key: string, e?: React.MouseEvent) => {
    if (e) e.stopPropagation();
    appendTag(tagName.replace(/_/g, ' '));
    setInsertedKey(key);
    showToast(`Added "${tagName}" to active prompt!`);
    setTimeout(() => setInsertedKey(null), 1500);
  };

  const handleCopyTag = (tagName: string, key: string, e: React.MouseEvent) => {
    e.stopPropagation();
    navigator.clipboard.writeText(tagName);
    setCopiedKey(key);
    showToast(`Copied "${tagName}" to clipboard!`);
    setTimeout(() => setCopiedKey(null), 1500);
  };

  const handleToggleDanbooruExpand = async (tagName: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (expandedDanbooruTag === tagName) {
      setExpandedDanbooruTag(null);
      return;
    }

    setExpandedDanbooruTag(tagName);
    if (!cooccurrences[tagName]) {
      setLoadingCooc(true);
      try {
        const coocs = await getDanbooruCooccurrences(tagName, 15);
        setCooccurrences(prev => ({ ...prev, [tagName]: coocs }));
      } catch (err) {
        console.error('Failed to load cooccurrences for', tagName, err);
      } finally {
        setLoadingCooc(false);
      }
    }
  };

  const handleSanitize = async () => {
    if (actionLoading) return;
    setActionLoading('sanitize');
    try {
      const res = await sanitizeTags();
      showToast(`Sanitized tags! ${res.tags_cleaned} cleaned, ${res.tags_deleted} pruned. ${res.total_remaining} left.`);
      await fetchCategories();
      await fetchTagsList(searchQuery, selectedCategory, true);
      triggerRefresh();
    } catch (e: any) {
      showToast(`Sanitization failed: ${e.message}`);
    } finally {
      setActionLoading(null);
    }
  };

  const handleResync = async () => {
    if (actionLoading) return;
    setActionLoading('resync');
    try {
      const res = await resyncWildcardTags();
      showToast(`Synced! Found ${res.total_tags_found} tags (${res.new_tags_added} new). Total: ${res.total_tags_in_db}`);
      await fetchCategories();
      await fetchTagsList(searchQuery, selectedCategory, true);
      triggerRefresh();
    } catch (e: any) {
      showToast(`Resync failed: ${e.message}`);
    } finally {
      setActionLoading(null);
    }
  };

  const handleImportDanbooru = async () => {
    if (actionLoading) return;
    setActionLoading('importDanbooru');
    try {
      const res = await importDanbooruToTags(5000);
      showToast(`Imported ${res.imported} Danbooru tags into main library! (${res.already_existing} were already present)`);
      await fetchCategories();
      triggerRefresh();
    } catch (e: any) {
      showToast(`Danbooru import failed: ${e.message}`);
    } finally {
      setActionLoading(null);
    }
  };

  const activeCategories = viewMode === 'library'
    ? categories
    : (danbooruStats?.categories || []).map(c => ({ name: c.category.charAt(0).toUpperCase() + c.category.slice(1), count: c.count }));

  const currentTotal = viewMode === 'library'
    ? totalCount
    : (danbooruStats?.total_tags || 31060);

  return (
    <div className="tags-view-container glass-panel">
      {/* Header Bar */}
      <div className="tags-header-section">
        <div className="tags-title-row">
          <div className="tags-title-group">
            <div className="tag-icon-badge">
              <Tag size={22} color="var(--accent-primary)" />
            </div>
            <div>
              <div className="tags-title-wrapper">
                <h2>Tag Studio & Lexicon</h2>
                <span className="total-tag-counter">
                  {currentTotal > 0 ? `${currentTotal.toLocaleString()} Tags` : 'Loading...'}
                </span>
              </div>
              <p className="tags-description">
                {viewMode === 'library' 
                  ? 'Browse, search, and click tags to quickly insert them into your prompt. Clean noise and sync AST tags automatically.'
                  : 'Danbooru probabilistic tag graph (31k tags, 3.2M co-occurrences). Explore frequently paired tags and prompt synergies.'}
              </p>
            </div>
          </div>

          <div className="tags-action-buttons">
            {/* View Mode Switcher */}
            <div className="lexicon-mode-toggle">
              <button 
                className={`mode-toggle-btn ${viewMode === 'library' ? 'active' : ''}`}
                onClick={() => { setViewMode('library'); setSelectedCategory('All'); setSearchQuery(''); }}
              >
                <Layers size={14} />
                <span>Wildcard Tags</span>
              </button>
              <button 
                className={`mode-toggle-btn ${viewMode === 'danbooru' ? 'active' : ''}`}
                onClick={() => { setViewMode('danbooru'); setSelectedCategory('All'); setSearchQuery(''); }}
              >
                <GitFork size={14} />
                <span>Danbooru Lexicon (31k)</span>
              </button>
            </div>

            {viewMode === 'library' ? (
              <>
                <button 
                  className="action-pill-btn sync-btn" 
                  onClick={handleResync} 
                  disabled={actionLoading !== null}
                  title="Parse wildcards with AST and sync missing tags into database"
                >
                  <RefreshCw size={14} className={actionLoading === 'resync' ? 'spinning' : ''} />
                  <span>{actionLoading === 'resync' ? 'Syncing...' : 'Sync Wildcards'}</span>
                </button>
                <button 
                  className="action-pill-btn clean-btn" 
                  onClick={handleSanitize} 
                  disabled={actionLoading !== null}
                  title="Standardize dynamic syntax, SD weights, and eliminate duplicates"
                >
                  <ShieldCheck size={14} className={actionLoading === 'sanitize' ? 'spinning' : ''} />
                  <span>{actionLoading === 'sanitize' ? 'Cleaning...' : 'Sanitize DB'}</span>
                </button>
              </>
            ) : (
              <button 
                className="action-pill-btn sync-btn" 
                onClick={handleImportDanbooru}
                disabled={actionLoading !== null}
                title="Import top 5,000 Danbooru tags into the main application tags database"
              >
                <ArrowDownToLine size={14} className={actionLoading === 'importDanbooru' ? 'spinning' : ''} />
                <span>{actionLoading === 'importDanbooru' ? 'Importing...' : 'Import to Library'}</span>
              </button>
            )}
          </div>
        </div>

        {/* Search and Filters */}
        <div className="tags-search-filter-bar">
          <div className="tags-search-box">
            <Search size={16} className="search-icon" />
            <input 
              type="text" 
              placeholder={viewMode === 'library' 
                ? "Search tags (e.g. cyberpunk, 1girl, cinematic lighting, armor)..." 
                : "Search Danbooru tags (e.g. 1girl, hatsune_miku, solo, long_hair)..."}
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="tags-search-input"
            />
            {searchQuery && (
              <button className="clear-search-btn" onClick={() => setSearchQuery('')}>
                <X size={14} />
              </button>
            )}
          </div>

          <div className="tags-category-tabs">
            <button 
              className={`category-tab-btn ${selectedCategory === 'All' ? 'active' : ''}`}
              onClick={() => handleCategorySelect('All')}
            >
              <span>All</span>
              <span className="cat-count-pill">{currentTotal.toLocaleString()}</span>
            </button>
            {activeCategories.map((cat) => (
              <button 
                key={cat.name}
                className={`category-tab-btn ${selectedCategory.toLowerCase() === cat.name.toLowerCase() ? 'active' : ''}`}
                onClick={() => handleCategorySelect(cat.name)}
                style={{
                  '--cat-color': CATEGORY_COLORS[cat.name]?.text || 'var(--accent-primary)'
                } as React.CSSProperties}
              >
                <span>{cat.name}</span>
                <span className="cat-count-pill">{cat.count.toLocaleString()}</span>
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Tags Grid Area */}
      <div className="tags-content-area">
        {loading ? (
          <div className="tags-loading-state">
            <div className="spinner"></div>
            <span>Loading {viewMode === 'library' ? 'tags' : 'Danbooru lexicon'}...</span>
          </div>
        ) : (viewMode === 'library' ? tags.length === 0 : danbooruTags.length === 0) ? (
          <div className="empty-state">
            <Layers size={40} strokeWidth={1.2} style={{ opacity: 0.5, marginBottom: '12px' }} />
            <div>No tags found matching "{searchQuery}".</div>
            <div style={{ fontSize: '12px', marginTop: '6px', opacity: 0.7 }}>
              Try a different keyword or reset category filter.
            </div>
          </div>
        ) : (
          <>
            <div className="tags-grid">
              {viewMode === 'library'
                ? tags.map((t) => {
                    const colorConfig = CATEGORY_COLORS[t.category] || CATEGORY_COLORS['General'];
                    const cardKey = `lib-${t.id}`;
                    const isJustInserted = insertedKey === cardKey;
                    const isJustCopied = copiedKey === cardKey;

                    return (
                      <div 
                        key={t.id} 
                        className={`tag-card ${isJustInserted ? 'just-inserted' : ''}`}
                        onClick={() => handleInsertTag(t.name, cardKey)}
                        title={`Click to insert "${t.name}" into prompt`}
                      >
                        <div className="tag-card-main">
                          <span className="tag-name">{t.name}</span>
                          {t.category && (
                            <span 
                              className="tag-badge"
                              style={{
                                backgroundColor: colorConfig.bg,
                                color: colorConfig.text,
                                borderColor: colorConfig.border
                              }}
                            >
                              {t.category}
                            </span>
                          )}
                        </div>

                        <div className="tag-card-actions">
                          <button 
                            className={`tag-action-btn ${isJustInserted ? 'success' : ''}`} 
                            onClick={(e) => handleInsertTag(t.name, cardKey, e)} 
                            title="Add to prompt"
                          >
                            {isJustInserted ? <Check size={13} /> : <Plus size={13} />}
                          </button>
                          <button 
                            className={`tag-action-btn ${isJustCopied ? 'success' : ''}`} 
                            onClick={(e) => handleCopyTag(t.name, cardKey, e)} 
                            title="Copy tag name"
                          >
                            {isJustCopied ? <Check size={13} /> : <Copy size={13} />}
                          </button>
                        </div>
                      </div>
                    );
                  })
                : danbooruTags.map((t) => {
                    const colorConfig = CATEGORY_COLORS[t.category] || CATEGORY_COLORS['general'];
                    const cardKey = `dan-${t.tag}`;
                    const isJustInserted = insertedKey === cardKey;
                    const isJustCopied = copiedKey === cardKey;
                    const isExpanded = expandedDanbooruTag === t.tag;
                    const coocList = cooccurrences[t.tag] || [];

                    return (
                      <div 
                        key={t.tag} 
                        className={`tag-card danbooru-card ${isExpanded ? 'expanded' : ''} ${isJustInserted ? 'just-inserted' : ''}`}
                        onClick={() => handleInsertTag(t.tag, cardKey)}
                        title={`Click to insert "${t.tag}" into prompt`}
                      >
                        <div className="danbooru-card-inner">
                          <div className="tag-card-main">
                            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                              <span className="tag-name">{t.tag}</span>
                              <span className="danbooru-count-label">{formatCount(t.total_count)}</span>
                            </div>
                            <span 
                              className="tag-badge"
                              style={{
                                backgroundColor: colorConfig.bg,
                                color: colorConfig.text,
                                borderColor: colorConfig.border
                              }}
                            >
                              {t.category}
                            </span>
                          </div>

                          <div className="tag-card-actions">
                            <button 
                              className={`tag-action-btn ${isExpanded ? 'active-pair' : ''}`}
                              onClick={(e) => handleToggleDanbooruExpand(t.tag, e)}
                              title="Show top co-occurring tags"
                            >
                              <GitFork size={13} />
                            </button>
                            <button 
                              className={`tag-action-btn ${isJustInserted ? 'success' : ''}`} 
                              onClick={(e) => handleInsertTag(t.tag, cardKey, e)} 
                              title="Add to prompt"
                            >
                              {isJustInserted ? <Check size={13} /> : <Plus size={13} />}
                            </button>
                            <button 
                              className={`tag-action-btn ${isJustCopied ? 'success' : ''}`} 
                              onClick={(e) => handleCopyTag(t.tag, cardKey, e)} 
                              title="Copy tag name"
                            >
                              {isJustCopied ? <Check size={13} /> : <Copy size={13} />}
                            </button>
                          </div>
                        </div>

                        {/* Expandable Co-occurrence Drawer */}
                        {isExpanded && (
                          <div className="cooccurrence-drawer" onClick={(e) => e.stopPropagation()}>
                            <div className="cooc-header">
                              <Sparkles size={12} color="#a855f7" />
                              <span>Frequently paired with <strong>{t.tag}</strong>:</span>
                            </div>
                            {loadingCooc && coocList.length === 0 ? (
                              <div className="cooc-loading">Loading synergy graph...</div>
                            ) : coocList.length === 0 ? (
                              <div className="cooc-empty">No direct pairs found.</div>
                            ) : (
                              <div className="cooc-chips-grid">
                                {coocList.map((pair) => (
                                  <button 
                                    key={pair.tag} 
                                    className="cooc-chip"
                                    onClick={() => handleInsertTag(pair.tag, `dan-${pair.tag}`)}
                                    title={`Click to add "${pair.tag}" to prompt (${formatCount(pair.count)} co-occurrences)`}
                                  >
                                    <span className="cooc-chip-name">{pair.tag}</span>
                                    <span className="cooc-chip-count">{formatCount(pair.count)}</span>
                                  </button>
                                ))}
                              </div>
                            )}
                          </div>
                        )}
                      </div>
                    );
                  })}
            </div>

            {(viewMode === 'library' ? tags.length >= 100 : danbooruTags.length >= 100) && (
              <div className="load-more-container">
                <button 
                  className="load-more-btn"
                  onClick={() => fetchTagsList(searchQuery, selectedCategory, false)}
                  disabled={loadingMore}
                >
                  {loadingMore ? 'Loading more...' : `Load More Tags (Showing ${viewMode === 'library' ? tags.length : danbooruTags.length})`}
                </button>
              </div>
            )}
          </>
        )}
      </div>

      {/* Floating Toast */}
      {toastMessage && (
        <div className="tags-toast animate-slide-up">
          <Sparkles size={14} color="var(--accent-primary)" />
          <span>{toastMessage}</span>
        </div>
      )}
    </div>
  );
};
