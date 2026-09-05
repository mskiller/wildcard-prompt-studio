import React from 'react';
import './MobilePromptToolbar.css';

interface MobilePromptToolbarProps {
  onInsertText: (text: string) => void;
}

export const MobilePromptToolbar: React.FC<MobilePromptToolbarProps> = ({ onInsertText }) => {
  const shortcuts = [
    { label: '{a|b}', insert: '{option1 | option2}' },
    { label: '__wildcard__', insert: '__colors__' },
    { label: '(weight)', insert: '(masterpiece:1.2)' },
    { label: '[negative]', insert: '[blurry, low quality]' },
    { label: '8k photo', insert: 'hyperrealistic, 8k resolution, cinematic lighting' },
  ];

  return (
    <div className="mobile-prompt-toolbar">
      {shortcuts.map((sc, i) => (
        <button key={i} className="syntax-pill-btn" onClick={() => onInsertText(sc.insert)}>
          {sc.label}
        </button>
      ))}
    </div>
  );
};
