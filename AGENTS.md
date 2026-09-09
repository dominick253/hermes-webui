# hermes-webui — Workspace Contract

DOX CHAIN: `~/.hermes/AGENTS.md` → `/home/dom/AGENTS.md` → this file.
Inherits the parent workspace rules (Senda git identity = dominick253 only,
never hand-edit `config.yaml`, browser-autonomy ladder, MCP docs-first).

## What this is
Single-file React 18 web UI for the **Hermes gateway `api_server`** platform
(chat with your agent from any device). Not the `:9119` dashboard (that embeds
the TUI — the user rejects it). Source of truth: `index.html` (inline JSX) +
`proxy.py` (stdlib SSE proxy). Full operational detail lives in the
`hermes-webui` skill.

## Build & deploy
```bash
npm install        # @babel/core + @babel/preset-react
node build.js      # transpiles inline JSX -> deploy.index.html + app.js
node --check app.js
# deploy (live host): sudo cp deploy.index.html -> /var/www/hermes-webui/index.html,
#                     sudo cp app.js react*.js favicon* site.webmanifest -> /var/www/hermes-webui/
#                     sudo cp -r fonts -> /var/www/hermes-webui/fonts   (self-hosted Inter + JetBrains Mono)
#                     sudo chown root:www-data on all
```
`/var/www/hermes-webui` is root-owned (served by caddy user `caddy`); build
artifacts land in this `dom`-owned dir first, then `sudo cp`.

## Conventions
- **No CDN / no runtime Babel** — self-hosted `react.min.js` + `react-dom.min.js`;
  `build.js` fails loudly if a `unpkg.com` or `text/babel` tag survives.
- **SPA API base is `location.protocol + '//' + location.host`** — never hardcode
  an IP/host in the SPA; it must stay portable.
- **proxy.py reads `API_SERVER_KEY` from the Hermes `.env` at runtime** — never a
  literal key, never committed.
- **Model lock: send `{model}` only, never `{provider}`** (custom AMD provider
  reports runtime `custom` ≠ declared `amd`; provider-inclusive locks 400).
- Caddy `/api/*` needs `flush_interval -1`; proxy must read upstream SSE
  line-by-line (`for line in resp:`) and send `Connection: close`.

## Secrets (keep OUT of this repo)
- `API_SERVER_KEY` (Hermes `.env`),
- Caddy basic-auth password (Caddyfile bcrypt hash).
- This repo is PUBLIC (`dominick253/hermes-webui`) — before any push, grep every
  committed file for `ghp_`, `sk-`, `API_SERVER_KEY=<value>`, private IPs, and
  `.env`/credentials; verify on the public side via `gh api .../contents/<f>`.

## Build artifacts
`app.js` and `deploy.index.html` are gitignored (regenerable via `npm run build`);
the repo is source-only.
