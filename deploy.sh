#!/bin/bash

# 🚀 SCRIPT DE DEPLOY AUTOMÁTICO - BOT LOL V3 ULTRA AVANÇADO
# Versão: 3.1.0
# Autor: Bot LoL V3 Team

set -e  # Parar execução em caso de erro

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Funções de log
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Banner
echo -e "${BLUE}"
echo "████████████████████████████████████████"
echo "█  🚀 BOT LOL V3 DEPLOY AUTOMÁTICO  █"
echo "█        Ultra Avançado v3.1.0        █"
echo "████████████████████████████████████████"
echo -e "${NC}"

# Configurações
APP_NAME="lol-predictor-v3"
BACKUP_DIR="./backups"
LOG_DIR="./logs"
DATA_DIR="./data"

# Verificar se está executando como root
if [[ $EUID -eq 0 ]]; then
   log_error "Este script não deve ser executado como root!"
   exit 1
fi

# Função para verificar dependências
check_dependencies() {
    log_info "Verificando dependências..."
    
    dependencies=("docker" "docker-compose" "git" "curl")
    for dep in "${dependencies[@]}"; do
        if ! command -v $dep &> /dev/null; then
            log_error "$dep não está instalado!"
            echo "Instale com: sudo apt update && sudo apt install -y $dep"
            exit 1
        else
            log_success "$dep ✓"
        fi
    done
}

# Função para verificar arquivo .env
check_env_file() {
    log_info "Verificando arquivo .env..."
    
    if [ ! -f ".env" ]; then
        log_warning "Arquivo .env não encontrado!"
        if [ -f "env.example" ]; then
            log_info "Copiando env.example para .env..."
            cp env.example .env
            log_warning "Configure o arquivo .env antes de continuar!"
            echo "Abra o arquivo .env e configure suas credenciais:"
            echo "  - TELEGRAM_TOKEN"
            echo "  - ADMIN_USER_ID"
            echo "  - REDIS_PASSWORD"
            echo "  - Outras configurações necessárias"
            exit 1
        else
            log_error "Arquivo env.example também não encontrado!"
            exit 1
        fi
    else
        log_success "Arquivo .env encontrado ✓"
    fi
    
    # Verificar se variáveis essenciais estão configuradas
    source .env
    if [ -z "$TELEGRAM_TOKEN" ] || [ "$TELEGRAM_TOKEN" = "sua_api_key_do_telegram_aqui" ]; then
        log_error "TELEGRAM_TOKEN não configurado no .env!"
        exit 1
    fi
}

# Função para criar diretórios necessários
create_directories() {
    log_info "Criando diretórios necessários..."
    
    directories=("$BACKUP_DIR" "$LOG_DIR" "$DATA_DIR" "monitoring" "nginx/ssl")
    for dir in "${directories[@]}"; do
        if [ ! -d "$dir" ]; then
            mkdir -p "$dir"
            log_success "Diretório $dir criado ✓"
        fi
    done
}

# Função para fazer backup antes do deploy
backup_data() {
    if [ -d "$DATA_DIR" ] && [ "$(ls -A $DATA_DIR)" ]; then
        log_info "Fazendo backup dos dados..."
        timestamp=$(date +"%Y%m%d_%H%M%S")
        backup_file="$BACKUP_DIR/backup_pre_deploy_$timestamp.tar.gz"
        tar -czf "$backup_file" "$DATA_DIR" 2>/dev/null || true
        log_success "Backup salvo em: $backup_file"
    fi
}

# Função para parar serviços
stop_services() {
    log_info "Parando serviços..."
    
    if docker-compose ps | grep -q "Up"; then
        docker-compose down
        log_success "Serviços parados ✓"
    else
        log_info "Nenhum serviço ativo encontrado"
    fi
}

# Função para construir imagens
build_images() {
    log_info "Construindo imagens Docker..."
    
    # Limpar imagens antigas (opcional)
    read -p "Deseja limpar imagens antigas? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        log_info "Limpando imagens antigas..."
        docker system prune -f
        docker image prune -f
    fi
    
    # Construir nova imagem
    docker-compose build --no-cache
    log_success "Imagens construídas ✓"
}

# Função para configurar Nginx
setup_nginx() {
    log_info "Configurando Nginx..."
    
    if [ ! -f "nginx/nginx.conf" ]; then
        log_info "Criando configuração do Nginx..."
        cat > nginx/nginx.conf << 'EOF'
events {
    worker_connections 1024;
}

http {
    upstream bot_backend {
        server lol-bot:8080;
    }

    server {
        listen 80;
        server_name _;
        
        location /health {
            proxy_pass http://bot_backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
        }
        
        location /metrics {
            proxy_pass http://bot_backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
        }
        
        location / {
            return 444;  # Bloquear outras requisições
        }
    }
}
EOF
        log_success "Configuração Nginx criada ✓"
    fi
}

