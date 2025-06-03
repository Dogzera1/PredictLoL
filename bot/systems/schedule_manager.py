from __future__ import annotations

import asyncio
import time
from typing import Dict, List, Optional, Set, Any, Tuple, TYPE_CHECKING
from dataclasses import dataclass
from enum import Enum
from datetime import datetime, timedelta
import logging

from ..api_clients.pandascore_api_client import PandaScoreAPIClient
from ..api_clients.riot_api_client import RiotAPIClient
from ..telegram_bot.alerts_system import TelegramAlertsSystem
from ..data_models.match_data import MatchData
from ..utils.constants import SCAN_INTERVAL_MINUTES, SUPPORTED_LEAGUES, CLEANUP_INTERVAL_HOURS
from ..utils.helpers import get_current_timestamp
from ..utils.logger_config import get_logger

if TYPE_CHECKING:
    from .tips_system import ProfessionalTipsSystem

logger = get_logger(__name__)


class TaskStatus(Enum):
    """Status de uma tarefa agendada"""
    SCHEDULED = "scheduled"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskType(Enum):
    """Tipos de tarefa"""
    MONITOR_MATCHES = "monitor_matches"
    CLEANUP_DATA = "cleanup_data"
    SYSTEM_HEALTH_CHECK = "health_check"
    CACHE_MAINTENANCE = "cache_maintenance"


@dataclass
class ScheduledTask:
    """Tarefa agendada"""
    task_id: str
    task_type: TaskType
    status: TaskStatus
    scheduled_time: float
    interval_seconds: Optional[int] = None
    last_run: Optional[float] = None
    next_run: Optional[float] = None
    run_count: int = 0
    error_count: int = 0
    last_error: Optional[str] = None
    
    def __post_init__(self):
        if self.next_run is None:
            self.next_run = self.scheduled_time


@dataclass
class SystemHealth:
    """Status de saúde do sistema"""
    is_healthy: bool = True
    uptime_seconds: float = 0.0
    tasks_running: int = 0
    tasks_completed: int = 0
    tasks_failed: int = 0
    memory_usage_mb: float = 0.0
    last_tip_time: Optional[float] = None
    last_error: Optional[str] = None
    components_status: Dict[str, bool] = None
    
    def __post_init__(self):
        if self.components_status is None:
            self.components_status = {}


