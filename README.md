# hermes-webui

A browser web UI for the [Hermes Agent](https://hermes-agent.nousresearch.com)
gateway `api_server`. Chat with your agent from any device — phone, tablet, or
desktop — over TLS, with SSE token streaming, per-session model selection,
thinking-level control, and per-message text-to-speech.

It is **not** a terminal-in-an-iframe. It is a proper single-file React SPA
talking to the gateway's REST + SSE API through a tiny stateless proxy.

## Stack

```
Browser ──(TLS + basic auth, Caddy)──▶ proxy.py ──(Bearer key)──▶ hermes gateway api_server
        :8443  (Caddy reverse proxy)     :8650  (stdlib)           :8642  (Hermes)
```

- **`index.html`** — the SPA. A single HTML file with an inline React (UMD) app,
  a sidebar with a grouped session list, a model selector, a thinking-level
  control, markdown rendering, copy buttons, and a read-aloud (TTS) button
  under every message. Self-hosted `react.min.js` / `react-dom.min.js` are
  referenced (no CDN, no runtime Babel) so it works on restricted networks.
- **`build.js`** — transpiles the inline JSX with Babel and rewrites the script
  tags to local files, emitting `deploy.index.html` + `app.js`.
- **`proxy.py`** — stdlib-only SSE proxy. Holds the `API_SERVER_KEY` server-side
  (read from the Hermes `.env` at startup) so the browser never sees it, and
  forwards `/api/*` to the gateway unbuffered.
- **Favicon + PWA** — the Hermes desktop logo as a full favicon set
  (`.ico`, 32/192/512 png) plus `apple-touch-icon.png` and `site.webmanifest`,
  so the tab shows the logo and the app can be installed as a PWA.

## Files

| File | Purpose |
|------|---------|
| `index.html` | SPA source of truth (inline JSX + self-hosted React refs). |
| `app.js` | Compiled JS bundle (build artifact). |
| `deploy.index.html` | Deployed HTML (local script tags, no Babel). |
| `react.min.js` / `react-dom.min.js` | Self-hosted React 18 UMD runtime. |
| `proxy.py` | Stateless stdlib SSE proxy (key injected server-side). |
| `build.js` | JSX → JS build script (Babel). |
| `favicon.*`, `apple-touch-icon.png`, `site.webmanifest` | Tab icon + PWA manifest. |

## Build

```bash
npm install        # pulls @babel/core + @babel/preset-react
npm run build      # → deploy.index.html + app.js
```

`build.js` fails loudly if the deployed HTML still references the CDN or a
`text/babel` runtime tag.

## Deploy (reference — this box)

The live stack on the Hermes host is:

- **Caddy** on `:8443` — TLS + HTTP basic auth, serves the web root and
  reverse-proxies `/api/*` to the local proxy.
- **`proxy.py`** on `127.0.0.1:8650` — run as a systemd user service; reads
  `API_SERVER_KEY` from the Hermes `.env` at startup.
- **Hermes gateway `api_server`** on `127.0.0.1:8642` — enabled in
  `config.yaml` under `gateway.api_server`.

Deploy the built assets into the web root (e.g. `/var/www/hermes-webui/`):
`deploy.index.html` → `index.html`, plus `app.js`, the React libs, and the
icon/PWA files.

> The exact ports, host paths, and the Caddy/systemd unit files are host
> specifics. This repo contains **no secrets** — see "Secrets" below.

## Secrets

Nothing secret is committed.

- The **`API_SERVER_KEY`** is read by `proxy.py` from the Hermes `.env` at
  runtime. It is not in this repo.
- The **basic-auth credentials** live in the host's Caddyfile, not here.
- The SPA discovers its API origin from `location.origin` (the host it is
  served from), so it carries no hardcoded keys, tokens, endpoints, or credentials.

If you self-host: keep `API_SERVER_KEY` and your Caddy basic-auth password
out of version control.

## License

MIT.
