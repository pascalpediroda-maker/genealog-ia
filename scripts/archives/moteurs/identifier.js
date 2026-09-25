// IDENTIFIER LE MOTEUR D'UN PORTAIL QU'ON NE CONNAIT PAS — l'etape 1 de la methode,
// et rien ne la faisait.
//
//   NODE_PATH="<maison>" \
//     node scripts/archives/moteurs/identifier.js <url> [secondes-d-attente]
//
// POURQUOI IL EXISTE. La skill dit « identifier le moteur : il se signe dans le HTML de
// la page d'accueil ». Vrai — SAUF derriere un WAF. Le 7 septembre 2026, l'AD31 a rendu
// 4 202 octets a urllib : la page de defi d'ANUBIS, identique pour toutes les URL du
// domaine. Aucune signature de moteur n'y est lisible, et on ne peut donc rien conclure
// AVANT d'avoir franchi le mur. Il faut un vrai Chrome fenetre, et lui laisser le temps.
//
// C'est la meme recette que boscop.js applique avant sa premiere requete, sortie ici pour
// servir a tout portail, quel que soit son moteur — y compris ceux qu'on n'a pas encore.
const { chromium } = require('playwright');

const URL = process.argv[2];
const ATTENTE = (parseInt(process.argv[3], 10) || 14) * 1000;
if (!URL) {
  console.error('usage : node identifier.js <url> [secondes-d-attente]');
  process.exit(1);
}

