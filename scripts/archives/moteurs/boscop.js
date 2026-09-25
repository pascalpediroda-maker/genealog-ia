// Telecharge plusieurs registres d'affilee dans une seule session Chrome, sur
// n'importe quel portail BOSCOP / Ligeo-Archives.
//
//   node boscop.js <dept> <fichier.tsv>                 (ark <TAB> dossier, une ligne par registre)
//   node boscop.js <dept> <fichier.tsv> --vues 200-204  (seulement ces vues-la)
//
// Le portail ne tenait qu'a deux constantes codees en dur — le domaine de la
// Loire et son prefixe d'ark. Elles vivent desormais dans portails.json, et le
// module sert la Loire comme le Bas-Rhin.
//
// LE BAS-RHIN EST DERRIERE ANUBIS, une preuve-de-travail : on ouvre d'abord la
// page de recherche et on lui laisse une dizaine de secondes, sinon toutes les
// requetes rendent le HTML du defi au lieu du manifeste, et le script conclut a
// tort que le registre n'a pas de vues.
const { chromium } = require('playwright');
const fs = require('fs'), path = require('path');

const CONF = JSON.parse(fs.readFileSync(path.join(__dirname, '..', 'portails.json'), 'utf8'));
const DEPT = process.argv[2];
const p = CONF.portails.find(x => x.dept === DEPT && x.moteur === 'boscop');
if (!p) {
  console.error('usage : node boscop.js <dept> <fichier.tsv>');
  console.error('portails boscop connus : '
    + CONF.portails.filter(x => x.moteur === 'boscop').map(x => x.dept).join(', '));
  process.exit(1);
}
const LOTS = fs.readFileSync(process.argv[3], 'utf8').trim().split('\n')
  .map(l => l.trim().split('\t')).filter(a => a.length === 2);

// --vues N-M : ne tirer que cette plage de vues, bornes comprises, numerotees a partir de 1
// comme sur le portail. AJOUTE LE 7 SEPTEMBRE 2026, parce que la question posee ce jour-la
// etait « la table annuelle est-elle en fin de registre ? » et qu'y repondre coutait 204
// images pour en lire trois. C'est la regle du carnet — l'index d'abord, puis LES DEUX OU
// TROIS VUES qui portent l'acte — et l'outil ne savait pas la servir.
//
// ET IL PREND UNE LISTE DEPUIS LE 9 SEPTEMBRE 2026 : « --vues 20,60,100-104,140 ». La
// borne unique obligeait a relancer un Chrome par vue des qu'on SONDAIT au lieu de lire
// une suite -- douze lancements pour douze vues echantillonnees dans le recensement
// d'Angouleme, et deux d'entre eux se sont percutes sur le profil Chrome partage. Or
// sonder est le geste normal sur un registre de 1 183 vues : on cherche ou commence une
// rue, pas a tout tirer.
const iVues = process.argv.indexOf('--vues');
let VUES = null;                              // Set des numeros demandes, ou null = tout
if (iVues > 0) {
  const spec = process.argv[iVues + 1] || '';
  VUES = new Set();
  for (const part of spec.split(',')) {
    const m = /^\s*(\d+)(?:-(\d+))?\s*$/.exec(part);
    if (!m) {
      console.error('--vues attend « 200-204 », « 20,60,100 », ou les deux melanges');
      process.exit(1);
    }
    const a = parseInt(m[1], 10), b = m[2] ? parseInt(m[2], 10) : a;
    for (let k = a; k <= b; k++) VUES.add(k);
  }
}

