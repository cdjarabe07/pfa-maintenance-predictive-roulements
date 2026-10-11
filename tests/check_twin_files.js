// Simule le mode « Analyser mes fichiers » du tableau de bord sur un dossier brut (DOM factice).
// Usage : node tests/check_twin_files.js <dossier_brut> [colonne]
const fs = require('fs'), path = require('path');
const dir = process.argv[2], col = process.argv[3] || '0';

// Objet factice universel : toute propriété / tout appel renvoie un objet factice
const fake = () => new Proxy(function(){}, {
  get: (t, k) => k === Symbol.toPrimitive ? (() => 0) : k in t ? t[k] : (t[k] = fake()),
  set: (t, k, v) => { t[k] = v; return true; },
  apply: () => fake(), construct: () => fake() });
const els = {};
global.document = fake();
document.getElementById = id => els[id] || (els[id] = Object.assign(fake(), {
  id, value: id === 'col' ? col : '', textContent: '', innerHTML: '', className: '', style: {}, dataset: {},
  clientWidth: 0, clientHeight: 0 }));
document.querySelectorAll = () => [];
document.documentElement = fake();
global.getComputedStyle = () => fake();
global.window = { devicePixelRatio: 1, addEventListener() {} };
global.addEventListener = () => {};
global.location = { hash: '' };
global.requestAnimationFrame = f => setImmediate(f);
global.ResizeObserver = class { observe() {} };
global.Worker = class { constructor() { throw new Error('pas de Worker dans le test'); } };
global.URL = { createObjectURL: () => '' };
global.FileReader = class { readAsText(f) { setImmediate(() => { this.result = fs.readFileSync(f.path, 'latin1'); this.onload(); }); } };

const html = fs.readFileSync(path.join(__dirname, '..', 'jumeau_numerique.html'), 'utf8');
const grab = id => { const a = html.indexOf('<script id="' + id + '"'), b = html.indexOf('>', a) + 1; return html.slice(b, html.indexOf('</script>', b)); };
els['model-data'] = { textContent: grab('model-data') };
els['replay-data'] = { textContent: grab('replay-data') };
els['engine'] = { textContent: grab('engine') };
eval(grab('engine'));
let main = html.slice(html.indexOf('<script>\n/* ======================= Données') + 8);
main = main.slice(0, main.indexOf('</script>'));
main = main.replace('startWorker(SRC.replay);', '');  // pas de précalcul du rejeu dans ce test
eval(main + `
;globalThis.__analyse = analyse; globalThis.__S = S; globalThis.__SRC = SRC; globalThis.__state = stateAt; globalThis.__smooth = smoothPred;`);

const files = fs.readdirSync(dir).sort().map(n => ({ name: n, path: path.join(dir, n), size: fs.statSync(path.join(dir, n)).size }));
const t0 = Date.now();
__analyse(files).then(() => {
  const s = __SRC.files;
  console.log(`${files.length} fichiers · colonne ${+col + 1} · ${((Date.now() - t0) / 1000).toFixed(1)} s`);
  console.log('message :', els['msg'].textContent);
  if (!s) return;
  const v = __smooth(s, __S.sel, __S.step, true);
  const st = __state(s, __S.sel, __S.step, true);
  console.log(`mode=${__S.mode} · roulement B${__S.sel} · RUL lissée ${v == null ? '—' : v.toFixed(2)} j · état ${st.st} · niveau ${st.db.toFixed(1)} dB`);
});
