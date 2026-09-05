/// <reference types="vite/client" />
const API_BASE = import.meta.env.VITE_API_BASE || '/api/v1';

export interface Krea2Options {
  prompt: string;
  variant?: 'turbo' | 'medium' | 'large' | string;
  quote_targets?: string[];
  clean_buzzwords?: boolean;
  provider?: 'kobold' | 'ollama' | 'gemini' | string;
  max_tokens?: number;
}

export async function krea2ImprovePrompt(options: Krea2Options): Promise<string> {
  const res = await fetch(`${API_BASE}/ai/krea2-improve`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(options),
  });

  if (!res.ok) {
    throw new Error(`Failed to improve prompt with Krea 2: ${res.statusText}`);
  }

  const data = await res.json();
  return data.improved_prompt;
}

export interface AnimaOptions {
  prompt: string;
  variant?: 'hybrid' | 'tag_focused' | 'natural_language';
  add_quality_tags?: boolean;
  clean_weights?: boolean;
  negative_prompt?: string;
  provider?: string;
  model?: string;
}

export async function animaImprovePrompt(options: AnimaOptions): Promise<string> {
  const res = await fetch(`${API_BASE}/ai/anima-improve`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(options),
  });

  if (!res.ok) {
    throw new Error(`Failed to improve prompt with Anima: ${res.statusText}`);
  }

  const data = await res.json();
  return data.improved_prompt;
}


export async function expandMatrixPrompt(prompt: string, maxLimit?: number, expandWildcards: boolean = true): Promise<string[]> {
  const res = await fetch(`${API_BASE}/generate/matrix`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ prompt, max_depth: 10, max_limit: maxLimit ?? null, expand_wildcards: expandWildcards }),
  });

  if (!res.ok) {
    throw new Error(`Failed to expand matrix prompt: ${res.statusText}`);
  }

  const data = await res.json();
  return data;
}

export async function executeMatrixSweep(prompt: string, limit?: number, expandWildcards: boolean = true): Promise<{ total_generated: number; prompts: string[]; status: string }> {
  const res = await fetch(`${API_BASE}/generate/matrix/execute`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ prompt, limit: limit ?? null, expand_wildcards: expandWildcards }),
  });

  if (!res.ok) {
    throw new Error(`Failed to execute matrix sweep: ${res.statusText}`);
  }

  return res.json();
}

export async function analyzeMatrixHeatmap(prompt: string, expandWildcards: boolean = true, maxLimit?: number): Promise<any> {
  const res = await fetch(`${API_BASE}/generate/matrix/analyze`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ prompt, expand_wildcards: expandWildcards, max_limit: maxLimit ?? null }),
  });
  if (!res.ok) {
    throw new Error(`Failed to analyze matrix heatmap: ${res.statusText}`);
  }
  return res.json();
}


export async function getSimulationTree(template: string): Promise<any> {

  const res = await fetch(`${API_BASE}/simulator/tree`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ template, iterations: 1 }),
  });
  if (!res.ok) throw new Error(`Failed to fetch AST tree: ${res.statusText}`);
  return res.json();
}

export async function getTagRecommendations(tags: string[]): Promise<string[]> {
  const res = await fetch(`${API_BASE}/simulator/recommendations`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ tags, top_k: 5 }),
  });
  if (!res.ok) throw new Error(`Failed to fetch tag recommendations: ${res.statusText}`);
  const data = await res.json();
  return data.recommendations;
}

export async function scoreAestheticPrompt(prompt: string): Promise<number> {
  const res = await fetch(`${API_BASE}/aesthetic/score`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ prompt }),
  });
  if (!res.ok) throw new Error(`Failed to calculate score: ${res.statusText}`);
  const data = await res.json();
  return data.aesthetic_score;
}

