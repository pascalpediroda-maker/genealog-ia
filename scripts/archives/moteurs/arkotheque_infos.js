// Resout le NUMERO DE NUMERISATION d'un registre sur un portail ARKOTHEQUE.
//
//   node arkotheque_infos.js 43 <registre> [fiche_registre]
//   node arkotheque_infos.js 43 --commune "Saint-Pal-de-Chalencon"
//
// archives-fr.md disait depuis le 16 aout 2026 que ce numero "ne se devine pas,
// il s'obtient par visionneuse-infos sur la fiche du registre" -- et aucun script
// ne le faisait : on le relevait a la main dans la visionneuse. D'ou celui-ci.
//
// POURQUOI UN VRAI CHROME ET PAS CURL. L'AD43 a un WAF, comme l'AD42. curl
// obtient bien la page de 322 octets qui porte le jeton anti-robot, mais suivre
// la redirection depuis l'exterieur rend "403 Attack detected" (verifie le
// 17 aout 2026 au soir). La recette du carnet -- fetch, puis suivre le
// window.location.href -- ne vaut que DANS le contexte d'une page ouverte par un
// Chrome fenetre. Une fenetre s'ouvre donc a l'ecran, et c'est normal.

const { chromium } = require('playwright');
const fs = require('fs'), path = require('path');

const CONF = JSON.parse(fs.readFileSync(path.join(__dirname, '..', 'portails.json'), 'utf8'));
const args = process.argv.slice(2);
const DEPT = args[0];
const p = CONF.portails.find(x => x.dept === DEPT && x.moteur === 'arkotheque');
if (!p) { console.error('portail arkotheque inconnu pour le departement ' + DEPT); process.exit(1); }
const R = p.recherche;

(async () => {
  const ctx = await chromium.launchPersistentContext('.chrome-' + DEPT, {
    channel: 'chrome', headless: false, viewport: { width: 1200, height: 800 } });
  const page = ctx.pages()[0] || await ctx.newPage();

  // il faut etre sur le site pour que le cookie de session vaille
  await page.goto(p.base + R.chemin, { waitUntil: 'domcontentloaded', timeout: 90000 });
  await page.waitForTimeout(5000);

  // `lire` porte la recette du jeton : la 1re requete rend un HTML de ~322 octets
  // avec window.location.href='/redirect_<JETON>/...'. On la suit UNE fois.
  const lire = async (u) => page.evaluate(async (url) => {
    const get = async (v) => {
      const r = await fetch(v);
      const t = await r.text();
      const m = t.match(/window\.location\.href='([^']+)'/);
      return m ? await (await fetch(m[1])).text() : t;
    };
    return await get(url);
  }, u);

  if (args[1] === '--commune') {
    const c = args[2];
    const sans = c.normalize('NFD').replace(/[̀-ͯ]/g, '');
    const q = `${R.champ_commune}`;
    const u = `${p.base}${R.chemin}?arko_default_liste=1`
      + `&filtreGroupes[groupes][0][${q}][q][]=${encodeURIComponent(c)}`
      + `&filtreGroupes[groupes][0][${q}][q][]=${encodeURIComponent(sans + '[[' + R.fiche_communes + ']]')}`
      + `&filtreGroupes[groupes][0][${q}][extras][mode]=popup`
      + `&--from=0&--resultSize=100`;
    const html = await lire(u);
    // les fiches de registre portent un identifiant vta<hex> ; on les sort avec
    // le libelle qui les suit, pour reperer la periode a l'oeil
    const vus = [...html.matchAll(/(vta[0-9a-f]{16,})/g)].map(m => m[1]);
    console.log('fiches trouvees : ' + [...new Set(vus)].join(' '));
    fs.writeFileSync('arko-liste.html', html);
    console.log('page complete -> arko-liste.html (' + html.length + ' octets)');
  } else {
    const reg = args[1];
    const fiche = args[2] || 'x';
    const u = R.visionneuse_infos.split(' ->')[0]
      .replace('{base}', p.base).replace('{instance}', R.instance)
      .replace('{fiche_registre}', fiche).replace('{visionneuse}', R.visionneuse)
      .replace('{registre}', reg);
    const t = await lire(u);
    let j = null;
    try { j = JSON.parse(t); } catch (e) { /* pas du JSON */ }
    if (!j) {
      console.log('reponse non-JSON (' + t.length + ' octets) :');
      console.log(t.slice(0, 1200));
    } else {
      const s = JSON.stringify(j);
      const num = s.match(/_recherche-images\/show\/(\d+)\/image\/(\d+)\/(\d+)/);
      console.log('registre ' + reg + (num ? ('  ->  numerisation ' + num[1]
        + ', registre ' + num[2] + ', rang de depart ' + num[3]) : '  -> src non trouvee'));
      for (const k of ['nbImages', 'nb_images', 'total', 'nbVues', 'titre', 'title', 'cote'])
        if (j[k] !== undefined) console.log('  ' + k + ' = ' + JSON.stringify(j[k]));
      fs.writeFileSync('arko-infos-' + reg + '.json', JSON.stringify(j, null, 1));
      console.log('  JSON complet -> arko-infos-' + reg + '.json');
    }
  }
  await ctx.close();
})();
