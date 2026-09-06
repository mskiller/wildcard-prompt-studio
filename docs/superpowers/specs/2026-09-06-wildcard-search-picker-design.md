# Design Specification: Searchable Wildcard Picker

**Date**: 2026-09-06  
**Status**: Approved by User  
**Target Subsystems**: Visual AST Canvas (`VisualASTCanvas.tsx`), Inspector Panel (`CanvasWildcardNode.tsx`), Matrix Toolbar (`WildcardMatrixPanel.tsx`)

---

## 1. Problem Statement & Motivation

When users import large collections of wildcards (e.g., 3,000+ wildcard files), selecting a wildcard via native HTML `<select>` elements becomes unusable:
1. Native `<select>` popups on the canvas node stretch across the entire viewport, obscuring the studio.
2. Users cannot search or filter by typing substrings (native `<select>` only jumps by prefix character).
3. The right inspector drawer and the "+ Pick existing" toolbar button suffer from the same sluggish, unsearchable 3,000+ item list.

## 2. Goals & Success Criteria

- **Sub-string search**: Typing partial words (e.g. `robot`, `female`, `scene`) immediately filters matching wildcards.
- **Unified UX across 3 touchpoints**:
  1. Wildcard node directly on the Visual AST Canvas.
  2. Right-side Inspector drawer for wildcard nodes.
  3. Top toolbar `+ Pick existing` button.
- **High Performance**: Smooth 60fps typing experience without DOM lags when filtering 3,000+ items (capped DOM rendering of top 80 results with match count feedback).
- **Keyboard & Touch/Mouse Friendly**: Up/Down arrow keys, Enter to pick, Escape to close, click-outside dismissal, auto-focusing search bar.
- **Canvas-Safe Interactions**: Keystrokes and clicks inside the picker do not bubble to canvas pan/zoom or node dragging.
- **Backward Compatible**: Supports custom wildcard paths that may not be in the preloaded list.

---

## 3. Architecture & Components

### 3.1 New Component: `WildcardSearchPicker`
**File**: `frontend/src/components/editor/WildcardSearchPicker.tsx`  
**Styles**: `frontend/src/components/editor/WildcardSearchPicker.css`

#### Props Interface:
```typescript
export interface WildcardSearchPickerProps {
  value?: string;
  availableWildcards: string[];
  placeholder?: string;
  onSelect: (wildcardName: string) => void;
  variant?: 'toolbar' | 'canvas-node' | 'inspector';
  allowCustom?: boolean;
  readOnly?: boolean;
  className?: string;
}
```

#### Component Internals:
- **`isOpen`**: Boolean state toggling dropdown popover.
- **`query`**: Input state for the filter text.
- **`filteredItems`**: Memoized case-insensitive search results filtering `availableWildcards`.
  - Filter logic: `w.toLowerCase().includes(q.toLowerCase())`
  - Render limit: First 80 items displayed in scrollable list with total match count.
- **`highlightIndex`**: Currently active item for arrow key navigation.
- **`popoverRef` & `inputRef`**: References for click-outside detection and autofocus.
- **Custom input support**: If `allowCustom` is true and `query` doesn't match an exact item, renders a *"Use custom: '{query}'"* option.

---

## 4. Integration Points

### 4.1 Visual AST Canvas (`VisualASTCanvas.tsx`)
- Replace the `<select className="canvas-node-wildcard-select">` inside wildcard node rendering with:
  ```tsx
  <WildcardSearchPicker
    variant="canvas-node"
    value={node.value}
    availableWildcards={availableWildcards}
    onSelect={(val) => {
      if (onUpdateNode) {
        onUpdateNode(node.id, { value: val, title: val });
      }
    }}
  />
  ```
- Elevate parent node `z-index` when open so the dropdown appears cleanly above neighboring nodes and connection wires.

### 4.2 Inspector Drawer (`CanvasWildcardNode.tsx`)
- Replace `<select className="wildcard-select">` with:
  ```tsx
  <WildcardSearchPicker
    variant="inspector"
    value={isAvailableMatch ? name : ''}
    availableWildcards={availableWildcards}
    placeholder="-- Search & choose wildcard --"
    onSelect={handleSelectChange}
    readOnly={readOnly}
  />
  ```
- Retain the existing manual text input below for fine-grained editing.

### 4.3 Matrix Toolbar (`WildcardMatrixPanel.tsx`)
- Replace `<select className="toolbar-wildcard-quick-picker">` with:
  ```tsx
  <WildcardSearchPicker
    variant="toolbar"
    value=""
    placeholder={`+ Pick existing (${availableWildcards.length})...`}
    availableWildcards={availableWildcards}
    onSelect={(picked) => {
      if (picked) {
        addNode('wildcard', picked);
      }
    }}
  />
  ```
- Reset selected value after picking so the toolbar button remains as a "+ Pick existing" action trigger.

---

## 5. UI/UX Specifications

- **Search Bar**:
  - Placeholder: `Filter wildcards (e.g. krea, robot)...`
  - Auto-focused when popover opens.
  - Clear button `×` to reset search.
- **Dropdown List**:
  - Max height: 260px with dark theme scrollbar.
  - Highlighted match substring for fast scanning.
  - Hover and arrow key selection highlight (`bg: rgba(129, 140, 248, 0.2)`).
- **Footer Info**:
  - Displays: `Showing 80 of {count} matches` if exceeds 80, or `{count} matches` otherwise.
- **Event Isolation**:
  - `e.stopPropagation()` on `onMouseDown` and `onKeyDown` to isolate from canvas pan/drag listeners.

---

## 6. Testing & Verification

1. **Unit/Integration verification**:
   - Verify frontend compiles without TypeScript errors (`npm run build` or Vite build check).
2. **Manual UX verification**:
   - Open Visual AST & Matrix Studio with 3,115+ wildcards loaded.
   - Test toolbar `+ Pick existing`: type search query, verify quick filter, select item, verify node added.
   - Test Canvas node: click picker on node, verify popover opens without taking over the whole screen, type substring, verify selection updates the node.
   - Test Inspector panel: select node, filter wildcards in inspector, verify canvas node synchronizes.
