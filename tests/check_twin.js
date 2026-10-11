// Vérifie le moteur du tableau de bord : prédictions du rejeu (vs Keras) et diagnostic d'enveloppe.
const fs = require('fs'), path = require('path');
const html = fs.readFileSync(path.join(__dirname, '..', 'jumeau_numerique.html'), 'utf8');
const grab = id => { const a = html.indexOf('<script id="' + id + '"'), b = html.indexOf('>', a) + 1; return html.slice(b, html.indexOf('</script>', b)); };
eval(grab('engine'));
const main = html.match(/<script>([\s\S]*?)<\/script>/)[1];
const cut = (a, b) => main.slice(main.indexOf(a), main.indexOf(b));
const REPLAY = JSON.parse(grab('replay-data')), FS = 20000, C = {crit: 'r', warn: 'o', acc2: 'v'};
eval(cut('var GEOM', 'var CSS'));
eval(cut('function fft2', '/* ======================= État'));
const rows = REPLAY.bearings[1], ref = reference(rows.slice(0, 200));
for (const [w, keras] of [[300, 2.711], [700, 2.623], [952, 0.059]])
  console.log(`fenêtre ${w} : Keras ${keras} | JS ${predictAt(rows, ref, w + 29, REPLAY.weights, 30).toFixed(3)}`);
for (const r of REPLAY.raw_b1) {
  const d = diagnose(envelopeSpectrum(decodeF32(r.f32), 800));
  console.log(`acquisition ${r.idx} : ` + d.map(x => `${x.key} ×${x.score.toFixed(1)}`).join(' · ') + ` | pics ${d[0].key} : ${d[0].peaks.map(p => p[0].toFixed(1)).join(', ')} Hz`);
}
