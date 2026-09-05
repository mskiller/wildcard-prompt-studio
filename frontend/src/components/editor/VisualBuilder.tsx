import React from 'react';
import { motion } from 'framer-motion';
import { GripVertical } from 'lucide-react';
import './VisualBuilder.css';

interface VisualBuilderProps {
  value: string;
  onChange: (val: string) => void;
}

export const VisualBuilder: React.FC<VisualBuilderProps> = ({ value, onChange }) => {
  // Simple parser: split by double newlines to form "blocks"
  const blocks = value.split(/\n\s*\n/).filter(b => b.trim() !== '');

  const updateBlock = (index: number, newText: string) => {
    const newBlocks = [...blocks];
    newBlocks[index] = newText;
    onChange(newBlocks.join('\n\n'));
  };

  const addBlock = () => {
    onChange(value + (value.trim() ? '\n\n' : '') + 'New Block...');
  };

  return (
    <div className="visual-builder-container">
      <div className="blocks-list">
        {blocks.map((block, index) => (
          <motion.div 
            key={index}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3, delay: index * 0.05 }}
            className="prompt-block glass-panel"
          >
            <div className="block-drag-handle">
              <GripVertical size={16} />
            </div>
            <div className="block-content">
              <textarea
                value={block}
                onChange={(e) => updateBlock(index, e.target.value)}
                placeholder="Enter prompt text or __wildcards__ here..."
              />
            </div>
          </motion.div>
        ))}
      </div>
      
      <motion.button 
        whileHover={{ scale: 1.02 }}
        whileTap={{ scale: 0.98 }}
        className="add-block-btn glass-panel"
        onClick={addBlock}
      >
        + Add New Block
      </motion.button>
    </div>
  );
};
