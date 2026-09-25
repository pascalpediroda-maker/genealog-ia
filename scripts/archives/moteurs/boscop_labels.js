// Lit le LABEL du manifeste IIIF d'une serie d'unites Boscop, et le nombre de vues.
//
//   node boscop_labels.js 67 1945100 1945170
//   node boscop_labels.js 67 --arks 1945107,1945160,1945247
//
// Pourquoi : la notice de la liste de resultats est tronquee et ne dit pas
// toujours le TYPE d'acte — « 1872 - (1872) » et rien d'autre. Le label du
// manifeste, lui, le porte en clair : « 3 E 162 /1 - Baptemes - (1712-1747) ».
// Une requete par unite, et on sait ce qu'on tire avant de le tirer.

const { chromium } = require('playwright');
const fs = require('fs'), path = require('path');

const CONF = JSON.parse(fs.readFileSync(path.join(__dirname, '..', 'portails.json'), 'utf8'));
const args = process.argv.slice(2);
const DEPT = args[0];
const p = CONF.portails.find(x => x.dept === DEPT && x.moteur === 'boscop');
if (!p) { console.error('portail boscop inconnu : ' + DEPT); process.exit(1); }

let arks = [];
if (args[1] === '--arks') arks = args[2].split(',').map(s => s.trim());
else {
  const a = parseInt(args[1], 10), b = parseInt(args[2], 10);
  for (let i = a; i <= b; i++) arks.push(String(i));
}

(async () => {
  const ctx = await chromium.launchPersistentContext('.chrome-' + DEPT, {
    channel: 'chrome', headless: false, viewport: { width: 1100, height: 760 } });
  const page = ctx.pages()[0] || await ctx.newPage();
  await page.goto(p.base + p.recherche.chemin, { waitUntil: 'domcontentloaded', timeout: 90000 });
  await page.waitForTimeout(11000);          // Anubis

  console.log(['ark', 'vues', 'label'].join('\t'));
  for (const ark of arks) {
    const u = p.image.manifeste.replace('{base}', '').replace('{ark_prefixe}', p.ark_prefixe)
      .replace('{ark}', ark);
    const r = await page.evaluate(async (v) => {
      try {
        const x = await fetch(v);
        if (!x.ok) return { err: x.status };
        const m = await x.json();
        const seq = m.sequences?.[0]?.canvases || m.items || [];
        const lab = typeof m.label === 'string' ? m.label
          : (m.label?.fr?.[0] || m.label?.none?.[0] || JSON.stringify(m.label));
        return { n: seq.length, lab };
      } catch (e) { return { err: e.message.slice(0, 60) }; }
    }, u);
    if (r.err) console.log(`${ark}\t—\t(erreur ${r.err})`);
    else console.log(`${ark}\t${r.n}\t${(r.lab || '').replace(/\s+/g, ' ').trim()}`);
    await page.waitForTimeout(400);
  }
  await ctx.close();
})();
