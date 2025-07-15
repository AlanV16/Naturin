// Header Dashboard JavaScript - Modal de cambio de foto de perfil

let selectedPreset = null;
let uploadedFile = null;

function openProfilePictureModal() {
    const modal = new bootstrap.Modal(document.getElementById('profilePictureModal'));
    
    // Asegurar z-index ultra alto antes de mostrar
    const modalElement = document.getElementById('profilePictureModal');
    modalElement.style.zIndex = '9999';
    
    modal.show();
    
    // Después de mostrar, asegurar z-index del backdrop
    setTimeout(() => {
        const backdrop = document.querySelector('.modal-backdrop');
        if (backdrop) {
            backdrop.style.zIndex = '9998';
        }
        
        // Forzar z-index en el dialog y content también
        const dialog = modalElement.querySelector('.modal-dialog');
        const content = modalElement.querySelector('.modal-content');
        if (dialog) dialog.style.zIndex = '10000';
        if (content) content.style.zIndex = '10001';
    }, 100);
}

// Inicialización cuando se carga el DOM
document.addEventListener('DOMContentLoaded', function() {
    // Inicializar tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Configurar drag and drop si los elementos existen
    const uploadArea = document.getElementById('uploadArea');
    const avatarFile = document.getElementById('avatarFile');
    
    if (uploadArea && avatarFile) {
        setupDragAndDrop();
    }
    
    // Fix para z-index del modal
    const profileModal = document.getElementById('profilePictureModal');
    if (profileModal) {
        profileModal.addEventListener('show.bs.modal', function() {
            this.style.zIndex = '9999';
            
            setTimeout(() => {
                const backdrop = document.querySelector('.modal-backdrop');
                if (backdrop) {
                    backdrop.style.zIndex = '9998';
                }
                
                // Forzar z-index en todos los elementos del modal
                const dialog = this.querySelector('.modal-dialog');
                const content = this.querySelector('.modal-content');
                if (dialog) dialog.style.zIndex = '10000';
                if (content) content.style.zIndex = '10001';
                
                // Blur el dashboard cuando el modal está abierto
                const dashboard = document.querySelector('.student-dashboard-bg');
                if (dashboard) {
                    dashboard.style.filter = 'blur(2px)';
                    // NO forzar z-index en el dashboard, debe mantener z-index auto
                }
            }, 100);
        });
        
        profileModal.addEventListener('hidden.bs.modal', function() {
            // Restaurar el dashboard cuando se cierra el modal
            const dashboard = document.querySelector('.student-dashboard-bg');
            if (dashboard) {
                dashboard.style.filter = 'none';
            }
        });
    }
});

function setupDragAndDrop() {
    const uploadArea = document.getElementById('uploadArea');
    const avatarFile = document.getElementById('avatarFile');
    
    uploadArea.addEventListener('click', () => avatarFile.click());
    
    uploadArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadArea.classList.add('dragover');
    });
    
    uploadArea.addEventListener('dragleave', () => {
        uploadArea.classList.remove('dragover');
    });
    
    uploadArea.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadArea.classList.remove('dragover');
        
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            handleFileSelect(files[0]);
        }
    });
    
    avatarFile.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            handleFileSelect(e.target.files[0]);
        }
    });
}

function handleFileSelect(file) {
    // Validar tipo de archivo
    if (!file.type.startsWith('image/')) {
        alert('Por favor selecciona una imagen válida.');
        return;
    }
    
    // Validar tamaño (5MB)
    if (file.size > 5 * 1024 * 1024) {
        alert('La imagen es demasiado grande. El tamaño máximo es 5MB.');
        return;
    }
    
    uploadedFile = file;
    selectedPreset = null;
    
    // Mostrar vista previa
    const reader = new FileReader();
    reader.onload = (e) => {
        updatePreview(e.target.result);
    };
    reader.readAsDataURL(file);
    
    // Actualizar UI
    const uploadArea = document.getElementById('uploadArea');
    const uploadContent = uploadArea.querySelector('.upload-content');
    uploadContent.innerHTML = `
        <i class="bi bi-check-circle text-success" style="font-size: 3rem;"></i>
        <h6 class="text-success mt-2">Imagen seleccionada</h6>
        <p class="text-muted">${file.name}</p>
        <button type="button" class="btn btn-outline-secondary btn-sm" onclick="clearSelection()">
            Cambiar imagen
        </button>
    `;
}

