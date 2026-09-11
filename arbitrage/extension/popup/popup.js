/**
 * Popup script for extension
 */

const API_URL = 'http://localhost:8000';

// Check API status on load
document.addEventListener('DOMContentLoaded', checkAPIStatus);

async function checkAPIStatus() {
    try {
        const response = await fetch(`${API_URL}/health`);
        if (response.ok) {
            document.getElementById('status').className = 'status online';
            document.getElementById('status').textContent = '✓ API Connected';
            document.getElementById('info').textContent = 'Ready to scan marketplaces.';
        } else {
            setOffline();
        }
    } catch (error) {
        setOffline();
    }
}

function setOffline() {
    document.getElementById('status').className = 'status offline';
    document.getElementById('status').textContent = '✗ API Offline';
    document.getElementById('info').textContent = 'Make sure the Python API is running on localhost:8000';
}
