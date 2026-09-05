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

