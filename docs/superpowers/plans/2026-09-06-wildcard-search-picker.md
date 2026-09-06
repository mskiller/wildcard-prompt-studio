# Searchable Wildcard Picker Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Provide an instant substring-searchable popover picker for selecting wildcards across the Visual AST Canvas node, right Inspector drawer, and top Matrix toolbar when thousands of wildcards are loaded.

**Architecture:** Create a reusable `WildcardSearchPicker` React component with custom popover, live substring filtering capped at 80 items for 60fps rendering, keyboard navigation, and event-isolation. Integrate it into `VisualASTCanvas.tsx`, `CanvasWildcardNode.tsx`, and `WildcardMatrixPanel.tsx`.

**Tech Stack:** React 18, TypeScript, Lucide React icons, CSS variables.

---

### Task 1: Create `WildcardSearchPicker` Component and Styles

**Files:**
- Create: `frontend/src/components/editor/WildcardSearchPicker.tsx`
- Create: `frontend/src/components/editor/WildcardSearchPicker.css`

- [ ] **Step 1: Write `WildcardSearchPicker.tsx`**

```tsx
import React, { useState, useRef, useEffect, useMemo, useId } from 'react';
import { Search, ChevronDown, X, Sparkles, Plus } from 'lucide-react';
import './WildcardSearchPicker.css';

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

const MAX_DISPLAY_ITEMS = 80;

export const WildcardSearchPicker: React.FC<WildcardSearchPickerProps> = ({
  value = '',
  availableWildcards = [],
  placeholder,
  onSelect,
  variant = 'inspector',
  allowCustom = true,
  readOnly = false,
  className = ''
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [query, setQuery] = useState('');
  const [highlightIndex, setHighlightIndex] = useState(0);

  const containerRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const listRef = useRef<HTMLDivElement>(null);

  // Close when clicking outside
  useEffect(() => {
    if (!isOpen) return;

    const handleClickOutside = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [isOpen]);

  // Focus search input when popover opens
  useEffect(() => {
    if (isOpen) {
      setQuery('');
      setHighlightIndex(0);
      setTimeout(() => {
        inputRef.current?.focus();
      }, 30);
    }
  }, [isOpen]);

  // Filter wildcards by substring (case-insensitive)
  const filtered = useMemo(() => {
    const trimmed = query.trim().toLowerCase();
    if (!trimmed) {
      return availableWildcards;
    }
    return availableWildcards.filter(w => w.toLowerCase().includes(trimmed));
  }, [query, availableWildcards]);

  const displayedItems = useMemo(() => {
    return filtered.slice(0, MAX_DISPLAY_ITEMS);
  }, [filtered]);

  const hasExactMatch = useMemo(() => {
    const trimmed = query.trim().toLowerCase();
    if (!trimmed) return true;
    return availableWildcards.some(w => w.toLowerCase() === trimmed);
  }, [query, availableWildcards]);

  // Keep highlighted index in bounds
  useEffect(() => {
    setHighlightIndex(0);
  }, [query]);

  // Scroll active item into view
  useEffect(() => {
    if (isOpen && listRef.current) {
      const activeEl = listRef.current.querySelector('.wildcard-item.is-highlighted') as HTMLElement;
      if (activeEl) {
        activeEl.scrollIntoView({ block: 'nearest' });
      }
    }
  }, [highlightIndex, isOpen]);

  const handleSelect = (item: string) => {
    onSelect(item);
    setIsOpen(false);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Escape') {
      e.stopPropagation();
      setIsOpen(false);
      return;
    }

    const totalCount = displayedItems.length + (allowCustom && !hasExactMatch && query.trim() ? 1 : 0);

    if (e.key === 'ArrowDown') {
      e.preventDefault();
      e.stopPropagation();
      setHighlightIndex(idx => (idx + 1) % Math.max(1, totalCount));
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      e.stopPropagation();
      setHighlightIndex(idx => (idx - 1 + totalCount) % Math.max(1, totalCount));
    } else if (e.key === 'Enter') {
      e.preventDefault();
      e.stopPropagation();
      if (displayedItems.length > 0 && highlightIndex < displayedItems.length) {
        handleSelect(displayedItems[highlightIndex]);
      } else if (allowCustom && query.trim()) {
        handleSelect(query.trim());
      }
    }
  };

  const displayLabel = value
    ? (variant === 'canvas-node' ? `__${value}__` : value)
    : (placeholder || (variant === 'toolbar' ? `+ Pick existing (${availableWildcards.length})...` : '-- Choose Wildcard --'));

  return (
    <div
      ref={containerRef}
      className={`wildcard-search-picker wildcard-search-picker-${variant} ${isOpen ? 'is-open' : ''} ${className}`}
      onMouseDown={e => e.stopPropagation()}
    >
      <button
        type="button"
        className="wildcard-picker-trigger"
        onClick={(e) => {
          e.stopPropagation();
          if (!readOnly) setIsOpen(!isOpen);
        }}
        disabled={readOnly}
        title={value ? `Wildcard: ${value}` : 'Click to search wildcards'}
        aria-expanded={isOpen}
      >
        <span className="trigger-icon">
          {variant === 'toolbar' ? <Plus size={13} /> : <Sparkles size={12} />}
        </span>
        <span className="trigger-text" title={value || displayLabel}>
          {displayLabel}
        </span>
        <ChevronDown size={13} className={`trigger-chevron ${isOpen ? 'rotate-180' : ''}`} />
      </button>

      {isOpen && (
        <div
          className="wildcard-picker-popover"
          onMouseDown={e => e.stopPropagation()}
          onKeyDown={handleKeyDown}
        >
          <div className="wildcard-picker-search-bar">
            <Search size={13} className="search-icon" />
            <input
              ref={inputRef}
              type="text"
              className="wildcard-picker-input"
              value={query}
              onChange={e => setQuery(e.target.value)}
              placeholder="Search wildcards..."
              aria-label="Filter wildcards"
            />
            {query && (
              <button
                type="button"
                className="clear-query-btn"
                onClick={() => setQuery('')}
                title="Clear search"
              >
                <X size={12} />
              </button>
            )}
          </div>

          <div className="wildcard-picker-list" ref={listRef} role="listbox">
            {displayedItems.length === 0 && (!allowCustom || !query.trim()) ? (
              <div className="wildcard-picker-empty">
                No wildcards match &ldquo;{query}&rdquo;
              </div>
            ) : (
              <>
                {displayedItems.map((item, idx) => {
                  const isSelected = item === value;
                  const isHighlighted = idx === highlightIndex;
                  return (
                    <div
                      key={item}
                      role="option"
                      aria-selected={isSelected}
                      className={`wildcard-item ${isSelected ? 'is-selected' : ''} ${isHighlighted ? 'is-highlighted' : ''}`}
                      onClick={() => handleSelect(item)}
                      onMouseEnter={() => setHighlightIndex(idx)}
                      title={item}
                    >
                      <span className="wildcard-item-prefix">__</span>
                      <span className="wildcard-item-name">{item}</span>
                      <span className="wildcard-item-suffix">__</span>
                      {isSelected && <span className="selected-check">✓</span>}
                    </div>
                  );
                })}

                {allowCustom && query.trim() && !hasExactMatch && (
                  <div
                    role="option"
                    className={`wildcard-item custom-item ${highlightIndex === displayedItems.length ? 'is-highlighted' : ''}`}
                    onClick={() => handleSelect(query.trim())}
                    onMouseEnter={() => setHighlightIndex(displayedItems.length)}
                    title={`Use custom: ${query.trim()}`}
                  >
                    <Plus size={12} className="custom-icon" />
                    <span className="custom-label">Use custom:</span>
                    <span className="wildcard-item-name">__{query.trim()}__</span>
                  </div>
                )}
              </>
            )}
          </div>

          <div className="wildcard-picker-footer">
            <span className="footer-count">
              {filtered.length > MAX_DISPLAY_ITEMS
                ? `Showing ${MAX_DISPLAY_ITEMS} of ${filtered.length} matches`
                : `${filtered.length} wildcard${filtered.length === 1 ? '' : 's'}`}
            </span>
            <span className="footer-hint">↑↓ to navigate, ↵ to pick</span>
          </div>
        </div>
      )}
    </div>
  );
};
```

