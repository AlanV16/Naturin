// Dashboard de Padres - Funcionalidad AJAX Completa
// NatureIn - Sistema Educativo Gamificado

// Variables globales
let currentContactId = null;
let currentSection = 'dashboard';

// Función para obtener el token CSRF
function getCSRFToken() {
    return document.querySelector('[name=csrfmiddlewaretoken]').value;
}

// Función para mostrar alertas profesionales
function showAlert(message, type = 'info') {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type === 'error' ? 'danger' : type} alert-dismissible fade show position-fixed`;
    alertDiv.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
    alertDiv.innerHTML = `
        <i class="bi bi-${type === 'success' ? 'check-circle' : type === 'error' ? 'exclamation-triangle' : 'info-circle'} me-2"></i>
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    document.body.appendChild(alertDiv);
    
    // Auto-remove después de 4 segundos
    setTimeout(() => {
        if (alertDiv.parentNode) {
            alertDiv.remove();
        }
    }, 4000);
}

// Función AJAX para registrar un hijo
function addChildAJAX(formData, onSuccess) {
    fetch('/users/ajax/add-child/', {
        method: 'POST',
        body: formData,
        headers: {
            'X-CSRFToken': getCSRFToken(),
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            if (typeof onSuccess === 'function') {
                onSuccess(data);
            }
        } else {
            showAlert(data.error || 'Error al registrar hijo', 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showAlert('Error al registrar hijo', 'error');
    });
}

// ============================================================================
// SECCIÓN: HIJOS
// ============================================================================

function refreshChildrenList() {
    fetch('/users/ajax/children-list/')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                document.getElementById('parentChildrenSection').innerHTML = data.html;
                updateChildrenCount();
            } else {
                showAlert(data.error, 'error');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showAlert('Error al cargar la lista de hijos', 'error');
        });
}

function deleteChild(childId) {
    if (!confirm('¿Estás seguro de que quieres eliminar este hijo?')) {
        return;
    }
    
    const formData = new FormData();
    formData.append('child_id', childId);
    
    fetch('/users/ajax/delete-child/', {
        method: 'POST',
        body: formData,
        headers: {
            'X-CSRFToken': getCSRFToken(),
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showAlert(data.message, 'success');
            refreshChildrenList();
        } else {
            showAlert(data.error, 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showAlert('Error al eliminar hijo', 'error');
    });
}

function updateChildrenCount() {
    const childrenCards = document.querySelectorAll('.child-card');
    const countElement = document.querySelector('.stat-number');
    if (countElement) {
        countElement.textContent = childrenCards.length;
    }
    
    // Deshabilitar botón si ya hay 5 hijos
    const addButton = document.querySelector('[data-bs-target="#addChildModal"]');
    if (childrenCards.length >= 5) {
        addButton.disabled = true;
        addButton.innerHTML = '<i class="bi bi-person-plus"></i> Máximo alcanzado';
    } else {
        addButton.disabled = false;
        addButton.innerHTML = '<i class="bi bi-person-plus"></i> Añadir Hijo';
    }
}

// ============================================================================
// SECCIÓN: CHAT
// ============================================================================

function loadChatContacts() {
    fetch('/users/ajax/chat-contacts/')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                document.getElementById('chatContactsContainer').innerHTML = data.html;
            } else {
                showAlert(data.error, 'error');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showAlert('Error al cargar contactos', 'error');
        });
}

// ============================================================================
// BÚSQUEDA DE DOCENTES
// ============================================================================

let searchTimeout = null;

function searchTeachers() {
    const searchInput = document.getElementById('teacherSearchInput');
    const query = searchInput.value.trim();
    
    if (query.length < 2) {
        hideSearchResults();
        return;
    }
    
    // Cancelar búsqueda anterior si existe
    if (searchTimeout) {
        clearTimeout(searchTimeout);
    }
    
    // Búsqueda con debounce (500ms)
    searchTimeout = setTimeout(() => {
        performTeacherSearch(query);
    }, 500);
}

