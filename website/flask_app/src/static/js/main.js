// Main JavaScript for Toronto AI Weather

document.addEventListener('DOMContentLoaded', function() {
    // Mobile menu toggle
    const menuToggle = document.querySelector('.mobile-menu-toggle');
    const nav = document.querySelector('nav');
    
    if (menuToggle) {
        menuToggle.addEventListener('click', function() {
            nav.classList.toggle('active');
        });
    }
    
    // Flash message close buttons
    const closeButtons = document.querySelectorAll('.flash-message .close-button');
    
    closeButtons.forEach(button => {
        button.addEventListener('click', function() {
            this.parentElement.style.display = 'none';
        });
    });
    
    // Tab functionality
    const tabs = document.querySelectorAll('.tab');
    
    tabs.forEach(tab => {
        tab.addEventListener('click', function() {
            // Remove active class from all tabs
            tabs.forEach(t => t.classList.remove('active'));
            
            // Add active class to clicked tab
            this.classList.add('active');
            
            // Hide all tab content
            const tabContents = document.querySelectorAll('.tab-content');
            tabContents.forEach(content => content.classList.remove('active'));
            
            // Show corresponding tab content
            const targetId = this.getAttribute('data-target');
            const targetContent = document.getElementById(targetId);
            if (targetContent) {
                targetContent.classList.add('active');
            }
        });
    });
    
    // Initialize maps if map container exists
    const mapContainer = document.getElementById('map');
    if (mapContainer) {
        initMap(mapContainer);
    }
    
    // Initialize device registration
    initDeviceRegistration();
    
    // Initialize distributed computation
    initDistributedComputation();
});

// Map initialization
function initMap(container) {
    // Get coordinates from data attributes or use defaults (Toronto)
    const lat = parseFloat(container.getAttribute('data-lat') || 43.6532);
    const lon = parseFloat(container.getAttribute('data-lon') || -79.3832);
    const zoom = parseInt(container.getAttribute('data-zoom') || 10);
    
    // Create map
    const map = L.map(container).setView([lat, lon], zoom);
    
    // Add dark theme tile layer
    L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
        subdomains: 'abcd',
        maxZoom: 19
    }).addTo(map);
    
    // Add marker for current location
    const marker = L.marker([lat, lon]).addTo(map);
    
    // If this is a weather map, add weather data
    if (container.classList.contains('weather-map')) {
        addWeatherOverlay(map);
    }
    
    // If this is a global map, add global weather data
    if (container.classList.contains('global-map')) {
        addGlobalWeatherOverlay(map);
    }
    
    // Make map responsive
    window.addEventListener('resize', function() {
        map.invalidateSize();
    });
    
    // Store map in global variable for later access
    window.currentMap = map;
    
    return map;
}

// Add weather overlay to map
function addWeatherOverlay(map) {
    // This would typically fetch weather data from the API
    // For now, we'll just add a simple temperature overlay
    
    // Example: Add a temperature gradient overlay
    const bounds = map.getBounds();
    const overlay = L.imageOverlay(
        '/static/img/temp_overlay.png',
        bounds,
        {
            opacity: 0.5,
            interactive: true
        }
    ).addTo(map);
}

// Add global weather overlay
function addGlobalWeatherOverlay(map) {
    // This would fetch global weather data
    // For now, just a placeholder
    console.log('Global weather overlay would be added here');
}

// Device registration for distributed computation
function initDeviceRegistration() {
    const registerButton = document.getElementById('register-device-button');
    
    if (registerButton) {
        registerButton.addEventListener('click', function() {
            // Check if user is logged in
            const userId = this.getAttribute('data-user-id');
            if (!userId) {
                alert('Please log in to register your device');
                return;
            }
            
            // Get device information
            const deviceInfo = getDeviceInfo();
            
            // Show confirmation dialog
            if (confirm(`Would you like to contribute processing power from this device?\n\nDevice: ${deviceInfo.name}\nCPU Cores: ${deviceInfo.cpuCores}\nMemory: ${deviceInfo.memory}MB\n\nYou can adjust resource allocation in your profile.`)) {
                registerDevice(deviceInfo);
            }
        });
    }
}

// Get device information
function getDeviceInfo() {
    return {
        uuid: generateUUID(),
        name: navigator.platform || 'Unknown Device',
        type: getDeviceType(),
        osName: navigator.platform || 'Unknown OS',
        osVersion: navigator.userAgent || 'Unknown Version',
        browserName: navigator.appName || 'Unknown Browser',
        browserVersion: navigator.appVersion || 'Unknown Version',
        cpuCores: navigator.hardwareConcurrency || 2,
        memory: 4096, // Placeholder, can't reliably get this from browser
        maxResourceAllocation: 0.5 // Default to 50%
    };
}

// Generate UUID for device
function generateUUID() {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
        const r = Math.random() * 16 | 0;
        const v = c === 'x' ? r : (r & 0x3 | 0x8);
        return v.toString(16);
    });
}