function selectPresetAvatar(presetName) {
    selectedPreset = presetName;
    uploadedFile = null;
    
    // Limpiar selección anterior
    document.querySelectorAll('.preset-avatar').forEach(avatar => {
        avatar.classList.remove('selected');
    });
    
    // Marcar como seleccionado
    const selectedAvatar = document.querySelector(`[data-preset="${presetName}"]`);
    if (selectedAvatar) {
        selectedAvatar.classList.add('selected');
    }
    
    // Actualizar vista previa
    const previewSrc = `/static/images/avatars/${presetName}`;
    updatePreview(previewSrc);
}

function updatePreview(imageSrc) {
    const preview = document.getElementById('avatarPreview');
    if (preview) {
        preview.innerHTML = `<img src="${imageSrc}" alt="Vista previa" class="img-fluid rounded-circle" style="width:100%;height:100%;object-fit:cover;">`;
    }
}

function clearSelection() {
    uploadedFile = null;
    selectedPreset = null;
    
    // Restaurar vista previa original
    const preview = document.getElementById('avatarPreview');
    if (preview) {
        const userAvatar = preview.dataset.userAvatar;
        const userInitial = preview.dataset.userInitial;
        
        if (userAvatar) {
            preview.innerHTML = `<img src="${userAvatar}" alt="Avatar actual" class="img-fluid rounded-circle" style="width:100%;height:100%;object-fit:cover;">`;
        } else {
            preview.innerHTML = `<span class="fw-bold avatar-initial">${userInitial}</span>`;
        }
    }
    
    // Restaurar área de upload
    const uploadArea = document.getElementById('uploadArea');
    if (uploadArea) {
        const uploadContent = uploadArea.querySelector('.upload-content');
        uploadContent.innerHTML = `
            <i class="bi bi-cloud-upload upload-icon"></i>
            <h6>Arrastra una imagen aquí</h6>
            <p class="text-muted mb-3">o</p>
            <button type="button" class="btn btn-outline-primary" onclick="document.getElementById('avatarFile').click()">
                Seleccionar Archivo
            </button>
        `;
    }
    
    // Limpiar selecciones de presets
    document.querySelectorAll('.preset-avatar').forEach(avatar => {
        avatar.classList.remove('selected');
    });
}

function saveProfilePicture() {
    if (!uploadedFile && !selectedPreset) {
        alert('Por favor selecciona una imagen o elige una predeterminada.');
        return;
    }
    
    const formData = new FormData();
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]');
    if (csrfToken) {
        formData.append('csrfmiddlewaretoken', csrfToken.value);
    }
    
    if (uploadedFile) {
        formData.append('avatar', uploadedFile);
    } else if (selectedPreset) {
        formData.append('preset_avatar', selectedPreset);
    }
    
    // Mostrar loading
    const saveBtn = document.getElementById('saveAvatarBtn');
    const originalText = saveBtn.innerHTML;
    saveBtn.innerHTML = '<i class="bi bi-arrow-clockwise me-2"></i>Guardando...';
    saveBtn.disabled = true;
    
    // Aquí iría la llamada AJAX para guardar
    // Por ahora simular el guardado
    setTimeout(() => {
        // Cerrar modal
        const modal = bootstrap.Modal.getInstance(document.getElementById('profilePictureModal'));
        if (modal) {
            modal.hide();
        }
        
        // Mostrar mensaje de éxito
        showToast('Foto de perfil actualizada correctamente', 'success');
        
        saveBtn.innerHTML = originalText;
        saveBtn.disabled = false;
    }, 1000);
}

function showToast(message, type = 'success') {
    // Crear toast dinámicamente
    const toastHtml = `
        <div class="toast align-items-center text-white bg-${type} border-0" role="alert">
            <div class="d-flex">
                <div class="toast-body">
                    <i class="bi bi-check-circle me-2"></i>${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        </div>
    `;
    
    let toastContainer = document.querySelector('.toast-container');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.className = 'toast-container position-fixed top-0 end-0 p-3';
        toastContainer.style.zIndex = '9999';
        document.body.appendChild(toastContainer);
    }
    
    toastContainer.insertAdjacentHTML('beforeend', toastHtml);
    const toast = new bootstrap.Toast(toastContainer.lastElementChild);
    toast.show();
}
