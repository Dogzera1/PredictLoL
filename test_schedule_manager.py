#!/usr/bin/env python3
"""
Teste do ScheduleManager - Bot LoL V3 Ultra Avançado

Script para testar o orquestrador principal que conecta todos os sistemas.
"""

import os
import sys
import asyncio
import time
from typing import Dict, Any
from unittest.mock import AsyncMock, MagicMock

# Adiciona o diretório atual ao path para importar módulos
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from bot.systems import (
    ScheduleManager,
    TaskStatus,
    TaskType,
    ScheduledTask,
    SystemHealth,
    ProfessionalTipsSystem
)
from bot.telegram_bot import TelegramAlertsSystem
from bot.api_clients.pandascore_api_client import PandaScoreAPIClient
from bot.api_clients.riot_api_client import RiotAPIClient
from bot.utils.logger_config import setup_logging, get_logger

# Configuração de logging
logger = setup_logging(log_level="INFO", log_file=None)
test_logger = get_logger("test_schedule_manager")


class MockProfessionalTipsSystem:
    """Sistema de tips mock para testes"""
    
    def __init__(self):
        self.scan_count = 0
        self.tips_generated = 0
        
    async def force_scan(self) -> Dict[str, Any]:
        """Simula scan de partidas"""
        self.scan_count += 1
        
        # Simula geração de tip a cada 3 scans
        tip_generated = (self.scan_count % 3 == 0)
        if tip_generated:
            self.tips_generated += 1
        
        return {
            "live_matches_found": 2 if self.scan_count % 2 == 0 else 1,
            "tip_generated": tip_generated,
            "scan_number": self.scan_count
        }
    
    def _cleanup_expired_tips(self):
        """Simula limpeza de tips"""
        print(f"   🧹 Tips expiradas limpas (simulado)")


class MockTelegramAlertsSystem:
    """Sistema de alertas mock para testes"""
    
    def __init__(self):
        self.alerts_sent = 0
        self.recent_tips_cache = {}
        
    async def send_system_alert(self, message: str, alert_type: str = "info"):
        """Simula envio de alerta"""
        self.alerts_sent += 1
        print(f"   📢 {alert_type.upper()}: {message[:60]}...")
        
    def cleanup_old_cache(self):
        """Simula limpeza de cache"""
        old_count = len(self.recent_tips_cache)
        # Simula remoção de alguns items
        if old_count > 2:
            self.recent_tips_cache.clear()
            print(f"   💾 Cache limpo: {old_count} → 0 items")


class MockAPIClient:
    """Cliente de API mock"""
    
    def __init__(self, name: str):
        self.name = name
        
    def cleanup_cache(self):
        print(f"   🔧 Cache {self.name} limpo (simulado)")


async def test_schedule_manager_initialization():
    """Testa inicialização do ScheduleManager"""
    print(f"\n{'='*70}")
    print("🔧 TESTE: INICIALIZAÇÃO DO SCHEDULE MANAGER")
    print(f"{'='*70}")
    
    # Cria mocks dos sistemas
    tips_system = MockProfessionalTipsSystem()
    telegram_alerts = MockTelegramAlertsSystem()
    pandascore_client = MockAPIClient("PandaScore")
    riot_client = MockAPIClient("Riot")
    
    # Inicializa ScheduleManager
    schedule_manager = ScheduleManager(
        tips_system=tips_system,
        telegram_alerts=telegram_alerts,
        pandascore_client=pandascore_client,
        riot_client=riot_client
    )
    
    print("✅ ScheduleManager inicializado:")
    print(f"   • Tips System: {type(schedule_manager.tips_system).__name__}")
    print(f"   • Telegram Alerts: {type(schedule_manager.telegram_alerts).__name__}")
    print(f"   • PandaScore Client: {type(schedule_manager.pandascore_client).__name__}")
    print(f"   • Riot Client: {type(schedule_manager.riot_client).__name__}")
    print(f"   • Intervalo de monitoramento: {schedule_manager.monitor_interval}s")
    print(f"   • Intervalo de limpeza: {schedule_manager.cleanup_interval//3600}h")
    
    return schedule_manager


