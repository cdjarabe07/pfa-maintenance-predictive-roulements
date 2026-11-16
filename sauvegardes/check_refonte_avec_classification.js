// Non-régression de la refonte : mêmes chiffres que la version d'avant (sauvegardes/), visite guidée, débordements.
// Usage : NODE_PATH=$(npm root -g) node tests/check_refonte.js
const { chromium } = require('playwright'); const path = require('path');
const root = path.resolve(__dirname, '..');
const NEW = 'file://' + path.join(root, 'site', 'jumeau_roulements.html');
const OLD = 'file://' + path.join(root, 'sauvegardes', 'jumeau_roulements_avant_refonte.html');
let bad = 0; const ok = (c, m) => { console.log((c ? 'OK   ' : 'FAIL ') + m); if (!c) bad++; };
const norm = t => (t || '').replace(/\s+/g, ' ').trim();
// zones numériques à comparer (ids présents dans les deux versions)
const SEL = ['#bn-title', '#bn-sub', '#clk', '#clk-rel', '#cards', '#wo-body', '#log', '#lead-sum', '#lead-body'];
async function snap(pg, i, src) {
  await pg.evaluate(([i, src]) => { const sel = document.querySelector('#src'); sel.value = src; sel.dispatchEvent(new Event('change')); const p = document.querySelector('#pos'); p.value = i; p.dispatchEvent(new Event('input')); }, [i, src]);
  await pg.waitForTimeout(60);
  const o = {}; for (const s of SEL) o[s] = norm(await pg.textContent(s)); return o;
}
(async () => {
  const br = await chromium.launch();
  const mk = async (url, w = 1600, h = 900, q = '?sans-visite') => { const c = await br.newContext({ viewport: { width: w, height: h } }); const p = await c.newPage(); p.errs = []; p.on('pageerror', e => p.errs.push(e.message)); await p.goto(url + q); await p.waitForFunction(() => window.__twin); return p; };
  const a = await mk(OLD, 1600, 900, ''), b = await mk(NEW);
  // 1. mêmes valeurs à plusieurs instants et pour chaque source d'étiquettes
  const srcs = await b.$$eval('#src option', o => o.map(x => x.value));
  let diff = 0, n = 0;
  for (const src of srcs) for (const i of [0, 120, 400, 492, 700, 900, 940, 982, 983]) {
    const x = await snap(a, i, src), y = await snap(b, i, src); n++;
    for (const s of SEL) if (x[s] !== y[s]) { diff++; if (diff < 4) console.log('  écart', s, i, src, '\n   ancien:', x[s].slice(0, 120), '\n   nouveau:', y[s].slice(0, 120)); }
  }
  ok(diff === 0, `supervision : textes et chiffres identiques à l'ancienne version (${n} instants × ${SEL.length} zones)`);
  // 2. pages de modèles, simulateur, limites : même texte
  for (const t of ['modeles', 'simulateur', 'limites']) {
    await a.click('#t-' + t); await b.click('#t-' + t);
    const ids = t === 'modeles' ? ['#mbars', '#cm', '#kpis', '#gapsum', '#mnote'] : t === 'simulateur' ? ['#sim', '#sim-verdict'] : ['#limits'];
    let d = 0;
    if (t === 'limites') {
      // la page est réorganisée par catégories : mêmes titres et mêmes paragraphes, dans n'importe quel ordre
      for (const sel of ['#limits h3', '#limits p']) {
        const x = (await a.$$eval(sel, e => e.filter(n => !n.closest('.gh')).map(n => n.textContent.replace(/\s+/g, ' ').trim()))).sort(), y = (await b.$$eval(sel, e => e.filter(n => !n.closest('.gh')).map(n => n.textContent.replace(/\s+/g, ' ').trim()))).sort();
        if (JSON.stringify(x) !== JSON.stringify(y)) { d++; console.log('  écart', t, sel); }
      }
    } else for (const s of ids) if (norm(await a.textContent(s)) !== norm(await b.textContent(s))) { d++; console.log('  écart', t, s); }
    ok(d === 0, t === 'limites' ? 'page limites : mêmes titres et mêmes paragraphes (réorganisés par catégorie)' : `page ${t} : contenus numériques identiques`);
  }
  // 3. prédictions : résultats identiques
  for (const [btn, res, sel] of [['#rul-demo-d', '#rul-res', ['#rul-val', '#rul-reco-t', '#rul-rms', '#rul-unc']], ['#rul-demo-h', '#rul-res', ['#rul-val', '#rul-reco-t', '#rul-rms', '#rul-unc']]]) {
    await a.click('#t-rul'); await b.click('#t-rul'); await a.click(btn); await b.click(btn); await a.waitForTimeout(700); await b.waitForTimeout(700);
    let d = 0; for (const s of sel) if (norm(await a.textContent(s)) !== norm(await b.textContent(s))) { d++; console.log('  écart', btn, s); }
    ok(d === 0, `durée de vie ${btn} : mêmes résultats (${norm(await b.textContent('#rul-val'))})`);
  }
  await a.click('#t-classe'); await b.click('#t-classe');
  const models = await b.$$eval('#cl-model option', o => o.map(x => x.value));
  for (const m of models) for (const ex of ['#cl-ex-h', '#cl-ex-d', '#cl-ex-now']) {
    await a.selectOption('#cl-model', m); await b.selectOption('#cl-model', m); await a.click(ex); await b.click(ex); await a.waitForTimeout(250); await b.waitForTimeout(250);
    const x = norm(await a.textContent('#cl-cards')), y = norm(await b.textContent('#cl-cards'));
    ok(x === y && x.length > 50, `état d'un roulement, ${m}, ${ex} : résultats identiques`);
  }
  ok(a.errs.length === 0 && b.errs.length === 0, 'aucune erreur JavaScript (ancienne et nouvelle versions)');
  // 4. débordement horizontal et lisibilité sur plusieurs tailles
  for (const [w, h] of [[1600, 900], [1366, 768], [1024, 768], [768, 1024], [390, 844]]) {
    const p = await mk(NEW, w, h); let worst = 0;
    for (const t of ['supervision', 'rul', 'classe', 'modeles', 'simulateur', 'limites']) {
      await p.click('#t-' + t); if (t === 'rul') await p.click('#rul-demo-d'); if (t === 'classe') await p.click('#cl-ex-d'); await p.waitForTimeout(150);
      worst = Math.max(worst, await p.evaluate(() => document.documentElement.scrollWidth - window.innerWidth));
    }
    ok(worst <= 2, `${w}×${h} : aucun défilement horizontal de la page (6 pages, dépassement max ${worst}px)`);
    ok(p.errs.length === 0, `${w}×${h} : aucune erreur JavaScript`);
    await p.context().close();
  }
  // 5. visite guidée : démarrage automatique, étapes sur chaque page, navigation, fermeture, mémoire
  { const c = await br.newContext({ viewport: { width: 1600, height: 900 } }); const p = await c.newPage(); const errs = []; p.on('pageerror', e => errs.push(e.message));
    await p.goto(NEW); await p.waitForFunction(() => window.__twin); await p.waitForSelector('#tourPop .st', { timeout: 3000 });
    ok(/Étape 1 sur \d+/.test(await p.textContent('#tourPop')), 'visite guidée : démarre à la première visite');
    await p.keyboard.press('ArrowRight'); await p.waitForTimeout(150); ok(/Étape 2 sur/.test(await p.textContent('#tourPop')), 'visite guidée : flèche droite = étape suivante');
    await p.keyboard.press('ArrowLeft'); await p.waitForTimeout(150); ok(/Étape 1 sur/.test(await p.textContent('#tourPop')), 'visite guidée : flèche gauche = étape précédente');
    await p.keyboard.press('Escape'); ok(!(await p.$('#tourPop')), 'visite guidée : Échap ferme la visite');
    await p.reload(); await p.waitForFunction(() => window.__twin); await p.waitForTimeout(1200);
    ok(!(await p.$('#tourPop')), 'visite guidée : ne repart pas seule après avoir été fermée');
    for (const t of ['supervision', 'rul', 'classe', 'modeles', 'simulateur', 'limites']) {
      await p.click('#t-' + t); if (t === 'rul') await p.click('#rul-demo-d'); if (t === 'classe') await p.click('#cl-ex-d');
      await p.click('#t-visite'); await p.waitForSelector('#tourPop .st');
      const total = +(/sur (\d+)/.exec(await p.textContent('#tourPop'))[1]); let seen = 0, inView = true;
      for (let k = 0; k < total; k++) {
        await p.waitForTimeout(80);
        const r = await p.evaluate(() => { const h = document.querySelector('#tourHole').getBoundingClientRect(), q = document.querySelector('#tourPop').getBoundingClientRect(); return { hw: h.width, hh: h.height, pl: q.left, pt: q.top, pr: q.right, pb: q.bottom, vw: innerWidth, vh: innerHeight }; });
        if (r.hw > 0 && r.hh > 0) seen++; if (r.pl < 0 || r.pt < 0 || r.pr > r.vw + 1 || r.pb > r.vh + 1) inView = false;
        await p.click('#tNext');
      }
      ok(seen === total && inView && !(await p.$('#tourPop')), `visite guidée, page ${t} : ${total} étapes, cadre visible, bulle dans l'écran, fin propre`);
    }
    await p.click('#t-supervision'); await p.click('#t-visite'); await p.waitForSelector('#tourPop .st'); await p.click('#t-rul', { force: true }).catch(() => {});
    ok(errs.length === 0, 'visite guidée : aucune erreur JavaScript');
    await c.close(); }
  // 6. mobile : la visite tient dans l'écran
  { const p = await mk(NEW, 390, 844, ''); await p.waitForSelector('#tourPop .st'); let inView = true;
    for (let k = 0; k < 9; k++) { await p.waitForTimeout(100); const r = await p.evaluate(() => { const q = document.querySelector('#tourPop'); if (!q) return null; const b = q.getBoundingClientRect(); return b.left >= 0 && b.right <= innerWidth + 1 && b.top >= 0 && b.bottom <= innerHeight + 1; }); if (r === null) break; if (!r) inView = false; if (await p.$('#tNext')) await p.click('#tNext'); }
    ok(inView, 'visite guidée sur mobile : la bulle reste dans l\'écran'); }
  await br.close();
  console.log(bad ? `\n${bad} échec(s)` : '\nTout est vert'); process.exit(bad ? 1 : 0);
})();
