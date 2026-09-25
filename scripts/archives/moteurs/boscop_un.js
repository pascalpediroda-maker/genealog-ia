// Telecharge un registre AD42 par l'API IIIF, depuis le contexte de la page
// (le WAF ne laisse passer qu'un vrai Chrome). Cadence : 1 vue/seconde.
const { chromium } = require('playwright');
const fs = require('fs'), path = require('path');
const ARK = process.argv[2], DEST = process.argv[3];
(async () => {
  const ctx = await chromium.launchPersistentContext('.chrome-profil', {
    channel:'chrome', headless:false, viewport:{width:1200,height:800} });
  const page = ctx.pages()[0] || await ctx.newPage();
  await page.goto('https://archives.loire.fr/ark:/51302/' + ARK, { waitUntil:'domcontentloaded', timeout:90000 });
  await page.waitForTimeout(8000);
  const services = await page.evaluate(async (ark) => {
    const r = await fetch('https://archives.loire.fr/ark:/51302/' + ark + '/manifest');
    const j = await r.json();
    const cv = (j.sequences && j.sequences[0] && j.sequences[0].canvases) || [];
    return cv.map(c => { const im = c.images && c.images[0] && c.images[0].resource;
      return (im && im.service && im.service['@id']) || (im && im['@id']) || null; }).filter(Boolean);
  }, ARK);
  console.log(services.length + ' vues');
  if (!services.length) { console.log('manifeste sans canvas'); await ctx.close(); return; }
  fs.mkdirSync(DEST, { recursive: true });
  for (let i = 0; i < services.length; i++) {
    const url = services[i] + '/full/full/0/native.jpg';
    const b64 = await page.evaluate(async (u) => {
      const r = await fetch(u); if (!r.ok) return 'ERR ' + r.status;
      const b = await r.arrayBuffer(); let s = ''; const a = new Uint8Array(b);
      const CH = 8192; for (let k=0;k<a.length;k+=CH) s += String.fromCharCode.apply(null, a.subarray(k,k+CH));
      return btoa(s);
    }, url);
    if (typeof b64 === 'string' && b64.startsWith('ERR')) { console.log('v'+(i+1), b64); continue; }
    const f = path.join(DEST, 'v' + String(i+1).padStart(3,'0') + '.jpg');
    fs.writeFileSync(f, Buffer.from(b64, 'base64'));
    console.log('v'+(i+1)+'/'+services.length, fs.statSync(f).size);
    await page.waitForTimeout(1000);
  }
  await ctx.close();
})();
