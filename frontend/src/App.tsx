import { MainLayout } from './components/layout/MainLayout';
import { PromptEditor } from './components/editor/PromptEditor';
import { SettingsView } from './components/settings/SettingsView';
import { ImporterUI } from './components/editor/ImporterUI';
import { TagsView } from './components/editor/TagsView';
import { Krea2StudioPanel } from './components/editor/Krea2StudioPanel';
import { AnimaStudioPanel } from './components/editor/AnimaStudioPanel';
import { WildcardMatrixPanel } from './components/editor/WildcardMatrixPanel';
import { PromptGraphViewer } from './components/editor/PromptGraphViewer';
import { AestheticRankerPanel } from './components/editor/AestheticRankerPanel';
import { RAGKnowledgeInspector } from './components/editor/RAGKnowledgeInspector';
import { VisionInspectorPanel } from './components/editor/VisionInspectorPanel';
import { ComfyUILiveStream } from './components/editor/ComfyUILiveStream';
import { GalleryView } from './components/gallery/GalleryView';
import { useAppStore } from './store/useAppStore';

function App() {
  const activeView = useAppStore(state => state.activeView);
  const setActiveDocument = useAppStore(state => state.setActiveDocument);

  const handleInsertPrompt = (promptText: string) => {
    setActiveDocument({
      type: 'prompt',
      id: Date.now(),
      name: 'Vision Prompt',
      content: promptText
    });
  };

  return (
    <MainLayout>
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', width: '100%', height: '100%', overflow: 'auto', padding: '16px' }}>
        {activeView === 'settings' && <SettingsView />}
        {activeView === 'explorer' && <PromptEditor />}
        {activeView === 'prompts' && <PromptEditor />}
        {activeView === 'wildcards' && <PromptEditor />}
        {activeView === 'tags' && <TagsView />}
        {activeView === 'gallery' && <GalleryView />}
        {activeView === 'krea2' && <Krea2StudioPanel />}
        {activeView === 'anima' && <AnimaStudioPanel />}
        {activeView === 'vision' && <VisionInspectorPanel onInsertPrompt={handleInsertPrompt} />}
        {activeView === 'comfyui' && <ComfyUILiveStream />}
        {activeView === 'matrix' && <WildcardMatrixPanel />}
        {activeView === 'simulator' && <PromptGraphViewer />}
        {activeView === 'aesthetic' && <AestheticRankerPanel />}
        {activeView === 'rag' && <RAGKnowledgeInspector />}
        {activeView === 'import' && <ImporterUI />}
      </div>
    </MainLayout>
  );
}

export default App;
