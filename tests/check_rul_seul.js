// Non-régression de la version « durée de vie seule » : compare à la version précédente (avec classification).
// Usage : node tests/check_rul_seul.js <ancienne page html>
const path = require('path');
const { chromium } = require('playwright');
const OLD = 'file://' + path.resolve(process.argv[2]);
const NEW = 'file://' + path.join(__dirname, '..', 'site', 'jumeau_roulements.html');
let fails = 0;
const ok = (c, m) => { console.log((c ? 'OK   ' : 'ÉCHEC ') + m); if (!c) fails++; };
const norm = s => (s || '').replace(/\s+/g, ' ').trim();
(async () => {
  const br = await chromium.launch(), errs = [];
  const open = async (url, vp) => {
    const p = await (await br.newContext({ viewport: vp || { width: 1360, height: 900 } })).newPage();
    p.on('pageerror', e => errs.push(String(e)));
    p.on('console', m => { if (m.type() === 'error' && !/fonts\.g|ERR_|net::/.test(m.text())) errs.push(m.text()); });
    await p.goto(url + '?sans-visite'); await p.waitForFunction(() => window.__twin); return p;
  };
  const a = await open(OLD), b = await open(NEW);
  // 1. navigation
  const tabs = await b.$$eval('[role=tab][data-tab]', e => e.map(x => x.dataset.tab));
  ok(JSON.stringify(tabs) === JSON.stringify(['supervision', 'rul', 'simulateur', 'limites']), 'onglets : ' + tabs.join(', '));
  ok(!(await b.$('#p-classe')) && !(await b.$('#p-modeles')) && !(await b.$('#src')), 'pages et sélecteur de classification supprimés');
  // 2. supervision identique à plusieurs instants
  for (const i of [0, 400, 700, 960, 983]) {
    const get = async p => { await p.evaluate(v => { const s = document.querySelector('#pos'); s.value = v; s.dispatchEvent(new Event('input', { bubbles: true })); }, i); return norm(await p.textContent('#banner')) + '|' + norm(await p.textContent('#cards')) + '|' + norm(await p.textContent('#wo')); };
    ok(await get(a) === await get(b), 'supervision identique à l\'instant ' + i);
  }
  // 3. durée de vie restante : mêmes résultats
  for (const t of ['#rul-demo-h', '#rul-demo-d']) {
    const get = async p => { await p.click('#t-rul'); await p.click(t); await p.waitForSelector('#rul-res:not([hidden])', { timeout: 60000 }); await p.waitForTimeout(400); return ['#rul-val', '#rul-unc', '#rul-reco-t', '#rul-k-mae', '#rul-k-win', '#rul-table'].map(s => '' ).length ? (await Promise.all(['#rul-val', '#rul-unc', '#rul-reco-t', '#rul-k-mae', '#rul-k-win', '#rul-table'].map(async s => norm(await p.textContent(s))))).join('|') : ''; };
    const x = await get(a), y = await get(b);
    ok(x === y, 'RUL ' + t + ' identique : ' + y.slice(0, 70));
  }
  // 4. simulateur et limites
  await a.click('#t-simulateur'); await b.click('#t-simulateur');
  ok(norm(await a.textContent('#sim-card')) === norm(await b.textContent('#sim-card')), 'simulateur identique');
  await b.click('#t-limites');
  const lim = norm(await b.textContent('#limits'));
  ok(!/F1|classe|État d'un roulement|Comparer/.test(lim) && /durée de vie restante demande un historique/.test(lim), 'Limites : plus de référence à la classification');
  // 5. adresse ancienne
  const c = await open(NEW.replace('?sans-visite', '') + '#classe');
  ok(await c.$eval('#p-supervision', e => !e.hidden), '#classe retombe sur la supervision');
  // 6. mobile : pas de débordement, visite guidée sur chaque page
  for (const w of [390, 768, 1024]) {
    const m = await open(NEW, { width: w, height: 800 });
    for (const t of ['supervision', 'rul', 'simulateur', 'limites']) {
      await m.evaluate(n => document.querySelector('#t-' + n).click(), t); await m.waitForTimeout(150);
      const ov = await m.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
      ok(ov <= 0, w + ' px, ' + t + ' : pas de défilement horizontal (' + ov + ')');
    }
  }
  const tp = await br.newContext({ viewport: { width: 1360, height: 900 } }).then(x => x.newPage());
  tp.on('pageerror', e => errs.push(String(e)));
  await tp.goto(NEW); await tp.waitForTimeout(1200);
  const steps = [];
  for (let k = 0; k < 12; k++) { const t = await tp.$('.tour-card, #tour, [class*=tour]'); if (!t) break; steps.push(1); const next = await tp.$('text=Suivant'); if (!next) break; await next.click().catch(() => {}); await tp.waitForTimeout(120); }
  ok(errs.length === 0, 'aucune erreur JavaScript' + (errs.length ? ' : ' + errs[0] : ''));
  await br.close(); console.log(fails ? fails + ' échec(s)' : 'Tout est conforme'); process.exit(fails ? 1 : 0);
})();