export async function evolvePrompts(population: string[], fitnessScores: number[]): Promise<string[]> {
  const res = await fetch(`${API_BASE}/aesthetic/evolve`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ population, fitness_scores: fitnessScores }),
  });
  if (!res.ok) throw new Error(`Failed to evolve prompts: ${res.statusText}`);
  const data = await res.json();
  return data.generation;
}

export async function searchCivitaiHub(query: string): Promise<any[]> {
  const res = await fetch(`${API_BASE}/aesthetic/civitai/search?q=${encodeURIComponent(query)}`);
  if (!res.ok) throw new Error(`Failed to search hub: ${res.statusText}`);
  return res.json();
}

export interface RAGDocument {
  id: number;
  title: string;
  content: string;
  tags: string[];
}

export interface RAGSearchResult extends RAGDocument {
  similarity_score: number;
}

export interface RAGStats {
  total_documents: number;
  total_tags: number;
  model_name: string;
}

export async function getRAGStats(): Promise<RAGStats> {
  const res = await fetch(`${API_BASE}/ai/rag/stats`);
  if (!res.ok) throw new Error(`Failed to fetch RAG stats: ${res.statusText}`);
  return res.json();
}

export async function getRAGDocuments(query?: string, tag?: string, signal?: AbortSignal): Promise<RAGDocument[]> {
  const origin = typeof window !== 'undefined' ? window.location.origin : 'http://localhost:5173';
  const fullBase = API_BASE.startsWith('http') ? API_BASE : `${origin}${API_BASE}`;
  const url = new URL(`${fullBase}/ai/rag/documents`);
  if (query) url.searchParams.append('query', query);
  if (tag) url.searchParams.append('tag', tag);

  const res = await fetch(url.toString(), { signal });
  if (!res.ok) throw new Error(`Failed to fetch RAG documents: ${res.statusText}`);
  const data = await res.json();
  return data.documents;
}

export async function deleteRAGDocument(docId: number): Promise<{ status: string; doc_id: number }> {
  const res = await fetch(`${API_BASE}/ai/rag/documents/${docId}`, {
    method: 'DELETE',
  });
  if (!res.ok) throw new Error(`Failed to delete RAG document: ${res.statusText}`);
  return res.json();
}

export async function searchRAGKnowledge(query: string, topK: number = 3): Promise<RAGSearchResult[]> {
  const res = await fetch(`${API_BASE}/ai/rag/search`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query, top_k: topK }),
  });
  if (!res.ok) throw new Error(`Failed to search RAG vector db: ${res.statusText}`);
  const data = await res.json();
  return data.results;
}

export async function indexRAGKnowledge(title: string, content: string, tags: string[] = []): Promise<{ status: string; document: RAGDocument }> {
  const res = await fetch(`${API_BASE}/ai/rag/index`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ title, content, tags }),
  });
  if (!res.ok) throw new Error(`Failed to index knowledge: ${res.statusText}`);
  return res.json();
}

export async function indexRAGDocument(title: string, content: string, tags: string[] = []): Promise<{ status: string; document: RAGDocument }> {
  return indexRAGKnowledge(title, content, tags);
}






export async function expandPrompt(prompt: string): Promise<string> {
  const res = await fetch(`${API_BASE}/generate/expand`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ prompt }),
  });

  if (!res.ok) {
    throw new Error(`Failed to expand prompt: ${res.statusText}`);
  }

  const data = await res.json();
  return data.expanded_prompt;
}

export async function improvePrompt(prompt: string, target_model: string, kobold_url: string, use_rag: boolean = false, max_tokens: number = 4096): Promise<string> {
  const res = await fetch(`${API_BASE}/ai/improve`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ prompt, target_model, kobold_url, use_rag, max_tokens }),
  });

  if (!res.ok) {
    throw new Error(`Failed to improve prompt: ${res.statusText}`);
  }

  const data = await res.json();
  return data.improved_prompt;
}

export interface GenerationOptionsData {
  models: string[];
  clips?: string[];
  vaes?: string[];
  samplers: string[];
  schedulers: string[];
  connected: boolean;
}

