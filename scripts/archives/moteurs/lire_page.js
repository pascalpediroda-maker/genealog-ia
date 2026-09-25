// LIRE UNE PAGE DERRIERE UN WAF — le trou d'outillage du 7 septembre 2026.
//
//   NODE_PATH="<maison>" \
//     node scripts/archives/moteurs/lire_page.js <url> [url2 ...] [--html] [--out fichier]
//
// POURQUOI. Le dossier savait TELECHARGER des registres derriere un WAF (boscop.js) et
// IDENTIFIER un moteur (identifier.js). Il ne savait pas simplement LIRE UNE PAGE. Le
// 7 septembre 2026, la fiche « Rechercher un dossier d'etranger » de l'AD31 — qui porte
// les delais de communicabilite, la cle de classement des dossiers et l'avertissement sur
// l'echantillonnage — a du etre copiee-collee a la main par le généalogiste parce qu'aucun outil ne
// pouvait la lire. Anubis rend 4 202 octets de defi a toute requete automatique, la meme
// page quelle que soit l'URL demandee.
//
// CE QUI REND CE MODULE UTILE PLUTOT QUE JETABLE :
//  * PROFIL PERSISTANT PAR DOMAINE. Anubis pose un cookie apres la preuve-de-travail ; en
//    reutilisant `.chrome-<domaine>`, seule la PREMIERE page paie les ~18 s. Les suivantes
//    passent d'emblee, et on peut donc lire dix pages d'un inventaire d'affilee.
//  * ATTENTE MESUREE, PAS DEVINEE. On boucle tant que la signature du defi est la, au lieu
//    de dormir un temps arbitraire.
//  * IL REND LA MAIN. `identifier.js` a d'abord garde sa fenetre ouverte 600 s : l'appelant
//    coupait au bout de son delai et TOUTE LA SORTIE ETAIT PERDUE. Ici on ferme, sauf
//    GARDER=1.
const { chromium } = require('playwright');
const fs = require('fs');

const args = process.argv.slice(2);
const HTML = args.includes('--html');
const iOut = args.indexOf('--out');
const OUT = iOut >= 0 ? args[iOut + 1] : null;
const URLS = args.filter((a, i) =>
  /^https?:\/\//.test(a) && !(iOut >= 0 && i === iOut + 1));

if (!URLS.length) {
  console.error('usage : node lire_page.js <url> [url2 ...] [--html] [--out fichier]');
  process.exit(1);
}

// Les signatures de defi rencontrees jusqu'ici. Voir references/portails.md.
//
// F5 / SHAPE SECURITY A ETE AJOUTE LE 18 SEPTEMBRE 2026, ET IL AVAIT GLISSE ENTRE LES
// MAILLES DEUX FOIS. Sa page de defi fait 6 826 octets -- JUSTE AU-DESSUS du seuil de
// 6 000 --, ne porte aucune des phrases connues, et se reconnait a trois choses : des
// scripts servis depuis /TSPD/, la ligne « Your support ID is: <20 chiffres> », et un
// <canvas> de 800x600 pour l'empreinte. Sans cette entree, lire_page.js a rendu la page
// de defi de l'AD62 en annoncant « defi franchi », et le moteur a ete declare
// « aucune signature connue » alors qu'on n'avait jamais vu le portail.
// L'« ANTI-DDOS FLOOD PROTECTION » A ETE AJOUTE LE 19 SEPTEMBRE 2026, SUR L'AD09, et il a
// glisse par le haut comme F5 par le bas : sa page fait 41 776 octets -- bien au-dessus du
// seuil -- et ne porte aucune des phrases connues. C'est un compte a rebours de TROIS
// SECONDES, encode en base64 dans un `eval(atob(...))`, qui pose un cookie et recharge. Un
// vrai Chrome le passe tout seul ; il suffit de ne pas rendre la main avant. Sans cette
// entree, lire_page.js a annonce « defi franchi » sur la page de pare-feu, et l'AD09 a
// failli etre declare « moteur inconnu » sans qu'on ait jamais vu le portail -- exactement
// la faute que l'entree F5 documentait la veille.
const DEFI = [/within\.website/i, /making sure you'?re not a bot/i, /just a moment/i,
              /attack detected/i, /checking your browser/i, /altcha/i,
              /\/TSPD\//i, /your support id is/i,
              /anti-?ddos/i, /flood protection/i];
const estDefi = h => DEFI.some(r => r.test(h)) || h.length < 6000;

const domaine = new URL(URLS[0]).hostname.replace(/[^a-z0-9.]/gi, '');

(async () => {
  const ctx = await chromium.launchPersistentContext('.chrome-' + domaine, {
    channel: 'chrome', headless: false, viewport: { width: 1280, height: 900 } });
  const page = ctx.pages()[0] || await ctx.newPage();
  const morceaux = [];

  for (const url of URLS) {
    process.stderr.write('-> ' + url + '\n');
    await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 90000 });

    let h = await page.content(), attendu = 0;
    while (estDefi(h) && attendu < 60000) {        // on attend TANT QUE le defi est la
      await page.waitForTimeout(3000);
      attendu += 3000;
      h = await page.content();
    }
    if (estDefi(h)) {
      process.stderr.write('   ⚠️ defi non franchi apres 60 s — page laissee telle quelle\n');
    } else if (attendu) {
      process.stderr.write('   defi franchi en ' + (attendu / 1000) + ' s\n');
    }

    let sortie;
    if (HTML) {
      sortie = h;
    } else {
      // le texte visible, pas le HTML : c'est ce qu'on veut lire neuf fois sur dix
      sortie = await page.evaluate(() => {
        document.querySelectorAll('script,style,noscript').forEach(e => e.remove());
        return (document.body ? document.body.innerText : '')
          .replace(/\n{3,}/g, '\n\n').trim();
      });
    }
    morceaux.push('===== ' + url + '\n' + sortie);
  }

  const tout = morceaux.join('\n\n');
  if (OUT) { fs.writeFileSync(OUT, tout, 'utf8'); process.stderr.write('ecrit : ' + OUT + '\n'); }
  else { console.log(tout); }

  if (process.env.GARDER) await page.waitForTimeout(600000);
  await ctx.close();
})();
