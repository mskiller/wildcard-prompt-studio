
import { MainLayout } from './components/layout/MainLayout';
import { PromptEditor } from './components/editor/PromptEditor';

function App() {
  return (
    <MainLayout>
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', width: '100%', height: '100%' }}>
        <PromptEditor />
      </div>
    </MainLayout>
  );
}

export default App;