export async function getGenerationOptions(comfyuiUrl?: string): Promise<GenerationOptionsData> {
  const origin = typeof window !== 'undefined' ? window.location.origin : 'http://localhost:5173';
  const fullBase = API_BASE.startsWith('http') ? API_BASE : `${origin}${API_BASE}`;
  const url = new URL(`${fullBase}/generate/options`);
  if (comfyuiUrl) url.searchParams.append('comfyui_url', comfyuiUrl);
  const res = await fetch(url.toString());
  if (!res.ok) {
    throw new Error(`Failed to fetch generation options: ${res.statusText}`);
  }
  return res.json();
}

export interface GenerationSettings {
  model: string;
  sampler: string;
  scheduler: string;
  steps: number;
  cfg: number;
  width: number;
  height: number;
  seed?: number;
}

export async function generateImage(prompt: string, comfyuiUrl: string, settings?: GenerationSettings): Promise<any> {
  const s = {
    model: settings?.model || 'v1-5-pruned-emaonly.safetensors',
    sampler: settings?.sampler || 'euler',
    scheduler: settings?.scheduler || 'normal',
    steps: settings?.steps || 20,
    cfg: settings?.cfg || 7,
    width: settings?.width || 512,
    height: settings?.height || 512,
    seed: settings?.seed || Math.floor(Math.random() * 10000000000)
  };
  // Basic Text2Image Workflow
  const workflow = {
    "3": { "class_type": "KSampler", "inputs": { "seed": s.seed, "steps": s.steps, "cfg": s.cfg, "sampler_name": s.sampler, "scheduler": s.scheduler, "denoise": 1, "model": ["4", 0], "positive": ["6", 0], "negative": ["7", 0], "latent_image": ["5", 0] } },
    "4": { "class_type": "CheckpointLoaderSimple", "inputs": { "ckpt_name": s.model } },
    "5": { "class_type": "EmptyLatentImage", "inputs": { "batch_size": 1, "width": s.width, "height": s.height } },
    "6": { "class_type": "CLIPTextEncode", "inputs": { "text": prompt, "clip": ["4", 1] } },
    "7": { "class_type": "CLIPTextEncode", "inputs": { "text": "text, watermark, ugly", "clip": ["4", 1] } },
    "8": { "class_type": "VAEDecode", "inputs": { "samples": ["3", 0], "vae": ["4", 2] } },
    "9": { "class_type": "SaveImage", "inputs": { "filename_prefix": "WildcardStudio", "images": ["8", 0] } }
  };

  const res = await fetch(`${API_BASE}/generate/submit`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ workflow, comfyui_url: comfyuiUrl })
  });

  if (!res.ok) {
    throw new Error(`Failed to submit workflow: ${res.statusText}`);
  }
  
  return res.json();
}

export async function getWildcards(): Promise<any[]> {
  const res = await fetch(`${API_BASE}/wildcards/`);
  if (!res.ok) {
    throw new Error(`Failed to fetch wildcards: ${res.statusText}`);
  }
  const data = await res.json();
  return Array.isArray(data) ? data : [];
}

export async function createWildcard(data: { filename: string; content: string }): Promise<any> {
  const res = await fetch(`${API_BASE}/wildcards/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    throw new Error(`Failed to create wildcard: ${res.statusText}`);
  }
  return res.json();
}

export async function updateWildcard(id: number, data: { filename?: string; content?: string }): Promise<any> {
  const res = await fetch(`${API_BASE}/wildcards/${id}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    throw new Error(`Failed to update wildcard: ${res.statusText}`);
  }
  return res.json();
}

export async function deleteWildcard(id: number): Promise<any> {
  const res = await fetch(`${API_BASE}/wildcards/${id}`, { method: 'DELETE' });
  if (!res.ok) {
    throw new Error(`Failed to delete wildcard: ${res.statusText}`);
  }
  return res.json();
}

