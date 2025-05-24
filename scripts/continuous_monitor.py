#!/usr/bin/env python3
"""
Sistema de Monitoramento Contínuo - Bot LoL V3
Monitora saúde, performance e funcionalidades em tempo real
"""

import asyncio
import aiohttp
import logging
import json
import psutil
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from pathlib import Path
import subprocess
import sqlite3

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/continuous_monitor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class SystemMonitor:
    """Monitor de recursos do sistema"""
    
    def __init__(self):
        self.alerts_threshold = {
            'cpu_percent': 85.0,
            'memory_percent': 90.0,
            'disk_percent': 95.0,
            'load_average': 4.0
        }
        
    def get_system_metrics(self) -> Dict:
        """Coleta métricas do sistema"""
        try:
            # CPU e Memória
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Load average (Linux/Mac)
            load_avg = None
            try:
                load_avg = psutil.getloadavg()[0]  # 1-minute load average
            except AttributeError:
                # Windows doesn't have load average
                pass
            
            # Processos do bot
            bot_processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
                try:
                    if 'python' in proc.info['name'].lower() and any(
                        name in ' '.join(proc.cmdline()) 
                        for name in ['main_v3', 'bot', 'lol']
                    ):
                        bot_processes.append(proc.info)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            return {
                'timestamp': datetime.now().isoformat(),
                'cpu_percent': cpu_percent,
                'memory': {
                    'total': memory.total,
                    'available': memory.available,
                    'used': memory.used,
                    'percent': memory.percent
                },
                'disk': {
                    'total': disk.total,
                    'used': disk.used,
                    'free': disk.free,
                    'percent': (disk.used / disk.total) * 100
                },
                'load_average': load_avg,
                'bot_processes': bot_processes
            }
        except Exception as e:
            logger.error(f"❌ Erro ao coletar métricas do sistema: {e}")
            return {}
    
    def check_system_health(self, metrics: Dict) -> List[str]:
        """Verifica saúde do sistema e retorna alertas"""
        alerts = []
        
        # CPU
        if metrics.get('cpu_percent', 0) > self.alerts_threshold['cpu_percent']:
            alerts.append(f"🚨 Alto uso de CPU: {metrics['cpu_percent']:.1f}%")
        
        # Memória
        memory_percent = metrics.get('memory', {}).get('percent', 0)
        if memory_percent > self.alerts_threshold['memory_percent']:
            alerts.append(f"🚨 Alto uso de memória: {memory_percent:.1f}%")
        
        # Disco
        disk_percent = metrics.get('disk', {}).get('percent', 0)
        if disk_percent > self.alerts_threshold['disk_percent']:
            alerts.append(f"🚨 Espaço em disco baixo: {disk_percent:.1f}%")
        
        # Load average
        load_avg = metrics.get('load_average')
        if load_avg and load_avg > self.alerts_threshold['load_average']:
            alerts.append(f"🚨 Alta carga do sistema: {load_avg:.2f}")
        
        # Processos do bot
        if not metrics.get('bot_processes'):
            alerts.append("🚨 Nenhum processo do bot detectado")
        
        return alerts


