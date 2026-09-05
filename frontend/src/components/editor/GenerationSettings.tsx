import React, { useEffect, useState } from 'react';
import { getGenerationOptions, GenerationSettings as ISettings } from '../../api';
import { useAppStore } from '../../store/useAppStore';
import { Settings, RefreshCw } from 'lucide-react';
import './GenerationSettings.css';

interface GenerationSettingsProps {
  settings: ISettings;
  setSettings: (settings: ISettings) => void;
  onGenerate: () => void;
  isGenerating: boolean;
}

const SDXL_RESOLUTIONS = [
  { label: 'Square (1024x1024)', width: 1024, height: 1024 },
  { label: 'Portrait (896x1152)', width: 896, height: 1152 },
  { label: 'Landscape (1152x896)', width: 1152, height: 896 },
  { label: 'Tall (832x1216)', width: 832, height: 1216 },
  { label: 'Wide (1216x832)', width: 1216, height: 832 },
  { label: 'Vertical (768x1344)', width: 768, height: 1344 },
  { label: 'Horizontal (1344x768)', width: 1344, height: 768 },
];

const DEFAULT_MODELS = [
  'v1-5-pruned-emaonly.safetensors',
  'sd_xl_base_1.0.safetensors',
  'sd_xl_refiner_1.0.safetensors',
  'flux1-dev.safetensors'
];
const DEFAULT_SAMPLERS = ['euler', 'euler_ancestral', 'heun', 'dpm_2', 'dpmpp_2m', 'dpmpp_sde', 'ddim', 'uni_pc'];
const DEFAULT_SCHEDULERS = ['normal', 'karras', 'exponential', 'sgm_uniform', 'simple', 'ddim_uniform'];

