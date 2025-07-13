Write-Host "=== VERIFICACION DE FUNCIONALIDADES ===" -ForegroundColor Green

# Verificar archivos principales
$files = @(
    "apps/users/templates/dashboards/dashboard_student.html",
    "apps/users/templates/dashboards/dashboard_teacher.html",
    "apps/users/templates/class/class_student.html",
    "apps/users/templates/class/class_teacher.html",
    "static/js/dashboard_student.js",
    "static/js/dashboard_teacher.js",
    "static/css/dashboards/style_dashboard_student.css",
    "static/css/dashboards/style_dashboard_teacher.css"
)

Write-Host "Verificando archivos..." -ForegroundColor Cyan
foreach ($file in $files) {
    if (Test-Path $file) {
        Write-Host "✓ $file" -ForegroundColor Green
    } else {
        Write-Host "✗ $file" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "=== RESUMEN ===" -ForegroundColor Yellow
$found = ($files | Where-Object { Test-Path $_ }).Count
Write-Host "Archivos encontrados: $found/$($files.Count)" -ForegroundColor Cyan

Write-Host ""
Write-Host "=== INSTRUCCIONES ===" -ForegroundColor Yellow
Write-Host "1. Ejecuta: python manage.py runserver" -ForegroundColor White
Write-Host "2. Abre: http://localhost:8000" -ForegroundColor White
Write-Host "3. Prueba los dashboards y funcionalidades" -ForegroundColor White 