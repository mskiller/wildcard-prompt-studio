import React, { useState, useEffect } from 'react';
import { scoreAestheticPrompt, evolvePrompts, searchCivitaiHub } from '../../api';
import './AestheticRankerPanel.css';

export const AestheticRankerPanel: React.FC = () => {
  const [prompts, setPrompts] = useState<string[]>([
    'a {cyberpunk|steampunk} city with neon lighting',
    'a photorealistic portrait of an astronaut',
    'a fantasy castle on a mountain peak'
  ]);
  const [scores, setScores] = useState<number[]>([]);
  const [hubResults, setHubResults] = useState<any[]>([]);
  const [loading, setLoading] = useState<boolean>(false);

  const handleEvaluate = async () => {
    setLoading(true);
    try {
      const calculatedScores = await Promise.all(prompts.map(p => scoreAestheticPrompt(p)));
      setScores(calculatedScores);
    } catch (e: any) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const handleEvolvePopulation = async () => {
    if (scores.length === 0) return;
    setLoading(true);
    try {
      const nextGen = await evolvePrompts(prompts, scores);
      setPrompts(nextGen);
      const nextScores = await Promise.all(nextGen.map(p => scoreAestheticPrompt(p)));
      setScores(nextScores);
    } catch (e: any) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    searchCivitaiHub('wildcard').then(res => setHubResults(res)).catch(() => {});
  }, []);

  return (
    <div className="aesthetic-panel">
      <h2>Aesthetic Scoring, Genetic Optimization & Model Hub Sync</h2>

      <div className="aesthetic-section">
        <h3>Genetic Prompt Optimizer (Population)</h3>
        <div style={{ display: 'flex', gap: '0.75rem' }}>
          <button onClick={handleEvaluate} disabled={loading} style={{ padding: '0.6rem 1.2rem', background: '#89b4fa', color: '#11111b', border: 'none', borderRadius: 6, fontWeight: 600, cursor: 'pointer' }}>
            Score Population Aesthetics
          </button>
          <button onClick={handleEvolvePopulation} disabled={loading || scores.length === 0} style={{ padding: '0.6rem 1.2rem', background: '#a6e3a1', color: '#11111b', border: 'none', borderRadius: 6, fontWeight: 600, cursor: 'pointer' }}>
            Evolve Next Generation
          </button>
        </div>

        {prompts.map((p, idx) => (
          <div key={idx} className="civitai-card">
            <span>{p}</span>
            {scores[idx] !== undefined && <span className="score-badge">Score: {scores[idx]} / 10</span>}
          </div>
        ))}
      </div>

      <div className="aesthetic-section">
        <h3>Civitai / HuggingFace Model Hub Wildcard Sync</h3>
        {hubResults.map((pack) => (
          <div key={pack.id} className="civitai-card">
            <div>
              <strong>{pack.name}</strong>
              <div style={{ fontSize: '0.8rem', color: '#a6adc8' }}>Downloads: {pack.downloads}</div>
            </div>
            <button style={{ padding: '0.4rem 0.8rem', background: '#cba6f7', color: '#11111b', border: 'none', borderRadius: 4, cursor: 'pointer' }}>
              Sync Pack
            </button>
          </div>
        ))}
      </div>
    </div>
  );
};
