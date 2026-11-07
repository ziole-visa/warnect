import readline from 'node:readline';

const rl = readline.createInterface({ input: process.stdin });
rl.on('line', (line) => {
  let req;
  try { req = JSON.parse(line); } catch { return; }
  if (req.cmd === 'start') {
    process.stdout.write(JSON.stringify({ type: 'event', event: 'started', data: { fake: true } }) + '\n');
    process.stdout.write(JSON.stringify({ type: 'response', id: req.id, ok: true, data: { status: 'starting' } }) + '\n');
    setTimeout(() => process.exit(1), 200);
  } else {
    process.stdout.write(JSON.stringify({ type: 'response', id: req.id, ok: true, data: {} }) + '\n');
  }
});
