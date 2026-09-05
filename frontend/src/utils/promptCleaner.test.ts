import { describe, it, expect } from 'vitest';
import { cleanPromptWeights } from './promptCleaner';

describe('cleanPromptWeights', () => {
  it('removes weighted tags with float weights', () => {
    expect(cleanPromptWeights('(prompt:1.2)')).toBe('prompt');
    expect(cleanPromptWeights('(a photo of a cat:0.85)')).toBe('a photo of a cat');
  });

  it('removes negative weights', () => {
    expect(cleanPromptWeights('(blurry:-0.5)')).toBe('blurry');
  });

  it('removes plain parentheses around terms', () => {
    expect(cleanPromptWeights('(cyberpunk city)')).toBe('cyberpunk city');
    expect(cleanPromptWeights('((masterpiece:1.2), high quality)')).toBe('masterpiece, high quality');
  });

  it('handles multiple weighted terms in prompt', () => {
    const input = '(red car:1.1), (blue sky:0.9), masterpiece';
    expect(cleanPromptWeights(input)).toBe('red car, blue sky, masterpiece');
  });

  it('returns empty string for empty input', () => {
    expect(cleanPromptWeights('')).toBe('');
  });
});
