// Funciones generales del dashboard del docente que no dependen de Django templates
document.addEventListener('DOMContentLoaded', function() {
    // Inicializar los tooltips de Bootstrap
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'))
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl)
    });
});

function showCreateCourseModal() {
    // Obtener un nuevo código de curso antes de mostrar el modal
    fetch('{% url "users:generate_class_code" %}', {
        method: 'GET',
        headers: {
            'X-CSRFToken': getCsrfToken(),
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.code) {
            document.getElementById('courseCode').value = data.code;
            document.getElementById('courseCode').readOnly = true; // El código no debe ser editable
            const modal = new bootstrap.Modal(document.getElementById('createCourseModal'));
            modal.show();
        } else {
            showAlert('Error al generar el código del curso', 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showAlert('Error al generar el código del curso', 'error');
    });
}

function submitCreateCourse() {
    const form = document.getElementById('createCourseForm');
    const formData = new FormData(form);

    // Validar campos requeridos - corregir para que coincida con los campos reales del formulario
    const requiredFields = ['courseName', 'courseCode', 'courseGrade', 'courseSection'];
    for (const fieldId of requiredFields) {
        const field = document.getElementById(fieldId);
        if (!field || !field.value) {
            showAlert(`Por favor complete el campo ${field ? (field.getAttribute('placeholder') || field.getAttribute('aria-label') || fieldId) : fieldId}`, 'warning');
            return;
        }
    }

    fetch('/accounts/api/create_class/', {
        method: 'POST',
        body: formData,
        headers: {
            'X-CSRFToken': getCsrfToken(),
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success && data.redirect_url) {
            window.location.href = data.redirect_url;
        } else if (data.success && data.course_id) {
            window.location.href = '/accounts/class/' + data.course_id + '/';
        } else if (data.success) {
            showAlert('Curso creado exitosamente, pero no se pudo redirigir.', 'success');
            window.location.reload();
        } else {
            showAlert(data.error || 'Error al crear el curso', 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showAlert('Error al crear el curso', 'error');
    });
}

function showAlert(message, type) {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type === 'error' ? 'danger' : type} alert-dismissible fade show`;
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    
    const container = document.querySelector('.container-fluid');
    container.insertBefore(alertDiv, container.firstChild);
    
    // Autoclose after 5 seconds
    setTimeout(() => {
        alertDiv.remove();
    }, 5000);
}

function getCsrfToken() {
    const csrfCookie = document.cookie.split(';')
        .find(cookie => cookie.trim().startsWith('csrftoken='));
    return csrfCookie ? csrfCookie.split('=')[1] : '';
}

// Funciones para otros modales
function showCreateAssignmentModal() {
    const modal = new bootstrap.Modal(document.getElementById('createAssignmentModal'));
    modal.show();
}

function showUploadMaterialModal() {
    const modal = new bootstrap.Modal(document.getElementById('uploadMaterialModal'));
    modal.show();
}

function showGradeSubmissionModal(submissionId, assignmentTitle, studentName) {
    const modal = new bootstrap.Modal(document.getElementById('gradeSubmissionModal'));
    document.getElementById('submissionInfo').innerHTML = `
        <div class="alert alert-info">
            <h6><strong>Tarea:</strong> ${assignmentTitle}</h6>
            <p class="mb-0"><strong>Estudiante:</strong> ${studentName}</p>
        </div>
    `;
    document.getElementById('submissionId').value = submissionId;
    modal.show();
}
