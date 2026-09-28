import { test, afterEach } from 'node:test';
import assert from 'node:assert/strict';
import { defaultPreferences, readPreferences, savePreferences } from './preferences.js';

const originalStorage = globalThis.localStorage;
afterEach(() => { globalThis.localStorage = originalStorage; });

test('guest display settings survive storage and reload', () => {
  const storage = new Map();
  globalThis.localStorage = { getItem: key => storage.get(key), setItem: (key, value) => storage.set(key, value) };
  const settings = { theme: 'dark', text_size: 'large', high_contrast: true, reduced_motion: true };
  assert.equal(savePreferences(settings), true);
  assert.deepEqual(readPreferences(), settings);
});

test('invalid stored preferences use safe defaults', () => {
  for (const value of ['invalid JSON', 'null', '{"theme":"invalid","text_size":"huge","high_contrast":"yes"}']) {
    globalThis.localStorage = { getItem: () => value };
    assert.deepEqual(readPreferences(), defaultPreferences);
  }
});

test('blocked browser storage does not prevent accessibility settings', () => {
  globalThis.localStorage = { getItem: () => { throw new Error('blocked'); }, setItem: () => { throw new Error('blocked'); } };
  assert.deepEqual(readPreferences(), defaultPreferences);
  assert.equal(savePreferences(defaultPreferences), false);
});
