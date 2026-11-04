import { makeWASocket, useMultiFileAuthState, DisconnectReason, getContentType, downloadMediaMessage } from 'arsya-baileys-open';
import readline from 'node:readline';
import fs from 'node:fs';
import path from 'node:path';
import { validateJid, validateText, validateLimit } from './lib/validators.js';
import { createEmitter, respond, respondError, parseLine } from './lib/protocol.js';

const authDir = path.resolve(process.argv[2] || './auth');
const LOG_LEVELS = { error: 0, warn: 1, info: 2, debug: 3 };
const logLevel = LOG_LEVELS[(process.argv[3] || process.env.WARNECT_LOG_LEVEL || 'info').toLowerCase()] ?? 2;

const MESSAGE_STORE_LIMIT = 500;
const messageStore = new Map();

let sock = null;
let stopping = false;
let connecting = false;
let connected = false;
let reconnectAttempts = 0;
let reconnectTimer = null;

const writeLine = (line) => process.stdout.write(line + '\n');
const emit = createEmitter(writeLine);

function log(level, ...args) {
  if (LOG_LEVELS[level] <= logLevel) {
    console.error(`[warnect-bridge:${level}]`, ...args);
  }
}

function ensureAuthDir() {
  fs.mkdirSync(authDir, { recursive: true, mode: 0o700 });
  try { fs.chmodSync(authDir, 0o700); } catch {}
}

function extractText(msg) {
  const m = msg.message || {};
  const type = getContentType(m);
  if (!type) return null;
  const content = m[type];
  if (!content) return null;
  if (type === 'conversation') return m.conversation;
  if (type === 'extendedTextMessage') return content.text ?? null;
  if (type === 'imageMessage' || type === 'videoMessage') return content.caption ?? null;
  if (type === 'documentMessage') return content.caption ?? content.fileName ?? null;
  return null;
}

function storeMessage(msg) {
  const id = msg?.key?.id;
  if (!id) return;
  messageStore.set(id, msg);
  if (messageStore.size > MESSAGE_STORE_LIMIT) {
    const oldest = messageStore.keys().next().value;
    if (oldest !== undefined) messageStore.delete(oldest);
  }
}

function parseIncoming(msg) {
  const m = msg.message || {};
  const type = getContentType(m);
  const content = type ? m[type] : null;
  const key = msg.key || {};
  const jid = key.remoteJid || null;
  return {
    id: key.id || null,
    chat: jid,
    sender: key.participant || (key.fromMe ? null : jid),
    fromMe: !!key.fromMe,
    isGroup: !!jid && jid.endsWith('@g.us'),
    type: type || null,
    text: extractText(msg),
    pushName: msg.pushName || null,
    timestamp: msg.messageTimestamp || null,
    hasMedia: !!content && typeof content === 'object' && 'mimetype' in content,
    fileName: content?.fileName || null,
    mimetype: content?.mimetype || null,
  };
}

async function connect() {
  if (stopping) return;
  if (connecting) return;
  connecting = true;
  try {
    ensureAuthDir();
    const { state, saveCreds } = await useMultiFileAuthState(authDir);
    sock = makeWASocket({
      auth: state,
      printQRInTerminal: false,
      syncFullHistory: false,
      markOnlineOnConnect: false,
      generateHighQualityLinkPreview: false,
    });

    sock.ev.on('creds.update', saveCreds);

    sock.ev.on('connection.update', (update) => {
      if (update.qr) emit('qr', update.qr);
      if (update.connection) emit('connection', { status: update.connection });

      if (update.connection === 'open') {
        connected = true;
        reconnectAttempts = 0;
        emit('ready', { user: sock?.user || null });
        log('info', 'connected');
      }

      if (update.connection === 'close') {
        connected = false;
        const statusCode = update.lastDisconnect?.error?.output?.statusCode ?? null;
        emit('connection', { status: 'close', code: statusCode });
        if (!stopping && statusCode !== DisconnectReason.loggedOut) {
          scheduleReconnect();
        } else if (statusCode === DisconnectReason.loggedOut) {
          emit('error', { code: 'logged_out', message: 'session logged out' });
        }
      }
    });

    sock.ev.on('messages.upsert', (event) => {
      for (const msg of event.messages || []) {
        if (!msg?.message) continue;
        try {
          storeMessage(msg);
          emit('message', parseIncoming(msg));
        } catch (e) {
          emit('error', { code: 'message_parse_failed', message: String(e?.message || e) });
        }
      }
    });

    emit('started', { authDir });
  } finally {
    connecting = false;
  }
}

function scheduleReconnect() {
  if (stopping || reconnectTimer) return;
  const delay = Math.min(30000, 1000 * Math.pow(2, reconnectAttempts));
  reconnectAttempts += 1;
  emit('reconnect', { attempt: reconnectAttempts, delay });
  log('warn', `reconnect in ${delay}ms (attempt ${reconnectAttempts})`);
  reconnectTimer = setTimeout(() => {
    reconnectTimer = null;
    connect().catch((e) => {
      emit('error', { code: 'reconnect_failed', message: String(e?.message || e) });
      scheduleReconnect();
    });
  }, delay);
}