- [ ] **Step 2: Write `WildcardSearchPicker.css`**

```css
.wildcard-search-picker {
  position: relative;
  display: inline-flex;
  width: 100%;
}

.wildcard-picker-trigger {
  width: 100%;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 6px;
  color: #e2e8f0;
  font-size: 11px;
  padding: 5px 8px;
  cursor: pointer;
  transition: all 0.15s ease;
  user-select: none;
  text-align: left;
}

.wildcard-picker-trigger:hover:not(:disabled) {
  background: rgba(255, 255, 255, 0.08);
  border-color: rgba(192, 132, 252, 0.4);
}

.wildcard-search-picker.is-open .wildcard-picker-trigger {
  border-color: #c084fc;
  box-shadow: 0 0 0 2px rgba(192, 132, 252, 0.2);
}

.trigger-icon {
  display: flex;
  align-items: center;
  color: #c084fc;
  flex-shrink: 0;
}

.trigger-text {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
}

.trigger-chevron {
  color: #94a3b8;
  flex-shrink: 0;
  transition: transform 0.15s ease;
}

.trigger-chevron.rotate-180 {
  transform: rotate(180deg);
}

/* Popover dropdown */
.wildcard-picker-popover {
  position: absolute;
  top: calc(100% + 4px);
  left: 0;
  width: 100%;
  min-width: 260px;
  max-width: 380px;
  background: #111420;
  border: 1px solid rgba(192, 132, 252, 0.35);
  border-radius: 8px;
  box-shadow: 0 12px 36px rgba(0, 0, 0, 0.65), 0 0 0 1px rgba(255, 255, 255, 0.05);
  z-index: 1000;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

/* Search input container */
.wildcard-picker-search-bar {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 7px 10px;
  background: rgba(255, 255, 255, 0.03);
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}

.wildcard-picker-search-bar .search-icon {
  color: #94a3b8;
  flex-shrink: 0;
}

.wildcard-picker-input {
  flex: 1;
  background: transparent;
  border: none;
  color: #f8fafc;
  font-size: 11px;
  outline: none;
}

.wildcard-picker-input::placeholder {
  color: #64748b;
}

.clear-query-btn {
  background: transparent;
  border: none;
  color: #94a3b8;
  cursor: pointer;
  display: flex;
  align-items: center;
  padding: 2px;
  border-radius: 4px;
}

.clear-query-btn:hover {
  color: #f8fafc;
  background: rgba(255, 255, 255, 0.1);
}

/* Scrollable items list */
.wildcard-picker-list {
  max-height: 220px;
  overflow-y: auto;
  padding: 4px;
  display: flex;
  flex-direction: column;
  gap: 1px;
}

.wildcard-picker-list::-webkit-scrollbar {
  width: 6px;
}

.wildcard-picker-list::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.15);
  border-radius: 3px;
}

.wildcard-item {
  display: flex;
  align-items: center;
  padding: 5px 8px;
  border-radius: 5px;
  cursor: pointer;
  font-size: 11px;
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  color: #cbd5e1;
  user-select: none;
  transition: background 0.1s ease;
}

.wildcard-item:hover,
.wildcard-item.is-highlighted {
  background: rgba(192, 132, 252, 0.18);
  color: #f3e8ff;
}

.wildcard-item.is-selected {
  background: rgba(192, 132, 252, 0.28);
  color: #ffffff;
  font-weight: 500;
}

.wildcard-item-prefix,
.wildcard-item-suffix {
  color: #a855f7;
  font-weight: bold;
}

.wildcard-item-name {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.selected-check {
  color: #c084fc;
  font-size: 11px;
  margin-left: 6px;
}

.custom-item {
  border-top: 1px dashed rgba(255, 255, 255, 0.1);
  margin-top: 4px;
  padding-top: 6px;
  color: #38bdf8;
}

.custom-icon {
  margin-right: 4px;
  color: #38bdf8;
}

.custom-label {
  font-size: 10px;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-right: 6px;
  color: #94a3b8;
}

.wildcard-picker-empty {
  padding: 18px 12px;
  text-align: center;
  color: #94a3b8;
  font-size: 11px;
}

/* Footer count */
.wildcard-picker-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 5px 10px;
  background: rgba(255, 255, 255, 0.02);
  border-top: 1px solid rgba(255, 255, 255, 0.06);
  font-size: 10px;
  color: #64748b;
}

.footer-hint {
  font-size: 9px;
  color: #475569;
}

/* Variant overrides */
.wildcard-search-picker-toolbar {
  width: auto;
}

.wildcard-search-picker-toolbar .wildcard-picker-trigger {
  padding: 4px 10px;
  background: rgba(192, 132, 252, 0.12);
  border-color: rgba(192, 132, 252, 0.3);
  color: #e9d5ff;
  font-family: inherit;
  font-weight: 500;
  border-radius: 6px;
}

.wildcard-search-picker-toolbar .wildcard-picker-trigger:hover {
  background: rgba(192, 132, 252, 0.2);
  border-color: rgba(192, 132, 252, 0.5);
}

.wildcard-search-picker-canvas-node .wildcard-picker-trigger {
  background: rgba(192, 132, 252, 0.08);
  border: 1px solid rgba(192, 132, 252, 0.3);
  padding: 4px 8px;
}
```

