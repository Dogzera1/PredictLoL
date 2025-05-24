#!/bin/bash

# 🌐 SCRIPT DE CONFIGURAÇÃO RÁPIDA PARA VPS - BOT LOL V3
# Este script configura automaticamente um VPS do zero para o bot

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

# Banner
echo -e "${BLUE}"
echo "████████████████████████████████████████"
echo "█  🌐 SETUP VPS AUTOMÁTICO  🌐       █"
echo "█       Bot LoL V3 Ultra             █"
echo "████████████████████████████████████████"
echo -e "${NC}"

# Detectar sistema operacional
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$NAME
    VER=$VERSION_ID
else
    log_error "Não foi possível detectar o sistema operacional"
    exit 1
fi

log_info "Sistema detectado: $OS $VER"

# Atualizar sistema
update_system() {
    log_info "Atualizando sistema..."
    
    if [[ "$OS" == *"Ubuntu"* ]] || [[ "$OS" == *"Debian"* ]]; then
        export DEBIAN_FRONTEND=noninteractive
        apt update && apt upgrade -y
        apt install -y curl wget git unzip htop nano ufw
    elif [[ "$OS" == *"CentOS"* ]] || [[ "$OS" == *"Red Hat"* ]]; then
        yum update -y
        yum install -y curl wget git unzip htop nano firewalld
    else
        log_warning "Sistema não testado, tentando instalação universal..."
    fi
    
    log_success "Sistema atualizado ✓"
}

