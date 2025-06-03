#!/usr/bin/env python3
"""
Teste forçado do ScheduleManager - Bot LoL V3
Verifica se o sistema de tips automático está funcionando corretamente
"""

import os
import sys
import asyncio
import time
import logging
from datetime import datetime

# Adiciona o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Setup de logging
from bot.utils.logger_config import setup_logging, get_logger
logger = setup_logging(log_level="INFO", log_file="test_schedule_manager.log")

# Configuração de ambiente
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    logger.warning("⚠️ python-dotenv não disponível")

# Força token correto
os.environ["TELEGRAM_BOT_TOKEN"] = "7584060058:AAHiZkgr-TFlbt8Ym1GNFMdvjfVa6oED9l8"
os.environ["TELEGRAM_ADMIN_USER_IDS"] = "8012415611"

async def test_schedule_manager():
    """Testa o ScheduleManager de forma isolada"""
    
    print("\n" + "="*70)
    print("🧪 TESTE FORÇADO DO SCHEDULE MANAGER")
    print("="*70)
    
    try:
        # Imports dos componentes
        logger.info("📦 Importando componentes...")
        
        from bot.systems.schedule_manager import ScheduleManager
        from bot.systems.tips_system import ProfessionalTipsSystem
        from bot.telegram_bot.alerts_system import TelegramAlertsSystem
        from bot.api_clients.pandascore_api_client import PandaScoreAPIClient
        from bot.api_clients.riot_api_client import RiotAPIClient
        from bot.core_logic import DynamicPredictionSystem, LoLGameAnalyzer, ProfessionalUnitsSystem
        
        logger.info("✅ Todos os componentes importados")
        
        # Inicializa componentes
        logger.info("🔧 Inicializando componentes...")
        
        # APIs
        pandascore_client = PandaScoreAPIClient()
        riot_client = RiotAPIClient()
        
        # Sistema de predição
        units_system = ProfessionalUnitsSystem()
        game_analyzer = LoLGameAnalyzer()
        prediction_system = DynamicPredictionSystem(
            game_analyzer=game_analyzer,
            units_system=units_system
        )
        
        # Sistema de tips
        tips_system = ProfessionalTipsSystem(
            pandascore_client=pandascore_client,
            riot_client=riot_client,
            prediction_system=prediction_system
        )
        
        # Sistema de alertas Telegram
        telegram_alerts = TelegramAlertsSystem(
            bot_token=os.getenv("TELEGRAM_BOT_TOKEN")
        )
        
        logger.info("✅ Componentes inicializados")
        
        # Cria ScheduleManager
        logger.info("⚙️ Criando ScheduleManager...")
        
        schedule_manager = ScheduleManager(
            tips_system=tips_system,
            telegram_alerts=telegram_alerts,
            pandascore_client=pandascore_client,
            riot_client=riot_client
        )
        
        logger.info("✅ ScheduleManager criado")
        
        # Testa tarefas individuais primeiro
        logger.info("\n🏃 Testando tarefas individuais...")
        
        await schedule_manager._create_scheduled_tasks()
        logger.info(f"📋 {len(schedule_manager.scheduled_tasks)} tarefas criadas")
        
        # Lista tarefas criadas
        for task_id, task in schedule_manager.scheduled_tasks.items():
            print(f"   • {task_id}: {task.task_type.value} (interval: {task.interval_seconds}s)")
        
        # Testa cada tarefa individualmente
        test_tasks = [
            ("monitor_live_matches", "🔍 Monitoramento de Partidas"),
            ("system_health_check", "💓 Health Check"),
            ("cache_maintenance", "🔧 Manutenção de Cache"),
            ("cleanup_old_data", "🧹 Limpeza de Dados")
        ]
        
        for task_id, task_name in test_tasks:
            if task_id in schedule_manager.scheduled_tasks:
                logger.info(f"\n{task_name}...")
                try:
                    success = await schedule_manager.force_task_execution(task_id)
                    logger.info(f"   Resultado: {'✅ Sucesso' if success else '❌ Falha'}")
                    
                    # Aguarda execução
                    await asyncio.sleep(2)
                    
                    # Verifica resultado
                    if task_id in schedule_manager.running_tasks:
                        task_async = schedule_manager.running_tasks[task_id]
                        if task_async.done():
                            try:
                                result = await task_async
                                logger.info(f"   Status: ✅ Concluída")
                            except Exception as e:
                                logger.error(f"   Status: ❌ Erro - {e}")
                        else:
                            logger.info(f"   Status: 🏃 Ainda executando")
                    
                except Exception as e:
                    logger.error(f"   Erro: {e}")
        
        # Testa ScheduleManager completo por tempo limitado
        logger.info("\n🚀 Testando ScheduleManager completo...")
        
        # Configura intervalos menores para teste
        for task in schedule_manager.scheduled_tasks.values():
            if task.task_type.value == "monitor_matches":
                task.interval_seconds = 60  # 1 minuto
            elif task.task_type.value == "health_check":
                task.interval_seconds = 30  # 30 segundos
            else:
                task.interval_seconds = 120  # 2 minutos
            
            task.next_run = time.time() + 5  # Todas começam em 5 segundos
        
        # Simula execução por 2 minutos
        logger.info("⏱️ Executando por 2 minutos...")
        
        # Inicia ScheduleManager em background
        schedule_task = asyncio.create_task(schedule_manager.start_scheduled_tasks())
        
        # Aguarda 2 minutos
        start_time = time.time()
        duration = 120  # 2 minutos
        
        while time.time() - start_time < duration:
            await asyncio.sleep(10)
            
            # Mostra status a cada 30 segundos
            if int(time.time() - start_time) % 30 == 0:
                status = schedule_manager.get_system_status()
                elapsed = time.time() - start_time
                
                print(f"\n📊 Status ({elapsed:.0f}s):")
                print(f"   • Tarefas executando: {status['tasks']['running_count']}")
                print(f"   • Tarefas concluídas: {status['statistics']['tasks_completed']}")
                print(f"   • Tips geradas: {status['statistics']['tips_generated']}")
                print(f"   • Sistema saudável: {'✅' if status['system']['is_healthy'] else '❌'}")
        
        # Para ScheduleManager
        logger.info("🛑 Parando ScheduleManager...")
        await schedule_manager.stop_scheduled_tasks()
        
        # Cancela task se ainda estiver rodando
        if not schedule_task.done():
            schedule_task.cancel()
            try:
                await schedule_task
            except asyncio.CancelledError:
                pass
        
        # Relatório final
        logger.info("\n📈 RELATÓRIO FINAL:")
        final_status = schedule_manager.get_system_status()
        
        print("\n" + "="*70)
        print("📈 RELATÓRIO FINAL DO TESTE")
        print("="*70)
        print(f"⏱️ Duração do teste: {duration}s")
        print(f"🔧 Tarefas criadas: {len(schedule_manager.scheduled_tasks)}")
        print(f"✅ Tarefas concluídas: {final_status['statistics']['tasks_completed']}")
        print(f"❌ Tarefas falhadas: {final_status['statistics']['tasks_failed']}")
        print(f"🎯 Tips geradas: {final_status['statistics']['tips_generated']}")
        print(f"💓 Sistema saudável: {'✅' if final_status['system']['is_healthy'] else '❌'}")
        print(f"📊 Memória usada: {final_status['system']['memory_usage_mb']:.1f}MB")
        
        print("\n📋 Detalhes das tarefas:")
        for task_id, task_details in final_status['tasks']['task_details'].items():
            print(f"   • {task_id}:")
            print(f"     - Execuções: {task_details['run_count']}")
            print(f"     - Erros: {task_details['error_count']}")
            print(f"     - Status: {task_details['status']}")
            
            if task_details['last_error']:
                print(f"     - Último erro: {task_details['last_error']}")
        
        if final_status['statistics']['tips_generated'] > 0:
            print("\n🎉 SUCESSO: Sistema gerou tips durante o teste!")
        else:
            print("\n⚠️ ATENÇÃO: Nenhuma tip foi gerada (pode ser normal se não há partidas adequadas)")
        
        print("="*70)
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Erro crítico no teste: {e}")
        import traceback
        logger.error(f"Stack trace: {traceback.format_exc()}")
        return False

async def main():
    """Função principal"""
    try:
        print("🧪 Iniciando teste isolado do ScheduleManager...")
        
        success = await test_schedule_manager()
        
        if success:
            print("\n✅ TESTE CONCLUÍDO COM SUCESSO!")
            print("💡 Se o teste passou, o problema pode estar na inicialização no Railway")
        else:
            print("\n❌ TESTE FALHOU!")
            print("💡 Há um problema na implementação do ScheduleManager")
            
    except Exception as e:
        print(f"\n❌ Erro fatal: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main()) 