// Les signatures, par moteur. Voir references/portails.md : un portail se signe du nom de
// son EDITEUR ou de son PRODUIT, indifferemment — c'est la meme maison.
const SIGNES = {
  'Arkotheque (1 egal 2)': [/arko_default_/i, /arko_fiche_/i, /arko-analytics/i, /arkotheque/i],
  // ⛔ LE `\b` DE FIN A FAIT MANQUER UN MOTEUR ENTIER, ET C'ETAIT INVISIBLE. Le portail de
  // la Savoie porte `mnesys` DOUZE FOIS dans son HTML — `interfaces/mnesys_cg73portailv1/
  // skins/…` — et `identifier.js` repondait « aucune signature connue ». La cause : LE
  // TIRET BAS EST UN CARACTERE DE MOT, donc `\b` ne coupe pas entre `mnesys` et `_cg73`.
  // Un nom d'habillage ou de theme colle presque toujours un suffixe au nom du produit :
  // on ancre au DEBUT du mot, jamais a la fin. C'est le cas GAIA du 18 septembre a
  // l'envers — la signature etait la, la regexp ne la voyait pas.
  'Boscop / Ligeo':        [/\bboscop/i, /\bligeo/i, /RECH_[A-Za-z]/, /arcfacette\.php/i],
  'Naoned / Mnesys':       [/\bnaoned/i, /\bmnesys/i, /\/visualizer\//i],
  'Anaphore (Thot/Arkheia)': [/\banaphore\b/i],
  '4D (4th Dimension)':    [/\/4DCGI\//i, /\/4Daction\//i],
  'ASP.NET WebForms':      [/__VIEWSTATE/, /__EVENTVALIDATION/],
  // ⚠️ `/vision/i` ETAIT UN FAUX AMI, ET IL A SIGNE L'AD83 COMME DU PRISMIA le
  // 19 septembre 2026. Le mot attrape « visionneuse », qui figure sur a peu pres tous les
  // portails d'archives francais — l'AD83 est un Arkotheque. Le produit s'ecrit « ViSiON »
  // avec ses capitales internes : on le cherche donc SANS le drapeau `i`, ce qui ne coute
  // rien et ne confond plus rien. Une signature trop large est pire qu'une signature
  // absente : l'absence fait chercher, le faux positif fait conclure.
  'Prismia ViSiON':        [/prismia/i, /\bViSiON\b/],
  // GAIA 9 MANQUAIT, ET CA S'EST PAYE LE 18 SEPTEMBRE 2026. Le moteur avait ete reconnu le
  // 12 septembre sur l'AD66, sa fiche etait au carnet et `gaia.py` allait etre ecrit le jour
  // meme -- mais identifier.js, lui, rendait « aucune signature connue » sur l'AD61, et une
  // session a refait tout le chemin a zero. Un moteur reconnu qui n'entre pas dans cette
  // table est un moteur qu'on redecouvrira.
  'GAIA 9':                [/GAIA 9\s*:/i, /\/mdr\/index\.php\//i, /requeteConstructor/i],
  // ET LE PORTALE ANTENATI MANQUAIT AUSSI, ouvert le 27 aout 2026 et jamais inscrit ici.
  // Trouve par `portails_coherence.py` a sa premiere execution, le 18 septembre : c'est
  // precisement le controle qu'on venait d'ecrire pour ne plus repayer le cas GAIA.
  'WordPress Antenati':    [/ark:\/12657\//, /an_ua\d+/, /dam-antenati\.cultura\.gov\.it/i],
  'ARCHINOE':              [/archinoe/i],
  // ANOM, ouvert le 20 septembre 2026. Developpement propre des Archives nationales
  // d'outre-mer : la base s'appelle `caomec2`, la visionneuse `osdanom`, et les images
  // portent toutes le prefixe `DAFANCAOM`. Trois marqueurs nets, aucun risque de faux ami.
  'ANOM (caomec2)':        [/caomec2/i, /osdanom/i, /DAFANCAOM/],
  // ⚠️ DJANGO N'EST PAS UN EDITEUR D'ARCHIVES, C'EST UN CADRE WEB, et cette entree dit donc
  // AUTRE CHOSE que les precedentes : « site fait maison, pas un progiciel connu ». Reconnaitre
  // Boscop predit les routes ; reconnaitre Django ne predit RIEN — Matricula cache sa recherche
  // derriere `/en/suchen/`, le suivant la mettra ailleurs. L'entree sert a ne pas rendre
  // « aucune signature connue », ce qui fait repartir de zero, et a dire tout de suite qu'il
  // faudra lire le HTML a la main. Elle est volontairement placee EN DERNIER : tout moteur
  // reel doit avoir sa chance avant, puisqu'un progiciel peut lui-meme tourner sur Django.
  'Django (site maison)':  [/csrfmiddlewaretoken/i, /\/i18n\/setlang\//i],
  'IIPImage (visionneuse)':[/iipsrv\.fcgi/i],
  'IIIF':                  [/\/manifest(\.json)?/i, /iiif/i],
};
const MUR = [/within\.website/i, /anubis/i, /not a bot/i, /attack detected/i, /cloudflare/i,
             // F5 / Shape Security : scripts en /TSPD/, « Your support ID is », canvas
             // d'empreinte. Page de defi de 6 826 octets, sans phrase reconnaissable.
             /\/TSPD\//i, /your support id is/i];

(async () => {
  // `ignoreHTTPSErrors` N'EST PAS UNE COMMODITE : UN PORTAIL PUBLIC PEUT SERVIR UN
  // CERTIFICAT PERIME PENDANT DES MOIS. Le 8 septembre 2026, celui de MEMOIRE DES HOMMES
  // — le site du ministere des armees qui publie les JMO de 14-18 — avait expire le
  // 20 novembre 2025, soit dix mois plus tot. curl rend SEC_E_CERT_EXPIRED et Chrome
  // s'arrete sur son interstitiel : sans cette option, on conclut « le site est en
  // panne » alors qu'il repond parfaitement. L'option ne change rien sur un certificat
  // valide ; elle evite de perdre une seance sur un portail vivant.
  const ctx = await chromium.launchPersistentContext('.chrome-ident', {
    channel: 'chrome', headless: false, ignoreHTTPSErrors: true,
    viewport: { width: 1280, height: 900 } });
  const page = ctx.pages()[0] || await ctx.newPage();

  console.log('-> ' + URL);
  await page.goto(URL, { waitUntil: 'domcontentloaded', timeout: 90000 });

  let html = await page.content();
  const barre = MUR.filter(r => r.test(html));
  if (barre.length) {
    console.log('   mur detecte (' + barre.map(String).join(', ') + ') — attente de '
      + (ATTENTE / 1000) + ' s');
    await page.waitForTimeout(ATTENTE);
    try { await page.waitForLoadState('networkidle', { timeout: 20000 }); } catch (e) {}
    html = await page.content();
  }

  const titre = await page.title();
  const gen = html.match(/<meta[^>]+name=["']?generator["']?[^>]*content=["']([^"']+)/i);
  console.log('\n=== ' + page.url());
  console.log('    titre      : ' + titre);
  console.log('    Generator  : ' + (gen ? gen[1] : '—'));
  console.log('    octets     : ' + html.length
    + (html.length < 8000 ? '   ⚠️ tres court : le mur n\'est peut-etre pas franchi' : ''));

  const trouves = Object.entries(SIGNES)
    .map(([nom, rs]) => [nom, rs.filter(r => r.test(html)).map(String)])
    .filter(([, m]) => m.length);
  console.log('\n    MOTEUR :');
  if (!trouves.length) console.log('      aucune signature connue — regarder le HTML a la main');
  for (const [nom, m] of trouves) console.log('      ' + nom + '  ' + m.join(' '));

  // Les portes d'entree. LE FILTRE NE CONNAISSAIT QUE L'ETAT CIVIL, et c'est trop etroit :
  // un service d'archives sert cinq ou six fonds sur le meme moteur, et l'etat civil n'est
  // que le premier qu'on ouvre. Le 8 septembre 2026, il a fallu les RECENSEMENTS de la
  // Vienne et les MATRICULES de la Dordogne — deux mots qu'aucune de ces expressions
  // n'attrapait, alors que les deux fonds etaient en ligne et a un clic.
  const liens = await page.$$eval('a[href]', as => as.map(a => [a.textContent.trim(), a.href]));
  const utiles = liens.filter(([t, h]) =>
    /recherche|archives en ligne|etat.civil|état.civil|registre|numeris|inventaire|fonds|recensement|d[ée]nombrement|matricul|militaire|cadastr|hypoth|notari|presse|journaux/i
      .test(t + ' ' + h));
  console.log('\n    PORTES D\'ENTREE (' + utiles.length + ') :');
  for (const [t, h] of utiles.slice(0, 25)) console.log('      ' + (t || '(sans texte)').slice(0, 52).padEnd(54) + h);

  // GARDER=1 laisse la fenetre ouverte pour regarder soi-meme ; sinon on rend la main,
  // sans quoi la sortie se perd quand l'appelant coupe au bout de son delai.
  if (process.env.GARDER) {
    console.log('\n(GARDER=1 : la fenetre reste ouverte — Ctrl+C pour fermer)');
    await page.waitForTimeout(600000);
  }
  await ctx.close();
})();