class BotHealthMonitor:
    """Monitor específico da saúde do bot"""
    
    def __init__(self, base_url: str = "http://localhost:8080"):
        self.base_url = base_url
        self.endpoints = {
            'health': '/health',
            'metrics': '/metrics',
            'status': '/status'
        }
        
    async def check_bot_health(self) -> Dict:
        """Verifica saúde do bot via endpoints"""
        health_status = {
            'is_online': False,
            'response_time': None,
            'endpoints_status': {},
            'last_activity': None,
            'error_rate': 0.0
        }
        
        async with aiohttp.ClientSession() as session:
            for endpoint_name, endpoint_path in self.endpoints.items():
                url = f"{self.base_url}{endpoint_path}"
                
                try:
                    start_time = time.time()
                    async with session.get(url, timeout=10) as response:
                        response_time = (time.time() - start_time) * 1000  # ms
                        
                        health_status['endpoints_status'][endpoint_name] = {
                            'status_code': response.status,
                            'response_time': response_time,
                            'is_healthy': response.status == 200
                        }
                        
                        if endpoint_name == 'health' and response.status == 200:
                            health_status['is_online'] = True
                            health_status['response_time'] = response_time
                            
                            # Tentar obter dados detalhados
                            try:
                                data = await response.json()
                                health_status.update(data)
                            except:
                                pass
                                
                except asyncio.TimeoutError:
                    health_status['endpoints_status'][endpoint_name] = {
                        'status_code': None,
                        'response_time': None,
                        'is_healthy': False,
                        'error': 'timeout'
                    }
                except Exception as e:
                    health_status['endpoints_status'][endpoint_name] = {
                        'status_code': None,
                        'response_time': None,
                        'is_healthy': False,
                        'error': str(e)
                    }
        
        return health_status
    
    async def test_bot_functionality(self) -> Dict:
        """Testa funcionalidades específicas do bot"""
        tests = {
            'api_integration': False,
            'prediction_system': False,
            'value_betting': False,
            'database_access': False
        }
        
        try:
            # Teste da API Riot
            async with aiohttp.ClientSession() as session:
                try:
                    # Endpoint de teste personalizado (você pode implementar)
                    async with session.get(f"{self.base_url}/test/riot-api", timeout=15) as response:
                        tests['api_integration'] = response.status == 200
                except:
                    pass
                
                # Teste do sistema de predição
                try:
                    async with session.get(f"{self.base_url}/test/prediction", timeout=15) as response:
                        tests['prediction_system'] = response.status == 200
                except:
                    pass
                    
                # Teste do value betting
                try:
                    async with session.get(f"{self.base_url}/test/value-betting", timeout=15) as response:
                        tests['value_betting'] = response.status == 200
                except:
                    pass
        except Exception as e:
            logger.error(f"❌ Erro nos testes de funcionalidade: {e}")
        
        return tests


class LogAnalyzer:
    """Analisador de logs para detectar problemas"""
    
    def __init__(self, log_files: List[str] = None):
        self.log_files = log_files or [
            'logs/bot.log',
            'logs/error.log',
            'logs/auto_updater.log'
        ]
        self.error_patterns = [
            'ERROR',
            'CRITICAL',
            'FATAL',
            'Exception',
            'Traceback',
            'Failed',
            'Connection refused',
            'Timeout'
        ]
        
    def analyze_recent_logs(self, hours: int = 1) -> Dict:
        """Analisa logs das últimas N horas"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        analysis = {
            'total_errors': 0,
            'error_types': {},
            'recent_errors': [],
            'patterns_detected': []
        }
        
        for log_file in self.log_files:
            if not Path(log_file).exists():
                continue
                
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    
                for line in lines[-1000:]:  # Últimas 1000 linhas
                    # Tentar extrair timestamp
                    try:
                        # Formato: 2024-01-01 12:00:00,123
                        timestamp_str = line[:23]
                        log_time = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S,%f')
                        
                        if log_time < cutoff_time:
                            continue
                    except:
                        continue
                    
                    # Verificar padrões de erro
                    for pattern in self.error_patterns:
                        if pattern.lower() in line.lower():
                            analysis['total_errors'] += 1
                            
                            error_type = pattern
                            analysis['error_types'][error_type] = analysis['error_types'].get(error_type, 0) + 1
                            
                            if len(analysis['recent_errors']) < 10:
                                analysis['recent_errors'].append({
                                    'timestamp': timestamp_str,
                                    'message': line.strip()[:200],
                                    'type': error_type
                                })
                            break
            
            except Exception as e:
                logger.error(f"❌ Erro ao analisar log {log_file}: {e}")
        
        return analysis


class DatabaseMonitor:
    """Monitor do banco de dados"""
    
    def __init__(self, db_path: str = "data/bot.db"):
        self.db_path = db_path
        
    def check_database_health(self) -> Dict:
        """Verifica saúde do banco de dados"""
        health = {
            'accessible': False,
            'size_mb': 0,
            'tables_count': 0,
            'last_backup': None,
            'integrity_check': False
        }
        
        try:
            # Verificar se arquivo existe
            if not Path(self.db_path).exists():
                return health
            
            # Tamanho do arquivo
            health['size_mb'] = Path(self.db_path).stat().st_size / (1024 * 1024)
            
            # Conectar e verificar
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Contar tabelas
            cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
            health['tables_count'] = cursor.fetchone()[0]
            
            # Verificar integridade
            cursor.execute("PRAGMA integrity_check")
            integrity_result = cursor.fetchone()[0]
            health['integrity_check'] = integrity_result == 'ok'
            
            health['accessible'] = True
            
            conn.close()
            
        except Exception as e:
            logger.error(f"❌ Erro ao verificar banco de dados: {e}")
            
        return health


class PerformanceTracker:
    """Rastreador de performance do bot"""
    
    def __init__(self):
        self.metrics_history = []
        self.max_history = 1440  # 24h com coletas a cada minuto
        
    def add_metrics(self, metrics: Dict):
        """Adiciona métricas ao histórico"""
        metrics['timestamp'] = datetime.now().isoformat()
        self.metrics_history.append(metrics)
        
        # Manter apenas último período
        if len(self.metrics_history) > self.max_history:
            self.metrics_history = self.metrics_history[-self.max_history:]
    
    def get_performance_summary(self, hours: int = 24) -> Dict:
        """Obtém resumo de performance"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        recent_metrics = [
            m for m in self.metrics_history
            if datetime.fromisoformat(m['timestamp']) >= cutoff_time
        ]
        
        if not recent_metrics:
            return {}
        
        # Calcular estatísticas
        response_times = [m.get('response_time', 0) for m in recent_metrics if m.get('response_time')]
        cpu_usage = [m.get('cpu_percent', 0) for m in recent_metrics if m.get('cpu_percent')]
        memory_usage = [m.get('memory_percent', 0) for m in recent_metrics if m.get('memory_percent')]
        
        summary = {
            'period_hours': hours,
            'data_points': len(recent_metrics),
            'uptime_percentage': self._calculate_uptime(recent_metrics),
            'response_time': {
                'avg': sum(response_times) / len(response_times) if response_times else 0,
                'min': min(response_times) if response_times else 0,
                'max': max(response_times) if response_times else 0
            },
            'cpu_usage': {
                'avg': sum(cpu_usage) / len(cpu_usage) if cpu_usage else 0,
                'max': max(cpu_usage) if cpu_usage else 0
            },
            'memory_usage': {
                'avg': sum(memory_usage) / len(memory_usage) if memory_usage else 0,
                'max': max(memory_usage) if memory_usage else 0
            }
        }
        
        return summary
    
    def _calculate_uptime(self, metrics: List[Dict]) -> float:
        """Calcula porcentagem de uptime"""
        if not metrics:
            return 0.0
            
        online_count = sum(1 for m in metrics if m.get('is_online', False))
        return (online_count / len(metrics)) * 100


