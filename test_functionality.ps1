# Script de prueba para funcionalidades del dashboard
# Ejecutar con: .\test_functionality.ps1

Write-Host "=== PRUEBA DE FUNCIONALIDADES DEL DASHBOARD ===" -ForegroundColor Green
Write-Host ""

# Función para mostrar resultados
function Show-Result {
    param(
        [string]$Test,
        [bool]$Success,
        [string]$Message = ""
    )
    
    if ($Success) {
        Write-Host "✓ $Test" -ForegroundColor Green
    } else {
        Write-Host "✗ $Test" -ForegroundColor Red
        if ($Message) {
            Write-Host "  Error: $Message" -ForegroundColor Yellow
        }
    }
}

# Función para verificar archivos
function Test-FileExists {
    param([string]$Path)
    return Test-Path $Path
}

# Función para verificar contenido de archivos
function Test-FileContent {
    param(
        [string]$Path,
        [string]$SearchText
    )
    if (Test-Path $Path) {
        $content = Get-Content $Path -Raw
        return $content -match $SearchText
    }
    return $false
}

Write-Host "1. Verificando archivos principales..." -ForegroundColor Cyan

# Verificar templates principales
$templates = @(
    "apps/users/templates/dashboards/dashboard_student.html",
    "apps/users/templates/dashboards/dashboard_teacher.html",
    "apps/users/templates/class/class_student.html",
    "apps/users/templates/class/class_teacher.html"
)

foreach ($template in $templates) {
    Show-Result "Template $template" (Test-FileExists $template)
}

Write-Host ""
Write-Host "2. Verificando archivos JavaScript..." -ForegroundColor Cyan

# Verificar archivos JavaScript
$jsFiles = @(
    "static/js/dashboard_student.js",
    "static/js/dashboard_teacher.js",
    "static/js/header_logged.js",
    "static/js/dashboard_ajax.js"
)

foreach ($jsFile in $jsFiles) {
    Show-Result "JavaScript $jsFile" (Test-FileExists $jsFile)
}

Write-Host ""
Write-Host "3. Verificando archivos CSS..." -ForegroundColor Cyan

# Verificar archivos CSS
$cssFiles = @(
    "static/css/dashboards/style_dashboard_student.css",
    "static/css/dashboards/style_dashboard_teacher.css",
    "static/css/dashboards/dashboard_optimized.css"
)

foreach ($cssFile in $cssFiles) {
    Show-Result "CSS $cssFile" (Test-FileExists $cssFile)
}

Write-Host ""
Write-Host "4. Verificando funcionalidades específicas..." -ForegroundColor Cyan

# Verificar funcionalidades en templates
if (Test-FileExists "apps/users/templates/dashboards/dashboard_student.html") {
    $studentContent = Get-Content "apps/users/templates/dashboards/dashboard_student.html" -Raw
    Show-Result "Dashboard estudiante - Modal de perfil" ($studentContent -match "showProfileModal")
    Show-Result "Dashboard estudiante - Unirse a clase" ($studentContent -match "showJoinClassForm")
    Show-Result "Dashboard estudiante - Avatar upload" ($studentContent -match "avatarInput")
}

if (Test-FileExists "apps/users/templates/dashboards/dashboard_teacher.html") {
    $teacherContent = Get-Content "apps/users/templates/dashboards/dashboard_teacher.html" -Raw
    Show-Result "Dashboard profesor - Modal de perfil" ($teacherContent -match "showProfileModal")
    Show-Result "Dashboard profesor - Crear curso" ($teacherContent -match "showCreateCourseModal")
    Show-Result "Dashboard profesor - Avatar upload" ($teacherContent -match "avatarInput")
}

Write-Host ""
Write-Host "5. Verificando funcionalidades de chat..." -ForegroundColor Cyan

# Verificar funcionalidades de chat
if (Test-FileExists "apps/users/templates/class/class_student.html") {
    $studentClassContent = Get-Content "apps/users/templates/class/class_student.html" -Raw
    Show-Result "Class student - Chat functionality" ($studentClassContent -match "addMessageToChat")
    Show-Result "Class student - AJAX chat" ($studentClassContent -match "fetch.*class_chat")
}

if (Test-FileExists "apps/users/templates/class/class_teacher.html") {
    $teacherClassContent = Get-Content "apps/users/templates/class/class_teacher.html" -Raw
    Show-Result "Class teacher - Chat functionality" ($teacherClassContent -match "addMessageToChat")
    Show-Result "Class teacher - AJAX chat" ($teacherClassContent -match "fetch.*class_chat")
}

Write-Host ""
Write-Host "6. Verificando URLs y endpoints..." -ForegroundColor Cyan

# Verificar archivos de URLs
$urlFiles = @(
    "apps/users/urls.py",
    "NatureIn/urls.py"
)

foreach ($urlFile in $urlFiles) {
    if (Test-FileExists $urlFile) {
        $urlContent = Get-Content $urlFile -Raw
        Show-Result "URLs en $urlFile" ($urlContent -match "dashboard|class|chat")
    }
}

Write-Host ""
Write-Host "7. Verificando vistas..." -ForegroundColor Cyan

# Verificar archivos de vistas
$viewFiles = @(
    "apps/users/views.py"
)

foreach ($viewFile in $viewFiles) {
    if (Test-FileExists $viewFile) {
        $viewContent = Get-Content $viewFile -Raw
        Show-Result "Vistas en $viewFile" ($viewContent -match "def.*dashboard|def.*class")
    }
}

Write-Host ""
Write-Host "8. Verificando modelos..." -ForegroundColor Cyan

# Verificar archivos de modelos
$modelFiles = @(
    "apps/users/models.py"
)

foreach ($modelFile in $modelFiles) {
    if (Test-FileExists $modelFile) {
        $modelContent = Get-Content $modelFile -Raw
        Show-Result "Modelos en $modelFile" ($modelContent -match "class.*User|class.*Aula")
    }
}

Write-Host ""
Write-Host "=== RESUMEN ===" -ForegroundColor Green

# Contar archivos encontrados
$totalTemplates = ($templates | Where-Object { Test-Path $_ }).Count
$totalJS = ($jsFiles | Where-Object { Test-Path $_ }).Count
$totalCSS = ($cssFiles | Where-Object { Test-Path $_ }).Count

Write-Host "Templates encontrados: $totalTemplates/$($templates.Count)" -ForegroundColor Cyan
Write-Host "Archivos JS encontrados: $totalJS/$($jsFiles.Count)" -ForegroundColor Cyan
Write-Host "Archivos CSS encontrados: $totalCSS/$($cssFiles.Count)" -ForegroundColor Cyan

Write-Host ""
Write-Host "=== INSTRUCCIONES PARA EJECUTAR ===" -ForegroundColor Yellow
Write-Host "1. Asegúrate de estar en el directorio raíz del proyecto" -ForegroundColor White
Write-Host "2. Ejecuta: python manage.py runserver" -ForegroundColor White
Write-Host "3. Abre http://localhost:8000 en tu navegador" -ForegroundColor White
Write-Host "4. Prueba las funcionalidades manualmente:" -ForegroundColor White
Write-Host "   - Login como estudiante y profesor" -ForegroundColor White
Write-Host "   - Acceder a los dashboards" -ForegroundColor White
Write-Host "   - Probar modales de perfil" -ForegroundColor White
Write-Host "   - Unirse a clases" -ForegroundColor White
Write-Host "   - Probar chat en las clases" -ForegroundColor White

Write-Host ""
Write-Host "Script completado!" -ForegroundColor Green 