export async function importWildcards(formData: FormData): Promise<{ imported_wildcards: number; extracted_tags: number }> {
  const res = await fetch(`${API_BASE}/wildcards/import`, {
    method: 'POST',
    body: formData,
  });
  if (!res.ok) {
    let errorMsg = `Upload failed with status ${res.status}`;
    try {
      const errorText = await res.text();
      if (errorText && errorText.trim()) {
        try {
          const parsed = JSON.parse(errorText);
          errorMsg = parsed.detail || parsed.message || errorText;
        } catch {
          errorMsg = errorText;
        }
      }
    } catch {
      // Ignore text read error
    }
    throw new Error(errorMsg);
  }
  return res.json();
}

export async function getPrompts(): Promise<any[]> {
  const res = await fetch(`${API_BASE}/prompts/`);
  if (!res.ok) {
    throw new Error(`Failed to fetch prompts: ${res.statusText}`);
  }
  const data = await res.json();
  return Array.isArray(data) ? data : [];
}

export async function createPrompt(data: { name: string; content: string; author?: string; license?: string; theme?: string }): Promise<any> {
  const res = await fetch(`${API_BASE}/prompts/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    throw new Error(`Failed to create prompt: ${res.statusText}`);
  }
  return res.json();
}

export async function updatePrompt(id: number, data: { name?: string; content?: string; author?: string; license?: string; theme?: string }): Promise<any> {
  const res = await fetch(`${API_BASE}/prompts/${id}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    throw new Error(`Failed to update prompt: ${res.statusText}`);
  }
  return res.json();
}

export async function deletePrompt(id: number): Promise<any> {
  const res = await fetch(`${API_BASE}/prompts/${id}`, { method: 'DELETE' });
  if (!res.ok) {
    throw new Error(`Failed to delete prompt: ${res.statusText}`);
  }
  return res.json();
}


export async function searchPrompts(query: string): Promise<any[]> {
  const origin = typeof window !== 'undefined' ? window.location.origin : 'http://localhost:5173';
  const fullBase = API_BASE.startsWith('http') ? API_BASE : `${origin}${API_BASE}`;
  const url = new URL(`${fullBase}/prompts/search`);
  url.searchParams.append('q', query);
  const res = await fetch(url.toString());
  if (!res.ok) {
    throw new Error(`Failed to search prompts: ${res.statusText}`);
  }
  const data = await res.json();
  return Array.isArray(data) ? data : [];
}

export async function getTags(): Promise<any[]> {
  const res = await fetch(`${API_BASE}/tags/`);
  if (!res.ok) {
    throw new Error(`Failed to fetch tags: ${res.statusText}`);
  }
  const data = await res.json();
  return Array.isArray(data) ? data : [];
}

export async function getProfiles(): Promise<any[]> {
  const res = await fetch(`${API_BASE}/profiles/`);
  if (!res.ok) {
    throw new Error(`Failed to fetch profiles: ${res.statusText}`);
  }
  return res.json();
}

export async function createProfile(data: any): Promise<any> {
  const res = await fetch(`${API_BASE}/profiles/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
  });
  if (!res.ok) {
    throw new Error(`Failed to create profile: ${res.statusText}`);
  }
  return res.json();
}

export async function updateProfile(id: number, data: any): Promise<any> {
  const res = await fetch(`${API_BASE}/profiles/${id}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
  });
  if (!res.ok) {
    throw new Error(`Failed to update profile: ${res.statusText}`);
  }
  return res.json();
}

export async function getGalleryImages(): Promise<any[]> {
  const res = await fetch(`${API_BASE}/images/gallery`);
  if (!res.ok) {
    throw new Error(`Failed to fetch gallery: ${res.statusText}`);
  }
  return res.json();
}

