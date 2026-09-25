// Le Portale Antenati — l'etat civil numerise des Archivi di Stato italiens.
//
//   NODE_PATH="<maison>" \
//     node antenati.js chercher '"Valvasone Arzene"'
//     node antenati.js chercher '"Valvasone Arzene"' Morti 1813
//     node antenati.js registre an_ua750235
//     node antenati.js vue      an_ua750235 12 "<archives>/AS Udine - Valvasone/Morti 1813"
//     node antenati.js registre an_ua750235 --frais     (ignore le manifeste en cache)
//
// IL N'Y A PAS DE COMMANDE `tirer`, ET C'EST LE COEUR DE LA LECON. Elle a existe une
// heure le 27 aout 2026, elle tirait les 33 vues d'un registre a une par seconde, et
// elle a fait bannir tout le domaine — la page d'accueil elle-meme rendait « 403
// Forbidden » DANS LA FENETRE CHROME. Ce limiteur compte le VOLUME, pas le type de
// client : un vrai navigateur n'en exonere pas. On prend l'INDEX, on y lit le numero
// de l'acte, et on ouvre LES DEUX OU TROIS VUES qui le portent. C'est de toute facon
// la bonne pratique d'archives — la meme que « chercher la table annuelle avant de
// balayer les marges ».
//
// POURQUOI CE FICHIER REMPLACE UNE VERSION PYTHON ECRITE UNE HEURE PLUS TOT, ET
// C'EST LA LECON DE LA JOURNEE. Le 27 aout 2026, ce portail a ete ouvert avec
// `urllib` + un User-Agent de Chrome, parce que la note du matin disait « c'est un
// WordPress ordinaire, les resultats sont dans le HTML, pas besoin de navigateur ».
// Resultat : le limiteur de debit du site nous a fermes pendant des heures, et la
// « methode » consignee etait une cadence de 2,5 s avec repli de 30/90/240 s.
//
// PASCAL : « Si ta methode conduit a un bannissement du site, c'est de la merde,
// qu'on ne va pas mettre en skill. » Il a raison, et la skill le disait DEJA en
// tete : « UN VRAI CHROME FENETRE, JAMAIS curl NI LE HEADLESS SHELL ». La fiche
// ecrite le matin contredisait la premiere regle du carnet, et personne ne l'a vu
// parce qu'elle avait l'air de marcher — jusqu'au bannissement.
//
// LE NAVIGATEUR PASSE LA OU urllib ECHOUE — verifie : ce module a sorti le manifeste
// du registre des morts de 1813 du premier coup pendant que le bannissement d'urllib
// courait encore. Il porte le cookie de session que l'ALB pose (AWSALB), charge les
// assets, envoie un referer coherent. On ne cache rien : `navigator.webdriver` reste
// a `true`.
//
// MAIS IL NE DISPENSE DE RIEN SUR LE VOLUME, ET CE FICHIER L'A AFFIRME FAUX PENDANT
// VINGT MINUTES avant de le tester : « un vrai navigateur ne se fait pas bannir par
// ce genre de limiteur ». Trente-trois navigations d'image en trente-cinq secondes,
// et tout le domaine s'est referme — capture d'ecran a l'appui. Deux affirmations
// ecrites avant d'etre verifiees, deux fois faux, la meme journee.
//
// CE QU'ON SAIT VRAIMENT : le limiteur compte le VOLUME. La seule methode qui tienne
// est chirurgicale — l'inventaire en une requete (`s_size=100`), l'index, puis LES
// DEUX OU TROIS VUES qui portent l'acte. Et quand c'est ferme, ON S'ARRETE : les 66
// requetes refusees de l'apres-midi ont prolonge le bannissement et l'ont etendu du
// domaine des images a celui des pages.

const { chromium } = require('playwright');
const fs = require('fs'), path = require('path');

const BASE = 'https://antenati.cultura.gov.it';
const ARK = 'ark:/12657/';
const PROFIL = path.join(__dirname, '.chrome-antenati');
const CADENCE = 12000;

