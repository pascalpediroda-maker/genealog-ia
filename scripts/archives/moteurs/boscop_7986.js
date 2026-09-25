// AD79 + AD86 — portail commun Deux-Sevres / Vienne, moteur BOSCOP (Ligeo Archives).
//   https://archives-deux-sevres-vienne.fr
//
// PIEGES PAYES LE 29 AOUT 2026, a ne pas repayer :
//  1. Le slug de l'URL de recherche est `ecalternatif`, mais le `type` interne est
//     `etatcivil`. Les deux se croisent dans les URL.
//  2. Remplir le champ TEXTE de la commune NE FILTRE RIEN : le moteur ne reconnait que le
//     MD5 pose par la facette. Sans lui il rend les 43 000 registres des deux departements
//     tries par date — et ca ressemble parfaitement a un resultat de commune.
//  3. Le md5 se demande a `/arcfacette.php`, qui exige un `token` present dans le HTML de
//     la page de recherche.
//  4. L'URL des resultats porte bien les criteres, mais sous la forme
//     `RECH_<champ>_Libel=<libelle>|` + `RECH_<champ>_Md5=<md5>|` — les pipes finaux
//     comptent. Chemin : /archive/resultats/etatcivil/registres/n:100/page:N ou /limit:25
//     (25 est le maximum offert).
//
//  5. CE PORTAIL SERT ONZE FONDS, PAS UN, et le module n'en connaissait qu'un. Releves le
//     8 septembre 2026 depuis la page d'accueil : etat civil (`ecalternatif`), NOTAIRES
//     (`notaires`), RECENSEMENT (`listerecensement`), militaires, cadastre, hypotheques,
//     enregistrement, enfants trouves, presse, ecrou, Seconde Guerre mondiale. Chacun a son
//     slug, son index et ses champs de facette — la recette ci-dessous est la meme, seuls
//     les trois noms changent. `sonde` les lit sur la page au lieu de les deviner.
//
// Usage :
//   node boscop_7986.js sonde     <slug> <n> [base]  (ex. listerecensement 104) — index et champs
//     `base` ouvre n'importe quel portail Boscop : la recette est celle du moteur, pas du portail.
//     ex. : sonde etatcivil 115 https://lasource.archives.lacharente.fr
//   node boscop_7986.js communes  <debut_du_nom>
//   node boscop_7986.js registres <libelle exact> [md5]
//   node boscop_7986.js manifeste <ark>            (ex. 28387/vta860cb04e6276eb61)
//   node boscop_7986.js tirer     <ark> <dossier> [premiere] [derniere]
const { chromium } = require('playwright');
const fs = require('fs'), path = require('path');
const BASE = 'https://archives-deux-sevres-vienne.fr';
const RECH = BASE + '/archive/recherche/ecalternatif/n:100';

async function ouvrir() {
  const ctx = await chromium.launchPersistentContext('.chrome-profil', {
    channel: 'chrome', headless: false, viewport: { width: 1500, height: 1200 } });
  const page = ctx.pages()[0] || await ctx.newPage();
  return { ctx, page };
}

