const API_BASE = 'http://localhost:8000/api/v1';

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