function performTeacherSearch(query) {
    fetch(`/users/ajax/search-teachers/?q=${encodeURIComponent(query)}`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                displaySearchResults(data.teachers);
            } else {
                showAlert(data.error, 'error');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showAlert('Error al buscar docentes', 'error');
        });
}

function displaySearchResults(teachers) {
    const resultsContainer = document.getElementById('searchResults');
    
    if (teachers.length === 0) {
        resultsContainer.innerHTML = `
            <div class="text-center py-3">
                <i class="bi bi-search text-muted"></i>
                <p class="text-muted mt-2">No se encontraron docentes</p>
            </div>
        `;
    } else {
        let html = '<h6 class="text-muted mb-2">Resultados de búsqueda</h6>';
        
        teachers.forEach(teacher => {
            html += `
                <div class="contact-item search-result" onclick="startChatWithTeacher(${teacher.id})" data-teacher-id="${teacher.id}">
                    <div class="d-flex align-items-center">
                        <div class="contact-avatar me-3">
                            ${teacher.avatar_url ? 
                                `<img src="${teacher.avatar_url}" alt="${teacher.name}" class="rounded-circle" width="40" height="40">` :
                                `<div class="avatar-placeholder rounded-circle d-flex align-items-center justify-content-center" style="width: 40px; height: 40px; background: #e9ecef;">
                                    <i class="bi bi-person text-muted"></i>
                                </div>`
                            }
                        </div>
                        <div class="contact-info">
                            <h6 class="mb-0">${teacher.name}</h6>
                            <small class="text-muted">${teacher.email}</small>
                            ${teacher.courses_count > 0 ? `<br><small class="text-primary">${teacher.courses_count} curso(s)</small>` : ''}
                        </div>
                        <div class="ms-auto">
                            <button class="btn btn-sm btn-outline-primary" onclick="startChatWithTeacher(${teacher.id}); event.stopPropagation();">
                                <i class="bi bi-chat-dots"></i> Chatear
                            </button>
                        </div>
                    </div>
                </div>
            `;
        });
        
        resultsContainer.innerHTML = html;
    }
    
    resultsContainer.style.display = 'block';
}

function hideSearchResults() {
    const resultsContainer = document.getElementById('searchResults');
    resultsContainer.style.display = 'none';
    resultsContainer.innerHTML = '';
}

function startChatWithTeacher(teacherId) {
    // Ocultar resultados de búsqueda
    hideSearchResults();
    
    // Limpiar campo de búsqueda
    document.getElementById('teacherSearchInput').value = '';
    
    // Cargar mensajes con el docente
    loadChatMessages(teacherId);
    
    // Marcar como contacto activo
    document.querySelectorAll('.contact-item').forEach(item => {
        item.classList.remove('active');
    });
    
    // Si el docente no está en la lista de contactos, agregarlo dinámicamente
    const existingContact = document.querySelector(`[data-contact-id="${teacherId}"]`);
    if (!existingContact) {
        addTeacherToContacts(teacherId);
    } else {
        existingContact.classList.add('active');
    }
}

function addTeacherToContacts(teacherId) {
    // Obtener información del docente y agregarlo a la lista de contactos
    fetch(`/users/ajax/teacher-info/${teacherId}/`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const contactsSection = document.querySelector('.contacts-section');
                const contactsList = contactsSection.querySelector('.contact-item:first-child').parentNode;
                
                const newContact = document.createElement('div');
                newContact.className = 'contact-item active';
                newContact.setAttribute('data-contact-id', teacherId);
                newContact.onclick = () => loadChatMessages(teacherId);
                
                newContact.innerHTML = `
                    <div class="d-flex align-items-center">
                        <div class="contact-avatar me-3">
                            ${data.teacher.avatar_url ? 
                                `<img src="${data.teacher.avatar_url}" alt="${data.teacher.name}" class="rounded-circle" width="40" height="40">` :
                                `<div class="avatar-placeholder rounded-circle d-flex align-items-center justify-content-center" style="width: 40px; height: 40px; background: #e9ecef;">
                                    <i class="bi bi-person text-muted"></i>
                                </div>`
                            }
                        </div>
                        <div class="contact-info">
                            <h6 class="mb-0">${data.teacher.name}</h6>
                            <small class="text-muted">${data.teacher.email}</small>
                        </div>
                        <div class="ms-auto">
                            <small class="text-muted">Docente</small>
                        </div>
                    </div>
                `;
                
                contactsList.insertBefore(newContact, contactsList.firstChild);
            }
        })
        .catch(error => {
            console.error('Error:', error);
        });
}

