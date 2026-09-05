import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { Language, translations } from '../i18n';

export type ViewType =
  | 'explorer'
  | 'prompts'
  | 'wildcards'
  | 'tags'
  | 'gallery'
  | 'import'
  | 'settings'
  | 'krea2'
  | 'anima'
  | 'matrix'
  | 'simulator'
  | 'aesthetic'
  | 'rag'
  | 'vision'
  | 'comfyui';

export type ActiveView = ViewType;

export type ThemeType = 'dark' | 'light';
export type KreaVariant = 'turbo' | 'medium' | 'large';

export interface ComfyStateSettings {
  selectedModel: string;
  selectedSampler: string;
  selectedScheduler: string;
  steps: number;
  cfg: number;
  width: number;
  height: number;
  resPreset: string;
  isCustomRes: boolean;
  singlePrompt: string;
  sweepInput: string;
  targetNodeId: string;
  seedNodeId: string;
  gallery: string[];
}

interface AppState {
  activeView: ViewType;
  setActiveView: (view: ViewType) => void;

  // Theme & i18n Language
  theme: ThemeType;
  setTheme: (theme: ThemeType) => void;
  language: Language;
  setLanguage: (lang: Language) => void;
  t: (key: keyof typeof translations['en']) => string;

  // API Connections
  comfyUIUrl: string;
  setComfyUIUrl: (url: string) => void;
  koboldCppUrl: string;
  setKoboldCppUrl: (url: string) => void;
  ollamaUrl: string;
  setOllamaUrl: (url: string) => void;
  geminiApiKey: string;
  setGeminiApiKey: (key: string) => void;

  // Prompt Improvement Defaults
  defaultKreaVariant: KreaVariant;
  setDefaultKreaVariant: (variant: KreaVariant) => void;
  defaultAIProvider: string;
  setDefaultAIProvider: (provider: string) => void;
  autoCleanBuzzwords: boolean;
  setAutoCleanBuzzwords: (clean: boolean) => void;
  autoQuoteTargets: boolean;
  setAutoQuoteTargets: (quote: boolean) => void;
  enableThinkingTokenBoost: boolean;
  setEnableThinkingTokenBoost: (enable: boolean) => void;
  maxOutputTokens: number;
  setMaxOutputTokens: (tokens: number) => void;

  // Live ComfyUI Stream Persisted Settings
  comfySettings: ComfyStateSettings;
  setComfySettings: (settings: Partial<ComfyStateSettings>) => void;

  activeDocument: { type: 'prompt' | 'wildcard'; id: number; name: string; content: string } | null;
  setActiveDocument: (doc: { type: 'prompt' | 'wildcard'; id: number; name: string; content: string } | null) => void;
  activeModelProfileId: number | null;
  setActiveModelProfileId: (id: number | null) => void;

  rightPanelTab: 'chat' | 'tools';
  setRightPanelTab: (tab: 'chat' | 'tools') => void;

  refreshKey: number;
  triggerRefresh: () => void;

  // Matrix Studio – last-used template (persisted)
  matrixPrompt: string;
  setMatrixPrompt: (prompt: string) => void;

  // Mobile navigation state
  isMobileMenuOpen: boolean;
  setMobileMenuOpen: (open: boolean) => void;
  toggleMobileMenu: () => void;
}

