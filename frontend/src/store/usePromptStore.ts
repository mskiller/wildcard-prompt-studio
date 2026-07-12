import { create } from 'zustand';

interface PromptStore {
  promptText: string;
  expandedPromptText: string;
  setPromptText: (text: string) => void;
  setExpandedPromptText: (text: string) => void;
}

export const usePromptStore = create<PromptStore>((set) => ({
  promptText: '',
  expandedPromptText: '',
  setPromptText: (text) => set({ promptText: text }),
  setExpandedPromptText: (text) => set({ expandedPromptText: text }),
}));
