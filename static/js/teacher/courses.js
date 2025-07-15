function generateCourseCode() {
    const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789';
    let code = '';
    for (let i = 0; i < 6; i++) {
        code += chars.charAt(Math.floor(Math.random() * chars.length));
    }
    return code;
}

function showCreateCourseModal() {
    const codeInput = document.getElementById('courseCode');
    if (codeInput) {
        codeInput.value = generateCourseCode();
    }
    
    // Detectar qué librería está disponible
    if (typeof $ !== 'undefined' && $.fn.modal) {
        // Usar jQuery Bootstrap
        $('#createCourseModal').modal('show');
    } else if (typeof bootstrap !== 'undefined') {
        // Usar Bootstrap 5 vanilla JS
        const modal = new bootstrap.Modal(document.getElementById('createCourseModal'));
        modal.show();
    } else {
        // Fallback sin Bootstrap - mostrar modal manualmente
        const modal = document.getElementById('createCourseModal');
        modal.classList.add('show');
        modal.style.display = 'block';
        modal.setAttribute('aria-hidden', 'false');
        document.body.classList.add('modal-open');
        
        // Crear backdrop
        const backdrop = document.createElement('div');
        backdrop.className = 'modal-backdrop fade show';
        backdrop.id = 'modal-backdrop';
        document.body.appendChild(backdrop);
    }
}

function hideCreateCourseModal() {
    if (typeof $ !== 'undefined' && $.fn.modal) {
        $('#createCourseModal').modal('hide');
    } else if (typeof bootstrap !== 'undefined') {
        const modalInstance = bootstrap.Modal.getInstance(document.getElementById('createCourseModal'));
        if (modalInstance) modalInstance.hide();
    } else {
        // Fallback sin Bootstrap
        const modal = document.getElementById('createCourseModal');
        modal.classList.remove('show');
        modal.style.display = 'none';
        modal.setAttribute('aria-hidden', 'true');
        document.body.classList.remove('modal-open');
        
        // Remover backdrop
        const backdrop = document.getElementById('modal-backdrop');
        if (backdrop) backdrop.remove();
    }
}

document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('createCourseForm');
    if (form) {
        form.addEventListener('submit', function(e) {
            e.preventDefault();

            const formData = {
                name: form.querySelector('#courseName')?.value || '',
                code: form.querySelector('#courseCode')?.value || '',
                description: form.querySelector('#courseDescription')?.value || '',
                subject: form.querySelector('#courseSubject')?.value || '',
                grade: form.querySelector('#courseGrade')?.value || ''
            };

            // Validar campos obligatorios
            if (!formData.name.trim()) {
                alert('El nombre del curso es requerido');
                return;
            }
            
            if (!formData.subject.trim()) {
                alert('La materia es requerida');
                return;
            }
            
            if (!formData.grade.trim()) {
                alert('El grado es requerido');
                return;
            }

            console.log('Enviando datos:', formData);
            
            const url = window.CREATE_COURSE_URL || '/accounts/teacher/create-course/';
            const token = window.CSRF_TOKEN || document.querySelector('[name=csrfmiddlewaretoken]')?.value;
            
            console.log('URL:', url);
            console.log('Token:', token);

            fetch(url, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "X-CSRFToken": token
                },
                body: JSON.stringify(formData)
            })
            .then(response => {
                console.log('Respuesta status:', response.status);
                return response.json();
            })
            .then(data => {
                console.log('Respuesta data:', data);
                if (data.success) {
                    hideCreateCourseModal();
                    alert(data.message || 'Curso creado exitosamente');
                    // Redirigir al detalle del curso creado
                    window.location.href = `/accounts/course/${data.course_id}/`;
                } else {
                    alert(data.error || "Error al crear el curso");
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert("Error al crear el curso: " + error.message);
            });
        });
    }

    // Event listeners para cerrar modal con botón X
    const closeButtons = document.querySelectorAll('[data-bs-dismiss="modal"]');
    closeButtons.forEach(button => {
        button.addEventListener('click', hideCreateCourseModal);
    });

    // Cerrar modal al hacer clic en el backdrop
    const modal = document.getElementById('createCourseModal');
    if (modal) {
        modal.addEventListener('click', function(e) {
            if (e.target === modal) {
                hideCreateCourseModal();
            }
        });
    }

    // Funcionalidad de búsqueda
    const courseSearch = document.getElementById('courseSearch');
    if (courseSearch) {
        courseSearch.addEventListener('input', function(e) {
            const searchTerm = e.target.value.toLowerCase();
            const courseItems = document.querySelectorAll('.course-item');
            
            courseItems.forEach(item => {
                const courseName = item.querySelector('.course-title')?.textContent.toLowerCase() || '';
                const teacherName = item.querySelector('.course-teacher')?.textContent.toLowerCase() || '';
                
                if (courseName.includes(searchTerm) || teacherName.includes(searchTerm)) {
                    item.style.display = 'block';
                } else {
                    item.style.display = 'none';
                }
            });
        });
    }

    // Funcionalidad de filtros
    document.querySelectorAll('.filter-tab').forEach(tab => {
        tab.addEventListener('click', function() {
            // Actualizar tabs activos
            document.querySelectorAll('.filter-tab').forEach(t => t.classList.remove('active'));
            this.classList.add('active');
            
            // Filtrar cursos
            const filter = this.dataset.filter;
            const courseItems = document.querySelectorAll('.course-item');
            
            courseItems.forEach(item => {
                const status = item.dataset.status;
                if (filter === 'all' || status === filter) {
                    item.style.display = 'block';
                } else {
                    item.style.display = 'none';
                }
            });
        });
    });
});

// Funciones adicionales para los botones de acción
function manageCourse(courseId) {
    window.location.href = `/accounts/teacher/course/${courseId}/manage/`;
}

function viewStudents(courseId) {
    window.location.href = `/accounts/teacher/course/${courseId}/students/`;
}

function createAssignment(courseId) {
    console.log('Crear tarea para curso:', courseId);
}

function editCourse(courseId) {
    console.log('Editar curso:', courseId);
}

function showCourseSettings(courseId) {
    console.log('Configuración del curso:', courseId);
}

