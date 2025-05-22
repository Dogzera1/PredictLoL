# Script para deploy do projeto no Vercel e configuração do webhook do Telegram
# Autor: LoL-GPT Team
# Data: 20/05/2025

# Informações do projeto
$projectId = "prj_Qvtpg9WToma2XYM420jU480FAXUR"
$token = "7584060058:AAG-L6BJ5Y3Y74MadbGYhzSuiygJixrblNo"

# Mostrar mensagem de início
Write-Host "====================================" -ForegroundColor Green
Write-Host "DEPLOY DO BOT LOL-GPT PARA O VERCEL" -ForegroundColor Green
Write-Host "====================================" -ForegroundColor Green
Write-Host ""

# Verificar se o Vercel CLI está instalado
try {
    $vercelVersion = vercel --version
    Write-Host "Vercel CLI detectado: $vercelVersion" -ForegroundColor Green
} catch {
    Write-Host "Vercel CLI não encontrado. Por favor, instale com:" -ForegroundColor Red
    Write-Host "npm install -g vercel" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Se não tiver npm, instale o Node.js primeiro:" -ForegroundColor Yellow
    Write-Host "https://nodejs.org/en/download/" -ForegroundColor Yellow
    exit 1
}

# Iniciar o deploy
Write-Host "Iniciando o deploy para o Vercel..." -ForegroundColor Cyan
try {
    vercel --prod --yes
    if ($LASTEXITCODE -ne 0) {
        throw "Erro no comando vercel"
    }
    Write-Host "Deploy concluído com sucesso!" -ForegroundColor Green
} catch {
    Write-Host "Erro durante o deploy: $_" -ForegroundColor Red
    exit 1
}

# Obter URL do projeto
Write-Host "Tentando obter URL do projeto..." -ForegroundColor Cyan
try {
    $projectInfo = vercel project ls --json | ConvertFrom-Json
    $project = $projectInfo | Where-Object { $_.id -eq $projectId }
    
    if ($project) {
        $projectName = $project.name
        $baseUrl = "https://$projectName.vercel.app"
        Write-Host "URL do projeto: $baseUrl" -ForegroundColor Green
    } else {
        # Pedir ao usuário para fornecer o URL
        Write-Host "Não foi possível obter automaticamente o URL. Por favor, verifique no painel do Vercel." -ForegroundColor Yellow
        $baseUrl = Read-Host "Digite o URL do seu projeto Vercel (ex: https://lol-gpt-apostas-xxxx.vercel.app)"
    }
} catch {
    Write-Host "Erro ao obter URL do projeto: $_" -ForegroundColor Red
    $baseUrl = Read-Host "Digite o URL do seu projeto Vercel (ex: https://lol-gpt-apostas-xxxx.vercel.app)"
}

# Configurar webhook
Write-Host "Configurando webhook do Telegram..." -ForegroundColor Cyan
$webhookUrl = "$baseUrl/api/webhook"

try {
    $result = Invoke-RestMethod -Uri "https://api.telegram.org/bot$token/setWebhook" -Method Post -Body @{
        url = $webhookUrl
    }
    
    if ($result.ok) {
        Write-Host "Webhook configurado com sucesso!" -ForegroundColor Green
        Write-Host "URL do webhook: $webhookUrl" -ForegroundColor Green
    } else {
        Write-Host "Erro ao configurar webhook: $($result.description)" -ForegroundColor Red
    }
} catch {
    Write-Host "Erro ao configurar webhook: $_" -ForegroundColor Red
    Write-Host "Execute manualmente o comando:" -ForegroundColor Yellow
    Write-Host "Invoke-RestMethod -Uri 'https://api.telegram.org/bot$token/setWebhook' -Method Post -Body @{ url = '$webhookUrl' }" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "====================================" -ForegroundColor Green
Write-Host "PROCESSO DE DEPLOY FINALIZADO" -ForegroundColor Green
Write-Host "====================================" -ForegroundColor Green 