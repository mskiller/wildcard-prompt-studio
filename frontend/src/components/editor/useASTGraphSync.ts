import React, { useState, useRef, useEffect, useMemo, useCallback } from 'react';
import { ASTCanvasNodeData } from './VisualASTCanvas';

export interface UseASTGraphSyncOptions {
  initialPrompt?: string;
  onPromptChange?: (newPrompt: string) => void;
}

export interface UseASTGraphSyncReturn {
  nodes: ASTCanvasNodeData[];
  setNodes: React.Dispatch<React.SetStateAction<ASTCanvasNodeData[]>>;
  selectedNodeId: string | null;
  setSelectedNodeId: (id: string | null) => void;
  hasCycle: boolean;
  isCompiling: boolean;
  updateNodeData: (id: string, partial: Partial<ASTCanvasNodeData>) => void;
  addNode: (type: 'text' | 'wildcard' | 'choice' | 'variable') => void;
  deleteNode: (id: string) => void;
  autoLayout: () => void;
  syncFromPrompt: (promptText: string) => void;
}

/**
 * Strips leading/trailing underscores and whitespace from a wildcard name.
 * e.g. "__category/name__" -> "category/name"
 */
export function cleanWildcardName(value?: string): string {
  if (!value) return '';
  return value.trim().replace(/^_+|_+$/g, '').trim();
}

/**
 * Checks for cycles in the node graph using depth-first search (DFS) with 3-color cycle detection.
 * Sets hasCycle = true if a back-edge is detected in node.outputs.
 */
export function detectCycle(nodes: ASTCanvasNodeData[]): boolean {
  if (!nodes || nodes.length === 0) return false;

  const adj = new Map<string, string[]>();
  for (const node of nodes) {
    adj.set(node.id, node.outputs || []);
  }

  // 0: unvisited, 1: visiting (recursion stack), 2: visited
  const state = new Map<string, number>();
  for (const node of nodes) {
    state.set(node.id, 0);
  }

  function dfs(nodeId: string): boolean {
    state.set(nodeId, 1);
    const neighbors = adj.get(nodeId);
    if (neighbors) {
      for (const neighborId of neighbors) {
        const neighborState = state.get(neighborId);
        if (neighborState === 1) {
          return true; // Back-edge detected
        }
        if (neighborState === 0) {
          if (dfs(neighborId)) return true;
        }
      }
    }
    state.set(nodeId, 2);
    return false;
  }

  for (const node of nodes) {
    if (state.get(node.id) === 0) {
      if (dfs(node.id)) return true;
    }
  }

  return false;
}

/**
 * Compiles an array of canvas nodes back into a reconstructed prompt string.
 * Supports:
 * - Text node -> node.value
 * - Wildcard node -> __${cleanWildcardName(node.value)}__
 * - Choice node -> {${node.options.map(o => o.weight !== 1.0 ? `${o.weight}::${o.text}` : o.text).join(' | ')}}
 * - Variable node -> $${node.title} = ${node.value}
 * Reconstructs space-separated or comma-separated prompt string.
 */