class AlertManager:
    """Gerenciador de alertas"""
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.alert_history = []
        self.cooldown_periods = {
            'system': 300,    # 5 minutos
            'bot': 180,       # 3 minutos
            'database': 600,  # 10 minutos
            'critical': 60    # 1 minuto
        }
        
    def should_send_alert(self, alert_type: str, message: str) -> bool:
        """Verifica se deve enviar alerta (cooldown)"""
        now = datetime.now()
        cooldown = self.cooldown_periods.get(alert_type, 300)
        
        # Verificar se já enviou alerta similar recentemente
        for alert in self.alert_history:
            if (alert['type'] == alert_type and 
                alert['message'] == message and
                (now - alert['timestamp']).total_seconds() < cooldown):
                return False
        
        return True
    
    def add_alert(self, alert_type: str, message: str, severity: str = 'warning'):
        """Adiciona alerta ao histórico"""
        alert = {
            'timestamp': datetime.now(),
            'type': alert_type,
            'message': message,
            'severity': severity
        }
        
        self.alert_history.append(alert)
        
        # Manter apenas últimas 24h
        cutoff = datetime.now() - timedelta(hours=24)
        self.alert_history = [
            a for a in self.alert_history 
            if a['timestamp'] >= cutoff
        ]
    
    async def send_alert(self, alert_type: str, message: str, severity: str = 'warning'):
        """Envia alerta se necessário"""
        if not self.should_send_alert(alert_type, message):
            return
        
        self.add_alert(alert_type, message, severity)
        
        # Enviar via diferentes canais
        await self._send_webhook_alert(message, severity)
        await self._send_telegram_alert(message, severity)
        
    async def _send_webhook_alert(self, message: str, severity: str):
        """Envia alerta via webhook"""
        webhook_url = self.config.get('webhook_url')
        if not webhook_url:
            return
            
        try:
            severity_emoji = {
                'info': '📋',
                'warning': '⚠️',
                'error': '❌',
                'critical': '🚨'
            }
            
            formatted_message = f"{severity_emoji.get(severity, '📋')} **Bot LoL V3 Alert**\n\n{message}\n\n⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            
            async with aiohttp.ClientSession() as session:
                payload = {"content": formatted_message}
                await session.post(webhook_url, json=payload, timeout=10)
                
        except Exception as e:
            logger.error(f"❌ Erro ao enviar webhook alert: {e}")
    
    async def _send_telegram_alert(self, message: str, severity: str):
        """Envia alerta via Telegram"""
        telegram_token = self.config.get('telegram_token')
        chat_id = self.config.get('alert_chat_id')
        
        if not telegram_token or not chat_id:
            return
            
        try:
            url = f"https://api.telegram.org/bot{telegram_token}/sendMessage"
            payload = {
                "chat_id": chat_id,
                "text": f"🚨 Bot LoL V3 Alert\n\n{message}",
                "parse_mode": "Markdown"
            }
            
            async with aiohttp.ClientSession() as session:
                await session.post(url, json=payload, timeout=10)
                
        except Exception as e:
            logger.error(f"❌ Erro ao enviar Telegram alert: {e}")


