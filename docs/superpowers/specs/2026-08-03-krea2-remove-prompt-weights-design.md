# Krea 2 Studio Panel - Remove Prompt Weights Design

## Overview
Krea 2 models do not support SD-style prompt weight syntax such as `(prompt:1.2)`, `(tag:0.8)`, or nested weight parentheses `((tag:1.1))`.
This feature introduces a dedicated **Remove Weights** 1-click action button inside the **Krea 2 Studio Panel** that strips all prompt weights (`( )` and `:X.XX`) instantly, loading the cleaned prompt into the Side-by-Side Diff / Preview Viewer.

---

## User Review & Approval
- User approved the design on 2026-08-03.
- Approach: Reusable frontend prompt cleaning utility (`src/utils/promptCleaner.ts`) integrated into `Krea2StudioPanel.tsx`.

---

## Architecture & Component Design

### 1. Prompt Cleaning Utility (`src/utils/promptCleaner.ts`)
A dedicated function `cleanPromptWeights(prompt: str): string`:
- **Iterative Weighted Group Removal**:
  `\(\s*([^():]+?)\s*:\s*-?\d+(?:\.\d+)?\s*\)` -> `$1`
- **Iterative Outer Parentheses Removal**:
  `\(\s*([^()]+?)\s*\)` -> `$1`
- **Stray Weight Removal**:
  `:\d+(?:\.\d+)?\b` -> ``
- **Whitespace & Formatting Cleanup**:
  Cleans duplicate spaces, leading/trailing whitespace, and empty commas.

### 2. Krea 2 Studio Panel UI (`Krea2StudioPanel.tsx`)
- Imports `cleanPromptWeights` from `../../utils/promptCleaner`.
- Adds `handleRemoveWeights` click handler.
- Adds `Scale` icon from `lucide-react`.
- Adds a button inside `.krea2-actions`:
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
- Updates `optimizedPrompt` and presents notification: `"Prompt weights removed!"`.

---

## Verification Plan
1. **Unit Tests**:
   - Create `src/utils/promptCleaner.test.ts` to test edge cases:
     - `(prompt:1.2)` -> `prompt`
     - `(tag: 0.85)` -> `tag`
     - `((masterpiece:1.2), high quality)` -> `masterpiece, high quality`
     - `(red car:1.1), (blue sky)` -> `red car, blue sky`
     - Clean text without weights remains unchanged.
2. **Manual Verification**:
   - Load Krea 2 Studio Panel in browser.
   - Enter weighted prompt and verify 1-click button cleans text correctly in Diff Viewer.
