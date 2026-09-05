# UI & Mobile/Desktop Adaptivity Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Transform Wildcard Prompt Studio into a fully adaptive experience across Desktop PCs and Mobile/Tablet devices, featuring automatic device detection, a touch-native Bottom Navigation Dock, slide-up Bottom Sheets, cyber-glass aesthetic styling, and touch micro-interactions.

**Architecture:** A reactive `useDeviceDetect` store tracks viewport dimensions and touch capabilities. On desktop, the high-density floating glass IDE layout is preserved. On mobile, `MainLayout` transforms the vertical activity bar into a floating glass `MobileBottomNav`, converts sidebar panels into `BottomSheet` slide-up drawers with swipe-to-dismiss gestures, and injects a mobile syntax toolbar into the prompt editor.

**Tech Stack:** React 18, TypeScript, Zustand, Lucide Icons, Vanilla CSS (Glassmorphism, CSS Custom Properties, Safe Area Insets, Media Queries).

---

### Task 1: Device Detection Store (`useDeviceDetect.ts`)

**Files:**
- Create: `j:/wildcard-prompt-studio/frontend/src/store/useDeviceDetect.ts`
- Modify: `j:/wildcard-prompt-studio/frontend/src/store/useAppStore.ts`

- [ ] **Step 1: Create `useDeviceDetect.ts` with viewport & pointer detection**

```typescript
import { useState, useEffect } from 'react';

export interface DeviceInfo {
  isMobile: boolean;
  isTablet: boolean;
  isDesktop: boolean;
  isTouch: boolean;
  width: number;
  height: number;
  orientation: 'portrait' | 'landscape';
}

export function useDeviceDetect(): DeviceInfo {
  const getDeviceInfo = (): DeviceInfo => {
    const width = typeof window !== 'undefined' ? window.innerWidth : 1200;
    const height = typeof window !== 'undefined' ? window.innerHeight : 800;
    const isTouch = typeof window !== 'undefined' && 
      (window.matchMedia('(pointer: coarse)').matches || navigator.maxTouchPoints > 0);
    
    const isMobile = width < 768 || (isTouch && width < 1024);
    const isTablet = width >= 768 && width <= 1024;
    const isDesktop = width > 1024 && !isTouch;

    return {
      isMobile,
      isTablet,
      isDesktop,
      isTouch,
      width,
      height,
      orientation: height > width ? 'portrait' : 'landscape',
    };
  };

  const [deviceInfo, setDeviceInfo] = useState<DeviceInfo>(getDeviceInfo());

  useEffect(() => {
    const handleResize = () => {
      setDeviceInfo(getDeviceInfo());
    };

    window.addEventListener('resize', handleResize);
    window.addEventListener('orientationchange', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
      window.removeEventListener('orientationchange', handleResize);
    };
  }, []);

  return deviceInfo;
}
```

- [ ] **Step 2: Export device detection in `useAppStore.ts`**

Update `frontend/src/store/useAppStore.ts` to include `isMobileMenuOpen` state and toggle action:

```typescript
// Add to AppState interface:
isMobileMenuOpen: boolean;
setMobileMenuOpen: (open: boolean) => void;
toggleMobileMenu: () => void;

// Add to store implementation:
isMobileMenuOpen: false,
setMobileMenuOpen: (open) => set({ isMobileMenuOpen: open }),
toggleMobileMenu: () => set((state) => ({ isMobileMenuOpen: !state.isMobileMenuOpen })),
```

- [ ] **Step 3: Verify TypeScript compilation**

