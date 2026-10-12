// Diagnostic instantané sur les deux fichiers d'exemple embarqués (DOM factice).
const fs = require('fs'), path = require('path');
const fake = () => new Proxy(function(){}, {
  get: (t, k) => k === Symbol.toPrimitive ? (() => 0) : k in t ? t[k] : (t[k] = fake()),
  set: (t, k, v) => { t[k] = v; return true; }, apply: () => fake(), construct: () => fake() });
const els = {};
global.document = fake();
document.getElementById = id => els[id] || (els[id] = Object.assign(fake(), { id, value: '', textContent: '', innerHTML: '', className: '', style: {}, dataset: {}, clientWidth: 0, clientHeight: 0, tBodies: [fake()] }));
document.querySelectorAll = () => [];
document.querySelector = () => fake();
global.getComputedStyle = () => fake();
global.window = { devicePixelRatio: 1, addEventListener() {} };
global.addEventListener = () => {};
global.location = { hash: '#notour' };
global.requestAnimationFrame = f => setImmediate(f);
global.ResizeObserver = class { observe() {} };
global.Worker = class { constructor() { throw new Error('pas de Worker'); } };
global.URL = { createObjectURL: () => '' };
global.localStorage = { getItem: () => '1', setItem() {} };
const html = fs.readFileSync(path.join(__dirname, '..', 'jumeau_numerique.html'), 'utf8');
const grab = id => { const a = html.indexOf('<script id="' + id + '"'), b = html.indexOf('>', a) + 1; return html.slice(b, html.indexOf('</script>', b)); };
['model-data', 'replay-data', 'extras-data', 'engine'].forEach(id => els[id] = { textContent: grab(id) });
eval(grab('engine'));
let main = html.slice(html.indexOf('<script>\n/* ======================= Données') + 8);
main = main.slice(0, main.indexOf('</script>')).replace('startWorker(SRC.replay);', '');
eval(main + ';globalThis.__run = runInst; globalThis.__I = () => INST; globalThis.__X = EXTRAS;');
for (const x of __X.examples) {
  const t0 = Date.now(), flat = decodeF32(x.f32), nc = x.channels, n = flat.length / nc, cols = [];
  for (let c = 0; c < nc; c++) { const a = new Float32Array(n); for (let i = 0; i < n; i++) a[i] = flat[i * nc + c]; cols.push(a); }
  __run(x.name, cols, 'test');
  const I = __I();
  console.log(`${x.name} (${((Date.now() - t0) / 1000).toFixed(1)} s) : source voie ${I.src.c + 1}, ` + I.ch.map(c => `V${c.c + 1} ${c.v.top.key}×${c.v.top.score.toFixed(1)}`).join(' | '));
  console.log('   ' + els['instTxt'].innerHTML.replace(/<[^>]+>/g, '').slice(0, 260));
}