export const GenerationSettings: React.FC<GenerationSettingsProps> = ({ settings, setSettings, onGenerate, isGenerating }) => {
  const { comfyUIUrl } = useAppStore();
  const [options, setOptions] = useState<{ models: string[], samplers: string[], schedulers: string[] }>({
    models: DEFAULT_MODELS, samplers: DEFAULT_SAMPLERS, schedulers: DEFAULT_SCHEDULERS
  });
  const [isComfyConnected, setIsComfyConnected] = useState<boolean>(true);
  const [loadingOpts, setLoadingOpts] = useState(false);
  const [isCustomRes, setIsCustomRes] = useState(false);

  const fetchOptions = async () => {
    setLoadingOpts(true);
    try {
      const data = await getGenerationOptions(comfyUIUrl);
      setIsComfyConnected(data.connected !== false);
      const fetchedModels = data.models && data.models.length > 0 ? data.models : DEFAULT_MODELS;
      const fetchedSamplers = data.samplers && data.samplers.length > 0 ? data.samplers : DEFAULT_SAMPLERS;
      const fetchedSchedulers = data.schedulers && data.schedulers.length > 0 ? data.schedulers : DEFAULT_SCHEDULERS;

      setOptions({
        models: fetchedModels,
        samplers: fetchedSamplers,
        schedulers: fetchedSchedulers
      });
      
      // Auto-select defaults if not set or invalid
      if (!settings.model || !fetchedModels.includes(settings.model)) {
        updateSetting('model', fetchedModels[0]);
      }
      if (!settings.sampler || !fetchedSamplers.includes(settings.sampler)) {
        updateSetting('sampler', fetchedSamplers[0]);
      }
      if (!settings.scheduler || !fetchedSchedulers.includes(settings.scheduler)) {
        updateSetting('scheduler', fetchedSchedulers[0]);
      }
    } catch (err) {
      console.error('Failed to fetch generation options:', err);
      setIsComfyConnected(false);
    } finally {
      setLoadingOpts(false);
    }
  };

  useEffect(() => {
    fetchOptions();
  }, [comfyUIUrl]);

  const updateSetting = (key: keyof ISettings, value: any) => {
    setSettings({ ...settings, [key]: value });
  };

  const handleResolutionChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const val = e.target.value;
    if (val === 'custom') {
      setIsCustomRes(true);
    } else {
      setIsCustomRes(false);
      const res = SDXL_RESOLUTIONS.find(r => r.label === val);
      if (res) {
        setSettings({ ...settings, width: res.width, height: res.height });
      }
    }
  };

  return (
    <div className="generation-settings glass-panel">
      <div className="settings-header">
        <Settings size={18} />
        <h4>Generation Settings</h4>
        <span style={{
          fontSize: '11px',
          padding: '2px 8px',
          borderRadius: '10px',
          marginLeft: 'auto',
          marginRight: '8px',
          background: isComfyConnected ? 'rgba(34, 197, 94, 0.15)' : 'rgba(239, 68, 68, 0.15)',
          color: isComfyConnected ? '#4ade80' : '#f87171',
          border: `1px solid ${isComfyConnected ? 'rgba(34, 197, 94, 0.3)' : 'rgba(239, 68, 68, 0.3)'}`
        }}>
          {isComfyConnected ? `✓ Live (${options.models.length})` : '⚠️ Fallback'}
        </span>
        <button className="refresh-btn" onClick={fetchOptions} disabled={loadingOpts} title="Refresh Models from ComfyUI">
          <RefreshCw size={14} className={loadingOpts ? 'spinning' : ''} />
        </button>
      </div>

      <div className="settings-body">
        <div className="settings-row">
          <label>Model (Checkpoint)</label>
          <select 
            className="glass-input" 
            value={settings.model || options.models[0] || ''} 
            onChange={(e) => updateSetting('model', e.target.value)}
          >
            {options.models.map(m => <option key={m} value={m}>{m}</option>)}
          </select>
        </div>

        <div className="settings-row split">
          <div className="settings-col">
            <label>Sampler</label>
            <select 
              className="glass-input" 
              value={settings.sampler || options.samplers[0] || 'euler'} 
              onChange={(e) => updateSetting('sampler', e.target.value)}
            >
              {options.samplers.map(s => <option key={s} value={s}>{s}</option>)}
            </select>
          </div>
          <div className="settings-col">
            <label>Scheduler</label>
            <select 
              className="glass-input" 
              value={settings.scheduler || options.schedulers[0] || 'normal'} 
              onChange={(e) => updateSetting('scheduler', e.target.value)}
            >
              {options.schedulers.map(s => <option key={s} value={s}>{s}</option>)}
            </select>
          </div>
        </div>

        <div className="settings-row split">
          <div className="settings-col">
            <label>Steps ({settings.steps})</label>
            <input type="range" min="1" max="100" value={settings.steps} onChange={(e) => updateSetting('steps', parseInt(e.target.value))} />
          </div>
          <div className="settings-col">
            <label>CFG Scale ({settings.cfg})</label>
            <input type="range" min="1" max="20" step="0.5" value={settings.cfg} onChange={(e) => updateSetting('cfg', parseFloat(e.target.value))} />
          </div>
        </div>

        <div className="settings-row">
          <label>Resolution</label>
          <select className="glass-input" onChange={handleResolutionChange} defaultValue="Square (1024x1024)">
            {SDXL_RESOLUTIONS.map(r => <option key={r.label} value={r.label}>{r.label}</option>)}
            <option value="custom">Custom...</option>
          </select>
          
          {isCustomRes && (
            <div className="custom-res-inputs">
              <input type="number" className="glass-input" value={settings.width} onChange={(e) => updateSetting('width', parseInt(e.target.value))} placeholder="Width" />
              <span>x</span>
              <input type="number" className="glass-input" value={settings.height} onChange={(e) => updateSetting('height', parseInt(e.target.value))} placeholder="Height" />
            </div>
          )}
        </div>
      </div>

      <div className="settings-footer">
        <button className="primary-button full-width" onClick={onGenerate} disabled={isGenerating}>
          {isGenerating ? 'Generating...' : 'Generate Image'}
        </button>
      </div>
    </div>
  );
};