// ============================================================================
// MEJORAS EN LA FUNCIÓN DE CHAT
// ============================================================================

function loadChatMessages(contactId) {
    currentContactId = contactId;
    
    // Actualizar estado activo del contacto
    document.querySelectorAll('.contact-item').forEach(item => {
        item.classList.remove('active');
    });
    document.querySelector(`[data-contact-id="${contactId}"]`).classList.add('active');
    
    // Mostrar indicador de carga
    const messagesContainer = document.getElementById('chatMessagesContainer');
    messagesContainer.innerHTML = `
        <div class="text-center py-4">
            <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">Cargando...</span>
            </div>
            <p class="text-muted mt-2">Cargando mensajes...</p>
        </div>
    `;
    
    fetch(`/users/ajax/chat-messages/${contactId}/`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                messagesContainer.innerHTML = data.html;
                scrollToBottom('chatMessagesContainer');
                
                // Marcar mensajes como leídos
                markMessagesAsRead(contactId);
            } else {
                messagesContainer.innerHTML = `
                    <div class="text-center py-4">
                        <i class="bi bi-exclamation-triangle text-warning" style="font-size: 2rem;"></i>
                        <p class="text-muted mt-2">Error al cargar mensajes</p>
                        <small class="text-muted">${data.error}</small>
                    </div>
                `;
            }
        })
        .catch(error => {
            console.error('Error:', error);
            messagesContainer.innerHTML = `
                <div class="text-center py-4">
                    <i class="bi bi-exclamation-triangle text-danger" style="font-size: 2rem;"></i>
                    <p class="text-muted mt-2">Error de conexión</p>
                    <small class="text-muted">No se pudieron cargar los mensajes</small>
                </div>
            `;
        });
}

