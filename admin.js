// Global variables
let socket;
let dashboardData = {
    totalUsers: 0,
    totalSwaps: 0,
    pendingSwaps: 0,
    bannedUsers: 0
};

// Initialize the application
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

// Initialize application
function initializeApp() {
    setupEventListeners();
    checkAuthStatus();
    initializeSocketIO();
}

// Setup event listeners
function setupEventListeners() {
    // Login form
    const loginForm = document.getElementById('login-form');
    if (loginForm) {
        loginForm.addEventListener('submit', handleLogin);
    }

    // Prevent form submission on enter for input fields
    document.addEventListener('keypress', function(e) {
        if (e.key === 'Enter' && e.target.tagName !== 'TEXTAREA' && e.target.tagName !== 'BUTTON') {
            e.preventDefault();
        }
    });
}

// Check authentication status
function checkAuthStatus() {
    const isLoggedIn = sessionStorage.getItem('adminLoggedIn') === 'true';
    if (isLoggedIn) {
        showDashboard();
        loadDashboardData();
    } else {
        showLogin();
    }
}

// Initialize Socket.IO for real-time updates
function initializeSocketIO() {
    try {
        socket = io();
        
        // Listen for real-time events
        socket.on('new_swap', function(data) {
            updateNotificationCount();
            showToast('New swap request received!', 'info');
            refreshStats();
        });

        socket.on('swap_update', function(data) {
            updateNotificationCount();
            showToast(`Swap status updated: ${data.status}`, 'info');
            refreshStats();
        });

        socket.on('connect', function() {
            console.log('Connected to Socket.IO server');
        });

        socket.on('disconnect', function() {
            console.log('Disconnected from Socket.IO server');
        });
    } catch (error) {
        console.warn('Socket.IO not available, continuing without real-time updates');
    }
}

// Handle login form submission
async function handleLogin(e) {
    e.preventDefault();
    
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    const loginBtn = document.querySelector('.login-btn');
    
    // Validate input
    if (!username || !password) {
        showToast('Please enter both username and password', 'error');
        return;
    }
    
    // Show loading state
    loginBtn.innerHTML = '<div class="loading"></div> Logging in...';
    loginBtn.disabled = true;
    
    try {
        const response = await fetch('/admin/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password })
        });
        
        if (response.ok) {
            sessionStorage.setItem('adminLoggedIn', 'true');
            showDashboard();
            loadDashboardData();
            showToast('Login successful!', 'success');
        } else {
            const error = await response.json();
            showToast(error.error || 'Login failed', 'error');
        }
    } catch (error) {
        showToast('An error occurred. Please try again.', 'error');
    } finally {
        loginBtn.innerHTML = '<i class="fas fa-sign-in-alt"></i> Login';
        loginBtn.disabled = false;
    }
}

// Show login screen
function showLogin() {
    document.getElementById('login-container').style.display = 'block';
    document.getElementById('dashboard-container').style.display = 'none';
}

// Show dashboard
function showDashboard() {
    document.getElementById('login-container').style.display = 'none';
    document.getElementById('dashboard-container').style.display = 'block';
}

// Logout functionality
function logout() {
    sessionStorage.removeItem('adminLoggedIn');
    showLogin();
    showToast('Logged out successfully!', 'success');
}

// Load initial dashboard data
async function loadDashboardData() {
    try {
        const response = await fetch('/admin/report');
        const data = await response.json();
        dashboardData.totalUsers = data.users.length;
        dashboardData.totalSwaps = data.swaps.length;
        dashboardData.pendingSwaps = data.swaps.filter(s => s.status === 'pending').length;
        dashboardData.bannedUsers = 0; // Placeholder; requires tracking banned users
        updateStatsDisplay();
    } catch (error) {
        console.error('Error loading dashboard data:', error);
    }
}

// Update stats display
function updateStatsDisplay() {
    document.getElementById('total-users').textContent = dashboardData.totalUsers;
    document.getElementById('total-swaps').textContent = dashboardData.totalSwaps;
    document.getElementById('pending-swaps').textContent = dashboardData.pendingSwaps;
    document.getElementById('banned-users').textContent = dashboardData.bannedUsers;
    updateNotificationCount();
}

// Update notification count
function updateNotificationCount() {
    const count = dashboardData.pendingSwaps; // Could expand to include other notifications
    document.getElementById('notification-count').textContent = count;
}

// Refresh stats and data
function refreshStats() {
    loadDashboardData();
    monitorSwaps(); // Refresh swap display
}

