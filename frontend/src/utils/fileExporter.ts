/**
 * Ensures filename ends with .txt and removes invalid filesystem characters.
 */
export function sanitizeFilename(name: string, fallback = 'export.txt'): string {
  if (!name || !name.trim()) return fallback;

  let cleaned = name.trim().replace(/[/\\?%*:|"<>]/g, '_');
  if (!cleaned.toLowerCase().endsWith('.txt')) {
    cleaned += '.txt';
  }
  return cleaned;
}

/**
 * Triggers a browser download of text content as a .txt file.
 */
export function exportAsTxtFile(filename: string, content: string): void {
  const finalName = sanitizeFilename(filename);
  const blob = new Blob([content], { type: 'text/plain;charset=utf-8' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = finalName;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}