(async () => {
  // LE PROFIL EST PARTAGE PAR DEPARTEMENT, ET C'EST VOULU : il garde le cookie de session
  // et la preuve-de-travail deja resolue, ce qui evite de repasser le defi anti-robot a
  // chaque lancement. Mais Chrome refuse d'ouvrir DEUX FOIS le meme profil, et l'erreur
  // ne dit rien d'utile -- elle deroule la ligne de commande de Chrome sur trente lignes.
  // Une deuxieme session tombe donc sur un profil a elle, en le disant.
  const opts = { channel: 'chrome', headless: false, viewport: { width: 1200, height: 800 } };
  let ctx;
  try {
    ctx = await chromium.launchPersistentContext('.chrome-' + DEPT, opts);
  } catch (e) {
    const bis = '.chrome-' + DEPT + '-' + process.pid;
    console.log('profil .chrome-' + DEPT + ' deja pris (une autre session tourne) — '
                + 'profil de secours ' + bis + ', le defi anti-robot sera a repasser');
    ctx = await chromium.launchPersistentContext(bis, opts);
  }
  const page = ctx.pages()[0] || await ctx.newPage();
  await page.goto(p.base + p.recherche.chemin, { waitUntil: 'domcontentloaded', timeout: 90000 });
  await page.waitForTimeout(11000);          // laisser passer le defi anti-robot
  for (const [ARK, DEST] of LOTS) {
    if (!VUES && fs.existsSync(DEST) && fs.readdirSync(DEST).length > 3) {
      console.log('== ' + DEST + ' : deja la, saute'); continue;
    }
    console.log('\n===== ' + DEST + '  ' + ARK);
    await page.goto(p.base + '/' + p.ark_prefixe + ARK,
      { waitUntil: 'domcontentloaded', timeout: 90000 });
    await page.waitForTimeout(6000);
    const services = await page.evaluate(async ([base, pref, ark]) => {
      const r = await fetch(base + '/' + pref + ark + '/manifest');
      const j = await r.json();
      const cv = (j.sequences && j.sequences[0] && j.sequences[0].canvases) || [];
      return cv.map(c => { const im = c.images && c.images[0] && c.images[0].resource;
        return (im && im.service && im.service['@id']) || (im && im['@id']) || null; }).filter(Boolean);
    }, [p.base, p.ark_prefixe, ARK]);
    console.log(services.length + ' vues');
    if (!services.length) { console.log('!! manifeste sans canvas'); continue; }
    fs.mkdirSync(DEST, { recursive: true });
    const veut = VUES
      ? [...VUES].filter(n => n >= 1 && n <= services.length).sort((a, b) => a - b)
      : services.map((_, i) => i + 1);
    if (VUES) {
      // DIRE CE QU'ON NE TIRERA PAS : une vue demandee au-dela du registre disparaissait
      // en silence, et le compte rendu annoncait une plage qu'on n'avait pas eue.
      const hors = [...VUES].filter(n => n < 1 || n > services.length);
      console.log('  vues demandees : ' + veut.join(',')
                  + (hors.length ? '  (hors registre, ignorees : ' + hors.join(',') + ')' : ''));
    }
    for (const n of veut) {
      const i = n - 1;
      const f = path.join(DEST, 'v' + String(i + 1).padStart(3, '0') + '.jpg');
      if (fs.existsSync(f) && fs.statSync(f).size > 50000) continue;
      const b64 = await page.evaluate(async (u) => {
        const r = await fetch(u); if (!r.ok) return 'ERR ' + r.status;
        const b = await r.arrayBuffer(); let s = ''; const a = new Uint8Array(b);
        const CH = 8192; for (let k = 0; k < a.length; k += CH) s += String.fromCharCode.apply(null, a.subarray(k, k + CH));
        return btoa(s);
      }, services[i] + '/full/full/0/native.jpg');
      if (typeof b64 === 'string' && b64.startsWith('ERR')) { console.log('v' + (i + 1) + ' ' + b64); continue; }
      fs.writeFileSync(f, Buffer.from(b64, 'base64'));
      if (VUES || (i + 1) % 20 === 0) console.log('  v' + (i + 1) + '/' + services.length);
      await page.waitForTimeout(p.image.cadence_ms || 1000);
    }
    console.log('fini ' + DEST);
  }
  await ctx.close();
  console.log('\nTOUT FINI');
})();
