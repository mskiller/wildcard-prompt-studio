# Settings Page Overhaul & i18n/Theme Architecture Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Overhaul the Settings page into a centralized control center supporting Light/Dark theme switching, English & French i18n internationalization, API connection management (ComfyUI, Ollama, KoboldCpp, Gemini), Prompt Improvement defaults (Krea 2 variants & rules), and Model Profile configuration.

**Architecture:** An extended Zustand state store ([useAppStore.ts](file:///j:/wildcard-prompt-studio/frontend/src/store/useAppStore.ts)) with persistent settings, a lightweight i18n translation dictionary (`i18n.ts`), dynamic CSS theme variables (`index.css`), and an enhanced tabbed UI ([SettingsView.tsx](file:///j:/wildcard-prompt-studio/frontend/src/components/settings/SettingsView.tsx)).

**Tech Stack:** React 18, TypeScript, Zustand (`persist`), Vanilla CSS tokens & dark/light variables.

---

## File Structure & Responsibilities

### Frontend Files:
- `frontend/src/store/useAppStore.ts`: Extended store holding theme (`dark`|`light`), language (`en`|`fr`), API URLs (ComfyUI, Ollama, KoboldCpp, Gemini key), and default prompt improvement settings (Krea 2 variant, auto-clean buzzwords, auto-quotes).
- `frontend/src/i18n.ts`: Translation dictionary mapping keys to English and French strings.
- `frontend/src/index.css`: Light theme variable overrides (`[data-theme="light"]`) and smooth transition tokens.
- `frontend/src/components/settings/SettingsView.tsx`: Redesigned settings view with tabs for **Appearance & Language**, **AI & Prompt Improvement**, **API Connections**, and **Model Profiles**.
- `frontend/src/components/settings/SettingsView.css`: Tabbed navigation styling for dark/light themes.

---

## Tasks

### Task 1: Translation Dictionary (`i18n.ts`) & Zustand State Extension

**Files:**
- Create: `frontend/src/i18n.ts`
- Modify: `frontend/src/store/useAppStore.ts`

- [ ] **Step 1: Create `frontend/src/i18n.ts` dictionary**

Define English (`en`) and French (`fr`) translations for all navigation tabs, settings titles, labels, buttons, and help texts.

- [ ] **Step 2: Update `frontend/src/store/useAppStore.ts`**

Add `theme` (`'dark'` | `'light'`), `language` (`'en'` | `'fr'`), `ollamaUrl`, `geminiApiKey`, `defaultKreaVariant`, `autoCleanBuzzwords`, `autoQuoteTargets`, and corresponding setter functions.

---

### Task 2: CSS Theme Token Engine (Dark / Light Mode)

**Files:**
- Modify: `frontend/src/index.css`

- [ ] **Step 1: Define `[data-theme="light"]` variables in `index.css`**

Add CSS custom properties for `--bg-color`, `--bg-card`, `--text-color`, `--text-secondary`, and `--border-color` for light mode.

---

### Task 3: Comprehensive Settings UI Suite (`SettingsView.tsx`)

**Files:**
- Modify: `frontend/src/components/settings/SettingsView.tsx`
- Modify: `frontend/src/components/settings/SettingsView.css`

- [ ] **Step 1: Rebuild `SettingsView.tsx` with 4 dedicated categories**
  - **Appearance & Language**: Light/Dark theme toggle buttons and English/French flag/language selectors.
  - **AI & Prompt Improvement**: Default Krea 2 variant selector (**Turbo**, **Medium**, **Large**), default LLM provider (**Ollama**, **KoboldCpp**, **Gemini**), and auto-clean/quote toggle rules.
  - **API Connections**: Full endpoint manager for ComfyUI, Ollama, KoboldCpp, and Gemini API keys with 1-click **Test Connection** ping handlers.
  - **Model Profiles**: Existing `ModelProfileEditor` integration.

- [ ] **Step 2: Add theme application `useEffect` to apply `data-theme` attribute to document root**

---

### Task 4: UI Navigation & End-to-End Verification

**Files:**
- Modify: `frontend/src/components/layout/Sidebar.tsx`
- Modify: `frontend/src/components/editor/Krea2StudioPanel.tsx`

- [ ] **Step 1: Update Sidebar and Krea 2 Studio panel to use `useAppStore` settings & i18n keys**
- [ ] **Step 2: Verify theme switching and French/English translation toggle in browser UI**

---