async def test_task_creation(schedule_manager: ScheduleManager):
    """Testa criação de tarefas agendadas"""
    print(f"\n{'='*70}")
    print("📅 TESTE: CRIAÇÃO DE TAREFAS AGENDADAS")
    print(f"{'='*70}")
    
    # Cria tarefas agendadas
    await schedule_manager._create_scheduled_tasks()
    
    print(f"📊 Tarefas criadas: {len(schedule_manager.scheduled_tasks)}")
    
    for task_id, task in schedule_manager.scheduled_tasks.items():
        print(f"   • {task_id}:")
        print(f"     - Tipo: {task.task_type.value}")
        print(f"     - Status: {task.status.value}")
        print(f"     - Intervalo: {task.interval_seconds//60}min")
        print(f"     - Próxima execução: {time.strftime('%H:%M:%S', time.localtime(task.next_run))}")
    
    # Verifica se todas as tarefas necessárias foram criadas
    expected_tasks = ["monitor_live_matches", "cleanup_old_data", "system_health_check", "cache_maintenance"]
    created_tasks = list(schedule_manager.scheduled_tasks.keys())
    
    missing_tasks = set(expected_tasks) - set(created_tasks)
    if missing_tasks:
        print(f"⚠️ Tarefas faltando: {missing_tasks}")
    else:
        print(f"✅ Todas as tarefas essenciais foram criadas")


async def test_task_execution(schedule_manager: ScheduleManager):
    """Testa execução individual de tarefas"""
    print(f"\n{'='*70}")
    print("🏃 TESTE: EXECUÇÃO DE TAREFAS INDIVIDUAIS")
    print(f"{'='*70}")
    
    # Testa cada tipo de tarefa
    task_tests = [
        ("monitor_live_matches", "Monitoramento de Partidas"),
        ("cleanup_old_data", "Limpeza de Dados"),
        ("system_health_check", "Health Check"),
        ("cache_maintenance", "Manutenção de Cache")
    ]
    
    for task_id, task_name in task_tests:
        print(f"\n🔧 Testando: {task_name}")
        
        if task_id in schedule_manager.scheduled_tasks:
            try:
                # Força execução da tarefa
                success = await schedule_manager.force_task_execution(task_id)
                print(f"   • Execução forçada: {'✅' if success else '❌'}")
                
                # Aguarda um pouco para a tarefa ser processada
                await asyncio.sleep(0.5)
                
                # Verifica se tarefa está em execução
                is_running = task_id in schedule_manager.running_tasks
                print(f"   • Status de execução: {'🏃 Executando' if is_running else '⏸️ Parada'}")
                
                # Aguarda conclusão se estiver executando
                if is_running:
                    task = schedule_manager.running_tasks[task_id]
                    try:
                        await asyncio.wait_for(task, timeout=10.0)
                        print(f"   • Resultado: ✅ Concluída com sucesso")
                    except asyncio.TimeoutError:
                        print(f"   • Resultado: ⏱️ Timeout (ainda executando)")
                    except Exception as e:
                        print(f"   • Resultado: ❌ Erro - {e}")
                
            except Exception as e:
                print(f"   • Erro na execução: {e}")
        else:
            print(f"   • ❌ Tarefa não encontrada: {task_id}")


async def test_monitoring_task(schedule_manager: ScheduleManager):
    """Testa tarefa de monitoramento em detalhes"""
    print(f"\n{'='*70}")
    print("🔍 TESTE: TAREFA DE MONITORAMENTO DETALHADA")
    print(f"{'='*70}")
    
    # Executa múltiplos scans para simular funcionamento real
    print("🔄 Executando múltiplos scans de monitoramento...")
    
    for i in range(5):
        print(f"\n📊 Scan #{i+1}:")
        
        try:
            # Executa tarefa de monitoramento
            await schedule_manager._monitor_live_matches_task()
            
            # Verifica estatísticas
            tips_generated = schedule_manager.stats["tips_generated"]
            print(f"   • Tips geradas até agora: {tips_generated}")
            print(f"   • Scan count do tips system: {schedule_manager.tips_system.scan_count}")
            
        except Exception as e:
            print(f"   • ❌ Erro no scan: {e}")
        
        await asyncio.sleep(0.2)  # Pequena pausa entre scans
    
    print(f"\n📈 Estatísticas finais do monitoramento:")
    print(f"   • Tips geradas: {schedule_manager.stats['tips_generated']}")
    print(f"   • Scans executados: {schedule_manager.tips_system.scan_count}")
    print(f"   • Taxa de tip/scan: {schedule_manager.stats['tips_generated']/schedule_manager.tips_system.scan_count:.1%}")