// LES FONDS, SONDES LE 8 SEPTEMBRE 2026. Trois chaines par fonds, et elles ne se deduisent
// pas les unes des autres : le SLUG de l'URL, le TYPE interne, le nom de l'INDEX.
const FONDS = {
  etatcivil:   { slug: 'ecalternatif',     n: 100, type: 'etatcivil',
                 index: 'ad7986diffusion_exploit_etatcivil',
                 fld: 'RECH_departement|RECH_commune|RECH_paroisse|RECH_typeregistre|RECH_typeacte|RECH_pasteur',
                 chemin: 'registres' },
  recensement: { slug: 'listerecensement', n: 104, type: 'recensement',
                 index: 'ad7986diffusion_exploit_recensement',
                 fld: 'RECH_departement|RECH_commune|RECH_annee',
                 // PAS DE SEGMENT INTERMEDIAIRE ICI : l'etat civil a `/registres/`, le
                 // recensement n'a rien. Une URL fausse rend une page VIDE, pas une erreur —
                 // et une page vide se lit « cette commune n'a pas de recensement en ligne ».
                 chemin: '' },
  // LE PREFIXE DES CHAMPS N'EST PAS LE MEME PARTOUT, ET LE NOM DU CHAMP COMMUNE NON PLUS.
  // L'etat civil et le recensement disent `RECH_commune` ; les notaires disent
  // `Rech_commune_residence`, en minuscules. Une facette interrogee avec le mauvais nom
  // rend zero item — et zero item se lit « cette commune n'a pas de notaire », ce qui est
  // faux. Ces deux chaines se LISENT : le HTML que rend arcfacette.php en cas d'echec
  // porte, dans son propre lien de tri, la liste `fld` exacte que le fonds attend.
  notaires:    { slug: 'notaires',         n: 96,  type: 'notaires',
                 index: 'ad7986diffusion_exploit_notaires',
                 fld: 'Rech_departement|Rech_commune_residence|Rech_notaire|Rech_type_acte',
                 prefixe: 'Rech_', champ_commune: 'commune_residence',
                 chemin: '' },
};

async function facette(page, champ, mot, limit = 40, fonds = 'etatcivil') {
  const F = FONDS[fonds] || FONDS.etatcivil;
  await page.goto(BASE + '/archive/recherche/' + F.slug + '/n:' + F.n,
                  { waitUntil: 'domcontentloaded', timeout: 90000 });
  await page.waitForTimeout(5000);
  return page.evaluate(async ([ch, m, lim, F]) => {
    const tk = document.documentElement.innerHTML.match(/token=([a-z0-9]+)/i);
    if (!tk) return { err: 'token introuvable' };
    const P = F.prefixe || 'RECH_';
    const C = (ch === 'commune' && F.champ_commune) ? F.champ_commune : ch;
    const u = '/arcfacette.php?ind=' + F.index
      + '&fld=' + F.fld
      + '&idf=arc_form_rech&idd=arc_liste_update&type=' + F.type + '&nav=1&limit=' + lim
      + '&token=' + tk[1] + '&id=' + P + C + '&autoc=1&fldcur=' + P + C
      + '&' + P + C + '=' + encodeURIComponent(m);
    const t = await (await fetch(u)).text();
    const out = [];
    const re = new RegExp('facette-select-rech_' + C + '" value="([^"]*)" data-md5="([^"]*)"', 'g');
    let x; while ((x = re.exec(t))) out.push({ libel: x[1], md5: x[2] });
    return { out, brut: out.length ? null : t.slice(0, 600) };
  }, [champ, mot, limit, F]);
}

async function registres(page, libel, md5, fonds = 'etatcivil') {
  const F = FONDS[fonds] || FONDS.etatcivil;
  const P = (F.prefixe || 'RECH_') + (F.champ_commune || 'commune');
  const q = P + '_Libel=' + encodeURIComponent(libel + '|')
          + '&' + P + '_Md5=' + encodeURIComponent(md5 + '|') + '&type=' + F.type;
  const tout = [];
  let total = null;
  // DOUZE PAGES DE VINGT-CINQ FONT TROIS CENTS LIGNES, ET LE FONDS DES NOTAIRES DE COUHE
  // EN COMPTE 627. Le plafond etait ecrit pour l'etat civil d'une commune, ou il ne se voyait
  // pas ; ailleurs il tronque en silence. La boucle s'arrete maintenant sur le TOTAL ANNONCE,
  // qui est le seul chiffre auquel on ait le droit de se comparer.
  for (let p = 1; p <= 60; p++) {
    const u = BASE + '/archive/resultats/' + F.type + (F.chemin ? '/' + F.chemin : '')
            + '/n:' + F.n + '/limit:25/page:' + p + '?' + q;
    await page.goto(u, { waitUntil: 'load', timeout: 90000 });
    await page.waitForTimeout(4500);
    const r = await page.evaluate(() => {
      const t = document.body.innerText;
      const m = t.match(/(\d+) r[ée]ponses/i);
      const rows = [...document.querySelectorAll('table tr')].slice(1).map(tr => {
        const c = [...tr.querySelectorAll('th,td')].map(td => td.innerText.trim().replace(/\s+/g, ' '));
        const a = tr.querySelector('a[href*="ark:"]');
        return { conservation: c[0], commune: c[1], desc: c[2], dates: c[3], cote: c[4],
                 paroisse: c[5], vues: c[6],
                 ark: a ? a.href.split('/daogrp')[0].split('/ark:/')[1] : null };
      }).filter(r => r.commune || r.desc);
      return { total: m ? +m[1] : null, rows };
    });
    if (r.total != null) total = r.total;
    tout.push(...r.rows);
    if (!r.rows.length || tout.length >= (total || 0)) break;
  }
  return { total, rows: tout };
}

