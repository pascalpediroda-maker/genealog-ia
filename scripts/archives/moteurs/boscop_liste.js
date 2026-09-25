// Liste les unites numerisees d'une commune sur un portail BOSCOP / Ligeo-Archives.
//
//   node boscop_liste.js 67 GOUGENHEIM
//   node boscop_liste.js 42 "Usson-en-Forez (Loire, France)"
//
// Rend un TSV : ark, cote, description, dates, vues.
// L'ark alimente ensuite boscop.js, qui tire les vues par le manifeste IIIF.
//
// LE PIEGE, ET IL N'EST PAS LE MEME D'UN PORTAIL A L'AUTRE. La Loire se contente
// de RECH_commune, mais veut le LIBELLE COMPLET pose par l'autocomplete —
// « Usson-en-Forez (Loire, France) ». Le Bas-Rhin, lui, IGNORE RECH_commune : il
// exige RECH_commune_Libel ET RECH_commune_Md5, tous deux suffixes d'une barre
// verticale, avec un libelle en MAJUSCULES NUES — « GOUGENHEIM », et surtout pas
// « Gougenheim (Bas-Rhin, France) », qui rend zero reponse. Le Md5 est celui du
// libelle majuscule, verifie au caractere pres : rien a scraper.
//
// Chaque portail porte donc son gabarit d'URL dans portails.json, champ
// `recherche.resultats`, avec {COMMUNE} et {md5} a substituer.
//
// ── UN PORTAIL SERT PLUSIEURS FONDS, ET ILS NE SE FILTRENT PAS PAREIL ────────
// Ajoute le 12 septembre 2026. L'AD16 sert dix fonds ; `recherche.resultats` n'en
// decrit qu'UN (les matricules). Pour l'etat civil, les parametres sont ailleurs,
// dans `fonds.<slug>`, et le champ commune s'y appelle `REch_commune` — E capitale,
// c minuscule. Un parametre inconnu est ignore EN SILENCE et le moteur rend alors
// les 8 409 registres du departement tries par date : ca ressemble parfaitement a
// un resultat de commune. D'ou le mode fonds :
//
//   node boscop_liste.js 16 "Angouleme" --fonds etatcivil --acte mariage --an 1924
//
// LE MD5 EST CELUI DU LIBELLE EN MAJUSCULES NON ACCENTUEES — md5("ANGOULEME"),
// md5("MARIAGE") —, pendant que le parametre `_Libel` porte le libelle affiche.
// Verifie au caractere pres contre les md5 notes dans portails.json.
// ET LES BARRES VERTICALES FINALES COMPTENT : `...Md5=<hash>|`.

const { chromium } = require('playwright');
const crypto = require('crypto');
const fs = require('fs'), path = require('path');

const CONF = JSON.parse(fs.readFileSync(path.join(__dirname, '..', 'portails.json'), 'utf8'));
const ARGS = process.argv.slice(2);
const opt = (nom) => { const i = ARGS.indexOf('--' + nom); return i > 0 ? ARGS[i + 1] : null; };
const [DEPT, COMMUNE] = ARGS;
const FONDS = opt('fonds'), ACTE = opt('acte'), AN = opt('an');
const p = CONF.portails.find(x => x.dept === DEPT && x.moteur === 'boscop');
if (!p || !COMMUNE) {
  console.error('usage : node boscop_liste.js <dept> "<COMMUNE>" [--fonds <slug> --acte <type> --an <annee>]');
  process.exit(1);
}
const F = FONDS ? (p.fonds || {})[FONDS] : null;
if (FONDS && !F) {
  console.error('fonds inconnu : ' + FONDS + '  (connus : '
    + Object.keys(p.fonds || {}).filter(k => (p.fonds[k] || {}).resultats).join(', ') + ')');
  process.exit(1);
}
const R = p.recherche;
if (!F && !R.resultats) { console.error('ce portail boscop n\'a pas de gabarit `recherche.resultats`'); process.exit(1); }

const md5 = s => crypto.createHash('md5').update(s).digest('hex');
// La cle de facette : libelle deaccentue, en capitales.
const cle = s => md5(s.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toUpperCase());