# Função para configurar monitoramento
setup_monitoring() {
    log_info "Configurando monitoramento..."
    
    # Prometheus config
    if [ ! -f "monitoring/prometheus.yml" ]; then
        cat > monitoring/prometheus.yml << 'EOF'
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'lol-bot'
    static_configs:
      - targets: ['lol-bot:8080']
    metrics_path: /metrics
    scrape_interval: 30s
EOF
        log_success "Configuração Prometheus criada ✓"
    fi
}

# Função para iniciar serviços
start_services() {
    log_info "Iniciando serviços..."
    
    docker-compose up -d
    
    # Aguardar serviços ficarem prontos
    log_info "Aguardando serviços ficarem prontos..."
    sleep 30
    
    # Verificar health dos containers
    containers=("lol-predictor-v3" "lol-redis" "lol-nginx")
    for container in "${containers[@]}"; do
        if docker ps | grep -q "$container"; then
            log_success "$container está rodando ✓"
        else
            log_error "$container falhou ao iniciar!"
            docker logs "$container" 2>/dev/null || true
        fi
    done
}

# Função para verificar saúde do sistema
health_check() {
    log_info "Executando verificações de saúde..."
    
    # Verificar se bot responde
    if curl -f http://localhost:8080/health &>/dev/null; then
        log_success "Bot está respondendo ✓"
    else
        log_warning "Bot não está respondendo na porta 8080"
    fi
    
    # Verificar Redis
    if docker exec lol-redis redis-cli ping &>/dev/null; then
        log_success "Redis está funcionando ✓"
    else
        log_warning "Redis não está respondendo"
    fi
    
    # Verificar logs por erros
    if docker logs lol-predictor-v3 2>&1 | grep -i error | tail -5; then
        log_warning "Erros encontrados nos logs (últimos 5):"
    fi
}

# Função para mostrar status dos serviços
show_status() {
    log_info "Status dos serviços:"
    docker-compose ps
    
    echo
    log_info "Acessos disponíveis:"
    echo "  🤖 Bot: Container lol-predictor-v3"
    echo "  📊 Prometheus: http://localhost:9090"
    echo "  📈 Grafana: http://localhost:3000 (admin/senha_definida_no_env)"
    echo "  🗄️  Redis: localhost:6379"
    echo "  📋 Logs: docker logs lol-predictor-v3 -f"
}

# Função para cleanup em caso de erro
cleanup_on_error() {
    log_error "Deploy falhou! Executando cleanup..."
    docker-compose down 2>/dev/null || true
    log_info "Cleanup concluído"
}

# Função principal
main() {
    log_info "Iniciando deploy do Bot LoL V3..."
    
    # Trap para cleanup em caso de erro
    trap cleanup_on_error ERR
    
    # Executar etapas do deploy
    check_dependencies
    check_env_file
    create_directories
    backup_data
    stop_services
    setup_nginx
    setup_monitoring
    build_images
    start_services
    health_check
    show_status
    
    echo
    log_success "🎉 Deploy concluído com sucesso!"
    echo -e "${GREEN}"
    echo "████████████████████████████████████████"
    echo "█       🚀 BOT LOL V3 ATIVO! 🚀       █"
    echo "█     Monitoramento 24/7 ativo        █"
    echo "████████████████████████████████████████"
    echo -e "${NC}"
    
    log_info "Para acompanhar logs: docker logs lol-predictor-v3 -f"
    log_info "Para parar: docker-compose down"
    log_info "Para atualizar: ./deploy.sh"
}

# Verificar argumentos
case "${1:-deploy}" in
    "deploy")
        main
        ;;
    "stop")
        log_info "Parando todos os serviços..."
        docker-compose down
        log_success "Serviços parados!"
        ;;
    "restart")
        log_info "Reiniciando serviços..."
        docker-compose restart
        log_success "Serviços reiniciados!"
        ;;
    "logs")
        docker logs lol-predictor-v3 -f
        ;;
    "status")
        show_status
        ;;
    "backup")
        backup_data
        ;;
    "help")
        echo "Uso: $0 [comando]"
        echo "Comandos:"
        echo "  deploy   - Deploy completo (padrão)"
        echo "  stop     - Parar todos os serviços"
        echo "  restart  - Reiniciar serviços"
        echo "  logs     - Mostrar logs do bot"
        echo "  status   - Mostrar status dos serviços"
        echo "  backup   - Fazer backup manual"
        echo "  help     - Mostrar esta ajuda"
        ;;
    *)
        log_error "Comando desconhecido: $1"
        log_info "Use: $0 help"
        exit 1
        ;;
esac 