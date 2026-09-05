import React, { useState, useEffect, useCallback, useRef } from 'react';
import {
  getRAGStats,
  getRAGDocuments,
  deleteRAGDocument,
  indexRAGDocument,
  searchRAGKnowledge,
  RAGDocument,
  RAGSearchResult,
  RAGStats,
} from '../../api';
import './RAGKnowledgeInspector.css';

export const RAGKnowledgeInspector: React.FC = () => {
  // Stats
  const [stats, setStats] = useState<RAGStats | null>(null);
  const [loadingStats, setLoadingStats] = useState<boolean>(true);

  // Active view tab
  const [activeTab, setActiveTab] = useState<'browser' | 'sandbox'>('browser');

  // Error message banner state
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Documents state
  const [documents, setDocuments] = useState<RAGDocument[]>([]);
  const [loadingDocs, setLoadingDocs] = useState<boolean>(false);
  const [docSearchQuery, setDocSearchQuery] = useState<string>('');
  const [debouncedQuery, setDebouncedQuery] = useState<string>('');
  const [selectedTag, setSelectedTag] = useState<string | null>(null);
  const [allTags, setAllTags] = useState<string[]>([]);
  const [deletingId, setDeletingId] = useState<number | null>(null);

  // Refs for request cancellation and timeout cleanup
  const abortControllerRef = useRef<AbortController | null>(null);
  const modalTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Live Query Sandbox state
  const [sandboxQuery, setSandboxQuery] = useState<string>('cyberpunk neon lighting');
  const [sandboxTopK, setSandboxTopK] = useState<number>(3);
  const [sandboxResults, setSandboxResults] = useState<RAGSearchResult[]>([]);
  const [loadingSandbox, setLoadingSandbox] = useState<boolean>(false);
  const [hasSearchedSandbox, setHasSearchedSandbox] = useState<boolean>(false);

  // Indexing Modal state
  const [showIndexModal, setShowIndexModal] = useState<boolean>(false);
  const [newTitle, setNewTitle] = useState<string>('');
  const [newContent, setNewContent] = useState<string>('');
  const [newTagsInput, setNewTagsInput] = useState<string>('');
  const [isIndexing, setIsIndexing] = useState<boolean>(false);
  const [indexStatusMsg, setIndexStatusMsg] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  // Debounce search query changes
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedQuery(docSearchQuery);
    }, 300);
    return () => clearTimeout(timer);
  }, [docSearchQuery]);

  // Component unmount cleanup
  useEffect(() => {
    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
      if (modalTimeoutRef.current) {
        clearTimeout(modalTimeoutRef.current);
      }
    };
  }, []);

  // Fetch Stats
  const loadStats = useCallback(async () => {
    setLoadingStats(true);
    try {
      const data = await getRAGStats();
      setStats(data);
    } catch (err: any) {
      console.error('Failed to load RAG stats:', err);
      setErrorMessage(`Failed to load RAG stats: ${err.message || err}`);
    } finally {
      setLoadingStats(false);
    }
  }, []);

  // Fetch Documents
  const loadDocuments = useCallback(async () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    const controller = new AbortController();
    abortControllerRef.current = controller;

    setLoadingDocs(true);
    try {
      const docs = await getRAGDocuments(
        debouncedQuery.trim() || undefined,
        selectedTag || undefined,
        controller.signal
      );
      setDocuments(docs);
      if (!selectedTag) {
        const tagSet = new Set<string>();
        docs.forEach((doc) => {
          if (Array.isArray(doc.tags)) {
            doc.tags.forEach((t) => tagSet.add(t));
          }
        });
        setAllTags(Array.from(tagSet).sort());
      }
    } catch (err: any) {
      if (err.name === 'AbortError') return;
      console.error('Failed to load RAG documents:', err);
      setErrorMessage(`Failed to load RAG documents: ${err.message || err}`);
    } finally {
      if (abortControllerRef.current === controller) {
        setLoadingDocs(false);
      }
    }
  }, [debouncedQuery, selectedTag]);

  // Initial & Dependency Load
  useEffect(() => {
    loadStats();
    loadDocuments();
  }, [loadStats, loadDocuments]);

  // Delete Document Handler
  const handleDeleteDocument = async (docId: number) => {
    if (!window.confirm('Are you sure you want to delete this document from the RAG store?')) {
      return;
    }
    setDeletingId(docId);
    try {
      await deleteRAGDocument(docId);
      setDocuments((prev) => prev.filter((d) => d.id !== docId));
      loadStats();
    } catch (err: any) {
      console.error('Failed to delete RAG document:', err);
      setErrorMessage(`Failed to delete RAG document: ${err.message || err}`);
    } finally {
      setDeletingId(null);
    }
  };

  // Live Query Sandbox Handler
  const handleRunSandboxQuery = async () => {
    if (!sandboxQuery.trim()) return;
    setLoadingSandbox(true);
    setHasSearchedSandbox(true);
    try {
      const results = await searchRAGKnowledge(sandboxQuery.trim(), sandboxTopK);
      setSandboxResults(results);
    } catch (err: any) {
      console.error('Sandbox search failed:', err);
      setErrorMessage(`Failed to run vector search: ${err.message || err}`);
    } finally {
      setLoadingSandbox(false);
    }
  };

  // Index Document Handler
  const handleIndexSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newTitle.trim() || !newContent.trim()) {
      setIndexStatusMsg({ type: 'error', text: 'Title and Content are required.' });
      return;
    }

    setIsIndexing(true);
    setIndexStatusMsg(null);
    try {
      const parsedTags = newTagsInput
        .split(',')
        .map((t) => t.trim())
        .filter((t) => t.length > 0);

      await indexRAGDocument(newTitle.trim(), newContent.trim(), parsedTags);
      setIndexStatusMsg({ type: 'success', text: 'Document indexed successfully into vector store!' });
      setNewTitle('');
      setNewContent('');
      setNewTagsInput('');
      
      // Refresh list & stats
      loadDocuments();
      loadStats();

      if (modalTimeoutRef.current) {
        clearTimeout(modalTimeoutRef.current);
      }
      modalTimeoutRef.current = setTimeout(() => {
        setShowIndexModal(false);
        setIndexStatusMsg(null);
      }, 1200);
    } catch (err: any) {
      setIndexStatusMsg({ type: 'error', text: `Failed to index document: ${err.message || err}` });
    } finally {
      setIsIndexing(false);
    }
  };

  return (
    <div className="rag-inspector-panel">
      {/* Status Header */}
      <header className="rag-header">
        <div className="rag-header-title">
          <div className="rag-title-icon">
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"></path>
              <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"></path>
              <circle cx="12" cy="10" r="3"></circle>
            </svg>
          </div>
          <div>
            <h2>RAG Knowledge & Vector Inspector</h2>
            <p className="rag-subtitle">Manage vector knowledge base and test semantic similarity searches</p>
          </div>
        </div>

        <div className="rag-header-actions">
          <button
            className="btn-index-trigger"
            onClick={() => {
              setIndexStatusMsg(null);
              setShowIndexModal(true);
            }}
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <line x1="12" y1="5" x2="12" y2="19"></line>
              <line x1="5" y1="12" x2="19" y2="12"></line>
            </svg>
            Index Document
          </button>
          <button
            className="btn-icon-refresh"
            onClick={() => {
              setErrorMessage(null);
              loadStats();
              loadDocuments();
            }}
            title="Refresh Knowledge Data"
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <polyline points="23 4 23 10 17 10"></polyline>
              <polyline points="1 20 1 14 7 14"></polyline>
              <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"></path>
            </svg>
          </button>
        </div>
      </header>

      {/* Error Message Banner */}
      {errorMessage && (
        <div className="rag-error-banner">
          <div className="rag-error-content">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="12" cy="12" r="10"></circle>
              <line x1="12" y1="8" x2="12" y2="12"></line>
              <line x1="12" y1="16" x2="12.01" y2="16"></line>
            </svg>
            <span>{errorMessage}</span>
          </div>
          <button className="btn-close-error" onClick={() => setErrorMessage(null)} title="Dismiss error">
            &times;
          </button>
        </div>
      )}

      {/* Stats Cards Bar */}
      <div className="rag-stats-bar">
        <div className="stat-card">
          <div className="stat-label">Vector Store Status</div>
          <div className="stat-value active-badge">
            <span className="pulse-dot"></span> Active (pgvector)
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Total Documents</div>
          <div className="stat-value">
            {loadingStats ? <span className="stat-skeleton">...</span> : stats?.total_documents ?? documents.length}
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Total Tags</div>
          <div className="stat-value">
            {loadingStats ? <span className="stat-skeleton">...</span> : stats?.total_tags ?? allTags.length}
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Embedding Model</div>
          <div className="stat-value model-name">
            {loadingStats ? <span className="stat-skeleton">...</span> : stats?.model_name || 'all-MiniLM-L6-v2'}
          </div>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="rag-tab-bar">
        <button
          className={`rag-tab ${activeTab === 'browser' ? 'active' : ''}`}
          onClick={() => setActiveTab('browser')}
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <rect x="3" y="3" width="7" height="7"></rect>
            <rect x="14" y="3" width="7" height="7"></rect>
            <rect x="14" y="14" width="7" height="7"></rect>
            <rect x="3" y="14" width="7" height="7"></rect>
          </svg>
          Knowledge Browser ({documents.length})
        </button>
        <button
          className={`rag-tab ${activeTab === 'sandbox' ? 'active' : ''}`}
          onClick={() => setActiveTab('sandbox')}
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"></polygon>
          </svg>
          Live Vector Sandbox
        </button>
      </div>

      {/* TAB 1: KNOWLEDGE BROWSER */}
      {activeTab === 'browser' && (
        <div className="rag-tab-content">
          {/* Search & Tag Filter controls */}
          <div className="rag-filter-section">
            <div className="rag-search-box">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <circle cx="11" cy="11" r="8"></circle>
                <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
              </svg>
              <input
                type="text"
                placeholder="Search knowledge documents by title or text..."
                value={docSearchQuery}
                onChange={(e) => setDocSearchQuery(e.target.value)}
              />
              {docSearchQuery && (
                <button className="btn-clear-search" onClick={() => setDocSearchQuery('')}>
                  &times;
                </button>
              )}
            </div>

            {/* Tag Filter Chips */}
            <div className="rag-tag-filter-chips">
              <span className="tag-filter-label">Filter by Tag:</span>
              <button
                className={`tag-chip ${selectedTag === null ? 'active' : ''}`}
                onClick={() => setSelectedTag(null)}
              >
                All
              </button>
              {allTags.map((tag) => (
                <button
                  key={tag}
                  className={`tag-chip ${selectedTag === tag ? 'active' : ''}`}
                  onClick={() => setSelectedTag(selectedTag === tag ? null : tag)}
                >
                  #{tag}
                </button>
              ))}
            </div>
          </div>

          {/* Document Cards List */}
          {loadingDocs ? (
            <div className="rag-loading-container">
              <div className="rag-spinner"></div>
              <span>Fetching vector knowledge documents...</span>
            </div>
          ) : documents.length === 0 ? (
            <div className="rag-empty-state">
              <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                <polyline points="14 2 14 8 20 8"></polyline>
                <line x1="16" y1="13" x2="8" y2="13"></line>
                <line x1="16" y1="17" x2="8" y2="17"></line>
                <polyline points="10 9 9 9 8 9"></polyline>
              </svg>
              <h4>No knowledge documents found</h4>
              <p>Try clearing filters or click "Index Document" above to embed new prompt knowledge.</p>
            </div>
          ) : (
            <div className="rag-doc-grid">
              {documents.map((doc) => (
                <div key={doc.id} className="rag-doc-card">
                  <div className="rag-doc-header">
                    <h3 className="rag-doc-title">{doc.title}</h3>
                    <button
                      className="btn-doc-delete"
                      onClick={() => handleDeleteDocument(doc.id)}
                      disabled={deletingId === doc.id}
                      title="Delete document"
                    >
                      {deletingId === doc.id ? (
                        <div className="mini-spinner"></div>
                      ) : (
                        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                          <polyline points="3 6 5 6 21 6"></polyline>
                          <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                        </svg>
                      )}
                    </button>
                  </div>

                  {Array.isArray(doc.tags) && doc.tags.length > 0 && (
                    <div className="rag-doc-tags">
                      {doc.tags.map((tag) => (
                        <span key={tag} className="tag-pill">
                          #{tag}
                        </span>
                      ))}
                    </div>
                  )}

                  <div className="rag-doc-body">
                    <p>{doc.content}</p>
                  </div>

                  <div className="rag-doc-footer">
                    <span className="doc-id-badge">ID: #{doc.id}</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* TAB 2: LIVE QUERY SANDBOX */}
      {activeTab === 'sandbox' && (
        <div className="rag-tab-content">
          <div className="sandbox-panel">
            <div className="sandbox-input-group">
              <div className="sandbox-field-grow">
                <label className="sandbox-label">Test Prompt Query</label>
                <input
                  type="text"
                  className="sandbox-query-input"
                  value={sandboxQuery}
                  onChange={(e) => setSandboxQuery(e.target.value)}
                  placeholder="Enter a prompt topic or concept (e.g. realistic portrait lighting)..."
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') handleRunSandboxQuery();
                  }}
                />
              </div>

              <div className="sandbox-field-shrink">
                <label className="sandbox-label">Top K Results</label>
                <select
                  className="sandbox-topk-select"
                  value={sandboxTopK}
                  onChange={(e) => setSandboxTopK(Number(e.target.value))}
                >
                  <option value={1}>1 result</option>
                  <option value={3}>3 results</option>
                  <option value={5}>5 results</option>
                  <option value={10}>10 results</option>
                </select>
              </div>

              <button
                className="btn-run-sandbox"
                onClick={handleRunSandboxQuery}
                disabled={loadingSandbox || !sandboxQuery.trim()}
              >
                {loadingSandbox ? (
                  <>
                    <div className="rag-spinner-sm"></div> Calculating...
                  </>
                ) : (
                  <>
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"></polygon>
                    </svg>
                    Run Vector Search
                  </>
                )}
              </button>
            </div>

            {/* Sandbox Results */}
            <div className="sandbox-results-container">
              {!hasSearchedSandbox ? (
                <div className="sandbox-placeholder">
                  <div className="sandbox-icon-wrap">
                    <svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                      <circle cx="11" cy="11" r="8"></circle>
                      <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
                    </svg>
                  </div>
                  <h4>Vector Similarity Sandbox</h4>
                  <p>Execute live semantic vector similarity queries against your embedded prompt knowledge base.</p>
                </div>
              ) : sandboxResults.length === 0 ? (
                <div className="rag-empty-state">
                  <h4>No matching knowledge vectors</h4>
                  <p>Try adjusting your search query or lowering the similarity threshold.</p>
                </div>
              ) : (
                <div className="sandbox-results-list">
                  {sandboxResults.map((item, idx) => {
                    // Ensure score is 0-100%
                    const rawScore = item.similarity_score ?? 0;
                    const percentScore = Math.min(100, Math.max(0, Math.round(rawScore > 1 ? rawScore : rawScore * 100)));

                    // Determine progress bar color theme
                    let scoreClass = 'score-high';
                    if (percentScore < 50) scoreClass = 'score-low';
                    else if (percentScore < 75) scoreClass = 'score-medium';

                    return (
                      <div key={item.id || idx} className="sandbox-result-card">
                        <div className="sandbox-card-top">
                          <div className="sandbox-rank-badge">#{idx + 1}</div>
                          <div className="sandbox-doc-info">
                            <h4 className="sandbox-item-title">{item.title}</h4>
                            {Array.isArray(item.tags) && item.tags.length > 0 && (
                              <div className="rag-doc-tags">
                                {item.tags.map((t) => (
                                  <span key={t} className="tag-pill">
                                    #{t}
                                  </span>
                                ))}
                              </div>
                            )}
                          </div>
                          <div className={`sandbox-similarity-pill ${scoreClass}`}>
                            {percentScore}% Match
                          </div>
                        </div>

                        {/* Similarity Progress Meter */}
                        <div className="similarity-meter-wrapper">
                          <div className="similarity-meter-track">
                            <div
                              className={`similarity-meter-fill ${scoreClass}`}
                              style={{ width: `${percentScore}%` }}
                            ></div>
                          </div>
                        </div>

                        <div className="sandbox-card-content">
                          <p>{item.content}</p>
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* INDEXING FORM MODAL */}
      {showIndexModal && (
        <div className="rag-modal-overlay" onClick={() => setShowIndexModal(false)}>
          <div className="rag-modal-card" onClick={(e) => e.stopPropagation()}>
            <div className="rag-modal-header">
              <div className="modal-title-wrap">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                  <polyline points="14 2 14 8 20 8"></polyline>
                  <line x1="12" y1="18" x2="12" y2="12"></line>
                  <line x1="9" y1="15" x2="15" y2="15"></line>
                </svg>
                <h3>Index Custom Knowledge Document</h3>
              </div>
              <button className="btn-modal-close" onClick={() => setShowIndexModal(false)}>
                &times;
              </button>
            </div>

            <form onSubmit={handleIndexSubmit} className="rag-modal-form">
              {indexStatusMsg && (
                <div className={`rag-alert ${indexStatusMsg.type}`}>
                  {indexStatusMsg.type === 'success' ? '✓ ' : '✕ '}
                  {indexStatusMsg.text}
                </div>
              )}

              <div className="form-group">
                <label>Document Title *</label>
                <input
                  type="text"
                  placeholder="e.g. Cyberpunk Lighting & Palette Guide"
                  value={newTitle}
                  onChange={(e) => setNewTitle(e.target.value)}
                  required
                />
              </div>

              <div className="form-group">
                <label>Knowledge Content / Prompt Guidelines *</label>
                <textarea
                  rows={5}
                  placeholder="Enter detailed prompt rules, style modifiers, or aesthetic guidelines to embed..."
                  value={newContent}
                  onChange={(e) => setNewContent(e.target.value)}
                  required
                />
              </div>

              <div className="form-group">
                <label>Tags (Comma Separated)</label>
                <input
                  type="text"
                  placeholder="e.g. lighting, cyberpunk, style, anime"
                  value={newTagsInput}
                  onChange={(e) => setNewTagsInput(e.target.value)}
                />
              </div>

              <div className="rag-modal-footer">
                <button
                  type="button"
                  className="btn-modal-cancel"
                  onClick={() => setShowIndexModal(false)}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="btn-modal-submit"
                  disabled={isIndexing}
                >
                  {isIndexing ? (
                    <>
                      <div className="rag-spinner-sm"></div> Embedding...
                    </>
                  ) : (
                    'Index into Vector DB'
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
