/**
 * Vastgoed AI Dealfinder — Content Script
 * Geïnjecteerd in Pararius, Jaap, Huislijn, Funda listing pagina's.
 * Extraheert data en toont de deal analyse overlay.
 */

(function () {
  "use strict";

  const SOURCE = detectSource();
  if (!SOURCE) return;

  // Wacht tot de pagina geladen is
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", main);
  } else {
    setTimeout(main, 1200); // Kleine delay voor JS-rendered content
  }

  function main() {
    const listing = extractListing(SOURCE);
    if (!listing || !listing.price_ask) {
      console.log("[Dealfinder] Geen listing data gevonden op deze pagina.");
      return;
    }

    showLoadingOverlay();

    chrome.runtime.sendMessage(
      { action: "analyzeListing", listing, source: SOURCE },
      (response) => {
        if (chrome.runtime.lastError) {
          console.error("[Dealfinder] Extension fout:", chrome.runtime.lastError.message);
          removeOverlay();
          return;
        }
        if (response && response.analysis) {
          showDealOverlay(response.analysis, listing);
        } else if (response && response.error) {
          showErrorOverlay(response.error);
        }
      }
    );
  }

  // ── Source detectie ────────────────────────────────────────────────────────

  function detectSource() {
    const host = window.location.hostname;
    if (host.includes("pararius")) return "pararius";
    if (host.includes("jaap")) return "jaap";
    if (host.includes("huislijn")) return "huislijn";
    if (host.includes("funda")) return "funda";
    return null;
  }

  // ── Data extractie per bron ────────────────────────────────────────────────

  function extractListing(source) {
    try {
      switch (source) {
        case "pararius": return extractPararius();
        case "jaap": return extractJaap();
        case "huislijn": return extractHuislijn();
        case "funda": return extractFunda();
        default: return null;
      }
    } catch (e) {
      console.error("[Dealfinder] Extractie fout:", e);
      return null;
    }
  }

  function extractPararius() {
    const title = text("h1.listing-detail-summary__title");
    const address = text(".listing-detail-summary__location");
    const priceRaw = text(".listing-detail-summary__price");
    const sizeRaw = text(".listing-detail-summary__sub-title");

    // Kenmerken
    const features = {};
    document.querySelectorAll(".listing-features__description dt").forEach((dt) => {
      const key = dt.textContent.trim().toLowerCase();
      const dd = dt.nextElementSibling;
      if (dd) features[key] = dd.textContent.trim();
    });

    return {
      title,
      address,
      city: extractCity(address),
      postcode: extractPostcode(address),
      price_ask: parsePrice(priceRaw),
      size_sqm: parseSqm(features["woonoppervlakte"] || features["oppervlakte"] || sizeRaw),
      rooms: parseInt(features["kamers"]) || null,
      bedrooms: parseInt(features["slaapkamers"]) || null,
      year_built: parseInt(features["bouwjaar"]) || null,
      description: text(".listing-detail-description__additional"),
      image_urls: extractImages(".photo-slider__photo-wrapper img"),
      url: window.location.href,
      source: "pararius",
    };
  }

  function extractJaap() {
    const title = text("h1.property-header-title");
    const address = text(".property-header-address");

    const features = {};
    document.querySelectorAll(".property-features-item").forEach((item) => {
      const label = text(item.querySelector(".property-features-label"));
      const value = text(item.querySelector(".property-features-value"));
      if (label) features[label.toLowerCase()] = value;
    });

    return {
      title,
      address,
      city: extractCity(address),
      postcode: extractPostcode(address),
      price_ask: parsePrice(text(".property-price")),
      size_sqm: parseSqm(features["woonoppervlak"] || features["oppervlakte"]),
      rooms: parseInt(features["kamers"]) || null,
      bedrooms: parseInt(features["slaapkamers"]) || null,
      year_built: parseInt(features["bouwjaar"]) || null,
      description: text(".property-description"),
      image_urls: extractImages(".property-images img"),
      url: window.location.href,
      source: "jaap",
    };
  }

  function extractHuislijn() {
    const address = text("h1");
    const features = {};
    document.querySelectorAll("dl dt").forEach((dt) => {
      const dd = dt.nextElementSibling;
      if (dd) features[dt.textContent.trim().toLowerCase()] = dd.textContent.trim();
    });

    return {
      title: address,
      address,
      city: extractCity(address),
      postcode: extractPostcode(address),
      price_ask: parsePrice(text(".price, [class*='price']")),
      size_sqm: parseSqm(features["woonoppervlakte"] || features["oppervlakte"]),
      rooms: parseInt(features["kamers"]) || null,
      bedrooms: parseInt(features["slaapkamers"]) || null,
      year_built: parseInt(features["bouwjaar"]) || null,
      description: text(".description, [class*='description']"),
      image_urls: extractImages("[class*='photo'] img, .gallery img"),
      url: window.location.href,
      source: "huislijn",
    };
  }

  function extractFunda() {
    const address = text("[data-test='street-name-house-number']");
    const city = text("[data-test='postal-code-city']");

    const features = {};
    document.querySelectorAll(".object-kenmerken-list li, .fd-list li").forEach((li) => {
      const label = text(li.querySelector("dt, .kenmerken-title"));
      const value = text(li.querySelector("dd, .kenmerken-value"));
      if (label) features[label.toLowerCase()] = value;
    });

    return {
      title: address + " " + city,
      address: address + ", " + city,
      city: extractCity(city),
      postcode: extractPostcode(city),
      price_ask: parsePrice(text(".object-header__price")),
      size_sqm: parseSqm(features["woonoppervlakte"] || features["oppervlakte"]),
      rooms: parseInt(features["aantal kamers"]) || null,
      bedrooms: parseInt(features["slaapkamers"]) || null,
      year_built: parseInt(features["bouwjaar"]) || null,
      description: text(".object-description-body, .fd-description-body"),
      image_urls: extractImages(".object-media-fotos img, [class*='photo'] img"),
      url: window.location.href,
      source: "funda",
    };
  }

  // ── Hulpfuncties ──────────────────────────────────────────────────────────

  function text(selector) {
    if (typeof selector === "string") {
      const el = document.querySelector(selector);
      return el ? el.textContent.trim() : null;
    }
    return selector ? selector.textContent.trim() : null;
  }

  function parsePrice(str) {
    if (!str) return null;
    const digits = str.replace(/[^\d]/g, "");
    return digits ? parseInt(digits) : null;
  }

  function parseSqm(str) {
    if (!str) return null;
    const match = str.match(/(\d+)/);
    return match ? parseInt(match[1]) : null;
  }

  function extractPostcode(str) {
    if (!str) return null;
    const match = str.match(/\b(\d{4}\s?[A-Z]{2})\b/);
    return match ? match[1].replace(" ", "") : null;
  }

  function extractCity(str) {
    if (!str) return null;
    const parts = str.split(",").map((s) => s.trim());
    return parts[parts.length - 1] || null;
  }

  function extractImages(selector) {
    const images = [];
    document.querySelectorAll(selector).forEach((img) => {
      const src = img.src || img.dataset.src || img.dataset.lazy;
      if (src && src.startsWith("http") && !images.includes(src)) {
        images.push(src);
      }
    });
    return images.slice(0, 8);
  }

  // ── Overlay beheer ─────────────────────────────────────────────────────────

  function removeOverlay() {
    const existing = document.getElementById("vastgoed-ai-overlay");
    if (existing) existing.remove();
  }

  function showLoadingOverlay() {
    removeOverlay();
    const overlay = document.createElement("div");
    overlay.id = "vastgoed-ai-overlay";
    overlay.className = "vdf-overlay vdf-loading";
    overlay.innerHTML = `
      <div class="vdf-card">
        <div class="vdf-header vdf-header-loading">
          <div class="vdf-logo">🏠 Dealfinder</div>
          <div class="vdf-spinner"></div>
        </div>
        <div class="vdf-body">
          <p class="vdf-loading-text">Analyse bezig...</p>
        </div>
      </div>
    `;
    document.body.appendChild(overlay);
  }

  function showErrorOverlay(error) {
    removeOverlay();
    const overlay = document.createElement("div");
    overlay.id = "vastgoed-ai-overlay";
    overlay.className = "vdf-overlay";
    overlay.innerHTML = `
      <div class="vdf-card">
        <div class="vdf-header vdf-header-error">
          <span>🏠 Dealfinder — Fout</span>
          <button class="vdf-close" onclick="document.getElementById('vastgoed-ai-overlay').remove()">✕</button>
        </div>
        <div class="vdf-body">
          <p class="vdf-error-text">Analyse mislukt: ${error}</p>
        </div>
      </div>
    `;
    document.body.appendChild(overlay);
  }

  function showDealOverlay(analysis, listing) {
    removeOverlay();

    const grade = analysis.deal_grade || "?";
    const score = analysis.deal_score || 0;
    const profit = analysis.potential_profit || 0;
    const roi = (analysis.roi_percentage || 0).toFixed(1);
    const reno_mid = analysis.reno_cost_mid || 0;
    const reno_min = analysis.reno_cost_min || 0;
    const reno_max = analysis.reno_cost_max || 0;
    const value = analysis.estimated_value_after_reno || 0;
    const woz = analysis.woz_value;
    const price = analysis.price_ask || listing.price_ask || 0;
    const klus = analysis.is_klus;
    const klus_pct = Math.round((analysis.klus_confidence || 0) * 100);
    const sqm_ask = analysis.price_per_sqm;
    const sqm_buurt = analysis.neighborhood_price_per_sqm;
    const invest = analysis.total_investment || 0;
    const breakdown = analysis.reno_breakdown || {};
    const keywords = (analysis.klus_keywords || []).join(", ") || "Geen gevonden";

    const gradeColor = {
      A: "#22C55E", B: "#3B82F6", C: "#F59E0B", D: "#EF4444", F: "#6B7280",
    }[grade] || "#6B7280";

    const profitColor = profit > 0 ? "#22C55E" : "#EF4444";
    const wozDiff = woz ? woz - price : null;
    const wozDiffText = wozDiff != null
      ? `<span class="${wozDiff >= 0 ? "vdf-green" : "vdf-red"}">${wozDiff >= 0 ? "+" : ""}€${fmt(Math.abs(wozDiff))}</span>`
      : "<span class='vdf-muted'>Onbekend</span>";

    const breakdownHtml = Object.entries(breakdown)
      .map(([item, cost]) => `
        <div class="vdf-row">
          <span class="vdf-label">${item.charAt(0).toUpperCase() + item.slice(1)}</span>
          <span class="vdf-value">€${fmt(cost)}</span>
        </div>
      `).join("") || "<div class='vdf-muted'>Geen details beschikbaar</div>";

    const overlay = document.createElement("div");
    overlay.id = "vastgoed-ai-overlay";
    overlay.className = "vdf-overlay";

    overlay.innerHTML = `
      <div class="vdf-card" id="vdf-card">

        <!-- Header -->
        <div class="vdf-header" style="background: ${gradeColor}">
          <div class="vdf-grade-circle">${grade}</div>
          <div class="vdf-header-center">
            <div class="vdf-score">${score}/100</div>
            <div class="vdf-header-sub">Deal Score</div>
          </div>
          <div class="vdf-header-right">
            <button class="vdf-close" id="vdf-close-btn">✕</button>
          </div>
        </div>

        <!-- Quick stats -->
        <div class="vdf-quick-stats">
          <div class="vdf-stat">
            <div class="vdf-stat-label">Vraagprijs</div>
            <div class="vdf-stat-value">€${fmt(price)}</div>
          </div>
          <div class="vdf-stat">
            <div class="vdf-stat-label">WOZ</div>
            <div class="vdf-stat-value vdf-green">${woz ? "€" + fmt(woz) : "?"}</div>
          </div>
          <div class="vdf-stat">
            <div class="vdf-stat-label">Winst</div>
            <div class="vdf-stat-value" style="color:${profitColor}">€${fmt(profit)}</div>
          </div>
          <div class="vdf-stat">
            <div class="vdf-stat-label">ROI</div>
            <div class="vdf-stat-value">${roi}%</div>
          </div>
        </div>

        <!-- Sections -->

        <!-- 1. Klus analyse -->
        <div class="vdf-section">
          <button class="vdf-section-btn" data-target="vdf-klus">
            ${klus ? "🔨" : "✅"} Kluswoning analyse
            <span class="vdf-badge ${klus ? "vdf-badge-red" : "vdf-badge-green"}">${klus_pct}%</span>
            <span class="vdf-chevron">▸</span>
          </button>
          <div class="vdf-section-content" id="vdf-klus" style="display:none">
            <div class="vdf-row">
              <span class="vdf-label">Kluswoning</span>
              <span class="vdf-value ${klus ? "vdf-red" : "vdf-green"}">${klus ? "Ja" : "Nee"} (${klus_pct}%)</span>
            </div>
            <div class="vdf-row">
              <span class="vdf-label">Trefwoorden</span>
              <span class="vdf-value vdf-small">${keywords}</span>
            </div>
          </div>
        </div>

        <!-- 2. Renovatiekosten -->
        <div class="vdf-section">
          <button class="vdf-section-btn" data-target="vdf-reno">
            🛠️ Renovatiekosten
            <span class="vdf-badge vdf-badge-blue">€${fmtK(reno_mid)}</span>
            <span class="vdf-chevron">▸</span>
          </button>
          <div class="vdf-section-content" id="vdf-reno" style="display:none">
            <div class="vdf-row vdf-highlight-row">
              <span class="vdf-label">Min – Gem – Max</span>
              <span class="vdf-value">€${fmtK(reno_min)} – €${fmtK(reno_mid)} – €${fmtK(reno_max)}</span>
            </div>
            <div class="vdf-divider"></div>
            ${breakdownHtml}
          </div>
        </div>

        <!-- 3. Marktwaarde -->
        <div class="vdf-section">
          <button class="vdf-section-btn" data-target="vdf-value">
            📊 Marktwaarde analyse
            <span class="vdf-chevron">▸</span>
          </button>
          <div class="vdf-section-content" id="vdf-value" style="display:none">
            <div class="vdf-row">
              <span class="vdf-label">WOZ waarde</span>
              <span class="vdf-value">${woz ? "€" + fmt(woz) : "Onbekend"}</span>
            </div>
            <div class="vdf-row">
              <span class="vdf-label">Verschil vraagprijs vs WOZ</span>
              <span class="vdf-value">${wozDiffText}</span>
            </div>
            <div class="vdf-row">
              <span class="vdf-label">Prijs/m² woning</span>
              <span class="vdf-value">${sqm_ask ? "€" + fmt(sqm_ask) : "?"}</span>
            </div>
            <div class="vdf-row">
              <span class="vdf-label">Prijs/m² buurt</span>
              <span class="vdf-value">${sqm_buurt ? "€" + fmt(sqm_buurt) : "?"}</span>
            </div>
            <div class="vdf-row">
              <span class="vdf-label">Waarde na renovatie</span>
              <span class="vdf-value vdf-green"><strong>€${fmt(value)}</strong></span>
            </div>
          </div>
        </div>

        <!-- 4. Investering -->
        <div class="vdf-section">
          <button class="vdf-section-btn" data-target="vdf-invest">
            💰 Investering & Winst
            <span class="vdf-chevron">▸</span>
          </button>
          <div class="vdf-section-content" id="vdf-invest" style="display:none">
            <div class="vdf-row">
              <span class="vdf-label">Vraagprijs</span>
              <span class="vdf-value">€${fmt(price)}</span>
            </div>
            <div class="vdf-row">
              <span class="vdf-label">+ Renovatiekosten</span>
              <span class="vdf-value">€${fmt(reno_mid)}</span>
            </div>
            <div class="vdf-row vdf-highlight-row">
              <span class="vdf-label">= Totale investering</span>
              <span class="vdf-value"><strong>€${fmt(invest)}</strong></span>
            </div>
            <div class="vdf-divider"></div>
            <div class="vdf-row">
              <span class="vdf-label">Verkoopwaarde na reno</span>
              <span class="vdf-value">€${fmt(value)}</span>
            </div>
            <div class="vdf-row vdf-profit-row">
              <span class="vdf-label">Potentiële winst</span>
              <span class="vdf-value" style="color:${profitColor}"><strong>€${fmt(profit)}</strong></span>
            </div>
            <div class="vdf-row">
              <span class="vdf-label">ROI</span>
              <span class="vdf-value"><strong>${roi}%</strong></span>
            </div>
          </div>
        </div>

        <!-- Actieknoppen -->
        <div class="vdf-actions">
          <button class="vdf-btn vdf-btn-save" id="vdf-save-btn" data-saved="false">
            ⭐ Opslaan
          </button>
          <button class="vdf-btn vdf-btn-copy" id="vdf-copy-btn">
            📋 Kopiëren
          </button>
        </div>

        <!-- Footer -->
        <div class="vdf-footer">
          <span>${analysis.cached ? "📦 Gecached" : "🔄 Vers"} · ${analysis.listing_id ? "ID: " + analysis.listing_id.slice(0, 8) : ""}</span>
        </div>

      </div>
    `;

    document.body.appendChild(overlay);
    attachEventListeners(overlay, analysis, listing);
  }

  function attachEventListeners(overlay, analysis, listing) {
    // Sluit knop
    document.getElementById("vdf-close-btn").addEventListener("click", () => {
      overlay.style.display = "none";
    });

    // Uitklap secties
    overlay.querySelectorAll(".vdf-section-btn").forEach((btn) => {
      btn.addEventListener("click", () => {
        const targetId = btn.dataset.target;
        const content = document.getElementById(targetId);
        const chevron = btn.querySelector(".vdf-chevron");
        if (content.style.display === "none") {
          content.style.display = "block";
          chevron.textContent = "▾";
        } else {
          content.style.display = "none";
          chevron.textContent = "▸";
        }
      });
    });

    // Opslaan knop
    document.getElementById("vdf-save-btn").addEventListener("click", (e) => {
      const btn = e.currentTarget;
      const saved = btn.dataset.saved === "true";
      if (!saved) {
        saveDeal(analysis, listing);
        btn.textContent = "★ Opgeslagen";
        btn.dataset.saved = "true";
        btn.style.background = "#F59E0B";
      } else {
        removeSavedDeal(listing.url);
        btn.textContent = "⭐ Opslaan";
        btn.dataset.saved = "false";
        btn.style.background = "";
      }
    });

    // Kopieer knop
    document.getElementById("vdf-copy-btn").addEventListener("click", () => {
      const text = buildCopyText(analysis, listing);
      navigator.clipboard.writeText(text).then(() => {
        const btn = document.getElementById("vdf-copy-btn");
        btn.textContent = "✅ Gekopieerd";
        setTimeout(() => (btn.textContent = "📋 Kopiëren"), 2000);
      });
    });
  }

  function saveDeal(analysis, listing) {
    chrome.storage.local.get("savedDeals", (data) => {
      const deals = data.savedDeals || [];
      deals.unshift({
        url: listing.url,
        address: listing.address,
        city: listing.city,
        price: listing.price_ask,
        score: analysis.deal_score,
        grade: analysis.deal_grade,
        profit: analysis.potential_profit,
        roi: analysis.roi_percentage,
        savedAt: new Date().toISOString(),
      });
      chrome.storage.local.set({ savedDeals: deals.slice(0, 50) }); // Max 50
    });
  }

  function removeSavedDeal(url) {
    chrome.storage.local.get("savedDeals", (data) => {
      const deals = (data.savedDeals || []).filter((d) => d.url !== url);
      chrome.storage.local.set({ savedDeals: deals });
    });
  }

  function buildCopyText(analysis, listing) {
    return [
      `🏠 Vastgoed Deal — Grade ${analysis.deal_grade} (${analysis.deal_score}/100)`,
      `📍 ${listing.address}, ${listing.city}`,
      `🔗 ${listing.url}`,
      ``,
      `💰 Vraagprijs: €${fmt(listing.price_ask)}`,
      `📋 WOZ waarde: €${fmt(analysis.woz_value || 0)}`,
      `🔨 Renovatiekosten: €${fmt(analysis.reno_cost_mid)}`,
      `🏠 Waarde na reno: €${fmt(analysis.estimated_value_after_reno)}`,
      ``,
      `💵 Potentiële winst: €${fmt(analysis.potential_profit)}`,
      `📈 ROI: ${(analysis.roi_percentage || 0).toFixed(1)}%`,
    ].join("\n");
  }

  function fmt(n) {
    if (n == null) return "0";
    return Math.round(n).toLocaleString("nl-NL");
  }

  function fmtK(n) {
    if (!n) return "0";
    return n >= 1000 ? Math.round(n / 1000) + "k" : fmt(n);
  }

})();