Run: `cd j:/wildcard-prompt-studio/frontend && npm run build`  
Expected: PASS with 0 errors.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/store/useDeviceDetect.ts frontend/src/store/useAppStore.ts
git commit -m "feat: add useDeviceDetect hook and mobile menu state"
```

---

### Task 2: Cyber-Glass Design System & Micro-Interactions (`index.css`)

**Files:**
- Modify: `j:/wildcard-prompt-studio/frontend/src/index.css`
- Modify: `j:/wildcard-prompt-studio/frontend/src/components/layout/MainLayout.css`

- [ ] **Step 1: Enhance `index.css` with dark obsidian glass tokens and touch styles**

Update `frontend/src/index.css` to add/refine root CSS variables and touch feedback utilities:

```css
:root {
  --bg-app: #070a12;
  --bg-surface: rgba(15, 23, 42, 0.75);
  --bg-panel: rgba(18, 26, 46, 0.65);
  --bg-glass-card: rgba(255, 255, 255, 0.04);
  --glass-border: rgba(255, 255, 255, 0.08);
  --glass-border-glow: rgba(6, 182, 212, 0.3);
  --glass-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.45);
  --backdrop-blur: blur(16px) saturate(180%);

  --accent-cyan: #06b6d4;
  --accent-purple: #a855f7;
  --accent-pink: #ec4899;
  --accent-amber: #f59e0b;
}

/* Touch micro-interactions */
@media (pointer: coarse) {
  button, .clickable, .activity-item, .sidebar-tree-item {
    min-height: 44px;
    min-width: 44px;
    touch-action: manipulation;
  }
}

button:active, .activity-item:active, .touch-shrink:active {
  transform: scale(0.96);
  transition: transform 0.1s ease;
}

/* Scrollbar refinement */
::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}

::-webkit-scrollbar-track {
  background: transparent;
}

::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.15);
  border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
  background: rgba(255, 255, 255, 0.3);
}
```

- [ ] **Step 2: Update `MainLayout.css` for responsive layout containers**

Modify `frontend/src/components/layout/MainLayout.css`:

```css
.layout-container {
  display: flex;
  flex-direction: column;
  height: 100vh;
  height: 100dvh;
  width: 100vw;
  background-color: var(--bg-app);
  overflow: hidden;
}

.layout-body {
  display: flex;
  flex: 1;
  overflow: hidden;
  padding: 8px;
  gap: 8px;
  position: relative;
}

@media (max-width: 768px) {
  .layout-body {
    padding: 4px;
    padding-bottom: calc(64px + env(safe-area-inset-bottom));
  }
}
```

- [ ] **Step 3: Verify build**

Run: `cd j:/wildcard-prompt-studio/frontend && npm run build`  
Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add frontend/src/index.css frontend/src/components/layout/MainLayout.css
git commit -m "style: upgrade cyber-glass design system and mobile layout styles"
```

---

### Task 3: Touch-Native Slide-Up Bottom Sheet Component (`BottomSheet.tsx`)

**Files:**
- Create: `j:/wildcard-prompt-studio/frontend/src/components/common/BottomSheet.tsx`
- Create: `j:/wildcard-prompt-studio/frontend/src/components/common/BottomSheet.css`

- [ ] **Step 1: Create `BottomSheet.css`**

```css
.bottom-sheet-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.6);
  backdrop-filter: blur(6px);
  z-index: 999;
  display: flex;
  flex-direction: column;
  justify-content: flex-end;
  animation: fadeIn 0.2s ease-out;
}

.bottom-sheet-container {
  background: var(--bg-surface);
  border-top-left-radius: 20px;
  border-top-right-radius: 20px;
  border: 1px solid var(--glass-border);
  border-bottom: none;
  box-shadow: 0 -10px 40px rgba(0, 0, 0, 0.5);
  max-height: 85vh;
  min-height: 40vh;
  display: flex;
  flex-direction: column;
  transform: translateY(0);
  transition: transform 0.25s cubic-bezier(0.33, 1, 0.68, 1);
  overflow: hidden;
  padding-bottom: env(safe-area-inset-bottom);
}

.bottom-sheet-handle-wrapper {
  padding: 12px;
  display: flex;
  justify-content: center;
  align-items: center;
  cursor: grab;
  touch-action: none;
}

.bottom-sheet-handle {
  width: 36px;
  height: 5px;
  background-color: rgba(255, 255, 255, 0.25);
  border-radius: 3px;
}

.bottom-sheet-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 16px 12px 16px;
  border-bottom: 1px solid var(--glass-border);
}

.bottom-sheet-title {
  font-weight: 600;
  font-size: var(--text-base);
  color: var(--fg-primary);
}

.bottom-sheet-content {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}
```

