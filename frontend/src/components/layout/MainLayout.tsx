import React from 'react';
import { Sidebar } from './Sidebar';
import { ContextPanel } from './ContextPanel';
import './MainLayout.css';

interface MainLayoutProps {
  children: React.ReactNode;
}

export const MainLayout: React.FC<MainLayoutProps> = ({ children }) => {
  return (
    <div className="layout-container">
      <div className="titlebar">
        <div className="titlebar-title">Wildcard Prompt Studio</div>
      </div>
      
      <div className="layout-body">
        <Sidebar />
        <main className="main-content">
          {children}
        </main>
        <ContextPanel />
      </div>
      
      <div className="statusbar">
        <span>Ready</span>
      </div>
    </div>
  );
};
