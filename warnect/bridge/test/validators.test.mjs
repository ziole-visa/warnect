import test from 'node:test';
import assert from 'node:assert/strict';
import { validateJid, validateText, validateLimit } from '../lib/validators.js';

test('validateJid accepts valid jids', () => {
  assert.equal(validateJid('6281234567890@s.whatsapp.net'), '6281234567890@s.whatsapp.net');
  assert.equal(validateJid('123456789-987654321@g.us'), '123456789-987654321@g.us');
  assert.equal(validateJid('123@lid'), '123@lid');
});

test('validateJid rejects invalid jids', () => {
  assert.throws(() => validateJid('not-a-jid'));
  assert.throws(() => validateJid('123@s.whatsapp.net.evil.com'));
  assert.throws(() => validateJid(''));
});

test('validateText enforces non-empty and max length', () => {
  assert.equal(validateText('hello'), 'hello');
  assert.throws(() => validateText(''));
  assert.throws(() => validateText('x'.repeat(10), 5));
});

test('validateLimit clamps valid numbers', () => {
  assert.equal(validateLimit('10', 100, 1000), 10);
  assert.throws(() => validateLimit(0));
  assert.throws(() => validateLimit(1001));
});