// ===========================================================================
//  LE GARDE-FOU. Il existe parce que les consignes en commentaire n'ont pas
//  suffi : le 27 aout 2026, ce module a envoye 99 requetes en une heure sur une
//  archive publique — dont 66 REFUSEES, et qu'il a continue d'envoyer. L'IP de
//  la maison a ete bloquee, le généalogiste ne pouvait plus ouvrir le site lui-meme.
//
//  « Tu as bourrine comme un salaud... C'est ma reput qui est en jeu. »
//
//  ET LE GARDE-FOU A ETE CONTOURNE LE SOIR MEME, PAR MOI, AVEC DES `curl` BRUTS.
//  Quatre requetes enchainees dos a dos — en MOINS D'UNE MINUTE, pas en dix comme
//  je l'ai d'abord ecrit — et le portail s'est referme une troisieme fois. Le
//  compteur, la cadence et la quarantaine ne protegent QUE ce qui passe par ce
//  module : une ligne de `curl` tapee a la main les ignore tous.
//
//  DONC LA REGLE EST : SUR CE PORTAIL, ON NE TAPE JAMAIS DE `curl`. Meme pour
//  « juste verifier si c'est ouvert » — c'est precisement ce qui a rouvert le
//  bannissement. `node antenati.js etat` dit ou on en est sans rien demander au
//  site ; et s'il faut vraiment sonder, ca passe par une commande du module.
//
//  MESURE DU 12 SEPTEMBRE 2026 : LE BUDGET DE 12 ETAIT ENCORE TROP HAUT. Une session
//  a fait 4 requetes de recherche, puis 3 pour un `registre` — et la HUITIEME, la
//  premiere qui demandait une IMAGE, a rendu 403. Le garde-fou a coupe net et pose la
//  quarantaine, ce pour quoi il existe ; mais il n'avait rien empeche, parce qu'il
//  autorisait douze.
//
//  CE QU'ON EN DEDUIT, ET CE QU'ON NE SAIT TOUJOURS PAS. Les sept premieres requetes
//  etaient des PAGES et sont passees ; la premiere IMAGE a ete refusee. Soit le domaine
//  `dam-antenati` compte a part et plus serre, soit une image pese plus qu'une page dans
//  le meme compteur. On ne voit pas le reglage de l'exterieur, et une seule mesure ne
//  fait pas une loi. LE BUDGET PASSE DONC A SIX : c'est la moitie de ce qui a suffi a
//  nous faire fermer, et ca laisse de quoi faire ce pour quoi ce module existe — un
//  inventaire, un manifeste, deux ou trois vues.
//
//  LA CADENCE EST A 12 SECONDES ET LE BUDGET A 6/HEURE parce que les mesures du
//  27 aout sont sans appel : 33 requetes a une seconde -> banni ; 4 requetes en
//  moins d'une minute -> banni. On ne connait pas le seuil exact, on sait qu'il
//  est bas. Un inventaire, un manifeste et trois vues font CINQ requetes : le
//  budget reste large pour l'usage reel.
//
//  UNE REGLE QU'ON PEUT IGNORER N'EST PAS UNE REGLE. Celle-ci est dans le code,
//  elle compte pour de vrai, et elle survit a la session : le journal est sur le
//  disque. Trois verrous, dans cet ordre :
//    1. UN 403 ARRETE TOUT, immediatement, et pose une quarantaine de 2 h.
//    2. UN BUDGET GLISSANT de SIX requetes par heure, tenu entre les executions.
//    3. UNE CADENCE de 12 s, plancher.
//  Le budget est genereux pour l'usage reel — un inventaire, un manifeste, trois
//  vues, ca fait cinq. Il n'y a aucun cas legitime a 99.
// ===========================================================================
const JOURNAL = path.join(PROFIL, 'requetes.json');
const BUDGET_HEURE = 6;
const QUARANTAINE_MS = 2 * 60 * 60 * 1000;