// Get device type
function getDeviceType() {
    const ua = navigator.userAgent;
    if (/(tablet|ipad|playbook|silk)|(android(?!.*mobi))/i.test(ua)) {
        return 'tablet';
    }
    if (/Mobile|Android|iP(hone|od)|IEMobile|BlackBerry|Kindle|Silk-Accelerated|(hpw|web)OS|Opera M(obi|ini)/.test(ua)) {
        return 'mobile';
    }
    return 'desktop';
}

// Register device with server
function registerDevice(deviceInfo) {
    // Send registration request to server
    fetch('/api/device/register', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-API-Key': getApiKey() // Function to get API key from storage or page
        },
        body: JSON.stringify(deviceInfo)
    })
    .then(response => response.json())
    .then(data => {
        if (data.device_id) {
            alert('Device registered successfully! Thank you for contributing to Toronto AI Weather.');
            
            // Store device ID in local storage
            localStorage.setItem('deviceId', data.device_id);
            localStorage.setItem('deviceUUID', deviceInfo.uuid);
            
            // Start heartbeat
            startHeartbeat(deviceInfo.uuid);
        } else {
            alert('Error registering device: ' + (data.error || 'Unknown error'));
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Error registering device. Please try again later.');
    });
}

// Get API key from page or storage
function getApiKey() {
    // Try to get from page
    const apiKeyElement = document.getElementById('api-key');
    if (apiKeyElement) {
        return apiKeyElement.value;
    }
    
    // Try to get from local storage
    return localStorage.getItem('apiKey') || '';
}

// Start device heartbeat
function startHeartbeat(deviceUUID) {
    // Send heartbeat every 30 seconds
    setInterval(() => {
        sendHeartbeat(deviceUUID);
    }, 30000);
    
    // Send initial heartbeat
    sendHeartbeat(deviceUUID);
}

// Send heartbeat to server
function sendHeartbeat(deviceUUID) {
    fetch('/api/device/heartbeat', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-API-Key': getApiKey()
        },
        body: JSON.stringify({
            device_uuid: deviceUUID,
            available_resources: getAvailableResources()
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.pending_tasks > 0) {
            // Process pending tasks
            processTasks(data.tasks);
        }
    })
    .catch(error => {
        console.error('Heartbeat error:', error);
    });
}

// Get available resources
function getAvailableResources() {
    // Get max resource allocation from local storage or use default
    const maxAllocation = parseFloat(localStorage.getItem('maxResourceAllocation') || 0.5);
    
    return {
        cpu: navigator.hardwareConcurrency * maxAllocation,
        memory: 2048 * maxAllocation, // Placeholder
        network: navigator.connection ? (navigator.connection.downlink || 10) : 10
    };
}

// Process tasks from server
function processTasks(tasks) {
    if (!tasks || tasks.length === 0) {
        return;
    }
    
    // Process each task
    tasks.forEach(task => {
        // Create worker for task
        const worker = new Worker('/static/js/task-worker.js');
        
        // Send task to worker
        worker.postMessage({
            task_uuid: task.task_uuid,
            task_type: task.task_type,
            data: JSON.parse(task.data)
        });
        
        // Listen for results
        worker.onmessage = function(e) {
            if (e.data.status === 'completed') {
                // Send result to server
                submitTaskResult(task.task_uuid, e.data);
                
                // Terminate worker
                worker.terminate();
            }
        };
    });
}

// Submit task result to server
function submitTaskResult(taskUUID, result) {
    fetch('/api/task/result', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-API-Key': getApiKey()
        },
        body: JSON.stringify({
            task_uuid: taskUUID,
            device_uuid: localStorage.getItem('deviceUUID'),
            status: result.status,
            result: result.result,
            cpu_usage: result.cpu_usage,
            memory_usage: result.memory_usage,
            duration: result.duration,
            result_quality: result.result_quality
        })
    })
    .then(response => response.json())
    .then(data => {
        console.log('Task result submitted:', data);
    })
    .catch(error => {
        console.error('Error submitting task result:', error);
    });
}

// Initialize distributed computation
function initDistributedComputation() {
    // Check if device is already registered
    const deviceId = localStorage.getItem('deviceId');
    const deviceUUID = localStorage.getItem('deviceUUID');
    
    if (deviceId && deviceUUID) {
        // Start heartbeat
        startHeartbeat(deviceUUID);
    }
}

// Weather icon mapping
function getWeatherIcon(condition) {
    const iconMap = {
        'Clear': 'fa-sun',
        'Clouds': 'fa-cloud',
        'Rain': 'fa-cloud-rain',
        'Drizzle': 'fa-cloud-rain',
        'Thunderstorm': 'fa-bolt',
        'Snow': 'fa-snowflake',
        'Mist': 'fa-smog',
        'Smoke': 'fa-smog',
        'Haze': 'fa-smog',
        'Dust': 'fa-smog',
        'Fog': 'fa-smog',
        'Sand': 'fa-wind',
        'Ash': 'fa-volcano',
        'Squall': 'fa-wind',
        'Tornado': 'fa-tornado'
    };
    
    return iconMap[condition] || 'fa-cloud';
}
