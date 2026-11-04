const JID_RE = /^\d+(-[\d]+)?@(s\.whatsapp\.net|g\.us|broadcast|lid|newsletter)$/;

export function validateJid(jid) {
  if (typeof jid !== 'string' || !JID_RE.test(jid)) {
    throw new Error(`invalid jid: ${jid}`);
  }
  return jid;
}

export function validateText(text, maxLength = 65536) {
  if (typeof text !== 'string' || text.length === 0) {
    throw new Error('text must be a non-empty string');
  }
  if (text.length > maxLength) {
    throw new Error(`text too long (max ${maxLength})`);
  }
  return text;
}

export function validateLimit(value, def = 100, max = 1000) {
  const n = Number(value ?? def);
  if (!Number.isFinite(n) || n < 1 || n > max) {
    throw new Error(`limit must be between 1 and ${max}`);
  }
  return Math.floor(n);
}

export function parseBool(value, def = false) {
  if (value === undefined || value === null) return def;
  return value === true || value === 'true' || value === 1 || value === '1';
}
