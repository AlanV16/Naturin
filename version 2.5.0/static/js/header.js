document.addEventListener('DOMContentLoaded', function () {
    // Elementos principales
    const navbarToggleBtn = document.getElementById('navbarToggleBtn');
    const mobileMenu = document.getElementById('mobileMenu');
    const closeMobileMenu = document.getElementById('closeMobileMenu');
    const switchDesktop = document.getElementById('teacherModeSwitch');
    const switchMobile = document.getElementById('teacherModeSwitchMobile');

    // Mostrar/ocultar menú móvil
    if (navbarToggleBtn && mobileMenu && closeMobileMenu) {
        navbarToggleBtn.addEventListener('click', function () {
            mobileMenu.classList.add('show');
            document.body.style.overflow = 'hidden';
        });
        closeMobileMenu.addEventListener('click', function () {
            mobileMenu.classList.remove('show');
            mobileMenu.classList.remove('dropdown-open');
            document.body.style.overflow = '';
        });
        // Cerrar menú móvil al hacer click fuera del contenido
        mobileMenu.addEventListener('click', function (e) {
            if (e.target === mobileMenu) {
                mobileMenu.classList.remove('show');
                mobileMenu.classList.remove('dropdown-open');
                document.body.style.overflow = '';
            }
        });
        // Cerrar menú móvil solo al hacer clic en enlaces (no en botones dropdown)
        mobileMenu.querySelectorAll('a').forEach(el => {
            el.addEventListener('click', function () {
                mobileMenu.classList.remove('show');
                mobileMenu.classList.remove('dropdown-open');
                document.body.style.overflow = '';
            });
        });
    }

    // Forzar dropdowns en menú móvil manualmente
    function isMobileMenu() {
        return window.innerWidth < 992;
    }

    if (mobileMenu) {
        mobileMenu.querySelectorAll('.dropdown-toggle').forEach(btn => {
            btn.addEventListener('click', function (e) {
                if (isMobileMenu()) {
                    e.preventDefault();
                    const parent = btn.closest('.dropdown');
                    const menu = parent.querySelector('.dropdown-menu');
                    // Cierra otros dropdowns abiertos
                    mobileMenu.querySelectorAll('.dropdown').forEach(drop => {
                        if (drop !== parent) {
                            drop.classList.remove('show');
                            const dropMenu = drop.querySelector('.dropdown-menu');
                            if (dropMenu) dropMenu.classList.remove('show');
                        }
                    });
                    // Alterna el actual
                    parent.classList.toggle('show');
                    menu.classList.toggle('show');
                    // Maneja overflow para dropdowns abiertos
                    setTimeout(() => {
                        const anyOpen = mobileMenu.querySelector('.dropdown.show');
                        if (anyOpen) {
                            mobileMenu.classList.add('dropdown-open');
                        } else {
                            mobileMenu.classList.remove('dropdown-open');
                        }
                    }, 50);
                }
            });
        });
    }

    // Sincronizar y activar modo oscuro desde ambos switches
    function setDarkMode(enabled) {
        if (enabled) {
            document.body.classList.add('dark-mode');
        } else {
            document.body.classList.remove('dark-mode');
        }
        // Sincroniza ambos switches
        if (switchDesktop) switchDesktop.checked = enabled;
        if (switchMobile) switchMobile.checked = enabled;
        // Guarda preferencia en localStorage
        localStorage.setItem('darkMode', enabled ? '1' : '0');
    }

    // Leer preferencia al cargar
    const darkPref = localStorage.getItem('darkMode');
    if (darkPref === '1') setDarkMode(true);

    if (switchDesktop) {
        switchDesktop.addEventListener('change', function () {
            setDarkMode(this.checked);
        });
    }
    if (switchMobile) {
        switchMobile.addEventListener('change', function () {
            setDarkMode(this.checked);
        });
    }

    // Asegurar que solo un dropdown esté abierto a la vez (Bootstrap 5, solo escritorio)
    document.addEventListener('show.bs.dropdown', function(event) {
        document.querySelectorAll('.dropdown-menu.show').forEach(dropdown => {
            if (!event.target.contains(dropdown)) {
                dropdown.classList.remove('show');
            }
        });
    });
});