function markMessagesAsRead(contactId) {
    fetch(`/users/ajax/mark-messages-read/${contactId}/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCSRFToken(),
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Actualizar contador de mensajes no leídos si existe
            updateUnreadMessagesCount();
        }
    })
    .catch(error => {
        console.error('Error marcando mensajes como leídos:', error);
    });
}

function updateUnreadMessagesCount() {
    // Actualizar contador de mensajes no leídos en el header si existe
    const unreadBadge = document.querySelector('.unread-messages-badge');
    if (unreadBadge) {
        fetch('/users/ajax/unread-messages-count/')
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    if (data.count > 0) {
                        unreadBadge.textContent = data.count;
                        unreadBadge.style.display = 'inline';
                    } else {
                        unreadBadge.style.display = 'none';
                    }
                }
            })
            .catch(error => {
                console.error('Error actualizando contador:', error);
            });
    }
}

function sendMessage() {
    if (!currentContactId) {
        showAlert('Selecciona un contacto primero', 'error');
        return;
    }
    
    const messageInput = document.getElementById('messageInput');
    const text = messageInput.value.trim();
    
    if (!text) {
        showAlert('Escribe un mensaje', 'error');
        return;
    }
    
    fetch('/users/ajax/send-message/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCSRFToken(),
        },
        body: JSON.stringify({
            contact_id: currentContactId,
            text: text
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            messageInput.value = '';
            loadChatMessages(currentContactId);
        } else {
            showAlert(data.error, 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showAlert('Error al enviar mensaje', 'error');
    });
}

function scrollToBottom(containerId) {
    const container = document.getElementById(containerId);
    if (container) {
        container.scrollTop = container.scrollHeight;
    }
}

// ============================================================================
// SECCIÓN: EVENTOS
// ============================================================================

function refreshEventsList() {
    fetch('/users/ajax/upcoming-events/')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                document.getElementById('eventsSection').innerHTML = data.html;
            } else {
                showAlert(data.error, 'error');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showAlert('Error al cargar eventos', 'error');
        });
}

// ============================================================================
// SECCIÓN: SUGERENCIAS
// ============================================================================

function sendSuggestion() {
    const form = document.getElementById('suggestionForm');
    const formData = new FormData(form);
    
    fetch('/users/ajax/send-suggestion/', {
        method: 'POST',
        body: formData,
        headers: {
            'X-CSRFToken': getCSRFToken(),
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showAlert(data.message, 'success');
            // Cerrar modal
            const modal = bootstrap.Modal.getInstance(document.getElementById('suggestionModal'));
            modal.hide();
            form.reset();
            // Refrescar lista de sugerencias
            refreshSuggestionsList();
        } else {
            showAlert(data.error, 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showAlert('Error al enviar sugerencia', 'error');
    });
}

function refreshSuggestionsList() {
    fetch('/users/ajax/suggestions-list/')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                document.getElementById('suggestionsSection').innerHTML = data.html;
            } else {
                showAlert(data.error, 'error');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showAlert('Error al cargar sugerencias', 'error');
        });
}

// ============================================================================
// SECCIÓN: RECURSOS EDUCATIVOS
// ============================================================================

function refreshEducationalResources() {
    fetch('/users/ajax/educational-resources/')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                document.getElementById('educationalContentSection').innerHTML = data.html;
            } else {
                showAlert(data.error, 'error');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showAlert('Error al cargar recursos educativos', 'error');
        });
}

// ============================================================================
// NAVEGACIÓN ENTRE SECCIONES
// ============================================================================

function showSection(sectionId) {
    // Ocultar todas las secciones
    document.querySelectorAll('.section-content').forEach(section => {
        section.style.display = 'none';
    });
    
    // Mostrar la sección seleccionada
    const targetSection = document.getElementById(sectionId);
    if (targetSection) {
        targetSection.style.display = 'block';
    }
    
    // Actualizar estado activo del sidebar
    document.querySelectorAll('.sidebar-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    event.target.closest('.sidebar-btn').classList.add('active');
    
    // Cargar datos específicos de la sección
    currentSection = sectionId;
    loadSectionData(sectionId);
}

function loadSectionData(sectionId) {
    switch(sectionId) {
        case 'childrenSection':
            refreshChildrenList();
            break;
        case 'chatSection':
            loadChatContacts();
            break;
        case 'calendarSection':
            refreshEventsList();
            break;
        case 'suggestionsSection':
            refreshSuggestionsList();
            break;
        case 'educationalContentSection':
            refreshEducationalResources();
            break;
    }
}

// Funciones específicas para cada sección
function showChildrenSection() {
    showSection('childrenSection');
}

function showChatSection() {
    showSection('chatSection');
}

function showCalendarSection() {
    showSection('calendarSection');
}

function showSuggestionsSection() {
    showSection('suggestionsSection');
}

function showEducationalContentSection() {
    showSection('educationalContentSection');
}

function showSuggestionModal() {
    const modal = new bootstrap.Modal(document.getElementById('suggestionModal'));
    modal.show();
}

// ============================================================================
// VALIDACIÓN DE FORMULARIOS
// ============================================================================

function validateAddChildForm() {
    const form = document.getElementById('addChildForm');
    if (!form.checkValidity()) {
        form.classList.add('was-validated');
        return false;
    }
    return true;
}

function validateSuggestionForm() {
    const form = document.getElementById('suggestionForm');
    if (!form.checkValidity()) {
        form.classList.add('was-validated');
        return false;
    }
    return true;
}

// ============================================================================
// FUNCIONALIDADES ADICIONALES DEL DASHBOARD
// ============================================================================

function updateDashboardStats() {
    fetch('/users/ajax/dashboard-stats/')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Actualizar contadores en tiempo real
                document.getElementById('childrenCount').textContent = data.stats.children_count;
                document.getElementById('coursesCount').textContent = data.stats.courses_count;
                document.getElementById('overdueAssignments').textContent = data.stats.overdue_assignments;
                document.getElementById('upcomingEvents').textContent = data.stats.upcoming_events;
            }
        })
        .catch(error => {
            console.error('Error actualizando estadísticas:', error);
        });
}

function refreshRecentActivities() {
    fetch('/users/ajax/recent-activities/')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                document.getElementById('recentActivitiesSection').innerHTML = data.html;
            }
        })
        .catch(error => {
            console.error('Error cargando actividades:', error);
        });
}

function showChildDetails(childId) {
    // Mostrar modal con detalles del hijo
    const modal = new bootstrap.Modal(document.getElementById('childDetailsModal'));
    
    // Cargar información del hijo
    fetch(`/users/ajax/child-progress/${childId}/`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                displayChildDetails(data.child);
                modal.show();
            } else {
                showAlert(data.error, 'error');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showAlert('Error al cargar detalles del hijo', 'error');
        });
}

function displayChildDetails(childData) {
    const modalBody = document.getElementById('childDetailsModalBody');
    
    let html = `
        <div class="child-details">
            <h5 class="mb-3">${childData.name} - Grado ${childData.grade}</h5>
            <div class="overall-progress mb-4">
                <h6>Progreso General</h6>
                <div class="progress" style="height: 20px;">
                    <div class="progress-bar bg-success" role="progressbar" style="width: ${childData.overall_progress}%">
                        ${childData.overall_progress}%
                    </div>
                </div>
            </div>
            <div class="courses-progress">
                <h6>Cursos</h6>
                <div class="row">
    `;
    
    childData.courses.forEach(course => {
        html += `
            <div class="col-md-6 mb-3">
                <div class="course-card">
                    <h6 class="fw-bold">${course.course_name}</h6>
                    <small class="text-muted">Prof. ${course.teacher}</small>
                    <div class="progress mt-2" style="height: 8px;">
                        <div class="progress-bar bg-primary" role="progressbar" style="width: ${course.progress}%"></div>
                    </div>
                    <small class="text-muted">${course.completed_assignments}/${course.assignments_count} tareas completadas</small>
                </div>
            </div>
        `;
    });
    
    html += `
                </div>
            </div>
        </div>
    `;
    
    modalBody.innerHTML = html;
}

function loadChildAssignments(childId) {
    fetch(`/users/ajax/child-assignments/${childId}/`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                document.getElementById('childAssignmentsSection').innerHTML = data.html;
            } else {
                showAlert(data.error, 'error');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showAlert('Error al cargar tareas', 'error');
        });
}

function loadChildGrades(childId) {
    fetch(`/users/ajax/child-grades/${childId}/`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                document.getElementById('childGradesSection').innerHTML = data.html;
            } else {
                showAlert(data.error, 'error');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showAlert('Error al cargar calificaciones', 'error');
        });
}

// ============================================================================
// FUNCIONALIDADES DE PERFIL
// ============================================================================

function showProfileModal() {
    const modal = new bootstrap.Modal(document.getElementById('profileModal'));
    modal.show();
}

function updateProfile() {
    const form = document.getElementById('profileForm');
    const formData = new FormData(form);
    
    fetch('/users/ajax/update-profile/', {
        method: 'POST',
        body: formData,
        headers: {
            'X-CSRFToken': getCSRFToken(),
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showAlert(data.message, 'success');
            const modal = bootstrap.Modal.getInstance(document.getElementById('profileModal'));
            modal.hide();
        } else {
            showAlert(data.error, 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showAlert('Error al actualizar perfil', 'error');
    });
}

// ============================================================================
// FUNCIONALIDADES DE CALENDARIO
// ============================================================================

function loadCalendarEvents() {
    fetch('/users/ajax/calendar-events/')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                displayCalendarEvents(data.events);
            } else {
                showAlert(data.error, 'error');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showAlert('Error al cargar eventos del calendario', 'error');
        });
}

function displayCalendarEvents(events) {
    const calendarContainer = document.getElementById('calendarContainer');
    
    if (events.length === 0) {
        calendarContainer.innerHTML = `
            <div class="text-center py-4">
                <i class="bi bi-calendar-x text-muted" style="font-size: 3rem;"></i>
                <p class="text-muted mt-2">No hay eventos en el calendario</p>
            </div>
        `;
        return;
    }
    
    let html = '<div class="calendar-events">';
    
    events.forEach(event => {
        const eventDate = new Date(event.start_date);
        const isToday = eventDate.toDateString() === new Date().toDateString();
        const isPast = eventDate < new Date();
        
        html += `
            <div class="calendar-event ${isToday ? 'today' : ''} ${isPast ? 'past' : ''}">
                <div class="event-date">
                    <div class="day">${eventDate.getDate()}</div>
                    <div class="month">${eventDate.toLocaleDateString('es-ES', {month: 'short'})}</div>
                </div>
                <div class="event-info">
                    <h6 class="mb-1">${event.title}</h6>
                    <small class="text-muted">${event.student_name} - ${event.course_name}</small>
                    <div class="event-time">
                        <small class="text-muted">${eventDate.toLocaleTimeString('es-ES', {hour: '2-digit', minute: '2-digit'})}</small>
                    </div>
                </div>
            </div>
        `;
    });
    
    html += '</div>';
    calendarContainer.innerHTML = html;
}

// ============================================================================
// FUNCIONALIDADES DE NOTIFICACIONES
// ============================================================================

function loadNotifications() {
    fetch('/users/ajax/notifications/')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                updateNotificationsBadge(data.count);
                displayNotifications(data.notifications);
            }
        })
        .catch(error => {
            console.error('Error cargando notificaciones:', error);
        });
}

function updateNotificationsBadge(count) {
    const badge = document.querySelector('.notifications-badge');
    if (badge) {
        if (count > 0) {
            badge.textContent = count;
            badge.style.display = 'inline';
        } else {
            badge.style.display = 'none';
        }
    }
}

function displayNotifications(notifications) {
    const container = document.getElementById('notificationsContainer');
    if (!container) return;
    
    if (notifications.length === 0) {
        container.innerHTML = `
            <div class="text-center py-3">
                <i class="bi bi-bell text-muted"></i>
                <p class="text-muted mt-2">No hay notificaciones</p>
            </div>
        `;
        return;
    }
    
    let html = '';
    notifications.forEach(notification => {
        html += `
            <div class="notification-item ${notification.is_read ? 'read' : 'unread'}">
                <div class="notification-icon">
                    <i class="bi bi-${getNotificationIcon(notification.type)}"></i>
                </div>
                <div class="notification-content">
                    <h6 class="mb-1">${notification.title}</h6>
                    <p class="mb-1">${notification.message}</p>
                    <small class="text-muted">${notification.created_at}</small>
                </div>
            </div>
        `;
    });
    
    container.innerHTML = html;
}

function getNotificationIcon(type) {
    const icons = {
        'assignment': 'file-earmark-text',
        'grade': 'star-fill',
        'announcement': 'megaphone',
        'achievement': 'trophy',
        'reminder': 'clock'
    };
    return icons[type] || 'bell';
}

// ============================================================================
// FUNCIONALIDADES DE EXPORTACIÓN
// ============================================================================

function exportChildReport(childId) {
    fetch(`/users/ajax/export-child-report/${childId}/`)
        .then(response => response.blob())
        .then(blob => {
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `reporte_hijo_${childId}.pdf`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
        })
        .catch(error => {
            console.error('Error:', error);
            showAlert('Error al exportar reporte', 'error');
        });
}

// ============================================================================
// INICIALIZACIÓN COMPLETA DEL DASHBOARD
// ============================================================================

document.addEventListener('DOMContentLoaded', function() {
    // Formulario de añadir hijo
    const addChildForm = document.getElementById('addChildForm');
    if (addChildForm) {
        addChildForm.addEventListener('submit', function(e) {
            e.preventDefault();
            if (!validateAddChildForm()) {
                return;
            }
            
            // Mostrar loading
            const submitBtn = addChildForm.querySelector('button[type="submit"]');
            const originalText = submitBtn.innerHTML;
            submitBtn.innerHTML = '<i class="bi bi-hourglass-split me-2"></i>Guardando...';
            submitBtn.disabled = true;
            
            // Preparar datos
            const formData = new FormData(addChildForm);
            
            // Llamada AJAX
            addChildAJAX(formData, (data) => {
                showAlert(data.message, 'success');
                const modal = bootstrap.Modal.getInstance(document.getElementById('addChildModal'));
                modal.hide();
                addChildForm.reset();
                addChildForm.classList.remove('was-validated');
                refreshChildrenList();
            });
        });
    }
    
    // Formulario de sugerencias
    const suggestionForm = document.getElementById('suggestionForm');
    if (suggestionForm) {
        suggestionForm.addEventListener('submit', function(e) {
            e.preventDefault();
            if (!validateSuggestionForm()) {
                return;
            }
            sendSuggestion();
        });
    }
    
    // Envío de mensajes con Enter
    const messageInput = document.getElementById('messageInput');
    if (messageInput) {
        messageInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            }
        });
    }
    
    // Auto-refresh cada 30 segundos para datos dinámicos
    setInterval(() => {
        if (currentSection === 'calendarSection') {
            refreshEventsList();
        }
    }, 30000);
    
    // Cargar datos iniciales
    refreshChildrenList();
    
    // Evento para búsqueda de docentes
    const teacherSearchInput = document.getElementById('teacherSearchInput');
    if (teacherSearchInput) {
        teacherSearchInput.addEventListener('input', searchTeachers);
        teacherSearchInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                performTeacherSearch(this.value.trim());
            }
        });
        
        // Ocultar resultados al hacer clic fuera
        document.addEventListener('click', function(e) {
            const searchContainer = document.getElementById('searchResults');
            const searchInput = document.getElementById('teacherSearchInput');
            
            if (!searchContainer.contains(e.target) && !searchInput.contains(e.target)) {
                hideSearchResults();
            }
        });
    }
    
    // Auto-refresh de mensajes cada 30 segundos si hay una conversación activa
    setInterval(() => {
        if (currentContactId && currentSection === 'chatSection') {
            loadChatMessages(currentContactId);
        }
    }, 30000);
    
    // Inicializar todas las funcionalidades
    updateDashboardStats();
    refreshRecentActivities();
    loadNotifications();
    
    // Auto-refresh cada 5 minutos
    setInterval(() => {
        updateDashboardStats();
        refreshRecentActivities();
        loadNotifications();
    }, 300000); // 5 minutos
    
    // Eventos adicionales
    setupEventListeners();
});

function setupEventListeners() {
    // Eventos para botones de acción rápida
    document.querySelectorAll('.quick-action-card').forEach(card => {
        card.addEventListener('click', function() {
            const action = this.getAttribute('data-action');
            if (action) {
                executeQuickAction(action);
            }
        });
    });
    
    // Eventos para tarjetas de hijos
    document.querySelectorAll('.child-card').forEach(card => {
        card.addEventListener('click', function() {
            const childId = this.getAttribute('data-child-id');
            if (childId) {
                showChildDetails(childId);
            }
        });
    });
}

function executeQuickAction(action) {
    switch(action) {
        case 'contact_teacher':
            showChatSection();
            break;
        case 'view_calendar':
            showCalendarSection();
            break;
        case 'send_suggestion':
            showSuggestionModal();
            break;
        case 'view_resources':
            showEducationalContentSection();
            break;
        default:
            console.log('Acción no implementada:', action);
    }
}

// Exportar funciones para uso global
window.dashboardParent = {
    refreshChildrenList,
    deleteChild,
    loadChatContacts,
    loadChatMessages,
    sendMessage,
    refreshEventsList,
    sendSuggestion,
    refreshSuggestionsList,
    refreshEducationalResources,
    showSection,
    showAlert,
    updateStats,
    updateDashboardStats,
    refreshRecentActivities,
    showChildDetails,
    loadChildAssignments,
    loadChildGrades,
    showProfileModal,
    updateProfile,
    loadCalendarEvents,
    loadNotifications,
    exportChildReport,
    executeQuickAction
};
