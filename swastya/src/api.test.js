import { test, afterEach } from 'node:test';
import assert from 'node:assert/strict';
import { api, setToken } from './api.js';

const originalFetch = globalThis.fetch;
const originalWindow = globalThis.window;
afterEach(() => { globalThis.fetch = originalFetch; globalThis.window = originalWindow; setToken(null); });

function unauthorized() {
  return { ok: false, status: 401, json: async () => ({ detail: 'Invalid email or password' }) };
}

test('incorrect login credentials do not dispatch session expiration', async () => {
  const events = [];
  globalThis.window = { dispatchEvent: event => events.push(event.type) };
  globalThis.fetch = async () => unauthorized();
  for (const token of [null, 'existing-session']) {
    setToken(token);
    await assert.rejects(api('/auth/login', { method: 'POST' }), /Invalid email or password/);
  }
  assert.deepEqual(events, []);
});

test('expired authenticated requests still dispatch session expiration', async () => {
  const events = [];
  globalThis.window = { dispatchEvent: event => events.push(event.type) };
  globalThis.fetch = async () => unauthorized();
  setToken('expired-session');
  await assert.rejects(api('/profile'));
  assert.deepEqual(events, ['session-expired']);
});

test('a late failure from an old session does not log out a new session', async () => {
  const events = [];
  globalThis.window = { dispatchEvent: event => events.push(event.type) };
  let finish;
  globalThis.fetch = () => new Promise(resolve => { finish = resolve; });
  setToken('old-session');
  const request = api('/profile');
  setToken('new-session');
  finish(unauthorized());
  await assert.rejects(request);
  assert.deepEqual(events, []);
});
