// Actualiza los contadores del dashboard de padres dinámicamente
function updateDashboardCounters() {
    fetch('/users/ajax/dashboard-stats/')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                document.getElementById('childrenCount').textContent = data.stats.children_count;
                document.getElementById('coursesCount').textContent = data.stats.courses_count;
                document.getElementById('overdueAssignments').textContent = data.stats.overdue_assignments;
                document.getElementById('upcomingEvents').textContent = data.stats.upcoming_events;
            }
        });
}

// Hook automático tras añadir hijo
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
            if (typeof onSuccess === 'function') onSuccess(data);
            updateDashboardCounters();
        } else {
            showAlert(data.error || 'Error al añadir hijo', 'error');
        }
    })
    .catch(() => showAlert('Error de red', 'error'));
}

// Hook automático tras eliminar hijo
function deleteChildAJAX(childId, onSuccess) {
    fetch('/users/ajax/delete-child/', {
        method: 'POST',
        body: new URLSearchParams({child_id: childId}),
        headers: {
            'X-CSRFToken': getCSRFToken(),
            'Content-Type': 'application/x-www-form-urlencoded',
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            if (typeof onSuccess === 'function') onSuccess(data);
            updateDashboardCounters();
        } else {
            showAlert(data.error || 'Error al eliminar hijo', 'error');
        }
    })
    .catch(() => showAlert('Error de red', 'error'));
}

// Utilidad para obtener el CSRF token
function getCSRFToken() {
    const csrfInput = document.querySelector('[name=csrfmiddlewaretoken]');
    return csrfInput ? csrfInput.value : '';
}

// Utilidad para mostrar alertas (puedes personalizarla)
function showAlert(message, type) {
    alert(message); // Reemplaza por tu sistema de alertas si tienes uno
} 