# Krea 2 Studio Panel - Remove Prompt Weights Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a "Remove Weights" 1-click action button in Krea 2 Studio Panel to strip prompt weights like `(prompt:1.2)`, `(tag:0.8)`, and `(tag)` from user prompts.

**Architecture:** Create a pure, reusable utility function `cleanPromptWeights` in `frontend/src/utils/promptCleaner.ts` with unit tests in Vitest, then connect it to a new button in `frontend/src/components/editor/Krea2StudioPanel.tsx`.

**Tech Stack:** React, TypeScript, Vitest, Lucide React (`Scale` icon).

---

### Task 1: Create Prompt Weight Cleaner Utility & Tests

**Files:**
- Create: `frontend/src/utils/promptCleaner.ts`
- Create: `frontend/src/utils/promptCleaner.test.ts`

- [ ] **Step 1: Write failing tests for `cleanPromptWeights`**

Create `frontend/src/utils/promptCleaner.test.ts`:
```typescript
import { describe, it, expect } from 'vitest';
import { cleanPromptWeights } from './promptCleaner';

describe('cleanPromptWeights', () => {
  it('removes weighted tags with float weights', () => {
    expect(cleanPromptWeights('(prompt:1.2)')).toBe('prompt');
    expect(cleanPromptWeights('(a photo of a cat:0.85)')).toBe('a photo of a cat');
  });

  it('removes negative weights', () => {
    expect(cleanPromptWeights('(blurry:-0.5)')).toBe('blurry');
  });

  it('removes plain parentheses around terms', () => {
    expect(cleanPromptWeights('(cyberpunk city)')).toBe('cyberpunk city');
    expect(cleanPromptWeights('((masterpiece:1.2), high quality)')).toBe('masterpiece, high quality');
  });

  it('handles multiple weighted terms in prompt', () => {
    const input = '(red car:1.1), (blue sky:0.9), masterpiece';
    expect(cleanPromptWeights(input)).toBe('red car, blue sky, masterpiece');
  });

  it('returns empty string for empty input', () => {
    expect(cleanPromptWeights('')).toBe('');
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd frontend && npm test src/utils/promptCleaner.test.ts`
Expected: FAIL (module `promptCleaner` not found)

- [ ] **Step 3: Write implementation of `cleanPromptWeights`**

Create `frontend/src/utils/promptCleaner.ts`:
```typescript
/**
 * Utility to strip SD-style weight syntax e.g. (tag:1.2) -> tag and (tag) -> tag
 */
export function cleanPromptWeights(prompt: string): string {
  if (!prompt) return '';

  let cleaned = prompt;

  // 1. Remove weighted syntax: (tag:1.2) -> tag or (tag: 0.8) -> tag
  let previous = '';
  while (previous !== cleaned) {
    previous = cleaned;
    cleaned = cleaned.replace(/\(\s*([^():]+?)\s*:\s*-?\d+(?:\.\d+)?\s*\)/g, '$1');
  }

  // 2. Remove plain outer parentheses: ((tag)) -> tag, (tag) -> tag
  previous = '';
  while (previous !== cleaned) {
    previous = cleaned;
    cleaned = cleaned.replace(/\(\s*([^()]+?)\s*\)/g, '$1');
  }

  // 3. Remove any stray colon weight suffixes like :1.2 if outside parentheses
  cleaned = cleaned.replace(/:\s*-?\d+(?:\.\d+)?\b/g, '');

  // 4. Clean up multiple spaces and empty/dangling commas
  cleaned = cleaned
    .replace(/,\s*,/g, ',')
    .replace(/^\s*,\s*|\s*,\s*$/g, '')
    .replace(/\s{2,}/g, ' ')
    .trim();

  return cleaned;
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd frontend && npm test src/utils/promptCleaner.test.ts`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add frontend/src/utils/promptCleaner.ts frontend/src/utils/promptCleaner.test.ts
git commit -m "feat: add cleanPromptWeights utility and tests"
```

---

### Task 2: Add Remove Weights Button to Krea 2 Studio Panel

**Files:**
- Modify: `frontend/src/components/editor/Krea2StudioPanel.tsx`

- [ ] **Step 1: Update imports and add `handleRemoveWeights` handler**

In `frontend/src/components/editor/Krea2StudioPanel.tsx`:
Add import:
```typescript
import { Scale } from 'lucide-react';
import { cleanPromptWeights } from '../../utils/promptCleaner';
```

Add handler:
```typescript
  // 1-Click Action: Remove Prompt Weights
  const handleRemoveWeights = () => {
    if (!originalPrompt.trim()) return;
    const cleaned = cleanPromptWeights(originalPrompt);
    setOptimizedPrompt(cleaned);
    showNotification('Prompt weights removed!');
  };
```

- [ ] **Step 2: Add Button in `.krea2-actions` grid**

Add button right after `🧹 Clean Buzzwords`:
```tsx
        <button
          className="action-btn"
          onClick={handleRemoveWeights}
          disabled={isLoading || !originalPrompt.trim()}
        >
          <Scale size={16} />
          ⚖️ Remove Weights
        </button>
```

- [ ] **Step 3: Verify build / tests pass**

Run: `cd frontend && npm test`
Expected: All frontend tests pass.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/components/editor/Krea2StudioPanel.tsx
git commit -m "feat: add Remove Weights button to Krea 2 Studio panel"
```
