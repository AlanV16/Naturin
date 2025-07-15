// Script específico para el dashboard
document.addEventListener('DOMContentLoaded', function () {
    console.log('Dashboard script loaded');
    
    // Verificar que Bootstrap está cargado
    if (typeof bootstrap === 'undefined') {
        console.error('Bootstrap no está cargado correctamente');
        return;
    } else {
        console.log('Bootstrap cargado correctamente');
    }
    
    // Inicializar todos los dropdowns de Bootstrap
    const dropdowns = document.querySelectorAll('.dropdown-toggle');
    console.log('Dropdowns encontrados:', dropdowns.length);
    
    dropdowns.forEach((dropdown, index) => {
        console.log(`Inicializando dropdown ${index + 1}:`, dropdown.id);
        
        // Verificar si el dropdown ya está inicializado
        if (!dropdown.hasAttribute('data-bs-toggle-initialized')) {
            try {
                // Inicializar el dropdown manualmente
                const dropdownInstance = new bootstrap.Dropdown(dropdown);
                dropdown.setAttribute('data-bs-toggle-initialized', 'true');
                console.log(`Dropdown ${dropdown.id} inicializado correctamente`);
                
                // Agregar eventos para debug
                dropdown.addEventListener('click', function(e) {
                    console.log('Dropdown clicked:', this.id);
                    console.log('Event prevented:', e.defaultPrevented);
                });
                
                // Agregar eventos de Bootstrap
                dropdown.addEventListener('show.bs.dropdown', function () {
                    console.log(`Dropdown ${this.id} mostrándose`);
                });
                
                dropdown.addEventListener('shown.bs.dropdown', function () {
                    console.log(`Dropdown ${this.id} mostrado`);
                });
                
                dropdown.addEventListener('hide.bs.dropdown', function () {
                    console.log(`Dropdown ${this.id} ocultándose`);
                });
                
            } catch (error) {
                console.error(`Error inicializando dropdown ${dropdown.id}:`, error);
            }
        }
    });
    
    // Función específica para el dropdown del usuario
    const userDropdown = document.getElementById('userDropdown');
    if (userDropdown) {
        console.log('Dropdown del usuario encontrado');
        
        // Verificar que el dropdown tenga el menú asociado
        const dropdownMenu = userDropdown.nextElementSibling;
        if (dropdownMenu && dropdownMenu.classList.contains('dropdown-menu')) {
            console.log('Menú del dropdown del usuario encontrado');
        } else {
            console.error('Menú del dropdown del usuario no encontrado');
        }
        
        // Agregar evento de click personalizado como respaldo
        userDropdown.addEventListener('click', function(e) {
            console.log('Click personalizado en dropdown del usuario');
            
            // Solo actuar si Bootstrap no está manejando el evento
            setTimeout(() => {
                const dropdownMenu = this.nextElementSibling;
                if (dropdownMenu && !dropdownMenu.classList.contains('show')) {
                    console.log('Activando dropdown manualmente');
                    
                    // Cerrar otros dropdowns
                    document.querySelectorAll('.dropdown-menu.show').forEach(menu => {
                        menu.classList.remove('show');
                    });
                    
                    // Mostrar este dropdown
                    dropdownMenu.classList.add('show');
                    this.setAttribute('aria-expanded', 'true');
                }
            }, 50);
        });
    } else {
        console.error('Dropdown del usuario no encontrado');
    }
    
    // Función para cerrar todos los dropdowns al hacer click fuera
    document.addEventListener('click', function(event) {
        console.log('Click en documento');
        
        if (!event.target.closest('.dropdown')) {
            console.log('Click fuera de dropdown - cerrando todos');
            const openDropdowns = document.querySelectorAll('.dropdown-menu.show');
            openDropdowns.forEach(dropdown => {
                dropdown.classList.remove('show');
                const toggle = dropdown.previousElementSibling;
                if (toggle) {
                    toggle.setAttribute('aria-expanded', 'false');
                }
            });
        }
    });
    
    // Verificar elementos específicos
    const notificationDropdown = document.querySelector('.dropdown .dropdown-toggle[data-bs-toggle="dropdown"]');
    if (notificationDropdown) {
        console.log('Dropdown de notificaciones encontrado');
    }
    
    // Debugging adicional
    console.log('Elementos con clase dropdown:', document.querySelectorAll('.dropdown').length);
    console.log('Elementos con clase dropdown-menu:', document.querySelectorAll('.dropdown-menu').length);
    console.log('Elementos con data-bs-toggle:', document.querySelectorAll('[data-bs-toggle="dropdown"]').length);
});
