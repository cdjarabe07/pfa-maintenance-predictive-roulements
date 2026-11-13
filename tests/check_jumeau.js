// Vérifie l'interface unique (site/jumeau_roulements.html) : calculs identiques à Python, parcours utilisateur, erreurs, captures.
// Usage : node tests/check_jumeau.js <dossier cases (make_jumeau_cases.py)> [dossier captures]
const fs = require('fs'), path = require('path');
const { chromium } = require('playwright');
const cdir = process.argv[2], shots = process.argv[3];
const root = path.join(__dirname, '..');
const C = JSON.parse(fs.readFileSync(path.join(cdir, 'cases.json'), 'utf8'));
let fails = 0;
const ok = (c, m) => { console.log((c ? 'OK   ' : 'ÉCHEC ') + m); if (!c) fails++; };

(async () => {
  const br = await chromium.launch();
  const pg = await (await br.newContext({ viewport: { width: 1360, height: 900 } })).newPage();
  const errs = [];
  pg.on('pageerror', e => errs.push(String(e)));
  pg.on('console', m => { if (m.type() === 'error' && !/fonts\.g|ERR_|net::/.test(m.text())) errs.push(m.text()); });
  await pg.goto('file://' + path.join(root, 'site', 'jumeau_roulements.html'));
  await pg.waitForFunction(() => window.__twin);

  // 1. variables calculées depuis un fichier brut = valeurs du CSV
  let worst = [0, 0, 0, 0];
  for (const c of C.cases) {
    const txt = fs.readFileSync(path.join(cdir, c.file), 'latin1');
    const f = await pg.evaluate(t => { const p = window.__twin.parseColumns(t); return p.cols.map(window.__twin.classFeatures); }, txt);
    for (let k = 0; k < 4; k++) for (let j = 0; j < 4; j++) worst[j] = Math.max(worst[j], Math.abs(f[k][j] - c.csv[k][j]) / Math.max(1e-9, Math.abs(c.csv[k][j])));
  }
  ok(worst.every(w => w < 2e-4), 'RMS / énergie / entropie / kurtosis depuis le brut = CSV (écarts relatifs max ' + worst.map(w => w.toExponential(1)).join(', ') + ')');

  // 2. prédictions JS = scikit-learn sur les 3 936 lignes
  const res = await pg.evaluate(({ feats, labels, expected }) => {
    const out = {}, T = window.__twin;
    for (const m of ['Règle IQR', 'Decision Tree', 'Logistic Regression', 'Gaussian Naive Bayes']) {
      let diff = 0, n = 0;
      for (const b of Object.keys(feats)) feats[b].forEach((x, i) => {
        const p = T.predictClass(m, b, x), e = m === 'Règle IQR' ? labels[b][i] : expected[b][m][i];
        diff += p !== e; n++;
      });
      out[m] = [diff, n];
    }
    return out;
  }, C);
  for (const [m, [d, n]] of Object.entries(res)) ok(d === 0, `${m} : ${n - d}/${n} prédictions identiques à Python`);

  // 3. durée de vie restante : même résultat que l'ancienne interface validée
  const html = fs.readFileSync(path.join(root, 'rul_4feat.html'), 'utf8');
  const els = {};
  global.document = { getElementById: id => els[id] || (els[id] = { style: {}, textContent: '', addEventListener() {} }) };
  global.Chart = class { destroy() {} }; Chart.defaults = {};
  els['model-data'] = { textContent: html.match(/<script id="model-data" type="application\/json">([\s\S]*?)<\/script>/)[1] };
  eval(html.match(/<script>([\s\S]*?)<\/script>/)[1]);
  const M = JSON.parse(els['model-data'].textContent);
  for (const name of ['healthy', 'degraded']) {
    const old = predict(M.demo[name], reference(M.demo.ref));
    const neu = await pg.evaluate(n => { const T = window.__twin, M = T.rulModel(); return T.rulPredict(M.demo[n], T.rulRef(M.demo.ref)); }, name);
    ok(Math.abs(old - neu) < 1e-9, `RUL ${name} : ${neu.toFixed(4)} j (ancienne interface ${old.toFixed(4)} j)`);
  }
  const f4 = await pg.evaluate(t => { const p = window.__twin.parseColumns(t); return window.__twin.rulFeatures(p.cols[0]); }, fs.readFileSync(path.join(cdir, 'idx974.txt'), 'latin1'));
  const sig = fs.readFileSync(path.join(cdir, 'idx974.txt'), 'latin1').split('\n').filter(Boolean).map(l => +l.split('\t')[0]);
  const o4 = sampleFeatures(sig);
  ok(f4.every((v, i) => Math.abs(v - o4[i]) < 1e-9 * Math.max(1, Math.abs(o4[i]))), 'variables du modèle de RUL identiques à l\'ancienne interface');

  // 4. parcours : onglets
  const tabs = ['supervision', 'rul', 'classe', 'modeles', 'simulateur', 'limites'];
  for (const t of tabs) {
    await pg.click('#t-' + t);
    const vis = await pg.evaluate(t => [...document.querySelectorAll('.panel')].filter(p => !p.hidden).map(p => p.id), t);
    ok(vis.length === 1 && vis[0] === 'p-' + t, 'onglet ' + t + ' affiché seul');
  }

  // 5. État d'un roulement : fichier sain, fichier dégradé, erreurs
  await pg.click('#t-classe');
  const pick = async f => { await pg.setInputFiles('#cl-file', path.join(cdir, f)); await pg.waitForTimeout(1500); };
  await pick('idx492.txt');
  let pills = await pg.$$eval('#cl-cards .pill', e => e.map(x => x.textContent));
  ok(pills.join() === 'NORMAL,NORMAL,NORMAL,NORMAL', 'fichier du 15/02 : ' + pills.join(', '));
  await pick('idx974.txt');
  pills = await pg.$$eval('#cl-cards .pill', e => e.map(x => x.textContent));
  ok(pills[0] === 'ANORMAL', 'fichier du 19/02 : ' + pills.join(', ') + ' | ' + await pg.textContent('#cl-sum-t'));
  if (shots) await pg.screenshot({ path: path.join(shots, 'classe.png'), fullPage: true });
  await pick('huit.txt');
  ok(/8 colonnes/.test(await pg.textContent('#cl-err')) && await pg.$eval('#cl-res', e => e.hidden), 'erreur claire pour un fichier à 8 colonnes');
  await pick('court.txt');
  ok(/20\s?480 lignes/.test(await pg.textContent('#cl-err')), 'erreur claire pour un relevé trop court');
  for (const m of ['Règle IQR', 'Logistic Regression', 'Gaussian Naive Bayes']) {
    await pg.selectOption('#cl-model', m); await pg.click('#cl-ex-d');
    const p0 = await pg.$eval('#cl-cards .pill', e => e.textContent);
    ok(p0 === 'ANORMAL', 'exemple du 19/02 avec ' + m + ' : ' + p0);
  }

  await pg.click('#cl-ex-h');
  pills = await pg.$$eval('#cl-cards .pill', e => e.map(x => x.textContent));
  ok(pills.join() === 'NORMAL,NORMAL,NORMAL,NORMAL', 'exemple du 13/02 : ' + pills.join(', '));

  // 6. Durée de vie restante : exemples, erreur sur trop peu de fichiers
  await pg.click('#t-rul');
  await pg.click('#rul-demo-d'); await pg.waitForTimeout(800);
  const rd = await pg.textContent('#rul-val'), reco = await pg.textContent('#rul-reco-t');
  await pg.click('#rul-demo-h'); await pg.waitForTimeout(800);
  const rh = await pg.textContent('#rul-val');
  ok(!(await pg.$eval('#rul-res', e => e.hidden)), `exemple dégradé : ${rd.trim()} (${reco.trim()}) ; sain : ${rh.trim()}`);
  if (shots) await pg.screenshot({ path: path.join(shots, 'rul.png'), fullPage: true });
  await pg.setInputFiles('#rul-files', [path.join(cdir, 'idx0.txt'), path.join(cdir, 'idx492.txt')]);
  await pg.waitForTimeout(500);
  ok(/2 fichier/.test(await pg.textContent('#rul-err')) && /230/.test(await pg.textContent('#rul-err')), 'message clair avec 2 fichiers seulement');

  // 7. supervision, bon de travail, synoptique
  await pg.click('#t-supervision');
  await pg.click('#go-alert'); await pg.waitForTimeout(200);
  ok(/Palier 1/.test(await pg.textContent('#wo-body')) && /Élevée/.test(await pg.textContent('#wo-body')), 'bon de travail à la première alerte');
  await pg.click('.pal[data-k="1"]');
  ok(await pg.$eval('.pal[data-k="1"]', e => e.getAttribute('aria-pressed') === 'true'), 'clic sur un palier du synoptique');
  await pg.evaluate(() => { const T = window.__twin; let i = 50; while (T.D.bearings.some(b => T.D.rule[b][i] === '1' || T.D.oof['Decision Tree'][b][i] === '1')) i++; const s = document.getElementById('pos'); s.value = i; s.dispatchEvent(new Event('input')); });
  await pg.waitForTimeout(100);
  ok(/Rien à signaler/.test(await pg.textContent('#wo-body')), 'aucun bon de travail quand tout est normal');
  await pg.click('#go-stop'); await pg.waitForTimeout(100);
  ok(/arrêt/i.test(await pg.textContent('#wo-body')), 'bon de travail à l\'arrêt machine');
  await pg.click('#go-alert');
  if (shots) {
    await pg.screenshot({ path: path.join(shots, 'supervision.png'), fullPage: true });
    for (const t of ['modeles', 'simulateur', 'limites']) { await pg.click('#t-' + t); await pg.screenshot({ path: path.join(shots, t + '.png'), fullPage: true }); }
    const mob = await (await br.newContext({ viewport: { width: 390, height: 844 }, deviceScaleFactor: 2 })).newPage();
    await mob.goto('file://' + path.join(root, 'site', 'jumeau_roulements.html'));
    await mob.waitForFunction(() => window.__twin);
    const sw = await mob.evaluate(() => document.documentElement.scrollWidth);
    ok(sw <= 392, 'mobile : pas de défilement horizontal de la page (largeur ' + sw + ')');
    await mob.screenshot({ path: path.join(shots, 'mobile.png') });
    await mob.click('#t-classe'); await mob.click('#cl-ex-d'); await mob.waitForTimeout(300);
    await mob.screenshot({ path: path.join(shots, 'mobile_classe.png'), fullPage: true });
  }
  ok(errs.length === 0, 'aucune erreur JavaScript' + (errs.length ? ' : ' + errs.join(' | ') : ''));
  await br.close();
  console.log(fails ? fails + ' échec(s)' : 'Tout est vert');
  process.exit(fails ? 1 : 0);
})();