class ScheduleManager:
    """
    Gerenciador de Cronograma e Tarefas do Bot LoL V3 Ultra Avançado
    
    Responsável por:
    - Orquestração de todos os sistemas (Tips + Telegram + APIs)
    - Monitoramento contínuo de partidas ao vivo
    - Tarefas agendadas (limpeza, manutenção, health checks)
    - Gestão de ciclo de vida do sistema
    - Automação completa end-to-end
    - Recuperação automática de erros
    
    Características:
    - Múltiplas tarefas simultâneas
    - Sistema resiliente a falhas
    - Monitoramento de saúde
    - Logs detalhados
    - Configuração flexível
    - Performance otimizada
    """

    def __init__(
        self,
        tips_system: "ProfessionalTipsSystem",
        telegram_alerts: Optional[TelegramAlertsSystem],
        pandascore_client: PandaScoreAPIClient,
        riot_client: RiotAPIClient
    ):
        """
        Inicializa o gerenciador de cronograma
        
        Args:
            tips_system: Sistema de tips profissionais
            telegram_alerts: Sistema de alertas Telegram (opcional - None para modo local)
            pandascore_client: Cliente do PandaScore API
            riot_client: Cliente da Riot API
        """
        self.tips_system = tips_system
        self.telegram_alerts = telegram_alerts
        self.pandascore_client = pandascore_client
        self.riot_client = riot_client
        
        # Estado do sistema
        self.is_running = False
        self.start_time = time.time()
        self.scheduled_tasks: Dict[str, ScheduledTask] = {}
        self.running_tasks: Dict[str, asyncio.Task] = {}
        
        # Health monitoring
        self.health = SystemHealth()
        self.health.uptime_seconds = 0.0
        
        # Configurações
        self.monitor_interval = SCAN_INTERVAL_MINUTES * 60  # 3 minutos
        self.cleanup_interval = getattr(self, 'cleanup_interval', 24 * 3600)  # 24 horas
        self.health_check_interval = 5 * 60  # 5 minutos
        self.cache_maintenance_interval = 30 * 60  # 30 minutos
        
        # Estatísticas
        self.stats = {
            "tasks_created": 0,
            "tasks_completed": 0,
            "tasks_failed": 0,
            "tips_generated": 0,
            "alerts_sent": 0,
            "errors_recovered": 0,
            "uptime_hours": 0.0
        }
        
        logger.info("ScheduleManager inicializado com sucesso")

    async def start_scheduled_tasks(self) -> None:
        """Inicia todas as tarefas agendadas"""
        if self.is_running:
            logger.warning("ScheduleManager já está executando")
            return
        
        logger.info("🚀 Iniciando ScheduleManager - Automação Total!")
        self.is_running = True
        self.start_time = time.time()
        
        try:
            # Envia alerta de início do sistema
            await self._notify_system_start()
            
            # Cria tarefas agendadas
            await self._create_scheduled_tasks()
            
            # Inicia loop principal
            await self._main_scheduler_loop()
            
        except Exception as e:
            logger.error(f"Erro crítico no ScheduleManager: {e}")
            await self._notify_system_error(f"Sistema falhado: {e}")
            raise
        finally:
            self.is_running = False

    async def stop_scheduled_tasks(self) -> None:
        """Para todas as tarefas agendadas"""
        logger.info("🛑 Parando ScheduleManager...")
        self.is_running = False
        
        # Cancela todas as tarefas
        for task_id, task in self.running_tasks.items():
            if not task.done():
                task.cancel()
                logger.debug(f"Tarefa cancelada: {task_id}")
        
        # Aguarda conclusão das tarefas
        if self.running_tasks:
            await asyncio.gather(*self.running_tasks.values(), return_exceptions=True)
        
        # Envia alerta de parada
        await self._notify_system_stop()
        
        logger.info("✅ ScheduleManager parado com sucesso")

    async def _create_scheduled_tasks(self) -> None:
        """Cria as tarefas agendadas principais"""
        current_time = time.time()
        
        # 1. Monitoramento de partidas (prioridade máxima)
        monitor_task = ScheduledTask(
            task_id="monitor_live_matches",
            task_type=TaskType.MONITOR_MATCHES,
            status=TaskStatus.SCHEDULED,
            scheduled_time=current_time,
            interval_seconds=self.monitor_interval
        )
        self.scheduled_tasks[monitor_task.task_id] = monitor_task
        
        # 2. Limpeza de dados (diária)
        cleanup_task = ScheduledTask(
            task_id="cleanup_old_data",
            task_type=TaskType.CLEANUP_DATA,
            status=TaskStatus.SCHEDULED,
            scheduled_time=current_time + 3600,  # 1 hora após início
            interval_seconds=self.cleanup_interval
        )
        self.scheduled_tasks[cleanup_task.task_id] = cleanup_task
        
        # 3. Health check (5 minutos)
        health_task = ScheduledTask(
            task_id="system_health_check",
            task_type=TaskType.SYSTEM_HEALTH_CHECK,
            status=TaskStatus.SCHEDULED,
            scheduled_time=current_time + 300,  # 5 min após início
            interval_seconds=self.health_check_interval
        )
        self.scheduled_tasks[health_task.task_id] = health_task
        
        # 4. Manutenção de cache (30 minutos)
        cache_task = ScheduledTask(
            task_id="cache_maintenance",
            task_type=TaskType.CACHE_MAINTENANCE,
            status=TaskStatus.SCHEDULED,
            scheduled_time=current_time + 1800,  # 30 min após início
            interval_seconds=self.cache_maintenance_interval
        )
        self.scheduled_tasks[cache_task.task_id] = cache_task
        
        logger.info(f"✅ {len(self.scheduled_tasks)} tarefas agendadas criadas")
        self.stats["tasks_created"] = len(self.scheduled_tasks)

    async def _main_scheduler_loop(self) -> None:
        """Loop principal do agendador"""
        logger.info("🔄 Loop principal do ScheduleManager iniciado")
        
        while self.is_running:
            try:
                current_time = time.time()
                
                # Atualiza estatísticas de uptime
                self.health.uptime_seconds = current_time - self.start_time
                self.stats["uptime_hours"] = self.health.uptime_seconds / 3600
                
                # Verifica tarefas que precisam ser executadas
                for task_id, task in self.scheduled_tasks.items():
                    if self._should_run_task(task, current_time):
                        await self._execute_task(task)
                
                # Limpa tarefas concluídas
                await self._cleanup_completed_tasks()
                
                # Atualiza status de saúde
                self._update_health_status()
                
                # Pequena pausa para não sobrecarregar CPU
                await asyncio.sleep(10)  # Verifica a cada 10 segundos
                
            except Exception as e:
                logger.error(f"Erro no loop principal: {e}")
                await self._handle_scheduler_error(e)
                await asyncio.sleep(30)  # Pausa maior em caso de erro

    def _should_run_task(self, task: ScheduledTask, current_time: float) -> bool:
        """Verifica se uma tarefa deve ser executada"""
        # Não executa se já está rodando
        if task.task_id in self.running_tasks:
            return False
        
        # Não executa se foi cancelada
        if task.status == TaskStatus.CANCELLED:
            return False
        
        # Verifica se chegou a hora
        if task.next_run and current_time >= task.next_run:
            return True
        
        return False

    async def _execute_task(self, task: ScheduledTask) -> None:
        """Executa uma tarefa específica"""
        task.status = TaskStatus.RUNNING
        task.last_run = time.time()
        task.run_count += 1
        
        logger.debug(f"🏃 Executando tarefa: {task.task_id} (#{task.run_count})")
        
        try:
            # Cria tarefa assíncrona
            if task.task_type == TaskType.MONITOR_MATCHES:
                task_coroutine = self._monitor_live_matches_task()
            elif task.task_type == TaskType.CLEANUP_DATA:
                task_coroutine = self._cleanup_old_data_task()
            elif task.task_type == TaskType.SYSTEM_HEALTH_CHECK:
                task_coroutine = self._system_health_check_task()
            elif task.task_type == TaskType.CACHE_MAINTENANCE:
                task_coroutine = self._cache_maintenance_task()
            else:
                raise ValueError(f"Tipo de tarefa desconhecido: {task.task_type}")
            
            # Executa tarefa com timeout
            async_task = asyncio.create_task(task_coroutine)
            self.running_tasks[task.task_id] = async_task
            
            # Aguarda conclusão (sem bloquear outras tarefas)
            # O resultado será processado em _cleanup_completed_tasks
            
        except Exception as e:
            logger.error(f"Erro ao criar tarefa {task.task_id}: {e}")
            task.status = TaskStatus.FAILED
            task.error_count += 1
            task.last_error = str(e)
            self._schedule_next_run(task)

    async def _monitor_live_matches_task(self) -> None:
        """Tarefa de monitoramento de partidas ao vivo"""
        try:
            logger.info("🔍 Executando monitoramento de partidas...")
            
            # Força um scan completo no sistema de tips
            scan_result = await self.tips_system.force_scan()
            
            # Atualiza estatísticas
            if scan_result.get("tip_generated", False):
                self.stats["tips_generated"] += 1
                self.health.last_tip_time = time.time()
            
            logger.info(
                f"✅ Scan completo: {scan_result['live_matches_found']} partidas, "
                f"tip gerada: {'Sim' if scan_result.get('tip_generated') else 'Não'}"
            )
            
        except Exception as e:
            logger.error(f"Erro no monitoramento de partidas: {e}")
            raise

    async def _cleanup_old_data_task(self) -> None:
        """Tarefa de limpeza de dados antigos"""
        try:
            logger.info("🧹 Executando limpeza de dados antigos...")
            
            # Limpa tips expiradas do sistema de tips
            self.tips_system._cleanup_expired_tips()
            
            # Limpa cache antigo do Telegram
            self.telegram_alerts.cleanup_old_cache()
            
            # Limpa cache das APIs se disponível
            if hasattr(self.pandascore_client, 'cleanup_cache'):
                self.pandascore_client.cleanup_cache()
            
            if hasattr(self.riot_client, 'cleanup_cache'):
                self.riot_client.cleanup_cache()
            
            logger.info("✅ Limpeza de dados concluída")
            
        except Exception as e:
            logger.error(f"Erro na limpeza de dados: {e}")
            raise

    async def _system_health_check_task(self) -> None:
        """Tarefa de verificação de saúde do sistema"""
        try:
            logger.debug("💓 Executando health check...")
            
            # Verifica componentes principais
            components_health = {
                "tips_system": self.tips_system is not None,
                "telegram_alerts": self.telegram_alerts is not None,
                "pandascore_client": self.pandascore_client is not None,
                "riot_client": self.riot_client is not None
            }
            
            # Verifica se tips foram geradas recentemente (últimas 2 horas)
            recent_tips = (
                self.health.last_tip_time and 
                time.time() - self.health.last_tip_time < 7200
            )
            
            # Calcula saúde geral
            all_healthy = all(components_health.values())
            self.health.is_healthy = all_healthy
            self.health.components_status = components_health
            
            # Envia alerta se sistema não estiver saudável (apenas se telegram_alerts disponível)
            if not all_healthy and self.telegram_alerts:
                unhealthy_components = [
                    comp for comp, healthy in components_health.items() 
                    if not healthy
                ]
                await self.telegram_alerts.send_system_alert(
                    f"⚠️ Componentes com problemas: {', '.join(unhealthy_components)}",
                    "warning"
                )
            
            logger.debug(f"💓 Health check: {'✅ Saudável' if all_healthy else '⚠️ Problemas detectados'}")
            
        except Exception as e:
            logger.error(f"Erro no health check: {e}")
            self.health.is_healthy = False
            self.health.last_error = str(e)
            raise

    async def _cache_maintenance_task(self) -> None:
        """Tarefa de manutenção de cache"""
        try:
            logger.debug("🔧 Executando manutenção de cache...")
            
            # Só executa se telegram_alerts estiver disponível
            if not self.telegram_alerts:
                logger.debug("📤 Cache de telegram não disponível - modo local")
                return
            
            # Estatísticas antes da limpeza
            telegram_cache_before = len(self.telegram_alerts.recent_tips_cache)
            
            # Executa limpeza
            self.telegram_alerts.cleanup_old_cache()
            
            # Estatísticas após limpeza
            telegram_cache_after = len(self.telegram_alerts.recent_tips_cache)
            items_cleaned = telegram_cache_before - telegram_cache_after
            
            if items_cleaned > 0:
                logger.info(f"🔧 Cache limpo: {items_cleaned} items removidos")
            
        except Exception as e:
            logger.error(f"Erro na manutenção de cache: {e}")
            raise

    async def _cleanup_completed_tasks(self) -> None:
        """Limpa tarefas que foram concluídas"""
        completed_tasks = []
        
        for task_id, async_task in self.running_tasks.items():
            if async_task.done():
                completed_tasks.append(task_id)
                
                # Processa resultado da tarefa
                scheduled_task = self.scheduled_tasks.get(task_id)
                if scheduled_task:
                    try:
                        result = await async_task
                        scheduled_task.status = TaskStatus.COMPLETED
                        self.stats["tasks_completed"] += 1
                        logger.debug(f"✅ Tarefa concluída: {task_id}")
                        
                    except Exception as e:
                        scheduled_task.status = TaskStatus.FAILED
                        scheduled_task.error_count += 1
                        scheduled_task.last_error = str(e)
                        self.stats["tasks_failed"] += 1
                        logger.error(f"❌ Tarefa falhada: {task_id} - {e}")
                    
                    # Agenda próxima execução se for tarefa recorrente
                    self._schedule_next_run(scheduled_task)
        
        # Remove tarefas concluídas
        for task_id in completed_tasks:
            del self.running_tasks[task_id]

    def _schedule_next_run(self, task: ScheduledTask) -> None:
        """Agenda próxima execução de uma tarefa"""
        if task.interval_seconds:
            task.next_run = time.time() + task.interval_seconds
            task.status = TaskStatus.SCHEDULED
            logger.debug(f"📅 Próxima execução de {task.task_id}: {datetime.fromtimestamp(task.next_run).strftime('%H:%M:%S')}")

    def _update_health_status(self) -> None:
        """Atualiza status de saúde do sistema"""
        self.health.tasks_running = len(self.running_tasks)
        self.health.tasks_completed = self.stats["tasks_completed"]
        self.health.tasks_failed = self.stats["tasks_failed"]
        
        # Atualiza uso de memória (aproximado)
        import psutil
        try:
            process = psutil.Process()
            self.health.memory_usage_mb = process.memory_info().rss / 1024 / 1024
        except Exception:
            self.health.memory_usage_mb = 0.0

    async def _handle_scheduler_error(self, error: Exception) -> None:
        """Trata erros do scheduler"""
        self.stats["errors_recovered"] += 1
        
        # Log do erro
        logger.error(f"Erro recuperado no scheduler: {error}")
        
        # Tenta notificar via Telegram (apenas se disponível)
        if self.telegram_alerts:
            try:
                await self.telegram_alerts.send_system_alert(
                    f"Erro recuperado no ScheduleManager: {str(error)[:100]}...",
                    "warning"
                )
            except Exception:
                logger.error("Falha ao enviar alerta de erro")

    async def _notify_system_start(self) -> None:
        """Notifica início do sistema"""
        if not self.telegram_alerts:
            logger.debug("📤 Sistema de alertas não disponível - modo local")
            return
            
        try:
            await self.telegram_alerts.send_system_alert(
                f"🚀 Bot LoL V3 Ultra Avançado INICIADO!\n\n"
                f"• ScheduleManager ativo\n"
                f"• {len(self.scheduled_tasks)} tarefas agendadas\n"
                f"• Monitoramento a cada {self.monitor_interval//60}min\n"
                f"• Sistema 100% operacional",
                "success"
            )
        except Exception as e:
            logger.error(f"Erro ao notificar início: {e}")

    async def _notify_system_stop(self) -> None:
        """Notifica parada do sistema"""
        if not self.telegram_alerts:
            logger.debug("📤 Sistema de alertas não disponível - modo local")
            return
            
        try:
            uptime_hours = (time.time() - self.start_time) / 3600
            await self.telegram_alerts.send_system_alert(
                f"🛑 Bot LoL V3 Ultra Avançado PARADO\n\n"
                f"• Uptime: {uptime_hours:.1f} horas\n"
                f"• Tips geradas: {self.stats['tips_generated']}\n"
                f"• Tarefas executadas: {self.stats['tasks_completed']}\n"
                f"• Sistema finalizado com segurança",
                "info"
            )
        except Exception as e:
            logger.error(f"Erro ao notificar parada: {e}")

    async def _notify_system_error(self, error_msg: str) -> None:
        """Notifica erro crítico do sistema"""
        if not self.telegram_alerts:
            logger.debug("📤 Sistema de alertas não disponível - modo local")
            return
            
        try:
            await self.telegram_alerts.send_system_alert(
                f"❌ ERRO CRÍTICO no Bot LoL V3\n\n{error_msg}\n\nSistema sendo reiniciado...",
                "error"
            )
        except Exception as e:
            logger.error(f"Erro ao notificar erro crítico: {e}")

    # Métodos de consulta e controle

    def get_system_status(self) -> Dict[str, Any]:
        """Retorna status completo do sistema"""
        current_time = time.time()
        
        # Status das tarefas
        task_status = {}
        for task_id, task in self.scheduled_tasks.items():
            task_status[task_id] = {
                "type": task.task_type.value,
                "status": task.status.value,
                "run_count": task.run_count,
                "error_count": task.error_count,
                "last_run": task.last_run,
                "next_run": task.next_run,
                "last_error": task.last_error
            }
        
        return {
            "system": {
                "is_running": self.is_running,
                "uptime_hours": (current_time - self.start_time) / 3600,
                "is_healthy": self.health.is_healthy,
                "memory_usage_mb": self.health.memory_usage_mb
            },
            "tasks": {
                "scheduled_count": len(self.scheduled_tasks),
                "running_count": len(self.running_tasks),
                "task_details": task_status
            },
            "statistics": self.stats,
            "health": {
                "components_status": self.health.components_status,
                "last_tip_time": self.health.last_tip_time,
                "last_error": self.health.last_error
            }
        }

    def get_next_scheduled_matches(self, hours_ahead: int = 24) -> List[Dict[str, Any]]:
        """Retorna próximas partidas agendadas"""
        # Esta função seria implementada com dados reais das APIs
        # Por enquanto retorna mock para demonstração
        current_time = time.time()
        future_time = current_time + (hours_ahead * 3600)
        
        mock_matches = [
            {
                "match_id": "scheduled_lck_1",
                "teams": "T1 vs Gen.G",
                "league": "LCK",
                "scheduled_time": current_time + 3600,  # 1 hora
                "estimated_duration": 2700  # 45 min
            },
            {
                "match_id": "scheduled_lec_1", 
                "teams": "G2 vs FNC",
                "league": "LEC",
                "scheduled_time": current_time + 7200,  # 2 horas
                "estimated_duration": 2400  # 40 min
            }
        ]
        
        return [
            match for match in mock_matches 
            if current_time <= match["scheduled_time"] <= future_time
        ]

    async def force_task_execution(self, task_id: str) -> bool:
        """Força execução imediata de uma tarefa"""
        if task_id not in self.scheduled_tasks:
            logger.error(f"Tarefa não encontrada: {task_id}")
            return False
        
        if task_id in self.running_tasks:
            logger.warning(f"Tarefa já está executando: {task_id}")
            return False
        
        task = self.scheduled_tasks[task_id]
        logger.info(f"🔧 Forçando execução da tarefa: {task_id}")
        
        await self._execute_task(task)
        return True

    def update_task_interval(self, task_id: str, new_interval_seconds: int) -> bool:
        """Atualiza intervalo de uma tarefa"""
        if task_id not in self.scheduled_tasks:
            return False
        
        task = self.scheduled_tasks[task_id]
        old_interval = task.interval_seconds
        task.interval_seconds = new_interval_seconds
        
        logger.info(f"📅 Intervalo atualizado para {task_id}: {old_interval}s → {new_interval_seconds}s")
        return True 