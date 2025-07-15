

class DashboardOptimized {
    constructor() {
        this.chartLoaded = false;
        this.chartInstance = null;
        this.init();
    }

    init() {
        this.setupLazyChart();
        this.preloadCriticalResources();
    }

    setupLazyChart() {
        const chartContainer = document.getElementById('performanceChart');
        if (!chartContainer) return;

        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    this.loadChart();
                    observer.unobserve(entry.target);
                }
            });
        }, {
            rootMargin: '50px'
        });

        observer.observe(chartContainer);
    }

    loadChart() {
        if (this.chartLoaded) return;
        
        const script = document.createElement('script');
        script.src = 'https://cdn.jsdelivr.net/npm/chart.js@3.9.1/dist/chart.min.js';
        script.onload = () => {
            this.chartLoaded = true;
            this.createPerformanceChart();
        };
        script.onerror = () => {
            console.warn('Chart.js failed to load');
        };
        document.head.appendChild(script);
    }

    createPerformanceChart() {
        const ctx = document.getElementById('performanceChart');
        if (!ctx || this.chartInstance) return;
        
        const completedPercentage = parseFloat(ctx.dataset.completed || 0);
        const pendingPercentage = parseFloat(ctx.dataset.pending || 100);
        
        this.chartInstance = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['Completado', 'Pendiente'],
                datasets: [{
                    data: [completedPercentage, pendingPercentage],
                    backgroundColor: [
                        completedPercentage >= 75 ? '#28a745' : 
                        completedPercentage >= 50 ? '#ffc107' : '#dc3545',
                        '#e9ecef'
                    ],
                    borderWidth: 0,
                    cutout: '70%'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: { enabled: false } // Deshabilitado para mejor rendimiento
                },
                animation: {
                    duration: 0 // Sin animaciones
                }
            }
        });
    }

    // Precargar recursos críticos
    preloadCriticalResources() {
        const criticalImages = [
            '/static/images/mascota/tuki.png'
        ];
        
        criticalImages.forEach(src => {
            const link = document.createElement('link');
            link.rel = 'preload';
            link.as = 'image';
            link.href = src;
            document.head.appendChild(link);
        });
    }

    // Cleanup para prevenir memory leaks
    destroy() {
        if (this.chartInstance) {
            this.chartInstance.destroy();
            this.chartInstance = null;
        }
    }
}

// Inicialización optimizada
function initDashboard() {
    console.log('Iniciando dashboard optimizado (sin modal)');
    window.dashboardOptimized = new DashboardOptimized();
}

// Event listeners optimizados
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initDashboard);
} else {
    initDashboard();
}

// Cleanup al salir
window.addEventListener('beforeunload', () => {
    if (window.dashboardOptimized) {
        window.dashboardOptimized.destroy();
    }
});

// Performance monitoring (opcional para debugging)
if (window.performance && window.performance.mark) {
    window.performance.mark('dashboard-script-loaded');
}
