import readline from 'node:readline';

function write(obj) {
  process.stdout.write(JSON.stringify(obj) + '\n');
}

const rl = readline.createInterface({ input: process.stdin });
rl.on('line', (line) => {
  let req;
  try { req = JSON.parse(line); } catch { return; }
  const { id, cmd } = req;
  if (cmd === 'start') {
    write({ type: 'event', event: 'started', data: { fake: true } });
    write({ type: 'response', id, ok: true, data: { status: 'starting' } });
  } else if (cmd === 'ping') {
    write({ type: 'response', id, ok: true, data: { pong: true } });
  } else if (cmd === 'send_text') {
    write({ type: 'event', event: 'message', data: { text: req.text } });
    write({ type: 'response', id, ok: true, data: { sent: true } });
  } else if (cmd === 'request_pairing_code') {
    write({ type: 'response', id, ok: true, data: { code: 'ABCD-1234' } });
  } else if (cmd === 'send_presence') {
    write({ type: 'response', id, ok: true, data: { presence: req.presence, jid: req.jid } });
  } else if (cmd === 'send_read') {
    write({ type: 'response', id, ok: true, data: { read: true, messageId: req.messageId } });
  } else if (cmd === 'download_media') {
    write({
      type: 'response',
      id,
      ok: true,
      data: { base64: Buffer.from('media-bytes').toString('base64'), size: 11, mimetype: 'image/png' },
    });
  } else if (cmd === 'get_profile_picture') {
    write({ type: 'response', id, ok: true, data: { url: 'https://example.com/p.jpg' } });
  } else if (cmd === 'get_groups') {
    write({ type: 'response', id, ok: true, data: { groups: [], total: 0 } });
  } else if (cmd === 'is_on_whatsapp') {
    write({ type: 'response', id, ok: true, data: { exists: true, jid: '123@s.whatsapp.net' } });
  } else if (cmd === 'send_reaction') {
    write({ type: 'response', id, ok: true, data: { reacted: true, messageId: req.messageId } });
  } else if (cmd === 'reply_message') {
    write({ type: 'response', id, ok: true, data: { sent: true, jid: req.jid, quoted: !!req.quotedId } });
  } else if (cmd === 'group_create') {
    write({ type: 'response', id, ok: true, data: { group: { id: '123@g.us', subject: req.subject } } });
  } else if (cmd === 'group_add_participants') {
    write({ type: 'response', id, ok: true, data: { result: [{ status: '200' }] } });
  } else if (cmd === 'list_methods') {
    write({ type: 'response', id, ok: true, data: { methods: ['sendMessage', 'groupCreate'] } });
  } else if (cmd === 'invoke') {
    write({ type: 'response', id, ok: true, data: { method: req.method, result: { echoed: req.args } } });
  } else if (cmd === 'slow') {
    // intentionally never responds
  } else if (cmd === 'stop') {
    write({ type: 'response', id, ok: true, data: { stopping: true } });
    setTimeout(() => process.exit(0), 10);
  } else {
    write({ type: 'response', id, ok: false, error: { code: 'unknown_command', message: cmd } });
  }
});
