const API_URL = "http://localhost:8000";

function extractPrice() {
  const priceText = document.body.innerText.match(/€\s*([\d.,]+)/);
  return priceText ? parseFloat(priceText[1].replace(".","").replace(",",".")) : null;
}

function createOverlay(data) {
  // Create detailed info panel
  const panel = document.createElement('div');
  panel.id = 'arbitrage-panel';

  const profitPct = Math.round(data.profit_pct * 100);
  const profitEur = Math.round(data.profit_eur);
  const dealColor = data.profit_pct > 0.40 ? '#28a745' : data.profit_pct > 0.25 ? '#20c997' : '#ffc107';
  const dealLabel = data.deal_score;

  panel.style.cssText = `
    position: fixed;
    bottom: 20px;
    right: 20px;
    background: white;
    border-left: 5px solid ${dealColor};
    border-radius: 6px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    padding: 16px;
    z-index: 999999;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    width: 280px;
    max-width: 90vw;
  `;

  panel.innerHTML = `
    <div style="margin-bottom: 12px;">
      <div style="font-size: 12px; color: #666; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 4px;">
        💰 Winst inschatting
      </div>
      <div style="font-size: 28px; font-weight: bold; color: ${dealColor};">
        €${profitEur}
      </div>
      <div style="font-size: 13px; color: #666; margin-top: 2px;">
        ${profitPct}% marge
      </div>
    </div>

    <div style="border-top: 1px solid #eee; padding-top: 12px; margin-bottom: 12px;">
      <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px; font-size: 12px;">
        <div>
          <div style="color: #999; margin-bottom: 2px;">Inkoopprijs</div>
          <div style="font-weight: 600; color: #333;">€${Math.round(data.current_price)}</div>
        </div>
        <div>
          <div style="color: #999; margin-bottom: 2px;">Geschat waarde</div>
          <div style="font-weight: 600; color: #333;">€${Math.round(data.estimated_value)}</div>
        </div>
        <div>
          <div style="color: #999; margin-bottom: 2px;">Zekerheid</div>
          <div style="font-weight: 600; color: #333;">${Math.round(data.confidence * 100)}%</div>
        </div>
        <div>
          <div style="color: #999; margin-bottom: 2px;">Status</div>
          <div style="font-weight: 600; color: ${dealColor};">${dealLabel}</div>
        </div>
      </div>
    </div>

    <div style="font-size: 11px; color: #999; line-height: 1.4;">
      📊 Gebaseerd op vergelijkbare verkochte items (categorie: ${data.category || 'elektronica'})
    </div>

    <div style="margin-top: 12px; text-align: center;">
      <button id="close-panel" style="
        background: none;
        border: none;
        color: #999;
        cursor: pointer;
        font-size: 12px;
        text-decoration: underline;
      ">Sluiten</button>
    </div>
  `;

  document.body.appendChild(panel);

  // Close button
  document.getElementById('close-panel').addEventListener('click', () => {
    panel.remove();
  });

  console.log('[Arbitrage] Panel created:', data);
}

async function analyzeListing() {
  const price = extractPrice();
  console.log('[Arbitrage] Price extracted:', price);

  if (!price || price < 5) return;

  const listing = {
    title: document.title || "Unknown",
    price: price,
    platform: "marktplaats",
    condition: "unknown",
    description: "",
    category: "electronics"
  };

  console.log('[Arbitrage] Analyzing:', listing);

  try {
    const res = await fetch(`${API_URL}/api/v1/estimate`, {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify(listing)
    });

    console.log('[Arbitrage] API response status:', res.status);

    if (res.ok) {
      const data = await res.json();
      console.log('[Arbitrage] API data:', data);

      if (data.profit_pct > 0.25) {
        createOverlay(data);
      } else {
        console.log('[Arbitrage] Profit too low:', data.profit_pct);
      }
    } else {
      const errText = await res.text();
      console.log('[Arbitrage] API error:', res.status, errText);
    }
  } catch(e) {
    console.log('[Arbitrage] Fetch error:', e);
  }
}

window.addEventListener("load", analyzeListing);
console.log('[Arbitrage] Content script loaded');