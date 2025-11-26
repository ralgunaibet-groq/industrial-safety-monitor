// Socket.IO connection
const socket = io();

// UI Elements
const startBtn = document.getElementById('startBtn');
const stopBtn = document.getElementById('stopBtn');
const statusBadge = document.getElementById('statusBadge');
const severityIndicator = document.getElementById('severityIndicator');
const hazardPresent = document.getElementById('hazardPresent');
const severityLevel = document.getElementById('severityLevel');
const descriptionBox = document.getElementById('descriptionBox');
const hazardsList = document.getElementById('hazardsList');
const recommendationsList = document.getElementById('recommendationsList');

// Statistics
const totalAnalyses = document.getElementById('totalAnalyses');
const hazardsFound = document.getElementById('hazardsFound');
const criticalAlerts = document.getElementById('criticalAlerts');
const uptimeElement = document.getElementById('uptime');

// State
let isMonitoring = false;
let sessionStats = {
    totalAnalyses: 0,
    hazardsFound: 0,
    criticalAlerts: 0,
    startTime: null
};

// Start Monitoring
startBtn.addEventListener('click', async () => {
    try {
        const response = await fetch('/start', { method: 'POST' });
        const data = await response.json();
        
        if (response.ok && data.status === 'started') {
            isMonitoring = true;
            startBtn.disabled = true;
            stopBtn.disabled = false;
            
            sessionStats.startTime = Date.now();
            updateUptime();
            
            updateStatusBadge('Monitoring Active', 'success');
            showNotification('Monitoring started successfully', 'success');
        } else if (response.status === 400) {
            // API key not set
            alert('Error: GROQ_API_KEY not set!\n\nPlease restart the app with:\nexport GROQ_API_KEY="your_key"\npython app.py');
            showNotification('API key not configured', 'error');
        } else {
            throw new Error(data.error || 'Failed to start monitoring');
        }
    } catch (error) {
        console.error('Failed to start monitoring:', error);
        alert('Failed to start monitoring: ' + error.message);
        showNotification('Failed to start monitoring', 'error');
    }
});

// Stop Monitoring
stopBtn.addEventListener('click', async () => {
    try {
        const response = await fetch('/stop', { method: 'POST' });
        const data = await response.json();
        
        if (data.status === 'stopped') {
            isMonitoring = false;
            startBtn.disabled = false;
            stopBtn.disabled = true;
            
            sessionStats.startTime = null;
            
            updateStatusBadge('Monitoring Stopped', 'stopped');
            showNotification('Monitoring stopped', 'info');
        }
    } catch (error) {
        console.error('Failed to stop monitoring:', error);
        showNotification('Failed to stop monitoring', 'error');
    }
});

// Socket.IO Event Handlers
socket.on('connect', () => {
    console.log('Connected to server');
});

socket.on('disconnect', () => {
    console.log('Disconnected from server');
    updateStatusBadge('Disconnected', 'error');
});

socket.on('analysis_update', (data) => {
    console.log('Analysis update:', data);
    updateAnalysis(data);
});

// Update Analysis Display
function updateAnalysis(data) {
    if (!data) return;
    
    // Update statistics
    sessionStats.totalAnalyses++;
    totalAnalyses.textContent = sessionStats.totalAnalyses;
    
    if (data.new_incident) {
        sessionStats.hazardsFound++;
        hazardsFound.textContent = sessionStats.hazardsFound;
        
        if (data.severity === 'critical' || data.severity === 'high') {
            sessionStats.criticalAlerts++;
            criticalAlerts.textContent = sessionStats.criticalAlerts;
        }
    }
    
    // Update hazard present status
    hazardPresent.textContent = data.hazard_present ? 'Yes' : 'No';
    hazardPresent.style.color = data.hazard_present ? '#f59e0b' : '#16a34a';
    
    // Update severity level
    severityLevel.textContent = data.severity.toUpperCase();
    severityLevel.style.color = getSeverityColor(data.severity);
    
    // Update severity indicator
    updateSeverityIndicator(data.severity);
    
    // Update description
    descriptionBox.innerHTML = `
        <p class="description-text">${data.description}</p>
    `;
    
    // Update hazards list
    if (data.hazard_types && data.hazard_types.length > 0) {
        hazardsList.innerHTML = data.hazard_types.map(hazard => `
            <div class="hazard-item ${data.severity === 'critical' ? 'alert-critical' : ''}">
                ${hazard}
            </div>
        `).join('');
    } else {
        hazardsList.innerHTML = '<div class="empty-state"><p>No hazards detected</p></div>';
    }
    
    // Update recommendations list
    if (data.recommended_actions && data.recommended_actions.length > 0) {
        recommendationsList.innerHTML = data.recommended_actions.map(action => `
            <div class="recommendation-item">
                ${action}
            </div>
        `).join('');
    } else {
        recommendationsList.innerHTML = '<div class="empty-state"><p>No recommendations at this time</p></div>';
    }
    
    // Update status badge
    if (data.hazard_present) {
        updateStatusBadge(`${data.severity.toUpperCase()} Hazard Detected`, data.severity);
    } else {
        updateStatusBadge('Safe - No Hazards', 'success');
    }
    
    // Play alert sound for critical hazards
    if (data.severity === 'critical' || data.severity === 'high') {
        playAlertSound();
    }
}