class ContinuousMonitor:
    """Monitor contínuo principal"""
    
    def __init__(self, config: Dict = None):
        self.config = config or self._load_config()
        
        self.system_monitor = SystemMonitor()
        self.bot_monitor = BotHealthMonitor(
            base_url=self.config.get('bot_url', 'http://localhost:8080')
        )
        self.log_analyzer = LogAnalyzer()
        self.db_monitor = DatabaseMonitor(
            db_path=self.config.get('db_path', 'data/bot.db')
        )
        self.performance_tracker = PerformanceTracker()
        self.alert_manager = AlertManager(self.config)
        
        self.check_interval = self.config.get('check_interval', 60)  # 1 minuto
        
    def _load_config(self) -> Dict:
        """Carrega configuração"""
        config_file = Path("config/monitor.json")
        
        if config_file.exists():
            try:
                with open(config_file) as f:
                    return json.load(f)
            except:
                pass
                
        return {
            'enabled': True,
            'check_interval': 60,
            'bot_url': 'http://localhost:8080',
            'db_path': 'data/bot.db'
        }
    
    async def perform_health_check(self) -> Dict:
        """Executa verificação completa de saúde"""
        logger.info("🔍 Executando verificação de saúde...")
        
        health_report = {
            'timestamp': datetime.now().isoformat(),
            'overall_status': 'healthy',
            'components': {}
        }
        
        # Sistema
        system_metrics = self.system_monitor.get_system_metrics()
        system_alerts = self.system_monitor.check_system_health(system_metrics)
        
        health_report['components']['system'] = {
            'status': 'unhealthy' if system_alerts else 'healthy',
            'metrics': system_metrics,
            'alerts': system_alerts
        }
        
        # Bot
        bot_health = await self.bot_monitor.check_bot_health()
        bot_tests = await self.bot_monitor.test_bot_functionality()
        
        health_report['components']['bot'] = {
            'status': 'healthy' if bot_health.get('is_online') else 'unhealthy',
            'health': bot_health,
            'functionality_tests': bot_tests
        }
        
        # Logs
        log_analysis = self.log_analyzer.analyze_recent_logs(hours=1)
        
        health_report['components']['logs'] = {
            'status': 'unhealthy' if log_analysis['total_errors'] > 10 else 'healthy',
            'analysis': log_analysis
        }
        
        # Database
        db_health = self.db_monitor.check_database_health()
        
        health_report['components']['database'] = {
            'status': 'healthy' if db_health.get('accessible') else 'unhealthy',
            'health': db_health
        }
        
        # Status geral
        unhealthy_components = [
            name for name, component in health_report['components'].items()
            if component['status'] == 'unhealthy'
        ]
        
        if unhealthy_components:
            health_report['overall_status'] = 'unhealthy'
            
        # Adicionar ao rastreador de performance
        performance_metrics = {
            'is_online': bot_health.get('is_online', False),
            'response_time': bot_health.get('response_time'),
            'cpu_percent': system_metrics.get('cpu_percent'),
            'memory_percent': system_metrics.get('memory', {}).get('percent')
        }
        self.performance_tracker.add_metrics(performance_metrics)
        
        return health_report
    
    async def process_alerts(self, health_report: Dict):
        """Processa e envia alertas baseados no health report"""
        components = health_report.get('components', {})
        
        # Alertas do sistema
        system_component = components.get('system', {})
        for alert in system_component.get('alerts', []):
            await self.alert_manager.send_alert('system', alert, 'warning')
        
        # Alertas do bot
        bot_component = components.get('bot', {})
        if bot_component.get('status') == 'unhealthy':
            await self.alert_manager.send_alert(
                'bot', 
                'Bot está offline ou não respondendo',
                'critical'
            )
        
        # Alertas de logs
        logs_component = components.get('logs', {})
        if logs_component.get('status') == 'unhealthy':
            error_count = logs_component.get('analysis', {}).get('total_errors', 0)
            await self.alert_manager.send_alert(
                'bot',
                f'Alto número de erros detectados nos logs: {error_count}',
                'error'
            )
        
        # Alertas do database
        db_component = components.get('database', {})
        if db_component.get('status') == 'unhealthy':
            await self.alert_manager.send_alert(
                'database',
                'Banco de dados inacessível ou com problemas',
                'error'
            )
    
    async def generate_daily_report(self):
        """Gera relatório diário"""
        logger.info("📊 Gerando relatório diário...")
        
        performance_summary = self.performance_tracker.get_performance_summary(hours=24)
        
        report = f"""📊 **Relatório Diário - Bot LoL V3**
⏰ **Data:** {datetime.now().strftime('%Y-%m-%d')}

🔧 **Performance (24h):**
• Uptime: {performance_summary.get('uptime_percentage', 0):.1f}%
• Tempo de resposta médio: {performance_summary.get('response_time', {}).get('avg', 0):.0f}ms
• Uso médio de CPU: {performance_summary.get('cpu_usage', {}).get('avg', 0):.1f}%
• Uso médio de memória: {performance_summary.get('memory_usage', {}).get('avg', 0):.1f}%

📋 **Alertas enviados:** {len([a for a in self.alert_manager.alert_history if (datetime.now() - a['timestamp']).days == 0])}

✅ Relatório gerado automaticamente"""

        await self.alert_manager._send_webhook_alert(report, 'info')
    
    async def monitor_loop(self):
        """Loop principal de monitoramento"""
        logger.info("🔍 Iniciando monitoramento contínuo...")
        
        last_daily_report = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        
        while True:
            try:
                if not self.config.get('enabled', True):
                    await asyncio.sleep(self.check_interval)
                    continue
                
                # Verificação de saúde
                health_report = await self.perform_health_check()
                
                # Processar alertas
                await self.process_alerts(health_report)
                
                # Relatório diário (às 6h)
                now = datetime.now()
                if (now.hour == 6 and now.minute < 5 and 
                    now.date() > last_daily_report.date()):
                    await self.generate_daily_report()
                    last_daily_report = now
                
                # Log de status
                overall_status = health_report.get('overall_status')
                if overall_status == 'healthy':
                    logger.info("✅ Sistema saudável")
                else:
                    logger.warning(f"⚠️ Sistema com problemas: {overall_status}")
                
                await asyncio.sleep(self.check_interval)
                
            except KeyboardInterrupt:
                logger.info("🛑 Monitor interrompido pelo usuário")
                break
            except Exception as e:
                logger.error(f"❌ Erro no loop de monitoramento: {e}")
                await asyncio.sleep(60)


def main():
    """Função principal"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Continuous Monitor Bot LoL V3")
    parser.add_argument("--config", help="Arquivo de configuração")
    parser.add_argument("--health-check", action="store_true", help="Executar apenas verificação de saúde")
    parser.add_argument("--daily-report", action="store_true", help="Gerar relatório diário")
    
    args = parser.parse_args()
    
    # Carregar configuração
    config = {}
    if args.config and Path(args.config).exists():
        with open(args.config) as f:
            config = json.load(f)
    
    monitor = ContinuousMonitor(config)
    
    if args.health_check:
        # Apenas verificação de saúde
        health_report = asyncio.run(monitor.perform_health_check())
        print(json.dumps(health_report, indent=2))
        return
    
    if args.daily_report:
        # Gerar relatório diário
        asyncio.run(monitor.generate_daily_report())
        return
    
    # Executar loop de monitoramento
    asyncio.run(monitor.monitor_loop())


if __name__ == "__main__":
    main() 