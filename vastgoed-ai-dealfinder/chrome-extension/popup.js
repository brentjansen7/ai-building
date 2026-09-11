// Vastgoed AI Dealfinder — Popup Logic

document.addEventListener("DOMContentLoaded", () => {
  loadSettings();
  loadSavedDeals();
  setupTabs();
  setupEventListeners();
});

// ── Tabs ───────────────────────────────────────────────────────────────────

function setupTabs() {
  document.querySelectorAll(".tab").forEach((tab) => {
    tab.addEventListener("click", () => {
      const targetId = tab.dataset.tab;
      document.querySelectorAll(".tab").forEach((t) => t.classList.remove("active"));
      document.querySelectorAll(".tab-content").forEach((c) => c.classList.remove("active"));
      tab.classList.add("active");
      document.getElementById(`tab-${targetId}`).classList.add("active");
    });
  });
}

// ── Settings ───────────────────────────────────────────────────────────────

function loadSettings() {
  chrome.runtime.sendMessage({ action: "getSettings" }, (settings) => {
    if (!settings) return;
    document.getElementById("apiBase").value = settings.apiBase || "";
    document.getElementById("apiKey").value = settings.apiKey || "";
    document.getElementById("minScore").value = settings.minScore || 70;
    document.getElementById("minScoreDisplay").textContent = settings.minScore || 70;
    document.getElementById("minROI").value = settings.minROI || 15;
    document.getElementById("minProfit").value = settings.minProfit || 30000;

    // Grades
    const grades = settings.grades || ["A", "B"];
    ["A", "B", "C", "D"].forEach((g) => {
      const el = document.getElementById(`grade-${g}`);
      const checkbox = el.querySelector("input");
      if (grades.includes(g)) {
        checkbox.checked = true;
        el.classList.add("checked");
      } else {
        checkbox.checked = false;
        el.classList.remove("checked");
      }
    });
  });
}

function setupEventListeners() {
  // Range slider live update
  document.getElementById("minScore").addEventListener("input", (e) => {
    document.getElementById("minScoreDisplay").textContent = e.target.value;
  });

  // Grade toggles
  document.querySelectorAll(".grade-checkbox").forEach((label) => {
    label.addEventListener("click", (e) => {
      const checkbox = label.querySelector("input");
      checkbox.checked = !checkbox.checked;
      label.classList.toggle("checked", checkbox.checked);
    });
  });

  // Settings opslaan
  document.getElementById("save-btn").addEventListener("click", saveSettings);

  // Deals wissen
  document.getElementById("clear-btn").addEventListener("click", () => {
    if (confirm("Alle opgeslagen deals verwijderen?")) {
      chrome.runtime.sendMessage({ action: "clearSavedDeals" }, () => {
        loadSavedDeals();
        showToast("Deals gewist");
      });
    }
  });
}

function saveSettings() {
  const grades = [];
  document.querySelectorAll(".grade-checkbox input:checked").forEach((cb) => {
    grades.push(cb.value);
  });

  const settings = {
    apiBase: document.getElementById("apiBase").value.trim() || "http://localhost:8000",
    apiKey: document.getElementById("apiKey").value.trim(),
    minScore: parseInt(document.getElementById("minScore").value),
    minROI: parseFloat(document.getElementById("minROI").value),
    minProfit: parseInt(document.getElementById("minProfit").value),
    grades,
  };

  chrome.runtime.sendMessage({ action: "saveSettings", settings }, () => {
    showToast("✓ Instellingen opgeslagen");
  });
}

// ── Saved Deals ────────────────────────────────────────────────────────────

function loadSavedDeals() {
  chrome.runtime.sendMessage({ action: "getSavedDeals" }, (response) => {
    const deals = response?.deals || [];
    const list = document.getElementById("deals-list");
    const clearBtn = document.getElementById("clear-btn");
    const countEl = document.getElementById("deals-count");

    countEl.textContent = `${deals.length} deal${deals.length !== 1 ? "s" : ""} opgeslagen`;

    if (deals.length === 0) {
      list.innerHTML = `
        <div class="empty-state">
          <div class="empty-icon">🏚️</div>
          <p>Nog geen deals opgeslagen.</p>
          <p style="margin-top:6px;font-size:11px;">Open een woningpagina om te beginnen.</p>
        </div>
      `;
      clearBtn.style.display = "none";
      return;
    }

    clearBtn.style.display = "block";
    list.innerHTML = deals.map((deal) => `
      <div class="deal-item" data-url="${deal.url}">
        <div class="deal-grade grade-${deal.grade}-bg">${deal.grade}</div>
        <div class="deal-info">
          <div class="deal-address">${deal.address || deal.city}</div>
          <div class="deal-meta">
            €${fmt(deal.price)} · Score ${deal.score} · ROI ${(deal.roi || 0).toFixed(1)}%
          </div>
        </div>
        <div class="deal-profit">€${fmtK(deal.profit)}</div>
      </div>
    `).join("");

    // Klik op deal → open URL
    list.querySelectorAll(".deal-item").forEach((item) => {
      item.addEventListener("click", () => {
        chrome.tabs.create({ url: item.dataset.url });
      });
    });
  });
}

// ── Utils ──────────────────────────────────────────────────────────────────

function fmt(n) {
  if (!n) return "0";
  return Math.round(n).toLocaleString("nl-NL");
}

function fmtK(n) {
  if (!n) return "0";
  return n >= 1000 ? Math.round(n / 1000) + "k" : fmt(n);
}

function showToast(msg) {
  const toast = document.getElementById("toast");
  toast.textContent = msg;
  toast.style.opacity = "1";
  setTimeout(() => (toast.style.opacity = "0"), 2000);
}
