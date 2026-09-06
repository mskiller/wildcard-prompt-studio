import React, { useState, useEffect, useRef, useCallback, useMemo } from 'react';
import {
  fetchMatrixSlice,
  MatrixPermutationItem,
  serializeASTToGraph,
  analyzeMatrixHeatmap,
  executeComfyUISweep,
  getWildcards,
  getGenerationOptions,
  syncRecentComfyOutputs,
  SweepResultItem,
  GenerationOptionsData
} from '../../api';
import {
  Network,
  Flame,
  Play,
  Zap,
  Layers,
  Sparkles,
  ChevronRight,
  ChevronDown,
  ChevronLeft,
  Activity,
  Plus,
  Trash2,
  Copy,
  Check,
  X,
  Sliders,
  GitFork,
  RefreshCw,
  Eye,
  Download,
  Image as ImageIcon,
  AlertTriangle
} from 'lucide-react';
import { VisualASTCanvas } from './VisualASTCanvas';
import { useASTGraphSync } from './useASTGraphSync';
import { CanvasChoiceNode } from './nodes/CanvasChoiceNode';
import { CanvasWildcardNode } from './nodes/CanvasWildcardNode';
import { CanvasTextNode } from './nodes/CanvasTextNode';
import { CanvasVarNode } from './nodes/CanvasVarNode';
import { WildcardSearchPicker } from './WildcardSearchPicker';
import { useAppStore } from '../../store/useAppStore';
import './WildcardMatrixPanel.css';

interface ASTNodeProps {
  node: any;
  depth?: number;
}

const ASTTreeNodeView: React.FC<ASTNodeProps> = ({ node, depth = 0 }) => {
  const [collapsed, setCollapsed] = useState<boolean>(false);

  if (!node) return null;

  const nodeType = node.type || node.node_type || 'UnknownNode';

  const getNodeBadgeClass = (type: string) => {
    switch (type) {
      case 'root':
      case 'RootNode': return 'badge-root';
      case 'choice':
      case 'ChoiceNode': return 'badge-choice';
      case 'wildcard':
      case 'WildcardNode': return 'badge-wildcard';
      case 'text':
      case 'TextNode': return 'badge-text';
      case 'variable':
      case 'VarAssignmentNode':
      case 'VarRefNode': return 'badge-var';
      case 'MacroNode': return 'badge-macro';
      default: return 'badge-default';
    }
  };

  const renderContent = () => {
    if (nodeType === 'TextNode' || nodeType === 'text') {
      return <span className="tree-text-content">"{node.text || node.value || ''}"</span>;
    }
    if (nodeType === 'WildcardNode' || nodeType === 'wildcard') {
      return <span className="tree-wildcard-name">__{node.name || node.value || ''}__</span>;
    }
    if (nodeType === 'VarAssignmentNode' || nodeType === 'VarRefNode' || nodeType === 'variable') {
      return <span className="tree-var-name">${node.var_name || node.title || ''}</span>;
    }
    if (nodeType === 'MacroNode') {
      return <span className="tree-macro-name">@{node.macro_name}({Array.isArray(node.args) ? node.args.join(', ') : ''})</span>;
    }
    return null;
  };

  const children: any[] = Array.isArray(node.children) ? node.children : [];
  const options: any[] = Array.isArray(node.options) ? node.options : [];
  const hasChildren = children.length > 0 || options.length > 0 || Boolean(node.value_node);

  return (
    <div className="ast-tree-node" style={{ marginLeft: `${depth * 14}px` }}>
      <div className="tree-node-header" onClick={() => hasChildren && setCollapsed(!collapsed)}>
        {hasChildren ? (
          collapsed ? <ChevronRight size={14} /> : <ChevronDown size={14} />
        ) : (
          <span className="tree-dot">•</span>
        )}
        <span className={`tree-type-badge ${getNodeBadgeClass(nodeType)}`}>{nodeType}</span>
        {renderContent()}
      </div>

      {!collapsed && (
        <div className="tree-node-children">
          {children.map((child, idx) => (
            <ASTTreeNodeView key={idx} node={child} depth={depth + 1} />
          ))}
          {options.map((opt, idx) => (
            <div key={idx} className="ast-choice-option" style={{ marginLeft: `${(depth + 1) * 14}px` }}>
              <span className="option-weight">Weight: {opt.weight ?? 1.0}</span>
              <ASTTreeNodeView node={opt.content || opt} depth={depth + 1} />
            </div>
          ))}
          {node.value_node && (
            <ASTTreeNodeView node={node.value_node} depth={depth + 1} />
          )}
        </div>
      )}
    </div>
  );
};

