// ============================================================================
// FUNCIONES AJAX PARA ACTUALIZACIÓN PARCIAL DE DASHBOARDS
// ============================================================================

// Función para obtener el token CSRF
function getCsrfToken() {
    const csrfInput = document.querySelector('[name=csrfmiddlewaretoken]');
    return csrfInput ? csrfInput.value : '';
}

// Función para mostrar alertas
function showAlert(message, type = 'info') {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type === 'error' ? 'danger' : type} alert-dismissible fade show position-fixed top-0 start-50 translate-middle-x mt-3`;
    alertDiv.style.zIndex = '9999';
    alertDiv.style.marginTop = '60px';
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    
    document.body.appendChild(alertDiv);
    
    // Autocerrar después de 5 segundos
    setTimeout(() => {
        alertDiv.remove();
    }, 5000);
}

// ============================================================================
// FUNCIONES PARA DOCENTE
// ============================================================================

function reloadTeacherCourses() {
    fetch('/accounts/ajax/teacher/courses/', {
        headers: {
            'X-CSRFToken': getCsrfToken(),
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.html) {
            const section = document.getElementById('teacherCoursesSection');
            if (section) {
                section.innerHTML = data.html;
            }
        } else if (data.error) {
            console.error('Error al recargar cursos:', data.error);
        }
    })
    .catch(error => {
        console.error('Error al recargar cursos:', error);
    });
}

function reloadTeacherPendingSubmissions() {
    fetch('/accounts/ajax/teacher/pending-submissions/', {
        headers: {
            'X-CSRFToken': getCsrfToken(),
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.html) {
            const section = document.getElementById('teacherPendingSection');
            if (section) {
                section.innerHTML = data.html;
            }
        } else if (data.error) {
            console.error('Error al recargar tareas pendientes:', data.error);
        }
    })
    .catch(error => {
        console.error('Error al recargar tareas pendientes:', error);
    });
}

// ============================================================================
// FUNCIONES PARA ESTUDIANTE
// ============================================================================

function reloadStudentCourses() {
    fetch('/accounts/ajax/student/courses/', {
        headers: {
            'X-CSRFToken': getCsrfToken(),
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.html) {
            const section = document.getElementById('studentCoursesSection');
            if (section) {
                section.innerHTML = data.html;
            }
        } else if (data.error) {
            console.error('Error al recargar cursos:', data.error);
        }
    })
    .catch(error => {
        console.error('Error al recargar cursos:', error);
    });
}

function reloadStudentAchievements() {
    fetch('/accounts/ajax/student/achievements/', {
        headers: {
            'X-CSRFToken': getCsrfToken(),
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.html) {
            const section = document.getElementById('studentAchievementsSection');
            if (section) {
                section.innerHTML = data.html;
            }
        } else if (data.error) {
            console.error('Error al recargar logros:', data.error);
        }
    })
    .catch(error => {
        console.error('Error al recargar logros:', error);
    });
}

// ============================================================================
// FUNCIONES PARA PADRE DE FAMILIA
// ============================================================================

function reloadParentChildren() {
    fetch('/accounts/ajax/parent/children/', {
        headers: {
            'X-CSRFToken': getCsrfToken(),
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.html) {
            const section = document.getElementById('parentChildrenSection');
            if (section) {
                section.innerHTML = data.html;
            }
        } else if (data.error) {
            console.error('Error al recargar hijos:', data.error);
        }
    })
    .catch(error => {
        console.error('Error al recargar hijos:', error);
    });
}

// ============================================================================
// FUNCIONES PARA ADMINISTRADOR
// ============================================================================

function reloadAdminUsers() {
    fetch('/accounts/ajax/admin/users/', {
        headers: {
            'X-CSRFToken': getCsrfToken(),
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.html) {
            const section = document.getElementById('adminUsersSection');
            if (section) {
                section.innerHTML = data.html;
            }
        } else if (data.error) {
            console.error('Error al recargar usuarios:', data.error);
        }
    })
    .catch(error => {
        console.error('Error al recargar usuarios:', error);
    });
}

// ============================================================================
// FUNCIONES GENÉRICAS PARA ACTUALIZACIÓN
// ============================================================================

// Función para actualizar múltiples secciones después de crear/editar algo
function updateDashboardSections(sections = []) {
    sections.forEach(section => {
        switch(section) {
            case 'teacher_courses':
                reloadTeacherCourses();
                break;
            case 'teacher_pending':
                reloadTeacherPendingSubmissions();
                break;
            case 'student_courses':
                reloadStudentCourses();
                break;
            case 'student_achievements':
                reloadStudentAchievements();
                break;
            case 'parent_children':
                reloadParentChildren();
                break;
            case 'admin_users':
                reloadAdminUsers();
                break;
        }
    });
}

// Función para actualizar estadísticas del dashboard
function updateDashboardStats() {
    // Aquí puedes agregar lógica para actualizar las tarjetas de estadísticas
    // Por ejemplo, recargar contadores de cursos, tareas, etc.
    console.log('Actualizando estadísticas del dashboard...');
}

// ============================================================================
// FUNCIONES ESPECÍFICAS PARA MODALES Y FORMULARIOS
// ============================================================================

// Función para actualizar después de crear un curso
function updateAfterCreateCourse() {
    // Determinar qué tipo de usuario es y actualizar las secciones correspondientes
    const userType = document.body.dataset.userType;
    
    if (userType === '2') { // Docente
        reloadTeacherCourses();
        updateDashboardStats();
    } else if (userType === '1') { // Estudiante
        reloadStudentCourses();
        updateDashboardStats();
    }
    
    showAlert('Curso creado exitosamente', 'success');
}

// Función para actualizar después de crear una tarea
function updateAfterCreateAssignment() {
    reloadTeacherPendingSubmissions();
    updateDashboardStats();
    showAlert('Tarea creada exitosamente', 'success');
}

// Función para actualizar después de unirse a una clase
function updateAfterJoinClass() {
    reloadStudentCourses();
    updateDashboardStats();
    showAlert('Te has unido exitosamente a la clase', 'success');
}

// Función para actualizar después de calificar una tarea
function updateAfterGradeSubmission() {
    reloadTeacherPendingSubmissions();
    updateDashboardStats();
    showAlert('Tarea calificada exitosamente', 'success');
}

// ============================================================================
// FUNCIONES PARA MENSAJERÍA
// ============================================================================

// Función para cargar mensajes de una conversación
function loadConversationMessages(conversationId) {
    fetch(`/accounts/messages/conversation/${conversationId}/`)
        .then(response => response.text())
        .then(html => {
            const chatContent = document.querySelector('.messages-content');
            if (chatContent) {
                chatContent.innerHTML = html;
            }
        })
        .catch(error => {
            console.error('Error al cargar mensajes:', error);
        });
}

// Función para enviar mensaje
function sendMessage(conversationId, message) {
    fetch(`/accounts/messages/conversation/${conversationId}/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCsrfToken(),
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: `message=${encodeURIComponent(message)}`
    })
    .then(response => {
        if (response.ok) {
            // Recargar mensajes
            loadConversationMessages(conversationId);
        }
    })
    .catch(error => {
        console.error('Error al enviar mensaje:', error);
    });
}

// ============================================================================
// INICIALIZACIÓN
// ============================================================================

document.addEventListener('DOMContentLoaded', function() {
    // Configurar listeners para formularios que necesiten actualización AJAX
    console.log('Dashboard AJAX functions loaded');
    
    // Agregar el tipo de usuario al body para identificar qué funciones usar
    const userType = document.querySelector('[data-user-type]');
    if (userType) {
        document.body.dataset.userType = userType.dataset.userType;
    }
    
    // Auto-actualización cada 30 segundos (opcional)
    // setInterval(() => {
    //     updateDashboardStats();
    // }, 30000);
}); 