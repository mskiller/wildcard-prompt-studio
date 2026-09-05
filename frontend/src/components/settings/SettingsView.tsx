import React, { useState, useEffect } from 'react';
import { useAppStore } from '../../store/useAppStore';
import { Cpu, Box, Moon, Sun, Globe, Wand2, Check, AlertCircle } from 'lucide-react';
import { ModelProfileEditor } from './ModelProfileEditor';
import { testIntegrationConnection } from '../../api';
import './SettingsView.css';

export const SettingsView: React.FC = () => {
  const {
    theme, setTheme,
    language, setLanguage,
    t,
    comfyUIUrl, setComfyUIUrl,
    koboldCppUrl, setKoboldCppUrl,
    ollamaUrl, setOllamaUrl,
    geminiApiKey, setGeminiApiKey,
    defaultKreaVariant, setDefaultKreaVariant,
    defaultAIProvider, setDefaultAIProvider,
    autoCleanBuzzwords, setAutoCleanBuzzwords,
    autoQuoteTargets, setAutoQuoteTargets,
    enableThinkingTokenBoost, setEnableThinkingTokenBoost,
    maxOutputTokens, setMaxOutputTokens
  } = useAppStore();

  const [activeTab, setActiveTab] = useState<'appearance' | 'prompt' | 'integrations' | 'profiles'>('appearance');
  const [testStatus, setTestStatus] = useState<Record<string, 'idle' | 'testing' | 'success' | 'failed'>>({});

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
  }, [theme]);

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
          </div>
        )}

        {activeTab === 'profiles' && (
          <ModelProfileEditor />
        )}
      </div>
    </div>
  );
};