export function compileToPrompt(nodes: ASTCanvasNodeData[]): string {
  if (!nodes || nodes.length === 0) return '';

  const compiledItems: Array<{ text: string; delimiter?: string }> = [];

  for (const node of nodes) {
    let str = '';
    switch (node.type) {
      case 'text':
        str = node.value ?? '';
        break;
      case 'wildcard': {
        const clean = cleanWildcardName(node.value);
        str = clean ? `__${clean}__` : '';
        break;
      }
      case 'choice': {
        if (node.options && node.options.length > 0) {
          const opts = node.options
            .map(o => {
              const hasCustomWeight = o.weight !== undefined && o.weight !== null && o.weight !== 1.0;
              if (hasCustomWeight) {
                return `${o.weight}::${o.text}`;
              }
              if (!o.text || !o.text.trim()) {
                return '1::';
              }
              return o.text;
            })
            .join(' | ');
          str = `{${opts}}`;
        } else if (node.value) {
          const trimmed = node.value.trim();
          str = trimmed.startsWith('{') && trimmed.endsWith('}') ? trimmed : `{${trimmed}}`;
        } else {
          str = '{}';
        }
        break;
      }
      case 'variable': {
        const cleanTitle = node.title.startsWith('$') ? node.title.slice(1) : node.title;
        str = node.value !== undefined && node.value !== '' ? `$${cleanTitle} = ${node.value}` : `$${cleanTitle}`;
        break;
      }
      case 'root':
      default:
        str = node.value ?? '';
        break;
    }

    if (str.trim().length > 0) {
      const delimiter = (node as any).delimiter as string | undefined;
      compiledItems.push({ text: str.trim(), delimiter });
    }
  }

  if (compiledItems.length === 0) return '';

  let result = '';
  for (let i = 0; i < compiledItems.length; i++) {
    const item = compiledItems[i];
    const isLast = i === compiledItems.length - 1;

    result += item.text;

    if (!isLast) {
      if (item.delimiter !== undefined) {
        result += item.delimiter;
      } else if (item.text.endsWith(',') || item.text.endsWith(';')) {
        result += ' ';
      } else {
        result += ' ';
      }
    }
  }

  return result.replace(/\s{2,}/g, ' ').trim();
}

interface RawToken {
  type: 'wildcard' | 'choice' | 'variable';
  start: number;
  end: number;
  raw: string;
  name?: string;
  value?: string;
  options?: Array<{ id: string; text: string; weight: number }>;
}

interface IntermediateNode {
  type: 'text' | 'wildcard' | 'choice' | 'variable';
  title: string;
  value: string;
  options?: Array<{ id: string; text: string; weight: number }>;
  delimiter?: string;
}

/**
 * Parses a prompt string into AST canvas nodes.
 * Preserves user (x, y) coordinates for existing nodes and assigns clean horizontal layout for new nodes.
 * Wires sequential outputs from node N to node N+1.
 */
