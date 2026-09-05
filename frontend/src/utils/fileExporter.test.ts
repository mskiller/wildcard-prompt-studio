import { describe, it, expect } from 'vitest';
import { sanitizeFilename } from './fileExporter';

describe('sanitizeFilename', () => {
  it('adds .txt extension if missing', () => {
    expect(sanitizeFilename('my_wildcard')).toBe('my_wildcard.txt');
  });

  it('preserves existing .txt extension', () => {
    expect(sanitizeFilename('prompt.txt')).toBe('prompt.txt');
  });

  it('replaces unsafe characters in filenames', () => {
    expect(sanitizeFilename('my/unsafe:file?name')).toBe('my_unsafe_file_name.txt');
  });

  it('uses default fallback if empty', () => {
    expect(sanitizeFilename('')).toBe('export.txt');
  });
});
