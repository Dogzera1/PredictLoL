#!/usr/bin/env python3
"""
Teste básico do ScheduleManager sem componentes complexos
"""
import asyncio
import signal
import sys
import time
from pathlib import Path

# Adiciona o diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent))

from bot.utils.logger_config import get_logger

logger = get_logger(__name__)

class SimpleScheduleTest:
    """Teste simples de agendamento"""
    
    def __init__(self):
        self.is_running = False
        self.task_count = 0
        
    async def simple_task(self):
        """Tarefa simples para teste"""
        self.task_count += 1
        current_time = time.strftime("%H:%M:%S")
        logger.info(f"✅ Tarefa #{self.task_count} executada às {current_time}")
        
        # Simula algum processamento
        await asyncio.sleep(1)
        
        return f"Tarefa {self.task_count} concluída"
    
    async def health_check(self):
        """Health check simples"""
        logger.info("💓 Health check executado")
        return "Sistema saudável"
    
    async def start_scheduled_tasks(self):
        """Inicia tarefas agendadas simples"""
        logger.info("🚀 Iniciando sistema de agendamento simples...")
        
        self.is_running = True
        
        # Cria tarefas em background
        tasks = [
            asyncio.create_task(self._task_scheduler("Monitoramento", 10)),  # A cada 10s
            asyncio.create_task(self._task_scheduler("Health Check", 30)),   # A cada 30s
            asyncio.create_task(self._task_scheduler("Status Report", 60))   # A cada 60s
        ]
        
        logger.info("✅ Tarefas agendadas iniciadas!")
        
        try:
            # Aguarda todas as tarefas
            await asyncio.gather(*tasks)
        except asyncio.CancelledError:
            logger.info("📋 Tarefas canceladas")
        finally:
            self.is_running = False
    
    async def _task_scheduler(self, task_name: str, interval_seconds: int):
        """Agendador simples para uma tarefa"""
        logger.info(f"⏰ Agendador '{task_name}' iniciado (intervalo: {interval_seconds}s)")
        
        while self.is_running:
            try:
                await asyncio.sleep(interval_seconds)
                
                if not self.is_running:
                    break
                
                # Executa a tarefa apropriada
                if "Monitoramento" in task_name:
                    result = await self.simple_task()
                elif "Health" in task_name:
                    result = await self.health_check()
                else:
                    result = await self.status_report()
                
                logger.debug(f"🔄 {task_name}: {result}")
                
            except asyncio.CancelledError:
                logger.info(f"📋 Agendador '{task_name}' cancelado")
                break
            except Exception as e:
                logger.error(f"❌ Erro no agendador '{task_name}': {e}")
                await asyncio.sleep(5)  # Aguarda antes de tentar novamente
    
    async def status_report(self):
        """Relatório de status"""
        uptime = time.time() - self.start_time if hasattr(self, 'start_time') else 0
        
        print("\n" + "=" * 50)
        print("📊 STATUS DO SISTEMA SIMPLES")
        print("=" * 50)
        print(f"🖥️  Status: {'✅ RODANDO' if self.is_running else '❌ PARADO'}")
        print(f"⏰ Uptime: {uptime:.0f} segundos")
        print(f"🔄 Tarefas executadas: {self.task_count}")
        print(f"🕐 Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 50)
        
        return f"Status: {self.task_count} tarefas executadas"
    
    async def stop(self):
        """Para o sistema"""
        logger.info("🛑 Parando sistema...")
        self.is_running = False

async def main():
    """Função principal"""
    print("🧪 TESTE DO SISTEMA DE AGENDAMENTO")
    print("=" * 50)
    print("💡 Testando funcionalidades básicas")
    print("🔧 Sem dependências complexas")
    print("=" * 50)
    
    scheduler = SimpleScheduleTest()
    scheduler.start_time = time.time()
    
    # Configura handlers de shutdown
    def signal_handler(signum, frame):
        print(f"\n📋 Recebido sinal {signum}, parando sistema...")
        asyncio.create_task(scheduler.stop())
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        print("✅ Sistema iniciado!")
        print("💡 Use Ctrl+C para parar")
        print("=" * 50)
        
        # Inicia sistema
        await scheduler.start_scheduled_tasks()
        
    except KeyboardInterrupt:
        print("\n🛑 Sistema parado pelo usuário")
    except Exception as e:
        logger.error(f"❌ Erro fatal: {e}")
        print(f"❌ Erro: {e}")
    finally:
        await scheduler.stop()

if __name__ == "__main__":
    asyncio.run(main()) 