// MyRVM Platform Integration - Monitoring Dashboard JavaScript

class MonitoringDashboard {
    constructor() {
        this.refreshInterval = 5000; // 5 seconds
        this.charts = {};
        this.isLoading = false;
        this.retryCount = 0;
        this.maxRetries = 3;
        
        this.init();
    }
    
    init() {
        this.hideLoadingOverlay();
        this.initializeCharts();
        this.startAutoRefresh();
        this.loadInitialData();
        
        // Add event listeners
        this.addEventListeners();
        
        console.log('Monitoring Dashboard initialized');
    }
    
    hideLoadingOverlay() {
        const overlay = document.getElementById('loading-overlay');
        if (overlay) {
            setTimeout(() => {
                overlay.classList.add('hidden');
            }, 1000);
        }
    }
    
    initializeCharts() {
        // Performance Chart
        const performanceCtx = document.getElementById('performance-chart');
        if (performanceCtx) {
            this.charts.performance = new Chart(performanceCtx, {
                type: 'line',
                data: {
                    labels: [],
                    datasets: [
                        {
                            label: 'CPU %',
                            data: [],
                            borderColor: '#e74c3c',
                            backgroundColor: 'rgba(231, 76, 60, 0.1)',
                            tension: 0.4
                        },
                        {
                            label: 'Memory %',
                            data: [],
                            borderColor: '#3498db',
                            backgroundColor: 'rgba(52, 152, 219, 0.1)',
                            tension: 0.4
                        },
                        {
                            label: 'Disk %',
                            data: [],
                            borderColor: '#f39c12',
                            backgroundColor: 'rgba(243, 156, 18, 0.1)',
                            tension: 0.4
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: {
                            beginAtZero: true,
                            max: 100,
                            ticks: {
                                callback: function(value) {
                                    return value + '%';
                                }
                            }
                        }
                    },
                    plugins: {
                        legend: {
                            position: 'top',
                        }
                    }
                }
            });
        }
        
        // Resource Chart
        const resourceCtx = document.getElementById('resource-chart');
        if (resourceCtx) {
            this.charts.resource = new Chart(resourceCtx, {
                type: 'doughnut',
                data: {
                    labels: ['Used', 'Available'],
                    datasets: [{
                        data: [0, 100],
                        backgroundColor: ['#e74c3c', '#ecf0f1'],
                        borderWidth: 0
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'bottom',
                        }
                    }
                }
            });
        }
    }
    
    startAutoRefresh() {
        setInterval(() => {
            this.refreshData();
        }, this.refreshInterval);
        
        // Start countdown timer
        this.startCountdown();
    }
    
    startCountdown() {
        const countdownElement = document.getElementById('refresh-countdown');
        if (!countdownElement) return;
        
        let seconds = this.refreshInterval / 1000;
        
        const countdown = setInterval(() => {
            countdownElement.textContent = seconds;
            seconds--;
            
            if (seconds < 0) {
                seconds = this.refreshInterval / 1000;
            }
        }, 1000);
    }
    
    async loadInitialData() {
        try {
            await Promise.all([
                this.loadSystemStatus(),
                this.loadMetrics(),
                this.loadAlerts(),
                this.loadConfig()
            ]);
        } catch (error) {
            console.error('Error loading initial data:', error);
            this.showError('Failed to load initial data');
        }
    }
    
    async refreshData() {
        if (this.isLoading) return;
        
        this.isLoading = true;
        
        try {
            await Promise.all([
                this.loadSystemStatus(),
                this.loadMetrics(),
                this.loadAlerts()
            ]);
            
            this.retryCount = 0;
        } catch (error) {
            console.error('Error refreshing data:', error);
            this.retryCount++;
            
            if (this.retryCount >= this.maxRetries) {
                this.showError('Connection lost. Retrying...');
            }
        } finally {
            this.isLoading = false;
        }
    }
    
    async loadSystemStatus() {
        try {
            const response = await fetch('/api/status');
            if (!response.ok) throw new Error('Failed to fetch system status');
            
            const status = await response.json();
            this.updateSystemStatus(status);
        } catch (error) {
            console.error('Error loading system status:', error);
            throw error;
        }
    }
    
    async loadMetrics() {
        try {
            const response = await fetch('/api/metrics');
            if (!response.ok) throw new Error('Failed to fetch metrics');
            
            const metrics = await response.json();
            this.updateMetrics(metrics);
            this.updateCharts(metrics);
        } catch (error) {
            console.error('Error loading metrics:', error);
            throw error;
        }
    }
    
    async loadAlerts() {
        try {
            const response = await fetch('/api/alerts');
            if (!response.ok) throw new Error('Failed to fetch alerts');
            
            const alerts = await response.json();
            this.updateAlerts(alerts);
        } catch (error) {
            console.error('Error loading alerts:', error);
            throw error;
        }
    }
    
    async loadConfig() {
        try {
            const response = await fetch('/api/config');
            if (!response.ok) throw new Error('Failed to fetch config');
            
            const config = await response.json();
            this.updateConfig(config);
        } catch (error) {
            console.error('Error loading config:', error);
        }
    }
    
    updateSystemStatus(status) {
        // Update status indicator
        const statusElement = document.getElementById('system-status');
        if (statusElement) {
            statusElement.textContent = status.status || 'unknown';
            statusElement.className = `status-indicator ${status.status || 'unknown'}`;
        }
        
        // Update last update time
        const lastUpdateElement = document.getElementById('last-update');
        if (lastUpdateElement && status.timestamp) {
            const updateTime = new Date(status.timestamp).toLocaleTimeString();
            lastUpdateElement.textContent = `Last update: ${updateTime}`;
        }
        
        // Update system uptime
        const uptimeElement = document.getElementById('system-uptime');
        if (uptimeElement && status.uptime) {
            uptimeElement.textContent = this.formatUptime(status.uptime);
        }
        
        // Update process memory
        const processMemoryElement = document.getElementById('process-memory');
        if (processMemoryElement && status.process_memory_mb) {
            processMemoryElement.textContent = `${status.process_memory_mb.toFixed(1)} MB`;
        }
    }
    
    updateMetrics(metrics) {
        // Update CPU usage
        const cpuUsage = metrics.system?.cpu?.percent || 0;
        this.updateProgressBar('cpu-usage', 'cpu-progress', cpuUsage);
        
        // Update Memory usage
        const memoryUsage = metrics.system?.memory?.percent || 0;
        this.updateProgressBar('memory-usage', 'memory-progress', memoryUsage);
        
        // Update Disk usage
        const diskUsage = metrics.system?.disk?.percent || 0;
        this.updateProgressBar('disk-usage', 'disk-progress', diskUsage);
        
        // Update CPU cores
        const cpuCoresElement = document.getElementById('cpu-cores');
        if (cpuCoresElement && metrics.system?.cpu?.count) {
            cpuCoresElement.textContent = metrics.system.cpu.count;
        }
    }
    
    updateProgressBar(valueId, progressId, value) {
        const valueElement = document.getElementById(valueId);
        const progressElement = document.getElementById(progressId);
        
        if (valueElement) {
            valueElement.textContent = `${value.toFixed(1)}%`;
        }
        
        if (progressElement) {
            progressElement.style.width = `${value}%`;
            
            // Update color based on value
            progressElement.className = 'progress-fill';
            if (value < 50) {
                progressElement.classList.add('low');
            } else if (value < 80) {
                progressElement.classList.add('medium');
            } else {
                progressElement.classList.add('high');
            }
        }
    }
    
    updateCharts(metrics) {
        const now = new Date().toLocaleTimeString();
        
        // Update performance chart
        if (this.charts.performance) {
            const chart = this.charts.performance;
            const maxDataPoints = 20;
            
            // Add new data point
            chart.data.labels.push(now);
            chart.data.datasets[0].data.push(metrics.system?.cpu?.percent || 0);
            chart.data.datasets[1].data.push(metrics.system?.memory?.percent || 0);
            chart.data.datasets[2].data.push(metrics.system?.disk?.percent || 0);
            
            // Remove old data points
            if (chart.data.labels.length > maxDataPoints) {
                chart.data.labels.shift();
                chart.data.datasets.forEach(dataset => dataset.data.shift());
            }
            
            chart.update('none');
        }
        
        // Update resource chart
        if (this.charts.resource) {
            const chart = this.charts.resource;
            const memoryUsed = metrics.system?.memory?.percent || 0;
            const memoryAvailable = 100 - memoryUsed;
            
            chart.data.datasets[0].data = [memoryUsed, memoryAvailable];
            chart.update('none');
        }
    }
    
    updateAlerts(alerts) {
        const alertsContainer = document.getElementById('alerts-container');
        const alertsCountElement = document.getElementById('alerts-count');
        const alertIndicator = document.getElementById('alert-indicator');
        
        if (!alertsContainer) return;
        
        const activeAlerts = alerts.active || {};
        const alertCount = Object.keys(activeAlerts).length;
        
        // Update alerts count
        if (alertsCountElement) {
            alertsCountElement.textContent = alertCount;
        }
        
        // Update alert indicator
        if (alertIndicator) {
            if (alertCount > 0) {
                alertIndicator.classList.add('has-alerts');
            } else {
                alertIndicator.classList.remove('has-alerts');
            }
        }
        
        // Update alerts display
        if (alertCount === 0) {
            alertsContainer.innerHTML = '<div class="no-alerts">No active alerts</div>';
        } else {
            let alertsHTML = '';
            Object.values(activeAlerts).forEach(alert => {
                alertsHTML += this.createAlertHTML(alert);
            });
            alertsContainer.innerHTML = alertsHTML;
        }
    }
    
    createAlertHTML(alert) {
        const timestamp = new Date(alert.timestamp).toLocaleString();
        
        return `
            <div class="alert-item ${alert.severity}">
                <div class="alert-content">
                    <div class="alert-message">${alert.message}</div>
                    <div class="alert-details">
                        ${alert.metric_path}: ${alert.metric_value} ${alert.condition} ${alert.threshold}
                    </div>
                    <div class="alert-timestamp">${timestamp}</div>
                </div>
            </div>
        `;
    }
    
    updateConfig(config) {
        // Update app status
        const appStatusElement = document.getElementById('app-status');
        if (appStatusElement) {
            appStatusElement.textContent = 'Running';
        }
        
        // Update environment
        const appEnvironmentElement = document.getElementById('app-environment');
        if (appEnvironmentElement && config.environment) {
            appEnvironmentElement.textContent = config.environment;
        }
        
        // Update version
        const appVersionElement = document.getElementById('app-version');
        if (appVersionElement && config.dashboard_version) {
            appVersionElement.textContent = config.dashboard_version;
        }
    }
    
    formatUptime(seconds) {
        const days = Math.floor(seconds / 86400);
        const hours = Math.floor((seconds % 86400) / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        
        if (days > 0) {
            return `${days}d ${hours}h ${minutes}m`;
        } else if (hours > 0) {
            return `${hours}h ${minutes}m`;
        } else {
            return `${minutes}m`;
        }
    }
    
    showError(message) {
        console.error(message);
        
        // You could add a toast notification here
        const statusElement = document.getElementById('system-status');
        if (statusElement) {
            statusElement.textContent = 'error';
            statusElement.className = 'status-indicator error';
        }
    }
    
    addEventListeners() {
        // Add any custom event listeners here
        document.addEventListener('keydown', (e) => {
            if (e.key === 'r' && e.ctrlKey) {
                e.preventDefault();
                this.refreshData();
            }
        });
        
        // Add click handlers for interactive elements
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('card')) {
                // Handle card clicks
                console.log('Card clicked:', e.target);
            }
        });
    }
    
    // Public methods for external use
    refresh() {
        this.refreshData();
    }
    
    exportData(format = 'json') {
        window.open(`/api/export?format=${format}`, '_blank');
    }
}

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.dashboard = new MonitoringDashboard();
});

// Handle page visibility changes
document.addEventListener('visibilitychange', () => {
    if (document.hidden) {
        console.log('Dashboard hidden - pausing updates');
    } else {
        console.log('Dashboard visible - resuming updates');
        if (window.dashboard) {
            window.dashboard.refresh();
        }
    }
});

// Handle window resize
window.addEventListener('resize', () => {
    if (window.dashboard && window.dashboard.charts) {
        Object.values(window.dashboard.charts).forEach(chart => {
            chart.resize();
        });
    }
});
