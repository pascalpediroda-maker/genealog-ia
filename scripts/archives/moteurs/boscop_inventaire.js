// BOSCOP / LIGEO PAR L'INVENTAIRE — quand le portail n'a pas de champ de commune.
//
//   node boscop_inventaire.js 57 communes [motif]
//   node boscop_inventaire.js 57 registres BOULAY
//   node boscop_inventaire.js 57 registres BOULAY --fonds td
//   node boscop_inventaire.js 57 tirer 23948/1152009.1820667 <archives>/.../BOULAY/100EDGG1 1 258
//   node boscop_inventaire.js 57 sonde <FRAD057_xxx>       (ouvrir un fonds inconnu)
//
// ── POURQUOI UN MODULE A PART, ET PAS UNE LIGNE DE PLUS DANS boscop_liste.js ──────────
// Mesure sur l'AD57 (Moselle) le 19 septembre 2026. `boscop_liste.js` interroge un
// FORMULAIRE : il pose un critere de commune (`RECH_commune`, ou `_Libel` + `_Md5`), lit
// « N reponses » et pagine. Les trois pieces manquent ici, et aucune ne se remplace par
// de la configuration :
//
//  1. AUCUN CHAMP DE LIEU N'EXISTE. Le seul formulaire d'archives est
//     /archive/recherche/simple/n:19 et ses champs sont RECH_S (plein texte),
//     RECH_SELECTOR, RECH_physloc (cote), RECH_TYP, RECH_dates_*. Mesure : ajouter
//     `RECH_commune=ZZZZZZZ` a une recherche rend EXACTEMENT le meme total que sans —
//     4 357 dans les deux cas. Le parametre inconnu est ignore en silence, comme partout.
//  2. LE PLEIN TEXTE N'EST PAS UN FILTRE DE COMMUNE, ET IL SUR-REND. `RECH_S=BOULAY`
//     restreint a l'inventaire de l'etat civil rend 38 notices ; l'arbre de BOULAY en
//     porte 30. Les huit autres sont VOLMERANGE-LES-BOULAY. 27 % de faux positifs, sans
//     un mot — et sur un patronyme de commune plus commun ce serait pire.
//  3. IL N'Y A RIEN A PAGINER. L'inventaire rend ses 976 communes en UNE page, et le
//     detail d'une commune rend TOUS ses registres en une page : 142 pour METZ, sans
//     pagination (zero occurrence de /page: dans le pane). La boucle de pagination de
//     `boscop_liste.js` n'a pas d'objet ici.
//
// Ce que `boscop_liste.js` fait bien, en revanche, il le ferait ici aussi : son selecteur
// `a[href*="ark:"]` RENDRAIT des arks sur ce portail. La fiche portails.json affirmait le
// contraire — « il rendrait zero sur une page pleine » —, c'est faux, mesure : 11 arks sur
// la page de resultats de Cocheren, 20 par page sur celle de Boulay. L'ark mosellan porte
// un POINT (`23948/1439585.1820648`), et la regexp `[A-Za-z0-9._~-]+` de boscop_liste.js
// l'accepte deja. Le mur n'etait pas l'extraction : c'est le CHEMIN D'ACCES.
//
// ── CE QUE CE MODULE FAIT, ET IL VAUT POUR TOUT LIGEO ─────────────────────────────────
// Un inventaire Ligeo est un ARBRE de notices. Deux routes, et elles suffisent :
//   /archives/fonds/<FONDS>            → la racine : tous les noeuds de premier niveau
//   /archives/fonds/<FONDS>/view:<id>  → le detail d'un noeud : ses enfants, avec cote,
//                                        intitule, dates, nombre de vues et ARK
// Puis l'image, qui est du IIIF standard :
//   /ark:/<prefixe>/<ark>/manifest     → le manifeste, un canvas par vue
//   <service>/full/full/0/native.jpg   → la vue a sa taille native
//
// RECOMPTE, parce qu'une liste qui tronque en silence est le defaut maison de ce dossier :
// Cocheren rend 11 notices par l'arbre et 11 par la recherche plein texte restreinte au
// meme inventaire. Les deux routes tombent d'accord. Pour BOULAY l'arbre en rend 30 et la
// recherche 38 — et ce sont les huit de trop qui sont faux, pas les trente qui manquent.
//
// ── LES FONDS DE LA MOSELLE ──────────────────────────────────────────────────────────
// Leur place est dans portails.json ; ils sont ici en attendant que le généalogiste valide la fiche.
// Chacun est un arbre de communes, SAUF les matricules qui sont un arbre de CLASSES.

