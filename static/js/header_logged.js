document.addEventListener('DOMContentLoaded', function () {
    // Menú móvil
    const navbarToggleBtn = document.getElementById('navbarToggleBtn');
    const mobileMenu = document.getElementById('mobileMenu');
    const closeMobileMenu = document.getElementById('closeMobileMenu');

    if (navbarToggleBtn && mobileMenu && closeMobileMenu) {
        navbarToggleBtn.addEventListener('click', function () {
            mobileMenu.classList.add('show');
            document.body.style.overflow = 'hidden';
        });
        closeMobileMenu.addEventListener('click', function () {
            mobileMenu.classList.remove('show');
            document.body.style.overflow = '';
        });
        mobileMenu.addEventListener('click', function (e) {
            if (e.target === mobileMenu) {
                mobileMenu.classList.remove('show');
                document.body.style.overflow = '';
            }
        });
        mobileMenu.querySelectorAll('a').forEach(el => {
            el.addEventListener('click', function () {
                mobileMenu.classList.remove('show');
                document.body.style.overflow = '';
            });
        });
    }

    // Modo oscuro sincronizado
    const switchDesktop = document.getElementById('teacherModeSwitch');
    const switchMobile = document.getElementById('teacherModeSwitchMobile');
    function setDarkMode(enabled) {
        if (enabled) {
            document.body.classList.add('dark-mode');
        } else {
            document.body.classList.remove('dark-mode');
        }
        if (switchDesktop) switchDesktop.checked = enabled;
        if (switchMobile) switchMobile.checked = enabled;
        localStorage.setItem('darkMode', enabled ? '1' : '0');
    }
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

    // Dropdown de perfil de usuario (userDropdown)
    const userDropdownBtn = document.getElementById('userDropdown');
    const userDropdownMenu = userDropdownBtn ? userDropdownBtn.nextElementSibling : null;
    let userDropdownOpen = false;

    function closeUserDropdown() {
        if (userDropdownMenu) {
            userDropdownMenu.classList.remove('show');
            userDropdownBtn.setAttribute('aria-expanded', 'false');
            userDropdownOpen = false;
        }
    }

    function openUserDropdown() {
        if (userDropdownMenu) {
            userDropdownMenu.classList.add('show');
            userDropdownBtn.setAttribute('aria-expanded', 'true');
            userDropdownOpen = true;
        }
    }

    if (userDropdownBtn && userDropdownMenu) {
        userDropdownBtn.addEventListener('click', function (e) {
            e.preventDefault();
            e.stopPropagation();
            if (userDropdownOpen) {
                closeUserDropdown();
            } else {
                openUserDropdown();
            }
        });
        // Cerrar al hacer clic fuera
        document.addEventListener('click', function (e) {
            if (userDropdownOpen && !userDropdownMenu.contains(e.target) && !userDropdownBtn.contains(e.target)) {
                closeUserDropdown();
            }
        });
        // Cerrar al seleccionar una opción
        userDropdownMenu.querySelectorAll('a, button').forEach(function (el) {
            el.addEventListener('click', function () {
                closeUserDropdown();
            });
        });
    }

    // Cierre global para ambos dropdowns al hacer clic fuera
    document.addEventListener('click', function (e) {
        // Usuario
        if (userDropdownOpen && userDropdownMenu && !userDropdownMenu.contains(e.target) && !userDropdownBtn.contains(e.target)) {
            closeUserDropdown();
        }
    });
}); 