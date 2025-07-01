console.log('🔔 Script de notificaciones cargado');

document.addEventListener('DOMContentLoaded', function() {
    console.log('🔔 DOM cargado, inicializando notificaciones');
    
    const notificationDropdown = document.getElementById('notificationDropdown');
    const notificationsContainer = document.getElementById('notifications-container');
    const notificationBadge = document.getElementById('notification-badge');
    
    console.log('🔔 Elementos encontrados:', {
        dropdown: !!notificationDropdown,
        container: !!notificationsContainer,
        badge: !!notificationBadge
    });
    
    if (!notificationDropdown || !notificationsContainer || !notificationBadge) {
        console.error('❌ Elementos de notificaciones no encontrados');
        return;
    }
    
    // Interceptar el clic en la campana
    notificationDropdown.addEventListener('click', function(e) {
        e.preventDefault();
        // Cargar notificaciones antes de mostrar el dropdown
        loadNotifications().then(() => {
            // Mostrar el dropdown manualmente usando Bootstrap
            const dropdown = bootstrap.Dropdown.getOrCreateInstance(notificationDropdown);
            dropdown.show();
            // Actualizar el contador
            loadNotificationCount();
        });
    });
    
    // Cierre automático al hacer clic fuera
    document.addEventListener('click', function(e) {
        const dropdown = bootstrap.Dropdown.getOrCreateInstance(notificationDropdown);
        const menu = notificationDropdown.nextElementSibling;
        if (menu && menu.classList.contains('show') && !notificationDropdown.contains(e.target) && !menu.contains(e.target)) {
            dropdown.hide();
        }
    });
    
    async function loadNotifications() {
        console.log('🔔 Cargando notificaciones...');
        const url = notificationDropdown.getAttribute('data-url-ajax') || '/gamification/notifications/ajax/';
        notificationsContainer.innerHTML = `<span class="text-center text-muted py-3 d-block"><i class="bi bi-hourglass-split"></i> Cargando...</span>`;
        try {
            const response = await fetch(url, {
                method: 'GET',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                }
            });
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const data = await response.json();
            const notifications = data.notifications;
            if (notifications.length === 0) {
                notificationsContainer.innerHTML = `
                    <span class="text-center text-muted py-3 d-block">
                        <i class="bi bi-bell-slash"></i><br>
                        No tienes notificaciones
                    </span>
                `;
            } else {
                let notificationsHtml = '<ul class="list-unstyled mb-0">';
                notifications.forEach(notification => {
                    notificationsHtml += `
                        <li class="dropdown-item ${!notification.is_read ? 'bg-light' : ''}">
                            <div class="d-flex justify-content-between align-items-start">
                                <div class="flex-grow-1">
                                    <div class="d-flex align-items-center mb-1">
                                        <strong class="me-2">${notification.title}</strong>
                                        ${!notification.is_read ? '<span class="badge bg-primary">Nueva</span>' : ''}
                                    </div>
                                    <p class="mb-1 small">${notification.message}</p>
                                    <small class="text-muted">
                                        <i class="bi bi-clock"></i> ${notification.created_at}
                                        <span class="ms-2">
                                            <i class="bi bi-tag"></i> ${notification.notification_type}
                                        </span>
                                    </small>
                                </div>
                            </div>
                        </li>
                    `;
                });
                notificationsHtml += '</ul>';
                notificationsContainer.innerHTML = notificationsHtml;
            }
        } catch (error) {
            console.error('❌ Error cargando notificaciones:', error);
            notificationsContainer.innerHTML = `
                <span class="text-center text-muted py-3 d-block">
                    <i class="bi bi-exclamation-triangle"></i><br>
                    Error al cargar notificaciones<br>
                    <small>${error.message}</small>
                </span>
            `;
        }
    }
    
    function loadNotificationCount() {
        console.log('🔔 Cargando conteo de notificaciones...');
        const url = notificationDropdown.getAttribute('data-url-count') || '/gamification/notifications/count/';
        fetch(url, {
            method: 'GET',
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
            }
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.unread_count > 0) {
                notificationBadge.textContent = data.unread_count;
                notificationBadge.style.display = 'inline';
            } else {
                notificationBadge.style.display = 'none';
            }
        })
        .catch(error => {
            console.error('❌ Error cargando conteo de notificaciones:', error);
            notificationBadge.style.display = 'none';
        });
    }
    // Cargar conteo inicial
    loadNotificationCount();
    setInterval(loadNotificationCount, 30000);
}); 