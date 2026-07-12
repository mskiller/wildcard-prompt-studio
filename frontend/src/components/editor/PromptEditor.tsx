import React from 'react';
import Editor from '@monaco-editor/react';
import { usePromptStore } from '../../store/usePromptStore';

export const PromptEditor: React.FC = () => {
  const { promptText, setPromptText } = usePromptStore();

  const handleEditorChange = (value: string | undefined) => {
    if (value !== undefined) {
      setPromptText(value);
    }
  };

  return (
    <div style={{ width: '100%', height: '100%' }}>
      <Editor
        height="100%"
        width="100%"
        theme="vs-dark"
        language="plaintext"
        value={promptText}
        onChange={handleEditorChange}
        options={{
          wordWrap: 'on',
          minimap: { enabled: false },
          fontSize: 14,
          fontFamily: 'var(--vscode-font-family)',
          padding: { top: 16 }
        }}
      />
    </div>
  );
};