const { chromium } = require('playwright');
const fs = require('fs'), path = require('path');

const CONF = JSON.parse(fs.readFileSync(path.join(__dirname, '..', 'portails.json'), 'utf8'));

const FONDS = {
  '57': {
    ec:          { id: 'FRAD057_605804',  quoi: 'registres paroissiaux et etat civil numerises', noeuds: 976 },
    // Le 7E est l'inventaire PAPIER du meme etat civil : il decrit des cotes, il ne porte
    // pas d'images. On le garde parce qu'il dit ce qui EXISTE quand `ec` ne dit que ce qui
    // est numerise — et l'ecart entre les deux est une question de recherche, pas un bug.
    ec_papier:   { id: 'FRAD057_954653',  quoi: '7E - etat civil (inventaire, non numerise)', noeuds: 931 },
    td:          { id: 'FRAD057_698861',  quoi: 'tables decennales', noeuds: 974 },
    recensement: { id: 'FRAD057_1018915', quoi: 'recensements de la population', noeuds: 71 },
    matricules:  { id: 'FRAD057_720959',  quoi: 'registres matricules (arbre de CLASSES)', noeuds: 29 },
  },
};

const ARGS = process.argv.slice(2);
const opt = (n) => { const i = ARGS.indexOf('--' + n); return i >= 0 ? ARGS[i + 1] : null; };
const libre = ARGS.filter((a, i) => !a.startsWith('--') && !(i > 0 && ARGS[i - 1].startsWith('--')));
const [DEPT, CMD, CIBLE, DEST, D0, D1] = libre;
const SLUG = opt('fonds') || 'ec';

const p = CONF.portails.find(x => x.dept === DEPT && x.moteur === 'boscop');
if (!p || !CMD) {
  console.error('usage : node boscop_inventaire.js <dept> communes|registres|tirer|sonde [cible] [--fonds ec|td|recensement|matricules]');
  process.exit(1);
}
const T = (FONDS[DEPT] || {})[SLUG];
if (!T && CMD !== 'sonde') {
  console.error('fonds inconnu : ' + SLUG + '  (connus : ' + Object.keys(FONDS[DEPT] || {}).join(', ') + ')');
  process.exit(1);
}
const BASE = p.base;
// Le prefixe ark se LIT dans les liens, il ne se devine pas. Celui de la Moselle est 23948.
const PREFIXE = p.ark_prefixe || '23948';

// UN NOM DE COMMUNE SE DESIGNE, IL NE SE RECOPIE PAS. L'inventaire ecrit « BOULAY » ici,
// « Boulay (Bolchen) » dans les tables decennales — le meme village, deux libelles. On
// compare donc sans accent, sans casse, et sur le DEBUT du libelle : « Boulay (Bolchen) »
// et « BOULAY : voir aussi… » repondent tous deux a `boulay`. Une designation ambigue est
// REFUSEE avec la liste des candidats : ouvrir le mauvais registre est pire qu'echouer.
const pli = s => (s || '').normalize('NFD').replace(/[\u0300-\u036f]/g, '')
  .toUpperCase().replace(/[^A-Z0-9]+/g, ' ').trim();

