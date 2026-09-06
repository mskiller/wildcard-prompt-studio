import React, { useRef, useEffect } from 'react';
import Editor, { useMonaco, OnMount } from '@monaco-editor/react';
import { setupMonacoEnvironment } from './monacoConfig';
import * as api from '../../api';

interface MonacoPromptEditorProps {
  value: string;
  onChange: (value: string | undefined) => void;
}

export const MonacoPromptEditor: React.FC<MonacoPromptEditorProps> = ({ value, onChange }) => {
  const monaco = useMonaco();
  const providerRef = useRef<any>(null);

  useEffect(() => {
    if (monaco) {
      setupMonacoEnvironment(monaco);
      
      // Register Autocomplete for wildcards and tags
      if (!providerRef.current) {
        providerRef.current = monaco.languages.registerCompletionItemProvider('prompt-lang', {
          triggerCharacters: ['_', '#'],
          provideCompletionItems: async (model, position) => {
            const word = model.getWordUntilPosition(position);
            const range = {
              startLineNumber: position.lineNumber,
              endLineNumber: position.lineNumber,
              startColumn: word.startColumn,
              endColumn: word.endColumn
            };

            const textUntilPosition = model.getValueInRange({
              startLineNumber: position.lineNumber,
              startColumn: 1,
              endLineNumber: position.lineNumber,
              endColumn: position.column
            });

            // 1. Wildcards Autocomplete (e.g. __)
            if (textUntilPosition.match(/__$/)) {
              try {
                const wildcards = await api.getWildcards();
                const suggestions = wildcards.map(w => ({
                  label: w.name,
                  kind: monaco.languages.CompletionItemKind.Variable,
                  insertText: w.name + '__',
                  range: range,
                  detail: 'Wildcard',
                  documentation: `Wildcard: __${w.name}__`
                }));
                return { suggestions };
              } catch (e) {
                return { suggestions: [] };
              }
            }

            // 2. Tag Autocomplete triggered by '#' (e.g. #cyber or #)
            const hashMatch = textUntilPosition.match(/#([a-zA-Z0-9_\-]*)$/);
            if (hashMatch) {
              const tagPrefix = hashMatch[1];
              const hashRange = {
                startLineNumber: position.lineNumber,
                endLineNumber: position.lineNumber,
                startColumn: position.column - tagPrefix.length - 1, // replace '#' too
                endColumn: position.column
              };

              try {
                const tags = await api.getTags({ q: tagPrefix || undefined, limit: 40 });
                const suggestions = tags.map(t => ({
                  label: t.name,
                  kind: monaco.languages.CompletionItemKind.Keyword,
                  insertText: t.name,
                  range: hashRange,
                  detail: `[${t.category}] Tag`,
                  documentation: `Prompt Tag: "${t.name}" (${t.category})`
                }));
                return { suggestions };
              } catch (e) {
                return { suggestions: [] };
              }
            }

            return { suggestions: [] };
          }
        });
      }
    }

    return () => {
      if (providerRef.current) {
        providerRef.current.dispose();
        providerRef.current = null;
      }
    };
  }, [monaco]);

  const handleEditorMount: OnMount = (editor) => {
    editor.focus();
  };

  return (
    <div className="glass-panel" style={{ flex: 1, overflow: 'hidden', padding: '10px' }}>
      <Editor
        height="100%"
        language="prompt-lang"
        theme="prompt-dark"
        value={value}
        onChange={onChange}
        onMount={handleEditorMount}
        options={{
          minimap: { enabled: false },
          fontSize: 14,
          fontFamily: "'JetBrains Mono', 'Fira Code', monospace",
          lineHeight: 1.6,
          padding: { top: 16 },
          scrollBeyondLastLine: false,
          smoothScrolling: true,
          cursorBlinking: "smooth",
          cursorSmoothCaretAnimation: "on",
          formatOnType: true,
          wordWrap: "on"
        }}
      />
    </div>
  );
};