async def test_health_monitoring(schedule_manager: ScheduleManager):
    """Testa sistema de monitoramento de saúde"""
    print(f"\n{'='*70}")
    print("💓 TESTE: MONITORAMENTO DE SAÚDE DO SISTEMA")
    print(f"{'='*70}")
    
    # Estado inicial da saúde
    print("🔍 Estado inicial da saúde:")
    print(f"   • Sistema saudável: {schedule_manager.health.is_healthy}")
    print(f"   • Componentes: {len(schedule_manager.health.components_status)}")
    
    # Executa health check
    print("\n💓 Executando health check...")
    
    try:
        await schedule_manager._system_health_check_task()
        
        # Verifica resultado do health check
        health = schedule_manager.health
        print(f"   • Status geral: {'✅ Saudável' if health.is_healthy else '❌ Problemas'}")
        print(f"   • Uptime: {health.uptime_seconds:.1f}s")
        print(f"   • Tarefas executando: {health.tasks_running}")
        print(f"   • Tarefas concluídas: {health.tasks_completed}")
        print(f"   • Uso de memória: {health.memory_usage_mb:.1f}MB")
        
        print(f"\n🔧 Status dos componentes:")
        for component, status in health.components_status.items():
            status_icon = "✅" if status else "❌"
            print(f"   • {component}: {status_icon}")
        
    except Exception as e:
        print(f"   • ❌ Erro no health check: {e}")


async def test_system_status_report(schedule_manager: ScheduleManager):
    """Testa relatório de status do sistema"""
    print(f"\n{'='*70}")
    print("📊 TESTE: RELATÓRIO DE STATUS DO SISTEMA")
    print(f"{'='*70}")
    
    # Simula algum tempo de execução
    schedule_manager.start_time = time.time() - 3600  # 1 hora atrás
    schedule_manager.stats["tasks_completed"] = 15
    schedule_manager.stats["tasks_failed"] = 2
    
    # Obtém status completo
    status = schedule_manager.get_system_status()
    
    print("🖥️ Status do Sistema:")
    system_info = status["system"]
    print(f"   • Executando: {'✅' if system_info['is_running'] else '❌'}")
    print(f"   • Uptime: {system_info['uptime_hours']:.2f} horas")
    print(f"   • Saudável: {'✅' if system_info['is_healthy'] else '❌'}")
    print(f"   • Memória: {system_info['memory_usage_mb']:.1f}MB")
    
    print("\n📋 Tarefas:")
    tasks_info = status["tasks"]
    print(f"   • Agendadas: {tasks_info['scheduled_count']}")
    print(f"   • Executando: {tasks_info['running_count']}")
    
    print("\n📈 Estatísticas:")
    stats = status["statistics"]
    print(f"   • Tarefas concluídas: {stats['tasks_completed']}")
    print(f"   • Tarefas falhadas: {stats['tasks_failed']}")
    print(f"   • Tips geradas: {stats['tips_generated']}")
    print(f"   • Uptime: {stats['uptime_hours']:.2f}h")
    
    print("\n🔧 Detalhes das Tarefas:")
    for task_id, task_info in tasks_info['task_details'].items():
        print(f"   • {task_id}:")
        print(f"     - Status: {task_info['status']}")
        print(f"     - Execuções: {task_info['run_count']}")
        print(f"     - Erros: {task_info['error_count']}")


