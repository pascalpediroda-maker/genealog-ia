// Telecharge un registre d'un portail ARKOTHEQUE (AD43 et tous les autres qui
// tournent dessus). Le module vaut pour le MOTEUR, pas pour le departement :
// ce qui change d'un portail a l'autre est dans portails.json.
//
//   node arkotheque.js 43 <numerisation> <registre> <nb_vues> <dossier>
//
// `numerisation` et `image_debut` se lisent dans l'URL de la visionneuse, apres
// le # :  .../visionneuse-infos/<instance>/<fiche>/<vis>/image/<image_debut>
// puis l'API visionneuse-infos rend la `src` qui porte le numero de numerisation.
//
// LE PIEGE, ET IL COUTE UNE HEURE SI ON NE LE CONNAIT PAS : la premiere requete
// sur une URL d'image ne rend PAS l'image mais un HTML de 264 octets contenant
// window.location.href='/redirect_<JETON>/...'. Il faut suivre cette redirection
// une fois ; le cookie est alors pose et toutes les suivantes servent le JPEG.
// Quatre motifs d'URL ont ete essayes en vain avant de lire le corps de la reponse.

const { chromium } = require('playwright');
const fs = require('fs'), path = require('path');

// portails.json est dans scripts/archives/, PAS dans moteurs/ : ce chemin etait
// faux et le script mourait sur un ENOENT avant la premiere requete. Corrige le
// 17 aout 2026 au soir, au premier usage reel depuis que le fichier a bouge.
const CONF = JSON.parse(fs.readFileSync(path.join(__dirname, '..', 'portails.json'), 'utf8'));
const [DEPT, NUM, REG, N, DEST] = process.argv.slice(2);
const p = CONF.portails.find(x => x.dept === DEPT && x.moteur === 'arkotheque');
if (!p) { console.error('portail arkotheque inconnu pour le departement ' + DEPT); process.exit(1); }

// {base_images} avant {base} : l'AD45 sert la recherche depuis
// consultation.archives-loiret.fr et LES IMAGES depuis www.archives-loiret.fr.
// Substituer {base} d'abord laisserait le motif le plus long intact.
const vueUrl = (rang) => p.image.vue
  .replace('{base_images}', p.base_images || p.base)
  .replace('{base}', p.base).replace('{numerisation}', NUM)
  .replace('{registre}', REG).replace('{rang}', rang);

(async () => {
  const ctx = await chromium.launchPersistentContext('.chrome-' + DEPT, {
    channel: 'chrome', headless: false, viewport: { width: 1200, height: 800 } });
  const page = ctx.pages()[0] || await ctx.newPage();

  // Il faut etre sur le site pour que le cookie de session vaille -- ET SUR LE
  // DOMAINE QUI SERT LES IMAGES. Le fetch ci-dessous part du contexte de la page :
  // ancre sur consultation.archives-loiret.fr, il tire vers www.archives-loiret.fr
  // et le navigateur le bloque en CORS, « TypeError: Failed to fetch ». La question
  // ne se posait pas en Haute-Loire, ou recherche et images partagent une origine.
  const ancrage = p.base_images ? p.base_images + '/' : p.base + p.recherche.chemin;
  await page.goto(ancrage, { waitUntil: 'domcontentloaded', timeout: 90000 });
  await page.waitForTimeout(5000);

  fs.mkdirSync(DEST, { recursive: true });
  const total = parseInt(N, 10);
  let ok = 0, vide = 0;

  for (let k = 0; k < total; k++) {
    const f = path.join(DEST, 'v' + String(k + 1).padStart(3, '0') + '.jpg');
    if (fs.existsSync(f) && fs.statSync(f).size > 50000) { ok++; continue; }

    const b64 = await page.evaluate(async (u) => {
      const lire = async (url) => {
        const r = await fetch(url);
        const ct = r.headers.get('content-type') || '';
        if (ct.startsWith('image')) return r;
        const t = await r.text();
        const m = t.match(/window\.location\.href='([^']+)'/);   // le jeton anti-robot
        return m ? await fetch(m[1]) : null;
      };
      const r = await lire(u);
      if (!r || !(r.headers.get('content-type') || '').startsWith('image')) return null;
      const b = await r.arrayBuffer(); let s = ''; const a = new Uint8Array(b);
      for (let i = 0; i < a.length; i += 8192) s += String.fromCharCode.apply(null, a.subarray(i, i + 8192));
      return btoa(s);
    }, vueUrl(k));

    if (!b64) { vide++; console.log('v' + (k + 1) + ' : rien'); }
    else { fs.writeFileSync(f, Buffer.from(b64, 'base64')); ok++; }
    if ((k + 1) % 20 === 0) console.log('  ' + (k + 1) + '/' + total);
    await page.waitForTimeout(p.image.cadence_ms || 1000);
  }
  console.log('fini : ' + ok + ' vues, ' + vide + ' manquantes -> ' + DEST);
  await ctx.close();
})();
