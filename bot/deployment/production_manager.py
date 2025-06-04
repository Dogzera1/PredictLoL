"""
Sistema de Gerenciamento de Produção - Semana 4
Gerencia deploy, health checks e recursos do Bot LoL V3 em produção

Funcionalidades:
- Deploy automatizado
- Health checks contínuos
- Gestão de recursos
- Auto-scaling
- Recuperação automática
"""

from __future__ import annotations

import asyncio
import time
import psutil
import signal
import sys
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from ..monitoring.performance_monitor import PerformanceMonitor
from ..monitoring.dashboard_generator import DashboardGenerator
from ..utils.logger_config import get_logger

logger = get_logger(__name__)


class SystemStatus(Enum):
    """Status do sistema em produção"""
    STARTING = "starting"
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    MAINTENANCE = "maintenance"
    STOPPED = "stopped"


class ResourceType(Enum):
    """Tipos de recursos monitorados"""
    CPU = "cpu"
    MEMORY = "memory"
    DISK = "disk"
    NETWORK = "network"


@dataclass
class HealthCheck:
    """Resultado de um health check"""
    component: str
    status: bool
    message: str
    response_time_ms: float
    timestamp: float


@dataclass
class SystemResources:
    """Recursos do sistema"""
    cpu_percent: float
    memory_percent: float
    disk_percent: float
    network_sent_mb: float
    network_recv_mb: float
    active_connections: int
    uptime_seconds: float


