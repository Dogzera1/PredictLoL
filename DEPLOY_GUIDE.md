# 🚀 GUIA COMPLETO DE DEPLOY EM PRODUÇÃO

## Bot LoL V3 Ultra Avançado - Deploy Guide

---

## 📋 ÍNDICE

1. [Pré-requisitos](#pré-requisitos)
2. [Opções de Deploy](#opções-de-deploy)
3. [Deploy com Docker (Recomendado)](#deploy-com-docker)
4. [Deploy com Systemd](#deploy-com-systemd)
5. [Deploy em VPS](#deploy-em-vps)
6. [Monitoramento e Logs](#monitoramento-e-logs)
7. [Backup e Manutenção](#backup-e-manutenção)
8. [Solução de Problemas](#solução-de-problemas)

---

## 🔧 PRÉ-REQUISITOS

### **Hardware Mínimo**
- **RAM**: 2GB (recomendado 4GB)
- **CPU**: 2 cores (recomendado 4 cores)
- **Armazenamento**: 20GB (recomendado 50GB)
- **Rede**: Conexão estável com internet

### **Software**
- **SO**: Ubuntu 20.04+ / Debian 11+ / CentOS 8+
- **Docker**: 20.0+ e Docker Compose
- **Python**: 3.9+ (se não usar Docker)
- **Git**: Para clonar repositório

### **Credenciais Necessárias**
- **Telegram Bot Token**: @BotFather
- **Riot API Key**: developer.riotgames.com
- **VPS/Cloud**: DigitalOcean, AWS, Vultr, etc.

---

## 🌟 OPÇÕES DE DEPLOY

### **1. 🐳 Docker (Recomendado)**
- ✅ Mais fácil e rápido
- ✅ Isolamento completo
- ✅ Monitoramento integrado
- ✅ Backups automáticos

### **2. 🔧 Systemd Service**
- ✅ Controle nativo do OS
- ✅ Performance máxima
- ✅ Integração com logs do sistema
- ❌ Mais complexo de configurar

### **3. ☁️ Cloud Platforms**
- ✅ Railway, Heroku, AWS
- ✅ Deploy automático
- ❌ Pode ser mais caro

---

## 🐳 DEPLOY COM DOCKER

### **Passo 1: Preparar Servidor**

```bash
# Atualizar sistema
sudo apt update && sudo apt upgrade -y

# Instalar Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Instalar Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Adicionar usuário ao grupo docker
sudo usermod -aG docker $USER
newgrp docker
```

### **Passo 2: Clonar e Configurar**

```bash
# Clonar repositório
git clone <seu-repositorio>
cd bot-lol-v3

# Copiar e configurar variáveis
cp env.example .env
nano .env
```

### **Passo 3: Configurar .env**

```bash
# 🤖 CONFIGURAÇÕES ESSENCIAIS
TELEGRAM_TOKEN=7897326299:AAFkX7lF4j_aQYPP70xfAkNyNON6-ZBbMcE
ADMIN_USER_ID=SEU_USER_ID_AQUI
REDIS_PASSWORD=senha_super_segura_123

# 🎮 APIs
RIOT_API_KEY=sua_riot_api_key_aqui

# 💰 CONFIGURAÇÕES FINANCEIRAS
DEFAULT_BANKROLL=10000.0
KELLY_FRACTION=0.25

# 📊 MONITORAMENTO
GRAFANA_PASSWORD=admin123
ENVIRONMENT=production
```

### **Passo 4: Deploy Automático**

```bash
# Dar permissão ao script
chmod +x deploy.sh

# Executar deploy
./deploy.sh

# Acompanhar logs
./deploy.sh logs
```

### **Comandos Úteis Docker**

```bash
# Ver status
./deploy.sh status

# Parar serviços
./deploy.sh stop

# Reiniciar
./deploy.sh restart

# Backup manual
./deploy.sh backup

# Ver logs em tempo real
docker logs lol-predictor-v3 -f

# Acessar container
docker exec -it lol-predictor-v3 bash
```

---

## 🔧 DEPLOY COM SYSTEMD

### **Passo 1: Configurar Systemd**

```bash
# Executar como root
sudo ./systemd-service.sh install
```

### **Passo 2: Instalar Bot**

```bash
# Copiar arquivos para diretório de produção
sudo cp -r . /opt/lol-bot-v3/
sudo chown -R lolbot:lolbot /opt/lol-bot-v3/

# Instalar dependências
cd /opt/lol-bot-v3
sudo -u lolbot pip3 install -r requirements_production.txt
```

### **Passo 3: Configurar e Iniciar**

```bash
# Configurar .env
sudo nano /opt/lol-bot-v3/.env

# Iniciar serviço
sudo systemctl start lol-bot-v3
sudo systemctl enable lol-bot-v3

# Verificar status
sudo systemctl status lol-bot-v3
```

### **Comandos Úteis Systemd**

```bash
# Ver logs
sudo journalctl -u lol-bot-v3 -f

# Reiniciar
sudo systemctl restart lol-bot-v3

# Parar
sudo systemctl stop lol-bot-v3

# Backup manual
sudo /usr/local/bin/lol-bot-v3-backup.sh
```

---

## ☁️ DEPLOY EM VPS

### **Opções de VPS Recomendadas**

#### **1. DigitalOcean ($10-20/mês)**
- ✅ Fácil de usar
- ✅ SSD rápido
- ✅ Boa documentação

```bash
# Criar droplet Ubuntu 22.04
# 2GB RAM, 1 CPU, 50GB SSD
# Seguir passos do Docker acima
```

#### **2. Vultr ($6-12/mês)**
- ✅ Mais barato
- ✅ Múltiplas localizações

#### **3. AWS EC2**
- ✅ Tier gratuito (12 meses)
- ✅ Muito confiável
- ❌ Mais complexo

### **Configuração Rápida VPS**

```bash
# Conectar via SSH
ssh root@SEU_IP_VPS

# Script de configuração automática
curl -fsSL https://raw.githubusercontent.com/SEU_REPO/setup-vps.sh | bash

# OU manual
apt update && apt upgrade -y
curl -fsSL https://get.docker.com | sh
git clone SEU_REPO
cd bot-lol-v3
./deploy.sh
```

---

## 📊 MONITORAMENTO E LOGS

### **Dashboards Disponíveis**

#### **1. Grafana (http://IP:3000)**
- 📈 Métricas do bot
- 📊 Performance financeira
- 🚨 Alertas automáticos
- 🎯 ROI tracking

#### **2. Prometheus (http://IP:9090)**
- 🔧 Métricas técnicas
- 💾 Uso de memória/CPU
- 🌐 Health checks

### **Comandos de Monitoramento**

```bash
# Logs em tempo real
docker logs lol-predictor-v3 -f

# Logs do sistema (systemd)
sudo journalctl -u lol-bot-v3 -f

# Status dos containers
docker ps

# Uso de recursos
docker stats

# Verificar saúde
curl http://localhost:8080/health
```

### **Alertas Configurados**

- 🚨 **Bot offline**: Restart automático
- 📈 **Alto uso de memória**: Alerta + log
- 💰 **Value bets detectados**: Notificação Telegram
- 🔄 **Backup automático**: Diário às 2h

---

## 💾 BACKUP E MANUTENÇÃO

### **Backups Automáticos**

```bash
# Docker: Backups em ./backups/
# Systemd: Backups em /opt/lol-bot-v3/backups/

# Frequência: Diário às 2h da manhã
# Retenção: 30 dias
# Tipo: tar.gz comprimido
```

### **Backup Manual**

```bash
# Docker
./deploy.sh backup

# Systemd
sudo /usr/local/bin/lol-bot-v3-backup.sh

# Manual completo
tar -czf backup_$(date +%Y%m%d).tar.gz data/ logs/
```

### **Restaurar Backup**

```bash
# Parar serviços
./deploy.sh stop

# Restaurar dados
tar -xzf backup_20241225.tar.gz

# Reiniciar
./deploy.sh start
```

### **Manutenção Regular**

```bash
# Limpeza de logs antigos (automática)
# Limpeza de imagens Docker
docker system prune -f

# Atualização do sistema
sudo apt update && sudo apt upgrade -y

# Atualização do bot
git pull
./deploy.sh
```

---

## 🔒 SEGURANÇA

### **Configurações de Segurança**

```bash
# Firewall básico
sudo ufw enable
sudo ufw allow ssh
sudo ufw allow 80
sudo ufw allow 443

# Fail2ban (proteção SSH)
sudo apt install fail2ban

# Usuários não-root
# Docker: usuário botuser automático
# Systemd: usuário lolbot criado automaticamente
```

### **Variáveis Sensíveis**

- ✅ Use arquivo `.env` sempre
- ✅ Nunca commite credenciais
- ✅ Use senhas fortes
- ✅ Rotate API keys regularmente

---

## 🚨 SOLUÇÃO DE PROBLEMAS

### **Bot Não Inicia**

```bash
# Verificar logs
docker logs lol-predictor-v3
# OU
sudo journalctl -u lol-bot-v3

# Verificar .env
cat .env | grep TOKEN

# Testar conexão
curl -X GET "https://api.telegram.org/bot<TOKEN>/getMe"
```

### **Alto Uso de Memória**

```bash
# Ver uso atual
docker stats lol-predictor-v3

# Reiniciar container
docker restart lol-predictor-v3

# Verificar logs por memory leaks
docker logs lol-predictor-v3 | grep -i memory
```

### **Bot Não Responde**

```bash
# Health check
curl http://localhost:8080/health

# Verificar Redis
docker exec lol-redis redis-cli ping

# Restart completo
./deploy.sh restart
```

### **Problemas de Rede**

```bash
# Testar API Riot
curl -H "X-Riot-Token: SUA_KEY" \
  "https://esports-api.lolesports.com/persisted/gw/getLive"

# Verificar DNS
nslookup api.telegram.org

# Verificar firewall
sudo ufw status
```

---

## 📚 LOGS IMPORTANTES

### **Localização dos Logs**

```bash
# Docker
./logs/

# Systemd
/opt/lol-bot-v3/logs/
journalctl -u lol-bot-v3

# Aplicação
- bot.log: Logs principais
- error.log: Apenas erros
- monitor.log: Monitoramento
- backup.log: Logs de backup
```

### **Logs Úteis para Debug**

```bash
# Últimos erros
docker logs lol-predictor-v3 2>&1 | grep ERROR | tail -10

# Atividade de predições
docker logs lol-predictor-v3 | grep "predição"

# Problemas de autorização
docker logs lol-predictor-v3 | grep "autorização"
```

---

## 🎯 PRÓXIMOS PASSOS

Após o deploy bem-sucedido:

1. ✅ **Testar todas as funcionalidades**
2. ✅ **Configurar alertas de monitoramento**
3. ✅ **Configurar backup para cloud (opcional)**
4. ✅ **Configurar domínio personalizado (opcional)**
5. ✅ **Implementar SSL/HTTPS (opcional)**
6. ✅ **Configurar CI/CD para updates automáticos**

---

## 🆘 SUPORTE

### **Contatos para Suporte**
- 📧 Email: admin@botlol.com
- 📱 Telegram: @BotLolSupport
- 📚 Documentação: github.com/repo/wiki

### **Logs para Enviar em Caso de Problema**
```bash
# Coletar logs para suporte
./deploy.sh logs > debug_logs.txt
docker ps > containers_status.txt
df -h > disk_usage.txt
free -h > memory_usage.txt
```

---

## ✅ CHECKLIST FINAL

- [ ] VPS configurado e acessível
- [ ] Docker e Docker Compose instalados
- [ ] Arquivo .env configurado com credenciais
- [ ] Deploy executado com sucesso
- [ ] Bot respondendo no Telegram
- [ ] Monitoramento funcionando (Grafana)
- [ ] Backups automáticos configurados
- [ ] Logs sendo gerados corretamente
- [ ] Sistema de autorização testado
- [ ] Firewall configurado

---

**🎉 Parabéns! Seu Bot LoL V3 Ultra Avançado está em produção!** 🚀 