async function handleCommand(req) {
  const { id, cmd } = req;
  try {
    switch (cmd) {
      case 'start': {
        await connect();
        respond(writeLine, id, { status: 'starting' });
        break;
      }
      case 'ping': {
        respond(writeLine, id, { pong: true, connected });
        break;
      }
      case 'send_text': {
        if (!sock) throw new Error('socket not started');
        validateJid(req.jid);
        validateText(req.text);
        await sock.sendMessage(req.jid, { text: req.text });
        respond(writeLine, id, { sent: true, jid: req.jid });
        break;
      }
      case 'send_image': {
        if (!sock) throw new Error('socket not started');
        validateJid(req.jid);
        const content = {};
        if (req.url) content.image = { url: req.url };
        else if (req.path) content.image = fs.readFileSync(path.resolve(req.path));
        else throw new Error('send_image requires url or path');
        if (req.caption) validateText(req.caption);
        if (req.caption) content.caption = req.caption;
        await sock.sendMessage(req.jid, content);
        respond(writeLine, id, { sent: true, jid: req.jid });
        break;
      }
      case 'send_document': {
        if (!sock) throw new Error('socket not started');
        validateJid(req.jid);
        if (!req.path) throw new Error('send_document requires path');
        const docPath = path.resolve(req.path);
        const stat = fs.statSync(docPath);
        if (!stat.isFile()) throw new Error('path is not a file');
        const content = {
          document: fs.readFileSync(docPath),
          fileName: req.filename || path.basename(docPath),
          mimetype: req.mimetype || 'application/octet-stream',
        };
        if (req.caption) content.caption = req.caption;
        await sock.sendMessage(req.jid, content);
        respond(writeLine, id, { sent: true, jid: req.jid });
        break;
      }
      case 'get_groups': {
        if (!sock) throw new Error('socket not started');
        const limit = validateLimit(req.limit, 100, 1000);
        const groups = await sock.groupFetchAllParticipating();
        const list = Object.values(groups).slice(0, limit).map((g) => ({
          id: g.id,
          subject: g.subject,
          participants: g.participants?.length ?? 0,
          creation: g.creation ?? null,
        }));
        respond(writeLine, id, { groups: list, total: Object.keys(groups).length });
        break;
      }
      case 'get_profile_picture': {
        if (!sock) throw new Error('socket not started');
        validateJid(req.jid);
        const url = await sock.profilePictureUrl(req.jid, req.pictureType || 'image');
        respond(writeLine, id, { url: url || null });
        break;
      }
      case 'is_on_whatsapp': {
        if (!sock) throw new Error('socket not started');
        if (!/^\d{6,20}$/.test(String(req.number || ''))) throw new Error('invalid number');
        const [result] = await sock.onWhatsApp(req.number);
        respond(writeLine, id, { exists: !!result?.exists, jid: result?.jid || null });
        break;
      }
      case 'request_pairing_code': {
        if (!sock) throw new Error('socket not started');
        const number = String(req.number || '').replace(/\D/g, '');
        if (!/^\d{6,20}$/.test(number)) throw new Error('invalid number');
        const code = await sock.requestPairingCode(number, req.customCode || undefined);
        respond(writeLine, id, { code });
        break;
      }
      case 'send_presence': {
        if (!sock) throw new Error('socket not started');
        validateJid(req.jid);
        const allowed = new Set(['composing', 'recording', 'paused', 'available', 'unavailable']);
        if (!allowed.has(req.presence)) throw new Error('invalid presence');
        await sock.sendPresenceUpdate(req.presence, req.jid);
        respond(writeLine, id, { presence: req.presence, jid: req.jid });
        break;
      }
      case 'send_read': {
        if (!sock) throw new Error('socket not started');
        validateJid(req.jid);
        if (!req.messageId) throw new Error('message id is required');
        await sock.readMessages([{ remoteJid: req.jid, id: req.messageId, participant: req.participant }]);
        respond(writeLine, id, { read: true, messageId: req.messageId });
        break;
      }
      case 'download_media': {
        if (!sock) throw new Error('socket not started');
        const raw = messageStore.get(req.messageId);
        if (!raw) throw new Error('message not found in local store');
        const buffer = await downloadMediaMessage(raw, 'buffer', {});
        if (!buffer || !buffer.length) throw new Error('media download failed');
        const type = getContentType(raw.message || {});
        const content = type ? raw.message[type] : null;
        respond(writeLine, id, {
          base64: buffer.toString('base64'),
          size: buffer.length,
          mimetype: content?.mimetype || null,
          fileName: content?.fileName || null,
          type: type || null,
        });
        break;
      }
      case 'logout': {
        if (sock) await sock.logout();
        respond(writeLine, id, { loggedOut: true });
        break;
      }
      case 'stop': {
        stopping = true;
        respond(writeLine, id, { stopping: true });
        setTimeout(() => shutdown(0), 50);
        break;
      }
      default:
        respondError(writeLine, id, 'unknown_command', `unknown command: ${cmd}`);
    }
  } catch (e) {
    respondError(writeLine, id, e?.code || 'command_failed', String(e?.message || e));
  }
}

function shutdown(code = 0) {
  stopping = true;
  if (reconnectTimer) {
    clearTimeout(reconnectTimer);
    reconnectTimer = null;
  }
  try { sock?.end(undefined); } catch {}
  process.exit(code);
}

const rl = readline.createInterface({ input: process.stdin });
rl.on('line', (line) => {
  let req;
  try {
    req = parseLine(line);
  } catch (e) {
    emit('error', { code: 'invalid_request', message: String(e?.message || e) });
    return;
  }
  if (!req) return;
  handleCommand(req);
});

process.on('SIGTERM', () => shutdown(0));
process.on('SIGINT', () => shutdown(0));
process.on('uncaughtException', (e) => {
  emit('error', { code: 'uncaught_exception', message: String(e?.message || e) });
  log('error', e);
});
process.on('unhandledRejection', (e) => {
  emit('error', { code: 'unhandled_rejection', message: String(e?.message || e) });
  log('error', e);
});
