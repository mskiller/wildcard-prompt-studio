# UI & Mobile/Desktop Adaptivity Design Specification

**Date:** 2026-08-01  
**Topic:** Mobile/Desktop Auto-Detection, Touch-Native Navigation, Glassmorphism UI Polish & Responsive Optimization  
**Status:** Approved by User  

---

## 1. Overview & Objectives

This update upgrades **Wildcard Prompt Studio** to be fully adaptive across both **Desktop PCs** and **Mobile / Tablet devices**. The update focuses strictly on user interface (UI), touch/feel user experience (UX), and modern cyber-glass aesthetics.

### Key Goals:
1. **Device Detection**: Detect mobile vs. desktop viewports and pointer capabilities dynamically.
2. **Responsive Layout Architecture**: Preserves full desktop multi-panel IDE while introducing a touch-native **Bottom Navigation Dock** and **Slide-Up Bottom Sheets** for mobile screens.
3. **Cyber-Glass Design System**: Upgrades styling with dynamic backdrop filters, obsidian dark glass themes, glowing neon accents, and clean modern typography.
4. **Touch-Native UX & Micro-Interactions**: Active press scale feedback (`scale(0.96)`), touch drag-to-dismiss handles for sheets, and sticky mobile prompt insertion toolbars.
5. **Mobile Canvas & Media Stream Optimization**: Responsive grid systems for Gallery, ComfyUI Live Stream, ANIMA Studio, and Inspector panels.

---

## 2. Device Detection Engine (`useDeviceDetect`)

### Implementation Details:
- **File:** `frontend/src/store/useDeviceDetect.ts` (and exported via `useAppStore.ts`)
- **State Properties**:
  - `isMobile`: `boolean` (`width < 768px || (isTouch && width < 1024px)`)
  - `isTablet`: `boolean` (`width >= 768px && width <= 1024px`)
  - `isDesktop`: `boolean` (`width > 1024px`)
  - `isTouch`: `boolean` (`window.matchMedia('(pointer: coarse)').matches || navigator.maxTouchPoints > 0`)
  - `orientation`: `'portrait' | 'landscape'`
- **Listeners**: Attaches `window.matchMedia` and `ResizeObserver` listeners for instant, zero-reload reactivity.

---

## 3. Responsive Layout & Touch-Native Navigation

### 3.1 Desktop Layout Architecture
- Preserves the existing high-density floating glass IDE structure.
- **Top Bar**: Fixed title bar with window controls and app title.
- **Activity Bar**: Vertical left icon bar (24px icons with active glow highlights).
- **Sidebar & Context Panels**: Side-by-side floating glass panels.
- **Status Bar**: Bottom bar displaying app status and current view telemetry.

### 3.2 Mobile Layout Architecture
- **Top Bar**: Compact mobile header with current view title, active document indicator, and quick settings trigger.
- **Main Canvas**: Full-width scrollable viewport (`calc(100vh - 104px)`).
- **Bottom Navigation Dock (`MobileBottomNav.tsx`)**:
  - Replaces the left activity bar on mobile (`isMobile === true`).
  - Fixed at the bottom (`height: 56px + env(safe-area-inset-bottom)`).
  - Contains primary tools: **Prompts**, **ANIMA Studio**, **ComfyUI Stream**, **Gallery**, plus a **More Tools** trigger.
- **Slide-Up Bottom Sheet (`BottomSheet.tsx`)**:
  - Sidebars, document trees, tags, and inspectors open inside a slide-up drawer sheet.
  - Includes a visual drag handle at top (`width: 36px`, `height: 4px`).
  - Touch swipe-down to dismiss gesture (`touchstart`, `touchmove`, `touchend`).
  - Dark glass backdrop overlay (`backdrop-filter: blur(4px)`).

---

## 4. Design System & Glassmorphic Aesthetics

### 4.1 CSS Design Tokens (`frontend/src/index.css`)
- **Color Palette**:
  - Obsidian Background: `#070a12`
  - Glass Surface Background: `rgba(15, 23, 42, 0.75)`
  - Glass Panel Border: `1px solid rgba(255, 255, 255, 0.08)`
  - Accent Colors: Cyan (`#06b6d4`), Neon Purple (`#a855f7`), Hot Pink (`#ec4899`), Amber (`#f59e0b`).
- **Glass Effects**:
  - `backdrop-filter: blur(16px) saturate(180%)`
  - `box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.45)`
- **Typography**:
  - Display & UI: `Inter`, system UI font fallback
  - Code & Prompts: `JetBrains Mono`, `Fira Code`, monospace

### 4.2 Micro-Interactions & Touch Feedback
- Active click/tap shrink physics: `button:active, .clickable:active { transform: scale(0.96); transition: transform 0.1s ease; }`
- Minimum touch hit targets: `min-height: 44px`, `min-width: 44px` on touch screens (`@media (pointer: coarse)`).
- Smooth view transition animations (`opacity` fade + `translateY` slide).

---

## 5. Mobile-Optimized Prompt Editor & Media Stream Viewers

### 5.1 Mobile Prompt Editor Toolbar
- Sticky floating syntax bar pinned above virtual keyboard on mobile.
- One-tap buttons for inserting `{ choice1 | choice2 }`, `__wildcards__`, `(weight:1.2)`, and tags.
- Responsive monospace editor with auto-adjusting font size (`15px`) and line spacing.

### 5.2 Responsive Media Viewers
- **Gallery (`GalleryView.tsx`)**:
  - Responsive masonry layout (1-column on mobile, 2-column on tablet, 4-column on desktop).
  - Modal viewer with pinch-to-zoom and quick prompt copy action.
- **ComfyUI Stream (`ComfyUILiveStream.tsx`)**:
  - Stacked layout on mobile with live canvas on top and collapsible node parameters in a bottom sheet.

---

## 6. Verification & Testing Plan

1. **Device Detection Unit & Integration Verification**: Verify `useDeviceDetect` correctly reports `isMobile`, `isTouch`, and breakpoints on window resize and touch emulation.
2. **Responsive Layout Verification**: Check Chrome DevTools Mobile Emulation (iPhone 14, Pixel 7, iPad Air, Desktop 1080p).
3. **Touch Gesture Verification**: Test drag-to-dismiss on `BottomSheet.tsx` and tap hitboxes on mobile.
4. **Build & Lint Verification**: Run `npm run build` in `frontend` to verify TypeScript compilation with zero errors.
