import React, { useEffect, useRef } from 'react';
import { DiffEditor, useMonaco } from '@monaco-editor/react';
import { setupMonacoEnvironment } from './monacoConfig';

interface DiffViewerProps {
  original: string;
  modified: string;
}

export const DiffViewer: React.FC<DiffViewerProps> = ({ original, modified }) => {
  const monaco = useMonaco();
  const diffEditorRef = useRef<any>(null);

  useEffect(() => {
    if (monaco) {
      setupMonacoEnvironment(monaco);
    }
  }, [monaco]);

  useEffect(() => {
    return () => {
      if (diffEditorRef.current) {
        try {
          diffEditorRef.current.setModel({ original: null, modified: null });
        } catch (e) {
          // Model already disposed
        }
      }
    };
  }, []);

  const handleDiffMount = (editor: any) => {
    diffEditorRef.current = editor;
  };

  return (
    <div className="glass-panel" style={{ width: '100%', height: '100%', minHeight: '300px', display: 'flex', flexDirection: 'column', overflow: 'hidden', padding: '8px' }}>
      <DiffEditor
        height="100%"
        width="100%"
        language="prompt-lang"
        theme="prompt-dark"
        original={original}
        modified={modified}
        onMount={handleDiffMount}
        options={{
          automaticLayout: true,
          minimap: { enabled: false },
          fontSize: 13,
          fontFamily: "'JetBrains Mono', 'Fira Code', monospace",
          lineHeight: 1.5,
          renderSideBySide: true,
          readOnly: true,
          wordWrap: 'on',
          scrollBeyondLastLine: false,
          padding: { top: 12 }
        }}
      />
    </div>
  );
};
