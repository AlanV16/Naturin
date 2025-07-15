/**
 * Expert Dashboard JavaScript
 * Handles sheet creation, file uploads, and expert-specific functionality
 */

document.addEventListener('DOMContentLoaded', function() {
    initializeExpertDashboard();
});

function initializeExpertDashboard() {
    loadCategories();
    setupCreateSheetForm();
    setupFileUpload();
    loadExpertSheets();
}

// Load categories for sheet creation
async function loadCategories() {
    try {
        const response = await fetch('/content/api/categories/');
        const data = await response.json();
        
        if (data.success) {
            const categorySelect = document.getElementById('sheetCategory');
            categorySelect.innerHTML = '<option value="">Seleccionar categoría</option>';
            
            data.categories.forEach(category => {
                const option = document.createElement('option');
                option.value = category.id;
                option.textContent = category.name;
                categorySelect.appendChild(option);
            });
        }
    } catch (error) {
        console.error('Error loading categories:', error);
        showAlert('Error al cargar las categorías', 'danger');
    }
}

// Setup create sheet form submission
function setupCreateSheetForm() {
    const form = document.getElementById('createSheetForm');
    const modal = new bootstrap.Modal(document.getElementById('createSheetModal'));
    
    form.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const submitBtn = form.querySelector('button[type="submit"]');
        const originalText = submitBtn.textContent;
        
        // Show loading state
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Creando...';
        
        try {
            const formData = new FormData(form);
            
            const response = await fetch('/content/api/sheets/create/', {
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCSRFToken()
                },
                body: formData
            });
            
            const data = await response.json();
            
            if (data.success) {
                showAlert('Ficha creada exitosamente', 'success');
                form.reset();
                modal.hide();
                loadExpertSheets(); // Reload the sheets list
            } else {
                showAlert(data.message || 'Error al crear la ficha', 'danger');
                
                // Show field errors if any
                if (data.errors) {
                    showFormErrors(data.errors);
                }
            }
        } catch (error) {
            console.error('Error creating sheet:', error);
            showAlert('Error de conexión al crear la ficha', 'danger');
        } finally {
            // Reset button state
            submitBtn.disabled = false;
            submitBtn.textContent = originalText;
        }
    });
}

// Setup file upload preview
function setupFileUpload() {
    const fileInputs = document.querySelectorAll('input[type="file"]');
    
    fileInputs.forEach(input => {
        input.addEventListener('change', function(e) {
            const file = e.target.files[0];
            const previewId = this.getAttribute('data-preview');
            
            if (file && previewId) {
                const preview = document.getElementById(previewId);
                
                if (file.type.startsWith('image/')) {
                    const reader = new FileReader();
                    reader.onload = function(e) {
                        preview.innerHTML = `<img src="${e.target.result}" class="img-thumbnail" style="max-height: 100px;">`;
                    };
                    reader.readAsDataURL(file);
                } else {
                    preview.innerHTML = `<i class="fas fa-file"></i> ${file.name}`;
                }
            }
        });
    });
}

// Load expert's sheets
async function loadExpertSheets() {
    try {
        const response = await fetch('/content/api/sheets/');
        const data = await response.json();
        
        if (data.success) {
            updateSheetsTable(data.sheets);
        }
    } catch (error) {
        console.error('Error loading sheets:', error);
    }
}

