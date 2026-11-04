import test from 'node:test';
import assert from 'node:assert/strict';
import { parseLine, respond, respondError, createEmitter } from '../lib/protocol.js';

test('parseLine parses valid request', () => {
  const req = parseLine('{"type":"request","id":"1","cmd":"ping"}');
  assert.equal(req.cmd, 'ping');
  assert.equal(req.id, '1');
});

test('parseLine rejects invalid payloads', () => {
  assert.throws(() => parseLine('not json'));
  assert.throws(() => parseLine('{"type":"event"}'));
  assert.throws(() => parseLine('{"type":"request","cmd":"ping"}'));
});

test('respond writes structured response', () => {
  const lines = [];
  respond((l) => lines.push(l), '1', { pong: true });
  const obj = JSON.parse(lines[0]);
  assert.equal(obj.type, 'response');
  assert.equal(obj.ok, true);
  assert.equal(obj.id, '1');
});

test('respondError writes structured error', () => {
  const lines = [];
  respondError((l) => lines.push(l), '2', 'bad', 'nope');
  const obj = JSON.parse(lines[0]);
  assert.equal(obj.ok, false);
  assert.equal(obj.error.code, 'bad');
});

test('createEmitter emits events', () => {
  const lines = [];
  const emit = createEmitter((l) => lines.push(l));
  emit('qr', 'abc');
  const obj = JSON.parse(lines[0]);
  assert.equal(obj.type, 'event');
  assert.equal(obj.event, 'qr');
  assert.equal(obj.data, 'abc');
});