export function parsePromptToNodes(
  prompt: string,
  existingNodes: ASTCanvasNodeData[] = []
): ASTCanvasNodeData[] {
  if (!prompt || !prompt.trim()) return [];

  const rawTokens: RawToken[] = [];
  let match: RegExpExecArray | null;

  // 1. Choice groups: support top-level choice groups with nested choices { ... { ... } ... }
  let i = 0;
  while (i < prompt.length) {
    if (prompt[i] === '\\') {
      i += 2;
      continue;
    }
    if (prompt[i] === '{') {
      const start = i;
      let depth = 1;
      let j = i + 1;
      while (j < prompt.length && depth > 0) {
        if (prompt[j] === '\\') {
          j += 2;
          continue;
        }
        if (prompt[j] === '{') {
          depth++;
        } else if (prompt[j] === '}') {
          depth--;
        }
        j++;
      }
      if (depth === 0) {
        const raw = prompt.substring(start, j);
        const inner = prompt.substring(start + 1, j - 1);

        // Split options by top-level pipe '|' only
        const rawOpts: string[] = [];
        let optStart = 0;
        let innerDepth = 0;
        for (let k = 0; k < inner.length; k++) {
          if (inner[k] === '\\') {
            k++;
            continue;
          }
          if (inner[k] === '{') innerDepth++;
          else if (inner[k] === '}') innerDepth--;
          else if (inner[k] === '|' && innerDepth === 0) {
            rawOpts.push(inner.substring(optStart, k));
            optStart = k + 1;
          }
        }
        rawOpts.push(inner.substring(optStart));

        const options = rawOpts.map((optStr, optIdx) => {
          const trimmed = optStr.trim();
          const weightMatch = trimmed.match(/^([0-9]+(?:\.[0-9]+)?)\s*(?:::|\$\$)\s*(.*)$/s);
          if (weightMatch) {
            const w = parseFloat(weightMatch[1]);
            return {
              id: `opt_${Date.now().toString(36)}_${optIdx}_${Math.random().toString(36).substring(2, 6)}`,
              text: weightMatch[2].trim(),
              weight: isNaN(w) ? 1.0 : w
            };
          }
          return {
            id: `opt_${Date.now().toString(36)}_${optIdx}_${Math.random().toString(36).substring(2, 6)}`,
            text: trimmed,
            weight: 1.0
          };
        });

        rawTokens.push({
          type: 'choice',
          start,
          end: j,
          raw,
          options
        });
        i = j;
        continue;
      }
    }
    i++;
  }

  // 2. Wildcards: __category/name__
  const wildcardRegex = /__([a-zA-Z0-9_\-/\\]+)__/g;
  while ((match = wildcardRegex.exec(prompt)) !== null) {
    rawTokens.push({
      type: 'wildcard',
      start: match.index,
      end: match.index + match[0].length,
      raw: match[0],
      value: match[1]
    });
  }

  // 3. Variables: $varName = value
  const varRegex = /\$([a-zA-Z0-9_]+)\s*=\s*([^,\n;{}]+)/g;
  while ((match = varRegex.exec(prompt)) !== null) {
    rawTokens.push({
      type: 'variable',
      start: match.index,
      end: match.index + match[0].length,
      raw: match[0],
      name: match[1],
      value: match[2].trim()
    });
  }

  // Sort tokens by start position and filter overlaps
  rawTokens.sort((a, b) => a.start - b.start);
  const nonOverlapping: RawToken[] = [];
  let lastEnd = 0;
  for (const tok of rawTokens) {
    if (tok.start >= lastEnd) {
      nonOverlapping.push(tok);
      lastEnd = tok.end;
    }
  }

  const items: IntermediateNode[] = [];
  let cursor = 0;

  for (let i = 0; i < nonOverlapping.length; i++) {
    const tok = nonOverlapping[i];
    if (tok.start > cursor) {
      const textBetween = prompt.substring(cursor, tok.start);
      const trimmed = textBetween.trim();
      const onlyDelimiter = /^[\s,;]+$/.test(textBetween);

      if (onlyDelimiter) {
        if (items.length > 0) {
          items[items.length - 1].delimiter = textBetween.includes(',') ? ', ' : ' ';
        }
      } else {
        if (/^[\s,;]*[,;]/.test(textBetween) && items.length > 0) {
          items[items.length - 1].delimiter = ', ';
        }
        let textVal = trimmed;
        let delim = ' ';
        if (/,\s*$/.test(textVal)) {
          textVal = textVal.replace(/,\s*$/, '').trim();
          delim = ', ';
        }
        if (/^,\s*/.test(textVal)) {
          textVal = textVal.replace(/^,\s*/, '').trim();
        }
        if (textVal) {
          items.push({
            type: 'text',
            title: 'Text Prompt',
            value: textVal,
            delimiter: delim
          });
        }
      }
    }

    if (tok.type === 'wildcard') {
      const clean = cleanWildcardName(tok.value);
      items.push({
        type: 'wildcard',
        title: clean || 'Wildcard',
        value: clean,
        delimiter: ' '
      });
    } else if (tok.type === 'choice') {
      items.push({
        type: 'choice',
        title: 'Choice Group',
        value: tok.raw,
        options: tok.options,
        delimiter: ' '
      });
    } else if (tok.type === 'variable') {
      items.push({
        type: 'variable',
        title: tok.name ? `$${tok.name}` : 'var',
        value: tok.value || '',
        delimiter: ' '
      });
    }

    cursor = tok.end;
  }

  // Handle remaining tail text
  if (cursor < prompt.length) {
    const tail = prompt.substring(cursor);
    const trimmed = tail.trim();
    const onlyDelimiter = /^[\s,;]+$/.test(tail);
    if (onlyDelimiter) {
      if (items.length > 0) {
        items[items.length - 1].delimiter = '';
      }
    } else {
      if (/^[\s,;]*[,;]/.test(tail) && items.length > 0) {
        items[items.length - 1].delimiter = ', ';
      }
      let textVal = trimmed;
      if (/^,\s*/.test(textVal)) {
        textVal = textVal.replace(/^,\s*/, '').trim();
      }
      if (/,\s*$/.test(textVal)) {
        textVal = textVal.replace(/,\s*$/, '').trim();
      }
      if (textVal) {
        items.push({
          type: 'text',
          title: 'Text Prompt',
          value: textVal,
          delimiter: ''
        });
      }
    }
  }

  // Preserve user (x, y) coordinates for existing nodes
  const remainingExisting = [...existingNodes];
  const matchedNodes: ASTCanvasNodeData[] = [];

  for (let i = 0; i < items.length; i++) {
    const item = items[i];

    // Priority 1: Match by exact type and value
    let foundIdx = remainingExisting.findIndex(
      ex => ex.type === item.type && ex.value === item.value
    );

    // Priority 2: Match by same type at same index
    if (foundIdx === -1) {
      foundIdx = remainingExisting.findIndex(
        (ex, idx) => ex.type === item.type && idx === i
      );
    }

    // Priority 3: Match existing node at index i
    if (foundIdx === -1 && remainingExisting[i]) {
      foundIdx = i;
    }

    let nodeData: ASTCanvasNodeData;
    if (foundIdx !== -1) {
      const existing = remainingExisting[foundIdx];
      remainingExisting.splice(foundIdx, 1);
      nodeData = {
        id: existing.id,
        type: item.type,
        title: item.title,
        value: item.value,
        options: item.options,
        x: existing.x,
        y: existing.y,
        outputs: []
      };
    } else {
      // New node: Assign layout position x = col * 300 + 40, y = 80
      nodeData = {
        id: `node_${Date.now().toString(36)}_${i}_${Math.random().toString(36).substring(2, 6)}`,
        type: item.type,
        title: item.title,
        value: item.value,
        options: item.options,
        x: i * 300 + 40,
        y: 80,
        outputs: []
      };
    }

    if (item.delimiter !== undefined) {
      (nodeData as any).delimiter = item.delimiter;
    }

    matchedNodes.push(nodeData);
  }

  // Wires sequential outputs from node N to node N+1
  for (let i = 0; i < matchedNodes.length; i++) {
    if (i < matchedNodes.length - 1) {
      matchedNodes[i].outputs = [matchedNodes[i + 1].id];
    } else {
      matchedNodes[i].outputs = [];
    }
  }

  return matchedNodes;
}