# Instalar Docker
install_docker() {
    log_info "Instalando Docker..."
    
    # Remover instalações antigas
    if [[ "$OS" == *"Ubuntu"* ]] || [[ "$OS" == *"Debian"* ]]; then
        apt remove -y docker docker-engine docker.io containerd runc 2>/dev/null || true
    fi
    
    # Instalar Docker
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    rm get-docker.sh
    
    # Adicionar usuário atual ao grupo docker
    usermod -aG docker $USER 2>/dev/null || true
    
    # Instalar Docker Compose
    COMPOSE_VERSION=$(curl -s https://api.github.com/repos/docker/compose/releases/latest | grep tag_name | cut -d '"' -f 4)
    curl -L "https://github.com/docker/compose/releases/download/${COMPOSE_VERSION}/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
    
    # Iniciar Docker
    systemctl enable docker
    systemctl start docker
    
    log_success "Docker instalado ✓"
}

# Configurar firewall
setup_firewall() {
    log_info "Configurando firewall..."
    
    if command -v ufw >/dev/null 2>&1; then
        # Ubuntu/Debian UFW
        ufw --force reset
        ufw default deny incoming
        ufw default allow outgoing
        ufw allow ssh
        ufw allow 80
        ufw allow 443
        ufw allow 9090  # Prometheus
        ufw allow 3000  # Grafana
        ufw --force enable
        log_success "UFW configurado ✓"
    elif command -v firewall-cmd >/dev/null 2>&1; then
        # CentOS/RHEL firewalld
        systemctl enable firewalld
        systemctl start firewalld
        firewall-cmd --permanent --add-service=ssh
        firewall-cmd --permanent --add-service=http
        firewall-cmd --permanent --add-service=https
        firewall-cmd --permanent --add-port=9090/tcp
        firewall-cmd --permanent --add-port=3000/tcp
        firewall-cmd --reload
        log_success "Firewalld configurado ✓"
    else
        log_warning "Firewall não configurado - configure manualmente"
    fi
}

# Configurar swap (se necessário)
setup_swap() {
    # Verificar se já tem swap
    if free | awk '/^Swap:/ {exit !$2}'; then
        log_info "Swap já configurado"
        return
    fi
    
    log_info "Configurando swap (2GB)..."
    
    # Criar arquivo de swap
    fallocate -l 2G /swapfile || dd if=/dev/zero of=/swapfile bs=1024 count=2097152
    chmod 600 /swapfile
    mkswap /swapfile
    swapon /swapfile
    
    # Adicionar ao fstab
    echo '/swapfile none swap sw 0 0' >> /etc/fstab
    
    # Configurar swappiness
    echo 'vm.swappiness=10' >> /etc/sysctl.conf
    
    log_success "Swap configurado ✓"
}

# Otimizar sistema
optimize_system() {
    log_info "Otimizando sistema..."
    
    # Limites de arquivos
    cat >> /etc/security/limits.conf << EOF
* soft nofile 65536
* hard nofile 65536
* soft nproc 32768
* hard nproc 32768
EOF

    # Parâmetros de rede
    cat >> /etc/sysctl.conf << EOF
net.core.somaxconn = 32768
net.ipv4.tcp_max_syn_backlog = 32768
net.core.netdev_max_backlog = 32768
net.ipv4.tcp_fin_timeout = 10
EOF

    sysctl -p 2>/dev/null || true
    
    log_success "Sistema otimizado ✓"
}

# Instalar dependências adicionais
install_dependencies() {
    log_info "Instalando dependências adicionais..."
    
    if [[ "$OS" == *"Ubuntu"* ]] || [[ "$OS" == *"Debian"* ]]; then
        apt install -y \
            python3 \
            python3-pip \
            python3-venv \
            nginx \
            redis-server \
            fail2ban \
            logrotate \
            cron \
            certbot
    elif [[ "$OS" == *"CentOS"* ]] || [[ "$OS" == *"Red Hat"* ]]; then
        yum install -y \
            python3 \
            python3-pip \
            nginx \
            redis \
            fail2ban \
            logrotate \
            cronie
    fi
    
    log_success "Dependências instaladas ✓"
}

# Configurar usuário para o bot
create_bot_user() {
    log_info "Criando usuário para o bot..."
    
    # Criar usuário se não existir
    if ! id "botuser" &>/dev/null; then
        useradd -m -s /bin/bash botuser
        usermod -aG docker botuser
        log_success "Usuário botuser criado ✓"
    else
        log_info "Usuário botuser já existe"
    fi
    
    # Criar diretório de trabalho
    mkdir -p /home/botuser/lol-bot-v3
    chown -R botuser:botuser /home/botuser/lol-bot-v3
}

# Configurar SSH (segurança)
secure_ssh() {
    log_info "Configurando SSH para segurança..."
    
    # Backup da configuração original
    cp /etc/ssh/sshd_config /etc/ssh/sshd_config.backup
    
    # Configurações de segurança
    sed -i 's/^#Port 22/Port 22/' /etc/ssh/sshd_config
    sed -i 's/^PermitRootLogin yes/PermitRootLogin no/' /etc/ssh/sshd_config
    sed -i 's/^#PasswordAuthentication yes/PasswordAuthentication yes/' /etc/ssh/sshd_config
    
    # Reiniciar SSH
    systemctl restart sshd || systemctl restart ssh
    
    log_success "SSH configurado ✓"
}

# Baixar e configurar bot
setup_bot() {
    log_info "Baixando Bot LoL V3..."
    
    # Mudar para usuário botuser
    cd /home/botuser
    
    # Clonar repositório (você deve substituir pela URL correta)
    if [ ! -d "lol-bot-v3" ]; then
        # Para este exemplo, vamos criar a estrutura
        mkdir -p lol-bot-v3
        cd lol-bot-v3
        
        # Criar estrutura básica
        mkdir -p {data,logs,backups,monitoring,nginx/ssl}
        
        log_info "Estrutura do bot criada. Clone seu repositório manualmente:"
        log_info "cd /home/botuser && git clone SEU_REPOSITORIO lol-bot-v3"
    else
        log_info "Bot já baixado"
    fi
    
    chown -R botuser:botuser /home/botuser/lol-bot-v3
}

# Configurar monitoramento básico
setup_monitoring() {
    log_info "Configurando monitoramento básico..."
    
    # Script de monitoramento do sistema
    cat > /usr/local/bin/system-monitor.sh << 'EOF'
#!/bin/bash
LOG_FILE="/var/log/system-monitor.log"

# Função de log
log_metric() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" >> "$LOG_FILE"
}

# CPU e Memória
CPU_USAGE=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | awk -F'%' '{print $1}')
MEM_USAGE=$(free | grep Mem | awk '{printf "%.1f", $3/$2 * 100.0}')
DISK_USAGE=$(df -h / | awk 'NR==2{printf "%s", $5}' | sed 's/%//')

log_metric "CPU: ${CPU_USAGE}% | MEM: ${MEM_USAGE}% | DISK: ${DISK_USAGE}%"