export const useAppStore = create<AppState>()(
  persist(
    (set, get) => ({
      activeView: 'explorer',
      setActiveView: (view) => set({ activeView: view }),

      theme: 'dark',
      setTheme: (theme) => set({ theme }),
      language: 'en',
      setLanguage: (language) => set({ language }),
      t: (key) => {
        const lang = get().language || 'en';
        return translations[lang][key] || translations['en'][key] || key;
      },

      comfyUIUrl: 'http://localhost:8188',
      setComfyUIUrl: (url) => set({ comfyUIUrl: url }),
      koboldCppUrl: 'http://localhost:5001',
      setKoboldCppUrl: (url) => set({ koboldCppUrl: url }),
      ollamaUrl: 'http://localhost:11434',
      setOllamaUrl: (url) => set({ ollamaUrl: url }),
      geminiApiKey: '',
      setGeminiApiKey: (key) => set({ geminiApiKey: key }),

      defaultKreaVariant: 'medium',
      setDefaultKreaVariant: (defaultKreaVariant) => set({ defaultKreaVariant }),
      defaultAIProvider: 'kobold',
      setDefaultAIProvider: (defaultAIProvider) => set({ defaultAIProvider }),
      autoCleanBuzzwords: true,
      setAutoCleanBuzzwords: (autoCleanBuzzwords) => set({ autoCleanBuzzwords }),
      autoQuoteTargets: true,
      setAutoQuoteTargets: (autoQuoteTargets) => set({ autoQuoteTargets }),
      enableThinkingTokenBoost: true,
      setEnableThinkingTokenBoost: (enableThinkingTokenBoost) => set({ enableThinkingTokenBoost }),
      maxOutputTokens: 4096,
      setMaxOutputTokens: (maxOutputTokens) => set({ maxOutputTokens }),

      comfySettings: {
        selectedModel: 'v1-5-pruned-emaonly.safetensors',
        selectedSampler: 'euler',
        selectedScheduler: 'normal',
        steps: 20,
        cfg: 7.0,
        width: 512,
        height: 512,
        resPreset: '512 x 512 (Square - SD 1.5)',
        isCustomRes: false,
        singlePrompt: 'masterpiece, best quality, vibrant futuristic cyberpunk city at sunset, highly detailed, 8k',
        sweepInput:
          'cyberpunk warrior standing in neon alley, 8k\nsteampunk inventor in brass workshop, masterpiece\nfantasy sorceress inside glowing crystal cavern, detailed',
        targetNodeId: '6',
        seedNodeId: '3',
        gallery: [],
      },
      setComfySettings: (settings) =>
        set((state) => ({
          comfySettings: { ...state.comfySettings, ...settings },
        })),

      activeDocument: null,
      setActiveDocument: (doc) => set({ activeDocument: doc }),
      activeModelProfileId: null,
      setActiveModelProfileId: (id) => set({ activeModelProfileId: id }),

      rightPanelTab: 'chat',
      setRightPanelTab: (tab) => set({ rightPanelTab: tab }),

      refreshKey: 0,
      triggerRefresh: () => set((state) => ({ refreshKey: state.refreshKey + 1 })),

      matrixPrompt: 'a {cyberpunk|steampunk|fantasy} {cat|dog|fox} in a {neon city|forest}',
      setMatrixPrompt: (matrixPrompt) => set({ matrixPrompt }),

      isMobileMenuOpen: false,
      setMobileMenuOpen: (open) => set({ isMobileMenuOpen: open }),
      toggleMobileMenu: () => set((state) => ({ isMobileMenuOpen: !state.isMobileMenuOpen })),
    }),
    {
      name: 'app-settings-storage',
      partialize: (state) => ({
        theme: state.theme,
        language: state.language,
        comfyUIUrl: state.comfyUIUrl,
        koboldCppUrl: state.koboldCppUrl,
        ollamaUrl: state.ollamaUrl,
        geminiApiKey: state.geminiApiKey,
        defaultKreaVariant: state.defaultKreaVariant,
        defaultAIProvider: state.defaultAIProvider,
        autoCleanBuzzwords: state.autoCleanBuzzwords,
        autoQuoteTargets: state.autoQuoteTargets,
        enableThinkingTokenBoost: state.enableThinkingTokenBoost,
        maxOutputTokens: state.maxOutputTokens,
        activeModelProfileId: state.activeModelProfileId,
        comfySettings: state.comfySettings,
        matrixPrompt: state.matrixPrompt,
      }),
    }
  )
);
