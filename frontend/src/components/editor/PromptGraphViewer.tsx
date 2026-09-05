import React, { useState } from 'react';
import { getSimulationTree, getTagRecommendations } from '../../api';
import './PromptGraphViewer.css';

export const PromptGraphViewer: React.FC = () => {
  const [template, setTemplate] = useState<string>('a {cute|fierce} __animals/cat__ in {cyberpunk|fantasy} city');
  const [treeData, setTreeData] = useState<any>(null);
  const [recommendations, setRecommendations] = useState<string[]>([]);
  const [loading, setLoading] = useState<boolean>(false);

  const handleSimulate = async () => {
    setLoading(true);
    try {
      const res = await getSimulationTree(template);
      setTreeData(res.tree);
      const recs = await getTagRecommendations(['cyberpunk']);
      setRecommendations(recs);
    } catch (e: any) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const renderNode = (node: any, depth: number = 0) => {
    if (!node) return null;
    return (
      <div key={depth + Math.random()} style={{ marginLeft: depth * 20, marginTop: 4 }}>
        <span className={`tree-node-box ${node.type}`}>
          [{node.type.toUpperCase()}] {node.label}
        </span>
        {node.children && node.children.map((c: any) => renderNode(c, depth + 1))}
      </div>
    );
  };

  return (
    <div className="graph-viewer-panel">
      <h2>Prompt AST Graph & Tag Recommendation Engine</h2>
      <div style={{ display: 'flex', gap: '1rem' }}>
        <input
          type="text"
          value={template}
          onChange={(e) => setTemplate(e.target.value)}
          style={{ flex: 1, padding: '0.6rem', borderRadius: 6, border: '1px solid rgba(255,255,255,0.2)', background: 'rgba(0,0,0,0.3)', color: '#fff' }}
        />
        <button
          onClick={handleSimulate}
          disabled={loading}
          style={{ padding: '0.6rem 1.2rem', borderRadius: 6, border: 'none', background: '#cba6f7', color: '#11111b', fontWeight: 600, cursor: 'pointer' }}
        >
          {loading ? 'Analyzing...' : 'Parse AST Graph'}
        </button>
      </div>

      {treeData && (
        <div className="graph-tree-container">
          <h3>AST Parse Tree Hierarchy</h3>
          {renderNode(treeData)}
        </div>
      )}

      {recommendations.length > 0 && (
        <div>
          <h3>Contextual Tag Recommendations</h3>
          <div className="recommendations-box">
            {recommendations.map((tag, idx) => (
              <span key={idx} className="tag-chip">
                + {tag}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
