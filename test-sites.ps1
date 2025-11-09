# Скрипт тестирования сайтов и GitHub Pages
Write-Host "🧪 Тестирование сайтов Faceit Stats Bot" -ForegroundColor Cyan
Write-Host "=" * 60

# Функция для проверки URL
function Test-Url {
    param(
        [string]$Url,
        [string]$Name
    )
    
    Write-Host "`n📍 Проверка: $Name" -ForegroundColor Yellow
    Write-Host "   URL: $Url"
    
    try {
        $response = Invoke-WebRequest -Uri $Url -Method Get -UseBasicParsing -TimeoutSec 10 -ErrorAction Stop
        $statusCode = $response.StatusCode
        
        if ($statusCode -eq 200) {
            Write-Host "   ✅ Статус: $statusCode OK" -ForegroundColor Green
            Write-Host "   📦 Размер: $($response.RawContentLength) bytes"
            
            # Проверка содержимого
            $content = $response.Content
            if ($content -match "Faceit") {
                Write-Host "   ✅ Содержит 'Faceit'" -ForegroundColor Green
            }
            if ($content -match "Stats Bot") {
                Write-Host "   ✅ Содержит 'Stats Bot'" -ForegroundColor Green
            }
            
            return $true
        } else {
            Write-Host "   ⚠️  Статус: $statusCode" -ForegroundColor Yellow
            return $false
        }
    }
    catch {
        Write-Host "   ❌ Ошибка: $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
}

# Тестирование сайтов
$results = @{}

# 1. GitHub Pages
$results["GitHub Pages"] = Test-Url -Url "https://pat1one.github.io/faceit-ai-bot/" -Name "GitHub Pages"

# 2. Главный сайт
Write-Host "`n📍 Проверка: Главный сайт (pattmsc.online)" -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "https://pattmsc.online" -UseBasicParsing -TimeoutSec 10 -ErrorAction Stop
    Write-Host "   ✅ Сайт доступен (Статус: $($response.StatusCode))" -ForegroundColor Green
    $results["Главный сайт"] = $true
}
catch {
    if ($_.Exception.Message -match "403") {
        Write-Host "   ⚠️  Статус 403: Сайт работает, но доступ ограничен (возможно Cloudflare)" -ForegroundColor Yellow
        $results["Главный сайт"] = $true
    } else {
        Write-Host "   ❌ Ошибка: $($_.Exception.Message)" -ForegroundColor Red
        $results["Главный сайт"] = $false
    }
}

# 3. API
Write-Host "`n📍 Проверка: API (api.pattmsc.online)" -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "https://api.pattmsc.online/docs" -UseBasicParsing -TimeoutSec 10 -ErrorAction Stop
    Write-Host "   ✅ API доступен (Статус: $($response.StatusCode))" -ForegroundColor Green
    $results["API"] = $true
}
catch {
    Write-Host "   ❌ API недоступен: $($_.Exception.Message)" -ForegroundColor Red
    $results["API"] = $false
}

# 4. Проверка downloads
Write-Host "`n📍 Проверка: Downloads" -ForegroundColor Yellow
$downloadFiles = @(
    "faceit-ai-bot-chrome.zip",
    "faceit-ai-bot-firefox.xpi",
    "faceit-ai-bot-docker.tar.gz"
)

$downloadsOk = 0
foreach ($file in $downloadFiles) {
    $url = "https://pattmsc.online/downloads/$file"
    try {
        $response = Invoke-WebRequest -Uri $url -Method Head -UseBasicParsing -TimeoutSec 5 -ErrorAction Stop
        Write-Host "   ✅ $file доступен" -ForegroundColor Green
        $downloadsOk++
    }
    catch {
        Write-Host "   ⚠️  $file не найден" -ForegroundColor Yellow
    }
}

# 5. Проверка GitHub Release
Write-Host "`n📍 Проверка: GitHub Release v0.2.0" -ForegroundColor Yellow
try {
    $releaseUrl = "https://api.github.com/repos/pat1one/faceit-ai-bot/releases/tags/v0.2.0"
    $response = Invoke-WebRequest -Uri $releaseUrl -UseBasicParsing -TimeoutSec 10 -ErrorAction Stop
    $releaseData = $response.Content | ConvertFrom-Json
    $assetsCount = $releaseData.assets.Count
    Write-Host "   ✅ Релиз v0.2.0 существует" -ForegroundColor Green
    Write-Host "   📦 Артефактов: $assetsCount" -ForegroundColor Cyan
    $results["GitHub Release"] = $true
}
catch {
    Write-Host "   ⚠️  Релиз v0.2.0 не найден" -ForegroundColor Yellow
    $results["GitHub Release"] = $false
}

# 6. Проверка Docker образов
Write-Host "`n📍 Проверка: Docker Images (ghcr.io)" -ForegroundColor Yellow

# Проверка API образа
try {
    $apiImageUrl = "https://ghcr.io/v2/pat1one/faceit-ai-bot/api/manifests/latest"
    $response = Invoke-WebRequest -Uri $apiImageUrl -Method Head -UseBasicParsing -TimeoutSec 10 -ErrorAction Stop
    Write-Host "   ✅ API образ (ghcr.io/pat1one/faceit-ai-bot/api:latest)" -ForegroundColor Green
    $results["Docker API"] = $true
}
catch {
    Write-Host "   ⚠️  API образ не найден" -ForegroundColor Yellow
    $results["Docker API"] = $false
}

# Проверка Web образа
try {
    $webImageUrl = "https://ghcr.io/v2/pat1one/faceit-ai-bot/web/manifests/latest"
    $response = Invoke-WebRequest -Uri $webImageUrl -Method Head -UseBasicParsing -TimeoutSec 10 -ErrorAction Stop
    Write-Host "   ✅ Web образ (ghcr.io/pat1one/faceit-ai-bot/web:latest)" -ForegroundColor Green
    $results["Docker Web"] = $true
}
catch {
    Write-Host "   ⚠️  Web образ не найден" -ForegroundColor Yellow
    $results["Docker Web"] = $false
}

# Итоги
Write-Host "`n" + ("=" * 60)
Write-Host "📊 ИТОГИ ТЕСТИРОВАНИЯ" -ForegroundColor Cyan
Write-Host ("=" * 60)

$totalTests = $results.Count
$passedTests = ($results.Values | Where-Object { $_ -eq $true }).Count

foreach ($test in $results.GetEnumerator()) {
    $status = if ($test.Value) { "✅ OK" } else { "❌ FAIL" }
    $color = if ($test.Value) { "Green" } else { "Red" }
    Write-Host "$status - $($test.Key)" -ForegroundColor $color
}

Write-Host "`n📈 Результат: $passedTests/$totalTests тестов пройдено"

if ($downloadsOk -gt 0) {
    Write-Host "📥 Downloads: $downloadsOk/$($downloadFiles.Count) файлов доступно" -ForegroundColor Cyan
}

# Процент успеха
if ($totalTests -gt 0) {
    $percentage = [math]::Round(($passedTests / $totalTests) * 100)
    Write-Host "✨ Успешность: $percentage%" -ForegroundColor Cyan
}

Write-Host ""
if ($passedTests -eq $totalTests) {
    Write-Host "🎉 Все тесты пройдены успешно!" -ForegroundColor Green
} elseif ($passedTests -gt 0) {
    Write-Host "⚠️  Некоторые тесты не прошли" -ForegroundColor Yellow
} else {
    Write-Host "❌ Все тесты провалены" -ForegroundColor Red
}

Write-Host "`n✅ Тестирование завершено!`n"
