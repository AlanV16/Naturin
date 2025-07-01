document.addEventListener('DOMContentLoaded', function() {
    // === VARIABLES ===
    const loginBtns = document.querySelectorAll('.login-btn');
    const registerBtns = document.querySelectorAll('.register-btn');
    const loginDropdown = document.querySelector('.login-dropdown');
    const registerDropdown = document.querySelector('.register-dropdown');
    const dropdownBackdrop = document.getElementById('dropdownBackdrop');

    // === FUNCIONES DE DROPDOWN ===
    function showDropdown(dropdown) {
        // Cerrar todos los dropdowns primero
        closeAllDropdowns();
        if (dropdown) {
            setTimeout(() => {
                dropdown.classList.add('show');
                dropdownBackdrop.classList.add('show');
            }, 10);
        }
    }

    function closeAllDropdowns() {
        document.querySelectorAll('.auth-dropdown-content').forEach(el => {
            el.classList.remove('show');
        });
        dropdownBackdrop.classList.remove('show');
    }

    // === EVENT LISTENERS PARA LOGIN ===
    loginBtns.forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            if (loginDropdown && loginDropdown.classList.contains('show')) {
                closeAllDropdowns();
            } else {
                showDropdown(loginDropdown);
            }
        });
    });

    // === EVENT LISTENERS PARA REGISTRO ===
    registerBtns.forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            if (registerDropdown && registerDropdown.classList.contains('show')) {
                closeAllDropdowns();
            } else {
                showDropdown(registerDropdown);
            }
        });
    });

    // === BACKDROP CLICK ===
    if (dropdownBackdrop) {
        dropdownBackdrop.addEventListener('click', closeAllDropdowns);
    }

    // === CLICK FUERA DEL DROPDOWN ===
    document.addEventListener('click', function(e) {
        if (!e.target.closest('.auth-dropdown')) {
            closeAllDropdowns();
        }
    });

    // === PREVENIR CIERRE AL HACER CLICK DENTRO ===
    document.querySelectorAll('.auth-dropdown-content').forEach(dropdown => {
        dropdown.addEventListener('click', function(e) {
            e.stopPropagation();
        });
    });

    // === TECLA ESCAPE ===
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            closeAllDropdowns();
        }
    });

    // === MODO OSCURO ===
    const switcher = document.getElementById('teacherModeSwitch');
    if (switcher) {
        // Cargar estado guardado
        const savedMode = localStorage.getItem('darkMode');
        if (savedMode === 'true') {
            document.body.classList.add('dark-mode');
            switcher.checked = true;
        }
        // Event listener para cambios
        switcher.addEventListener('change', function() {
            if (this.checked) {
                document.body.classList.add('dark-mode');
                localStorage.setItem('darkMode', 'true');
            } else {
                document.body.classList.remove('dark-mode');
                localStorage.setItem('darkMode', 'false');
            }
        });
    }

    // === CARRUSEL DE BOOTSTRAP ===
    const carousels = document.querySelectorAll('.carousel');
    carousels.forEach(function(carousel) {
        if (window.bootstrap) {
            new bootstrap.Carousel(carousel, {
                interval: 5000,
                wrap: true,
                pause: 'hover'
            });
        }
    });

    // === ANIMACIONES SUAVES ===
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.animation = 'fadeInUp 0.6s ease forwards';
            }
        });
    }, observerOptions);

    // Observar elementos para animaciones
    document.querySelectorAll('.card, .alert, .badge').forEach(el => {
        observer.observe(el);
    });
});

// === ANIMACIONES CSS ===
const style = document.createElement('style');
style.textContent = `
    @keyframes fadeInUp {
        from {
            opacity: 0;
            transform: translateY(20px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    .card, .alert, .badge {
        opacity: 0;
    }
`;
document.head.appendChild(style);