// ── LES DEUX LECTURES DE PAGE ────────────────────────────────────────────────────────
function noeudsDe(html) {
  const out = [];
  const re = /\/view:(\d+)" id="tv_a3node-notice-\d+"[^>]*>([^<]*)</g;
  let m; while ((m = re.exec(html))) out.push({ id: m[1], nom: deco(m[2]).trim() });
  return out;
}
function deco(s) {
  return s.replace(/&#(\d+);/g, (_, d) => String.fromCharCode(+d))
    .replace(/&amp;/g, '&').replace(/&lt;/g, '<').replace(/&gt;/g, '>')
    .replace(/&quot;/g, '"').replace(/&nbsp;/g, ' ')
    .replace(/&eacute;/g, 'é').replace(/&egrave;/g, 'è').replace(/&agrave;/g, 'à')
    .replace(/&ccedil;/g, 'ç').replace(/&uuml;/g, 'ü').replace(/&ocirc;/g, 'ô');
}
function registresDe(html) {
  const d = html.split('id="arc_col_droite"')[1];
  if (!d) return [];
  const out = [];
  const re = /<li class="arc_notice ?" id="N_(\d+)">([\s\S]*?)(?=<li class="arc_notice ?" id="N_|$)/g;
  let m;
  while ((m = re.exec(d))) {
    const b = m[2];
    const g = (k) => { const x = b.match(new RegExp('<span class="' + k + '">([\\s\\S]*?)</span>'));
      return x ? deco(x[1].replace(/<[^>]+>/g, '')).replace(/\s+/g, ' ').replace(/\s*-\s*$/, '').trim() : ''; };
    const ark = b.match(/href="\/ark:\/(\d+\/[\d.]+)"/);
    const vues = b.match(/<p class="nb_vues">\s*(\d+)/);
    out.push({ id: m[1], cote: g('cote'), titre: g('unittitle'), dates: g('date'),
               vues: vues ? +vues[1] : null, ark: ark ? ark[1] : null });
  }
  return out;
}

// ── LE NAVIGATEUR ────────────────────────────────────────────────────────────────────
// Anubis pose sa preuve-de-travail une fois par profil : on attend TANT QUE le defi est la,
// au lieu de dormir un temps arbitraire (meme recette que lire_page.js).
const DEFI = [/within\.website/i, /making sure you'?re not a bot/i, /just a moment/i,
              /attack detected/i, /checking your browser/i, /altcha/i];
async function html(page, url) {
  await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 90000 });
  let h = await page.content(), t = 0;
  while ((DEFI.some(r => r.test(h)) || h.length < 6000) && t < 60000) {
    await page.waitForTimeout(3000); t += 3000; h = await page.content();
  }
  return h;
}