- [ ] **Step 3: Run build to verify TypeScript compilation**
Run: `npm run build` in `frontend`
Expected: Passes without errors.

- [ ] **Step 4: Commit**
```bash
git add frontend/src/components/editor/WildcardSearchPicker.tsx frontend/src/components/editor/WildcardSearchPicker.css
git commit -m "feat(editor): add reusable WildcardSearchPicker component"
```

---

### Task 2: Integrate `WildcardSearchPicker` into Visual AST Canvas Node

**Files:**
- Modify: `frontend/src/components/editor/VisualASTCanvas.tsx`
- Modify: `frontend/src/components/editor/VisualASTCanvas.css`

- [ ] **Step 1: Update `VisualASTCanvas.tsx`**
Import `WildcardSearchPicker` and replace lines 388-419 (the `<select className="canvas-node-wildcard-select">`) with:
```tsx
<div className="canvas-wildcard-preview-box" onMouseDown={e => e.stopPropagation()}>
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
</div>
```

- [ ] **Step 2: Update `VisualASTCanvas.css`**
Ensure `.canvas-node-wildcard` has appropriate overflow visibility so the popover is not clipped, and add `.canvas-node:has(.wildcard-search-picker.is-open)` elevation:
```css
.canvas-node:has(.wildcard-search-picker.is-open) {
  z-index: 100;
}
```