export async function createImage(data: any): Promise<any> {
  const res = await fetch(`${API_BASE}/images/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
  });
  if (!res.ok) {
    throw new Error(`Failed to create image record: ${res.statusText}`);
  }
  return res.json();
}

export async function testIntegrationConnection(provider: string, url?: string): Promise<boolean> {
  try {
    const res = await fetch(`${API_BASE}/ai/integrations/test`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ provider, url })
    });
    return res.ok;
  } catch (e) {
    return false;
  }
}

export async function inspectComfyUIWorkflow(serverUrl: string, workflowJson: object): Promise<any> {
  const res = await fetch(`${API_BASE}/comfyui/workflow/inspect`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ workflow: workflowJson, server_url: serverUrl }),
  });
  if (!res.ok) {
    throw new Error(`Failed to inspect ComfyUI workflow: ${res.statusText}`);
  }
  return res.json();
}

export async function checkPromptVaultSimilarity(promptText: string): Promise<any> {
  const res = await fetch(`${API_BASE}/prompts/vault/similarity`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ prompt_text: promptText }),
  });
  if (!res.ok) {
    throw new Error(`Failed to check prompt vault similarity: ${res.statusText}`);
  }
  return res.json();
}

export interface SweepExecuteOptions {
  workflow?: Record<string, any>;
  targetNodeId?: string;
  seedNodeId?: string;
  prompts: string[];
  seedStrategy?: 'fixed' | 'random' | 'sequential';
  baseSeed?: number;
  steps?: number;
  cfg?: number;
  samplerName?: string;
  scheduler?: string;
  model?: string;
  clip?: string;
  vae?: string;
}

export async function executeComfyUISweep(options: SweepExecuteOptions): Promise<{ queued_count: number; job_results: any[] }> {
  const payload = {
    workflow: options.workflow,
    target_node_id: options.targetNodeId,
    seed_node_id: options.seedNodeId,
    prompts: options.prompts,
    seed_strategy: options.seedStrategy || 'sequential',
    base_seed: options.baseSeed ?? 42,
    steps: options.steps ?? 10,
    cfg: options.cfg ?? 1.0,
    sampler_name: options.samplerName ?? 'er_sde',
    scheduler: options.scheduler ?? 'beta',
    model: options.model ?? 'Mklan_Kea2_V1.safetensors',
    clip: options.clip ?? 'qwen3-vl-4b-heretic.safetensors',
    vae: options.vae ?? 'qwen_image_vae.safetensors'
  };

  const res = await fetch(`${API_BASE}/comfyui/execute-sweep`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });

  if (!res.ok) throw new Error(`Failed to execute ComfyUI sweep: ${res.statusText}`);
  return res.json();
}

export async function serializeASTToGraph(prompt: string): Promise<any> {
  const res = await fetch(`${API_BASE}/simulator/ast/serialize`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ prompt })
  });
  if (!res.ok) throw new Error(`Failed to serialize AST: ${res.statusText}`);
  return res.json();
}

export async function deserializeGraphToAST(graphObj: object): Promise<any> {
  const res = await fetch(`${API_BASE}/simulator/ast/deserialize`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ graph: graphObj }),
  });
  if (!res.ok) {
    throw new Error(`Failed to deserialize graph to AST: ${res.statusText}`);
  }
  return res.json();
}

export interface SweepResultItem {
  id?: number;
  filename: string;
  prompt_content?: string;
  seed?: number;
  steps?: number;
  cfg_scale?: number;
  sampler_name?: string;
  url?: string;
}

export async function syncRecentComfyOutputs(
  prefix: string = 'MatrixSweep',
  limit: number = 50,
  baseUrl?: string
): Promise<{ imported_count: number; items: SweepResultItem[] }> {
  const res = await fetch(`${API_BASE}/comfyui/sync-recent-outputs`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ prefix, limit, base_url: baseUrl })
  });
  if (!res.ok) throw new Error(`Failed to sync ComfyUI outputs: ${res.statusText}`);
  return res.json();
}



