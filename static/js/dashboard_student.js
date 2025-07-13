// JS específico para dashboard de estudiante
// Puedes agregar aquí funciones propias del dashboard_student

// Ejemplo: mostrar/ocultar formulario de unirse a clase
function showJoinClassForm() {
    const card = document.getElementById('joinClassCard');
    card.style.display = 'block';
    card.style.animation = 'fadeIn 0.3s ease';
    setTimeout(() => {
        document.getElementById('courseCode').focus();
        card.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }, 100);
}

function hideJoinClassForm() {
    const card = document.getElementById('joinClassCard');
    card.style.animation = 'fadeOut 0.3s ease';
    setTimeout(() => {
        card.style.display = 'none';
    }, 300);
}

// Función para unirse a clase vía AJAX
function joinClassAJAX(event) {
    event.preventDefault();
    
    const form = event.target;
    const formData = new FormData(form);
    const submitButton = form.querySelector('button[type="submit"]');
    const originalText = submitButton.innerHTML;
    
    // Cambiar texto del botón
    submitButton.innerHTML = '<i class="bi bi-hourglass-split me-2"></i>Uniéndose...';
    submitButton.disabled = true;
    
    fetch('/accounts/api/join-class/', {
        method: 'POST',
        body: formData,
        headers: {
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Mostrar mensaje de éxito
            showAlert('¡Te has unido a la clase exitosamente!', 'success');
            
            // Ocultar formulario
            hideJoinClassForm();
            
            // Actualizar sección de cursos
            updateStudentCoursesSection();
            
            // Redirigir a la clase después de un breve delay
            setTimeout(() => {
                if (data.redirect_url) {
                    window.location.href = data.redirect_url;
                } else {
                    window.location.reload();
                }
            }, 1500);
            
        } else {
            showAlert(data.error || 'Error al unirse a la clase', 'error');
            submitButton.innerHTML = originalText;
            submitButton.disabled = false;
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showAlert('Error al unirse a la clase', 'error');
        submitButton.innerHTML = originalText;
        submitButton.disabled = false;
    });
}

// Función para mostrar alertas
function showAlert(message, type) {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type === 'error' ? 'danger' : type} alert-dismissible fade show position-fixed top-0 start-50 translate-middle-x mt-3`;
    alertDiv.style.zIndex = '9999';
    alertDiv.style.marginTop = '60px';
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    
    document.body.appendChild(alertDiv);
    
    // Autoclose after 5 seconds
    setTimeout(() => {
        alertDiv.remove();
    }, 5000);
}

// Función para actualizar la sección de cursos
function updateStudentCoursesSection() {
    fetch('/accounts/ajax/student/courses/', {
        headers: {
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
        }
    })
    .then(response => response.text())
    .then(html => {
        document.getElementById('studentCoursesSection').innerHTML = html;
    })
    .catch(error => {
        console.error('Error actualizando cursos:', error);
    });
}

document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') {
        hideJoinClassForm();
    }
});

document.addEventListener('DOMContentLoaded', function() {
    // Configurar el formulario de unirse a clase
    const joinClassForm = document.getElementById('joinClassForm');
    if (joinClassForm) {
        joinClassForm.addEventListener('submit', joinClassAJAX);
    }
    
    // Fix para modales - Solo para modales del dashboard (NO el modal de perfil)
    const dashboardModals = document.querySelectorAll('.modal:not(#profilePictureModal)');
    dashboardModals.forEach(function(modal) {
        modal.addEventListener('show.bs.modal', function() {
            this.style.zIndex = '1055';
            const backdrop = document.querySelector('.modal-backdrop');
            if (backdrop) {
                backdrop.style.zIndex = '1050';
            }
        });
    });
});