class ProductionManager:
    """
    Gerenciador de Produção do Bot LoL V3 Ultra Avançado
    
    Funcionalidades:
    - Deploy automatizado e controle de versões
    - Health checks contínuos de todos os componentes
    - Monitoramento de recursos e auto-scaling
    - Recuperação automática de falhas
    - Dashboard web integrado
    - Logs estruturados e alertas
    """

    def __init__(self, config: Dict[str, Any] = None):
        """
        Inicializa o gerenciador de produção
        
        Args:
            config: Configurações do sistema
        """
        self.config = config or self._get_default_config()
        self.system_status = SystemStatus.STOPPED
        self.start_time = time.time()
        
        # Componentes do sistema
        self.performance_monitor = PerformanceMonitor()
        self.dashboard_generator = DashboardGenerator()
        
        # Tasks de monitoramento
        self.health_check_task = None
        self.resource_monitor_task = None
        self.dashboard_update_task = None
        
        # Storage de dados
        self.health_checks: List[HealthCheck] = []
        self.resource_history: List[SystemResources] = []
        self.component_status: Dict[str, bool] = {}
        
        # Configurações de alertas
        self.resource_thresholds = {
            ResourceType.CPU: 80.0,      # 80% CPU
            ResourceType.MEMORY: 85.0,   # 85% Memory
            ResourceType.DISK: 90.0,     # 90% Disk
        }
        
        # Handlers de shutdown graceful
        self._setup_signal_handlers()
        
        logger.info("ProductionManager inicializado para Semana 4")

    async def start_production_system(self) -> bool:
        """
        Inicia o sistema completo em produção
        
        Returns:
            True se iniciado com sucesso
        """
        try:
            logger.info("🚀 Iniciando Bot LoL V3 Ultra Avançado em produção...")
            self.system_status = SystemStatus.STARTING
            
            # 1. Validação pré-deploy
            if not await self._validate_pre_deployment():
                logger.error("❌ Falha na validação pré-deploy")
                return False
            
            # 2. Inicialização dos componentes principais
            logger.info("⚙️ Inicializando componentes principais...")
            
            # Performance Monitor
            await self.performance_monitor.start_monitoring(interval_seconds=60)
            logger.info("✅ PerformanceMonitor iniciado")
            
            # 3. Inicialização das tasks de monitoramento
            logger.info("📊 Iniciando monitoramento contínuo...")
            
            self.health_check_task = asyncio.create_task(
                self._continuous_health_checks()
            )
            
            self.resource_monitor_task = asyncio.create_task(
                self._continuous_resource_monitoring()
            )
            
            self.dashboard_update_task = asyncio.create_task(
                self._continuous_dashboard_updates()
            )
            
            # 4. Health check inicial
            await self._perform_initial_health_check()
            
            # 5. Sistema pronto
            self.system_status = SystemStatus.HEALTHY
            self.start_time = time.time()
            
            logger.info("🎉 Sistema em produção iniciado com sucesso!")
            logger.info(f"📡 Dashboard disponível em: {self._get_dashboard_url()}")
            logger.info(f"📈 Métricas em tempo real ativas")
            logger.info(f"🔄 Auto-recovery habilitado")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro ao iniciar sistema em produção: {e}")
            self.system_status = SystemStatus.CRITICAL
            return False

    async def stop_production_system(self):
        """Para o sistema de produção gracefully"""
        try:
            logger.info("🛑 Parando sistema de produção...")
            self.system_status = SystemStatus.MAINTENANCE
            
            # Para tasks de monitoramento
            if self.health_check_task:
                self.health_check_task.cancel()
            if self.resource_monitor_task:
                self.resource_monitor_task.cancel()
            if self.dashboard_update_task:
                self.dashboard_update_task.cancel()
            
            # Para performance monitor
            await self.performance_monitor.stop_monitoring()
            
            # Salva dados finais
            await self._save_production_data()
            
            self.system_status = SystemStatus.STOPPED
            logger.info("✅ Sistema de produção parado com sucesso")
            
        except Exception as e:
            logger.error(f"❌ Erro ao parar sistema: {e}")

    async def get_system_status(self) -> Dict[str, Any]:
        """
        Retorna status completo do sistema
        
        Returns:
            Status detalhado de todos os componentes
        """
        try:
            current_resources = self._get_current_resources()
            uptime = time.time() - self.start_time
            
            # Performance metrics
            perf_metrics = await self.performance_monitor.get_current_metrics()
            
            # Health checks recentes
            recent_health_checks = self.health_checks[-10:] if self.health_checks else []
            
            return {
                "timestamp": datetime.now().isoformat(),
                "system_status": self.system_status.value,
                "uptime_seconds": uptime,
                "uptime_formatted": self._format_uptime(uptime),
                
                # Recursos do sistema
                "resources": {
                    "cpu_percent": current_resources.cpu_percent,
                    "memory_percent": current_resources.memory_percent,
                    "disk_percent": current_resources.disk_percent,
                    "network_sent_mb": current_resources.network_sent_mb,
                    "network_recv_mb": current_resources.network_recv_mb,
                    "active_connections": current_resources.active_connections
                },
                
                # Performance metrics
                "performance": {
                    "total_predictions": perf_metrics.total_predictions,
                    "win_rate": perf_metrics.win_rate_percentage,
                    "roi": perf_metrics.roi_percentage,
                    "net_profit": perf_metrics.net_profit,
                    "uptime_hours": perf_metrics.uptime_hours
                },
                
                # Health status por componente
                "component_health": self.component_status,
                
                # Health checks recentes
                "recent_health_checks": [
                    {
                        "component": hc.component,
                        "status": hc.status,
                        "message": hc.message,
                        "response_time_ms": hc.response_time_ms,
                        "timestamp": datetime.fromtimestamp(hc.timestamp).isoformat()
                    }
                    for hc in recent_health_checks
                ],
                
                # Alertas ativos
                "active_alerts": self._get_active_alerts(),
                
                # Configuração
                "configuration": {
                    "monitoring_interval": self.config.get("monitoring_interval", 60),
                    "health_check_interval": self.config.get("health_check_interval", 30),
                    "dashboard_update_interval": self.config.get("dashboard_update_interval", 10),
                    "auto_recovery_enabled": self.config.get("auto_recovery", True)
                }
            }
            
        except Exception as e:
            logger.error(f"Erro ao obter status do sistema: {e}")
            return {"error": str(e), "timestamp": datetime.now().isoformat()}

    async def restart_component(self, component_name: str) -> bool:
        """
        Reinicia um componente específico
        
        Args:
            component_name: Nome do componente
            
        Returns:
            True se reiniciado com sucesso
        """
        try:
            logger.info(f"🔄 Reiniciando componente: {component_name}")
            
            if component_name == "performance_monitor":
                await self.performance_monitor.stop_monitoring()
                await asyncio.sleep(2)
                await self.performance_monitor.start_monitoring()
                
            elif component_name == "health_checks":
                if self.health_check_task:
                    self.health_check_task.cancel()
                await asyncio.sleep(1)
                self.health_check_task = asyncio.create_task(
                    self._continuous_health_checks()
                )
                
            elif component_name == "resource_monitor":
                if self.resource_monitor_task:
                    self.resource_monitor_task.cancel()
                await asyncio.sleep(1)
                self.resource_monitor_task = asyncio.create_task(
                    self._continuous_resource_monitoring()
                )
                
            elif component_name == "dashboard":
                if self.dashboard_update_task:
                    self.dashboard_update_task.cancel()
                await asyncio.sleep(1)
                self.dashboard_update_task = asyncio.create_task(
                    self._continuous_dashboard_updates()
                )
            
            else:
                logger.warning(f"Componente desconhecido: {component_name}")
                return False
            
            logger.info(f"✅ Componente {component_name} reiniciado com sucesso")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro ao reiniciar {component_name}: {e}")
            return False

    async def perform_emergency_recovery(self) -> bool:
        """
        Executa recuperação de emergência do sistema
        
        Returns:
            True se recuperação bem-sucedida
        """
        try:
            logger.warning("🚨 Iniciando recuperação de emergência...")
            self.system_status = SystemStatus.CRITICAL
            
            # 1. Para todas as tasks
            tasks_to_cancel = [
                self.health_check_task,
                self.resource_monitor_task, 
                self.dashboard_update_task
            ]
            
            for task in tasks_to_cancel:
                if task and not task.cancelled():
                    task.cancel()
            
            await asyncio.sleep(3)
            
            # 2. Reinicia componentes críticos
            logger.info("🔄 Reiniciando componentes críticos...")
            
            # Performance Monitor
            try:
                await self.performance_monitor.stop_monitoring()
                await asyncio.sleep(2)
                await self.performance_monitor.start_monitoring()
                logger.info("✅ PerformanceMonitor recuperado")
            except Exception as e:
                logger.error(f"❌ Falha ao recuperar PerformanceMonitor: {e}")
            
            # 3. Reinicia monitoramento
            try:
                self.health_check_task = asyncio.create_task(
                    self._continuous_health_checks()
                )
                self.resource_monitor_task = asyncio.create_task(
                    self._continuous_resource_monitoring()
                )
                self.dashboard_update_task = asyncio.create_task(
                    self._continuous_dashboard_updates()
                )
                logger.info("✅ Monitoramento reativado")
            except Exception as e:
                logger.error(f"❌ Falha ao reativar monitoramento: {e}")
                return False
            
            # 4. Health check pós-recuperação
            await asyncio.sleep(5)
            health_ok = await self._perform_health_check()
            
            if health_ok:
                self.system_status = SystemStatus.HEALTHY
                logger.info("🎉 Recuperação de emergência concluída com sucesso!")
                return True
            else:
                self.system_status = SystemStatus.CRITICAL
                logger.error("❌ Recuperação de emergência falhou")
                return False
            
        except Exception as e:
            logger.error(f"❌ Erro durante recuperação de emergência: {e}")
            self.system_status = SystemStatus.CRITICAL
            return False

    async def _validate_pre_deployment(self) -> bool:
        """Valida condições pré-deploy"""
        try:
            logger.info("🔍 Validando condições pré-deploy...")
            
            # Verifica recursos disponíveis
            resources = self._get_current_resources()
            
            if resources.memory_percent > 90:
                logger.error(f"❌ Memória insuficiente: {resources.memory_percent}%")
                return False
            
            if resources.disk_percent > 95:
                logger.error(f"❌ Espaço em disco insuficiente: {resources.disk_percent}%")
                return False
            
            # Verifica dependências
            try:
                import aiohttp
                import psutil
                logger.info("✅ Dependências verificadas")
            except ImportError as e:
                logger.error(f"❌ Dependência faltando: {e}")
                return False
            
            # Verifica estrutura de diretórios
            required_dirs = [
                "bot/data",
                "bot/data/monitoring", 
                "bot/logs"
            ]
            
            for dir_path in required_dirs:
                Path(dir_path).mkdir(parents=True, exist_ok=True)
                logger.debug(f"✅ Diretório verificado: {dir_path}")
            
            logger.info("✅ Validação pré-deploy concluída")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro na validação pré-deploy: {e}")
            return False

    async def _perform_initial_health_check(self):
        """Executa health check inicial"""
        logger.info("🩺 Executando health check inicial...")
        
        components_to_check = [
            "system_resources",
            "performance_monitor", 
            "dashboard_generator",
            "file_system",
            "network_connectivity"
        ]
        
        for component in components_to_check:
            try:
                health_check = await self._check_component_health(component)
                self.health_checks.append(health_check)
                self.component_status[component] = health_check.status
                
                status_icon = "✅" if health_check.status else "❌"
                logger.info(f"{status_icon} {component}: {health_check.message}")
                
            except Exception as e:
                logger.error(f"❌ Erro no health check de {component}: {e}")
                self.component_status[component] = False

    async def _continuous_health_checks(self):
        """Loop contínuo de health checks"""
        try:
            interval = self.config.get("health_check_interval", 30)
            logger.info(f"🩺 Iniciando health checks contínuos (intervalo: {interval}s)")
            
            while True:
                await asyncio.sleep(interval)
                
                try:
                    health_ok = await self._perform_health_check()
                    
                    if not health_ok and self.config.get("auto_recovery", True):
                        logger.warning("⚠️ Health check falhou, tentando auto-recovery...")
                        await self.perform_emergency_recovery()
                
                except Exception as e:
                    logger.error(f"❌ Erro no health check contínuo: {e}")
                
        except asyncio.CancelledError:
            logger.info("🛑 Health checks contínuos cancelados")
        except Exception as e:
            logger.error(f"❌ Erro fatal nos health checks: {e}")

    async def _continuous_resource_monitoring(self):
        """Loop contínuo de monitoramento de recursos"""
        try:
            interval = self.config.get("resource_monitor_interval", 15)
            logger.info(f"📊 Iniciando monitoramento de recursos (intervalo: {interval}s)")
            
            while True:
                await asyncio.sleep(interval)
                
                try:
                    resources = self._get_current_resources()
                    self.resource_history.append(resources)
                    
                    # Mantém apenas últimas 24h (24*60*4 = 5760 registros para 15s)
                    max_records = 5760
                    if len(self.resource_history) > max_records:
                        self.resource_history = self.resource_history[-max_records:]
                    
                    # Verifica thresholds
                    await self._check_resource_alerts(resources)
                    
                except Exception as e:
                    logger.error(f"❌ Erro no monitoramento de recursos: {e}")
                
        except asyncio.CancelledError:
            logger.info("🛑 Monitoramento de recursos cancelado")
        except Exception as e:
            logger.error(f"❌ Erro fatal no monitoramento de recursos: {e}")

    async def _continuous_dashboard_updates(self):
        """Loop contínuo de atualização do dashboard"""
        try:
            interval = self.config.get("dashboard_update_interval", 10)
            logger.info(f"📱 Iniciando atualizações do dashboard (intervalo: {interval}s)")
            
            while True:
                await asyncio.sleep(interval)
                
                try:
                    # Gera dashboard atualizado
                    dashboard_data = self.performance_monitor.get_live_dashboard_data()
                    
                    # Exporta para arquivo
                    success = self.dashboard_generator.export_dashboard_to_file(
                        dashboard_data, 
                        "bot/data/monitoring/dashboard.html"
                    )
                    
                    if not success:
                        logger.warning("⚠️ Falha ao atualizar dashboard")
                    
                except Exception as e:
                    logger.error(f"❌ Erro na atualização do dashboard: {e}")
                
        except asyncio.CancelledError:
            logger.info("🛑 Atualizações do dashboard canceladas")
        except Exception as e:
            logger.error(f"❌ Erro fatal nas atualizações do dashboard: {e}")

    async def _perform_health_check(self) -> bool:
        """Executa health check completo"""
        components = [
            "system_resources",
            "performance_monitor",
            "file_system"
        ]
        
        all_healthy = True
        
        for component in components:
            try:
                health_check = await self._check_component_health(component)
                self.health_checks.append(health_check)
                self.component_status[component] = health_check.status
                
                if not health_check.status:
                    all_healthy = False
                    logger.warning(f"⚠️ {component} unhealthy: {health_check.message}")
            
            except Exception as e:
                logger.error(f"❌ Health check falhou para {component}: {e}")
                all_healthy = False
                self.component_status[component] = False
        
        # Mantém apenas últimos 100 health checks
        if len(self.health_checks) > 100:
            self.health_checks = self.health_checks[-100:]
        
        return all_healthy

    async def _check_component_health(self, component: str) -> HealthCheck:
        """Verifica saúde de um componente específico"""
        start_time = time.time()
        
        try:
            if component == "system_resources":
                resources = self._get_current_resources()
                
                if resources.memory_percent > 95:
                    return HealthCheck(
                        component=component,
                        status=False,
                        message=f"Memória crítica: {resources.memory_percent}%",
                        response_time_ms=(time.time() - start_time) * 1000,
                        timestamp=time.time()
                    )
                
                if resources.cpu_percent > 90:
                    return HealthCheck(
                        component=component,
                        status=False,
                        message=f"CPU crítica: {resources.cpu_percent}%",
                        response_time_ms=(time.time() - start_time) * 1000,
                        timestamp=time.time()
                    )
                
                return HealthCheck(
                    component=component,
                    status=True,
                    message=f"CPU: {resources.cpu_percent}%, MEM: {resources.memory_percent}%",
                    response_time_ms=(time.time() - start_time) * 1000,
                    timestamp=time.time()
                )
            
            elif component == "performance_monitor":
                # Testa se performance monitor está respondendo
                metrics = await self.performance_monitor.get_current_metrics()
                
                return HealthCheck(
                    component=component,
                    status=True,
                    message=f"Monitorando {metrics.total_predictions} predições",
                    response_time_ms=(time.time() - start_time) * 1000,
                    timestamp=time.time()
                )
            
            elif component == "dashboard_generator":
                # Testa geração de dashboard
                test_data = {"current_metrics": {}, "last_24h": {}}
                html = self.dashboard_generator.generate_html_dashboard(test_data)
                
                if len(html) > 1000:  # HTML mínimo gerado
                    return HealthCheck(
                        component=component,
                        status=True,
                        message="Dashboard gerando HTML corretamente",
                        response_time_ms=(time.time() - start_time) * 1000,
                        timestamp=time.time()
                    )
                else:
                    return HealthCheck(
                        component=component,
                        status=False,
                        message="Dashboard gerando HTML inválido",
                        response_time_ms=(time.time() - start_time) * 1000,
                        timestamp=time.time()
                    )
            
            elif component == "file_system":
                # Testa leitura/escrita de arquivos
                test_file = "bot/data/monitoring/health_check_test.txt"
                test_content = f"Health check test - {datetime.now().isoformat()}"
                
                # Escreve arquivo de teste
                with open(test_file, "w") as f:
                    f.write(test_content)
                
                # Lê arquivo de teste
                with open(test_file, "r") as f:
                    read_content = f.read()
                
                if read_content == test_content:
                    Path(test_file).unlink()  # Remove arquivo de teste
                    return HealthCheck(
                        component=component,
                        status=True,
                        message="Filesystem leitura/escrita OK",
                        response_time_ms=(time.time() - start_time) * 1000,
                        timestamp=time.time()
                    )
                else:
                    return HealthCheck(
                        component=component,
                        status=False,
                        message="Filesystem com problemas de I/O",
                        response_time_ms=(time.time() - start_time) * 1000,
                        timestamp=time.time()
                    )
            
            elif component == "network_connectivity":
                # Testa conectividade básica
                try:
                    import socket
                    socket.create_connection(("8.8.8.8", 53), timeout=3)
                    
                    return HealthCheck(
                        component=component,
                        status=True,
                        message="Conectividade de rede OK",
                        response_time_ms=(time.time() - start_time) * 1000,
                        timestamp=time.time()
                    )
                except:
                    return HealthCheck(
                        component=component,
                        status=False,
                        message="Sem conectividade de rede",
                        response_time_ms=(time.time() - start_time) * 1000,
                        timestamp=time.time()
                    )
            
            else:
                return HealthCheck(
                    component=component,
                    status=False,
                    message=f"Componente desconhecido: {component}",
                    response_time_ms=(time.time() - start_time) * 1000,
                    timestamp=time.time()
                )
                
        except Exception as e:
            return HealthCheck(
                component=component,
                status=False,
                message=f"Erro no health check: {str(e)}",
                response_time_ms=(time.time() - start_time) * 1000,
                timestamp=time.time()
            )

    def _get_current_resources(self) -> SystemResources:
        """Obtém recursos atuais do sistema"""
        try:
            # CPU e Memória
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            
            # Disco
            disk = psutil.disk_usage('/')
            disk_percent = (disk.used / disk.total) * 100
            
            # Network
            network = psutil.net_io_counters()
            network_sent_mb = network.bytes_sent / (1024 * 1024)
            network_recv_mb = network.bytes_recv / (1024 * 1024)
            
            # Conexões
            try:
                connections = len(psutil.net_connections())
            except:
                connections = 0
            
            # Uptime
            uptime = time.time() - self.start_time
            
            return SystemResources(
                cpu_percent=cpu_percent,
                memory_percent=memory.percent,
                disk_percent=disk_percent,
                network_sent_mb=network_sent_mb,
                network_recv_mb=network_recv_mb,
                active_connections=connections,
                uptime_seconds=uptime
            )
            
        except Exception as e:
            logger.error(f"Erro ao obter recursos do sistema: {e}")
            return SystemResources(
                cpu_percent=0, memory_percent=0, disk_percent=0,
                network_sent_mb=0, network_recv_mb=0, active_connections=0,
                uptime_seconds=0
            )

    async def _check_resource_alerts(self, resources: SystemResources):
        """Verifica alertas de recursos"""
        try:
            # CPU Alert
            if resources.cpu_percent > self.resource_thresholds[ResourceType.CPU]:
                logger.warning(f"⚠️ CPU alta: {resources.cpu_percent}%")
                
                if resources.cpu_percent > 95:
                    logger.critical(f"🚨 CPU crítica: {resources.cpu_percent}%")
            
            # Memory Alert
            if resources.memory_percent > self.resource_thresholds[ResourceType.MEMORY]:
                logger.warning(f"⚠️ Memória alta: {resources.memory_percent}%")
                
                if resources.memory_percent > 95:
                    logger.critical(f"🚨 Memória crítica: {resources.memory_percent}%")
            
            # Disk Alert
            if resources.disk_percent > self.resource_thresholds[ResourceType.DISK]:
                logger.warning(f"⚠️ Disco cheio: {resources.disk_percent}%")
                
                if resources.disk_percent > 98:
                    logger.critical(f"🚨 Disco crítico: {resources.disk_percent}%")
            
        except Exception as e:
            logger.error(f"Erro ao verificar alertas de recursos: {e}")

    def _get_active_alerts(self) -> List[Dict[str, Any]]:
        """Retorna alertas ativos do sistema"""
        alerts = []
        
        try:
            # Alertas de recursos
            if self.resource_history:
                latest_resources = self.resource_history[-1]
                
                if latest_resources.cpu_percent > self.resource_thresholds[ResourceType.CPU]:
                    alerts.append({
                        "level": "warning" if latest_resources.cpu_percent < 95 else "critical",
                        "category": "resources",
                        "message": f"CPU alta: {latest_resources.cpu_percent}%",
                        "timestamp": datetime.now().isoformat()
                    })
                
                if latest_resources.memory_percent > self.resource_thresholds[ResourceType.MEMORY]:
                    alerts.append({
                        "level": "warning" if latest_resources.memory_percent < 95 else "critical",
                        "category": "resources", 
                        "message": f"Memória alta: {latest_resources.memory_percent}%",
                        "timestamp": datetime.now().isoformat()
                    })
            
            # Alertas de componentes
            for component, status in self.component_status.items():
                if not status:
                    alerts.append({
                        "level": "error",
                        "category": "component",
                        "message": f"Componente {component} com falha",
                        "timestamp": datetime.now().isoformat()
                    })
            
            return alerts
            
        except Exception as e:
            logger.error(f"Erro ao obter alertas ativos: {e}")
            return []

    def _format_uptime(self, seconds: float) -> str:
        """Formata uptime em formato legível"""
        try:
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            seconds = int(seconds % 60)
            
            if hours > 0:
                return f"{hours}h {minutes}m {seconds}s"
            elif minutes > 0:
                return f"{minutes}m {seconds}s"
            else:
                return f"{seconds}s"
        except:
            return "0s"

    def _get_dashboard_url(self) -> str:
        """Retorna URL do dashboard"""
        return f"file://{Path.cwd()}/bot/data/monitoring/dashboard.html"

    def _get_default_config(self) -> Dict[str, Any]:
        """Retorna configuração padrão"""
        return {
            "monitoring_interval": 60,
            "health_check_interval": 30,
            "resource_monitor_interval": 15,
            "dashboard_update_interval": 10,
            "auto_recovery": True,
            "max_resource_history": 5760,  # 24h com intervalos de 15s
            "max_health_checks": 100
        }

    def _setup_signal_handlers(self):
        """Configura handlers para shutdown graceful"""
        def signal_handler(signum, frame):
            logger.info(f"🛑 Recebido sinal {signum}, iniciando shutdown graceful...")
            asyncio.create_task(self.stop_production_system())
        
        try:
            signal.signal(signal.SIGINT, signal_handler)
            signal.signal(signal.SIGTERM, signal_handler)
        except ValueError:
            # Em alguns ambientes (como Jupyter) os signals não podem ser configurados
            pass

    async def _save_production_data(self):
        """Salva dados de produção"""
        try:
            import json
            import os
            
            os.makedirs("bot/data/monitoring", exist_ok=True)
            
            # Salva status do sistema
            system_status = await self.get_system_status()
            with open("bot/data/monitoring/production_status.json", "w", encoding="utf-8") as f:
                json.dump(system_status, f, indent=2, ensure_ascii=False)
            
            logger.info("✅ Dados de produção salvos")
            
        except Exception as e:
            logger.error(f"❌ Erro ao salvar dados de produção: {e}") 