async function manifeste(page, ark) {
  await page.goto(BASE + '/ark:/' + ark, { waitUntil: 'domcontentloaded', timeout: 90000 });
  await page.waitForTimeout(6000);
  return page.evaluate(async (a) => {
    for (const u of ['/ark:/' + a + '/manifest', '/ark:/' + a + '/manifest.json']) {
      try {
        const r = await fetch(u); if (!r.ok) continue;
        const j = await r.json();
        const cv = (j.sequences && j.sequences[0] && j.sequences[0].canvases) || j.items || [];
        const svc = cv.map(c => {
          const im = (c.images && c.images[0] && c.images[0].resource)
                  || (c.items && c.items[0] && c.items[0].items && c.items[0].items[0] && c.items[0].items[0].body);
          return im && ((im.service && (im.service['@id'] || im.service.id)) || im['@id'] || im.id);
        }).filter(Boolean);
        return { url: u, n: cv.length, svc };
      } catch (e) {}
    }
    return { err: 'aucun manifeste', apercu: document.body.innerText.slice(0, 600) };
  }, ark);
}

// SONDER UN FONDS QU'ON N'A PAS ENCORE OUVERT — l'index, le type et les champs de facette
// se LISENT dans le HTML de sa page de recherche. Les deviner par analogie avec l'etat civil
// ne marche pas : le slug de l'URL, le `type` interne et le nom de l'index sont trois chaines
// differentes, et elles ne se deduisent pas les unes des autres (`ecalternatif` /
// `etatcivil` / `ad7986diffusion_exploit_etatcivil`).
// `base` EST UN ARGUMENT PARCE QUE LA RECETTE EST CELLE DE BOSCOP, PAS CELLE DE CE PORTAIL.
// Le 9 septembre 2026 il a fallu sonder l'etat civil et les recensements de l'AD16, qui tourne
// sur le meme moteur derriere Anubis : sans ce parametre on recopiait la fonction ailleurs, ce
// que ce dossier existe pour empecher. Le module garde son nom — c'est lui qui porte la recette.
async function sonde(page, slug, n, base) {
  const B = base || BASE;
  await page.goto(B + '/archive/recherche/' + slug + '/n:' + n,
                  { waitUntil: 'domcontentloaded', timeout: 90000 });
  // ANUBIS : une preuve-de-travail qu'un vrai Chrome resout seul, mais qui demande du temps.
  // Six secondes suffisent quand il n'y a pas de mur ; il en faut le double quand il y en a un.
  await page.waitForTimeout(/anubis|within\.website/i.test(await page.content()) ? 16000 : 6000);
  return page.evaluate(() => {
    const h = document.documentElement.innerHTML;
    const u = (r) => [...new Set((h.match(r) || []))];
    return {
      titre: document.title,
      token: (h.match(/token=([a-z0-9]+)/i) || [])[1] || null,
      index: u(/ad7986[a-z0-9_]+/gi),
      type: u(/[?&]type=([a-z0-9]+)/gi),
      champs: u(/RECH_[A-Za-z0-9_]+/g).slice(0, 40),
      // LE CHEMIN DES RESULTATS NE SE DEVINE PAS NON PLUS. Il vaut `registres` pour l'etat
      // civil, et rien ne dit qu'un autre fonds garde le meme mot : une URL fausse rend une
      // page vide, qui ressemble a s'y meprendre a « cette commune n'a pas de registre ».
      resultats: u(/\/archive\/resultats\/[A-Za-z0-9_\/:.-]+/g).slice(0, 12),
      apercu: document.body.innerText.replace(/\s+/g, ' ').slice(0, 400),
    };
  });
}

