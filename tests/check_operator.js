// Simule le parcours opérateur (chargement d'un dossier brut) avec un DOM minimal.
// Usage : node tests/check_operator.js <dossier_brut> [nb_fichiers] [colonne]
const fs = require('fs'), path = require('path');
const dir = process.argv[2], nmax = +(process.argv[3] || 1e9), col = process.argv[4] || '0';
const els = {};
global.document = { getElementById: id => els[id] || (els[id] = {
  id, style: {}, textContent: '', innerHTML: '', className: '', value: id === 'channel' ? col : '',
  addEventListener(ev, fn) { this['on' + ev] = fn; } }) };
global.Chart = class { destroy() {} };
Chart.defaults = {};
global.FileReader = class { readAsText(f) { setImmediate(() => { this.result = fs.readFileSync(f.path, 'latin1'); this.onload(); }); } };
global.alert = m => console.log('ALERT', m);

const html = fs.readFileSync(path.join(__dirname, '..', 'rul_4feat.html'), 'utf8');
const json = html.match(/<script id="model-data" type="application\/json">([\s\S]*?)<\/script>/)[1];
const code = html.match(/<script>([\s\S]*?)<\/script>/)[1];
document.getElementById('model-data').textContent = json;
eval(code);

const files = fs.readdirSync(dir).sort().slice(-nmax)
  .map(n => ({ name: n, path: path.join(dir, n), size: fs.statSync(path.join(dir, n)).size }));
const t0 = Date.now();
els['folder'].onchange({ target: { files } });
const wait = setInterval(() => {
  const err = document.getElementById('opError').style.display === 'flex';
  if (!(err || document.getElementById('opResults').style.display === 'block')) return;
  clearInterval(wait);
  console.log(`${files.length} fichiers, colonne ${+col + 1}, ${((Date.now() - t0) / 1000).toFixed(1)} s`);
  if (err) console.log('ERREUR AFFICHÉE :', els['opError'].textContent);
  else console.log('ÉTAT :', els['opStatusTxt'].textContent, '| RUL :', els['opRul'].textContent,
                   '| RMS vs neuf :', els['opRms'].textContent, '\nINFO :', els['opMetaInfo'].textContent);
}, 200);