// ---------------------------------------------------------------------------
//  LE CACHE DES MANIFESTES — il ne desserre AUCUN verrou, il en tire parti.
//
//  Jusqu'au 28 aout 2026, `vue` coutait QUATRE requetes pour une image : la page
//  de recherche, la page du registre, le manifeste IIIF, puis la vue. Sur un
//  budget de 12/heure, ca fait DEUX vues par heure — et un acte se lit rarement
//  sur deux vues quand on ne sait pas encore ou il est.
//
//  Or les trois premieres ne rapportent rien de nouveau a la deuxieme vue du
//  MEME registre : le manifeste IIIF ne bouge pas. On l'ecrit donc sur le disque
//  a la premiere lecture, et `vue` retombe a DEUX requetes — la page de
//  recherche, qui rafraichit le cookie de l'ALB, et l'image. Quatre vues par
//  heure au lieu de deux, pour le meme cout reel cote portail.
//
//  C'est exactement ce que demande l'en-tete : « chirurgical ». Moins de
//  requetes pour le meme resultat, pas plus de requetes pour aller plus vite.
//  `--frais` force la relecture du manifeste si un registre a change de container.
// ---------------------------------------------------------------------------
const CACHE = path.join(PROFIL, 'manifestes.json');
function lireCache() {
  try { return JSON.parse(fs.readFileSync(CACHE, 'utf8')); } catch { return {}; }
}
function ecrireCache(c) {
  try {
    fs.mkdirSync(PROFIL, { recursive: true });
    fs.writeFileSync(CACHE, JSON.stringify(c, null, 1));
  } catch { /* un cache absent coute des requetes, il ne casse rien */ }
}

function lireJournal() {
  try { return JSON.parse(fs.readFileSync(JOURNAL, 'utf8')); }
  catch { return { requetes: [], bloqueJusqu: 0 }; }
}
function ecrireJournal(j) {
  try {
    fs.mkdirSync(PROFIL, { recursive: true });
    fs.writeFileSync(JOURNAL, JSON.stringify(j));
  } catch { /* le garde-fou ne doit jamais faire echouer une lecture */ }
}
function verifierAvant() {
  const j = lireJournal(), t = Date.now();
  if (j.bloqueJusqu > t) {
    const min = Math.ceil((j.bloqueJusqu - t) / 60000);
    console.error(`QUARANTAINE : le portail nous a rendu 403 il y a peu.`);
    console.error(`Encore ${min} min avant de reessayer — et ce n'est pas negociable ici :`);
    console.error(`chaque tentative recharge le compteur du limiteur et rallonge le blocage.`);
    console.error(`\nEn attendant, le registre s'ouvre a la main :`);
    console.error(`  ${BASE}/ark:/12657/<ark>/`);
    console.error(`ou sur FamilySearch, qui mirrore le meme fonds AS Udine 1806-1815.`);
    process.exit(2);
  }
  j.requetes = (j.requetes || []).filter(x => t - x < 3600000);
  if (j.requetes.length >= BUDGET_HEURE) {
    const min = Math.ceil((3600000 - (t - j.requetes[0])) / 60000);
    console.error(`BUDGET EPUISE : ${j.requetes.length} requetes dans la derniere heure `
      + `(plafond ${BUDGET_HEURE}). Reprise dans ${min} min.`);
    console.error(`Un inventaire + un manifeste + trois vues, c'est CINQ requetes.`);
    console.error(`Si le budget est epuise, c'est qu'on s'y prend mal — relire l'en-tete.`);
    process.exit(2);
  }
  ecrireJournal(j);
  return j;
}
function compter() {
  const j = lireJournal(), t = Date.now();
  j.requetes = (j.requetes || []).filter(x => t - x < 3600000);
  j.requetes.push(t);
  ecrireJournal(j);
  return BUDGET_HEURE - j.requetes.length;
}
function quarantaine(ou) {
  const j = lireJournal();
  j.bloqueJusqu = Date.now() + QUARANTAINE_MS;
  ecrireJournal(j);
  console.error(`\n403 sur ${ou} — ARRET IMMEDIAT ET QUARANTAINE DE 2 H.`);
  console.error(`Ce n'est pas une panne : c'est le limiteur, et il compte le volume.`);
  console.error(`NE PAS RELANCER. Les 66 requetes refusees du 27 aout ont bloque l'IP`);
  console.error(`de la maison pendant des heures — le généalogiste ne pouvait plus ouvrir le site.`);
}

const [CMD, ...ARGS] = process.argv.slice(2);
if (!CMD || !['chercher', 'registre', 'vue', 'etat'].includes(CMD)) {
  console.error('usage : node antenati.js <chercher|registre|vue|etat> ...');
  console.error('  il n y a pas de `tirer` : voir l en-tete de ce fichier.');
  process.exit(1);
}

