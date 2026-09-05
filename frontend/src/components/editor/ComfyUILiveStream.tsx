import React, { useState, useEffect, useRef } from 'react';
import { useAppStore, ComfyStateSettings } from '../../store/useAppStore';
import { getGenerationOptions, createImage, inspectComfyUIWorkflow } from '../../api';
import { Play, Zap, Sparkles, Maximize2, Download, X, Layers, Image as ImageIcon, RefreshCw, Sliders, MapPin } from 'lucide-react';
import './ComfyUILiveStream.css';

interface ComfyUILiveStreamProps {
  workflow?: Record<string, unknown>;
  targetNodeId?: string;
  prompts?: string[];
  onExecuted?: (data: Record<string, unknown>) => void;
  onCompletedFrame?: (imageUrl: string) => void;
}

const RESOLUTION_PRESETS = [
  { label: '512 x 512 (Square - SD 1.5)', width: 512, height: 512 },
  { label: '768 x 768 (Square Medium)', width: 768, height: 768 },
  { label: '1024 x 1024 (Square - SDXL)', width: 1024, height: 1024 },
  { label: '896 x 1152 (Portrait - SDXL)', width: 896, height: 1152 },
  { label: '1152 x 896 (Landscape - SDXL)', width: 1152, height: 896 },
  { label: '832 x 1216 (Tall)', width: 832, height: 1216 },
  { label: '1216 x 832 (Wide)', width: 1216, height: 832 },
];

