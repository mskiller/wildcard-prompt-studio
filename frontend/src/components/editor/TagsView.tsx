import React, { useEffect, useState } from 'react';
import { Tag } from 'lucide-react';
import { getTags } from '../../api';
import './TagsView.css';

export const TagsView: React.FC = () => {
  const [tags, setTags] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchTags = async () => {
      try {
        const t = await getTags();
        setTags(t);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    fetchTags();
  }, []);

  return (
    <div className="tags-view-container glass-panel">
      <div className="tags-header">
        <Tag size={24} color="var(--accent-primary)" />
        <h2>Tag Database</h2>
      </div>
      
      <p className="tags-description">
        These are the tags extracted from your wildcards and prompts. They can be used to categorize your library.
      </p>

      {loading ? (
        <div className="spinner"></div>
      ) : tags.length === 0 ? (
        <div className="empty-state">No tags found. Import some wildcards to populate tags!</div>
      ) : (
        <div className="tags-grid">
          {tags.map(t => (
            <div key={t.id} className="tag-card">
              <span className="tag-name">{t.name}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