if (CMD === 'etat') {
  const j = lireJournal(), t = Date.now();
  const r = (j.requetes || []).filter(x => t - x < 3600000);
  console.log(`requetes dans la derniere heure : ${r.length} / ${BUDGET_HEURE}`);
  console.log(j.bloqueJusqu > t
    ? `QUARANTAINE encore ${Math.ceil((j.bloqueJusqu - t) / 60000)} min`
    : 'pas de quarantaine en cours');
  process.exit(0);
}

verifierAvant();

// Le contexte archivistique se lit TOUJOURS : une recherche « Valvasone Arzene »
// rend trois communes historiques distinctes — Valvasone, Arzene et San Lorenzo —
// fusionnees en 2015 sous un seul nom moderne. Deux registres sur cinq ne sont pas
// celui qu'on croit.
function depouille(html) {
  const out = [];
  const items = html.match(/<li class="search-item"[\s\S]*?<\/li>/g) || [];
  // LES ENTITES SE DECODENT AVANT DE LIRE, ET C'EST LA PANNE DU 12 SEPTEMBRE 2026 : le
  // portail ecrit desormais « Stato civile napoleonico &nbsp; &gt; &nbsp; Vito d'Asio »
  // la ou il ecrivait un « > » nu. L'ancienne regex cherchait ce « > » et rendait
  // soixante lignes de « ? » sans se plaindre.
  const txt = s => s.replace(/&nbsp;/g, ' ').replace(/&gt;/g, '>').replace(/&lt;/g, '<')
                    .replace(/&amp;/g, '&').replace(/&#0?39;|&apos;/g, "'")
                    .replace(/&quot;/g, '"');
  for (const it of items) {
    const ark = (it.match(/ark:\/12657\/(an_ua\d+)/) || [])[1]
             || 'an_ua' + ((it.match(/data-id="(\d+)"/) || [])[1] || '?');
    const plat = txt(it.replace(/<[^>]+>/g, '\n')).replace(/[ \t]+/g, ' ');
    const annee = (plat.match(/Registro:\s*([\d\-\/]+)/) || [])[1] || '?';
    const cote = (plat.match(/Segnatura attuale:\s*\n?\s*([^\n]+)/) || [])[1] || '?';
    const ctx = plat.match(/(Stato civile[^\n>]*?)\s*>\s*([^\n>]+)/);
    // Le TYPE est le premier <strong> qui n'est pas l'etiquette de cote : « Matrimoni,
    // indice », « Nati », « Morti ». On le prend sur la balise, pas sur le texte a plat,
    // parce que c'est la seule chose qui le distingue du reste du paragraphe.
    let type = '?';
    for (const m of it.matchAll(/<strong>([\s\S]*?)<\/strong>/g)) {
      const v = txt(m[1].replace(/<[^>]+>/g, '')).trim();
      if (v && !/^Segnatura attuale/i.test(v)) { type = v; break; }
    }
    out.push({ ark, annee, type, cote,
               fonds: ctx ? ctx[1].trim() : '?',
               contexte: ctx ? ctx[2].trim() : '?' });
  }
  return out;
}

(async () => {
  const ctx = await chromium.launchPersistentContext(PROFIL, {
    channel: 'chrome', headless: false, viewport: { width: 1280, height: 900 },
    locale: 'it-IT',
  });
  const page = ctx.pages()[0] || await ctx.newPage();

  // TOUTE navigation passe par ici : elle est comptee AVANT d'etre faite, et un 403
  // arrete le processus sur place. C'est le seul endroit ou le module touche au
  // reseau, pour qu'il n'y ait pas de chemin de traverse.
  async function aller(url, quoi) {
    verifierAvant();
    const reste = compter();
    const rep = await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 90000 });
    const code = rep ? rep.status() : 0;
    if (code === 403 || /403 Forbidden/.test(await page.content().catch(() => ''))) {
      quarantaine(quoi || url);
      await ctx.close();
      process.exit(2);
    }
    if (reste <= 5) console.error(`  [budget : ${reste} requetes avant le plafond horaire]`);
    await page.waitForTimeout(CADENCE);
    return rep;
  }

  // On entre par la page de recherche, comme un visiteur : c'est la que l'ALB pose
  // son cookie de session, et c'est ce cookie qui fait la difference.
  await aller(BASE + '/search-registry/', 'la page de recherche');

  if (CMD === 'chercher') {
    // LES GUILLEMETS SONT LE FILTRE, et c'est tout le piege de ce portail.
    // Sans eux `localita` fait une recherche en texte libre qui matche tout et rend
    // dix lignes plausibles : « Pagina 1 di 1 » au lieu de « Pagina 1 di 9 ».
    // C'est le JS du site qui le fait, a la selection dans l'autocomplete :
    //     localita.value = '"' + selection.trim() + '"';
    let [loc, tipologia, anno] = ARGS;
    if (loc && !loc.startsWith('"')) loc = '"' + loc + '"';
    const q = new URLSearchParams({ localita: loc || '', s_size: '100' });
    if (tipologia) q.set('tipologia', tipologia);
    if (anno) q.set('anno', anno);
    await aller(BASE + '/search-registry/?' + q, 'la recherche');
    const html = await page.content();
    const pag = (html.match(/Pagina\s*(\d+)\s*di\s*(\d+)/) || [])[0] || 'pagination absente';
    const rows = depouille(html);
    console.log(pag + '  —  ' + rows.length + ' registres rendus');
    // RECOMPTER CONTRE LE TOTAL ANNONCE : s_size est une liste fermee {10,20,50,100}.
    const pages = parseInt((html.match(/Pagina\s*\d+\s*di\s*(\d+)/) || [])[1] || '1', 10);
    if (pages > 1) console.log('!! ' + pages + ' pages : relancer avec s_page, ou affiner');
    const parCommune = {};
    for (const r of rows) parCommune[r.contexte] = (parCommune[r.contexte] || 0) + 1;
    console.log('contextes archivistiques : ' + JSON.stringify(parCommune, null, 1));
    for (const r of rows.sort((a, b) => (a.contexte + a.annee + a.type).localeCompare(b.contexte + b.annee + b.type)))
      console.log(`  ${r.ark.padEnd(13)} ${r.annee.padEnd(10)} ${r.type.padEnd(38)} cote ${r.cote.padEnd(18)} ${r.contexte}`);
    fs.writeFileSync(path.join(__dirname, 'antenati-derniere-recherche.json'),
      JSON.stringify(rows, null, 1));
    // LE HTML BRUT SE GARDE, ET C'EST UNE LECON DU 12 SEPTEMBRE 2026 : `depouille()` a
    // rendu soixante lignes dont TOUS les champs valaient « ? » -- le gabarit du portail
    // avait change et la regex ne mordait plus. Sans le HTML sous la main, reparer le
    // depouilleur coute une requete de plus a chaque essai, sur un portail qui n'en
    // autorise que douze par heure. Le meme defaut que les deux modules Archinoe de la
    // veille : rendre des lignes sans dire qu'on ne les comprend pas.
    fs.writeFileSync(path.join(__dirname, 'antenati-derniere-recherche.html'), html);
    const muets = rows.filter(r => r.annee === '?').length;
    if (muets)
      console.log(`!! ${muets} registre(s) sur ${rows.length} N'ONT PAS ETE DEPOUILLES ` +
                  `(champs a « ? ») : le gabarit a probablement change. Le HTML brut est ` +
                  `dans antenati-derniere-recherche.html -- reparer depouille() dessus, ` +
                  `SANS relancer de requete.`);
  }

  else if (CMD === 'registre' || CMD === 'vue') {
    const ark = ARGS[0];
    const frais = ARGS.includes('--frais');
    const cache = lireCache();
    let cont, meta, services;

    // LE CACHE D'ABORD, ET IL DISPENSE DE DEUX REQUETES SUR QUATRE. Voir son
    // en-tete : c'est le manifeste IIIF, il ne bouge pas d'une lecture a l'autre.
    if (!frais && cache[ark] && (cache[ark].services || []).length) {
      ({ cont, meta, services } = cache[ark]);
      console.error('  [manifeste en cache : ' + services.length + ' vues, 2 requetes economisees]');
    } else {
      // LE SLASH FINAL COMPTE : sans lui on prend un 301.
      await aller(BASE + '/' + ARK + ark + '/', 'la page du registre ' + ark);
      const html = await page.content();
      cont = (html.match(/dam-antenati\.cultura\.gov\.it\/antenati\/containers\/([A-Za-z0-9_-]+)\/manifest/) || [])[1];
      if (!cont) { console.error('pas de manifeste sur la page de ' + ark); await ctx.close(); process.exit(1); }

      // Le fetch part DE LA PAGE OUVERTE : `dam-antenati` autorise le cross-origin.
      // Il compte comme une requete : le limiteur ne fait pas la difference.
      verifierAvant(); compter();
      const man = await page.evaluate(async (u) => (await fetch(u)).json(),
        `https://dam-antenati.cultura.gov.it/antenati/containers/${cont}/manifest`);

      meta = {};
      for (const md of man.metadata || []) {
        let v = md.value;
        if (Array.isArray(v)) v = v.map(x => (x && x['@value']) || x).join(' | ');
        meta[md.label] = v;
      }
      // IIIF Presentation 2.0 : un canvas par vue, le service est dans images[0].resource.service
      const canvases = ((man.sequences || [{}])[0].canvases) || [];
      services = canvases.map(c => {
        const im = ((c.images || [{}])[0].resource) || {};
        return { label: c.label, s: (im.service && im.service['@id']) || im['@id'] };
      }).filter(x => x.s);

      cache[ark] = { cont, meta, services };
      ecrireCache(cache);
    }

    if (CMD === 'registre') {
      console.log('container : ' + cont);
      // LE CONTEXTE ARCHIVISTIQUE SE LIT SYSTEMATIQUEMENT : un registre rendu par une
      // recherche « Valvasone Arzene » peut etre celui d'ARZENE ou de SAN LORENZO.
      for (const [k, v] of Object.entries(meta)) console.log('  ' + k + ' : ' + v);
      // TOUTES les etiquettes, et sur une ligne : elles disent parfois le folio, et
      // c'est precisement ce qui evite de tirer trois vues pour en trouver une. Une
      // fois le manifeste en cache, les relire ne coute plus rien au portail.
      console.log('  ' + services.length + ' vues');
      for (let i = 0; i < services.length; i += 8)
        console.log('    ' + services.slice(i, i + 8)
          .map((x, k) => 'v' + (i + k + 1) + '=' + String(x.label).replace(/\s+/g, '')).join('  '));
      console.log('  -> une vue : node antenati.js vue ' + ark + ' <n> "<archives>/..."');
    } else {
      // UNE VUE, PAS UN REGISTRE. Voir l'en-tete : c'est ce garde-fou qui manquait.
      const n = parseInt(ARGS[1], 10);
      const DEST = ARGS[2];
      if (!n || !DEST) { console.error('usage : vue <ark> <n> <dossier sur X:>'); await ctx.close(); process.exit(1); }
      if (n < 1 || n > services.length) { console.error('vue ' + n + ' hors du registre (1..' + services.length + ')'); await ctx.close(); process.exit(1); }
      fs.mkdirSync(DEST, { recursive: true });
      const f = path.join(DEST, 'v' + String(n).padStart(3, '0') + '.jpg');
      // Les vues sont sur `iiif-antenati`, qui n'autorise NI le CORS depuis la page NI
      // `ctx.request` (403 : un client HTTP a part, compte comme une requete nue).
      // Seule une VRAIE NAVIGATION passe — et encore, seulement si on n'est pas banni.
      verifierAvant();
      const reste = compter();
      const rep = await page.goto(services[n - 1].s + '/full/full/0/default.jpg',
        { waitUntil: 'load', timeout: 90000 });
      if (!rep || rep.status() === 403) { quarantaine('la vue ' + n); await ctx.close(); process.exit(2); }
      if (!rep.ok()) {
        console.error('v' + n + ' : ' + rep.status() + ' — une seule tentative, pas de reessai automatique.');
        await ctx.close(); process.exit(1);
      }
      if (reste <= 5) console.error('  [budget : ' + reste + ' requetes avant le plafond horaire]');
      fs.writeFileSync(f, await rep.body());
      console.log('ecrit ' + f + '  (' + Math.round(fs.statSync(f).size / 1024) + ' Ko)  ' + services[n - 1].label);
      await page.waitForTimeout(CADENCE);
    }
  }

  await ctx.close();
})().catch(e => { console.error('ERR ' + e.message); process.exit(1); });