(async () => {
  const dom = new URL(BASE).hostname;
  const ctx = await chromium.launchPersistentContext('.chrome-' + dom, {
    channel: 'chrome', headless: false, viewport: { width: 1400, height: 950 } });
  const page = ctx.pages()[0] || await ctx.newPage();
  try {
    if (CMD === 'sonde') {
      const h = await html(page, BASE + '/archives/fonds/' + (CIBLE || T.id));
      const n = noeudsDe(h);
      console.log('# ' + (CIBLE || T.id) + ' — ' + n.length + ' noeuds de premier niveau'
        + '  (pagination : ' + (/\/page:|tv_page/.test(h) ? 'OUI ⚠️' : 'aucune') + ')');
      for (const x of n.slice(0, 15)) console.log('  ' + x.id + '\t' + x.nom);
      if (n.length > 15) console.log('  …');
      return;
    }

    // Toujours partir de la racine : c'est elle qui donne l'id du noeud, et elle tient en
    // une requete. La recompter contre le nombre note dans FONDS signale une refonte du
    // fonds plutot que de la laisser passer en silence.
    const racine = await html(page, BASE + '/archives/fonds/' + T.id);
    const noeuds = noeudsDe(racine);
    if (/\/page:|tv_page/.test(racine))
      console.error('⚠️ cet inventaire pagine — la racine n\'est PAS complete, voir le module');
    if (T.noeuds && noeuds.length !== T.noeuds)
      console.error('⚠️ ' + noeuds.length + ' noeuds lus, ' + T.noeuds + ' attendus — le fonds a bouge');

    if (CMD === 'communes') {
      const f = CIBLE ? pli(CIBLE) : null;
      const l = f ? noeuds.filter(x => pli(x.nom).includes(f)) : noeuds;
      console.log('# ' + T.id + ' — ' + T.quoi + ' — ' + noeuds.length + ' noeuds'
        + (f ? ', ' + l.length + ' retenus' : ''));
      for (const x of l) console.log(x.id + '\t' + x.nom);
      return;
    }

    if (CMD === 'registres') {
      if (!CIBLE) { console.error('donner une commune'); return; }
      let id = /^\d+$/.test(CIBLE) ? CIBLE : null;
      if (!id) {
        const c = pli(CIBLE);
        let cand = noeuds.filter(x => pli(x.nom) === c);
        if (!cand.length) cand = noeuds.filter(x => pli(x.nom).startsWith(c + ' ') || pli(x.nom).startsWith(c + ':'));
        if (!cand.length) cand = noeuds.filter(x => pli(x.nom).includes(c));
        if (!cand.length) { console.error('commune introuvable : ' + CIBLE); return; }
        if (cand.length > 1) {
          console.error('designation ambigue — preciser, ou donner l\'id :');
          for (const x of cand) console.error('   ' + x.id + '\t' + x.nom);
          return;
        }
        id = cand[0].id;
        console.log('# ' + cand[0].nom + '  (noeud ' + id + ')');
      }
      const h = await html(page, BASE + '/archives/fonds/' + T.id + '/view:' + id);
      const r = registresDe(h);
      if (/arc_pagination|\/page:/.test(h.split('id="arc_col_droite"')[1] || ''))
        console.error('⚠️ le detail de ce noeud PAGINE — la liste ci-dessous est partielle');
      console.log(['ark', 'cote', 'dates', 'vues', 'intitule'].join('\t'));
      let n = 0;
      for (const x of r) {
        if (!x.ark || !/\./.test(x.ark)) continue;        // le noeud commune lui-meme n'a pas de point
        n++;
        console.log([x.ark, x.cote, x.dates, x.vues == null ? '?' : x.vues, x.titre].join('\t'));
      }
      console.error(n + ' unites numerisees (' + r.length + ' notices dans le noeud)');
      return;
    }

    if (CMD === 'tirer') {
      if (!CIBLE || !DEST) { console.error('donner <ark> <dossier> [premiere] [derniere]'); return; }
      await html(page, BASE + '/ark:/' + CIBLE + '/dao/0');
      const m = await page.evaluate(async (a) => {
        const x = await fetch('/ark:/' + a + '/manifest');
        if (!x.ok) return { err: x.status };
        const j = await x.json();
        const cv = (j.sequences && j.sequences[0] && j.sequences[0].canvases) || [];
        return { label: typeof j.label === 'string' ? j.label : JSON.stringify(j.label),
                 svc: cv.map(c => c.images[0].resource.service['@id']) };
      }, CIBLE);
      if (!m.svc || !m.svc.length) { console.error('pas de manifeste : ' + JSON.stringify(m)); return; }
      console.log(m.label);
      const deb = parseInt(D0 || '1', 10), fin = Math.min(parseInt(D1 || '0', 10) || m.svc.length, m.svc.length);
      console.log(m.svc.length + ' vues ; tirage ' + deb + '-' + fin);
      fs.mkdirSync(DEST, { recursive: true });
      for (let i = deb; i <= fin; i++) {
        // LE NUMERO DE VUE EST DANS LE NOM DU FICHIER, PAS DANS SA POSITION : on ne tire
        // presque jamais un registre en entier, et indexer une liste triee ferait lire un
        // acte pour un autre.
        const f = path.join(DEST, 'v' + String(i).padStart(3, '0') + '.jpg');
        if (fs.existsSync(f)) { console.log('v' + i + ' deja la'); continue; }
        const b64 = await page.evaluate(async (u) => {
          const x = await fetch(u); if (!x.ok) return 'ERR ' + x.status;
          const b = await x.arrayBuffer(); let s = ''; const arr = new Uint8Array(b);
          for (let k = 0; k < arr.length; k += 8192) s += String.fromCharCode.apply(null, arr.subarray(k, k + 8192));
          return btoa(s);
        }, m.svc[i - 1] + '/full/full/0/native.jpg');
        if (typeof b64 === 'string' && b64.startsWith('ERR')) { console.log('v' + i + ' ' + b64); continue; }
        fs.writeFileSync(f, Buffer.from(b64, 'base64'));
        console.log('v' + i + '/' + fin + '  ' + fs.statSync(f).size);
        await page.waitForTimeout(p.image?.cadence_ms || 900);
      }
      return;
    }
    console.error('commandes : communes | registres | tirer | sonde');
  } finally { await ctx.close(); }
})();
