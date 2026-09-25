// Liste les registres numerises d'une commune sur un portail ARKOTHEQUE.
//
//   node arkotheque_liste.js 45 "Cléry-Saint-André" [> clery.tsv]
//
// Rend un TSV : cote, paroisse, description, dates, nb_vues, fiche, registre.
// Les deux dernieres colonnes sont ce qu'il faut pour telecharger : `registre`
// est l'idArkoFile a passer a arkotheque_infos.js, qui resout la numerisation,
// puis a arkotheque.js, qui tire les vues.
//
// POURQUOI IL EXISTE. `arkotheque_infos.js --commune` construit l'URL de PAGE de
// l'AD43. L'AD45 ne repond pas a cette forme : ses parametres portent tous le
// prefixe '{instance}--', son champ commune se contente du libelle accentue, et
// c'est /_recherche-api/moteur qui rend le tableau, en JSON. Plutot que de
// tordre le script de l'AD43, celui-ci parle l'API — la forme la plus propre, et
// probablement transposable aux autres portails Arkotheque.
//
// LE PLAFOND QUI NE SE DIT PAS : resultSize est borne a 25 en silence. Demander
// 200 rend 25 sans erreur ni avertissement. On pagine sur `from` et on se fie a
// resultats.total. C'est la meme famille de piege que les parametres ignores
// sans bruit de l'AD37, et elle coute une liste tronquee qu'on croit complete.

const { chromium } = require('playwright');
const fs = require('fs'), path = require('path');

const CONF = JSON.parse(fs.readFileSync(path.join(__dirname, '..', 'portails.json'), 'utf8'));
const [DEPT, COMMUNE, TYPE] = process.argv.slice(2);
const p = CONF.portails.find(x => x.dept === DEPT && x.moteur === 'arkotheque');
if (!p || !COMMUNE) {
  console.error('usage : node arkotheque_liste.js <dept> "<Commune>" [<Type de registre>]');
  process.exit(1);
}
const R = p.recherche;
if (!R.api) { console.error('ce portail arkotheque n\'expose pas /_recherche-api/moteur'); process.exit(1); }

const pref = R.prefixe_params ? R.instance + '--' : '';
const enc = (k, v) => encodeURIComponent(k) + '=' + encodeURIComponent(v);

function urlPage(from, taille) {
  const g = `${pref}filtreGroupes[groupes][0]`;
  const q = [
    enc('refUnique', R.instance),
    enc(`${pref}ficheFocus`, ''),
    enc(`${pref}filtreGroupes[mode]`, 'simple'),
    enc(`${pref}filtreGroupes[op]`, 'AND'),
    enc(`${g}[${R.champ_commune}][op]`, 'AND'),
    enc(`${g}[${R.champ_commune}][q][]`, COMMUNE),
    enc(`${g}[${R.champ_commune}][extras][mode]`, 'popup'),
  ];
  if (TYPE) {
    q.push(enc(`${g}[${R.champ_type_registre}][op]`, 'AND'));
    q.push(enc(`${g}[${R.champ_type_registre}][q][]`, TYPE));
    q.push(enc(`${g}[${R.champ_type_registre}][extras][mode]`, 'select'));
  }
  q.push(enc(`${pref}from`, String(from)));
  q.push(enc(`${pref}resultSize`, String(taille)));
  return p.base + R.api + '?' + q.join('&');
}

(async () => {
  const ctx = await chromium.launchPersistentContext('.chrome-' + DEPT, {
    channel: 'chrome', headless: false, viewport: { width: 1200, height: 800 } });
  const page = ctx.pages()[0] || await ctx.newPage();
  await page.goto(p.base + R.chemin, { waitUntil: 'domcontentloaded', timeout: 90000 });
  await page.waitForTimeout(5000);

  const PAS = 25;                       // le plafond silencieux du portail
  let from = 0, total = null, lignes = [];

  while (total === null || from < total) {
    const lot = await page.evaluate(async (u) => {
      const get = async (v) => {
        const r = await fetch(v);
        const t = await r.text();
        const m = t.match(/window\.location\.href='([^']+)'/);   // le jeton anti-robot
        return m ? await (await fetch(m[1])).text() : t;
      };
      const d = JSON.parse(await get(u));
      const doc = new DOMParser().parseFromString(d.resultats.html, 'text/html');
      const out = [];
      for (const tr of doc.querySelectorAll('tr.resultat_container')) {
        const td = [...tr.querySelectorAll('td')].map(
          c => c.textContent.replace(/\s+/g, ' ').trim());
        const b = tr.querySelector('button[data-visionneuse]');
        let fiche = '', registre = '', vues = '';
        if (b) {
          try {
            const v = JSON.parse(b.getAttribute('data-visionneuse'));
            fiche = v.refUniqueFiche || '';
            registre = v.idArkoFile || '';
          } catch (e) {}
        }
        const mv = (td[td.length - 1] || '').match(/\((\d+)\s*images?\)/);
        vues = mv ? mv[1] : '0';
        out.push({ cote: td[0] || '', lieu: td[1] || '', desc: td[2] || '',
                   notes: td[3] || '', date: td[4] || '', vues, fiche, registre });
      }
      return { total: d.resultats.total, lignes: out };
    }, urlPage(from, PAS));

    if (total === null) {
      total = lot.total;
      console.error(`${total} registres pour ${COMMUNE}${TYPE ? ' / ' + TYPE : ''}`);
    }
    if (!lot.lignes.length) break;
    lignes = lignes.concat(lot.lignes);
    from += PAS;
    process.stderr.write(`  ${Math.min(from, total)}/${total}\r`);
    await page.waitForTimeout(p.image?.cadence_ms || 1000);
  }
  console.error('');

  console.log(['cote', 'lieu', 'description', 'notes', 'dates', 'vues', 'fiche', 'registre'].join('\t'));
  for (const l of lignes) {
    console.log([l.cote, l.lieu, l.desc, l.notes, l.date, l.vues, l.fiche, l.registre]
      .map(x => String(x).replace(/\t/g, ' ')).join('\t'));
  }
  console.error(`${lignes.length} lignes ecrites (annonce : ${total})`);
  await ctx.close();
})();
