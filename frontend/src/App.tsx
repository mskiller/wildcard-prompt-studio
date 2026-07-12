import React from 'react';
import { MainLayout } from './components/layout/MainLayout';

function App() {
  return (
    <MainLayout>
      <div style={{ flex: 1, padding: '1rem' }}>
        <h2>Main Editor Area</h2>
        <p style={{ color: '#888', marginTop: '1rem' }}>Select a file from the explorer to begin editing.</p>
      </div>
    </MainLayout>
  );
}

export default App;