# Verificar se Docker está rodando
if ! systemctl is-active --quiet docker; then
    log_metric "ALERTA: Docker não está rodando!"
    systemctl start docker
fi

# Verificar espaço em disco
if [ "$DISK_USAGE" -gt 90 ]; then
    log_metric "ALERTA: Espaço em disco baixo: ${DISK_USAGE}%"
fi

# Verificar memória
if [ $(echo "$MEM_USAGE > 90" | bc) -eq 1 ]; then
    log_metric "ALERTA: Uso de memória alto: ${MEM_USAGE}%"
fi
EOF

    chmod +x /usr/local/bin/system-monitor.sh
    
    # Cron job para monitoramento
    echo "*/5 * * * * root /usr/local/bin/system-monitor.sh" > /etc/cron.d/system-monitor
    
    log_success "Monitoramento configurado ✓"
}

# Função principal
main() {
    log_info "Iniciando configuração automática do VPS..."
    
    # Verificar se está executando como root
    if [[ $EUID -ne 0 ]]; then
        log_error "Este script deve ser executado como root!"
        exit 1
    fi
    
    # Executar configurações
    update_system
    install_dependencies
    install_docker
    setup_swap
    optimize_system
    setup_firewall
    secure_ssh
    create_bot_user
    setup_bot
    setup_monitoring
    
    echo
    log_success "🎉 Configuração do VPS concluída!"
    echo -e "${GREEN}"
    echo "████████████████████████████████████████"
    echo "█     🌐 VPS CONFIGURADO! 🌐         █"
    echo "█       Pronto para o Bot LoL V3      █"
    echo "████████████████████████████████████████"
    echo -e "${NC}"
    
    log_info "Próximos passos:"
    echo "1. 🔑 Configure autenticação por chave SSH (recomendado)"
    echo "2. 📁 Clone seu repositório do bot:"
    echo "   cd /home/botuser"
    echo "   git clone SEU_REPOSITORIO lol-bot-v3"
    echo "3. ⚙️ Configure o arquivo .env"
    echo "4. 🚀 Execute o deploy:"
    echo "   cd /home/botuser/lol-bot-v3"
    echo "   ./deploy.sh"
    echo
    
    log_info "Informações do sistema:"
    echo "• IP do servidor: $(curl -s ipv4.icanhazip.com 2>/dev/null || echo 'N/A')"
    echo "• Docker version: $(docker --version)"
    echo "• Docker Compose: $(docker-compose --version)"
    echo "• Usuário do bot: botuser"
    echo "• Diretório de trabalho: /home/botuser/lol-bot-v3"
    echo
    
    log_info "Comandos úteis:"
    echo "• Ver logs do sistema: tail -f /var/log/system-monitor.log"
    echo "• Status Docker: systemctl status docker"
    echo "• Mudar para usuário bot: su - botuser"
    echo "• Ver containers: docker ps"
    echo
    
    log_warning "IMPORTANTE:"
    echo "• Configure autenticação por chave SSH e desabilite senha"
    echo "• Altere a porta SSH padrão (22) se necessário"
    echo "• Configure backup automático para cloud"
    echo "• Monitore logs regularmente"
    
    # Reiniciar para aplicar todas as configurações
    echo
    read -p "Deseja reiniciar o sistema agora? (recomendado) [y/N]: " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        log_info "Reiniciando sistema em 10 segundos..."
        sleep 10
        reboot
    else
        log_info "Lembre-se de reiniciar o sistema manualmente para aplicar todas as configurações"
    fi
}

# Verificar argumentos
case "${1:-setup}" in
    "setup")
        main
        ;;
    "docker-only")
        log_info "Instalando apenas Docker..."
        install_docker
        log_success "Docker instalado!"
        ;;
    "security")
        log_info "Configurando apenas segurança..."
        setup_firewall
        secure_ssh
        log_success "Segurança configurada!"
        ;;
    "help")
        echo "Uso: $0 [comando]"
        echo "Comandos:"
        echo "  setup       - Configuração completa (padrão)"
        echo "  docker-only - Instalar apenas Docker"
        echo "  security    - Configurar apenas segurança"
        echo "  help        - Mostrar esta ajuda"
        ;;
    *)
        log_error "Comando desconhecido: $1"
        exit 1
        ;;
esac 