export const WildcardMatrixPanel: React.FC = () => {
  const { matrixPrompt: storedPrompt, setMatrixPrompt, activeDocument, discordWebhookUrl, syncDiscordConfig } = useAppStore();
  const [prompt, setPromptLocal] = useState<string>(storedPrompt);
  const setPrompt = (val: string) => { setPromptLocal(val); setMatrixPrompt(val); };

  // Sync Discord configuration from backend on mount
  useEffect(() => {
    if (syncDiscordConfig) {
      syncDiscordConfig();
    }
  }, [syncDiscordConfig]);
  const [sliceItems, setSliceItems] = useState<MatrixPermutationItem[]>([]);
  const [totalCount, setTotalCount] = useState<number>(0);
  const [currentOffset, setCurrentOffset] = useState<number>(0);
  const [pageSize, setPageSize] = useState<number>(250);
  const [isSampleMode, setIsSampleMode] = useState<boolean>(false);
  const [sampleCount, setSampleCount] = useState<number>(100);
  const [sampleCountInput, setSampleCountInput] = useState<string>('100');
  const [jumpIndexInput, setJumpIndexInput] = useState<string>('');
  const [pageInput, setPageInput] = useState<string>('1');
  const selectedPromptsMap = useRef<Map<number, string>>(new Map());
  const latestRequestIdRef = useRef<number>(0);

  // Derive combinations from sliceItems
  const combinations = useMemo(() => sliceItems.map((item) => item.prompt), [sliceItems]);

  const totalPages = Math.max(1, Math.ceil(totalCount / pageSize));
  const currentPage = Math.floor(currentOffset / pageSize) + 1;
  const [graphTree, setGraphTree] = useState<any | null>(null);
  const [heatmapScores, setHeatmapScores] = useState<any | null>(null);
  const [workspaceMode, setWorkspaceMode] = useState<'split' | 'canvas' | 'grid' | 'heatmap' | 'tree' | 'results'>('split');
  const [loading, setLoading] = useState<boolean>(false);
  const [status, setStatus] = useState<string>('');
  const [copiedIdx, setCopiedIdx] = useState<number | null>(null);
  const [availableWildcards, setAvailableWildcards] = useState<string[]>([]);

  // Batch Sweep Results & Lightbox
  const [sweepResults, setSweepResults] = useState<SweepResultItem[]>([]);
  const [isSyncingSweep, setIsSyncingSweep] = useState<boolean>(false);
  const [lightboxIndex, setLightboxIndex] = useState<number | null>(null);

  const handleSyncSweepOutputs = useCallback(async (manual: boolean = false) => {
    setIsSyncingSweep(true);
    try {
      const res = await syncRecentComfyOutputs('MatrixSweep', 50);
      if (res && Array.isArray(res.items)) {
        setSweepResults(res.items);
        if (manual) {
          setStatus(`Synced ${res.items.length} generated images from ComfyUI.`);
        }
      }
    } catch (e: any) {
      if (manual) setStatus(`Sync error: ${e.message}`);
    } finally {
      setIsSyncingSweep(false);
    }
  }, []);

  // Initial load of past sweep images from ComfyUI / DB
  useEffect(() => {
    handleSyncSweepOutputs(false);
  }, [handleSyncSweepOutputs]);

  // Keyboard navigation for enlarged lightbox
  useEffect(() => {
    if (lightboxIndex === null) return;
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        setLightboxIndex(null);
      } else if (e.key === 'ArrowLeft') {
        setLightboxIndex((prev) => (prev !== null && prev > 0 ? prev - 1 : prev));
      } else if (e.key === 'ArrowRight') {
        setLightboxIndex((prev) => (prev !== null && prev < sweepResults.length - 1 ? prev + 1 : prev));
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [lightboxIndex, sweepResults.length]);

  // ComfyUI Batch Parameter Bar State (Configured with Krea2 / Live ComfyUI Defaults)
  const [model, setModel] = useState<string>('Mklan_Kea2_V1.safetensors');
  const [clip, setClip] = useState<string>('qwen3-vl-4b-heretic.safetensors');
  const [vae, setVae] = useState<string>('qwen_image_vae.safetensors');
  const [samplerName, setSamplerName] = useState<string>('er_sde');
  const [scheduler, setScheduler] = useState<string>('beta');
  const [steps, setSteps] = useState<number>(10);
  const [cfg, setCfg] = useState<number>(1.0);
  const [seedStrategy, setSeedStrategy] = useState<'fixed' | 'sequential' | 'random'>('sequential');
  const [baseSeed, setBaseSeed] = useState<number>(42);
  const [expandWildcards, setExpandWildcards] = useState<boolean>(true);
  const [sendToDiscord, setSendToDiscord] = useState<boolean>(false);

  // Resolution controls (Default: 896x1152 as requested)
  const [width, setWidth] = useState<number>(896);
  const [height, setHeight] = useState<number>(1152);

  // Queue mode, limits & manual permutation selection
  const [queueMode, setQueueMode] = useState<'view' | 'range' | 'sample' | 'all'>('view');
  const [queueRangeStart, setQueueRangeStart] = useState<number>(1);
  const [queueRangeStep, setQueueRangeStep] = useState<number>(1);
  const [queueRangeCount, setQueueRangeCount] = useState<number>(10);
  const [queueSampleCount, setQueueSampleCount] = useState<number>(10);
  const [maxPromptsToQueue, setMaxPromptsToQueue] = useState<number>(10);
  const [selectedIndices, setSelectedIndices] = useState<Set<number>>(new Set());

  const effectiveRangeCount = useMemo(() => {
    if (totalCount <= 0 || queueRangeStart > totalCount) return 0;
    if (queueRangeStep <= 1) {
      return Math.min(queueRangeCount, totalCount - queueRangeStart + 1);
    }
    const maxAvailable = Math.floor((totalCount - queueRangeStart) / queueRangeStep) + 1;
    return Math.max(1, Math.min(queueRangeCount, maxAvailable));
  }, [totalCount, queueRangeStart, queueRangeCount, queueRangeStep]);

  const rangeEnd = useMemo(() => {
    if (totalCount <= 0) return 0;
    if (queueRangeStep <= 1) {
      return Math.min(queueRangeStart + queueRangeCount - 1, totalCount);
    }
    const lastIndex = queueRangeStart + (effectiveRangeCount - 1) * queueRangeStep;
    return Math.min(lastIndex, totalCount);
  }, [totalCount, queueRangeStart, queueRangeStep, effectiveRangeCount]);

  const handleToggleSelectPrompt = (item: MatrixPermutationItem) => {
    setSelectedIndices((prev) => {
      const next = new Set(prev);
      if (next.has(item.index)) {
        next.delete(item.index);
        selectedPromptsMap.current.delete(item.index);
      } else {
        next.add(item.index);
        selectedPromptsMap.current.set(item.index, item.prompt);
      }
      return next;
    });
  };

  const handleSelectFirstN = (n: number) => {
    const count = Math.min(n, sliceItems.length);
    const newSet = new Set(selectedIndices);
    for (let i = 0; i < count; i++) {
      const it = sliceItems[i];
      newSet.add(it.index);
      selectedPromptsMap.current.set(it.index, it.prompt);
    }
    setSelectedIndices(newSet);
  };

  const handleSelectRandomN = (n: number) => {
    const count = Math.min(n, sliceItems.length);
    const indices = Array.from({ length: sliceItems.length }, (_, i) => i);
    for (let i = indices.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [indices[i], indices[j]] = [indices[j], indices[i]];
    }
    const newSet = new Set(selectedIndices);
    for (let i = 0; i < count; i++) {
      const it = sliceItems[indices[i]];
      newSet.add(it.index);
      selectedPromptsMap.current.set(it.index, it.prompt);
    }
    setSelectedIndices(newSet);
  };

  const handleSelectAllShown = () => {
    const newSet = new Set(selectedIndices);
    for (const it of sliceItems) {
      newSet.add(it.index);
      selectedPromptsMap.current.set(it.index, it.prompt);
    }
    setSelectedIndices(newSet);
  };

  const handleClearSelection = () => {
    setSelectedIndices(new Set());
    selectedPromptsMap.current.clear();
  };

  // Live ComfyUI Availabilities
  const [comfyOptions, setComfyOptions] = useState<GenerationOptionsData>({
    models: ['Mklan_Kea2_V1.safetensors', 'Mklan_Krea28v1.safetensors'],
    clips: ['qwen3-vl-4b-heretic.safetensors'],
    vaes: ['qwen_image_vae.safetensors'],
    samplers: ['er_sde', 'euler', 'euler_ancestral', 'dpmpp_2m_sde'],
    schedulers: ['beta', 'normal', 'karras'],
    connected: false
  });
  const [isRefreshingOptions, setIsRefreshingOptions] = useState<boolean>(false);

  const fetchComfyAvailabilities = useCallback(async () => {
    setIsRefreshingOptions(true);
    try {
      const opts = await getGenerationOptions();
      if (opts) {
        setComfyOptions({
          models: opts.models || [],
          clips: opts.clips || [],
          vaes: opts.vaes || [],
          samplers: opts.samplers || [],
          schedulers: opts.schedulers || [],
          connected: !!opts.connected
        });
        if (opts.models?.length) {
          const matchModel = opts.models.find((m: string) =>
            m.toLowerCase().includes('kea2') || m.toLowerCase().includes('krea28') || m.toLowerCase().includes('krea2')
          );
          if (matchModel) setModel(matchModel);
        }
        if (opts.clips?.length) {
          const matchClip = opts.clips.find((c: string) =>
            c.toLowerCase().includes('qwen3-vl-4b-heretic') || c.toLowerCase().includes('heretic')
          );
          if (matchClip) setClip(matchClip);
        }
        if (opts.vaes?.length) {
          const matchVae = opts.vaes.find((v: string) => v.toLowerCase().includes('qwen_image_vae'));
          if (matchVae) setVae(matchVae);
        }
        if (opts.samplers?.length) {
          const matchSampler = opts.samplers.find((s: string) => s.toLowerCase() === 'er_sde');
          if (matchSampler) setSamplerName(matchSampler);
        }
        if (opts.schedulers?.length) {
          const matchSched = opts.schedulers.find((sch: string) => sch.toLowerCase() === 'beta');
          if (matchSched) setScheduler(matchSched);
        }
      }
    } catch {
      // Keep existing defaults
    } finally {
      setIsRefreshingOptions(false);
    }
  }, []);

  useEffect(() => {
    fetchComfyAvailabilities();
  }, [fetchComfyAvailabilities]);

  const expandDebounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const sweepPollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const loadSlice = useCallback(
    async (
      offset: number = 0,
      limit: number = pageSize,
      sampleSize?: number,
      promptOverride?: string,
      expandWcOverride?: boolean
    ) => {
      const targetPrompt = promptOverride !== undefined ? promptOverride : prompt;
      const targetExpandWc = expandWcOverride !== undefined ? expandWcOverride : expandWildcards;

      const requestId = ++latestRequestIdRef.current;

      if (!targetPrompt.trim()) {
        setSliceItems([]);
        setTotalCount(0);
        setCurrentOffset(0);
        setIsSampleMode(false);
        setPageInput('1');
        return;
      }

      setLoading(true);
      try {
        const res = await fetchMatrixSlice({
          prompt: targetPrompt,
          offset,
          limit,
          expandWildcards: targetExpandWc,
          sampleSize,
        });

        if (requestId !== latestRequestIdRef.current) return;

        setSliceItems(res.items);
        setTotalCount(res.total_count);
        setCurrentOffset(res.offset);
        setIsSampleMode(res.is_sample);

        const effectiveLimit = limit || pageSize || 250;
        const computedPage = Math.floor(res.offset / effectiveLimit) + 1;
        setPageInput(String(computedPage));

        if (res.is_sample) {
          setStatus(`Sampled ${res.items.length} random variants (out of ${res.total_count.toLocaleString()} total).`);
        } else {
          const start = res.total_count > 0 ? res.offset + 1 : 0;
          const end = Math.min(res.offset + res.items.length, res.total_count);
          setStatus(
            `Generated ${res.total_count.toLocaleString()} permutations (viewing #${start.toLocaleString()} - #${end.toLocaleString()} of ${res.total_count.toLocaleString()}).`
          );
        }
      } catch (e: any) {
        if (requestId !== latestRequestIdRef.current) return;
        setStatus(`Error loading permutations: ${e.message}`);
      } finally {
        if (requestId === latestRequestIdRef.current) {
          setLoading(false);
        }
      }
    },
    [prompt, pageSize, expandWildcards]
  );

  const handleFirstPage = () => {
    if (currentPage > 1) {
      loadSlice(0, pageSize);
    }
  };

  const handlePrevPage = () => {
    if (currentPage > 1) {
      const newOffset = Math.max(0, currentOffset - pageSize);
      loadSlice(newOffset, pageSize);
    }
  };

  const handleNextPage = () => {
    if (currentPage < totalPages) {
      const targetOffset = Math.min(currentOffset + pageSize, (totalPages - 1) * pageSize);
      loadSlice(targetOffset, pageSize);
    }
  };

  const handleLastPage = () => {
    if (currentPage < totalPages) {
      const lastOffset = Math.max(0, (totalPages - 1) * pageSize);
      loadSlice(lastOffset, pageSize);
    }
  };

  const handlePageInputSubmit = (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    const parsed = parseInt(pageInput.trim(), 10);
    if (isNaN(parsed)) {
      setPageInput(String(currentPage));
      return;
    }
    const clampedPage = Math.max(1, Math.min(parsed, totalPages));
    setPageInput(String(clampedPage));
    if (clampedPage === currentPage && !isSampleMode) return;
    const targetOffset = (clampedPage - 1) * pageSize;
    loadSlice(targetOffset, pageSize);
  };

  const handleJumpToIndexSubmit = (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!jumpIndexInput.trim()) return;
    const parsed = parseInt(jumpIndexInput.replace(/,/g, '').trim(), 10);
    if (isNaN(parsed)) return;
    if (totalCount <= 0) return;
    const targetOffset = Math.max(0, Math.min(parsed - 1, totalCount - 1));
    loadSlice(targetOffset, pageSize);
  };

  const handleSampleRandom = (count: number = sampleCount) => {
    loadSlice(0, pageSize, count);
  };

  const handleResetToSequential = () => {
    setIsSampleMode(false);
    loadSlice(currentOffset, pageSize);
  };

  const handlePageSizeChange = (newSize: number) => {
    setPageSize(newSize);
    loadSlice(0, newSize, undefined, prompt, expandWildcards);
  };

  const handleToggleExpandWildcards = (enabled: boolean) => {
    setExpandWildcards(enabled);
    loadSlice(0, pageSize, undefined, prompt, enabled);
  };

  // Debounced matrix expansion runner (unlimited permutations via slice)
  const triggerExpansion = useCallback(
    (promptToExpand: string, expandWc: boolean = expandWildcards) => {
      if (expandDebounceRef.current) {
        clearTimeout(expandDebounceRef.current);
      }
      handleClearSelection();
      if (!promptToExpand.trim()) {
        setSliceItems([]);
        setTotalCount(0);
        setCurrentOffset(0);
        setIsSampleMode(false);
        setPageInput('1');
        return;
      }
      expandDebounceRef.current = setTimeout(async () => {
        try {
          await loadSlice(0, pageSize, undefined, promptToExpand, expandWc);
        } catch {
          // Keep current status if syntax is mid-edit
        }
      }, 300);
    },
    [expandWildcards, pageSize, loadSlice]
  );

  // Bi-directional AST Graph Sync
  const {
    nodes,
    setNodes,
    selectedNodeId,
    setSelectedNodeId,
    hasCycle,
    isCompiling,
    updateNodeData,
    addNode,
    deleteNode,
    autoLayout,
    syncFromPrompt
  } = useASTGraphSync({
    initialPrompt: prompt,
    onPromptChange: (newPrompt) => {
      setPrompt(newPrompt);
      triggerExpansion(newPrompt, expandWildcards);
    }
  });

  const selectedNode = nodes.find((n) => n.id === selectedNodeId) || null;

  // Load available wildcards for inspector dropdown
  useEffect(() => {
    getWildcards()
      .then((data) => {
        if (Array.isArray(data)) {
          const names = data
            .map((w: any) => {
              const fn = typeof w === 'string' ? w : w.filename || w.name || '';
              return fn.replace(/\.txt$/i, '');
            })
            .filter(Boolean);
          setAvailableWildcards(names);
        }
      })
      .catch(() => {});
  }, []);

  // Trigger initial matrix expansion on mount
  useEffect(() => {
    triggerExpansion(prompt, expandWildcards);
  }, []);

  useEffect(() => {
    return () => {
      if (expandDebounceRef.current) {
        clearTimeout(expandDebounceRef.current);
      }
      if (sweepPollRef.current) {
        clearInterval(sweepPollRef.current);
      }
    };
  }, []);

  const handlePreview = async () => {
    handleClearSelection();
    setLoading(true);
    try {
      const [, resGraph, resHeatmap] = await Promise.all([
        loadSlice(0, pageSize, undefined, prompt, expandWildcards),
        serializeASTToGraph(prompt).catch(() => null),
        analyzeMatrixHeatmap(prompt, expandWildcards, 500).catch(() => null),
      ]);
      if (resGraph?.graph) {
        setGraphTree(resGraph.graph);
      }
      if (resHeatmap) {
        setHeatmapScores(resHeatmap);
      }
    } catch (e: any) {
      setStatus(`Error: ${e.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleExecuteBatchSweep = async () => {
    if (sliceItems.length === 0 && totalCount === 0) {
      setStatus('No permutations available to queue. Preview or edit template first.');
      return;
    }

    if (queueMode === 'range' && queueRangeStart > totalCount) {
      setStatus(`Range start #${queueRangeStart} exceeds total permutations (${totalCount.toLocaleString()}).`);
      return;
    }

    if (queueMode === 'all') {
      if (totalCount > 10000) {
        const confirmed = window.confirm(
          `Queueing ${totalCount.toLocaleString()} variants is very large and may take significant time. Consider using Range Slice or Random Sample mode instead. Do you want to continue?`
        );
        if (!confirmed) {
          return;
        }
      } else if (totalCount > 2000) {
        const confirmed = window.confirm(
          `Queueing ${totalCount.toLocaleString()} prompts will submit a large batch to ComfyUI. Are you sure you want to proceed?`
        );
        if (!confirmed) {
          return;
        }
      }
    }

    setLoading(true);
    try {
      let promptsToSend: string[] = [];
      let queueModeDesc = '';

      if (queueMode === 'range') {
        if (queueRangeStep <= 1) {
          setStatus(`Fetching range slice #${queueRangeStart}–#${rangeEnd}...`);
          const sliceRes = await fetchMatrixSlice({
            prompt,
            offset: Math.max(0, queueRangeStart - 1),
            limit: queueRangeCount,
            expandWildcards,
          });
          promptsToSend = sliceRes.items.map((it) => it.prompt);
          queueModeDesc = `${promptsToSend.length} variants from range #${queueRangeStart} to #${rangeEnd}`;
        } else {
          // Stepped range selection: calculate exact indices
          const targetIndices: number[] = [];
          for (let i = 0; i < queueRangeCount; i++) {
            const idx1Based = queueRangeStart + i * queueRangeStep;
            if (idx1Based > totalCount) break;
            targetIndices.push(idx1Based - 1); // 0-based for API
          }
          if (targetIndices.length === 0) {
            setStatus('No valid permutation indices in specified range/step.');
            setLoading(false);
            return;
          }
          setStatus(`Fetching ${targetIndices.length} stepped variants (step ${queueRangeStep}) from #${queueRangeStart} to #${rangeEnd}...`);
          const sliceRes = await fetchMatrixSlice({
            prompt,
            indices: targetIndices,
            expandWildcards,
          });
          promptsToSend = sliceRes.items.map((it) => it.prompt);
          queueModeDesc = `${promptsToSend.length} stepped variants (step ${queueRangeStep}) from #${queueRangeStart} to #${rangeEnd}`;
        }
      } else if (queueMode === 'sample') {
        setStatus(`Sampling ${queueSampleCount} random variants...`);
        const sampleRes = await fetchMatrixSlice({
          prompt,
          sampleSize: queueSampleCount,
          expandWildcards,
        });
        promptsToSend = sampleRes.items.map((it) => it.prompt);
        queueModeDesc = `${promptsToSend.length} random samples across ${totalCount.toLocaleString()} total`;
      } else if (queueMode === 'all') {
        setStatus(`Fetching all ${totalCount.toLocaleString()} variants...`);
        const BATCH_SIZE = 2000;
        const allPrompts: string[] = [];
        for (let offset = 0; offset < totalCount; offset += BATCH_SIZE) {
          const fetchLimit = Math.min(BATCH_SIZE, totalCount - offset);
          const allRes = await fetchMatrixSlice({
            prompt,
            offset,
            limit: fetchLimit,
            expandWildcards,
          });
          allPrompts.push(...allRes.items.map((it) => it.prompt));
          if (allRes.items.length < fetchLimit) break;
        }
        promptsToSend = allPrompts;
        queueModeDesc = `all ${promptsToSend.length} variants across ${totalCount.toLocaleString()} total`;
      } else {
        // queueMode === 'view'
        if (selectedIndices.size > 0) {
          promptsToSend = Array.from(selectedIndices)
            .sort((a, b) => a - b)
            .map((idx) => selectedPromptsMap.current.get(idx) || sliceItems.find((it) => it.index === idx)?.prompt)
            .filter((p): p is string => Boolean(p));
          queueModeDesc = `${promptsToSend.length} manually selected`;
        } else {
          promptsToSend = combinations.slice(0, maxPromptsToQueue);
          queueModeDesc = `${promptsToSend.length} (of ${totalCount.toLocaleString()})`;
        }
      }

      if (promptsToSend.length === 0) {
        setStatus('No prompts selected to queue.');
        return;
      }

      setStatus(`Queueing ${queueModeDesc} batch sweep jobs in ComfyUI (${width}x${height})...`);
      const res = await executeComfyUISweep({
        prompts: promptsToSend,
        seedStrategy,
        baseSeed,
        steps,
        cfg,
        samplerName,
        scheduler,
        model,
        clip,
        vae,
        width,
        height,
        sendToDiscord,
        discordWebhookUrl: sendToDiscord ? discordWebhookUrl : undefined,
      });
      const discordMsg = sendToDiscord ? ' (with live Discord delivery)' : '';
      setStatus(`Successfully queued ${res.queued_count} batch sweep jobs in ComfyUI (${width}x${height})${discordMsg}! Generating...`);

      // Poll periodically to stream completed images into the results space
      if (sweepPollRef.current) clearInterval(sweepPollRef.current);
      let pollCount = 0;
      sweepPollRef.current = setInterval(async () => {
        pollCount++;
        try {
          const syncRes = await syncRecentComfyOutputs('MatrixSweep', 50);
          if (syncRes && Array.isArray(syncRes.items)) {
            setSweepResults(syncRes.items);
          }
        } catch {
          // ignore transient errors during generation
        }
        if (pollCount >= 20) {
          if (sweepPollRef.current) {
            clearInterval(sweepPollRef.current);
            sweepPollRef.current = null;
          }
        }
      }, 3000);
    } catch (e: any) {
      setStatus(`Batch sweep error: ${e.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleAnalyzeGraphAndHeatmap = async () => {
    setLoading(true);
    try {
      const [resGraph, resHeatmap] = await Promise.all([
        serializeASTToGraph(prompt).catch(() => null),
        analyzeMatrixHeatmap(prompt, expandWildcards, 500).catch(() => null),
      ]);
      if (resGraph?.graph) setGraphTree(resGraph.graph);
      if (resHeatmap) setHeatmapScores(resHeatmap);
      setStatus('Graph structure and token heatmap analyzed.');
    } catch (e: any) {
      setStatus(`Analysis error: ${e.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleCopyPrompt = async (text: string, idx: number) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopiedIdx(idx);
      setTimeout(() => setCopiedIdx(null), 1800);
    } catch {
      // Fallback if clipboard permission is denied
    }
  };

  const getNodeBadgeClass = (type: string) => {
    switch (type) {
      case 'root':
      case 'RootNode': return 'badge-root';
      case 'choice':
      case 'ChoiceNode': return 'badge-choice';
      case 'wildcard':
      case 'WildcardNode': return 'badge-wildcard';
      case 'text':
      case 'TextNode': return 'badge-text';
      case 'variable':
      case 'VarAssignmentNode':
      case 'VarRefNode': return 'badge-var';
      case 'MacroNode': return 'badge-macro';
      default: return 'badge-default';
    }
  };

  // Helper for per-variation heatmap token score
  const getVariationTokenScore = (promptText: string) => {
    const tokens = promptText.split(',').filter((t) => t.trim().length > 0);
    const count = tokens.length;
    let heatClass = 'heat-low';
    if (count > 60) heatClass = 'heat-extreme';
    else if (count > 40) heatClass = 'heat-high';
    else if (count > 20) heatClass = 'heat-medium';
    return { count, heatClass };
  };

  // Node Inspector Drawer / Floating Card Renderer
  const renderNodeInspector = () => {
    if (!selectedNode) return null;

    return (
      <aside className="node-inspector-drawer">
        <div className="node-inspector-header">
          <div className="node-inspector-title-area">
            <span className={`tree-type-badge ${getNodeBadgeClass(selectedNode.type)}`}>
              {selectedNode.type.toUpperCase()}
            </span>
            <span className="node-inspector-title" title={selectedNode.title || selectedNode.id}>
              {selectedNode.title || selectedNode.id}
            </span>
          </div>
          <div className="node-inspector-actions">
            <button
              type="button"
              className="inspector-delete-btn"
              onClick={() => deleteNode(selectedNode.id)}
              title="Delete node from graph"
            >
              <Trash2 size={13} />
              <span>Delete Node</span>
            </button>
            <button
              type="button"
              className="inspector-close-btn"
              onClick={() => setSelectedNodeId(null)}
              title="Close inspector"
            >
              <X size={15} />
            </button>
          </div>
        </div>

        <div className="node-inspector-body">
          {selectedNode.type === 'text' && (
            <CanvasTextNode
              text={selectedNode.value}
              onChange={(text) => updateNodeData(selectedNode.id, { value: text })}
            />
          )}

          {selectedNode.type === 'wildcard' && (
            <CanvasWildcardNode
              name={selectedNode.value}
              availableWildcards={availableWildcards}
              onChange={(name) =>
                updateNodeData(selectedNode.id, { value: name, title: name || 'Wildcard' })
              }
            />
          )}

          {selectedNode.type === 'choice' && (
            <CanvasChoiceNode
              options={selectedNode.options || []}
              onChange={(options) =>
                updateNodeData(selectedNode.id, {
                  options,
                  value: `{${options.map((o) => (o.weight !== 1.0 ? `${o.weight}::${o.text}` : o.text)).join(' | ')}}`
                })
              }
            />
          )}

          {selectedNode.type === 'variable' && (
            <CanvasVarNode
              varName={selectedNode.title}
              value={selectedNode.value}
              onChange={(varName, val) =>
                updateNodeData(selectedNode.id, { title: varName, value: val })
              }
            />
          )}

          {selectedNode.type !== 'text' &&
            selectedNode.type !== 'wildcard' &&
            selectedNode.type !== 'choice' &&
            selectedNode.type !== 'variable' && (
              <CanvasTextNode
                text={selectedNode.value}
                onChange={(text) => updateNodeData(selectedNode.id, { value: text })}
              />
            )}
        </div>
      </aside>
    );
  };

  // ComfyUI Batch Parameter Bar Renderer
  const renderComfyUIBatchBar = () => (
    <div className="comfyui-batch-bar">
      <div className="batch-bar-title-row">
        <div className="batch-bar-title">
          <Sliders size={14} className="batch-bar-icon" />
          <span>ComfyUI Batch Parameters</span>
        </div>
        <div className="batch-bar-status-area">
          <span className={`batch-conn-indicator ${comfyOptions.connected ? 'online' : 'offline'}`}>
            <span className="conn-dot"></span>
            {comfyOptions.connected ? 'ComfyUI Online' : 'ComfyUI Offline'}
          </span>
          <button
            type="button"
            className="batch-refresh-btn"
            onClick={fetchComfyAvailabilities}
            disabled={isRefreshingOptions}
            title="Refresh models, CLIPs, VAEs, and samplers from ComfyUI"
          >
            <RefreshCw size={12} className={isRefreshingOptions ? 'spin-icon' : ''} />
          </button>
        </div>
      </div>

      <div className="batch-controls-row">
        {/* Model / UNET Selector */}
        <div className="batch-field">
          <label>Model / UNET</label>
          <select
            className="batch-input batch-select batch-select-wide"
            value={model}
            onChange={(e) => setModel(e.target.value)}
            title={model}
          >
            {!comfyOptions.models.includes(model) && (
              <option value={model}>{model}</option>
            )}
            {comfyOptions.models.map((m) => (
              <option key={m} value={m}>
                {m}
              </option>
            ))}
          </select>
        </div>

        {/* CLIP Selector */}
        <div className="batch-field">
          <label>CLIP</label>
          <select
            className="batch-input batch-select batch-select-wide"
            value={clip}
            onChange={(e) => setClip(e.target.value)}
            title={clip}
          >
            {!comfyOptions.clips?.includes(clip) && (
              <option value={clip}>{clip}</option>
            )}
            {(comfyOptions.clips || []).map((c) => (
              <option key={c} value={c}>
                {c}
              </option>
            ))}
          </select>
        </div>

        {/* VAE Selector */}
        <div className="batch-field">
          <label>VAE</label>
          <select
            className="batch-input batch-select batch-select-wide"
            value={vae}
            onChange={(e) => setVae(e.target.value)}
            title={vae}
          >
            {!comfyOptions.vaes?.includes(vae) && (
              <option value={vae}>{vae}</option>
            )}
            {(comfyOptions.vaes || []).map((v) => (
              <option key={v} value={v}>
                {v}
              </option>
            ))}
          </select>
        </div>

        {/* Sampler Selector */}
        <div className="batch-field">
          <label>Sampler</label>
          <select
            className="batch-input batch-select"
            value={samplerName}
            onChange={(e) => setSamplerName(e.target.value)}
          >
            {!comfyOptions.samplers.includes(samplerName) && (
              <option value={samplerName}>{samplerName}</option>
            )}
            {comfyOptions.samplers.map((s) => (
              <option key={s} value={s}>
                {s}
              </option>
            ))}
          </select>
        </div>

        {/* Scheduler Selector */}
        <div className="batch-field">
          <label>Scheduler</label>
          <select
            className="batch-input batch-select"
            value={scheduler}
            onChange={(e) => setScheduler(e.target.value)}
          >
            {!comfyOptions.schedulers.includes(scheduler) && (
              <option value={scheduler}>{scheduler}</option>
            )}
            {comfyOptions.schedulers.map((sch) => (
              <option key={sch} value={sch}>
                {sch}
              </option>
            ))}
          </select>
        </div>

        {/* Steps */}
        <div className="batch-field">
          <label>Steps</label>
          <input
            type="number"
            className="batch-input number-small"
            min={1}
            max={150}
            value={steps}
            onChange={(e) => setSteps(parseInt(e.target.value, 10) || 10)}
          />
        </div>

        {/* CFG */}
        <div className="batch-field">
          <label>CFG</label>
          <input
            type="number"
            className="batch-input number-small"
            min={0}
            max={30}
            step={0.1}
            value={cfg}
            onChange={(e) => setCfg(parseFloat(e.target.value) || 1.0)}
          />
        </div>

        {/* Seed Strategy */}
        <div className="batch-field">
          <label>Seed Strategy</label>
          <select
            className="batch-input batch-select"
            value={seedStrategy}
            onChange={(e) => setSeedStrategy(e.target.value as 'fixed' | 'sequential' | 'random')}
          >
            <option value="sequential">Sequential</option>
            <option value="fixed">Fixed</option>
            <option value="random">Random</option>
          </select>
        </div>

        {/* Base Seed */}
        <div className="batch-field">
          <label>Base Seed</label>
          <input
            type="number"
            className="batch-input"
            value={baseSeed}
            onChange={(e) => setBaseSeed(parseInt(e.target.value, 10) || 0)}
          />
        </div>

        {/* Resolution Preset */}
        <div className="batch-field">
          <label>Resolution</label>
          <select
            className="batch-input batch-select"
            value={
              ['896x1152', '1024x1024', '1152x896', '832x1216', '1216x832', '768x1024', '1024x768'].includes(`${width}x${height}`)
                ? `${width}x${height}`
                : 'custom'
            }
            onChange={(e) => {
              const val = e.target.value;
              if (val && val !== 'custom') {
                const [w, h] = val.split('x').map(Number);
                setWidth(w);
                setHeight(h);
              }
            }}
            title="Choose aspect ratio & resolution preset"
          >
            <option value="896x1152">896 × 1152 (Default Portrait)</option>
            <option value="1024x1024">1024 × 1024 (Square 1:1)</option>
            <option value="1152x896">1152 × 896 (Landscape 9:7)</option>
            <option value="832x1216">832 × 1216 (Portrait 2:3)</option>
            <option value="1216x832">1216 × 832 (Landscape 3:2)</option>
            <option value="768x1024">768 × 1024 (Portrait 3:4)</option>
            <option value="1024x768">1024 × 768 (Landscape 4:3)</option>
            <option value="custom">Custom ({width} × {height})</option>
          </select>
        </div>

        {/* Width Case */}
        <div className="batch-field">
          <label>Width</label>
          <input
            type="number"
            className="batch-input number-small"
            min={64}
            max={4096}
            step={64}
            value={width}
            onChange={(e) => setWidth(Math.max(64, parseInt(e.target.value, 10) || 896))}
            title="Image width in pixels (e.g. 896)"
            aria-label="Image width"
          />
        </div>

        {/* Height Case */}
        <div className="batch-field">
          <label>Height</label>
          <input
            type="number"
            className="batch-input number-small"
            min={64}
            max={4096}
            step={64}
            value={height}
            onChange={(e) => setHeight(Math.max(64, parseInt(e.target.value, 10) || 1152))}
            title="Image height in pixels (e.g. 1152)"
            aria-label="Image height"
          />
        </div>

        {/* Batch Queue Mode Switcher */}
        <div className="batch-field">
          <label>Queue Mode</label>
          <div className="batch-mode-toggle-group" role="group" aria-label="Batch Queue Mode">
            <button
              type="button"
              className={`batch-mode-btn ${queueMode === 'view' ? 'active' : ''}`}
              onClick={() => setQueueMode('view')}
              title="Queue from current view slice or manual card selections"
            >
              View / Selected
            </button>
            <button
              type="button"
              className={`batch-mode-btn ${queueMode === 'range' ? 'active' : ''}`}
              onClick={() => setQueueMode('range')}
              title="Queue a sequential range slice"
            >
              Range Slice
            </button>
            <button
              type="button"
              className={`batch-mode-btn ${queueMode === 'sample' ? 'active' : ''}`}
              onClick={() => setQueueMode('sample')}
              title="Queue a random sample across parameter space"
            >
              Random Sample
            </button>
            <button
              type="button"
              className={`batch-mode-btn ${queueMode === 'all' ? 'active' : ''}`}
              onClick={() => setQueueMode('all')}
              title={`Queue all ${totalCount.toLocaleString()} permutations`}
            >
              All
            </button>
          </div>
        </div>

        {/* Contextual Queue Inputs */}
        {queueMode === 'view' && (
          <div className="batch-field">
            <label>Limit</label>
            {selectedIndices.size > 0 ? (
              <div className="batch-selected-badge" title="Manual selection active in grid below">
                <span>{selectedIndices.size} cards selected manually</span>
              </div>
            ) : (
              <input
                type="number"
                className="batch-input number-small"
                min={1}
                max={totalCount || 10000}
                value={maxPromptsToQueue}
                onChange={(e) => setMaxPromptsToQueue(Math.max(1, parseInt(e.target.value, 10) || 1))}
                title="Number of prompts to send from current view slice"
                aria-label="Prompts to queue from view"
              />
            )}
          </div>
        )}

        {queueMode === 'range' && (
          <div className="batch-field">
            <label>Range Slice</label>
            <div className="batch-range-fields">
              <div className="batch-range-input-group">
                <span className="batch-range-label">Start #</span>
                <input
                  type="number"
                  className="batch-input batch-range-input number-small"
                  min={1}
                  max={Math.max(1, totalCount)}
                  value={queueRangeStart}
                  onChange={(e) => setQueueRangeStart(Math.max(1, parseInt(e.target.value, 10) || 1))}
                  title={`Start permutation index (1 to ${totalCount})`}
                  aria-label="Range start index"
                />
              </div>
              <div className="batch-range-input-group">
                <span className="batch-range-label">Step</span>
                <input
                  type="number"
                  className="batch-input batch-range-input number-small"
                  min={1}
                  max={Math.max(1, totalCount)}
                  value={queueRangeStep}
                  onChange={(e) => setQueueRangeStep(Math.max(1, parseInt(e.target.value, 10) || 1))}
                  title="Step increment between permutations (1 = consecutive, 5 = advance by 5 each time)"
                  aria-label="Range step size"
                />
              </div>
              <div className="batch-range-input-group">
                <span className="batch-range-label">Count</span>
                <input
                  type="number"
                  className="batch-input batch-range-input number-small"
                  min={1}
                  max={2000}
                  value={queueRangeCount}
                  onChange={(e) => setQueueRangeCount(Math.max(1, Math.min(2000, parseInt(e.target.value, 10) || 1)))}
                  title="Number of permutations to queue (max 2000)"
                  aria-label="Range count"
                />
              </div>
              <span className="batch-helper-text">
                {queueRangeStep > 1
                  ? `e.g. #${queueRangeStart}, #${queueRangeStart + queueRangeStep}... (to #${rangeEnd}, step ${queueRangeStep})`
                  : `e.g. #${queueRangeStart} - #${rangeEnd}`}
              </span>
            </div>
          </div>
        )}

        {queueMode === 'sample' && (
          <div className="batch-field">
            <label>Sample Count</label>
            <div className="batch-range-fields">
              <input
                type="number"
                className="batch-input batch-range-input number-small"
                min={1}
                max={2000}
                value={queueSampleCount}
                onChange={(e) => setQueueSampleCount(Math.max(1, Math.min(2000, parseInt(e.target.value, 10) || 1)))}
                title="Number of random permutations to sample (max 2000)"
                aria-label="Sample count"
              />
              <span className="batch-helper-text">
                randomly sampled from {totalCount.toLocaleString()} total
              </span>
            </div>
          </div>
        )}

        {queueMode === 'all' && (
          <div className="batch-field">
            <label>Batch Scope</label>
            <div className="batch-all-scope-container">
              <span className="batch-all-badge">
                All {totalCount.toLocaleString()} variants
              </span>
              {totalCount > 2000 && (
                <span
                  className="batch-warning-indicator"
                  title="Queueing > 2,000 prompts will submit a large batch to ComfyUI"
                >
                  <AlertTriangle size={13} className="warning-icon" /> Large Batch (&gt;2,000)
                </span>
              )}
            </div>
          </div>
        )}

        {/* Expand Wildcards */}
        <div className="batch-field batch-checkbox-field">
          <label className="expand-wildcards-toggle-sm" title="Expand each wildcard into all its possibilities">
            <input
              type="checkbox"
              checked={expandWildcards}
              onChange={(e) => handleToggleExpandWildcards(e.target.checked)}
            />
            <Sparkles size={12} className="toggle-icon" />
            <span>Expand Wildcards</span>
          </label>
        </div>

        {/* Send to Discord */}
        <div className="batch-field batch-checkbox-field">
          <label
            className="expand-wildcards-toggle-sm"
            title={
              discordWebhookUrl
                ? "Send each generated image + prompt to Discord (Webhook connected)"
                : "Send each generated image + prompt to Discord (Configure in Settings > Integrations)"
            }
          >
            <input
              type="checkbox"
              checked={sendToDiscord}
              onChange={(e) => setSendToDiscord(e.target.checked)}
            />
            <span style={{ fontSize: 12 }}>📨</span>
            <span>Send to Discord</span>
            {discordWebhookUrl ? (
              <span
                style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '3px',
                  fontSize: '10px',
                  color: '#4ade80',
                  background: 'rgba(74, 222, 128, 0.15)',
                  padding: '1px 5px',
                  borderRadius: '10px',
                  fontWeight: 600,
                  marginLeft: '4px'
                }}
                title="Discord Webhook Active"
              >
                ● Connected
              </span>
            ) : null}
          </label>
        </div>

        {/* Queue Button */}
        <button
          type="button"
          className="matrix-btn success"
          onClick={handleExecuteBatchSweep}
          disabled={loading || (sliceItems.length === 0 && totalCount === 0)}
          title={
            queueMode === 'view' && selectedIndices.size > 0
              ? `Queue ${selectedIndices.size} selected variants at ${width}x${height}`
              : queueMode === 'view'
              ? `Queue ${Math.min(maxPromptsToQueue, combinations.length)} from View (${width}×${height})`
              : queueMode === 'range'
              ? queueRangeStep > 1
                ? `Queue ${effectiveRangeCount} (step ${queueRangeStep}) from Range #${queueRangeStart}–#${rangeEnd} (${width}×${height})`
                : `Queue ${effectiveRangeCount} from Range #${queueRangeStart}–#${rangeEnd} (${width}×${height})`
              : queueMode === 'sample'
              ? `Queue ${queueSampleCount} Random Samples (${width}×${height})`
              : `Queue All (${totalCount.toLocaleString()}) (${width}×${height})`
          }
        >
          <Play size={14} />{' '}
          {queueMode === 'view' && (
            selectedIndices.size > 0
              ? `Queue ${selectedIndices.size} Selected (${width}×${height})`
              : `Queue ${Math.min(maxPromptsToQueue, combinations.length)} from View (${width}×${height})`
          )}
          {queueMode === 'range' && (
            queueRangeStep > 1
              ? `Queue ${effectiveRangeCount} (Step ${queueRangeStep}) from Range #${queueRangeStart}–#${rangeEnd} (${width}×${height})`
              : `Queue ${effectiveRangeCount} from Range #${queueRangeStart}–#${rangeEnd} (${width}×${height})`
          )}
          {queueMode === 'sample' && `Queue ${queueSampleCount} Random Samples (${width}×${height})`}
          {queueMode === 'all' && `Queue All (${totalCount.toLocaleString()}) (${width}×${height})`}
        </button>
      </div>
    </div>
  );

  // Slice Navigator Bar Renderer
  const renderSliceNavigator = () => {
    const start = totalCount > 0 ? currentOffset + 1 : 0;
    const end = Math.min(currentOffset + sliceItems.length, totalCount);

    return (
      <div className="matrix-slice-navigator">
        {/* Status readout */}
        <div className="slice-status-row">
          <div className="slice-status-info">
            {isSampleMode ? (
              <span className="slice-badge sample">
                🎲 Sampled <strong>{sliceItems.length}</strong> random variants of <strong>{totalCount.toLocaleString()}</strong> total
              </span>
            ) : (
              <span className="slice-badge">
                Total: <strong>{totalCount.toLocaleString()}</strong> Permutations | Viewing #{start.toLocaleString()} - #{end.toLocaleString()} of {totalCount.toLocaleString()}
              </span>
            )}
          </div>
        </div>

        {/* Controls Row */}
        <div className="slice-controls-row">
          {/* Page Size Dropdown */}
          <div className="slice-nav-group page-size-group">
            <label className="slice-nav-label">Page Size:</label>
            <select
              className="slice-select"
              value={pageSize}
              onChange={(e) => handlePageSizeChange(Number(e.target.value))}
              disabled={loading}
              aria-label="Page size"
            >
              <option value="50">50 / page</option>
              <option value="100">100 / page</option>
              <option value="250">250 / page</option>
              <option value="500">500 / page</option>
              <option value="1000">1000 / page</option>
            </select>
          </div>

          {/* Paging Controls */}
          <div className="slice-nav-group paging-controls">
            <button
              type="button"
              className="slice-nav-btn"
              onClick={handleFirstPage}
              disabled={currentPage <= 1 || loading || isSampleMode}
              title="First Page (<<)"
              aria-label="First page"
            >
              &laquo;
            </button>
            <button
              type="button"
              className="slice-nav-btn"
              onClick={handlePrevPage}
              disabled={currentPage <= 1 || loading || isSampleMode}
              title="Previous Page (<)"
              aria-label="Previous page"
            >
              &lsaquo;
            </button>

            <form className="slice-page-form" onSubmit={handlePageInputSubmit}>
              <span className="slice-nav-label">Page</span>
              <input
                type="text"
                className="slice-page-input"
                value={pageInput}
                onChange={(e) => setPageInput(e.target.value)}
                onBlur={handlePageInputSubmit}
                disabled={loading || isSampleMode}
                title="Press Enter to jump to page"
                aria-label="Page number"
              />
              <span className="slice-nav-label">of {totalPages.toLocaleString()}</span>
            </form>

            <button
              type="button"
              className="slice-nav-btn"
              onClick={handleNextPage}
              disabled={currentPage >= totalPages || loading || isSampleMode}
              title="Next Page (>)"
              aria-label="Next page"
            >
              &rsaquo;
            </button>
            <button
              type="button"
              className="slice-nav-btn"
              onClick={handleLastPage}
              disabled={currentPage >= totalPages || loading || isSampleMode}
              title="Last Page (>>)"
              aria-label="Last page"
            >
              &raquo;
            </button>
          </div>

          {/* Jump to Index */}
          <form className="slice-nav-group slice-jump-container" onSubmit={handleJumpToIndexSubmit}>
            <label className="slice-nav-label">Jump to #</label>
            <input
              type="text"
              className="slice-jump-input"
              placeholder="e.g. 25000"
              value={jumpIndexInput}
              onChange={(e) => setJumpIndexInput(e.target.value)}
              disabled={loading}
              aria-label="Jump to variation index"
            />
            <button
              type="submit"
              className="slice-nav-btn go-btn"
              disabled={loading || !jumpIndexInput.trim()}
              aria-label="Go to variation index"
            >
              Go
            </button>
          </form>

          {/* Random Sampling */}
          <div className="slice-nav-group slice-sample-container">
            <input
              type="number"
              className="slice-sample-input"
              min={1}
              max={2000}
              value={sampleCountInput}
              onChange={(e) => {
                const valStr = e.target.value;
                setSampleCountInput(valStr);
                const parsed = parseInt(valStr, 10);
                if (!isNaN(parsed) && parsed >= 1) {
                  setSampleCount(Math.min(parsed, 2000));
                }
              }}
              onBlur={() => {
                const parsed = parseInt(sampleCountInput.trim(), 10);
                if (isNaN(parsed) || parsed < 1) {
                  setSampleCount(100);
                  setSampleCountInput('100');
                } else {
                  const clamped = Math.max(1, Math.min(parsed, 2000));
                  setSampleCount(clamped);
                  setSampleCountInput(String(clamped));
                }
              }}
              disabled={loading}
              title="Number of random permutations to sample"
              aria-label="Sample count"
            />
            <button
              type="button"
              className="slice-nav-btn sample-btn"
              onClick={() => handleSampleRandom(sampleCount)}
              disabled={loading || totalCount === 0}
              title="Sample random permutations uniformly across entire combinatorial space"
              aria-label="Sample random variations"
            >
              🎲 Sample {sampleCount} Random
            </button>
            {isSampleMode && (
              <button
                type="button"
                className="slice-nav-btn sequential-btn"
                onClick={handleResetToSequential}
                disabled={loading}
                title="Return to sequential paginated view"
                aria-label="Switch to sequential view"
              >
                Sequential View
              </button>
            )}
          </div>
        </div>
      </div>
    );
  };

  // Matrix Permutations Grid Renderer
  const renderMatrixGrid = () => {
    if (sliceItems.length === 0 && totalCount === 0) {
      return (
        <div className="matrix-empty-state">
          <p>No permutations generated yet. Enter wildcard syntax or click "Preview Permutations".</p>
        </div>
      );
    }

    return (
      <div className="matrix-grid-container">
        {renderSliceNavigator()}

        {/* Permutation Selection Bar */}
        <div className="matrix-selection-bar">
          <div className="selection-info">
            <span className="selection-badge">
              Selected: <strong>{selectedIndices.size}</strong> {totalCount > 0 ? `of ${totalCount.toLocaleString()}` : ''}
            </span>
            {selectedIndices.size > 0 && (
              <span className="selection-hint">
                (Batch sweep will queue only these {selectedIndices.size} selected variants)
              </span>
            )}
          </div>
          <div className="selection-btn-group">
            <button
              type="button"
              className="selection-btn"
              onClick={() => handleSelectFirstN(maxPromptsToQueue)}
              title={`Select first ${maxPromptsToQueue} permutations`}
            >
              Select First {maxPromptsToQueue}
            </button>
            <button
              type="button"
              className="selection-btn"
              onClick={() => handleSelectRandomN(maxPromptsToQueue)}
              title={`Randomly select ${maxPromptsToQueue} permutations`}
            >
              Random {maxPromptsToQueue}
            </button>
            <button
              type="button"
              className="selection-btn"
              onClick={handleSelectAllShown}
              title={`Select all currently visible (${sliceItems.length}) permutations`}
            >
              Select Visible ({sliceItems.length})
            </button>
            {selectedIndices.size > 0 && (
              <button
                type="button"
                className="selection-btn clear"
                onClick={handleClearSelection}
                title="Deselect all permutations"
              >
                Clear
              </button>
            )}
          </div>
        </div>

        <div className="matrix-grid">
          {sliceItems.map((item) => {
            const score = getVariationTokenScore(item.prompt);
            const isCopied = copiedIdx === item.index;
            const isSelected = selectedIndices.has(item.index);
            return (
              <div
                key={item.index}
                className={`matrix-card ${isSelected ? 'is-selected' : ''}`}
                onClick={() => handleToggleSelectPrompt(item)}
                title="Click card or checkbox to select for queue"
              >
                <div className="matrix-card-header">
                  <div className="card-header-left" onClick={(e) => e.stopPropagation()}>
                    <input
                      type="checkbox"
                      className="matrix-card-checkbox"
                      checked={isSelected}
                      onChange={() => handleToggleSelectPrompt(item)}
                      title={`Select variation #${item.index}`}
                      aria-label={`Select variation #${item.index}`}
                    />
                    <span className="matrix-badge">Variation #{item.index.toLocaleString()}</span>
                  </div>
                  <div className="card-header-actions" onClick={(e) => e.stopPropagation()}>
                    <span className={`heatmap-pill ${score.heatClass}`}>
                      <Flame size={11} /> {score.count} tokens
                    </span>
                    <button
                      type="button"
                      className={`card-copy-btn ${isCopied ? 'copied' : ''}`}
                      onClick={() => handleCopyPrompt(item.prompt, item.index)}
                      title="Copy variation prompt"
                      aria-label="Copy variation prompt"
                    >
                      {isCopied ? <Check size={12} /> : <Copy size={12} />}
                    </button>
                  </div>
                </div>
                <div className="matrix-prompt-text">{item.prompt}</div>
              </div>
            );
          })}
        </div>
      </div>
    );
  };

  // Token Heatmap & Category Distribution Renderer
  const renderHeatmap = () => (
    <div className="heatmap-panel">
      <div className="heatmap-panel-header">
        <h4>🔥 Token Heatmap & Category Distribution Scoring Indicator</h4>
        <button className="analyze-btn" onClick={handleAnalyzeGraphAndHeatmap} disabled={loading}>
          <Activity size={13} /> {loading ? 'Analyzing...' : 'Re-analyze Heatmap'}
        </button>
      </div>

      {heatmapScores ? (
        <div className="heatmap-metrics-grid">
          <div className="metric-cards-row">
            <div className="metric-card">
              <span className="metric-title">Permutations Count</span>
              <span className="metric-value">{heatmapScores.combinations_count || totalCount}</span>
            </div>
            <div className="metric-card">
              <span className="metric-title">Avg Token Count</span>
              <span className="metric-value highlight">{heatmapScores.avg_token_count ?? 'N/A'}</span>
            </div>
            <div className="metric-card">
              <span className="metric-title">Min / Max Range</span>
              <span className="metric-value">{heatmapScores.min_token_count ?? 0} - {heatmapScores.max_token_count ?? 0}</span>
            </div>
          </div>

          {heatmapScores.category_distribution && (
            <div className="category-dist-box">
              <h5>Tag Category Proportions</h5>
              <div className="category-bars">
                {Object.entries(heatmapScores.category_distribution as Record<string, number>).map(([cat, count]) => (
                  <div key={cat} className="category-bar-row">
                    <span className="cat-name">{cat}</span>
                    <div className="cat-track">
                      <div
                        className={`cat-fill cat-${cat}`}
                        style={{
                          width: `${Math.min(100, ((count as number) / Math.max(1, heatmapScores.combinations_count || totalCount || 1)) * 100)}%`
                        }}
                      ></div>
                    </div>
                    <span className="cat-count">{count as number}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      ) : (
        <div className="heatmap-empty">
          {loading ? 'Analyzing heatmap...' : 'Click "Analyze Heatmap" or "Preview Permutations" to view token heatmap distribution metrics.'}
        </div>
      )}
    </div>
  );

  // AST Graph Tree Renderer
  const renderASTTree = () => (
    <div className="graph-tree-panel">
      <div className="tree-panel-header">
        <h4>🌳 AST Graph Tree Preview</h4>
        <span className="tree-subtitle">Hierarchical parsed syntax tree representation</span>
      </div>
      {graphTree ? (
        <div className="ast-tree-container">
          <ASTTreeNodeView node={graphTree} />
        </div>
      ) : (
        <div className="tree-empty">
          {loading ? 'Building graph tree...' : 'Click "Analyze Graph & Heatmap" or "Preview Permutations" to generate graph tree preview.'}
        </div>
      )}
    </div>
  );

  const renderSweepResultsSpace = () => {
    return (
      <div className="matrix-sweep-results-section">
        <div className="sweep-results-header">
          <div className="sweep-results-title">
            <ImageIcon size={18} style={{ color: '#cba6f7' }} />
            <h4>Generated Sweep Results ({sweepResults.length})</h4>
            <span className="sweep-badge-saved">Auto-saved to Gallery</span>
            {isSyncingSweep && (
              <span className="sweep-syncing-indicator">
                <RefreshCw size={12} className="spin" /> Syncing...
              </span>
            )}
          </div>
          <div className="sweep-results-actions">
            <button
              type="button"
              className="matrix-btn secondary sm"
              onClick={() => handleSyncSweepOutputs(true)}
              disabled={isSyncingSweep}
              title="Sync completed generations from ComfyUI"
            >
              <RefreshCw size={13} className={isSyncingSweep ? 'spin' : ''} />
              Sync from ComfyUI
            </button>
            {sweepResults.length > 0 && (
              <button
                type="button"
                className="matrix-btn secondary sm"
                onClick={() => setSweepResults([])}
                title="Clear view"
              >
                <Trash2 size={13} />
                Clear
              </button>
            )}
          </div>
        </div>

        {sweepResults.length === 0 ? (
          <div className="sweep-results-empty">
            <ImageIcon size={32} style={{ opacity: 0.3, marginBottom: 8 }} />
            <p>No generated images in this sweep view yet.</p>
            <p className="subtext">
              Click <strong>Queue Batch Sweep</strong> above to generate images in ComfyUI, or click <strong>Sync from ComfyUI</strong> to load recent runs.
            </p>
          </div>
        ) : (
          <div className="sweep-results-grid">
            {sweepResults.map((item, idx) => {
              const imgSrc = item.url || `/api/v1/images/file/${item.filename}`;
              return (
                <div
                  key={item.id || item.filename || idx}
                  className="sweep-result-card glass-panel"
                  onClick={() => setLightboxIndex(idx)}
                  title="Click to view larger with prompt"
                >
                  <div className="sweep-card-img-wrapper">
                    <img
                      src={imgSrc}
                      alt={item.filename}
                      className="sweep-card-img"
                      loading="lazy"
                      onError={(e) => {
                        const target = e.currentTarget;
                        const fallback = `/api/v1/images/file/${item.filename}`;
                        if (target.src !== window.location.origin + fallback) {
                          target.src = fallback;
                        }
                      }}
                    />
                    <div className="sweep-card-hover-overlay">
                      <Eye size={20} />
                      <span>View Larger</span>
                    </div>
                  </div>
                  <div className="sweep-card-meta">
                    <div className="sweep-card-tags">
                      {item.seed !== undefined && item.seed !== null && (
                        <span className="sweep-tag seed">Seed: {item.seed}</span>
                      )}
                      {item.steps && <span className="sweep-tag steps">{item.steps} st</span>}
                      {item.cfg_scale !== undefined && item.cfg_scale !== null && (
                        <span className="sweep-tag cfg">{item.cfg_scale} cfg</span>
                      )}
                    </div>
                    {item.prompt_content && (
                      <div className="sweep-card-prompt-preview" title={item.prompt_content}>
                        {item.prompt_content}
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    );
  };

  const renderLightboxModal = () => {
    if (lightboxIndex === null || !sweepResults[lightboxIndex]) return null;
    const item = sweepResults[lightboxIndex];
    const imgSrc = item.url || `/api/v1/images/file/${item.filename}`;
    const hasPrev = lightboxIndex > 0;
    const hasNext = lightboxIndex < sweepResults.length - 1;

    return (
      <div className="matrix-lightbox-overlay" onClick={() => setLightboxIndex(null)}>
        <div className="matrix-lightbox-modal" onClick={(e) => e.stopPropagation()}>
          <div className="matrix-lightbox-header">
            <div className="lightbox-title-area">
              <ImageIcon size={18} style={{ color: '#cba6f7' }} />
              <span className="lightbox-filename">{item.filename}</span>
              <span className="lightbox-counter">
                {lightboxIndex + 1} / {sweepResults.length}
              </span>
            </div>
            <button
              type="button"
              className="lightbox-close-btn"
              onClick={() => setLightboxIndex(null)}
              title="Close (Esc)"
            >
              <X size={18} />
            </button>
          </div>

          <div className="matrix-lightbox-body">
            {hasPrev && (
              <button
                type="button"
                className="lightbox-nav-btn prev"
                onClick={() => setLightboxIndex(lightboxIndex - 1)}
                title="Previous Image (Left Arrow)"
              >
                <ChevronLeft size={24} />
              </button>
            )}

            <div className="lightbox-image-container">
              <img
                src={imgSrc}
                alt={item.filename}
                className="matrix-lightbox-img"
                onError={(e) => {
                  const target = e.currentTarget;
                  const fallback = `/api/v1/images/file/${item.filename}`;
                  if (target.src !== window.location.origin + fallback) {
                    target.src = fallback;
                  }
                }}
              />
            </div>

            {hasNext && (
              <button
                type="button"
                className="lightbox-nav-btn next"
                onClick={() => setLightboxIndex(lightboxIndex + 1)}
                title="Next Image (Right Arrow)"
              >
                <ChevronRight size={24} />
              </button>
            )}
          </div>

          <div className="matrix-lightbox-prompt-space">
            <div className="prompt-space-header">
              <span className="prompt-label">Generating Prompt:</span>
              <div className="prompt-space-params">
                {item.seed !== undefined && item.seed !== null && (
                  <span className="param-badge">Seed: {item.seed}</span>
                )}
                {item.sampler_name && <span className="param-badge">Sampler: {item.sampler_name}</span>}
                {item.steps && <span className="param-badge">Steps: {item.steps}</span>}
                {item.cfg_scale !== undefined && item.cfg_scale !== null && (
                  <span className="param-badge">CFG: {item.cfg_scale}</span>
                )}
              </div>
            </div>

            <div className="prompt-space-content">
              {item.prompt_content || 'No prompt recorded for this image.'}
            </div>

            <div className="prompt-space-actions">
              <button
                type="button"
                className="matrix-btn primary sm"
                onClick={() => handleCopyPrompt(item.prompt_content || '', 99999)}
              >
                {copiedIdx === 99999 ? <Check size={14} /> : <Copy size={14} />}
                {copiedIdx === 99999 ? 'Copied Prompt!' : 'Copy Prompt'}
              </button>

              <a
                href={imgSrc}
                download={item.filename}
                className="matrix-btn secondary sm"
                target="_blank"
                rel="noreferrer"
              >
                <Download size={14} />
                Download PNG
              </a>

              {item.prompt_content && (
                <button
                  type="button"
                  className="matrix-btn secondary sm"
                  onClick={() => {
                    setPrompt(item.prompt_content || '');
                    setLightboxIndex(null);
                  }}
                  title="Load this prompt into the Matrix Studio"
                >
                  <Sparkles size={14} />
                  Load into Studio
                </button>
              )}
            </div>
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="matrix-panel">
      {/* Studio Header */}
      <div className="matrix-header">
        <div className="matrix-header-title-area">
          <h2>Visual AST & Matrix Studio</h2>
          <span className="matrix-header-subtitle">
            Unified interactive AST canvas, combinatorial generator & ComfyUI batch runner
          </span>
        </div>
        <div className="matrix-tab-pills">
          <button
            type="button"
            className={`pill-btn ${workspaceMode === 'split' ? 'active' : ''}`}
            onClick={() => setWorkspaceMode('split')}
          >
            <Layers size={14} /> Split View
          </button>
          <button
            type="button"
            className={`pill-btn ${workspaceMode === 'canvas' ? 'active' : ''}`}
            onClick={() => setWorkspaceMode('canvas')}
          >
            <Network size={14} /> Canvas
          </button>
          <button
            type="button"
            className={`pill-btn ${workspaceMode === 'grid' ? 'active' : ''}`}
            onClick={() => setWorkspaceMode('grid')}
          >
            <Zap size={14} /> Grid ({totalCount.toLocaleString()})
          </button>
          <button
            type="button"
            className={`pill-btn ${workspaceMode === 'heatmap' ? 'active' : ''}`}
            onClick={() => {
              setWorkspaceMode('heatmap');
              if (!heatmapScores) handleAnalyzeGraphAndHeatmap();
            }}
          >
            <Flame size={14} /> Heatmap
          </button>
          <button
            type="button"
            className={`pill-btn ${workspaceMode === 'tree' ? 'active' : ''}`}
            onClick={() => {
              setWorkspaceMode('tree');
              if (!graphTree) handleAnalyzeGraphAndHeatmap();
            }}
          >
            <GitFork size={14} /> AST Tree
          </button>
          <button
            type="button"
            className={`pill-btn ${workspaceMode === 'results' ? 'active' : ''}`}
            onClick={() => setWorkspaceMode('results')}
          >
            <ImageIcon size={14} /> Sweep Results ({sweepResults.length})
          </button>
        </div>
      </div>

      {/* Wildcard Template Prompt Bar */}
      <div className="matrix-input-area">
        <div className="input-label-row">
          <label>Wildcard Matrix Template:</label>
          <div className="input-actions-right">
            {activeDocument && (
              <button
                className="analyze-btn"
                title={`Load content from "${activeDocument.name}" into the template`}
                onClick={() => {
                  const content = activeDocument.content || '';
                  setPrompt(content);
                  syncFromPrompt(content);
                  triggerExpansion(content);
                }}
              >
                <GitFork size={13} /> Use Editor Prompt
              </button>
            )}
            <button className="analyze-btn" onClick={handleAnalyzeGraphAndHeatmap} disabled={loading}>
              <Activity size={13} /> Analyze Graph &amp; Heatmap
            </button>
          </div>
        </div>
        <textarea
          className="matrix-textarea"
          value={prompt}
          onChange={(e) => {
            const val = e.target.value;
            setPrompt(val);
            syncFromPrompt(val);
            triggerExpansion(val);
          }}
          placeholder="e.g. a {cyberpunk|steampunk|fantasy} {cat|dog|fox} in a {neon city|forest}"
        />
        <div className="matrix-actions">
          <label className="expand-wildcards-toggle" title="When checked, also expands each wildcard used in the prompt into all its possibilities for the matrix sweep preview">
            <input
              type="checkbox"
              checked={expandWildcards}
              onChange={(e) => handleToggleExpandWildcards(e.target.checked)}
            />
            <Sparkles size={14} className="toggle-icon" />
            <span>Expand Wildcards into Matrix ({availableWildcards.length > 0 ? `${availableWildcards.length} loaded` : 'Active'})</span>
          </label>
          <button className="matrix-btn primary" onClick={handlePreview} disabled={loading}>
            <Sparkles size={14} /> {loading ? 'Processing...' : 'Preview Permutations'}
          </button>
        </div>
      </div>

      {/* Node Toolbar & Workspace Mode Switcher */}
      <div className="matrix-node-toolbar">
        <div className="toolbar-left-group">
          <div className="toolbar-add-group">
            <span className="toolbar-label">Add Node:</span>
            <button
              type="button"
              className="toolbar-node-btn"
              onClick={() => addNode('text')}
              title="Add Text phrase node"
            >
              <Plus size={13} /> Text
            </button>
            <div className="toolbar-wildcard-add-group">
              <button
                type="button"
                className="toolbar-node-btn"
                onClick={() => addNode('wildcard')}
                title="Add blank Wildcard node"
              >
                <Plus size={13} /> Wildcard
              </button>
              {availableWildcards.length > 0 && (
                <WildcardSearchPicker
                  variant="toolbar"
                  value=""
                  placeholder={`+ Pick existing (${availableWildcards.length})...`}
                  availableWildcards={availableWildcards}
                  onSelect={(picked) => {
                    if (picked) {
                      addNode('wildcard', picked);
                    }
                  }}
                />
              )}
            </div>
            <button
              type="button"
              className="toolbar-node-btn"
              onClick={() => addNode('choice')}
              title="Add Choice Group node"
            >
              <Plus size={13} /> Choice Group
            </button>
            <button
              type="button"
              className="toolbar-node-btn"
              onClick={() => addNode('variable')}
              title="Add Variable node"
            >
              <Plus size={13} /> Variable
            </button>
          </div>

          <div className="permutation-count-badge" title="Active permutations count">
            <Zap size={13} />
            <span>{totalCount.toLocaleString()} Permutations</span>
          </div>

          {isCompiling && (
            <span className="compiling-pill" title="AST compiling...">
              <Sparkles size={12} className="spin-icon" /> Compiling...
            </span>
          )}
        </div>

        <div className="workspace-mode-switcher">
          <button
            type="button"
            className={`mode-btn ${workspaceMode === 'split' ? 'active' : ''}`}
            onClick={() => setWorkspaceMode('split')}
            title="Split: Canvas (top) + Grid (bottom)"
          >
            <Layers size={13} /> Split
          </button>
          <button
            type="button"
            className={`mode-btn ${workspaceMode === 'canvas' ? 'active' : ''}`}
            onClick={() => setWorkspaceMode('canvas')}
            title="Fullscreen Visual Canvas"
          >
            <Network size={13} /> Canvas
          </button>
          <button
            type="button"
            className={`mode-btn ${workspaceMode === 'grid' ? 'active' : ''}`}
            onClick={() => setWorkspaceMode('grid')}
            title="Fullscreen Permutations Grid"
          >
            <Zap size={13} /> Grid
          </button>
          <button
            type="button"
            className={`mode-btn ${workspaceMode === 'heatmap' ? 'active' : ''}`}
            onClick={() => {
              setWorkspaceMode('heatmap');
              if (!heatmapScores) handleAnalyzeGraphAndHeatmap();
            }}
            title="Token Heatmap & Category Breakdown"
          >
            <Flame size={13} /> Heatmap
          </button>
          <button
            type="button"
            className={`mode-btn ${workspaceMode === 'results' ? 'active' : ''}`}
            onClick={() => setWorkspaceMode('results')}
            title="Generated Sweep Results & Lightbox"
          >
            <ImageIcon size={13} /> Results ({sweepResults.length})
          </button>
        </div>
      </div>

      {status && <div className="matrix-status">{status}</div>}

      {/* Main Workspace Mode Content */}
      {workspaceMode === 'split' && (
        <div className="workspace-split-layout">
          <div className="workspace-canvas-pane">
            <VisualASTCanvas
              nodes={nodes}
              onNodesChange={setNodes}
              onNodeSelect={setSelectedNodeId}
              selectedNodeId={selectedNodeId}
              onAutoLayout={autoLayout}
              hasCycle={hasCycle}
              availableWildcards={availableWildcards}
              onUpdateNode={updateNodeData}
            />
            {renderNodeInspector()}
          </div>

          <div className="workspace-grid-pane">
            {renderComfyUIBatchBar()}
            {renderMatrixGrid()}
            {renderSweepResultsSpace()}
          </div>
        </div>
      )}

      {workspaceMode === 'canvas' && (
        <div className="workspace-canvas-fullscreen">
          <div className="workspace-canvas-pane fullscreen">
            <VisualASTCanvas
              nodes={nodes}
              onNodesChange={setNodes}
              onNodeSelect={setSelectedNodeId}
              selectedNodeId={selectedNodeId}
              onAutoLayout={autoLayout}
              hasCycle={hasCycle}
              availableWildcards={availableWildcards}
              onUpdateNode={updateNodeData}
            />
            {renderNodeInspector()}
          </div>
        </div>
      )}

      {workspaceMode === 'grid' && (
        <div className="workspace-grid-fullscreen">
          {renderComfyUIBatchBar()}
          {renderMatrixGrid()}
          {renderSweepResultsSpace()}
        </div>
      )}

      {workspaceMode === 'results' && (
        <div className="workspace-results-fullscreen">
          {renderSweepResultsSpace()}
        </div>
      )}

      {workspaceMode === 'heatmap' && (
        <div className="workspace-heatmap-layout">
          {renderHeatmap()}
        </div>
      )}

      {workspaceMode === 'tree' && (
        <div className="workspace-tree-layout">
          {renderASTTree()}
        </div>
      )}

      {renderLightboxModal()}
    </div>
  );
};
