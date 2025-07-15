// En static/js/shared/calendar.js

document.addEventListener('DOMContentLoaded', function() {
    initializeCalendar();
});

function initializeCalendar() {
    // Inicializar controles de vista
    const viewControls = document.querySelectorAll('input[name="view"]');
    viewControls.forEach(control => {
        control.addEventListener('change', function() {
            changeView(this.value);
        });
    });

    // Inicializar formulario de crear evento
    const createEventForm = document.getElementById('createEventForm');
    if (createEventForm) {
        createEventForm.addEventListener('submit', handleCreateEvent);
    }
}

function navigateMonth(year, month) {
    const url = new URL(window.location.href);
    url.searchParams.set('year', year);
    url.searchParams.set('month', month);
    window.location.href = url.toString();
}

function changeView(viewType) {
    const url = new URL(window.location.href);
    url.searchParams.set('view', viewType);
    window.location.href = url.toString();
}

function selectDay(date, dayElement) {
    // Remover selección previa
    document.querySelectorAll('.calendar-day').forEach(day => {
        day.classList.remove('selected-day');
    });
    
    // Añadir selección al día actual
    dayElement.classList.add('selected-day');
    
    // Mostrar eventos del día seleccionado en el sidebar
    showSelectedDayEvents(date);
}

function showSelectedDayEvents(date) {
    const selectedDaySection = document.getElementById('selectedDayEvents');
    const upcomingEventsSection = document.getElementById('upcomingEventsSection');
    const selectedDateSpan = document.getElementById('selectedDate');
    const eventsList = document.getElementById('selectedDayEventsList');
    
    // Formatear la fecha para mostrar
    const dateObj = new Date(date + 'T00:00:00');
    const formattedDate = dateObj.toLocaleDateString('es-ES', {
        weekday: 'long',
        year: 'numeric',
        month: 'long',
        day: 'numeric'
    });
    
    selectedDateSpan.textContent = formattedDate;
    
    // Obtener eventos del día desde los datos
    const dayEvents = eventsData[date] || [];
    
    if (dayEvents.length === 0) {
        eventsList.innerHTML = `
            <div class="no-events">
                <i class="bi bi-calendar-x me-2"></i>
                No hay eventos programados para este día
            </div>
        `;
    } else {
        let eventsHTML = '';
        dayEvents.forEach(event => {
            eventsHTML += `
                <div class="event-card ${event.color_class}" onclick="showEventDetails('${event.id}')">
                    <div class="event-title">
                        <i class="bi bi-${event.icon} me-2"></i>
                        ${event.title}
                    </div>
                    <div class="event-time">
                        <i class="bi bi-clock me-1"></i>
                        ${event.start_time}
                        ${event.location ? `
                            <span class="ms-2">
                                <i class="bi bi-geo-alt me-1"></i>
                                ${event.location}
                            </span>
                        ` : ''}
                    </div>
                    ${event.description ? `
                        <div class="event-description">
                            ${event.description.length > 80 ? event.description.substring(0, 80) + '...' : event.description}
                        </div>
                    ` : ''}
                    ${event.course ? `
                        <div class="event-course">
                            <i class="bi bi-book me-1"></i>
                            ${event.course}
                        </div>
                    ` : ''}
                </div>
            `;
        });
        eventsList.innerHTML = eventsHTML;
    }
    
    // Mostrar la sección de eventos del día seleccionado
    selectedDaySection.style.display = 'block';
    // Ocultar la sección de próximos eventos
    upcomingEventsSection.style.display = 'none';
}

function showDayEvents(date) {
    // Esta función ahora redirige a selectDay para consistencia
    const dayElement = document.querySelector(`[data-date="${date}"]`);
    if (dayElement) {
        selectDay(date, dayElement);
    }
}

