#!/bin/bash

# 🔧 CONFIGURAÇÃO SYSTEMD SERVICE - BOT LOL V3
# Este script configura o bot como serviço do sistema

set -e

# Cores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Verificar se está executando como root
if [[ $EUID -ne 0 ]]; then
   log_error "Este script deve ser executado como root (sudo)!"
   exit 1
fi

# Configurações
SERVICE_NAME="lol-bot-v3"
WORK_DIR="/opt/lol-bot-v3"
USER="lolbot"
GROUP="lolbot"

echo -e "${BLUE}"
echo "████████████████████████████████████████"
echo "█   🔧 SYSTEMD SERVICE SETUP  🔧     █"
echo "█       Bot LoL V3 Ultra             █"
echo "████████████████████████████████████████"
echo -e "${NC}"

# Função para criar usuário do sistema
create_system_user() {
    log_info "Criando usuário do sistema..."
    
    if ! id "$USER" &>/dev/null; then
        useradd --system --home-dir "$WORK_DIR" --shell /bin/bash "$USER"
        log_success "Usuário $USER criado ✓"
    else
        log_info "Usuário $USER já existe"
    fi
    
    # Criar grupo se não existir
    if ! getent group "$GROUP" &>/dev/null; then
        groupadd "$GROUP"
        usermod -a -G "$GROUP" "$USER"
        log_success "Grupo $GROUP criado ✓"
    fi
}

# Função para configurar diretórios
setup_directories() {
    log_info "Configurando diretórios..."
    
    # Criar diretório de trabalho
    mkdir -p "$WORK_DIR"/{data,logs,backups}
    
    # Configurar permissões
    chown -R "$USER:$GROUP" "$WORK_DIR"
    chmod 755 "$WORK_DIR"
    chmod 755 "$WORK_DIR"/{data,logs,backups}
    
    log_success "Diretórios configurados ✓"
}

# Função para criar arquivo de serviço systemd
create_systemd_service() {
    log_info "Criando serviço systemd..."
    
    cat > "/etc/systemd/system/${SERVICE_NAME}.service" << EOF
[Unit]
Description=Bot LoL V3 Ultra Avançado - Predições eSports
After=network.target network-online.target
Wants=network-online.target
StartLimitIntervalSec=300
StartLimitBurst=5

[Service]
Type=simple
User=$USER
Group=$GROUP
WorkingDirectory=$WORK_DIR
ExecStart=/usr/bin/python3 $WORK_DIR/main_v3_riot_integrated.py
ExecReload=/bin/kill -HUP \$MAINPID
KillMode=mixed
KillSignal=SIGINT
TimeoutStopSec=30
Restart=always
RestartSec=10

# Configurações de segurança
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=$WORK_DIR
ProtectKernelTunables=true
ProtectKernelModules=true
ProtectControlGroups=true

# Configurações de recursos
MemoryMax=1G
CPUQuota=50%

# Variáveis de ambiente
Environment=PYTHONPATH=$WORK_DIR
Environment=PYTHONUNBUFFERED=1
Environment=ENVIRONMENT=production
EnvironmentFile=$WORK_DIR/.env

# Logging
StandardOutput=journal
StandardError=journal
SyslogIdentifier=lol-bot-v3

[Install]
WantedBy=multi-user.target
EOF

    log_success "Serviço systemd criado ✓"
}

# Função para criar script de log rotation
create_logrotate() {
    log_info "Configurando rotação de logs..."
    
    cat > "/etc/logrotate.d/${SERVICE_NAME}" << EOF
$WORK_DIR/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 $USER $GROUP
    postrotate
        systemctl reload $SERVICE_NAME || true
    endscript
}
EOF

    log_success "Logrotate configurado ✓"
}

# Função para criar script de backup automático
create_backup_script() {
    log_info "Criando script de backup automático..."
    
    cat > "/usr/local/bin/${SERVICE_NAME}-backup.sh" << EOF
#!/bin/bash
# Backup automático do Bot LoL V3

BACKUP_DIR="$WORK_DIR/backups"
DATA_DIR="$WORK_DIR/data"
TIMESTAMP=\$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="\$BACKUP_DIR/auto_backup_\$TIMESTAMP.tar.gz"

# Criar backup
if [ -d "\$DATA_DIR" ] && [ "\$(ls -A \$DATA_DIR)" ]; then
    tar -czf "\$BACKUP_FILE" "\$DATA_DIR" 2>/dev/null
    echo "Backup criado: \$BACKUP_FILE"
    
    # Manter apenas últimos 7 backups
    find "\$BACKUP_DIR" -name "auto_backup_*.tar.gz" -type f -mtime +7 -delete
    echo "Backups antigos removidos"
else
    echo "Nenhum dado para backup"
fi
EOF

    chmod +x "/usr/local/bin/${SERVICE_NAME}-backup.sh"
    chown "$USER:$GROUP" "/usr/local/bin/${SERVICE_NAME}-backup.sh"
    
    log_success "Script de backup criado ✓"
}

# Função para configurar cron job
setup_cron() {
    log_info "Configurando backup automático (cron)..."
    
    # Criar cron job para backup diário às 2h
    cat > "/etc/cron.d/${SERVICE_NAME}-backup" << EOF
# Backup automático do Bot LoL V3 - diário às 2h
0 2 * * * $USER /usr/local/bin/${SERVICE_NAME}-backup.sh >> $WORK_DIR/logs/backup.log 2>&1
EOF

    log_success "Cron job configurado ✓"
}