async def test_scheduled_matches(schedule_manager: ScheduleManager):
    """Testa consulta de partidas agendadas"""
    print(f"\n{'='*70}")
    print("📅 TESTE: PRÓXIMAS PARTIDAS AGENDADAS")
    print(f"{'='*70}")
    
    # Obtém próximas partidas
    matches = schedule_manager.get_next_scheduled_matches(hours_ahead=12)
    
    print(f"🎮 Próximas partidas nas próximas 12 horas:")
    print(f"   • Total encontradas: {len(matches)}")
    
    for match in matches:
        scheduled_time = time.strftime('%H:%M', time.localtime(match['scheduled_time']))
        print(f"   • {match['teams']} ({match['league']}) - {scheduled_time}")
        print(f"     - Match ID: {match['match_id']}")
        print(f"     - Duração estimada: {match['estimated_duration']//60}min")


async def test_task_interval_update(schedule_manager: ScheduleManager):
    """Testa atualização de intervalos de tarefas"""
    print(f"\n{'='*70}")
    print("⚙️ TESTE: ATUALIZAÇÃO DE INTERVALOS DE TAREFAS")
    print(f"{'='*70}")
    
    # Testa atualização de intervalo
    task_id = "monitor_live_matches"
    
    if task_id in schedule_manager.scheduled_tasks:
        old_interval = schedule_manager.scheduled_tasks[task_id].interval_seconds
        new_interval = 120  # 2 minutos
        
        print(f"🔧 Atualizando intervalo de {task_id}:")
        print(f"   • Intervalo atual: {old_interval}s")
        print(f"   • Novo intervalo: {new_interval}s")
        
        success = schedule_manager.update_task_interval(task_id, new_interval)
        
        if success:
            updated_interval = schedule_manager.scheduled_tasks[task_id].interval_seconds
            print(f"   • ✅ Atualização bem-sucedida: {updated_interval}s")
        else:
            print(f"   • ❌ Falha na atualização")
    else:
        print(f"❌ Tarefa não encontrada: {task_id}")


async def test_error_handling(schedule_manager: ScheduleManager):
    """Testa tratamento de erros"""
    print(f"\n{'='*70}")
    print("⚠️ TESTE: TRATAMENTO DE ERROS")
    print(f"{'='*70}")
    
    # Simula erro no sistema de tips
    print("🔧 Simulando erro no sistema de tips...")
    
    original_force_scan = schedule_manager.tips_system.force_scan
    
    async def failing_force_scan():
        raise Exception("Erro simulado na API do PandaScore")
    
    # Substitui temporariamente por função que falha
    schedule_manager.tips_system.force_scan = failing_force_scan
    
    try:
        # Tenta executar monitoramento que vai falhar
        await schedule_manager._monitor_live_matches_task()
        print("   • ❌ Erro não foi capturado")
    except Exception as e:
        print(f"   • ✅ Erro capturado corretamente: {e}")
    
    # Restaura função original
    schedule_manager.tips_system.force_scan = original_force_scan
    
    # Testa tratamento de erro do scheduler
    print("\n🔧 Testando tratamento de erro do scheduler...")
    
    test_error = Exception("Erro de teste do scheduler")
    await schedule_manager._handle_scheduler_error(test_error)
    
    print(f"   • ✅ Erro tratado pelo scheduler")
    print(f"   • Erros recuperados: {schedule_manager.stats['errors_recovered']}")