- [ ] **Step 2: Create `BottomSheet.tsx`**

```typescript
import React, { useState, useRef } from 'react';
import { X } from 'lucide-react';
import './BottomSheet.css';

interface BottomSheetProps {
  isOpen: boolean;
  onClose: () => void;
  title?: string;
  children: React.ReactNode;
}

export const BottomSheet: React.FC<BottomSheetProps> = ({ isOpen, onClose, title, children }) => {
  const [startY, setStartY] = useState<number | null>(null);
  const [currentY, setCurrentY] = useState<number>(0);
  const containerRef = useRef<HTMLDivElement>(null);

  if (!isOpen) return null;

  const handleTouchStart = (e: React.TouchEvent) => {
    setStartY(e.touches[0].clientY);
  };

  const handleTouchMove = (e: React.TouchEvent) => {
    if (startY === null) return;
    const deltaY = e.touches[0].clientY - startY;
    if (deltaY > 0) {
      setCurrentY(deltaY);
    }
  };

  const handleTouchEnd = () => {
    if (currentY > 100) {
      onClose();
    }
    setStartY(null);
    setCurrentY(0);
  };

  return (
    <div className="bottom-sheet-overlay" onClick={onClose}>
      <div 
        ref={containerRef}
        className="bottom-sheet-container"
        style={{ transform: `translateY(${currentY}px)` }}
        onClick={(e) => e.stopPropagation()}
      >
        <div 
          className="bottom-sheet-handle-wrapper"
          onTouchStart={handleTouchStart}
          onTouchMove={handleTouchMove}
          onTouchEnd={handleTouchEnd}
        >
          <div className="bottom-sheet-handle" />
        </div>
        {title && (
          <div className="bottom-sheet-header">
            <span className="bottom-sheet-title">{title}</span>
            <button className="icon-action-btn" onClick={onClose} style={{ background: 'transparent', border: 'none', color: 'var(--fg-muted)', cursor: 'pointer' }}>
              <X size={20} />
            </button>
          </div>
        )}
        <div className="bottom-sheet-content">
          {children}
        </div>
      </div>
    </div>
  );
};
```

- [ ] **Step 3: Verify TypeScript compilation**

Run: `cd j:/wildcard-prompt-studio/frontend && npm run build`  
Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add frontend/src/components/common/BottomSheet.tsx frontend/src/components/common/BottomSheet.css
git commit -m "feat: add touch-native Slide-Up BottomSheet component"
```

---

### Task 4: Mobile Bottom Navigation Dock Component (`MobileBottomNav.tsx`)

**Files:**
- Create: `j:/wildcard-prompt-studio/frontend/src/components/layout/MobileBottomNav.tsx`
- Create: `j:/wildcard-prompt-studio/frontend/src/components/layout/MobileBottomNav.css`

- [ ] **Step 1: Create `MobileBottomNav.css`**

```css
.mobile-bottom-nav {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  height: calc(56px + env(safe-area-inset-bottom));
  padding-bottom: env(safe-area-inset-bottom);
  background: var(--bg-surface);
  border-top: 1px solid var(--glass-border);
  backdrop-filter: var(--backdrop-blur);
  display: flex;
  align-items: center;
  justify-content: space-around;
  z-index: 900;
}

.mobile-nav-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: var(--fg-muted);
  font-size: 10px;
  gap: 2px;
  flex: 1;
  height: 100%;
  border: none;
  background: transparent;
  cursor: pointer;
  transition: color 0.2s ease, transform 0.1s ease;
}

.mobile-nav-item.active {
  color: var(--accent-cyan);
}

.mobile-nav-item.active svg {
  filter: drop-shadow(0 0 6px var(--accent-cyan));
}

.more-tools-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
  padding: 8px 0;
}

.more-tool-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 16px 8px;
  background: var(--bg-glass-card);
  border: 1px solid var(--glass-border);
  border-radius: 12px;
  color: var(--fg-primary);
  font-size: 12px;
  border: none;
  cursor: pointer;
  text-align: center;
}

