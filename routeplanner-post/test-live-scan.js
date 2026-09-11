// Live end-to-end test van de scan-pipeline.
// Genereert synthetische pakket-labels (SVG -> JPEG via sharp) en stuurt ze
// door de ECHTE Cloudflare Worker proxy, net als de browser-app dat doet.
// Doel: bewijzen dat worker -> Claude -> response-parsing een correct adres oplevert.

const sharp = require('sharp');

const PROXY_URL = 'https://claude-proxy.brent-jansen2009.workers.dev';

const PROMPT = `Dit is een foto van een pakket of tijdschrift dat bezorgd moet worden.
Lees het BEZORGADRES (het adres van de ontvanger, NIET het retouradres/afzender).

Geef het adres in dit formaat: Straatnaam Huisnummer, Postcode Stad
Voorbeeld: Lavendel 63, 2925 XE Krimpen aan den IJssel

Als er meerdere bezorgadressen op de foto staan, geef ze allemaal op aparte regels.
Als het onleesbaar is, schrijf dan alleen: ONLEESBAAR
Geef GEEN afzendadres, GEEN namen, GEEN extra uitleg. Alleen het adres.`;

// Een paar realistische test-labels (afzender + ontvanger, zoals een echt pakket)
const CASES = [
    {
        naam: 'Standaard label',
        verwacht: { straat: 'Lavendel', nr: '63', pc: '2925', stad: 'Krimpen' },
        afzender: 'Afzender: Webshop BV\nPostbus 1200\n3000 AA Rotterdam',
        ontvanger: 'Bezorgadres:\nJan de Vries\nLavendel 63\n2925 XE Krimpen aan den IJssel',
    },
    {
        naam: 'Postcode aan elkaar',
        verwacht: { straat: 'Zonnebloem', nr: '64', pc: '2925', stad: 'Krimpen' },
        afzender: 'Retour: Magazijn Noord\n1011 AB Amsterdam',
        ontvanger: 'Aan:\nFam. Bakker\nZonnebloem 64\n2925AB Krimpen aan den IJssel',
    },
    {
        naam: 'Lange straatnaam',
        verwacht: { straat: 'Burgemeester', nr: '12', pc: '2924', stad: 'Krimpen' },
        afzender: 'Sender: Logistics Center\n5600 XX Eindhoven',
        ontvanger: 'Deliver to:\nP. Janssen\nBurgemeester Aalberslaan 12 A\n2924 CK Krimpen aan den IJssel',
    },
];

function maakLabelSvg(afzender, ontvanger) {
    const esc = s => s.replace(/&/g, '&amp;').replace(/</g, '&lt;');
    const afzLines = afzender.split('\n');
    const ontLines = ontvanger.split('\n');
    const afzTspans = afzLines.map((l, i) =>
        `<tspan x="40" dy="${i === 0 ? 0 : 26}">${esc(l)}</tspan>`).join('');
    const ontTspans = ontLines.map((l, i) =>
        `<tspan x="40" dy="${i === 0 ? 0 : 34}">${esc(l)}</tspan>`).join('');
    return `<svg width="800" height="600" xmlns="http://www.w3.org/2000/svg">
        <rect width="800" height="600" fill="#ffffff"/>
        <rect x="20" y="20" width="760" height="560" fill="none" stroke="#000" stroke-width="3"/>
        <text x="40" y="70" font-family="Arial" font-size="20" fill="#444">${afzTspans}</text>
        <line x1="20" y1="200" x2="780" y2="200" stroke="#000" stroke-width="2"/>
        <text x="40" y="260" font-family="Arial" font-size="30" font-weight="bold" fill="#000">${ontTspans}</text>
        <rect x="560" y="420" width="200" height="140" fill="#000"/>
        <text x="600" y="500" font-family="monospace" font-size="40" fill="#fff">|||I|II|</text>
    </svg>`;
}

async function scanEenFoto(base64, mime) {
    const resp = await fetch(PROXY_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            contents: [{ parts: [
                { text: PROMPT },
                { inline_data: { mime_type: mime, data: base64 } }
            ]}],
            generationConfig: { temperature: 0.1, maxOutputTokens: 200 }
        })
    });
    if (!resp.ok) {
        const err = await resp.json().catch(() => ({}));
        throw new Error(err?.error?.message || `HTTP ${resp.status}`);
    }
    const data = await resp.json();
    return data?.candidates?.[0]?.content?.parts?.[0]?.text || '';
}

(async () => {
    console.log('\n=== LIVE SCAN TEST via ' + PROXY_URL + ' ===\n');
    let geslaagd = 0;
    for (const c of CASES) {
        const svg = maakLabelSvg(c.afzender, c.ontvanger);
        const jpeg = await sharp(Buffer.from(svg)).jpeg({ quality: 85 }).toBuffer();
        const b64 = jpeg.toString('base64');
        process.stdout.write(`[${c.naam.padEnd(22)}] `);
        try {
            const tekst = (await scanEenFoto(b64, 'image/jpeg')).trim();
            const v = c.verwacht;
            const ok = tekst.includes(v.straat) && tekst.includes(v.nr)
                    && tekst.includes(v.pc) && tekst.includes(v.stad)
                    && !tekst.includes('Rotterdam') && !tekst.includes('Amsterdam')
                    && !tekst.includes('Eindhoven'); // mag geen afzender pakken
            console.log((ok ? 'OK ' : 'FOUT') + '  -> ' + tekst.replace(/\n/g, ' | '));
            if (ok) geslaagd++;
        } catch (e) {
            console.log('FOUT  ' + e.message);
        }
        await new Promise(r => setTimeout(r, 1500));
    }
    console.log(`\n=== ${geslaagd}/${CASES.length} geslaagd ===\n`);
    process.exit(geslaagd === CASES.length ? 0 : 1);
})();
