# Export .txt File Feature Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add an Export .txt file capability to the File Explorer Editor (`PromptEditor.tsx`) and Sidebar tree (`Sidebar.tsx`) to download active prompts and wildcards as `.txt` files.

**Architecture:** Create a `fileExporter.ts` utility that generates client-side text file downloads, then integrate an `Export .txt` button into the `PromptEditor` toolbar and quick export buttons into `Sidebar.tsx`.

**Tech Stack:** React, TypeScript, Vitest, Lucide React (`Download` icon).

---

### Task 1: Create File Exporter Utility & Tests

**Files:**
- Create: `frontend/src/utils/fileExporter.ts`
- Create: `frontend/src/utils/fileExporter.test.ts`

- [ ] **Step 1: Write tests for `sanitizeFilename` and `exportAsTxtFile`**

Create `frontend/src/utils/fileExporter.test.ts`:
```typescript
import { describe, it, expect } from 'vitest';
import { sanitizeFilename } from './fileExporter';

describe('sanitizeFilename', () => {
  it('adds .txt extension if missing', () => {
    expect(sanitizeFilename('my_wildcard')).toBe('my_wildcard.txt');
  });

  it('preserves existing .txt extension', () => {
    expect(sanitizeFilename('prompt.txt')).toBe('prompt.txt');
  });

  it('replaces unsafe characters in filenames', () => {
    expect(sanitizeFilename('my/unsafe:file?name')).toBe('my_unsafe_file_name.txt');
  });

  it('uses default fallback if empty', () => {
    expect(sanitizeFilename('')).toBe('export.txt');
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd frontend && npm test src/utils/fileExporter.test.ts`
Expected: FAIL (module `fileExporter` not found)

- [ ] **Step 3: Implement `fileExporter.ts`**

Create `frontend/src/utils/fileExporter.ts`:
```typescript
/**
 * Ensures filename ends with .txt and removes invalid filesystem characters.
 */
export function sanitizeFilename(name: string, fallback = 'export.txt'): string {
  if (!name || !name.trim()) return fallback;

  let cleaned = name.trim().replace(/[/\\?%*:|"<>]/g, '_');
  if (!cleaned.toLowerCase().endsWith('.txt')) {
    cleaned += '.txt';
  }
  return cleaned;
}

/**
 * Triggers a browser download of text content as a .txt file.
 */
export function exportAsTxtFile(filename: string, content: string): void {
  const finalName = sanitizeFilename(filename);
  const blob = new Blob([content], { type: 'text/plain;charset=utf-8' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = finalName;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd frontend && npm test src/utils/fileExporter.test.ts`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add frontend/src/utils/fileExporter.ts frontend/src/utils/fileExporter.test.ts
git commit -m "feat: add fileExporter utility for txt export"
```

---

### Task 2: Add Export .txt Button to Prompt Editor Toolbar

**Files:**
- Modify: `frontend/src/components/editor/PromptEditor.tsx`

- [ ] **Step 1: Update imports in `PromptEditor.tsx`**

Add `Download` to `lucide-react` imports and import `exportAsTxtFile` from `../../utils/fileExporter`:
```typescript
import { Code, LayoutTemplate, FileText, Sparkles, Image as ImageIcon, SlidersHorizontal, Wand2, Save, MessageSquare, Download } from 'lucide-react';
import { exportAsTxtFile } from '../../utils/fileExporter';
```

- [ ] **Step 2: Add `handleExportTxt` click handler**

Inside `PromptEditor` component:
```typescript
  const handleExportTxt = () => {
    if (!promptText) return;
    const defaultName = activeDocument ? activeDocument.name : 'prompt_export.txt';
    exportAsTxtFile(defaultName, promptText);
    showToast(`Exported ${defaultName.endsWith('.txt') ? defaultName : defaultName + '.txt'}!`, 'success');
  };
```

- [ ] **Step 3: Add Export .txt button in toolbar**

Right after the `Save` button in `.toolbar-tabs`:
```tsx
            <button 
              className="tab-btn"
              onClick={handleExportTxt}
              disabled={!promptText.trim()}
              style={{ color: 'var(--accent-primary, #6366f1)', fontWeight: 600 }}
              title="Export working text as .txt file"
            >
              <Download size={16} /> Export .txt
            </button>
```

- [ ] **Step 4: Commit**

```bash
git add frontend/src/components/editor/PromptEditor.tsx
git commit -m "feat: add Export .txt button to PromptEditor toolbar"
```

---

### Task 3: Add Quick Export Action Icons to Sidebar Tree

**Files:**
- Modify: `frontend/src/components/layout/Sidebar.tsx`

- [ ] **Step 1: Update imports in `Sidebar.tsx`**

Add `Download` to `lucide-react` imports and import `exportAsTxtFile` from `../../utils/fileExporter`:
```typescript
import { Download } from 'lucide-react';
import { exportAsTxtFile } from '../../utils/fileExporter';
```

- [ ] **Step 2: Add quick export buttons to wildcard and prompt tree items**

Add helper handler in `Sidebar.tsx`:
```typescript
  const handleQuickExport = (e: React.MouseEvent, name: string, content: string) => {
    e.stopPropagation();
    exportAsTxtFile(name, content || '');
  };
```

Update item rendering in `Sidebar.tsx` for prompts, wildcards, and explorer sections to include a quick export icon on hover:
```tsx
  <button 
    className="icon-action-btn" 
    onClick={(e) => handleQuickExport(e, p.name, p.content)} 
    title={`Export ${p.name} as .txt`}
    style={{ background: 'transparent', border: 'none', color: 'var(--fg-muted)', cursor: 'pointer', padding: '2px 4px', marginLeft: 'auto' }}
  >
    <Download size={13} />
  </button>
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/layout/Sidebar.tsx
git commit -m "feat: add quick export buttons to Sidebar tree items"
```