# Função para criar script de monitoramento
create_monitoring_script() {
    log_info "Criando script de monitoramento..."
    
    cat > "/usr/local/bin/${SERVICE_NAME}-monitor.sh" << EOF
#!/bin/bash
# Monitoramento do Bot LoL V3

SERVICE="$SERVICE_NAME"
LOG_FILE="$WORK_DIR/logs/monitor.log"

# Função de log
log_message() {
    echo "\$(date '+%Y-%m-%d %H:%M:%S') - \$1" >> "\$LOG_FILE"
}

# Verificar se serviço está rodando
if ! systemctl is-active --quiet "\$SERVICE"; then
    log_message "ALERTA: Serviço \$SERVICE não está ativo! Tentando reiniciar..."
    systemctl restart "\$SERVICE"
    
    sleep 10
    
    if systemctl is-active --quiet "\$SERVICE"; then
        log_message "Serviço \$SERVICE reiniciado com sucesso"
    else
        log_message "ERRO: Falha ao reiniciar serviço \$SERVICE"
    fi
else
    log_message "Serviço \$SERVICE está funcionando normalmente"
fi

# Verificar uso de memória
MEMORY_USAGE=\$(systemctl show "\$SERVICE" --property=MemoryCurrent --value)
if [ "\$MEMORY_USAGE" -gt 1073741824 ]; then  # 1GB
    log_message "AVISO: Alto uso de memória: \$((\$MEMORY_USAGE / 1024 / 1024))MB"
fi
EOF

    chmod +x "/usr/local/bin/${SERVICE_NAME}-monitor.sh"
    
    # Cron job para monitoramento a cada 5 minutos
    cat > "/etc/cron.d/${SERVICE_NAME}-monitor" << EOF
# Monitoramento do Bot LoL V3 - a cada 5 minutos
*/5 * * * * root /usr/local/bin/${SERVICE_NAME}-monitor.sh
EOF

    log_success "Script de monitoramento criado ✓"
}

# Função para instalar dependências
install_dependencies() {
    log_info "Instalando dependências..."
    
    # Atualizar sistema
    apt update
    
    # Instalar Python e pip se não estiverem instalados
    apt install -y python3 python3-pip python3-venv
    
    # Instalar outras dependências úteis
    apt install -y curl wget git htop
    
    log_success "Dependências instaladas ✓"
}

# Função para configurar firewall (opcional)
setup_firewall() {
    if command -v ufw &> /dev/null; then
        log_info "Configurando firewall UFW..."
        
        # Permitir SSH
        ufw allow ssh
        
        # Permitir portas do monitoramento (opcional)
        ufw allow 9090  # Prometheus
        ufw allow 3000  # Grafana
        
        log_success "Firewall configurado ✓"
    else
        log_info "UFW não instalado, pulando configuração de firewall"
    fi
}

# Função principal
main() {
    log_info "Iniciando configuração do serviço systemd..."
    
    install_dependencies
    create_system_user
    setup_directories
    create_systemd_service
    create_logrotate
    create_backup_script
    setup_cron
    create_monitoring_script
    setup_firewall
    
    # Recarregar systemd
    systemctl daemon-reload
    
    log_success "🎉 Configuração concluída!"
    echo
    echo -e "${GREEN}████████████████████████████████████████"
    echo "█     🔧 SYSTEMD CONFIGURADO! 🔧     █"
    echo "████████████████████████████████████████${NC}"
    echo
    
    log_info "Próximos passos:"
    echo "1. Copie os arquivos do bot para: $WORK_DIR"
    echo "2. Configure o arquivo .env em: $WORK_DIR/.env"
    echo "3. Instale dependências Python:"
    echo "   cd $WORK_DIR && pip3 install -r requirements_production.txt"
    echo "4. Inicie o serviço:"
    echo "   sudo systemctl start $SERVICE_NAME"
    echo "   sudo systemctl enable $SERVICE_NAME"
    echo
    
    log_info "Comandos úteis:"
    echo "• Status: sudo systemctl status $SERVICE_NAME"
    echo "• Logs: sudo journalctl -u $SERVICE_NAME -f"
    echo "• Restart: sudo systemctl restart $SERVICE_NAME"
    echo "• Stop: sudo systemctl stop $SERVICE_NAME"
    echo "• Backup manual: sudo /usr/local/bin/${SERVICE_NAME}-backup.sh"
}

# Verificar argumentos
case "${1:-install}" in
    "install")
        main
        ;;
    "uninstall")
        log_info "Removendo serviço..."
        systemctl stop "$SERVICE_NAME" 2>/dev/null || true
        systemctl disable "$SERVICE_NAME" 2>/dev/null || true
        rm -f "/etc/systemd/system/${SERVICE_NAME}.service"
        rm -f "/etc/logrotate.d/${SERVICE_NAME}"
        rm -f "/usr/local/bin/${SERVICE_NAME}-backup.sh"
        rm -f "/usr/local/bin/${SERVICE_NAME}-monitor.sh"
        rm -f "/etc/cron.d/${SERVICE_NAME}-backup"
        rm -f "/etc/cron.d/${SERVICE_NAME}-monitor"
        systemctl daemon-reload
        log_success "Serviço removido!"
        ;;
    "help")
        echo "Uso: $0 [comando]"
        echo "Comandos:"
        echo "  install   - Instalar e configurar serviço (padrão)"
        echo "  uninstall - Remover serviço"
        echo "  help      - Mostrar esta ajuda"
        ;;
    *)
        log_error "Comando desconhecido: $1"
        exit 1
        ;;
esac 