import React, { useState, useEffect } from 'react';
import { getProfiles, createProfile, updateProfile } from '../../api';
import { useAppStore } from '../../store/useAppStore';

export const ModelProfileEditor: React.FC = () => {
  const triggerRefresh = useAppStore(state => state.triggerRefresh);
  const [profiles, setProfiles] = useState<any[]>([]);
  const [activeProfileId, setActiveProfileId] = useState<number | null>(null);
  
  const [name, setName] = useState('');
  const [defaultNegativePrompt, setDefaultNegativePrompt] = useState('');
  const [triggerWords, setTriggerWords] = useState('');
  const [customRules, setCustomRules] = useState('');

  const [saving, setSaving] = useState(false);

  useEffect(() => {
    loadProfiles();
  }, []);

  const loadProfiles = async () => {
    try {
      const data = await getProfiles();
      setProfiles(data);
      if (data.length > 0 && !activeProfileId) {
        selectProfile(data[0]);
      }
    } catch (err) {
      console.error(err);
    }
  };

  const selectProfile = (profile: any) => {
    setActiveProfileId(profile.id);
    setName(profile.name);
    setDefaultNegativePrompt(profile.default_negative_prompt || '');
    setTriggerWords(profile.trigger_words || '');
    setCustomRules(profile.custom_rules || '');
  };

  const handleCreateNew = () => {
    setActiveProfileId(null);
    setName('New Profile');
    setDefaultNegativePrompt('');
    setTriggerWords('');
    setCustomRules('');
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      const payload = {
        name,
        default_negative_prompt: defaultNegativePrompt,
        trigger_words: triggerWords,
        custom_rules: customRules
      };

      if (activeProfileId) {
        await updateProfile(activeProfileId, payload);
      } else {
        const newProfile = await createProfile(payload);
        setActiveProfileId(newProfile.id);
      }
      await loadProfiles();
      triggerRefresh();
    } catch (err) {
      console.error(err);
      alert("Failed to save profile.");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="settings-section">
      <h3>Model Profiles</h3>
      <p className="settings-description">
        Define custom rules, negative prompts, and trigger words for different AI generation models.
      </p>

      <div style={{ display: 'flex', gap: '20px', marginBottom: '24px' }}>
        <select 
          className="glass-input" 
          style={{ width: '250px' }}
          value={activeProfileId || ''}
          onChange={(e) => {
            const pId = parseInt(e.target.value);
            const p = profiles.find(x => x.id === pId);
            if (p) selectProfile(p);
          }}
        >
          <option value="" disabled>Select Profile</option>
          {profiles.map(p => (
            <option key={p.id} value={p.id}>{p.name}</option>
          ))}
        </select>
        <button className="primary-button" onClick={handleCreateNew}>Create New</button>
        <button 
          className="primary-button" 
          style={{ background: '#cba6f7', color: '#11111b' }}
          onClick={() => {
            setActiveProfileId(null);
            setName('Krea 2');
            setDefaultNegativePrompt('');
            setTriggerWords('');
            setCustomRules('Faithfulness first. Direct T2I natural language structure: [Subject] in [Setting] with [Lighting/Camera Optics]. Automatically wrap text targets in double quotes like "hello world". Do not use SD anti-patterns like 8k, masterpiece, or hyper-detailed.');
          }}
        >
          + Load Krea 2 Preset
        </button>
      </div>


      <div className="settings-form-group">
        <label>Profile Name</label>
        <input 
          type="text" 
          className="glass-input" 
          value={name}
          onChange={(e) => setName(e.target.value)}
        />
      </div>

      <div className="settings-form-group">
        <label>Default Negative Prompt</label>
        <textarea 
          className="glass-input" 
          value={defaultNegativePrompt}
          onChange={(e) => setDefaultNegativePrompt(e.target.value)}
          placeholder="e.g. low quality, worst quality, bad anatomy..."
        />
      </div>

      <div className="settings-form-group">
        <label>Trigger Words</label>
        <input 
          type="text" 
          className="glass-input" 
          value={triggerWords}
          onChange={(e) => setTriggerWords(e.target.value)}
          placeholder="e.g. 1girl, masterpiece"
        />
        <p className="form-help">Words that should automatically be appended to prompts using this model.</p>
      </div>

      <div className="settings-form-group">
        <label>Custom AI Rules</label>
        <textarea 
          className="glass-input" 
          value={customRules}
          onChange={(e) => setCustomRules(e.target.value)}
          placeholder="e.g. This model prefers natural language over tags. Do not use danbooru tags."
          style={{ minHeight: '120px' }}
        />
        <p className="form-help">Instructions given to the AI Assistant when asking it to expand or improve prompts for this specific model.</p>
      </div>

      <button className="primary-button" onClick={handleSave} disabled={saving}>
        {saving ? 'Saving...' : 'Save Profile'}
      </button>
    </div>
  );
};