// Update Status Badge
function updateStatusBadge(text, status) {
    const statusIcon = statusBadge.querySelector('.status-icon');
    const statusText = statusBadge.querySelector('.status-text');
    
    statusText.textContent = text;
    
    // Update colors based on status
    switch(status) {
        case 'success':
            statusIcon.style.color = '#16a34a';
            break;
        case 'low':
            statusIcon.style.color = '#16a34a';
            break;
        case 'medium':
            statusIcon.style.color = '#f59e0b';
            break;
        case 'high':
            statusIcon.style.color = '#f97316';
            break;
        case 'critical':
            statusIcon.style.color = '#dc2626';
            break;
        case 'error':
            statusIcon.style.color = '#dc2626';
            break;
        case 'stopped':
            statusIcon.style.color = '#64748b';
            break;
        default:
            statusIcon.style.color = '#cbd5e1';
    }
}

// Update Severity Indicator
function updateSeverityIndicator(severity) {
    // Remove all severity classes
    severityIndicator.className = 'severity-indicator';
    
    // Add new severity class
    severityIndicator.classList.add(`severity-${severity}`);
    
    // Update text
    const severityText = severityIndicator.querySelector('.severity-text');
    severityText.textContent = severity.toUpperCase();
}

// Get Severity Color
function getSeverityColor(severity) {
    switch(severity) {
        case 'none':
            return '#16a34a';
        case 'low':
            return '#16a34a';
        case 'medium':
            return '#f59e0b';
        case 'high':
            return '#f97316';
        case 'critical':
            return '#dc2626';
        default:
            return '#cbd5e1';
    }
}

// Update Uptime
function updateUptime() {
    if (!sessionStats.startTime) return;
    
    const elapsed = Date.now() - sessionStats.startTime;
    const totalMinutes = Math.floor(elapsed / 60000);
    const seconds = Math.floor((elapsed % 60000) / 1000);
    
    uptimeElement.textContent = `${pad(totalMinutes)}:${pad(seconds)}`;
    
    if (isMonitoring) {
        setTimeout(updateUptime, 1000);
    }
}

function pad(num) {
    return num.toString().padStart(2, '0');
}

// Show Notification
function showNotification(message, type = 'info') {
    // You can implement a toast notification here
    console.log(`[${type.toUpperCase()}] ${message}`);
}

// Play Alert Sound
function playAlertSound() {
    // Create a simple beep using Web Audio API
    try {
        const audioContext = new (window.AudioContext || window.webkitAudioContext)();
        const oscillator = audioContext.createOscillator();
        const gainNode = audioContext.createGain();
        
        oscillator.connect(gainNode);
        gainNode.connect(audioContext.destination);
        
        oscillator.frequency.value = 800;
        oscillator.type = 'sine';
        
        gainNode.gain.setValueAtTime(0.3, audioContext.currentTime);
        gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.5);
        
        oscillator.start(audioContext.currentTime);
        oscillator.stop(audioContext.currentTime + 0.5);
    } catch (error) {
        console.error('Failed to play alert sound:', error);
    }
}

// Initialize
console.log('Industrial Safety Monitor initialized');

