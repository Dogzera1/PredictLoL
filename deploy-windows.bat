@echo off
setlocal EnableDelayedExpansion

REM 🚀 SCRIPT DE DEPLOY PARA WINDOWS - BOT LOL V3 ULTRA AVANÇADO
REM Versão: 3.1.0

title Bot LoL V3 - Deploy Windows

echo.
echo ████████████████████████████████████████
echo █  🚀 BOT LOL V3 DEPLOY WINDOWS  🚀   █
echo █        Ultra Avançado v3.1.0        █
echo ████████████████████████████████████████
echo.

REM Verificar se Docker está instalado
docker --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker não está instalado ou não está no PATH!
    echo.
    echo Baixe e instale Docker Desktop para Windows:
    echo https://www.docker.com/products/docker-desktop
    echo.
    pause
    exit /b 1
)

REM Verificar se Docker Compose está disponível
docker-compose --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker Compose não está disponível!
    echo.
    echo Certifique-se de que Docker Desktop está instalado e rodando.
    pause
    exit /b 1
)

echo [INFO] Docker encontrado ✓
echo [INFO] Docker Compose encontrado ✓
echo.

REM Verificar arquivo .env
if not exist ".env" (
    echo [WARNING] Arquivo .env não encontrado!
    if exist "env.example" (
        echo [INFO] Copiando env.example para .env...
        copy env.example .env >nul
        echo.
        echo [WARNING] Configure o arquivo .env antes de continuar!
        echo Abra o arquivo .env e configure:
        echo   - TELEGRAM_TOKEN
        echo   - ADMIN_USER_ID  
        echo   - REDIS_PASSWORD
        echo   - Outras configurações necessárias
        echo.
        pause
        exit /b 1
    ) else (
        echo [ERROR] Arquivo env.example também não encontrado!
        pause
        exit /b 1
    )
) else (
    echo [INFO] Arquivo .env encontrado ✓
)

REM Criar diretórios necessários
if not exist "data" mkdir data
if not exist "logs" mkdir logs
if not exist "backups" mkdir backups
if not exist "monitoring" mkdir monitoring
if not exist "nginx" mkdir nginx
if not exist "nginx\ssl" mkdir nginx\ssl

echo [INFO] Diretórios criados ✓

REM Verificar se há containers rodando
for /f %%i in ('docker ps -q') do set CONTAINERS_RUNNING=1
if defined CONTAINERS_RUNNING (
    echo [INFO] Parando containers existentes...
    docker-compose down
)

REM Processar argumentos
set COMMAND=%1
if "%COMMAND%"=="" set COMMAND=deploy

if "%COMMAND%"=="deploy" goto :deploy
if "%COMMAND%"=="stop" goto :stop
if "%COMMAND%"=="restart" goto :restart
if "%COMMAND%"=="logs" goto :logs
if "%COMMAND%"=="status" goto :status
if "%COMMAND%"=="backup" goto :backup
if "%COMMAND%"=="help" goto :help

echo [ERROR] Comando desconhecido: %COMMAND%
echo Use: %0 help
pause
exit /b 1

:deploy
echo [INFO] Iniciando deploy completo...
echo.

REM Backup automático antes do deploy
if exist "data" (
    echo [INFO] Fazendo backup dos dados...
    for /f "tokens=2-4 delims=/ " %%a in ('date /t') do (set mydate=%%c%%a%%b)
    for /f "tokens=1-2 delims=/:" %%a in ("%TIME%") do (set mytime=%%a%%b)
    set mytime=!mytime: =0!
    
    if exist "backups\backup_pre_deploy_!mydate!_!mytime!.zip" del "backups\backup_pre_deploy_!mydate!_!mytime!.zip"
    powershell -command "Compress-Archive -Path 'data' -DestinationPath 'backups\backup_pre_deploy_!mydate!_!mytime!.zip'" >nul 2>&1
    echo [INFO] Backup salvo ✓
)

