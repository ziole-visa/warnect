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
  } else if (cmd === 'slow') {
    // intentionally never responds
  } else if (cmd === 'stop') {
    write({ type: 'response', id, ok: true, data: { stopping: true } });
    setTimeout(() => process.exit(0), 10);
  } else {
    write({ type: 'response', id, ok: false, error: { code: 'unknown_command', message: cmd } });
  }
});