function showEventDetails(eventId) {
    // Obtener detalles del evento via AJAX
    fetch(`/api/events/${eventId}/`)
        .then(response => response.json())
        .then(data => {
            const modalTitle = document.getElementById('eventDetailTitle');
            const modalBody = document.getElementById('eventDetailBody');
            
            modalTitle.textContent = data.title;
            modalBody.innerHTML = `
                <div class="event-details">
                    <div class="detail-item">
                        <strong>Tipo:</strong> ${data.event_type}
                    </div>
                    <div class="detail-item">
                        <strong>Fecha:</strong> ${data.start_date}
                    </div>
                    <div class="detail-item">
                        <strong>Hora:</strong> ${data.start_time}
                    </div>
                    ${data.location ? `<div class="detail-item"><strong>Ubicación:</strong> ${data.location}</div>` : ''}
                    ${data.description ? `<div class="detail-item"><strong>Descripción:</strong> ${data.description}</div>` : ''}
                    ${data.course ? `<div class="detail-item"><strong>Curso:</strong> ${data.course}</div>` : ''}
                </div>
            `;
            
            const modal = new bootstrap.Modal(document.getElementById('eventDetailModal'));
            modal.show();
        })
        .catch(error => {
            console.error('Error:', error);
            showMessage('Error al cargar los detalles del evento', 'error');
        });
}

function handleCreateEvent(e) {
    e.preventDefault();
    
    const formData = new FormData(e.target);
    const eventData = {
        title: formData.get('title'),
        event_type: formData.get('event_type'),
        date: formData.get('date'),
        time: formData.get('time'),
        location: formData.get('location'),
        description: formData.get('description'),
    };

    fetch('/api/events/create/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify(eventData)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showMessage('Evento creado exitosamente', 'success');
            const modal = bootstrap.Modal.getInstance(document.getElementById('createEventModal'));
            modal.hide();
            // Recargar página para mostrar el nuevo evento
            window.location.reload();
        } else {
            showMessage(data.message || 'Error al crear el evento', 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showMessage('Error al crear el evento', 'error');
    });
}

function showMessage(message, type) {
    // Mostrar mensajes de toast o alertas
    const alertClass = type === 'error' ? 'alert-danger' : 
                      type === 'success' ? 'alert-success' : 'alert-info';
    
    const alert = document.createElement('div');
    alert.className = `alert ${alertClass} alert-dismissible fade show`;
    alert.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.body.appendChild(alert);
    
    setTimeout(() => {
        alert.remove();
    }, 5000);
}

function showModal(title, content) {
    const modal = document.getElementById('eventDetailModal');
    const modalTitle = document.getElementById('eventDetailTitle');
    const modalBody = document.getElementById('eventDetailBody');
    
    modalTitle.textContent = title;
    modalBody.innerHTML = content;
    
    const bsModal = new bootstrap.Modal(modal);
    bsModal.show();
}

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

function showUpcomingEvents() {
    const selectedDaySection = document.getElementById('selectedDayEvents');
    const upcomingEventsSection = document.getElementById('upcomingEventsSection');
    
    // Ocultar la sección de eventos del día seleccionado
    selectedDaySection.style.display = 'none';
    // Mostrar la sección de próximos eventos
    upcomingEventsSection.style.display = 'block';
    
    // Remover selección de días
    document.querySelectorAll('.calendar-day').forEach(day => {
        day.classList.remove('selected-day');
    });
}

// Añadir evento para hacer clic fuera del calendario
document.addEventListener('DOMContentLoaded', function() {
    initializeCalendar();
    
    // Hacer clic fuera del calendario para mostrar próximos eventos
    document.addEventListener('click', function(e) {
        const calendarGrid = document.querySelector('.calendar-grid');
        const selectedDaySection = document.getElementById('selectedDayEvents');
        
        if (calendarGrid && !calendarGrid.contains(e.target) && 
            selectedDaySection && selectedDaySection.style.display === 'block') {
            // Solo si hay un día seleccionado y se hace clic fuera del calendario
            if (e.target.closest('.sidebar-section') === null) {
                showUpcomingEvents();
            }
        }
    });
});