.more-tool-card:active {
  transform: scale(0.95);
}
```

- [ ] **Step 2: Create `MobileBottomNav.tsx`**

```typescript
import React, { useState } from 'react';
import { FileText, Sparkles, Cpu, Folder, MoreHorizontal, Wand2, Tag, Grid, Activity, Award, Database, Eye, Settings, UploadCloud } from 'lucide-react';
import { useAppStore, ViewType } from '../../store/useAppStore';
import { BottomSheet } from '../common/BottomSheet';
import './MobileBottomNav.css';

export const MobileBottomNav: React.FC = () => {
  const { activeView, setActiveView } = useAppStore();
  const [isMoreOpen, setIsMoreOpen] = useState(false);

  const primaryItems: { view: ViewType; label: string; icon: React.ReactNode }[] = [
    { view: 'prompts', label: 'Prompts', icon: <FileText size={20} /> },
    { view: 'anima', label: 'ANIMA', icon: <Sparkles size={20} style={{ color: '#ec4899' }} /> },
    { view: 'comfyui', label: 'ComfyUI', icon: <Cpu size={20} /> },
    { view: 'gallery', label: 'Gallery', icon: <Folder size={20} style={{ color: '#fab387' }} /> },
  ];

  const moreItems: { view: ViewType; label: string; icon: React.ReactNode }[] = [
    { view: 'explorer', label: 'Explorer', icon: <Folder size={22} /> },
    { view: 'wildcards', label: 'Wildcards', icon: <Sparkles size={22} /> },
    { view: 'tags', label: 'Tags', icon: <Tag size={22} /> },
    { view: 'krea2', label: 'Krea 2', icon: <Wand2 size={22} /> },
    { view: 'vision', label: 'Vision', icon: <Eye size={22} /> },
    { view: 'matrix', label: 'Matrix', icon: <Grid size={22} /> },
    { view: 'simulator', label: 'Simulator', icon: <Activity size={22} /> },
    { view: 'aesthetic', label: 'Aesthetic', icon: <Award size={22} /> },
    { view: 'rag', label: 'RAG Knowledge', icon: <Database size={22} /> },
    { view: 'import', label: 'Import', icon: <UploadCloud size={22} /> },
    { view: 'settings', label: 'Settings', icon: <Settings size={22} /> },
  ];

  const handleSelectView = (view: ViewType) => {
    setActiveView(view);
    setIsMoreOpen(false);
  };

  return (
    <>
      <nav className="mobile-bottom-nav">
        {primaryItems.map((item) => (
          <button
            key={item.view}
            className={`mobile-nav-item ${activeView === item.view ? 'active' : ''}`}
            onClick={() => handleSelectView(item.view)}
          >
            {item.icon}
            <span>{item.label}</span>
          </button>
        ))}
        <button
          className={`mobile-nav-item ${isMoreOpen ? 'active' : ''}`}
          onClick={() => setIsMoreOpen(true)}
        >
          <MoreHorizontal size={20} />
          <span>More</span>
        </button>
      </nav>

      <BottomSheet isOpen={isMoreOpen} onClose={() => setIsMoreOpen(false)} title="Studio Tools">
        <div className="more-tools-grid">
          {moreItems.map((item) => (
            <button
              key={item.view}
              className="more-tool-card"
              onClick={() => handleSelectView(item.view)}
            >
              {item.icon}
              <span>{item.label}</span>
            </button>
          ))}
        </div>
      </BottomSheet>
    </>
  );
};
```

- [ ] **Step 3: Verify TypeScript compilation**

Run: `cd j:/wildcard-prompt-studio/frontend && npm run build`  
Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add frontend/src/components/layout/MobileBottomNav.tsx frontend/src/components/layout/MobileBottomNav.css
git commit -m "feat: add MobileBottomNav dock with quick tools bottom sheet"
```

---

### Task 5: Mobile/Desktop Layout Integration in `MainLayout.tsx` & `Sidebar.tsx`

