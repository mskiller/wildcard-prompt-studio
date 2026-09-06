import React, { useState, useRef, useEffect, useMemo, useCallback } from 'react';
import { ZoomIn, ZoomOut, Maximize2, RefreshCw, AlertTriangle } from 'lucide-react';
import './VisualASTCanvas.css';

export interface ASTCanvasNodeData {
  id: string;
  type: 'root' | 'text' | 'wildcard' | 'choice' | 'variable';
  x: number;
  y: number;
  title: string;
  value: string;
  options?: Array<{ id: string; text: string; weight: number }>;
  outputs: string[];
}

export interface VisualASTCanvasProps {
  nodes: ASTCanvasNodeData[];
  onNodesChange: (nodes: ASTCanvasNodeData[]) => void;
  onNodeSelect?: (nodeId: string) => void;
  selectedNodeId?: string | null;
  onAutoLayout?: () => void;
  hasCycle?: boolean;
  availableWildcards?: string[];
  onUpdateNode?: (nodeId: string, updates: Partial<ASTCanvasNodeData>) => void;
}

const TYPE_PILL_LABELS: Record<ASTCanvasNodeData['type'], string> = {
  root: 'ROOT',
  text: 'TEXT',
  wildcard: 'WILDCARD',
  choice: 'CHOICE',
  variable: 'VAR'
};

const NODE_WIDTH = 240;
const PORT_Y_OFFSET = 48;