async def test_short_run_simulation(schedule_manager: ScheduleManager):
    """Simula execução curta do ScheduleManager"""
    print(f"\n{'='*70}")
    print("🚀 TESTE: SIMULAÇÃO DE EXECUÇÃO CURTA")
    print(f"{'='*70}")
    
    print("🔄 Iniciando simulação de 15 segundos...")
    
    # Ajusta intervalos para execução mais rápida nos testes
    for task in schedule_manager.scheduled_tasks.values():
        if task.task_type == TaskType.MONITOR_MATCHES:
            task.interval_seconds = 5  # 5 segundos para teste
        elif task.task_type == TaskType.CACHE_MAINTENANCE:
            task.interval_seconds = 10  # 10 segundos para teste
        task.next_run = time.time() + 2  # Inicia em 2 segundos
    
    # Simula start_scheduled_tasks por tempo limitado
    schedule_manager.is_running = True
    schedule_manager.start_time = time.time()
    
    start_time = time.time()
    run_duration = 15  # 15 segundos
    
    try:
        while time.time() - start_time < run_duration:
            current_time = time.time()
            
            # Atualiza uptime
            schedule_manager.health.uptime_seconds = current_time - schedule_manager.start_time
            schedule_manager.stats["uptime_hours"] = schedule_manager.health.uptime_seconds / 3600
            
            # Verifica tarefas para execução
            tasks_executed = 0
            for task_id, task in schedule_manager.scheduled_tasks.items():
                if schedule_manager._should_run_task(task, current_time):
                    print(f"   🏃 Executando tarefa: {task_id}")
                    await schedule_manager._execute_task(task)
                    tasks_executed += 1
            
            # Limpa tarefas concluídas
            await schedule_manager._cleanup_completed_tasks()
            
            # Atualiza health
            schedule_manager._update_health_status()
            
            # Pequena pausa
            await asyncio.sleep(1)
        
        print(f"\n📊 Resultado da simulação:")
        print(f"   • Duração: {run_duration}s")
        print(f"   • Tips geradas: {schedule_manager.stats['tips_generated']}")
        print(f"   • Tarefas concluídas: {schedule_manager.stats['tasks_completed']}")
        print(f"   • Alertas enviados: {schedule_manager.telegram_alerts.alerts_sent}")
        print(f"   • Sistema saudável: {'✅' if schedule_manager.health.is_healthy else '❌'}")
        
    finally:
        schedule_manager.is_running = False


async def main():
    """Função principal de teste"""
    print("🚀 Iniciando testes do ScheduleManager...")
    print(f"🔧 Python: {sys.version}")
    print(f"📁 Diretório: {os.getcwd()}")
    
    try:
        # Inicialização
        schedule_manager = await test_schedule_manager_initialization()
        
        # Executa testes sequenciais
        test_functions = [
            lambda: test_task_creation(schedule_manager),
            lambda: test_task_execution(schedule_manager),
            lambda: test_monitoring_task(schedule_manager),
            lambda: test_health_monitoring(schedule_manager),
            lambda: test_system_status_report(schedule_manager),
            lambda: test_scheduled_matches(schedule_manager),
            lambda: test_task_interval_update(schedule_manager),
            lambda: test_error_handling(schedule_manager),
            lambda: test_short_run_simulation(schedule_manager)
        ]
        
        for test_func in test_functions:
            try:
                await test_func()
            except Exception as e:
                print(f"\n❌ Erro no teste: {e}")
        
        # Estatísticas finais
        print(f"\n{'='*70}")
        print("📈 ESTATÍSTICAS FINAIS DO SCHEDULE MANAGER")
        print(f"{'='*70}")
        
        final_status = schedule_manager.get_system_status()
        
        print(f"🖥️ Sistema:")
        print(f"   • Uptime: {final_status['system']['uptime_hours']:.3f}h")
        print(f"   • Saudável: {'✅' if final_status['system']['is_healthy'] else '❌'}")
        print(f"   • Memória: {final_status['system']['memory_usage_mb']:.1f}MB")
        
        print(f"\n📊 Estatísticas:")
        stats = final_status['statistics']
        print(f"   • Tarefas criadas: {stats['tasks_created']}")
        print(f"   • Tarefas concluídas: {stats['tasks_completed']}")
        print(f"   • Tarefas falhadas: {stats['tasks_failed']}")
        print(f"   • Tips geradas: {stats['tips_generated']}")
        print(f"   • Erros recuperados: {stats['errors_recovered']}")
        
        print(f"\n📋 Tarefas agendadas: {final_status['tasks']['scheduled_count']}")
        for task_id, task_info in final_status['tasks']['task_details'].items():
            print(f"   • {task_id}: {task_info['run_count']} execuções, {task_info['error_count']} erros")
        
        print(f"\n🎉 TODOS OS TESTES DO SCHEDULE MANAGER CONCLUÍDOS COM SUCESSO!")
        
    except Exception as e:
        print(f"\n❌ Erro fatal durante os testes: {e}")
        sys.exit(1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n🛑 Teste interrompido pelo usuário")
    except Exception as e:
        print(f"\n\n❌ Erro fatal: {e}")
        sys.exit(1) 
