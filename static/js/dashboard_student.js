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
document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') {
        hideJoinClassForm();
    }
});
document.addEventListener('DOMContentLoaded', function() {
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
