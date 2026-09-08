// Build the Hermes Web UI deploy bundle (no CDN / no runtime Babel).
//
// Source of truth : <repo>/index.html  (references local react.min.js +
//                   react-dom.min.js and an inline <script type="text/babel">
//                   JSX block).
// Output          : <repo>/deploy.index.html + <repo>/app.js
//
// Usage:
//   npm install        # once, pulls @babel/core + @babel/preset-react
//   node build.js
//
// build.js transpiles the inline JSX with Babel and rewrites the script
// tags so the deployed page loads only local files:
//   - /react.min.js
//   - /react-dom.min.js
//   - /app.js
// No Babel at runtime, no CDN — phone-proof on restricted networks.
//
// After building, copy deploy.index.html -> index.html and app.js into your
// web root (e.g. /var/www/hermes-webui/). See README "Deploy".

const fs = require('fs');
const path = require('path');
const babel = require('@babel/core');

// Resolve the repo root from this script's location (portable).
const SRC = __dirname;

function read(p) { return fs.readFileSync(p, 'utf8'); }

let html = read(path.join(SRC, 'index.html'));

// 1. Transpile the inline JSX.
const m = html.match(/<script type="text\/babel">([\s\S]*?)<\/script>/);
if (!m) { console.error('ERROR: no <script type="text/babel"> found in index.html'); process.exit(1); }
const appJs = babel.transformSync(m[1], {
  presets: [['@babel/preset-react']],
  filename: 'app.jsx',
}).code;

// 2. Build the deployed HTML: swap CDN/babel script tags for local ones.
let out = html
  .replace(/<script[^>]*unpkg\.com\/react@18[^>]*><\/script>/, '<script src="/react.min.js"></script>')
  .replace(/<script[^>]*unpkg\.com\/react-dom@18[^>]*><\/script>\s*/, '<script src="/react-dom.min.js"></script>\n')
  .replace(/<script[^>]*unpkg\.com\/@babel\/standalone[^>]*><\/script>\s*/, '')
  .replace(/<script type="text\/babel">[\s\S]*?<\/script>/, '<script src="/app.js"></script>');

const bad = /unpkg\.com|text\/babel/.test(out);

console.log('app.js bytes:', appJs.length);
console.log('deploy html still refs cdn/babel?', bad);
if (bad) {
  console.error('=== remaining refs ===');
  out.split('\n').filter(l => /unpkg|text\/babel/.test(l)).forEach(l => console.error('  ' + l.trim()));
  process.exit(1);
}
fs.writeFileSync(path.join(SRC, 'deploy.index.html'), out);
fs.writeFileSync(path.join(SRC, 'app.js'), appJs);
console.log('wrote deploy.index.html + app.js to repo root');