(async () => {
  const [cmd, ...a] = process.argv.slice(2);
  const { ctx, page } = await ouvrir();
  try {
    if (cmd === 'sonde') {
      console.log(JSON.stringify(await sonde(page, a[0], a[1] || '100', a[2]), null, 1));

    } else if (cmd === 'communes') {
      const f = await facette(page, 'commune', a[0]);
      console.log(JSON.stringify(f.out && f.out.length ? f.out : f, null, 1));

    } else if (cmd === 'registres' || cmd === 'recensements' || cmd === 'notaires') {
      const fonds = cmd === 'registres' ? 'etatcivil'
                  : cmd === 'recensements' ? 'recensement' : 'notaires';
      let libel = a[0], md5 = a[1];
      if (!md5) {
        const f = await facette(page, 'commune', libel.split(' (')[0], 40, fonds);
        const c = (f.out || []).find(o => o.libel === libel) || (f.out || [])[0];
        if (!c) { console.log('commune introuvable ' + JSON.stringify(f).slice(0, 500)); return; }
        libel = c.libel; md5 = c.md5;
        console.log('# ' + libel + '  md5=' + md5);
      }
      const r = await registres(page, libel, md5, fonds);
      console.log('# total annonce : ' + r.total + ' — lignes recuperees : ' + r.rows.length);
      for (const x of r.rows)
        console.log([x.dates, x.desc, x.cote, x.conservation, x.ark || '(pas en ligne)'].join(' | '));

    } else if (cmd === 'manifeste') {
      const m = await manifeste(page, a[0]);
      console.log(JSON.stringify({ url: m.url, n: m.n, err: m.err, apercu: m.apercu, ex: (m.svc || []).slice(0, 2) }, null, 1));

    } else if (cmd === 'tirer') {
      const ark = a[0], dest = a[1], d0 = a[2] || '1', d1 = a[3] || '0';
      const m = await manifeste(page, ark);
      if (!m.svc || !m.svc.length) { console.log('pas de manifeste ' + JSON.stringify(m).slice(0, 500)); return; }
      const deb = parseInt(d0, 10), fin = parseInt(d1, 10) || m.svc.length;
      console.log(m.svc.length + ' vues ; tirage ' + deb + '-' + fin);
      fs.mkdirSync(dest, { recursive: true });
      for (let i = deb; i <= Math.min(fin, m.svc.length); i++) {
        const f = path.join(dest, 'v' + String(i).padStart(3, '0') + '.jpg');
        if (fs.existsSync(f)) { console.log('v' + i + ' deja la'); continue; }
        const b64 = await page.evaluate(async (u) => {
          const r = await fetch(u); if (!r.ok) return 'ERR ' + r.status;
          const b = await r.arrayBuffer(); let s = ''; const arr = new Uint8Array(b);
          for (let k = 0; k < arr.length; k += 8192) s += String.fromCharCode.apply(null, arr.subarray(k, k + 8192));
          return btoa(s);
        }, m.svc[i - 1] + '/full/full/0/native.jpg');
        if (typeof b64 === 'string' && b64.startsWith('ERR')) { console.log('v' + i + ' ' + b64); continue; }
        fs.writeFileSync(f, Buffer.from(b64, 'base64'));
        console.log('v' + i + '/' + fin + '  ' + fs.statSync(f).size);
        await page.waitForTimeout(900);
      }
    } else console.log('commandes : communes | registres | manifeste | tirer');
  } finally { await ctx.close(); }
})();
