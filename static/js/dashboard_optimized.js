/**
 * Dashboard Optimizado - JavaScript
 * Versión optimizada para mejor rendimiento
 */

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

    // Configurar modal correctamente
    setupModal() {
        // Verificar que Bootstrap Modal esté disponible
        if (typeof bootstrap === 'undefined' || typeof bootstrap.Modal === 'undefined') {
            console.error('Bootstrap Modal no está disponible');
            return;
        }

        // Asegurar que el modal se inicialice correctamente
        const modal = document.getElementById('joinClassModal');
        if (modal) {
            // Inicializar el modal manualmente si es necesario
            const bsModal = new bootstrap.Modal(modal, {
                backdrop: true,
                keyboard: true,
                focus: true
            });

            // Agregar event listeners para debug
            modal.addEventListener('show.bs.modal', function (event) {
                console.log('Modal showing');
                document.body.classList.add('modal-open');
            });
            
            modal.addEventListener('shown.bs.modal', function (event) {
                console.log('Modal shown');
                // Enfocar el input del código del curso
                const courseCodeInput = modal.querySelector('#courseCode');
                if (courseCodeInput) {
                    setTimeout(() => courseCodeInput.focus(), 100);
                }
            });
            
            modal.addEventListener('hide.bs.modal', function (event) {
                console.log('Modal hiding');
            });

            modal.addEventListener('hidden.bs.modal', function (event) {
                console.log('Modal hidden');
                document.body.classList.remove('modal-open');
            });
        }

        // Verificar que todos los botones que abren el modal funcionen
        const modalTriggers = document.querySelectorAll('[data-bs-target="#joinClassModal"]');
        modalTriggers.forEach(trigger => {
            trigger.addEventListener('click', function(e) {
                console.log('Modal trigger clicked');
                // Asegurar que el evento no se propague
                e.stopPropagation();
                
                // Fallback manual si Bootstrap no funciona
                if (!modal.classList.contains('show')) {
                    setTimeout(() => {
                        if (!modal.classList.contains('show')) {
                            console.log('Activando modal manualmente');
                            modal.style.display = 'block';
                            modal.classList.add('show');
                            document.body.classList.add('modal-open');
                            
                            // Crear backdrop manualmente
                            const backdrop = document.createElement('div');
                            backdrop.className = 'modal-backdrop fade show';
                            backdrop.id = 'manual-backdrop';
                            document.body.appendChild(backdrop);
                            
                            // Cerrar modal al hacer click en backdrop
                            backdrop.addEventListener('click', () => {
                                modal.style.display = 'none';
                                modal.classList.remove('show');
                                document.body.classList.remove('modal-open');
                                backdrop.remove();
                            });
                        }
                    }, 100);
                }
            });
        });
    }

    // Lazy loading para el gráfico de rendimiento
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

    // Cargar Chart.js de forma diferida
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

    // Crear gráfico optimizado sin animaciones costosas
    createPerformanceChart() {
        const ctx = document.getElementById('performanceChart');
        if (!ctx || this.chartInstance) return;
        
        // Obtener datos del template
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
    // Verificar que Bootstrap esté disponible
    if (typeof bootstrap === 'undefined') {
        console.error('Bootstrap no está cargado');
        return;
    }
    
    console.log('Bootstrap disponible, iniciando dashboard');
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
