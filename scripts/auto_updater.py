#!/usr/bin/env python3
"""
Sistema de Auto-Update Inteligente - Bot LoL V3
Monitora o repositório Git e atualiza automaticamente quando necessário
"""

import os
import sys
import asyncio
import subprocess
import logging
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List
import aiohttp
from pathlib import Path

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/auto_updater.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class GitMonitor:
    """Monitor de mudanças no repositório Git"""
    
    def __init__(self, repo_path: str = ".", remote: str = "origin", branch: str = "main"):
        self.repo_path = Path(repo_path)
        self.remote = remote
        self.branch = branch
        self.last_commit = None
        self.update_file = self.repo_path / "data" / "last_update.json"
        
    def get_current_commit(self) -> str:
        """Obtém hash do commit atual"""
        try:
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ Erro ao obter commit atual: {e}")
            return ""
    
    def get_remote_commit(self) -> str:
        """Obtém hash do último commit remoto"""
        try:
            # Fetch latest changes
            subprocess.run(
                ["git", "fetch", self.remote],
                cwd=self.repo_path,
                check=True,
                capture_output=True
            )
            
            # Get remote commit hash
            result = subprocess.run(
                ["git", "rev-parse", f"{self.remote}/{self.branch}"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ Erro ao obter commit remoto: {e}")
            return ""
    
    def has_updates(self) -> bool:
        """Verifica se há updates disponíveis"""
        current = self.get_current_commit()
        remote = self.get_remote_commit()
        
        if not current or not remote:
            return False
            
        has_updates = current != remote
        
        if has_updates:
            logger.info(f"📦 Update disponível: {current[:8]} -> {remote[:8]}")
        
        return has_updates
    
    def get_commit_info(self, commit_hash: str) -> Dict:
        """Obtém informações de um commit"""
        try:
            result = subprocess.run(
                ["git", "show", "--format=%H|%an|%ad|%s", "--no-patch", commit_hash],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True
            )
            
            parts = result.stdout.strip().split('|', 3)
            return {
                'hash': parts[0],
                'author': parts[1],
                'date': parts[2],
                'message': parts[3]
            }
        except subprocess.CalledProcessError:
            return {}
    
    def get_changelog_since_last_update(self) -> List[Dict]:
        """Obtém changelog desde último update"""
        if not self.last_commit:
            return []
            
        try:
            result = subprocess.run(
                ["git", "log", f"{self.last_commit}..HEAD", "--format=%H"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True
            )
            
            commits = result.stdout.strip().split('\n')
            changelog = []
            
            for commit in commits:
                if commit:
                    info = self.get_commit_info(commit)
                    if info:
                        changelog.append(info)
            
            return changelog
        except subprocess.CalledProcessError:
            return []
    
    def save_update_info(self):
        """Salva informações do último update"""
        update_info = {
            'last_commit': self.get_current_commit(),
            'last_update': datetime.now().isoformat(),
            'branch': self.branch,
            'remote': self.remote
        }
        
        os.makedirs(self.update_file.parent, exist_ok=True)
        with open(self.update_file, 'w') as f:
            json.dump(update_info, f, indent=2)
    
    def load_update_info(self):
        """Carrega informações do último update"""
        if self.update_file.exists():
            try:
                with open(self.update_file, 'r') as f:
                    info = json.load(f)
                    self.last_commit = info.get('last_commit')
                    return info
            except (json.JSONDecodeError, FileNotFoundError):
                pass
        return {}


class SafeUpdater:
    """Sistema de update seguro com rollback"""
    
    def __init__(self, repo_path: str = ".", backup_dir: str = "backups"):
        self.repo_path = Path(repo_path)
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(exist_ok=True)
        
    def create_backup(self) -> str:
        """Cria backup antes do update"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"pre_update_backup_{timestamp}"
        backup_path = self.backup_dir / f"{backup_name}.tar.gz"
        
        try:
            # Criar backup comprimido
            subprocess.run([
                "tar", "-czf", str(backup_path),
                "--exclude=.git",
                "--exclude=backups",
                "--exclude=logs",
                "--exclude=__pycache__",
                "."
            ], cwd=self.repo_path, check=True)
            
            logger.info(f"💾 Backup criado: {backup_path}")
            return str(backup_path)
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ Erro ao criar backup: {e}")
            return ""
    
    def perform_update(self) -> bool:
        """Executa o update do Git"""
        try:
            # Stash local changes
            subprocess.run(
                ["git", "stash", "push", "-m", "auto-updater-stash"],
                cwd=self.repo_path,
                capture_output=True
            )
            
            # Pull latest changes
            result = subprocess.run(
                ["git", "pull", "origin", "main"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True
            )
            
            logger.info("✅ Update Git concluído com sucesso")
            logger.info(f"📋 Output: {result.stdout}")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ Erro no update Git: {e}")
            logger.error(f"📋 Error output: {e.stderr}")
            return False
    
    def update_dependencies(self) -> bool:
        """Atualiza dependências Python"""
        try:
            # Atualizar pip
            subprocess.run([
                sys.executable, "-m", "pip", "install", "--upgrade", "pip"
            ], check=True, capture_output=True)
            
            # Instalar/atualizar requirements
            if (self.repo_path / "requirements_production.txt").exists():
                subprocess.run([
                    sys.executable, "-m", "pip", "install", "-r", 
                    "requirements_production.txt", "--upgrade"
                ], cwd=self.repo_path, check=True, capture_output=True)
            
            logger.info("✅ Dependências atualizadas")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ Erro ao atualizar dependências: {e}")
            return False
    
    def restart_services(self) -> bool:
        """Reinicia serviços após update"""
        try:
            # Verificar se existe docker-compose
            if (self.repo_path / "docker-compose.yml").exists():
                subprocess.run([
                    "docker-compose", "restart"
                ], cwd=self.repo_path, check=True, capture_output=True)
                logger.info("🐳 Serviços Docker reiniciados")
                
            # Verificar se existe systemd service
            elif os.path.exists("/etc/systemd/system/lol-bot-v3.service"):
                subprocess.run([
                    "systemctl", "restart", "lol-bot-v3"
                ], check=True, capture_output=True)
                logger.info("🔄 Serviço systemd reiniciado")
                
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ Erro ao reiniciar serviços: {e}")
            return False


class HealthChecker:
    """Verificador de saúde do sistema após updates"""
    
    def __init__(self, health_url: str = "http://localhost:8080/health"):
        self.health_url = health_url
        
    async def wait_for_service(self, timeout: int = 120) -> bool:
        """Aguarda serviço ficar online"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(self.health_url, timeout=10) as response:
                        if response.status == 200:
                            logger.info("✅ Serviço está saudável")
                            return True
            except:
                pass
            
            await asyncio.sleep(5)
            
        logger.error("❌ Timeout aguardando serviço ficar saudável")
        return False
    
    async def comprehensive_health_check(self) -> Dict:
        """Verificação completa de saúde"""
        checks = {
            'service_online': False,
            'api_responsive': False,
            'database_ok': False,
            'memory_usage': 'unknown'
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                # Health endpoint
                async with session.get(self.health_url, timeout=10) as response:
                    if response.status == 200:
                        checks['service_online'] = True
                        data = await response.json()
                        checks.update(data.get('checks', {}))
                
                # API test
                async with session.get(f"{self.health_url.replace('/health', '/api/test')}", timeout=10) as response:
                    checks['api_responsive'] = response.status == 200
                    
        except Exception as e:
            logger.error(f"❌ Erro na verificação de saúde: {e}")
            
        return checks


class NotificationSystem:
    """Sistema de notificações para updates"""
    
    def __init__(self, webhook_url: str = None, telegram_token: str = None, chat_id: str = None):
        self.webhook_url = webhook_url
        self.telegram_token = telegram_token
        self.chat_id = chat_id
        
    async def send_update_notification(self, success: bool, changelog: List[Dict], rollback: bool = False):
        """Envia notificação de update"""
        if rollback:
            message = "🚨 **Auto-Update FAILED - Rollback executado**"
        elif success:
            message = "✅ **Auto-Update executado com sucesso!**"
        else:
            message = "❌ **Auto-Update falhou!**"
            
        message += f"\n⏰ **Time:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        if changelog:
            message += "\n\n📋 **Changelog:**"
            for commit in changelog[-3:]:  # Últimos 3 commits
                message += f"\n• {commit['message'][:50]}..."
                
        await self._send_message(message)
    
    async def send_error_alert(self, error: str):
        """Envia alerta de erro"""
        message = f"🚨 **Auto-Updater Error Alert**\n\n❌ {error}\n⏰ {datetime.now()}"
        await self._send_message(message)
    
    async def _send_message(self, message: str):
        """Envia mensagem via webhook ou Telegram"""
        try:
            if self.webhook_url:
                async with aiohttp.ClientSession() as session:
                    payload = {"content": message}
                    await session.post(self.webhook_url, json=payload)
                    
            if self.telegram_token and self.chat_id:
                url = f"https://api.telegram.org/bot{self.telegram_token}/sendMessage"
                payload = {
                    "chat_id": self.chat_id,
                    "text": message,
                    "parse_mode": "Markdown"
                }
                async with aiohttp.ClientSession() as session:
                    await session.post(url, json=payload)
                    
            logger.info("📱 Notificação enviada")
        except Exception as e:
            logger.error(f"❌ Erro ao enviar notificação: {e}")


class AutoUpdater:
    """Sistema principal de auto-update"""
    
    def __init__(self, config: Dict = None):
        self.config = config or self._load_config()
        
        self.git_monitor = GitMonitor(
            repo_path=self.config.get('repo_path', '.'),
            remote=self.config.get('remote', 'origin'),
            branch=self.config.get('branch', 'main')
        )
        
        self.updater = SafeUpdater(
            repo_path=self.config.get('repo_path', '.'),
            backup_dir=self.config.get('backup_dir', 'backups')
        )
        
        self.health_checker = HealthChecker(
            health_url=self.config.get('health_url', 'http://localhost:8080/health')
        )
        
        self.notifier = NotificationSystem(
            webhook_url=self.config.get('webhook_url'),
            telegram_token=self.config.get('telegram_token'),
            chat_id=self.config.get('notification_chat_id')
        )
        
        self.check_interval = self.config.get('check_interval', 300)  # 5 minutos
        self.maintenance_window = self.config.get('maintenance_window', (2, 6))  # 2h-6h
        
    def _load_config(self) -> Dict:
        """Carrega configuração do auto-updater"""
        config_file = Path("config/auto_updater.json")
        
        if config_file.exists():
            try:
                with open(config_file) as f:
                    return json.load(f)
            except:
                pass
                
        # Configuração padrão
        return {
            'enabled': True,
            'check_interval': 300,
            'auto_restart': True,
            'maintenance_window': [2, 6],
            'max_retries': 3,
            'rollback_on_failure': True
        }
    
    def is_maintenance_window(self) -> bool:
        """Verifica se está na janela de manutenção"""
        current_hour = datetime.now().hour
        start, end = self.maintenance_window
        
        if start <= end:
            return start <= current_hour < end
        else:  # Window crosses midnight
            return current_hour >= start or current_hour < end
    
    async def perform_safe_update(self) -> bool:
        """Executa update seguro com rollback"""
        logger.info("🚀 Iniciando auto-update...")
        
        # Criar backup
        backup_path = self.updater.create_backup()
        if not backup_path:
            await self.notifier.send_error_alert("Falha ao criar backup")
            return False
        
        try:
            # Obter changelog antes do update
            changelog = self.git_monitor.get_changelog_since_last_update()
            
            # Executar update
            if not self.updater.perform_update():
                raise Exception("Falha no update Git")
                
            # Atualizar dependências
            if not self.updater.update_dependencies():
                raise Exception("Falha ao atualizar dependências")
                
            # Reiniciar serviços
            if self.config.get('auto_restart', True):
                if not self.updater.restart_services():
                    raise Exception("Falha ao reiniciar serviços")
                    
                # Aguardar serviço ficar online
                if not await self.health_checker.wait_for_service():
                    raise Exception("Serviço não ficou saudável após restart")
            
            # Verificação de saúde final
            health = await self.health_checker.comprehensive_health_check()
            if not health.get('service_online', False):
                raise Exception("Verificação de saúde falhou")
            
            # Salvar informações do update
            self.git_monitor.save_update_info()
            
            # Notificar sucesso
            await self.notifier.send_update_notification(True, changelog)
            
            logger.info("✅ Auto-update concluído com sucesso!")
            return True
            
        except Exception as e:
            logger.error(f"❌ Auto-update falhou: {e}")
            
            # Rollback se configurado
            if self.config.get('rollback_on_failure', True):
                await self._perform_rollback(backup_path)
                await self.notifier.send_update_notification(False, [], rollback=True)
            else:
                await self.notifier.send_update_notification(False, [])
                
            return False
    
    async def _perform_rollback(self, backup_path: str):
        """Executa rollback para backup"""
        try:
            logger.info(f"🔄 Executando rollback para: {backup_path}")
            
            # Extrair backup
            subprocess.run([
                "tar", "-xzf", backup_path
            ], cwd=self.updater.repo_path, check=True)
            
            # Reiniciar serviços
            self.updater.restart_services()
            
            logger.info("✅ Rollback concluído")
        except Exception as e:
            logger.error(f"❌ Erro no rollback: {e}")
    
    async def monitor_loop(self):
        """Loop principal de monitoramento"""
        logger.info("🔍 Iniciando monitoramento de auto-update...")
        
        # Carregar informações do último update
        self.git_monitor.load_update_info()
        
        while True:
            try:
                if not self.config.get('enabled', True):
                    await asyncio.sleep(self.check_interval)
                    continue
                
                # Verificar se há updates
                if self.git_monitor.has_updates():
                    # Verificar janela de manutenção
                    if self.config.get('respect_maintenance_window', True):
                        if not self.is_maintenance_window():
                            logger.info("⏰ Update disponível, aguardando janela de manutenção...")
                            await asyncio.sleep(300)  # Verificar novamente em 5 min
                            continue
                    
                    # Executar update
                    await self.perform_safe_update()
                
                await asyncio.sleep(self.check_interval)
                
            except KeyboardInterrupt:
                logger.info("🛑 Auto-updater interrompido pelo usuário")
                break
            except Exception as e:
                logger.error(f"❌ Erro no loop de monitoramento: {e}")
                await self.notifier.send_error_alert(str(e))
                await asyncio.sleep(60)  # Aguardar 1 minuto antes de tentar novamente


def main():
    """Função principal"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Auto-Updater Bot LoL V3")
    parser.add_argument("--config", help="Arquivo de configuração")
    parser.add_argument("--force-update", action="store_true", help="Forçar update")
    parser.add_argument("--check-only", action="store_true", help="Apenas verificar updates")
    
    args = parser.parse_args()
    
    # Carregar configuração
    config = {}
    if args.config and Path(args.config).exists():
        with open(args.config) as f:
            config = json.load(f)
    
    # Criar auto-updater
    auto_updater = AutoUpdater(config)
    
    if args.check_only:
        # Apenas verificar
        has_updates = auto_updater.git_monitor.has_updates()
        print(f"Updates disponíveis: {'Sim' if has_updates else 'Não'}")
        return
    
    if args.force_update:
        # Forçar update
        asyncio.run(auto_updater.perform_safe_update())
    else:
        # Executar loop de monitoramento
        asyncio.run(auto_updater.monitor_loop())


if __name__ == "__main__":
    main() 