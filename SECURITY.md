# Security Policy

## Supported versions

| Version | Supported |
| ------- | --------- |
| 0.2.x   | ✅        |

## Reporting a vulnerability

Please do not open a public issue for security problems. Contact the maintainer
through the repository's private security advisory feature or the contact listed
on the GitHub profile.

Include:

- affected version
- steps to reproduce
- impact assessment
- suggested fix (if any)

## Hardening notes

- The bridge communicates over local stdio only; no TCP port is opened.
- Node dependencies are pinned through `package-lock.json` and installed with
  `npm ci`.
- Session/auth directory is created with `0700` permissions.
- Inputs are validated before reaching the WhatsApp socket.
- Outgoing sends are rate-limited by default (`min_send_interval`).