/**
 * Bi-Directional Synchronization Hook for AST Canvas Graph & Prompt String.
 */
export function useASTGraphSync(options: UseASTGraphSyncOptions = {}): UseASTGraphSyncReturn {
  const { initialPrompt = '', onPromptChange } = options;

  const [nodes, setNodes] = useState<ASTCanvasNodeData[]>(() => {
    if (!initialPrompt) return [];
    return parsePromptToNodes(initialPrompt, []);
  });
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const [isCompiling, setIsCompiling] = useState<boolean>(false);

  const nodesRef = useRef<ASTCanvasNodeData[]>(nodes);
  nodesRef.current = nodes;

  const onPromptChangeRef = useRef(onPromptChange);
  useEffect(() => {
    onPromptChangeRef.current = onPromptChange;
  }, [onPromptChange]);

  const isExternalSyncRef = useRef<boolean>(false);
  const lastEmittedPromptRef = useRef<string>(initialPrompt);
  const lastReceivedPromptRef = useRef<string>(initialPrompt);
  const debounceTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Sync if initialPrompt prop updates externally
  const prevInitialPromptRef = useRef<string>(initialPrompt);
  useEffect(() => {
    if (initialPrompt !== prevInitialPromptRef.current) {
      prevInitialPromptRef.current = initialPrompt;
      lastReceivedPromptRef.current = initialPrompt;
      isExternalSyncRef.current = true;
      const parsed = parsePromptToNodes(initialPrompt, nodesRef.current);
      setNodes(parsed);
    }
  }, [initialPrompt]);

  // Memoized cycle detection via DFS
  const hasCycle = useMemo(() => detectCycle(nodes), [nodes]);

  // Debounced synchronization to onPromptChange (150ms)
  useEffect(() => {
    if (isExternalSyncRef.current) {
      isExternalSyncRef.current = false;
      return;
    }

    const compiled = compileToPrompt(nodes);

    if (compiled === lastEmittedPromptRef.current || compiled === lastReceivedPromptRef.current) {
      return;
    }

    setIsCompiling(true);

    if (debounceTimerRef.current) {
      clearTimeout(debounceTimerRef.current);
    }

    debounceTimerRef.current = setTimeout(() => {
      lastEmittedPromptRef.current = compiled;
      setIsCompiling(false);
      onPromptChangeRef.current?.(compiled);
    }, 150);

    return () => {
      if (debounceTimerRef.current) {
        clearTimeout(debounceTimerRef.current);
      }
    };
  }, [nodes]);

  // Synchronize canvas nodes from external prompt string
  const syncFromPrompt = useCallback((promptText: string) => {
    lastReceivedPromptRef.current = promptText;
    isExternalSyncRef.current = true;
    const nextNodes = parsePromptToNodes(promptText, nodesRef.current);
    setNodes(nextNodes);
  }, []);

  // Update a single node's properties
  const updateNodeData = useCallback((id: string, partial: Partial<ASTCanvasNodeData>) => {
    setNodes(prev =>
      prev.map(node => {
        if (node.id !== id) return node;
        return { ...node, ...partial };
      })
    );
  }, []);

  // Add a new node in sequence
  const addNode = useCallback((type: 'text' | 'wildcard' | 'choice' | 'variable') => {
    setNodes(prev => {
      const col = prev.length;
      const newNodeId = `node_${Date.now().toString(36)}_${Math.random().toString(36).substring(2, 7)}`;
      let newNode: ASTCanvasNodeData;

      switch (type) {
        case 'text':
          newNode = {
            id: newNodeId,
            type: 'text',
            title: 'Text Prompt',
            value: 'new prompt phrase',
            x: col * 300 + 40,
            y: 80,
            outputs: []
          };
          break;
        case 'wildcard':
          newNode = {
            id: newNodeId,
            type: 'wildcard',
            title: 'Wildcard',
            value: 'wildcard_name',
            x: col * 300 + 40,
            y: 80,
            outputs: []
          };
          break;
        case 'choice':
          newNode = {
            id: newNodeId,
            type: 'choice',
            title: 'Choice Group',
            value: '{optionA | optionB}',
            options: [
              { id: `opt_${Date.now().toString(36)}_1`, text: 'optionA', weight: 1.0 },
              { id: `opt_${Date.now().toString(36)}_2`, text: 'optionB', weight: 1.0 }
            ],
            x: col * 300 + 40,
            y: 80,
            outputs: []
          };
          break;
        case 'variable':
          newNode = {
            id: newNodeId,
            type: 'variable',
            title: '$var_name',
            value: 'value',
            x: col * 300 + 40,
            y: 80,
            outputs: []
          };
          break;
      }

      // Wires sequential outputs from previous last node to new node
      const updated = prev.map((n, idx) => {
        if (idx === prev.length - 1) {
          return {
            ...n,
            outputs: [newNode.id]
          };
        }
        return n;
      });

      setSelectedNodeId(newNode.id);
      return [...updated, newNode];
    });
  }, []);

  // Delete a node and re-wire connections
  const deleteNode = useCallback((id: string) => {
    setNodes(prev => {
      const targetNode = prev.find(n => n.id === id);
      const targetOutputs = targetNode?.outputs || [];

      const remaining = prev.filter(n => n.id !== id);

      // Reconnect outputs across the deleted node
      return remaining.map(n => {
        if (n.outputs && n.outputs.includes(id)) {
          const rewired = n.outputs
            .filter(outId => outId !== id)
            .concat(targetOutputs)
            .filter((v, idx, arr) => arr.indexOf(v) === idx);
          return { ...n, outputs: rewired };
        }
        return n;
      });
    });

    setSelectedNodeId(prev => (prev === id ? null : prev));
  }, []);

  // Auto-layout: repositions all nodes sequentially into horizontal flow
  const autoLayout = useCallback(() => {
    setNodes(prev => {
      return prev.map((node, index) => ({
        ...node,
        x: index * 300 + 40,
        y: 80
      }));
    });
  }, []);

  return {
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
  };
}
