import { create } from 'zustand';

interface PromptStore {
  promptText: string;
  expandedPromptText: string;
  currentPrompt?: any;
  setPromptText: (text: string) => void;
  setExpandedPromptText: (text: string) => void;
  appendTag: (tag: string) => void;
}

export const usePromptStore = create<PromptStore>((set) => ({
  promptText: '',
  expandedPromptText: '',
  setPromptText: (text) => set({ promptText: text }),
  setExpandedPromptText: (text) => set({ expandedPromptText: text }),
  appendTag: (tag: string) => set((state) => {
    const trimmed = state.promptText.trim();
    if (!trimmed) return { promptText: tag };
    if (trimmed.endsWith(',')) return { promptText: `${trimmed} ${tag}` };
    return { promptText: `${trimmed}, ${tag}` };
  }),
}));