// Update sheets table
function updateSheetsTable(sheets) {
    const tbody = document.querySelector('#expertSheetsTable tbody');
    if (!tbody) return;
    
    tbody.innerHTML = '';
    
    if (sheets.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="5" class="text-center text-muted">
                    <i class="fas fa-inbox fa-2x mb-3"></i>
                    <p>No tienes fichas creadas aún</p>
                </td>
            </tr>
        `;
        return;
    }
    
    sheets.forEach(sheet => {
        const row = document.createElement('tr');
        
        // Obtener icono según el tipo
        const typeIcons = {
            'flora': '<i class="bi bi-flower1 text-success"></i>',
            'fauna': '<i class="bi bi-bug text-primary"></i>',
            'ecosystem': '<i class="bi bi-geo-alt text-warning"></i>'
        };
        
        // Mostrar tags relevantes
        const relevantTags = [];
        if (sheet.tags) {
            if (sheet.tags.clasificacion_biologica) {
                relevantTags.push(sheet.tags.clasificacion_biologica);
            }
            if (sheet.tags.estado_conservacion) {
                relevantTags.push(sheet.tags.estado_conservacion);
            }
            if (sheet.tags.tipo_ecosistema) {
                relevantTags.push(sheet.tags.tipo_ecosistema);
            }
        }
        
        row.innerHTML = `
            <td>
                <div class="d-flex align-items-center">
                    ${sheet.image ? `<img src="${sheet.image}" class="rounded me-3" style="width: 40px; height: 40px; object-fit: cover;">` : ''}
                    <div>
                        <h6 class="mb-1">
                            ${typeIcons[sheet.sheet_type] || ''} ${sheet.title}
                        </h6>
                        <small class="text-muted">${sheet.category_name}</small>
                        ${relevantTags.length > 0 ? `
                            <div class="mt-1">
                                ${relevantTags.map(tag => `<span class="badge bg-light text-dark me-1">${tag}</span>`).join('')}
                            </div>
                        ` : ''}
                    </div>
                </div>
            </td>
            <td>${getStatusBadge(sheet.status)}</td>
            <td><small class="text-muted">${formatDate(sheet.created_at)}</small></td>
            <td><small class="text-muted">${formatDate(sheet.updated_at)}</small></td>
            <td>
                <div class="btn-group btn-group-sm">
                    <button class="btn btn-outline-primary" onclick="viewSheet(${sheet.id})" title="Ver ficha">
                        <i class="bi bi-eye"></i>
                    </button>
                    <button class="btn btn-outline-secondary" onclick="editSheet(${sheet.id})" title="Editar ficha">
                        <i class="bi bi-pencil"></i>
                    </button>
                    ${sheet.status === 'draft' ? `
                        <button class="btn btn-outline-danger" onclick="deleteSheet(${sheet.id})" title="Eliminar ficha">
                            <i class="bi bi-trash"></i>
                        </button>
                    ` : ''}
                </div>
            </td>
        `;
        tbody.appendChild(row);
    });
}

// Get status badge HTML
function getStatusBadge(status) {
    const badges = {
        'draft': '<span class="badge bg-secondary">Borrador</span>',
        'pending_review': '<span class="badge bg-warning">Pendiente de Revisión</span>',
        'in_review': '<span class="badge bg-info">En Revisión</span>',
        'approved': '<span class="badge bg-success">Aprobado</span>',
        'published': '<span class="badge bg-primary">Publicado</span>',
        'rejected': '<span class="badge bg-danger">Rechazado</span>'
    };
    
    return badges[status] || `<span class="badge bg-light text-dark">${status}</span>`;
}

// Format date for display
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('es-ES', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    });
}

// Sheet actions
function viewSheet(sheetId) {
    // TODO: Implement view sheet functionality
    console.log('View sheet:', sheetId);
}

function editSheet(sheetId) {
    // TODO: Implement edit sheet functionality
    console.log('Edit sheet:', sheetId);
}

function deleteSheet(sheetId) {
    if (confirm('¿Estás seguro de que quieres eliminar esta ficha?')) {
        // TODO: Implement delete sheet functionality
        console.log('Delete sheet:', sheetId);
    }
}

// Utility functions
function getCSRFToken() {
    return document.querySelector('[name=csrfmiddlewaretoken]').value;
}

function showAlert(message, type) {
    const alertsContainer = document.getElementById('alertsContainer') || document.body;
    
    const alert = document.createElement('div');
    alert.className = `alert alert-${type} alert-dismissible fade show`;
    alert.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    alertsContainer.appendChild(alert);
    
    // Auto-dismiss after 5 seconds
    setTimeout(() => {
        if (alert.parentNode) {
            alert.remove();
        }
    }, 5000);
}

function showFormErrors(errors) {
    // Clear previous errors
    document.querySelectorAll('.invalid-feedback').forEach(el => el.remove());
    document.querySelectorAll('.is-invalid').forEach(el => el.classList.remove('is-invalid'));
    
    // Show new errors
    Object.keys(errors).forEach(field => {
        const input = document.querySelector(`[name="${field}"]`);
        if (input) {
            input.classList.add('is-invalid');
            
            const feedback = document.createElement('div');
            feedback.className = 'invalid-feedback';
            feedback.textContent = errors[field][0]; // Show first error message
            
            input.parentNode.appendChild(feedback);
        }
    });
}

// Export functions for global access
window.expertDashboard = {
    loadCategories,
    loadExpertSheets,
    viewSheet,
    editSheet,
    deleteSheet
};
