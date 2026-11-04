import { makeWASocket, useMultiFileAuthState, DisconnectReason } from 'arsya-baileys-open';
import readline from 'node:readline';
import fs from 'node:fs';

const authDir = process.argv[2] || './auth';
let sock = null;

function send(obj) {
  process.stdout.write(JSON.stringify(obj) + '\n');
}

const rl = readline.createInterface({ input: process.stdin });
rl.on('line', async (line) => {
  let cmd;
  try { cmd = JSON.parse(line); } catch { return; }

  try {
    if (cmd.cmd === 'start') {
      const { state, saveCreds } = await useMultiFileAuthState(authDir);
      sock = makeWASocket({ auth: state, printQRInTerminal: false });
      sock.ev.on('creds.update', saveCreds);
      sock.ev.on('connection.update', (u) => {
        if (u.qr) send({ event: 'qr', data: u.qr });
        if (u.connection) send({ event: 'connection', data: u.connection });
        if (u.lastDisconnect?.error) {
          send({ event: 'error', data: String(u.lastDisconnect.error) });
        }
      });
      sock.ev.on('messages.upsert', (m) => {
        for (const msg of m.messages || []) {
          if (!msg.message) continue;
          const text = msg.message.conversation
            || msg.message.extendedTextMessage?.text
            || null;
          send({ event: 'message', data: { key: msg.key, text, message: msg.message } });
        }
      });
      send({ event: 'started' });
    } else if (cmd.cmd === 'sendText') {
      if (!sock) throw new Error('socket not started');
      await sock.sendMessage(cmd.jid, { text: cmd.text });
      send({ event: 'sent', data: { jid: cmd.jid } });
    } else if (cmd.cmd === 'stop') {
      try { sock?.end(); } catch {}
      process.exit(0);
    } else {
      send({ event: 'error', data: 'unknown command: ' + cmd.cmd });
    }
  } catch (e) {
    send({ event: 'error', data: String(e?.message || e) });
  }
});

process.on('SIGTERM', () => { try { sock?.end(); } catch {} process.exit(0); });
process.on('SIGINT', () => { try { sock?.end(); } catch {} process.exit(0); });