REM Criar configuração Nginx se não existir
if not exist "nginx\nginx.conf" (
    echo [INFO] Criando configuração Nginx...
    (
        echo events {
        echo     worker_connections 1024;
        echo }
        echo.
        echo http {
        echo     upstream bot_backend {
        echo         server lol-bot:8080;
        echo     }
        echo.
        echo     server {
        echo         listen 80;
        echo         server_name _;
        echo.        
        echo         location /health {
        echo             proxy_pass http://bot_backend;
        echo             proxy_set_header Host $host;
        echo             proxy_set_header X-Real-IP $remote_addr;
        echo         }
        echo.        
        echo         location /metrics {
        echo             proxy_pass http://bot_backend;
        echo             proxy_set_header Host $host;
        echo             proxy_set_header X-Real-IP $remote_addr;
        echo         }
        echo.        
        echo         location / {
        echo             return 444;
        echo         }
        echo     }
        echo }
    ) > nginx\nginx.conf
    echo [INFO] Configuração Nginx criada ✓
)

REM Criar configuração Prometheus se não existir
if not exist "monitoring\prometheus.yml" (
    echo [INFO] Criando configuração Prometheus...
    (
        echo global:
        echo   scrape_interval: 15s
        echo.
        echo scrape_configs:
        echo   - job_name: 'lol-bot'
        echo     static_configs:
        echo       - targets: ['lol-bot:8080']
        echo     metrics_path: /metrics
        echo     scrape_interval: 30s
    ) > monitoring\prometheus.yml
    echo [INFO] Configuração Prometheus criada ✓
)

echo [INFO] Construindo imagens Docker...
docker-compose build --no-cache
if errorlevel 1 (
    echo [ERROR] Falha ao construir imagens!
    pause
    exit /b 1
)
echo [INFO] Imagens construídas ✓

echo [INFO] Iniciando serviços...
docker-compose up -d
if errorlevel 1 (
    echo [ERROR] Falha ao iniciar serviços!
    pause
    exit /b 1
)

echo [INFO] Aguardando serviços ficarem prontos...
timeout /t 30 /nobreak >nul

echo [INFO] Verificando saúde dos containers...
docker ps

echo.
echo [SUCCESS] 🎉 Deploy concluído com sucesso!
echo.
echo ████████████████████████████████████████
echo █       🚀 BOT LOL V3 ATIVO! 🚀       █
echo █     Monitoramento 24/7 ativo        █
echo ████████████████████████████████████████
echo.
echo [INFO] Acessos disponíveis:
echo   🤖 Bot: Container lol-predictor-v3
echo   📊 Prometheus: http://localhost:9090
echo   📈 Grafana: http://localhost:3000
echo   🗄️  Redis: localhost:6379
echo.
echo [INFO] Comandos úteis:
echo   Ver logs: %0 logs
echo   Status: %0 status
echo   Parar: %0 stop
echo   Restart: %0 restart
echo.
pause
goto :eof

:stop
echo [INFO] Parando todos os serviços...
docker-compose down
echo [SUCCESS] Serviços parados!
pause
goto :eof

:restart
echo [INFO] Reiniciando serviços...
docker-compose restart
echo [SUCCESS] Serviços reiniciados!
pause
goto :eof

:logs
echo [INFO] Mostrando logs do bot (Ctrl+C para sair)...
docker logs lol-predictor-v3 -f
goto :eof

:status
echo [INFO] Status dos serviços:
docker-compose ps
echo.
echo [INFO] Uso de recursos:
docker stats --no-stream
pause
goto :eof

:backup
echo [INFO] Criando backup manual...
for /f "tokens=2-4 delims=/ " %%a in ('date /t') do (set mydate=%%c%%a%%b)
for /f "tokens=1-2 delims=/:" %%a in ("%TIME%") do (set mytime=%%a%%b)
set mytime=!mytime: =0!

if exist "data" (
    powershell -command "Compress-Archive -Path 'data' -DestinationPath 'backups\manual_backup_!mydate!_!mytime!.zip'" >nul 2>&1
    echo [SUCCESS] Backup criado: backups\manual_backup_!mydate!_!mytime!.zip
) else (
    echo [WARNING] Diretório data não encontrado
)
pause
goto :eof

:help
echo Uso: %0 [comando]
echo.
echo Comandos disponíveis:
echo   deploy   - Deploy completo (padrão)
echo   stop     - Parar todos os serviços
echo   restart  - Reiniciar serviços
echo   logs     - Mostrar logs do bot
echo   status   - Mostrar status dos serviços
echo   backup   - Fazer backup manual
echo   help     - Mostrar esta ajuda
echo.
pause
goto :eof 