// Ban user
async function banUser() {
    const userId = document.getElementById('user-id').value;
    if (!userId) {
        showToast('Please enter a user ID', 'error');
        return;
    }
    
    if (!confirm(`Are you sure you want to ban user ${userId}?`)) return;
    
    try {
        const response = await fetch(`/admin/ban/${userId}`, { method: 'POST' });
        const data = await response.json();
        showToast(data.message, 'success');
        refreshStats();
    } catch (error) {
        showToast('Failed to ban user', 'error');
    }
}

// Review and clear user skills
async function reviewUser() {
    const userId = document.getElementById('user-id').value;
    if (!userId) {
        showToast('Please enter a user ID', 'error');
        return;
    }
    
    if (!confirm(`Are you sure you want to clear skills for user ${userId}?`)) return;
    
    try {
        const response = await fetch(`/admin/review/${userId}`, { method: 'PUT' });
        const data = await response.json();
        showToast(data.message, 'success');
        refreshStats();
    } catch (error) {
        showToast('Failed to clear skills', 'error');
    }
}

// Monitor swaps
async function monitorSwaps() {
    const status = document.getElementById('swap-status').value;
    try {
        const response = await fetch(`/admin/swaps${status ? `?status=${status}` : ''}`);
        const swaps = await response.json();
        displayData(swaps, 'Swaps', status ? `Filtered by ${status}` : 'All Swaps');
    } catch (error) {
        showToast('Failed to load swaps', 'error');
    }
}

// Broadcast message
async function broadcastMessage() {
    const message = document.getElementById('broadcast-message').value.trim();
    if (!message) {
        showToast('Please enter a message', 'error');
        return;
    }
    
    try {
        const response = await fetch('/admin/broadcast', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message })
        });
        const data = await response.json();
        showToast(data.message, 'success');
        document.getElementById('broadcast-message').value = '';
    } catch (error) {
        showToast('Failed to send broadcast', 'error');
    }
}

// Download report
async function downloadReport() {
    try {
        const response = await fetch('/admin/report');
        const data = await response.json();
        const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'skill_swap_report.json';
        a.click();
        window.URL.revokeObjectURL(url);
        showToast('Report downloaded successfully!', 'success');
    } catch (error) {
        showToast('Failed to download report', 'error');
    }
}

// Display data in the content area
function displayData(data, title, subtitle = '') {
    const content = document.getElementById('display-content');
    content.innerHTML = '';

    if (!data.length) {
        content.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-inbox"></i>
                <p>No ${title.toLowerCase()} to display.</p>
            </div>
        `;
        document.getElementById('display-title').textContent = `${title} ${subtitle}`;
        return;
    }

    const table = document.createElement('table');
    table.className = 'data-table';
    
    const thead = document.createElement('thead');
    const tbody = document.createElement('tbody');
    
    const headers = Object.keys(data[0] || {});
    const headerRow = document.createElement('tr');
    headers.forEach(header => {
        const th = document.createElement('th');
        th.textContent = header.charAt(0).toUpperCase() + header.slice(1).replace('_', ' ');
        headerRow.appendChild(th);
    });
    thead.appendChild(headerRow);
    
    data.forEach(item => {
        const row = document.createElement('tr');
        headers.forEach(header => {
            const td = document.createElement('td');
            let value = item[header];
            if (header === 'status') {
                const badgeClass = `status-${value.toLowerCase()}`;
                td.innerHTML = `<span class="status-badge ${badgeClass}">${value}</span>`;
            } else if (header === 'created_at') {
                td.textContent = new Date(value).toLocaleString();
            } else {
                td.textContent = value;
            }
            row.appendChild(td);
        });
        tbody.appendChild(row);
    });
    
    table.appendChild(thead);
    table.appendChild(tbody);
    content.appendChild(table);
    document.getElementById('display-title').textContent = `${title} ${subtitle}`;
}

// Show toast notification
function showToast(message, type = 'info') {
    const container = document.getElementById('toast-container');
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.innerHTML = `
        <div class="toast-header">${type.charAt(0).toUpperCase() + type.slice(1)}</div>
        <div class="toast-message">${message}</div>
    `;
    container.appendChild(toast);
    
    setTimeout(() => toast.classList.add('fade-in'), 10);
    setTimeout(() => {
        toast.classList.add('hidden');
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// Refresh data display
function refreshData() {
    monitorSwaps();
    loadDashboardData();
}