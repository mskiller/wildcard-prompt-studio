/**
 * Utility to strip SD-style weight syntax e.g. (tag:1.2) -> tag and (tag) -> tag
 */
export function cleanPromptWeights(prompt: string): string {
  if (!prompt) return '';

  let cleaned = prompt;

  // 1. Remove weighted syntax: (tag:1.2) -> tag or (tag: 0.8) -> tag
  let previous = '';
  while (previous !== cleaned) {
    previous = cleaned;
    cleaned = cleaned.replace(/\(\s*([^():]+?)\s*:\s*-?\d+(?:\.\d+)?\s*\)/g, '$1');
  }

  // 2. Remove plain outer parentheses: ((tag)) -> tag, (tag) -> tag
  previous = '';
  while (previous !== cleaned) {
    previous = cleaned;
    cleaned = cleaned.replace(/\(\s*([^()]+?)\s*\)/g, '$1');
  }

  // 3. Remove any stray colon weight suffixes like :1.2 if outside parentheses
  cleaned = cleaned.replace(/:\s*-?\d+(?:\.\d+)?\b/g, '');

  // 4. Clean up multiple spaces and empty/dangling commas
  cleaned = cleaned
    .replace(/,\s*,/g, ',')
    .replace(/^\s*,\s*|\s*,\s*$/g, '')
    .replace(/\s{2,}/g, ' ')
    .trim();

  return cleaned;
}
