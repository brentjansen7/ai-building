/**
 * AI Arbitrage System - Chrome Extension Background Script
 * Handles API communication and background tasks
 */

const API_URL = 'http://localhost:8000';

// Listen for messages from content script
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  console.log('[Background] Message received:', request);

  if (request.action === 'checkArbitrage') {
    checkArbitrage(request.listing).then(result => {
      sendResponse({ success: true, data: result });
    }).catch(error => {
      sendResponse({ success: false, error: error.message });
    });
    return true; // Keep channel open for async response
  }

  if (request.action === 'getListings') {
    getListings(request.platform).then(result => {
      sendResponse({ success: true, data: result });
    }).catch(error => {
      sendResponse({ success: false, error: error.message });
    });
    return true;
  }
});

/**
 * Check if a listing has arbitrage potential
 */
async function checkArbitrage(listing) {
  const response = await fetch(`${API_URL}/api/v1/estimate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(listing)
  });

  if (!response.ok) throw new Error('API error');
  return await response.json();
}

/**
 * Get listings from API
 */
async function getListings(platform) {
  const response = await fetch(`${API_URL}/api/v1/listings?platform=${platform}`);
  if (!response.ok) throw new Error('API error');
  return await response.json();
}

// Test API connection on install
chrome.runtime.onInstalled.addListener(() => {
  console.log('[Extension] AI Arbitrage System installed');
  fetch(`${API_URL}/health`).catch(() => {
    console.warn('[Extension] API not reachable at localhost:8000');
  });
});