**Files:**
- Modify: `j:/wildcard-prompt-studio/frontend/src/components/layout/MainLayout.tsx`
- Modify: `j:/wildcard-prompt-studio/frontend/src/components/layout/Sidebar.tsx`
- Modify: `j:/wildcard-prompt-studio/frontend/src/components/layout/Sidebar.css`

- [ ] **Step 1: Adapt `MainLayout.tsx` to switch between Desktop Activity Bar and Mobile Bottom Nav**

Update `frontend/src/components/layout/MainLayout.tsx`:

```typescript
import React, { useEffect } from 'react';
import { Sidebar } from './Sidebar';
import { ContextPanel } from './ContextPanel';
import { MobileBottomNav } from './MobileBottomNav';
import { useAppStore } from '../../store/useAppStore';
import { useDeviceDetect } from '../../store/useDeviceDetect';
import { Menu } from 'lucide-react';
import './MainLayout.css';

interface MainLayoutProps {
  children: React.ReactNode;
}

export const MainLayout: React.FC<MainLayoutProps> = ({ children }) => {
  const theme = useAppStore(state => state.theme);
  const toggleMobileMenu = useAppStore(state => state.toggleMobileMenu);
  const { isMobile } = useDeviceDetect();

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme || 'dark');
  }, [theme]);

  return (
    <div className={`layout-container ${isMobile ? 'is-mobile-layout' : 'is-desktop-layout'}`}>
      <div className="titlebar">
        {isMobile && (
          <button 
            className="icon-action-btn" 
            onClick={toggleMobileMenu}
            style={{ background: 'transparent', border: 'none', color: 'var(--fg-primary)', cursor: 'pointer', padding: '4px' }}
          >
            <Menu size={20} />
          </button>
        )}
        <div className="titlebar-title">Wildcard Prompt Studio</div>
      </div>
      
      <div className="layout-body">
        <Sidebar />
        <main className="main-content">
          {children}
        </main>
        {!isMobile && <ContextPanel />}
      </div>
      
      {!isMobile && (
        <div className="statusbar">
          <span>Ready</span>
        </div>
      )}

      {isMobile && <MobileBottomNav />}
    </div>
  );
};
```

- [ ] **Step 2: Adapt `Sidebar.tsx` to render as a BottomSheet on mobile when menu toggled**

Update `frontend/src/components/layout/Sidebar.tsx` to check `isMobile` and wrap with `BottomSheet` if `isMobile`:

```typescript
// Import useDeviceDetect and BottomSheet
import { useDeviceDetect } from '../../store/useDeviceDetect';
import { BottomSheet } from '../common/BottomSheet';

// Inside Sidebar component:
const { isMobile } = useDeviceDetect();
const { isMobileMenuOpen, setMobileMenuOpen } = useAppStore();

// If isMobile, render Sidebar content inside BottomSheet:
if (isMobile) {
  return (
    <BottomSheet isOpen={isMobileMenuOpen} onClose={() => setMobileMenuOpen(false)} title="Explorer & Documents">
      <div className="mobile-sidebar-inner">
        {/* Render search & tree items without the vertical desktop activity bar */}
      </div>
    </BottomSheet>
  );
}
```

- [ ] **Step 3: Add CSS for `Sidebar.css` mobile adjustments**

Modify `frontend/src/components/layout/Sidebar.css` to hide vertical activity bar on mobile:

```css
@media (max-width: 768px) {
  .sidebar-container {
    display: none;
  }
}
```

- [ ] **Step 4: Verify build**

Run: `cd j:/wildcard-prompt-studio/frontend && npm run build`  
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/layout/MainLayout.tsx frontend/src/components/layout/Sidebar.tsx frontend/src/components/layout/Sidebar.css
git commit -m "feat: integrate responsive device detection into MainLayout and Sidebar"
```

---

### Task 6: Mobile Prompt Quick Syntax Toolbar (`MobilePromptToolbar.tsx`)

**Files:**
- Create: `j:/wildcard-prompt-studio/frontend/src/components/editor/MobilePromptToolbar.tsx`
- Create: `j:/wildcard-prompt-studio/frontend/src/components/editor/MobilePromptToolbar.css`
- Modify: `j:/wildcard-prompt-studio/frontend/src/components/editor/PromptEditor.tsx`

- [ ] **Step 1: Create `MobilePromptToolbar.css`**

```css
.mobile-prompt-toolbar {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background: var(--bg-surface);
  border-top: 1px solid var(--glass-border);
  overflow-x: auto;
  white-space: nowrap;
}