- [ ] **Step 3: Run build to verify TypeScript compilation**
Run: `npm run build` in `frontend`
Expected: Passes without errors.

- [ ] **Step 4: Commit**
```bash
git add frontend/src/components/editor/VisualASTCanvas.tsx frontend/src/components/editor/VisualASTCanvas.css
git commit -m "feat(canvas): integrate WildcardSearchPicker into AST canvas nodes"
```

---

### Task 3: Integrate `WildcardSearchPicker` into Inspector Drawer

**Files:**
- Modify: `frontend/src/components/editor/nodes/CanvasWildcardNode.tsx`

- [ ] **Step 1: Update `CanvasWildcardNode.tsx`**
Import `WildcardSearchPicker` and replace the `<select className="wildcard-select">` block (lines 45-66) with:
```tsx
{hasAvailable && (
  <div className="wildcard-select-container">
    <WildcardSearchPicker
      variant="inspector"
      value={isAvailableMatch ? name : ''}
      availableWildcards={availableWildcards}
      placeholder="-- Search & choose wildcard --"
      onSelect={(val) => {
        if (val) onChange(val);
      }}
      readOnly={readOnly}
    />
  </div>
)}
```

- [ ] **Step 2: Run build to verify TypeScript compilation**
Run: `npm run build` in `frontend`
Expected: Passes without errors.

- [ ] **Step 3: Commit**
```bash
git add frontend/src/components/editor/nodes/CanvasWildcardNode.tsx
git commit -m "feat(inspector): integrate WildcardSearchPicker into node inspector drawer"
```

---

### Task 4: Integrate `WildcardSearchPicker` into Matrix Toolbar

**Files:**
- Modify: `frontend/src/components/editor/WildcardMatrixPanel.tsx`

- [ ] **Step 1: Update `WildcardMatrixPanel.tsx`**
Import `WildcardSearchPicker` and replace the toolbar quick picker `<select className="toolbar-wildcard-quick-picker">` block (lines 1532-1552) with:
```tsx
{availableWildcards.length > 0 && (
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
)}
```

- [ ] **Step 2: Run build to verify TypeScript compilation**
Run: `npm run build` in `frontend`
Expected: Passes without errors.

- [ ] **Step 3: Commit**
```bash
git add frontend/src/components/editor/WildcardMatrixPanel.tsx
git commit -m "feat(matrix): integrate WildcardSearchPicker into matrix toolbar"
```

---

### Task 5: End-to-End Verification

- [ ] **Step 1: Run production build**
Run: `npm run build` in `frontend`
Expected: `dist` compiled successfully with 0 errors.

- [ ] **Step 2: Verify git status and commits**
Run: `git log -n 5 --oneline` to confirm clean commits.
