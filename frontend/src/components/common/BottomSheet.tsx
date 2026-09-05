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