export const VisualASTCanvas: React.FC<VisualASTCanvasProps> = ({
  nodes,
  onNodesChange,
  onNodeSelect,
  selectedNodeId = null,
  onAutoLayout,
  hasCycle = false,
  availableWildcards = [],
  onUpdateNode
}) => {
  const [zoom, setZoom] = useState<number>(1);
  const [pan, setPan] = useState<{ x: number; y: number }>({ x: 40, y: 40 });
  const [isPanning, setIsPanning] = useState<boolean>(false);
  const [draggedNodeId, setDraggedNodeId] = useState<string | null>(null);

  const containerRef = useRef<HTMLDivElement>(null);
  const nodesRef = useRef<ASTCanvasNodeData[]>(nodes);
  nodesRef.current = nodes;

  const dragStartRef = useRef<{
    mouseX: number;
    mouseY: number;
    initialNodeX: number;
    initialNodeY: number;
  }>({ mouseX: 0, mouseY: 0, initialNodeX: 0, initialNodeY: 0 });

  const panStartRef = useRef<{
    mouseX: number;
    mouseY: number;
    panX: number;
    panY: number;
  }>({ mouseX: 0, mouseY: 0, panX: 40, panY: 40 });

  // Map for fast node coordinate lookup
  const nodeMap = useMemo(() => {
    const map = new Map<string, ASTCanvasNodeData>();
    nodes.forEach(n => map.set(n.id, n));
    return map;
  }, [nodes]);

  // Handle wheel zoom clamped between 0.3x and 2.5x with passive: false
  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    const handleWheel = (e: WheelEvent) => {
      e.preventDefault();
      const zoomFactor = e.deltaY < 0 ? 1.1 : 0.9;
      setZoom(prev => {
        const next = Math.min(2.5, Math.max(0.3, prev * zoomFactor));
        return Math.round(next * 100) / 100;
      });
    };

    container.addEventListener('wheel', handleWheel, { passive: false });
    return () => {
      container.removeEventListener('wheel', handleWheel);
    };
  }, []);

  // Window-level mousemove and mouseup handlers for smooth dragging & panning
  useEffect(() => {
    const handleWindowMouseMove = (e: MouseEvent) => {
      if (isPanning) {
        const dx = e.clientX - panStartRef.current.mouseX;
        const dy = e.clientY - panStartRef.current.mouseY;
        setPan({
          x: panStartRef.current.panX + dx,
          y: panStartRef.current.panY + dy
        });
      } else if (draggedNodeId) {
        const dx = (e.clientX - dragStartRef.current.mouseX) / zoom;
        const dy = (e.clientY - dragStartRef.current.mouseY) / zoom;
        const updated = nodesRef.current.map(node =>
          node.id === draggedNodeId
            ? {
                ...node,
                x: Math.round(dragStartRef.current.initialNodeX + dx),
                y: Math.round(dragStartRef.current.initialNodeY + dy)
              }
            : node
        );
        onNodesChange(updated);
      }
    };

    const handleWindowMouseUp = () => {
      if (isPanning) setIsPanning(false);
      if (draggedNodeId) setDraggedNodeId(null);
    };

    if (isPanning || draggedNodeId) {
      window.addEventListener('mousemove', handleWindowMouseMove);
      window.addEventListener('mouseup', handleWindowMouseUp);
    }

    return () => {
      window.removeEventListener('mousemove', handleWindowMouseMove);
      window.removeEventListener('mouseup', handleWindowMouseUp);
    };
  }, [isPanning, draggedNodeId, zoom, onNodesChange]);

  // Canvas background mousedown (pan)
  const handleCanvasMouseDown = useCallback((e: React.MouseEvent) => {
    if (e.button !== 0) return;
    if ((e.target as HTMLElement).closest('.canvas-node')) return;
    if ((e.target as HTMLElement).closest('.canvas-control-toolbar')) return;

    setIsPanning(true);
    panStartRef.current = {
      mouseX: e.clientX,
      mouseY: e.clientY,
      panX: pan.x,
      panY: pan.y
    };
  }, [pan]);

  // Node mousedown (drag & select)
  const handleNodeMouseDown = useCallback((e: React.MouseEvent, node: ASTCanvasNodeData) => {
    if (e.button !== 0) return;
    e.stopPropagation();
    onNodeSelect?.(node.id);
    setDraggedNodeId(node.id);
    dragStartRef.current = {
      mouseX: e.clientX,
      mouseY: e.clientY,
      initialNodeX: node.x,
      initialNodeY: node.y
    };
  }, [onNodeSelect]);

  // Zoom controls
  const handleZoomIn = () => {
    setZoom(z => Math.min(2.5, Math.round((z + 0.15) * 100) / 100));
  };

  const handleZoomOut = () => {
    setZoom(z => Math.max(0.3, Math.round((z - 0.15) * 100) / 100));
  };

  const handleResetView = () => {
    setZoom(1);
    setPan({ x: 40, y: 40 });
  };

  // Render SVG cubic bezier connection curves
  const renderConnections = () => {
    const curves: JSX.Element[] = [];

    nodes.forEach(source => {
      if (!source.outputs || source.outputs.length === 0) return;

      source.outputs.forEach(targetId => {
        const target = nodeMap.get(targetId);
        if (!target) return;

        const startX = source.x + NODE_WIDTH;
        const startY = source.y + PORT_Y_OFFSET;
        const endX = target.x;
        const endY = target.y + PORT_Y_OFFSET;

        const isBackward = endX <= startX;
        const isCycleEdge = hasCycle || isBackward;

        let d: string;
        if (isBackward) {
          // Backward / loop-back curve
          const loopOffset = Math.max(50, Math.abs(endX - startX) * 0.4);
          const dyOffset = startY >= endY ? -60 : 60;
          const cx1 = startX + loopOffset;
          const cy1 = startY + dyOffset;
          const cx2 = endX - loopOffset;
          const cy2 = endY + dyOffset;
          d = `M ${startX} ${startY} C ${cx1} ${cy1}, ${cx2} ${cy2}, ${endX} ${endY}`;
        } else {
          // Smooth forward cubic bezier curve
          const dx = Math.max(40, (endX - startX) * 0.5);
          const cx1 = startX + dx;
          const cy1 = startY;
          const cx2 = endX - dx;
          const cy2 = endY;
          d = `M ${startX} ${startY} C ${cx1} ${cy1}, ${cx2} ${cy2}, ${endX} ${endY}`;
        }

        curves.push(
          <path
            key={`${source.id}->${targetId}`}
            d={d}
            className={`canvas-bezier-cable ${isCycleEdge ? 'cable-cycle-warning' : ''}`}
            markerEnd={isCycleEdge ? 'url(#cycleArrow)' : 'url(#cableArrow)'}
          />
        );
      });
    });

    return curves;
  };

  return (
    <div
      className="visual-ast-canvas-container"
      ref={containerRef}
      onMouseDown={handleCanvasMouseDown}
      style={{
        backgroundPosition: `${pan.x}px ${pan.y}px`,
        backgroundSize: `${24 * zoom}px ${24 * zoom}px`
      }}
    >
      {/* Control Toolbar */}
      <div className="canvas-control-toolbar">
        <button
          type="button"
          className="canvas-tool-btn"
          onClick={handleZoomIn}
          title="Zoom In"
        >
          <ZoomIn size={15} />
        </button>
        <span className="canvas-zoom-badge">{Math.round(zoom * 100)}%</span>
        <button
          type="button"
          className="canvas-tool-btn"
          onClick={handleZoomOut}
          title="Zoom Out"
        >
          <ZoomOut size={15} />
        </button>
        <button
          type="button"
          className="canvas-tool-btn"
          onClick={handleResetView}
          title="Reset View (100%)"
        >
          <Maximize2 size={15} />
        </button>

        {onAutoLayout && (
          <button
            type="button"
            className="canvas-tool-btn primary"
            onClick={onAutoLayout}
            title="Auto-Arrange Layout"
          >
            <RefreshCw size={14} />
            <span>Auto Layout</span>
          </button>
        )}

        {hasCycle && (
          <span className="canvas-cycle-alert" title="Circular wildcard recursion detected!">
            <AlertTriangle size={14} /> Loop Detected
          </span>
        )}
      </div>

      {/* Cycle Warning Banner */}
      {hasCycle && (
        <div className="canvas-cycle-warning-banner" role="alert">
          <AlertTriangle size={16} className="cycle-banner-icon" />
          <span className="cycle-banner-text">
            <strong>Circular Loop Detected:</strong> Wildcard recursion graph contains cyclic dependencies.
          </span>
        </div>
      )}

      {/* Interactive Canvas Stage */}
      <div
        className="canvas-stage"
        style={{
          transform: `translate(${pan.x}px, ${pan.y}px) scale(${zoom})`,
          transformOrigin: '0 0'
        }}
      >
        {/* SVG Bezier Cable Layer */}
        <svg className="canvas-svg-layer">
          <defs>
            <linearGradient id="cableGrad" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="#818cf8" />
              <stop offset="100%" stopColor="#c084fc" />
            </linearGradient>
            <filter id="cableGlow" x="-20%" y="-20%" width="140%" height="140%">
              <feGaussianBlur stdDeviation="3" result="blur" />
              <feMerge>
                <feMergeNode in="blur" />
                <feMergeNode in="SourceGraphic" />
              </feMerge>
            </filter>
            <marker
              id="cableArrow"
              markerWidth="8"
              markerHeight="8"
              refX="7"
              refY="4"
              orient="auto"
            >
              <polygon points="0 1, 7 4, 0 7" fill="#818cf8" />
            </marker>
            <marker
              id="cycleArrow"
              markerWidth="8"
              markerHeight="8"
              refX="7"
              refY="4"
              orient="auto"
            >
              <polygon points="0 1, 7 4, 0 7" fill="#ef4444" />
            </marker>
          </defs>
          {renderConnections()}
        </svg>

        {/* Node Cards */}
        {nodes.map(node => {
          const isSelected = selectedNodeId === node.id;
          const isDragging = draggedNodeId === node.id;

          return (
            <div
              key={node.id}
              className={`canvas-node canvas-node-${node.type} ${isSelected ? 'selected' : ''} ${isDragging ? 'is-dragging' : ''}`}
              style={{ left: `${node.x}px`, top: `${node.y}px` }}
              onMouseDown={e => handleNodeMouseDown(e, node)}
            >
              <div className="canvas-node-port port-in" title="Input Port" />

              <div className="canvas-node-header">
                <span className="node-type-pill">
                  {TYPE_PILL_LABELS[node.type] || node.type.toUpperCase()}
                </span>
                <span className="node-title" title={node.title}>{node.title}</span>
              </div>

              <div className="canvas-node-body">
                {node.type === 'choice' && node.options && node.options.length > 0 ? (
                  <div className="choice-options-summary">
                    {node.options.map(opt => {
                      const hasWildcard = opt.text.includes('__');
                      return (
                        <div
                          key={opt.id}
                          className={`choice-summary-pill ${hasWildcard ? 'has-wildcard' : ''}`}
                          title={`${opt.weight}x ${opt.text}${hasWildcard ? ' (contains wildcards)' : ''}`}
                        >
                          <span className="opt-weight">{opt.weight}×</span>
                          <span className="opt-text">{opt.text}</span>
                        </div>
                      );
                    })}
                  </div>
                ) : node.type === 'wildcard' ? (
                  <div className="canvas-wildcard-preview-box" onMouseDown={e => e.stopPropagation()}>
                    {availableWildcards && availableWildcards.length > 0 ? (
                      <select
                        className="canvas-node-wildcard-select"
                        value={availableWildcards.includes(node.value) ? node.value : ''}
                        onChange={(e) => {
                          const val = e.target.value;
                          if (val && onUpdateNode) {
                            onUpdateNode(node.id, { value: val, title: val });
                          }
                        }}
                        title={`Select wildcard (${availableWildcards.length} available)`}
                        aria-label="Select wildcard"
                      >
                        <option value="" disabled>
                          -- Choose Wildcard ({availableWildcards.length}) --
                        </option>
                        {availableWildcards.map(w => (
                          <option key={w} value={w}>
                            __{w}__
                          </option>
                        ))}
                        {node.value && !availableWildcards.includes(node.value) && (
                          <option value={node.value}>{node.value} (custom)</option>
                        )}
                      </select>
                    ) : (
                      <div className="node-value-preview" title={node.value}>
                        __{node.value || 'wildcard_name'}__
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="node-value-preview" title={node.value}>
                    {node.value || <span className="node-value-empty">(empty)</span>}
                  </div>
                )}
              </div>

              <div className="canvas-node-port port-out" title="Output Port" />
            </div>
          );
        })}

        {nodes.length === 0 && (
          <div className="canvas-empty-state">
            <p>No AST nodes parsed yet. Type a wildcard prompt to generate the graph.</p>
          </div>
        )}
      </div>
    </div>
  );
};