function urlFonds(n) {
  const q = ['type=' + F.type,
             'REch_commune_Libel=' + encodeURIComponent(COMMUNE) + '|',
             'REch_commune_Md5=' + cle(COMMUNE) + '|'];
  if (ACTE) q.push('RECH_typeacte_Libel=' + encodeURIComponent(ACTE) + '|',
                   'RECH_typeacte_Md5=' + cle(ACTE) + '|');
  if (AN) q.push('RECH_unitdate_exacte=' + encodeURIComponent(AN));
  const chemin = n > 1 ? F.resultats.replace(/(\/n:\d+)$/, `$1/page:${n}`) : F.resultats;
  return p.base + chemin + '?' + q.join('&');
}

function urlPage(n) {
  if (F) return urlFonds(n);
  let u = R.resultats
    .replace('{COMMUNE}', encodeURIComponent(COMMUNE))
    .replace('{commune}', encodeURIComponent(COMMUNE))
    .replace('{md5}', md5(COMMUNE))
    .replace('{page}', String(n));
  if (!R.resultats.includes('{page}')) {
    // pagination dans le chemin, a la mode Boscop : /page:N juste avant le ?
    u = u.replace(/(\/n:\d+)(\?)/, `$1/page:${n}$2`);
  }
  return p.base + u;
}

(async () => {
  const ctx = await chromium.launchPersistentContext('.chrome-' + DEPT, {
    channel: 'chrome', headless: false, viewport: { width: 1400, height: 950 } });
  const page = ctx.pages()[0] || await ctx.newPage();

  // passer le defi anti-robot une fois pour toutes (Anubis sur l'AD67)
  await page.goto(p.base + R.chemin, { waitUntil: 'domcontentloaded', timeout: 90000 });
  await page.waitForTimeout(11000);

  const vus = new Map();
  let total = null;
  for (let n = 1; n <= 60; n++) {
    await page.goto(urlPage(n), { waitUntil: 'domcontentloaded', timeout: 90000 });
    await page.waitForTimeout(4500);
    const lot = await page.evaluate(() => {
      const t = document.body.innerText.replace(/\s+/g, ' ');
      const m = t.match(/(\d+)\s*r[ée]ponses?/i);
      const out = [];
      for (const a of document.querySelectorAll('a[href*="ark:"]')) {
        const href = a.getAttribute('href') || '';
        // L'ARK N'EST PAS TOUJOURS UN NOMBRE. La Loire le numerote en chiffres, mais
        // l'AD16 et le portail commun AD79/86 l'ecrivent « vta922a8b35077a220e » —
        // et `(\d+)` ne captait rien : le script annoncait « 1 reponse » puis
        // « 0 unites ecrites », sans dire pourquoi. Corrige le 12 septembre 2026.
        const mk = href.match(/ark:\/\d+\/([A-Za-z0-9._~-]+)/);
        if (!mk) continue;
        const bloc = a.closest('tr,li,article,div.notice');
        const txt = ((bloc ? bloc.innerText : a.textContent) || '')
          .replace(/\s+/g, ' ').trim();
        if (txt.length > 8) out.push({ ark: mk[1], txt: txt.slice(0, 220) });
      }
      return { total: m ? parseInt(m[1], 10) : null, out };
    });
    if (total === null && lot.total !== null) {
      total = lot.total;
      console.error(`${total} reponses pour ${COMMUNE}`);
    }
    let neufs = 0;
    for (const o of lot.out) if (!vus.has(o.ark)) { vus.set(o.ark, o.txt); neufs++; }
    process.stderr.write(`  page ${n} : ${lot.out.length} liens, ${neufs} nouveaux, ${vus.size} au total\r`);
    if (!neufs) break;                       // plus rien de neuf : on s'arrete
    if (total && vus.size >= total) break;
    await page.waitForTimeout(p.image?.cadence_ms || 1000);
  }
  console.error('');

  console.log(['ark', 'notice'].join('\t'));
  for (const [ark, txt] of vus) console.log(ark + '\t' + txt.replace(/\t/g, ' '));
  console.error(`${vus.size} unites ecrites${total ? ' (annonce : ' + total + ')' : ''}`);
  await ctx.close();
})();