export const ComfyUILiveStream: React.FC<ComfyUILiveStreamProps> = ({
  workflow: initialWorkflow = {},
  targetNodeId: initialTargetNodeId = '6',
  prompts: initialPrompts = [],
  onExecuted,
  onCompletedFrame
}) => {
  const { comfyUIUrl, comfySettings, setComfySettings } = useAppStore();
  const [status, setStatus] = useState<string>('Idle');
  const [wsStatus, setWsStatus] = useState<string>('Disconnected');
  const [wsConnected, setWsConnected] = useState<boolean>(false);
  const [activeNode, setActiveNode] = useState<string | null>(null);
  const [progress, setProgress] = useState<number>(0);
  const [currentStep, setCurrentStep] = useState<number>(0);
  const [totalSteps, setTotalSteps] = useState<number>(comfySettings.steps || 20);
  const [livePreview, setLivePreview] = useState<string | null>(null);
  const [previewImageSrc, setPreviewImageSrc] = useState<string | null>(null);
  const [isExecuting, setIsExecuting] = useState<boolean>(false);
  const [lightboxImage, setLightboxImage] = useState<string | null>(null);

  const [isDrawerOpen, setIsDrawerOpen] = useState<boolean>(false);
  const [inspectedGraph, setInspectedGraph] = useState<{
    nodes: { node_id: string; class_type: string; title: string; inputs: string[] }[];
    prompt_nodes: { node_id: string; class_type: string; title: string; inputs: string[] }[];
    sampler_nodes: { node_id: string; class_type: string; title: string; inputs: string[] }[];
  } | null>(null);
  const [isInspecting, setIsInspecting] = useState<boolean>(false);


  // Sync helpers to keep Zustand store updated and persisted
  const updateSetting = <K extends keyof ComfyStateSettings>(key: K, value: ComfyStateSettings[K]) => {
    setComfySettings({ [key]: value });
  };

  const selectedModel = comfySettings.selectedModel || 'v1-5-pruned-emaonly.safetensors';
  const selectedSampler = comfySettings.selectedSampler || 'euler';
  const selectedScheduler = comfySettings.selectedScheduler || 'normal';
  const steps = comfySettings.steps || 20;
  const cfg = comfySettings.cfg || 7.0;
  const width = comfySettings.width || 512;
  const height = comfySettings.height || 512;
  const resPreset = comfySettings.resPreset || '512 x 512 (Square - SD 1.5)';
  const isCustomRes = comfySettings.isCustomRes || false;
  const singlePrompt = comfySettings.singlePrompt || 'masterpiece, best quality, vibrant futuristic cyberpunk city at sunset, highly detailed, 8k';
  const sweepInput = comfySettings.sweepInput || (initialPrompts.length > 0 ? initialPrompts.join('\n') : 'cyberpunk warrior standing in neon alley, 8k\nsteampunk inventor in brass workshop, masterpiece\nfantasy sorceress inside glowing crystal cavern, detailed');
  const targetNodeId = comfySettings.targetNodeId || initialTargetNodeId || '6';
  const seedNodeId = comfySettings.seedNodeId || '3';
  const gallery = comfySettings.gallery || [];

  const galleryRef = useRef(gallery);
  useEffect(() => {
    galleryRef.current = gallery;
  }, [gallery]);

  const [options, setOptions] = useState<{ models: string[]; samplers: string[]; schedulers: string[] }>({
    models: ['v1-5-pruned-emaonly.safetensors', 'sd_xl_base_1.0.safetensors', 'flux1-dev.safetensors'],
    samplers: ['euler', 'euler_ancestral', 'dpmpp_2m', 'dpmpp_sde', 'ddim', 'uni_pc'],
    schedulers: ['normal', 'karras', 'exponential', 'sgm_uniform', 'simple']
  });
  const [loadingOpts, setLoadingOpts] = useState<boolean>(false);

  // Track pending prompt IDs for history polling fallback
  const pendingPromptIdsRef = useRef<Set<string>>(new Set());

  // Interactive controls
  const [activeTab, setActiveTab] = useState<'single' | 'matrix' | 'workflow'>('single');
  const [isExpanding, setIsExpanding] = useState<boolean>(false);

  const onExecutedRef = useRef(onExecuted);
  onExecutedRef.current = onExecuted;
  const onCompletedFrameRef = useRef(onCompletedFrame);
  onCompletedFrameRef.current = onCompletedFrame;

  // Unique clientId for WebSocket subscription
  const clientIdRef = useRef<string>(`client_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`);

  const parsedPrompts = sweepInput
    .split('\n')
    .map((p) => p.trim())
    .filter(Boolean);

  // Fetch ComfyUI models, samplers, schedulers dynamically
  const fetchComfyOptions = async () => {
    setLoadingOpts(true);
    try {
      const data = await getGenerationOptions(comfyUIUrl);
      if (data) {
        if (Array.isArray(data.models) && data.models.length > 0) {
          setOptions((prev) => ({ ...prev, models: data.models }));
          if (!data.models.includes(selectedModel)) {
            updateSetting('selectedModel', data.models[0]);
          }
        }
        if (Array.isArray(data.samplers) && data.samplers.length > 0) {
          setOptions((prev) => ({ ...prev, samplers: data.samplers }));
          if (!data.samplers.includes(selectedSampler)) {
            updateSetting('selectedSampler', data.samplers[0]);
          }
        }
        if (Array.isArray(data.schedulers) && data.schedulers.length > 0) {
          setOptions((prev) => ({ ...prev, schedulers: data.schedulers }));
          if (!data.schedulers.includes(selectedScheduler)) {
            updateSetting('selectedScheduler', data.schedulers[0]);
          }
        }
      }
    } catch (e) {
      console.warn('Could not fetch ComfyUI options, using fallback list:', e);
    } finally {
      setLoadingOpts(false);
    }
  };

  useEffect(() => {
    fetchComfyOptions();
  }, [comfyUIUrl]);

  // Helper to save finished image to App Gallery & display in Live Stream
  const saveAndDisplayImage = async (filename: string, subfolder: string = '', type: string = 'output') => {
    const viewParams = new URLSearchParams({
      filename: filename,
      subfolder: subfolder,
      type: type
    });
    if (comfyUIUrl) viewParams.append('base_url', comfyUIUrl);
    const viewUrl = `/api/v1/comfyui/view?${viewParams.toString()}`;

    setLivePreview(viewUrl);
    if (!galleryRef.current.includes(viewUrl)) {
      updateSetting('gallery', [viewUrl, ...galleryRef.current]);
    }
    onCompletedFrameRef.current?.(viewUrl);

    // Save image to App Database Gallery
    try {
      await createImage({
        filename: filename,
        prompt_id: null,
        seed: Math.floor(Math.random() * 1000000000),
        cfg_scale: cfg,
        steps: steps,
        sampler_name: selectedSampler,
        width: width,
        height: height,
        comfyui_url: comfyUIUrl || undefined
      });
    } catch (err) {
      console.error('Error saving image to app database gallery:', err);
    }
  };

  // Fallback history checker for prompt ID
  const checkPromptHistory = async (promptId: string) => {
    try {
      const url = `/api/v1/comfyui/history/${promptId}${comfyUIUrl ? `?base_url=${encodeURIComponent(comfyUIUrl)}` : ''}`;
      const res = await fetch(url);
      if (!res.ok) return;
      const historyData = await res.json();
      const promptEntry = historyData[promptId];
      if (promptEntry && promptEntry.outputs) {
        for (const nodeId of Object.keys(promptEntry.outputs)) {
          const nodeOutput = promptEntry.outputs[nodeId];
          if (nodeOutput && Array.isArray(nodeOutput.images)) {
            for (const img of nodeOutput.images) {
              if (img.filename) {
                await saveAndDisplayImage(img.filename, img.subfolder || '', img.type || 'output');
              }
            }
          }
        }
        pendingPromptIdsRef.current.delete(promptId);
      }
    } catch (e) {
      console.error('Error checking prompt history:', e);
    }
  };

  const pollAllPendingHistory = async () => {
    const ids = Array.from(pendingPromptIdsRef.current);
    for (const pid of ids) {
      await checkPromptHistory(pid);
    }
  };

  useEffect(() => {
    let isMounted = true;
    let ws: WebSocket | null = null;
    let reconnectTimer: ReturnType<typeof setTimeout> | null = null;
    const clientId = clientIdRef.current;

    const connect = () => {
      if (!isMounted) return;
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const host = window.location.host;
      const params = new URLSearchParams();
      if (comfyUIUrl) {
        params.append('base_url', comfyUIUrl);
      }
      const queryStr = params.toString() ? `?${params.toString()}` : '';
      const wsUrl = `${protocol}//${host}/api/v1/comfyui/ws/${clientId}${queryStr}`;

      try {
        ws = new WebSocket(wsUrl);

        ws.onopen = () => {
          if (!isMounted) return;
          setWsConnected(true);
          setWsStatus('Connected');
        };

        ws.onclose = () => {
          if (!isMounted) return;
          setWsConnected(false);
          setWsStatus('Disconnected');
          setActiveNode(null);
          reconnectTimer = setTimeout(connect, 3000);
        };

        ws.onerror = (error) => {
          console.error('ComfyUI WebSocket error:', error);
          if (!isMounted) return;
          setWsStatus('Error');
          setWsConnected(false);
          setIsExecuting(false);
          setActiveNode(null);
        };

        ws.onmessage = (event) => {
          if (!isMounted) return;
          try {
            const payload = JSON.parse(event.data);
            const type = payload.type;
            const data = (payload.data || {}) as Record<string, any>;

            switch (type) {
              case 'executing':
                if (data.node) {
                  const nodeTitle = data.display_name || data.title || data.class_type || (data.node === '3' ? 'KSampler' : `Node #${data.node}`);
                  const badgeText = nodeTitle.startsWith('Node #') ? nodeTitle : `Node #${data.node}: ${nodeTitle}`;
                  setActiveNode(badgeText);
                  setIsExecuting(true);
                  setStatus(`Executing ${badgeText}`);
                } else {
                  setActiveNode(null);
                  setIsExecuting(false);
                  setStatus('Execution Complete');
                  setProgress(100);
                  pollAllPendingHistory();
                }
                break;

              case 'progress':
                const current = data.value ?? data.currentStep ?? 0;
                const total = data.max ?? data.totalSteps ?? 1;
                const pct = total > 0 ? Math.round((current / total) * 100) : 0;
                setCurrentStep(current);
                setTotalSteps(total);
                setProgress(pct);
                setIsExecuting(true);
                break;

              case 'preview_image': {
                const b64 = data.image_b64 || data.b64 || data.preview;
                if (b64) {
                  const imgSrc = b64.startsWith('data:image') ? b64 : `data:image/jpeg;base64,${b64}`;
                  setPreviewImageSrc(imgSrc);
                  setLivePreview(imgSrc);
                }
                break;
              }

              case 'executed': {
                if (data.output?.images?.[0]) {
                  for (const img of data.output.images) {
                    if (img.filename) {
                      saveAndDisplayImage(img.filename, img.subfolder || '', img.type || 'output');
                    }
                  }
                } else if (data.prompt_id) {
                  checkPromptHistory(data.prompt_id);
                } else if (data.image_b64) {
                  const finalImgUrl = data.image_b64.startsWith('data:image') ? data.image_b64 : `data:image/png;base64,${data.image_b64}`;
                  setLivePreview(finalImgUrl);
                  if (!galleryRef.current.includes(finalImgUrl)) {
                    updateSetting('gallery', [finalImgUrl, ...galleryRef.current]);
                  }
                }
                onExecutedRef.current?.(data as Record<string, unknown>);
                break;
              }

              case 'status':
                if (data.status?.exec_info?.queue_remaining !== undefined) {
                  const remaining = data.status.exec_info.queue_remaining;
                  if (remaining > 0) {
                    setIsExecuting(true);
                    setStatus(`Processing Queue (${remaining} remaining)`);
                  } else {
                    setIsExecuting(false);
                    setStatus('Idle');
                    setActiveNode(null);
                    pollAllPendingHistory();
                  }
                }
                break;

              default:
                break;
            }
          } catch (err) {
            console.error('Error handling WebSocket message:', err);
          }
        };
      } catch (e) {
        console.error('WebSocket creation error:', e);
        reconnectTimer = setTimeout(connect, 3000);
      }
    };

    connect();

    return () => {
      isMounted = false;
      if (reconnectTimer) clearTimeout(reconnectTimer);
      if (ws) {
        const socket = ws;
        socket.onopen = null;
        socket.onclose = null;
        socket.onerror = null;
        socket.onmessage = null;
        if (socket.readyState === WebSocket.OPEN) {
          socket.close();
        } else if (socket.readyState === WebSocket.CONNECTING) {
          socket.onopen = () => {
            try { socket.close(); } catch (_) {}
          };
        }
        ws = null;
      }
    };
  }, [comfyUIUrl]);

  const handleResPresetChange = (presetLabel: string) => {
    updateSetting('resPreset', presetLabel);
    if (presetLabel === 'custom') {
      updateSetting('isCustomRes', true);
    } else {
      updateSetting('isCustomRes', false);
      const found = RESOLUTION_PRESETS.find((p) => p.label === presetLabel);
      if (found) {
        updateSetting('width', found.width);
        updateSetting('height', found.height);
      }
    }
  };

  // Build Text-to-Image Workflow using selected model, sampler, scheduler, steps, cfg, resolution
  const getActiveWorkflow = (promptText: string) => {
    if (Object.keys(initialWorkflow).length > 0) {
      return initialWorkflow;
    }
    return {
      '3': {
        class_type: 'KSampler',
        inputs: {
          seed: Math.floor(Math.random() * 1000000000),
          steps: steps,
          cfg: cfg,
          sampler_name: selectedSampler,
          scheduler: selectedScheduler,
          denoise: 1,
          model: ['4', 0],
          positive: [targetNodeId || '6', 0],
          negative: ['7', 0],
          latent_image: ['5', 0]
        }
      },
      '4': { class_type: 'CheckpointLoaderSimple', inputs: { ckpt_name: selectedModel } },
      '5': { class_type: 'EmptyLatentImage', inputs: { batch_size: 1, width: width, height: height } },
      '6': { class_type: 'CLIPTextEncode', inputs: { text: promptText, clip: ['4', 1] } },
      '7': { class_type: 'CLIPTextEncode', inputs: { text: 'text, watermark, ugly, low quality', clip: ['4', 1] } },
      '8': { class_type: 'VAEDecode', inputs: { samples: ['3', 0], vae: ['4', 2] } },
      '9': { class_type: 'SaveImage', inputs: { filename_prefix: 'WildcardStudio', images: ['8', 0] } }
    };
  };

  const handleInspectWorkflow = async () => {
    setIsInspecting(true);
    try {
      const currentWf = getActiveWorkflow(singlePrompt);
      const result = await inspectComfyUIWorkflow(comfyUIUrl || '', currentWf);
      setInspectedGraph(result);
    } catch (err) {
      console.error('Error inspecting workflow graph:', err);
    } finally {
      setIsInspecting(false);
    }
  };

  const handleSingleGenerate = async () => {
    if (!singlePrompt.trim()) return;
    setIsExecuting(true);
    setTotalSteps(steps);
    setStatus('Dispatching Single Image...');
    try {
      const wf = getActiveWorkflow(singlePrompt);
      const response = await fetch('/api/v1/comfyui/execute-sweep', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          workflow: wf,
          target_node_id: targetNodeId || '6',
          seed_node_id: seedNodeId || '3',
          prompts: [singlePrompt],
          base_url: comfyUIUrl,
          client_id: clientIdRef.current
        })
      });
      if (!response.ok) {
        setStatus(`Execution failed: HTTP ${response.status}`);
        setIsExecuting(false);
        return;
      }
      const data = await response.json();
      if (data.job_results?.[0]?.prompt_id) {
        pendingPromptIdsRef.current.add(data.job_results[0].prompt_id);
      }
      setStatus(`Queued prompt in ComfyUI`);
    } catch (err) {
      console.error('Single generation error:', err);
      setStatus('Execution failed');
      setIsExecuting(false);
    }
  };

  const handleStartSweep = async () => {
    if (!parsedPrompts.length) return;
    setIsExecuting(true);
    setTotalSteps(steps);
    setStatus(`Dispatching Sweep (${parsedPrompts.length} Prompts)...`);
    try {
      const wf = getActiveWorkflow(parsedPrompts[0]);
      const response = await fetch('/api/v1/comfyui/execute-sweep', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          workflow: wf,
          target_node_id: targetNodeId || '6',
          seed_node_id: seedNodeId || '3',
          prompts: parsedPrompts,
          base_url: comfyUIUrl,
          client_id: clientIdRef.current
        })
      });
      if (!response.ok) {
        setStatus(`Sweep failed: HTTP ${response.status}`);
        setIsExecuting(false);
        return;
      }
      const data = await response.json();
      if (Array.isArray(data.job_results)) {
        for (const resItem of data.job_results) {
          if (resItem?.prompt_id) {
            pendingPromptIdsRef.current.add(resItem.prompt_id);
          }
        }
      }
      setStatus(`Queued ${data.queued_count} jobs in ComfyUI`);
    } catch (err) {
      console.error('Sweep execution error:', err);
      setStatus('Execution failed');
      setIsExecuting(false);
    }
  };

  const handleExpandMatrix = async () => {
    const rawText = activeTab === 'single' ? singlePrompt : sweepInput;
    if (!rawText.trim()) return;
    setIsExpanding(true);
    try {
      const response = await fetch('/api/v1/generate/matrix', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt: rawText, max_depth: 20 })
      });
      if (response.ok) {
        const generatedList: string[] = await response.json();
        if (Array.isArray(generatedList) && generatedList.length > 0) {
          updateSetting('sweepInput', generatedList.join('\n'));
          setActiveTab('matrix');
        }
      }
    } catch (e) {
      console.error('Failed to expand matrix:', e);
    } finally {
      setIsExpanding(false);
    }
  };

  const handleSamplePrompts = () => {
    updateSetting(
      'sweepInput',
      [
        'epic cinematic portrait of an astronaut exploring glowing alien flora, 8k resolution',
        'hyperrealistic portrait of a cyberpunk hacker with neon cybernetics, dramatic lighting',
        'serene studio ghibli style cottage in a sunlit meadow, lush nature, masterpiece',
        'futuristic sports car driving through rainy neon city at night, reflections, raytracing'
      ].join('\n')
    );
  };

  return (
    <div className="comfyui-live-stream">
      {/* Header Bar */}
      <div className="stream-header">
        <div className="header-title">
          <h3>⚡ Live ComfyUI Stream & Sweep Controller</h3>
          {activeNode && (
            <span className="active-node-badge pulse">
              <span className="node-icon">⚙️</span> {activeNode}
            </span>
          )}
        </div>
        <div className="status-badges">
          <span className={`ws-badge ${wsConnected ? 'connected' : 'disconnected'}`}>
            <span className="ws-dot"></span>
            {wsStatus}
          </span>
          <span className={`status-badge ${isExecuting ? 'active' : ''}`}>{status}</span>
          <button
            className="action-btn secondary"
            style={{ padding: '5px 10px', fontSize: '0.78rem' }}
            onClick={() => {
              setIsDrawerOpen(true);
              handleInspectWorkflow();
            }}
          >
            <MapPin size={13} /> Node Mapping Drawer
          </button>
        </div>
      </div>

      {/* Main Stream Grid */}
      <div className="stream-main-grid">
        {/* Left Column: Live Preview & Canvas */}
        <div className="stream-left-pane">
          <div className="preview-container">
            {(previewImageSrc || livePreview) ? (
              <img
                src={previewImageSrc || livePreview!}
                alt="Live ComfyUI Preview"
                className="live-frame frame-fade-in"
                onError={() => {
                  setLivePreview(null);
                  setPreviewImageSrc(null);
                }}
              />
            ) : (
              <div className="placeholder-frame">
                <ImageIcon size={36} className="placeholder-icon" />
                <span>Real-Time ComfyUI Render Stream</span>
                <p className="placeholder-sub">Queue a prompt or matrix sweep to watch live sampling steps</p>
              </div>
            )}

            {livePreview && (
              <button
                className="fullscreen-btn"
                title="Open Fullscreen Lightbox"
                onClick={() => setLightboxImage(livePreview)}
              >
                <Maximize2 size={16} />
              </button>
            )}
          </div>

          <div className="progress-bar-container">
            <div
              className={`progress-bar-fill ${isExecuting ? 'pulsing' : ''}`}
              style={{ width: `${progress}%` }}
            ></div>
          </div>
          <div className="progress-text">
            Step {currentStep} / {totalSteps} ({progress}%)
          </div>

          {/* Completed Gallery */}
          {gallery.length > 0 && (
            <div className="completed-gallery">
              <div className="gallery-header">
                <h4>Completed Frames ({gallery.length})</h4>
                <button className="clear-gallery-btn" onClick={() => updateSetting('gallery', [])}>
                  Clear
                </button>
              </div>
              <div className="gallery-grid">
                {gallery.map((imgUrl, idx) => (
                  <div key={`${imgUrl}-${idx}`} className="thumb-wrapper">
                    <img
                      src={imgUrl}
                      alt={`Completed render ${idx + 1}`}
                      className="gallery-thumb"
                      onClick={() => setLivePreview(imgUrl)}
                    />
                    <button
                      className="thumb-zoom"
                      onClick={(e) => {
                        e.stopPropagation();
                        setLightboxImage(imgUrl);
                      }}
                    >
                      <Maximize2 size={12} />
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Right Column: Controls & Generation Settings */}
        <div className="stream-right-pane">
          {/* Generation Settings Panel */}
          <div className="settings-panel-card">
            <div className="panel-title-row">
              <Sliders size={15} className="title-icon" />
              <span>ComfyUI Model & Generation Settings</span>
              <button
                className="refresh-options-btn"
                onClick={fetchComfyOptions}
                disabled={loadingOpts}
                title="Refresh models and options from ComfyUI"
              >
                <RefreshCw size={13} className={loadingOpts ? 'spinning' : ''} />
              </button>
            </div>

            {/* Model Selector */}
            <div className="settings-field">
              <label className="field-label">Model (Safetensors Checkpoint)</label>
              <select
                className="select-input"
                value={selectedModel}
                onChange={(e) => updateSetting('selectedModel', e.target.value)}
              >
                {options.models.map((m) => (
                  <option key={m} value={m}>
                    {m}
                  </option>
                ))}
              </select>
            </div>

            {/* Sampler & Scheduler Grid */}
            <div className="settings-dual-row">
              <div className="settings-field">
                <label className="field-label">Sampler</label>
                <select
                  className="select-input"
                  value={selectedSampler}
                  onChange={(e) => updateSetting('selectedSampler', e.target.value)}
                >
                  {options.samplers.map((s) => (
                    <option key={s} value={s}>
                      {s}
                    </option>
                  ))}
                </select>
              </div>

              <div className="settings-field">
                <label className="field-label">Scheduler</label>
                <select
                  className="select-input"
                  value={selectedScheduler}
                  onChange={(e) => updateSetting('selectedScheduler', e.target.value)}
                >
                  {options.schedulers.map((sch) => (
                    <option key={sch} value={sch}>
                      {sch}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            {/* Steps & CFG Sliders */}
            <div className="settings-dual-row">
              <div className="settings-field">
                <div className="field-label-row">
                  <span>Steps</span>
                  <span className="field-val-badge">{steps}</span>
                </div>
                <input
                  type="range"
                  min="1"
                  max="100"
                  value={steps}
                  onChange={(e) => updateSetting('steps', parseInt(e.target.value))}
                  className="range-slider"
                />
              </div>

              <div className="settings-field">
                <div className="field-label-row">
                  <span>CFG Scale</span>
                  <span className="field-val-badge">{cfg}</span>
                </div>
                <input
                  type="range"
                  min="1"
                  max="30"
                  step="0.5"
                  value={cfg}
                  onChange={(e) => updateSetting('cfg', parseFloat(e.target.value))}
                  className="range-slider"
                />
              </div>
            </div>

            {/* Resolution Preset / Custom */}
            <div className="settings-field">
              <label className="field-label">Image Resolution</label>
              <select
                className="select-input"
                value={resPreset}
                onChange={(e) => handleResPresetChange(e.target.value)}
              >
                {RESOLUTION_PRESETS.map((p) => (
                  <option key={p.label} value={p.label}>
                    {p.label}
                  </option>
                ))}
                <option value="custom">Custom Dimensions...</option>
              </select>

              {isCustomRes && (
                <div className="custom-res-row">
                  <input
                    type="number"
                    className="num-input"
                    value={width}
                    onChange={(e) => updateSetting('width', parseInt(e.target.value) || 512)}
                    placeholder="Width"
                  />
                  <span>x</span>
                  <input
                    type="number"
                    className="num-input"
                    value={height}
                    onChange={(e) => updateSetting('height', parseInt(e.target.value) || 512)}
                    placeholder="Height"
                  />
                </div>
              )}
            </div>
          </div>

          {/* Navigation Tabs for Prompts & Sweeps */}
          <div className="control-tabs">
            <button
              className={`tab-btn ${activeTab === 'single' ? 'active' : ''}`}
              onClick={() => setActiveTab('single')}
            >
              <Play size={14} /> Single Prompt
            </button>
            <button
              className={`tab-btn ${activeTab === 'matrix' ? 'active' : ''}`}
              onClick={() => setActiveTab('matrix')}
            >
              <Zap size={14} /> Matrix Sweep ({parsedPrompts.length})
            </button>
            <button
              className={`tab-btn ${activeTab === 'workflow' ? 'active' : ''}`}
              onClick={() => setActiveTab('workflow')}
            >
              <Layers size={14} /> Workflow & Nodes
            </button>
          </div>

          {/* Tab 1: Single Prompt */}
          {activeTab === 'single' && (
            <div className="tab-content">
              <label className="input-label">Generation Prompt</label>
              <textarea
                className="prompt-textarea"
                rows={3}
                value={singlePrompt}
                onChange={(e) => updateSetting('singlePrompt', e.target.value)}
                placeholder="Type your prompt here... Use {a|b} for matrix variations"
              />
              <div className="tab-actions">
                <button
                  onClick={handleExpandMatrix}
                  disabled={isExpanding || !singlePrompt.trim()}
                  className="action-btn secondary"
                >
                  <Sparkles size={14} /> {isExpanding ? 'Expanding...' : 'Expand to Sweep'}
                </button>
                <button
                  onClick={handleSingleGenerate}
                  disabled={isExecuting || !singlePrompt.trim()}
                  className="action-btn primary"
                >
                  <Play size={14} /> {isExecuting ? 'Executing...' : 'Send to ComfyUI'}
                </button>
              </div>
            </div>
          )}

          {/* Tab 2: Matrix Sweep */}
          {activeTab === 'matrix' && (
            <div className="tab-content">
              <div className="label-with-actions">
                <label className="input-label">Matrix Sweep Prompts (1 per line)</label>
                <button className="text-action-btn" onClick={handleSamplePrompts}>
                  🎲 Load Samples
                </button>
              </div>
              <textarea
                className="prompt-textarea matrix"
                rows={5}
                value={sweepInput}
                onChange={(e) => updateSetting('sweepInput', e.target.value)}
                placeholder="Enter one prompt per line..."
              />
              <div className="tab-actions">
                <button
                  onClick={handleExpandMatrix}
                  disabled={isExpanding || !sweepInput.trim()}
                  className="action-btn secondary"
                >
                  <Sparkles size={14} /> {isExpanding ? 'Expanding...' : 'Expand Syntax'}
                </button>
                <button
                  onClick={handleStartSweep}
                  disabled={isExecuting || parsedPrompts.length === 0}
                  className="action-btn primary"
                >
                  <Zap size={14} />{' '}
                  {isExecuting ? 'Running Sweep...' : `Run Matrix Sweep (${parsedPrompts.length})`}
                </button>
              </div>
            </div>
          )}

          {/* Tab 3: Workflow Configuration */}
          {activeTab === 'workflow' && (
            <div className="tab-content">
              <div className="node-config-group">
                <label className="input-label">Target Text Encoder Node ID</label>
                <input
                  type="text"
                  className="node-input"
                  value={targetNodeId}
                  onChange={(e) => updateSetting('targetNodeId', e.target.value)}
                  placeholder="e.g. 6 (CLIPTextEncode)"
                />
                <span className="field-help">Node ID in ComfyUI workflow where text prompt is injected</span>
              </div>

              <div className="node-config-group">
                <label className="input-label">Target Seed Node ID</label>
                <input
                  type="text"
                  className="node-input"
                  value={seedNodeId}
                  onChange={(e) => updateSetting('seedNodeId', e.target.value)}
                  placeholder="e.g. 3 (KSampler)"
                />
                <span className="field-help">Node ID where random seeds are assigned per sweep job</span>
              </div>

              <div className="workflow-status-card">
                <div className="card-row">
                  <span className="card-label">Workflow Source:</span>
                  <span className="card-val">
                    {Object.keys(initialWorkflow).length > 0 ? 'Custom Workflow Payload' : 'Built-in Standard T2I'}
                  </span>
                </div>
                <div className="card-row">
                  <span className="card-label">Target Endpoint:</span>
                  <span className="card-val">{comfyUIUrl || 'http://localhost:8188'}</span>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Lightbox Modal */}
      {lightboxImage && (
        <div className="lightbox-overlay" onClick={() => setLightboxImage(null)}>
          <div className="lightbox-modal" onClick={(e) => e.stopPropagation()}>
            <button className="lightbox-close" onClick={() => setLightboxImage(null)}>
              <X size={20} />
            </button>
            <img src={lightboxImage} alt="Fullscreen Render" className="lightbox-img" />
            <div className="lightbox-actions">
              <a
                href={lightboxImage}
                download="comfyui_render.png"
                target="_blank"
                rel="noreferrer"
                className="lightbox-download-btn"
              >
                <Download size={14} /> Download High-Res Image
              </a>
            </div>
          </div>
        </div>
      )}

      {/* Dynamic Workflow Node Input Mapping Drawer */}
      {isDrawerOpen && (
        <div className="mapping-drawer-overlay" onClick={() => setIsDrawerOpen(false)}>
          <div className="mapping-drawer-content" onClick={(e) => e.stopPropagation()}>
            <div className="drawer-header">
              <h4>Node Input Mapping Drawer</h4>
              <div className="drawer-actions">
                <button className="refresh-options-btn" onClick={handleInspectWorkflow} disabled={isInspecting} title="Re-inspect workflow graph">
                  <RefreshCw size={14} className={isInspecting ? 'spinning' : ''} />
                </button>
                <button className="lightbox-close" onClick={() => setIsDrawerOpen(false)}>
                  <X size={18} />
                </button>
              </div>
            </div>

            <div className="drawer-body">
              <p className="drawer-intro">
                Dynamically inspect node inputs from the active ComfyUI workflow graph and set prompt/seed target nodes.
              </p>

              {inspectedGraph ? (
                <div className="drawer-sections">
                  <div className="drawer-section">
                    <h5>Prompt Encoders ({inspectedGraph.prompt_nodes?.length || 0})</h5>
                    <div className="node-list">
                      {(inspectedGraph.prompt_nodes || []).map((node) => (
                        <div key={node.node_id} className={`node-card ${targetNodeId === node.node_id ? 'active-target' : ''}`}>
                          <div className="node-card-title">Node #{node.node_id}: {node.title}</div>
                          <div className="node-card-meta">{node.class_type}</div>
                          <button
                            className="node-select-btn"
                            onClick={() => updateSetting('targetNodeId', node.node_id)}
                          >
                            {targetNodeId === node.node_id ? '✓ Active Text Target' : 'Set as Prompt Target'}
                          </button>
                        </div>
                      ))}
                    </div>
                  </div>

                  <div className="drawer-section">
                    <h5>Samplers & Generators ({inspectedGraph.sampler_nodes?.length || 0})</h5>
                    <div className="node-list">
                      {(inspectedGraph.sampler_nodes || []).map((node) => (
                        <div key={node.node_id} className={`node-card ${seedNodeId === node.node_id ? 'active-target' : ''}`}>
                          <div className="node-card-title">Node #{node.node_id}: {node.title}</div>
                          <div className="node-card-meta">{node.class_type}</div>
                          <button
                            className="node-select-btn"
                            onClick={() => updateSetting('seedNodeId', node.node_id)}
                          >
                            {seedNodeId === node.node_id ? '✓ Active Seed Target' : 'Set as Seed Target'}
                          </button>
                        </div>
                      ))}
                    </div>
                  </div>

                  <div className="drawer-section">
                    <h5>All Discovered Graph Nodes ({inspectedGraph.nodes?.length || 0})</h5>
                    <div className="nodes-table-wrapper">
                      <table className="nodes-table">
                        <thead>
                          <tr>
                            <th>ID</th>
                            <th>Class Type</th>
                            <th>Title</th>
                            <th>Inputs</th>
                          </tr>
                        </thead>
                        <tbody>
                          {(inspectedGraph.nodes || []).map((node) => (
                            <tr key={node.node_id}>
                              <td>#{node.node_id}</td>
                              <td>{node.class_type}</td>
                              <td>{node.title}</td>
                              <td>{Array.isArray(node.inputs) ? node.inputs.join(', ') : 'None'}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="drawer-empty">
                  {isInspecting ? 'Inspecting workflow graph...' : 'Click "Inspect" to discover dynamic node inputs.'}
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
