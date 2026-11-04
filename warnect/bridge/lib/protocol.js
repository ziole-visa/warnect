export function createEmitter(writeLine) {
  return function emit(event, data = null) {
    writeLine(JSON.stringify({ type: 'event', event, data }));
  };
}

export function respond(writeLine, id, data = null) {
  writeLine(JSON.stringify({ type: 'response', id, ok: true, data }));
}

export function respondError(writeLine, id, code, message) {
  writeLine(JSON.stringify({ type: 'response', id, ok: false, error: { code, message } }));
}

export function parseLine(line) {
  const trimmed = String(line || '').trim();
  if (!trimmed) return null;
  const obj = JSON.parse(trimmed);
  if (!obj || typeof obj !== 'object') throw new Error('payload must be an object');
  if (obj.type !== 'request') throw new Error('unsupported message type');
  if (obj.id === undefined || obj.id === null) throw new Error('request id is required');
  if (typeof obj.cmd !== 'string' || !obj.cmd) throw new Error('request cmd is required');
  return obj;
}
