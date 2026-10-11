// Vérifie le JS de l'interface : features (vs Python) et, si fourni, la prédiction (vs Keras).
// Usage : node tests/check_js.js <cas.json>   (cas.json produit par tests/make_cases.py)
const fs = require('fs');
const html = fs.readFileSync(__dirname + '/../interface_body.html', 'utf8');
const cut = (a, b) => html.slice(html.indexOf(a), html.indexOf(b));
eval(cut('function modelForward', 'var MODEL ='));
eval(cut('function fft2', 'function parseSignal'));
eval(cut('function median', 'var chFeat'));
const cases = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
let worst = 0;
for (const c of cases.signals) {
  const js = sampleFeatures(c.signal);
  const rel = js.map((v, i) => Math.abs(v - c.features[i]) / Math.max(1e-9, Math.abs(c.features[i])));
  worst = Math.max(worst, ...rel);
}
console.log(`features : ${cases.signals.length} signaux, écart relatif max JS/Python = ${worst.toExponential(2)}`);
if (cases.model) {
  global.MODEL = cases.model;
  for (const p of cases.predictions) {
    const js = predict(p.seq, reference(p.ref));
    console.log(`prédiction ${p.name} : Keras = ${p.keras.toFixed(5)} | JS = ${js.toFixed(5)}`);
  }
}
