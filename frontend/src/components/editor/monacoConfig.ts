import * as monaco from 'monaco-editor';

export function setupMonacoEnvironment(monacoInstance: typeof monaco) {
  // Define custom language for .prompt
  monacoInstance.languages.register({ id: 'prompt-lang' });

  // Define Monarch tokens provider
  monacoInstance.languages.setMonarchTokensProvider('prompt-lang', {
    tokenizer: {
      root: [
        // Frontmatter
        [/^---$/, { token: 'meta.frontmatter', next: '@frontmatter' }],
        
        // Wildcards: __color__
        [/__[a-zA-Z0-9_/\-]+__/, 'keyword.wildcard'],
        
        // Inline choices: {a|b|c}
        [/\{[^{}]*\}/, 'string.choice'],
        
        // Dynamic Macros: $range(...), $repeat(...)
        [/\$[a-zA-Z0-9_]+\([^)]*\)/, 'keyword.macro'],
        
        // Variable assignments and references: $var = ... or $var
        [/\$[a-zA-Z0-9_]+/, 'variable.ref'],

        // Danbooru Tag Category Tokens
        [/by\s+[a-zA-Z0-9_]+/, 'tag.artist'],
        [/hatsune miku|1girl|1boy|character/, 'tag.character'],
        [/genshin|fate|pokemon|vocaloid/, 'tag.copyright'],
        [/masterpiece|highres|absurdres|solo/, 'tag.meta'],

        // Settings block: [Setting: value]
        [/\[[a-zA-Z0-9_]+:.*\]/, 'annotation.setting'],
      ],
      frontmatter: [
        [/^---$/, { token: 'meta.frontmatter', next: '@pop' }],
        [/[a-zA-Z0-9_-]+:/, 'keyword.yaml-key'],
        [/.*$/, 'string.yaml-value'],
      ]
    }
  });

  // Define custom theme with Danbooru tag colors
  monacoInstance.editor.defineTheme('prompt-dark', {
    base: 'vs-dark',
    inherit: true,
    rules: [
      { token: 'meta.frontmatter', foreground: '5c6370', fontStyle: 'bold' },
      { token: 'keyword.yaml-key', foreground: 'e06c75' },
      { token: 'string.yaml-value', foreground: '98c379' },
      { token: 'keyword.wildcard', foreground: 'c678dd', fontStyle: 'bold' },
      { token: 'string.choice', foreground: '61afef' },
      { token: 'keyword.macro', foreground: 'e5c07b', fontStyle: 'bold' },
      { token: 'variable.ref', foreground: '56b6c2' },

      // Danbooru Tag Colors Standard
      { token: 'tag.artist', foreground: 'C00000', fontStyle: 'bold' },      // Red (#C00000)
      { token: 'tag.character', foreground: '00A000', fontStyle: 'bold' },   // Green (#00A000)
      { token: 'tag.copyright', foreground: 'A000A0', fontStyle: 'bold' },   // Purple (#A000A0)
      { token: 'tag.general', foreground: '0073FF' },                       // Blue (#0073FF)
      { token: 'tag.meta', foreground: 'FF8C00', fontStyle: 'italic' },     // Orange (#FF8C00)

      { token: 'annotation.setting', foreground: 'd19a66', fontStyle: 'italic' },
    ],
    colors: {
      'editor.background': '#1e222d',
      'editor.lineHighlightBackground': '#2c313c',
    }
  });
}
