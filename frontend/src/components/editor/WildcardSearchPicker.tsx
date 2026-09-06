import React, { useState, useRef, useEffect, useMemo, useCallback } from 'react';
import { Search, Plus, ChevronDown, X, Check } from 'lucide-react';
import './WildcardSearchPicker.css';

export interface WildcardSearchPickerProps {
  value?: string;
  availableWildcards: string[];
  placeholder?: string;
  onSelect: (wildcardName: string) => void;
  variant?: 'toolbar' | 'canvas-node' | 'inspector';
  allowCustom?: boolean;
  readOnly?: boolean;
  className?: string;
}

const MAX_DISPLAY_ITEMS = 80;

interface SelectableItem {
  type: 'wildcard' | 'custom';
  value: string;
}

export const WildcardSearchPicker: React.FC<WildcardSearchPickerProps> = ({
  value,
  availableWildcards = [],
  placeholder,
  onSelect,
  variant = 'canvas-node',
  allowCustom = true,
  readOnly = false,
  className = '',
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [query, setQuery] = useState('');
  const [highlightedIndex, setHighlightedIndex] = useState(0);

  const containerRef = useRef<HTMLDivElement>(null);
  const triggerRef = useRef<HTMLButtonElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const listRef = useRef<HTMLDivElement>(null);

  // Normalize query and compute filtered wildcards
  const trimmedQuery = query.trim();
  const cleanCustomValue = useMemo(
    () => trimmedQuery.replace(/^__+|__+$/g, ''),
    [trimmedQuery]
  );

  const filteredWildcards = useMemo(() => {
    if (!trimmedQuery) {
      return availableWildcards;
    }
    const lower = trimmedQuery.toLowerCase();
    return availableWildcards.filter(w => w.toLowerCase().includes(lower));
  }, [availableWildcards, trimmedQuery]);

  const displayedWildcards = useMemo(() => {
    return filteredWildcards.slice(0, MAX_DISPLAY_ITEMS);
  }, [filteredWildcards]);

  // Check if query exactly matches an existing wildcard (case-insensitive)
  const exactMatch = useMemo(() => {
    if (!cleanCustomValue) return false;
    const lower = cleanCustomValue.toLowerCase();
    return availableWildcards.some(w => w.toLowerCase() === lower);
  }, [availableWildcards, cleanCustomValue]);

  const showCustomOption = Boolean(allowCustom && cleanCustomValue && !exactMatch);

  // Build unified list of selectable items for keyboard navigation
  const selectableItems = useMemo<SelectableItem[]>(() => {
    const items: SelectableItem[] = displayedWildcards.map(w => ({
      type: 'wildcard',
      value: w,
    }));
    if (showCustomOption) {
      items.push({
        type: 'custom',
        value: cleanCustomValue,
      });
    }
    return items;
  }, [displayedWildcards, showCustomOption, cleanCustomValue]);

  // Keep highlightedIndex in bounds when selectable items change
  useEffect(() => {
    if (selectableItems.length > 0) {
      setHighlightedIndex(prev => {
        if (prev < 0 || prev >= selectableItems.length) {
          return 0;
        }
        return prev;
      });
    } else {
      setHighlightedIndex(-1);
    }
  }, [selectableItems]);

  // Focus input and scroll highlighted into view when opened
  useEffect(() => {
    if (isOpen) {
      requestAnimationFrame(() => {
        inputRef.current?.focus();
      });
    }
  }, [isOpen]);

  // Scroll active item into view
  useEffect(() => {
    if (isOpen && listRef.current && highlightedIndex >= 0) {
      const activeEl = listRef.current.querySelector(
        `[data-index="${highlightedIndex}"]`
      ) as HTMLElement | null;
      if (activeEl) {
        activeEl.scrollIntoView({ block: 'nearest' });
      }
    }
  }, [highlightedIndex, isOpen]);

  // Click outside to close
  useEffect(() => {
    if (!isOpen) return;

    const handleClickOutside = (event: MouseEvent | TouchEvent) => {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    document.addEventListener('touchstart', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
      document.removeEventListener('touchstart', handleClickOutside);
    };
  }, [isOpen]);

  const handlePick = useCallback(
    (wildcardName: string) => {
      onSelect(wildcardName);
      setIsOpen(false);
      setQuery('');
      triggerRef.current?.focus();
    },
    [onSelect]
  );

  const openPopover = useCallback(() => {
    if (readOnly) return;
    setIsOpen(true);
    setQuery('');

    if (value) {
      const cleanVal = value.replace(/^__+|__+$/g, '');
      const idx = availableWildcards.findIndex(
        w => w.toLowerCase() === cleanVal.toLowerCase()
      );
      if (idx >= 0 && idx < MAX_DISPLAY_ITEMS) {
        setHighlightedIndex(idx);
      } else {
        setHighlightedIndex(0);
      }
    } else {
      setHighlightedIndex(0);
    }
  }, [readOnly, value, availableWildcards]);

  const handleTriggerClick = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (readOnly) return;
    if (isOpen) {
      setIsOpen(false);
    } else {
      openPopover();
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    e.stopPropagation();

    if (!isOpen) {
      if (e.key === 'Enter' || e.key === ' ' || e.key === 'ArrowDown') {
        e.preventDefault();
        openPopover();
      }
      return;
    }

    if (e.key === 'Escape') {
      e.preventDefault();
      setIsOpen(false);
      triggerRef.current?.focus();
      return;
    }

    if (e.key === 'ArrowDown') {
      e.preventDefault();
      if (selectableItems.length === 0) return;
      setHighlightedIndex(prev => (prev + 1) % selectableItems.length);
      return;
    }

    if (e.key === 'ArrowUp') {
      e.preventDefault();
      if (selectableItems.length === 0) return;
      setHighlightedIndex(prev =>
        prev <= 0 ? selectableItems.length - 1 : prev - 1
      );
      return;
    }

    if (e.key === 'Enter') {
      e.preventDefault();
      if (highlightedIndex >= 0 && highlightedIndex < selectableItems.length) {
        const item = selectableItems[highlightedIndex];
        handlePick(item.value);
      } else if (showCustomOption) {
        handlePick(cleanCustomValue);
      }
      return;
    }

    if (e.key === 'Tab') {
      setIsOpen(false);
    }
  };

  // Format trigger button label
  const getTriggerLabel = () => {
    if (value) {
      if (variant === 'canvas-node') {
        const clean = value.replace(/^__+|__+$/g, '');
        return `__${clean}__`;
      }
      return value;
    }
    if (placeholder) return placeholder;
    switch (variant) {
      case 'toolbar':
        return 'Add Wildcard';
      case 'canvas-node':
        return 'Select wildcard...';
      case 'inspector':
      default:
        return 'Select wildcard...';
    }
  };

  const isPlaceholder = !value;

  // Render trigger icon based on variant
  const renderTriggerIcon = () => {
    if (variant === 'toolbar') {
      return <Plus size={14} className="wildcard-picker-icon" aria-hidden="true" />;
    }
    return <Search size={13} className="wildcard-picker-icon" aria-hidden="true" />;
  };

  // Substring highlight helper
  const renderHighlightedWildcard = (text: string, highlight: string) => {
    if (!highlight.trim()) {
      return text;
    }
    const escaped = highlight.trim().replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    const regex = new RegExp(`(${escaped})`, 'gi');
    const parts = text.split(regex);
    return (
      <>
        {parts.map((part, i) =>
          part.toLowerCase() === highlight.trim().toLowerCase() ? (
            <span key={i} className="wildcard-picker-highlight-match">
              {part}
            </span>
          ) : (
            part
          )
        )}
      </>
    );
  };

  // Match count text for footer
  const getFooterMatchCount = () => {
    const total = filteredWildcards.length;
    if (total > MAX_DISPLAY_ITEMS) {
      return `Showing ${displayedWildcards.length} of ${total} matches`;
    }
    if (total === 1) {
      return '1 match';
    }
    if (total === 0) {
      return '0 matches';
    }
    return `${total} wildcards`;
  };

  return (
    <div
      ref={containerRef}
      className={`wildcard-search-picker wildcard-search-picker-${variant} ${
        isOpen ? 'is-open' : ''
      } ${readOnly ? 'is-readonly' : ''} ${className}`.trim()}
      onMouseDown={e => e.stopPropagation()}
      onPointerDown={e => e.stopPropagation()}
      onKeyDown={handleKeyDown}
    >
      <button
        ref={triggerRef}
        type="button"
        className={`wildcard-picker-trigger ${isPlaceholder ? 'is-placeholder' : ''}`}
        onClick={handleTriggerClick}
        onMouseDown={e => e.stopPropagation()}
        disabled={readOnly}
        aria-haspopup="listbox"
        aria-expanded={isOpen}
        title={value ? `Wildcard: ${value}` : placeholder || 'Choose wildcard'}
      >
        <div className="wildcard-picker-trigger-left">
          {renderTriggerIcon()}
          <span className="wildcard-picker-label">{getTriggerLabel()}</span>
        </div>
        <ChevronDown
          size={14}
          className={`wildcard-picker-chevron ${isOpen ? 'is-open' : ''}`}
          aria-hidden="true"
        />
      </button>

      {isOpen && (
        <div
          className="wildcard-search-picker-popover"
          role="listbox"
          onMouseDown={e => e.stopPropagation()}
          onPointerDown={e => e.stopPropagation()}
        >
          {/* Search Header */}
          <div
            className="wildcard-picker-search-container"
            onMouseDown={e => e.stopPropagation()}
          >
            <Search size={14} className="wildcard-picker-search-icon" aria-hidden="true" />
            <input
              ref={inputRef}
              type="text"
              className="wildcard-picker-search-input"
              placeholder="Search wildcards..."
              value={query}
              onChange={e => setQuery(e.target.value)}
              onKeyDown={handleKeyDown}
              onMouseDown={e => e.stopPropagation()}
              aria-label="Search wildcards"
              autoComplete="off"
              spellCheck={false}
            />
            {query.length > 0 && (
              <button
                type="button"
                className="wildcard-picker-clear-btn"
                onClick={e => {
                  e.stopPropagation();
                  setQuery('');
                  inputRef.current?.focus();
                }}
                onMouseDown={e => e.stopPropagation()}
                title="Clear query"
                aria-label="Clear query"
              >
                <X size={13} />
              </button>
            )}
          </div>

          {/* List of items */}
          <div
            ref={listRef}
            className="wildcard-picker-list"
            onMouseDown={e => e.stopPropagation()}
          >
            {displayedWildcards.map((wildcard, idx) => {
              const isSelected =
                value === wildcard ||
                value === `__${wildcard}__` ||
                value?.replace(/^__+|__+$/g, '') === wildcard;
              const isHighlighted = highlightedIndex === idx;

              return (
                <div
                  key={wildcard}
                  data-index={idx}
                  className={`wildcard-picker-item ${
                    isHighlighted ? 'is-highlighted' : ''
                  } ${isSelected ? 'is-selected' : ''}`}
                  onClick={e => {
                    e.stopPropagation();
                    handlePick(wildcard);
                  }}
                  onMouseEnter={() => setHighlightedIndex(idx)}
                  onMouseDown={e => e.stopPropagation()}
                  role="option"
                  aria-selected={isSelected}
                >
                  <span className="wildcard-picker-item-text">
                    {renderHighlightedWildcard(wildcard, trimmedQuery)}
                  </span>
                  {isSelected && (
                    <Check
                      size={13}
                      className="wildcard-picker-check-icon"
                      aria-hidden="true"
                    />
                  )}
                </div>
              );
            })}

            {/* Custom value option */}
            {showCustomOption && (
              <div
                data-index={displayedWildcards.length}
                className={`wildcard-picker-item wildcard-picker-item-custom ${
                  highlightedIndex === displayedWildcards.length ? 'is-highlighted' : ''
                }`}
                onClick={e => {
                  e.stopPropagation();
                  handlePick(cleanCustomValue);
                }}
                onMouseEnter={() => setHighlightedIndex(displayedWildcards.length)}
                onMouseDown={e => e.stopPropagation()}
                role="option"
                aria-selected={highlightedIndex === displayedWildcards.length}
              >
                <div className="wildcard-picker-custom-content">
                  <Plus size={13} className="wildcard-picker-custom-icon" />
                  <span>
                    Use custom: <strong>__{cleanCustomValue}__</strong>
                  </span>
                </div>
              </div>
            )}

            {/* Empty state */}
            {displayedWildcards.length === 0 && !showCustomOption && (
              <div
                className="wildcard-picker-empty"
                onMouseDown={e => e.stopPropagation()}
              >
                No matching wildcards
              </div>
            )}
          </div>

          {/* Footer */}
          <div
            className="wildcard-picker-footer"
            onMouseDown={e => e.stopPropagation()}
          >
            <span className="wildcard-picker-footer-count">
              {getFooterMatchCount()}
            </span>
            <span className="wildcard-picker-footer-hint">
              ↑↓ to navigate, ↵ to pick
            </span>
          </div>
        </div>
      )}
    </div>
  );
};
