// Unit-test voor de adres-parsing in scan.js (zelfde transformatie-keten).
// Verifieert: lijstmarkeringen, labelprefixen, postcode-spatie, filtering, dedup.

function parseAdressen(tekst) {
    const gevonden = [];
    tekst.split('\n')
        .map(r => r.trim())
        .map(r => r.replace(/^\s*(?:[-*•·]|\d{1,2}[.)])\s+/, ''))
        .map(r => r.replace(/^(?:bezorgadres|adres|aan|deliver to|bezorg)\s*[:.]?\s+/i, ''))
        .map(r => r.replace(/\b(\d{4})([A-Za-z]{2})\b/g, '$1 $2'))
        .map(r => r.trim())
        .filter(r => r.length > 5 && /\d/.test(r) && !/^onleesbaar$/i.test(r))
        .forEach(r => { if (!gevonden.includes(r)) gevonden.push(r); });
    return gevonden;
}

const tests = [
    ['Standaard', 'Lavendel 63, 2925 XE Krimpen aan den IJssel',
        ['Lavendel 63, 2925 XE Krimpen aan den IJssel']],
    ['Postcode aan elkaar', 'Zonnebloem 64, 2925AB Krimpen aan den IJssel',
        ['Zonnebloem 64, 2925 AB Krimpen aan den IJssel']],
    ['Lijstnummer', '1. Lavendel 63, 2925 XE Krimpen\n2) Zonnebloem 64, 2924 AB Krimpen',
        ['Lavendel 63, 2925 XE Krimpen', 'Zonnebloem 64, 2924 AB Krimpen']],
    ['Bullet', '- Lavendel 63, 2925 XE Krimpen\n• Berk 12, 2925 AA Krimpen',
        ['Lavendel 63, 2925 XE Krimpen', 'Berk 12, 2925 AA Krimpen']],
    ['Labelprefix', 'Bezorgadres: Lavendel 63, 2925 XE Krimpen',
        ['Lavendel 63, 2925 XE Krimpen']],
    ['ONLEESBAAR weg', 'ONLEESBAAR',
        []],
    ['Lege regels + dubbel', 'Lavendel 63, 2925 XE Krimpen\n\nLavendel 63, 2925 XE Krimpen',
        ['Lavendel 63, 2925 XE Krimpen']],
    ['Regel zonder cijfer weg', 'Krimpen aan den IJssel\nLavendel 63, 2925 XE Krimpen',
        ['Lavendel 63, 2925 XE Krimpen']],
    ['Korte ruis weg', 'OK\nBerk 12, 2925 AA Krimpen',
        ['Berk 12, 2925 AA Krimpen']],
];

let ok = 0;
for (const [naam, input, verwacht] of tests) {
    const out = parseAdressen(input);
    const pass = JSON.stringify(out) === JSON.stringify(verwacht);
    console.log((pass ? 'OK  ' : 'FOUT') + '  ' + naam + (pass ? '' : `\n      kreeg:    ${JSON.stringify(out)}\n      verwacht: ${JSON.stringify(verwacht)}`));
    if (pass) ok++;
}
console.log(`\n=== ${ok}/${tests.length} geslaagd ===`);
process.exit(ok === tests.length ? 0 : 1);
