document.addEventListener('DOMContentLoaded', function () {
    const tabButtons = document.querySelectorAll('#aprenderTabs .nav-link');
    const contentLoader = document.getElementById('tab-content-loader');
    const contentDynamic = document.getElementById('tab-content-dynamic');

    function showLoader() {
        contentLoader.style.display = 'block';
        contentDynamic.innerHTML = '';
    }
    function hideLoader() {
        contentLoader.style.display = 'none';
    }
    function loadTab(section, params = null) {
        showLoader();
        let url = '';
        if (section === 'educativas') {
            url = '/especies/tab/';
        } else if (section === 'multimedia') {
            url = '/multimedia/tab/';
        } else if (section === 'mapa') {
            url = '/mapa-especies/tab/';
        }
        if (params) {
            url += '?' + params;
        }
        fetch(url)
            .then(response => {
                if (!response.ok) throw new Error('Error al cargar el contenido.');
                return response.text();
            })
            .then(html => {
                hideLoader();
                contentDynamic.innerHTML = html;
                attachFilterHandler();
                attachPaginationHandler();
            })
            .catch(err => {
                hideLoader();
                contentDynamic.innerHTML = '<div class="alert alert-danger">No se pudo cargar el contenido.</div>';
            });
    }
    function attachFilterHandler() {
        const filterForm = document.getElementById('multimedia-filter-form');
        if (filterForm) {
            filterForm.addEventListener('submit', function (e) {
                e.preventDefault();
                const formData = new FormData(filterForm);
                const params = new URLSearchParams(formData).toString();
                loadTab('multimedia', params);
            });
            const clearBtn = document.getElementById('clear-filters');
            if (clearBtn) {
                clearBtn.addEventListener('click', function (e) {
                    e.preventDefault();
                    filterForm.reset();
                    loadTab('multimedia');
                });
            }
        }
    }
    function attachPaginationHandler() {
        const pagination = contentDynamic.querySelector('.multimedia-pagination');
        if (pagination) {
            pagination.querySelectorAll('.page-btn[data-page]').forEach(btn => {
                btn.addEventListener('click', function (e) {
                    e.preventDefault();
                    const page = this.getAttribute('data-page');
                    // Mantener los filtros actuales
                    const filterForm = document.getElementById('multimedia-filter-form');
                    let params = '';
                    if (filterForm) {
                        const formData = new FormData(filterForm);
                        params = new URLSearchParams(formData).toString();
                        if (params) {
                            params += '&';
                        }
                    }
                    params += 'page=' + page;
                    loadTab('multimedia', params);
                });
            });
        }
    }
    function getTabFromUrl() {
        const params = new URLSearchParams(window.location.search);
        const tab = params.get('tab');
        if (tab === 'multimedia') return 'multimedia';
        if (tab === 'mapa') return 'mapa';
        return 'educativas';
    }
    tabButtons.forEach(btn => {
        btn.addEventListener('click', function () {
            tabButtons.forEach(b => b.classList.remove('active'));
            this.classList.add('active');
            loadTab(this.dataset.section);
        });
    });
    // Carga inicial mejorada
    const initialTab = getTabFromUrl();
    tabButtons.forEach(b => b.classList.remove('active'));
    const btnToActivate = Array.from(tabButtons).find(btn => btn.dataset.section === initialTab);
    if (btnToActivate) {
        btnToActivate.classList.add('active');
        btnToActivate.click(); // Dispara el evento y carga el contenido correcto
    } else {
        loadTab(initialTab);
    }
}); 