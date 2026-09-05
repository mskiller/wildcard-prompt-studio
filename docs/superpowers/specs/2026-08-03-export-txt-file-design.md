# Export .txt File Feature Design

## Overview
Add a dedicated **Export .txt** button in the File Explorer Editor (`PromptEditor.tsx`) and quick export action icons in the Sidebar tree (`Sidebar.tsx`) to allow users to export their active wildcards or prompts as standard `.txt` text files directly to their device.

---

## User Review & Approval
- User approved the design on 2026-08-03.
- Approach: Dual Export options — Primary `Export .txt` button in `PromptEditor.tsx` toolbar + quick download icon on file tree items in `Sidebar.tsx`.

---

## Architecture & Component Design

### 1. Download Helper Utility (`src/utils/fileExporter.ts`)
A dedicated helper function `exportAsTxtFile(filename: string, content: string)`:
- Sanitizes the filename to ensure it ends with `.txt` and contains valid file characters.
- Uses `Blob` and `URL.createObjectURL`:
  ```typescript
  const blob = new Blob([content], { type: 'text/plain;charset=utf-8' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
  ```

### 2. Editor Toolbar Integration (`PromptEditor.tsx`)
- Adds a button inside `.toolbar-tabs` next to `Save`:
  ```tsx
  <button
    className="tab-btn"
    onClick={handleExportTxt}
    disabled={!promptText.trim()}
    title="Export current prompt or wildcard as .txt file"
    style={{ color: 'var(--accent-primary, #6366f1)', fontWeight: 600 }}
  >
    <Download size={16} /> Export .txt
  </button>
  ```
- Triggering `handleExportTxt`:
  - Determines filename: `activeDocument ? (activeDocument.name.endsWith('.txt') ? activeDocument.name : `${activeDocument.name}.txt`) : 'prompt_export.txt'`.
  - Calls `exportAsTxtFile(filename, promptText)`.
  - Shows toast: `Exported ${filename}!`.

### 3. Sidebar Integration (`Sidebar.tsx`)
- Adds a small `<Download size={14} />` action button on hover for each wildcard and prompt item in `Sidebar.tsx`.
- Clicking the download icon triggers `exportAsTxtFile` for that specific item's content without needing to switch focus if desired.

---

## Verification Plan
1. **Unit Tests**:
   - Test filename sanitization and extension handling in `fileExporter.test.ts`.
2. **Manual Verification**:
   - Edit a prompt in `PromptEditor` and click `Export .txt`. Verify `.txt` file downloads with correct text content.
   - Edit a wildcard in `PromptEditor` and click `Export .txt`. Verify `.txt` file downloads with correct name and wildcard entries.
   - Click quick export button on sidebar tree items.