.syntax-pill-btn {
  background: var(--bg-glass-card);
  border: 1px solid var(--glass-border);
  color: var(--fg-primary);
  font-family: var(--font-mono);
  font-size: 12px;
  padding: 6px 12px;
  border-radius: 16px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 4px;
}

.syntax-pill-btn:active {
  transform: scale(0.95);
  background: var(--accent-cyan);
  color: #000;
}
```

- [ ] **Step 2: Create `MobilePromptToolbar.tsx`**

```typescript
import React from 'react';
import './MobilePromptToolbar.css';

interface MobilePromptToolbarProps {
  onInsertText: (text: string) => void;
}

export const MobilePromptToolbar: React.FC<MobilePromptToolbarProps> = ({ onInsertText }) => {
  const shortcuts = [
    { label: '{a|b}', insert: '{option1 | option2}' },
    { label: '__wildcard__', insert: '__colors__' },
    { label: '(weight)', insert: '(masterpiece:1.2)' },
    { label: '[negative]', insert: '[blurry, low quality]' },
    { label: '8k photo', insert: 'hyperrealistic, 8k resolution, cinematic lighting' },
  ];

  return (
    <div className="mobile-prompt-toolbar">
      {shortcuts.map((sc, i) => (
        <button key={i} className="syntax-pill-btn" onClick={() => onInsertText(sc.insert)}>
          {sc.label}
        </button>
      ))}
    </div>
  );
};
```

- [ ] **Step 3: Attach `MobilePromptToolbar` to `PromptEditor.tsx` when `isMobile` is true**

Modify `frontend/src/components/editor/PromptEditor.tsx` to import `useDeviceDetect` and render `MobilePromptToolbar` at the bottom of the prompt editing canvas on mobile.

- [ ] **Step 4: Verify build**

Run: `cd j:/wildcard-prompt-studio/frontend && npm run build`  
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/editor/MobilePromptToolbar.tsx frontend/src/components/editor/MobilePromptToolbar.css frontend/src/components/editor/PromptEditor.tsx
git commit -m "feat: add MobilePromptToolbar for fast mobile syntax insertion"
```

---

### Task 7: Gallery & Live Stream Touch & Media Optimization

**Files:**
- Modify: `j:/wildcard-prompt-studio/frontend/src/components/gallery/GalleryView.tsx`
- Modify: `j:/wildcard-prompt-studio/frontend/src/components/editor/ComfyUILiveStream.tsx`

- [ ] **Step 1: Ensure Gallery masonry grid scales down to 1-column on mobile**

Modify `frontend/src/components/gallery/GalleryView.css`:

```css
@media (max-width: 600px) {
  .gallery-grid {
    grid-template-columns: 1fr !important;
    gap: 12px;
  }
}
```

- [ ] **Step 2: Ensure ComfyUI Live Stream canvas stacks vertically on mobile**

Modify `frontend/src/components/editor/ComfyUILiveStream.css`:

```css
@media (max-width: 768px) {
  .comfy-stream-layout {
    flex-direction: column !important;
  }
}
```

- [ ] **Step 3: Verify build**

Run: `cd j:/wildcard-prompt-studio/frontend && npm run build`  
Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add frontend/src/components/gallery/GalleryView.css frontend/src/components/editor/ComfyUILiveStream.css
git commit -m "style: optimize Gallery and ComfyUI live stream layouts for mobile viewports"
```

---

### Task 8: Verification & Production Build Validation

- [ ] **Step 1: Execute production build**

Run: `cd j:/wildcard-prompt-studio/frontend && npm run build`  
Expected: Clean build with 0 TypeScript compilation or bundle errors.

- [ ] **Step 2: Final git status check**

Run: `git status`  
Expected: Working tree clean, all commits applied.
