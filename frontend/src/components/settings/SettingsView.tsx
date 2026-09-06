import React, { useState, useEffect } from 'react';
import { useAppStore } from '../../store/useAppStore';
import { 
  Cpu, Box, Moon, Sun, Globe, Wand2, Check, AlertCircle, 
  Database, Trash2, RefreshCw, AlertTriangle, ShieldAlert, 
  Sparkles, Tag, FileText, Image as ImageIcon 
} from 'lucide-react';
import { ModelProfileEditor } from './ModelProfileEditor';
import { testIntegrationConnection, getSystemStats, resetDatabase, SystemStats } from '../../api';
import './SettingsView.css';

export const SettingsView: React.FC = () => {
  const {
    theme, setTheme,
    language, setLanguage,
    t,
    triggerRefresh,
    comfyUIUrl, setComfyUIUrl,
    koboldCppUrl, setKoboldCppUrl,
    ollamaUrl, setOllamaUrl,
    geminiApiKey, setGeminiApiKey,
    discordWebhookUrl, setDiscordWebhookUrl,
    defaultKreaVariant, setDefaultKreaVariant,
    defaultAIProvider, setDefaultAIProvider,
    autoCleanBuzzwords, setAutoCleanBuzzwords,
    autoQuoteTargets, setAutoQuoteTargets,
    enableThinkingTokenBoost, setEnableThinkingTokenBoost,
    maxOutputTokens, setMaxOutputTokens
  } = useAppStore();

  const [activeTab, setActiveTab] = useState<'appearance' | 'prompt' | 'integrations' | 'profiles' | 'database'>('appearance');
  const [testStatus, setTestStatus] = useState<Record<string, 'idle' | 'testing' | 'success' | 'failed'>>({});

  // Database & Storage state
  const [systemStats, setSystemStats] = useState<SystemStats | null>(null);
  const [loadingStats, setLoadingStats] = useState(false);
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [isResetModalOpen, setIsResetModalOpen] = useState(false);
  const [resetConfirmText, setResetConfirmText] = useState('');
  const [resetFeedback, setResetFeedback] = useState<string | null>(null);

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
  }, [theme]);

  const fetchStats = async () => {
    setLoadingStats(true);
    try {
      const stats = await getSystemStats();
      setSystemStats(stats);
    } catch (e) {
      console.error('Failed to fetch system stats', e);
    } finally {
      setLoadingStats(false);
    }
  };

  useEffect(() => {
    if (activeTab === 'database') {
      fetchStats();
    }
  }, [activeTab]);

  const handleResetScope = async (scope: 'prompts' | 'wildcards' | 'tags' | 'gallery') => {
    const labels: Record<string, string> = {
      prompts: 'all saved prompts',
      wildcards: 'all wildcard collections',
      tags: 'all indexed library tags',
      gallery: 'all image generation history'
    };
    if (window.confirm(`Are you sure you want to clear ${labels[scope]}? This cannot be undone.`)) {
      setActionLoading(scope);
      try {
        const res = await resetDatabase(scope);
        setResetFeedback(res.message);
        await fetchStats();
        triggerRefresh();
        setTimeout(() => setResetFeedback(null), 5000);
      } catch (e: any) {
        alert(`Failed to clear ${scope}: ${e.message}`);
      } finally {
        setActionLoading(null);
      }
    }
  };

  const handleFactoryReset = async () => {
    if (resetConfirmText !== 'RESET') return;
    setActionLoading('all');
    try {
      const res = await resetDatabase('all', 'RESET');
      setResetFeedback(res.message);
      setIsResetModalOpen(false);
      setResetConfirmText('');
      await fetchStats();
      triggerRefresh();
      setTimeout(() => setResetFeedback(null), 5000);
    } catch (e: any) {
      alert(`Factory reset failed: ${e.message}`);
    } finally {
      setActionLoading(null);
    }
  };

  const handleTestConnection = async (type: string, url: string) => {
    setTestStatus(prev => ({ ...prev, [type]: 'testing' }));
    const success = await testIntegrationConnection(type, url);
    setTestStatus(prev => ({ ...prev, [type]: success ? 'success' : 'failed' }));
  };

  return (
    <div className="settings-container">
      <div className="settings-sidebar glass-panel">
        <h2 className="settings-sidebar-title">{t('settings')}</h2>
        <ul className="settings-nav">
          <li className={activeTab === 'appearance' ? 'active' : ''} onClick={() => setActiveTab('appearance')}>
            <Globe size={18} /> {t('appearanceLanguage')}
          </li>
          <li className={activeTab === 'prompt' ? 'active' : ''} onClick={() => setActiveTab('prompt')}>
            <Wand2 size={18} /> {t('aiPromptImprovement')}
          </li>
          <li className={activeTab === 'integrations' ? 'active' : ''} onClick={() => setActiveTab('integrations')}>
            <Cpu size={18} /> {t('apiConnections')}
          </li>
          <li className={activeTab === 'profiles' ? 'active' : ''} onClick={() => setActiveTab('profiles')}>
            <Box size={18} /> {t('modelProfiles')}
          </li>
          <li className={activeTab === 'database' ? 'active' : ''} onClick={() => setActiveTab('database')}>
            <Database size={18} /> {t('databaseStorage')}
          </li>
        </ul>
      </div>

      <div className="settings-content glass-panel">
        {activeTab === 'appearance' && (
          <div className="settings-section">
            <h3>{t('appearanceLanguage')}</h3>
            <p className="settings-description">{t('generalDesc')}</p>

            <div className="settings-form-group">
              <label>{t('theme')}</label>
              <div className="toggle-group">
                <button className={`toggle-btn ${theme === 'dark' ? 'active' : ''}`} onClick={() => setTheme('dark')}>
                  <Moon size={16} /> {t('darkMode')}
                </button>
                <button className={`toggle-btn ${theme === 'light' ? 'active' : ''}`} onClick={() => setTheme('light')}>
                  <Sun size={16} /> {t('lightMode')}
                </button>
              </div>
            </div>

            <div className="settings-form-group">
              <label>{t('language')}</label>
              <div className="toggle-group">
                <button className={`toggle-btn ${language === 'en' ? 'active' : ''}`} onClick={() => setLanguage('en')}>
                  {t('english')}
                </button>
                <button className={`toggle-btn ${language === 'fr' ? 'active' : ''}`} onClick={() => setLanguage('fr')}>
                  {t('french')}
                </button>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'prompt' && (
          <div className="settings-section">
            <h3>{t('aiPromptImprovement')}</h3>
            <p className="settings-description">{t('promptRulesDesc')}</p>

            <div className="settings-form-group">
              <label>{t('defaultKreaVariant')}</label>
              <div className="toggle-group">
                <button className={`toggle-btn ${defaultKreaVariant === 'turbo' ? 'active' : ''}`} onClick={() => setDefaultKreaVariant('turbo')}>
                  Turbo (2K)
                </button>
                <button className={`toggle-btn ${defaultKreaVariant === 'medium' ? 'active' : ''}`} onClick={() => setDefaultKreaVariant('medium')}>
                  Medium (Artistic)
                </button>
                <button className={`toggle-btn ${defaultKreaVariant === 'large' ? 'active' : ''}`} onClick={() => setDefaultKreaVariant('large')}>
                  Large (Optics)
                </button>
              </div>
            </div>

            <div className="settings-form-group">
              <label>{t('defaultAIProvider')}</label>
              <div className="toggle-group">
                <button className={`toggle-btn ${defaultAIProvider === 'kobold' ? 'active' : ''}`} onClick={() => setDefaultAIProvider('kobold')}>
                  KoboldCpp (Local)
                </button>
                <button className={`toggle-btn ${defaultAIProvider === 'ollama' ? 'active' : ''}`} onClick={() => setDefaultAIProvider('ollama')}>
                  Ollama (Local)
                </button>
                <button className={`toggle-btn ${defaultAIProvider === 'gemini' ? 'active' : ''}`} onClick={() => setDefaultAIProvider('gemini')}>
                  Gemini (Cloud)
                </button>
              </div>
            </div>

            <div className="settings-form-group" style={{ marginTop: 20 }}>
              <label className="checkbox-label">
                <input type="checkbox" checked={autoCleanBuzzwords} onChange={(e) => setAutoCleanBuzzwords(e.target.checked)} />
                <span>{t('autoCleanBuzzwords')}</span>
              </label>
            </div>

            <div className="settings-form-group">
              <label className="checkbox-label">
                <input type="checkbox" checked={autoQuoteTargets} onChange={(e) => setAutoQuoteTargets(e.target.checked)} />
                <span>{t('autoQuoteTargets')}</span>
              </label>
            </div>

            <div className="settings-form-group" style={{ marginTop: 20 }}>
              <label className="checkbox-label">
                <input
                  type="checkbox"
                  checked={enableThinkingTokenBoost}
                  onChange={(e) => setEnableThinkingTokenBoost(e.target.checked)}
                />
                <span>{t('enableThinkingTokenBoost')}</span>
              </label>
              <p className="form-help">{t('thinkingTokenHelp')}</p>
            </div>

            {enableThinkingTokenBoost && (
              <div className="settings-form-group">
                <label>{t('maxOutputTokens')}</label>
                <select
                  value={maxOutputTokens}
                  onChange={(e) => setMaxOutputTokens(Number(e.target.value))}
                  className="glass-input"
                  style={{ width: '220px' }}
                >
                  <option value={1024}>1024 Tokens</option>
                  <option value={2048}>2048 Tokens</option>
                  <option value={4096}>4096 Tokens (Recommended)</option>
                  <option value={8192}>8192 Tokens</option>
                </select>
              </div>
            )}
          </div>
        )}

        {activeTab === 'integrations' && (
          <div className="settings-section">
            <h3>{t('apiConnections')}</h3>
            <p className="settings-description">Connect to local inference servers and cloud AI endpoints.</p>

            <div className="settings-form-group">
              <label>{t('comfyuiUrl')}</label>
              <input type="text" value={comfyUIUrl} onChange={(e) => setComfyUIUrl(e.target.value)} className="glass-input" />
              <p className="form-help">{t('comfyuiHelp')}</p>
              <button className="test-btn" onClick={() => handleTestConnection('comfyui', comfyUIUrl)}>
                {testStatus['comfyui'] === 'testing' ? t('testing') : t('testConnection')}
              </button>
              {testStatus['comfyui'] === 'success' && <span className="test-status success"><Check size={14} /> {t('connected')}</span>}
              {testStatus['comfyui'] === 'failed' && <span className="test-status failed"><AlertCircle size={14} /> {t('connectionFailed')}</span>}
            </div>

            <div className="settings-form-group">
              <label>{t('koboldUrl')}</label>
              <input type="text" value={koboldCppUrl} onChange={(e) => setKoboldCppUrl(e.target.value)} className="glass-input" />
              <p className="form-help">{t('koboldHelp')}</p>
              <button className="test-btn" onClick={() => handleTestConnection('kobold', koboldCppUrl)}>
                {testStatus['kobold'] === 'testing' ? t('testing') : t('testConnection')}
              </button>
              {testStatus['kobold'] === 'success' && <span className="test-status success"><Check size={14} /> {t('connected')}</span>}
              {testStatus['kobold'] === 'failed' && <span className="test-status failed"><AlertCircle size={14} /> {t('connectionFailed')}</span>}
            </div>

            <div className="settings-form-group">
              <label>{t('ollamaUrl')}</label>
              <input type="text" value={ollamaUrl} onChange={(e) => setOllamaUrl(e.target.value)} className="glass-input" />
              <p className="form-help">{t('ollamaHelp')}</p>
              <button className="test-btn" onClick={() => handleTestConnection('ollama', ollamaUrl)}>
                {testStatus['ollama'] === 'testing' ? t('testing') : t('testConnection')}
              </button>
              {testStatus['ollama'] === 'success' && <span className="test-status success"><Check size={14} /> {t('connected')}</span>}
              {testStatus['ollama'] === 'failed' && <span className="test-status failed"><AlertCircle size={14} /> {t('connectionFailed')}</span>}
            </div>


            <div className="settings-form-group">
              <label>{t('geminiKey')}</label>
              <input type="password" value={geminiApiKey} onChange={(e) => setGeminiApiKey(e.target.value)} placeholder="AIzaSy..." className="glass-input" />
              <p className="form-help">{t('geminiHelp')}</p>
            </div>

            <div className="settings-form-group">
              <label>📨 Discord Webhook URL</label>
              <input
                type="password"
                value={discordWebhookUrl}
                onChange={(e) => setDiscordWebhookUrl(e.target.value)}
                placeholder="https://discord.com/api/webhooks/..."
                className="glass-input"
              />
              <p className="form-help">
                Webhook used by the Matrix Studio "Send to Discord" option. Each generated image + prompt will be posted to this channel when the batch finishes.
              </p>
            </div>
          </div>
        )}

        {activeTab === 'profiles' && (
          <ModelProfileEditor />
        )}

        {activeTab === 'database' && (
          <div className="settings-section">
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
              <h3>Database & Storage Maintenance</h3>
              <button 
                className="icon-action-btn" 
                onClick={fetchStats}
                disabled={loadingStats}
                title="Refresh Database Stats"
                style={{ display: 'flex', alignItems: 'center', gap: '6px', padding: '6px 12px', borderRadius: '6px', background: 'rgba(255,255,255,0.06)', border: '1px solid var(--glass-border)', color: 'var(--fg-secondary)', cursor: 'pointer' }}
              >
                <RefreshCw size={14} className={loadingStats ? 'spin' : ''} />
                <span>{loadingStats ? 'Refreshing...' : 'Refresh Stats'}</span>
              </button>
            </div>
            <p className="settings-description">
              Monitor active database record counts, manage stored documents, and perform maintenance or resets.
            </p>

            {resetFeedback && (
              <div style={{ padding: '12px 16px', borderRadius: '8px', background: 'rgba(34, 197, 94, 0.15)', border: '1px solid rgba(34, 197, 94, 0.4)', color: '#4ade80', fontSize: '13px', marginBottom: '20px' }}>
                {resetFeedback}
              </div>
            )}

            {/* Live Stats Cards Grid */}
            <div className="database-stats-grid">
              <div className="db-stat-card">
                <div className="db-stat-header">
                  <span>Prompts</span>
                  <FileText size={16} />
                </div>
                <div className="db-stat-value">{systemStats ? systemStats.prompts_count.toLocaleString() : '...'}</div>
                <div className="db-stat-label">Saved prompt templates</div>
              </div>

              <div className="db-stat-card">
                <div className="db-stat-header">
                  <span>Wildcards</span>
                  <Sparkles size={16} />
                </div>
                <div className="db-stat-value">{systemStats ? systemStats.wildcards_count.toLocaleString() : '...'}</div>
                <div className="db-stat-label">Custom wildcard collections</div>
              </div>

              <div className="db-stat-card">
                <div className="db-stat-header">
                  <span>Tags Library</span>
                  <Tag size={16} />
                </div>
                <div className="db-stat-value">{systemStats ? systemStats.tags_count.toLocaleString() : '...'}</div>
                <div className="db-stat-label">Indexed AST & tag studio items</div>
              </div>

              <div className="db-stat-card">
                <div className="db-stat-header">
                  <span>Image Gallery</span>
                  <ImageIcon size={16} />
                </div>
                <div className="db-stat-value">{systemStats ? systemStats.images_count.toLocaleString() : '...'}</div>
                <div className="db-stat-label">Generated images in history</div>
              </div>

              <div className="db-stat-card">
                <div className="db-stat-header">
                  <span>Danbooru Lexicon</span>
                  <Database size={16} color="#c084fc" />
                </div>
                <div className="db-stat-value" style={{ color: '#c084fc' }}>
                  {systemStats ? systemStats.danbooru.total_tags.toLocaleString() : '...'}
                </div>
                <div className="db-stat-label">3.2M co-occurrence pairs</div>
                <div className="db-stat-sub">
                  {systemStats?.danbooru.ready ? `Active • ${systemStats.danbooru.db_size_mb} MB` : 'Not loaded'}
                </div>
              </div>
            </div>

            {/* Granular Table Actions */}
            <h4 style={{ fontSize: '15px', color: 'var(--fg-primary)', margin: '0 0 12px 0' }}>Granular Database Actions</h4>
            <div className="db-granular-section">
              <div className="db-action-row">
                <div className="db-action-info">
                  <span className="db-action-title">Clear Prompts</span>
                  <span className="db-action-desc">Delete all saved prompts from the database. Leaves wildcards and tags intact.</span>
                </div>
                <button 
                  className="btn-danger-outline"
                  onClick={() => handleResetScope('prompts')}
                  disabled={actionLoading !== null}
                >
                  {actionLoading === 'prompts' ? 'Clearing...' : 'Clear Prompts'}
                </button>
              </div>

              <div className="db-action-row">
                <div className="db-action-info">
                  <span className="db-action-title">Clear Wildcards</span>
                  <span className="db-action-desc">Delete all wildcard entries and collections from the database.</span>
                </div>
                <button 
                  className="btn-danger-outline"
                  onClick={() => handleResetScope('wildcards')}
                  disabled={actionLoading !== null}
                >
                  {actionLoading === 'wildcards' ? 'Clearing...' : 'Clear Wildcards'}
                </button>
              </div>

              <div className="db-action-row">
                <div className="db-action-info">
                  <span className="db-action-title">Clear Tags Library</span>
                  <span className="db-action-desc">Prune indexed tags. Tags can be re-synced anytime from Tag Studio.</span>
                </div>
                <button 
                  className="btn-danger-outline"
                  onClick={() => handleResetScope('tags')}
                  disabled={actionLoading !== null}
                >
                  {actionLoading === 'tags' ? 'Clearing...' : 'Clear Tags'}
                </button>
              </div>

              <div className="db-action-row">
                <div className="db-action-info">
                  <span className="db-action-title">Clear Image Gallery</span>
                  <span className="db-action-desc">Remove all generation metadata and saved images from gallery history.</span>
                </div>
                <button 
                  className="btn-danger-outline"
                  onClick={() => handleResetScope('gallery')}
                  disabled={actionLoading !== null}
                >
                  {actionLoading === 'gallery' ? 'Clearing...' : 'Clear Gallery'}
                </button>
              </div>
            </div>

            {/* Danger Zone: Factory Reset */}
            <div className="danger-zone">
              <div className="danger-zone-header">
                <ShieldAlert size={20} />
                <span>Danger Zone: Factory Reset</span>
              </div>
              <p className="danger-zone-desc">
                Permanently wipes all prompts, wildcards, tags, evaluation metrics, and image gallery history. This returns Prompt Studio to a fresh, pristine state.
              </p>
              <button 
                className="btn-danger-solid"
                onClick={() => { setIsResetModalOpen(true); setResetConfirmText(''); }}
              >
                <Trash2 size={16} /> Reset Entire Database
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Factory Reset Modal */}
      {isResetModalOpen && (
        <div className="reset-modal-backdrop" onClick={() => setIsResetModalOpen(false)}>
          <div className="reset-modal" onClick={(e) => e.stopPropagation()}>
            <div className="reset-modal-header">
              <AlertTriangle size={22} />
              <span>Confirm Factory Reset</span>
            </div>
            <p className="reset-modal-text">
              This action cannot be undone. All saved prompts, wildcards, custom tags, and image generations will be permanently erased.
            </p>
            <p className="reset-modal-text" style={{ fontWeight: 600, color: 'var(--fg-primary)' }}>
              Type <span style={{ color: '#ef4444', fontFamily: 'monospace' }}>RESET</span> below to confirm:
            </p>
            <input 
              type="text" 
              className="reset-modal-input"
              placeholder="RESET"
              value={resetConfirmText}
              onChange={(e) => setResetConfirmText(e.target.value)}
              autoFocus
            />
            <div className="reset-modal-actions">
              <button className="btn-secondary" onClick={() => setIsResetModalOpen(false)}>
                Cancel
              </button>
              <button 
                className="btn-danger-solid"
                disabled={resetConfirmText !== 'RESET' || actionLoading !== null}
                onClick={handleFactoryReset}
              >
                {actionLoading === 'all' ? 'Resetting...' : 'Permanently Reset Everything'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
