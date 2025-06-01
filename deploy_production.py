#!/usr/bin/env python3
"""
Script de Deploy em Produção - Semana 4
Deploy completo do Bot LoL V3 Ultra Avançado

Execução:
    python deploy_production.py

Funcionalidades:
- Deploy automatizado completo
- Integração de todos os componentes
- Sistema de monitoramento em tempo real
- Dashboard web e API REST
- Health checks e auto-recovery
"""

import asyncio
import sys
import os
import signal
from pathlib import Path
from typing import Optional

# Adiciona o diretório raiz ao path
sys.path.append(str(Path(__file__).parent))

from bot.deployment.production_manager import ProductionManager
from bot.deployment.production_api import ProductionAPI
from bot.utils.logger_config import get_logger

logger = get_logger(__name__)


class ProductionDeployment:
    """
    Sistema completo de deploy em produção
    
    Integra todos os componentes:
    - ProductionManager (core system)
    - ProductionAPI (REST API + WebSocket)
    - Dashboard web em tempo real
    - Monitoramento contínuo
    """

    def __init__(self):
        """Inicializa o sistema de deploy"""
        self.production_manager: Optional[ProductionManager] = None
        self.production_api: Optional[ProductionAPI] = None
        self.is_running = False
        
        # Configuração
        self.config = {
            "api_host": "0.0.0.0",
            "api_port": 8080,
            "monitoring_interval": 60,
            "health_check_interval": 30,
            "dashboard_update_interval": 10,
            "auto_recovery": True
        }
        
        logger.info("🚀 Bot LoL V3 Ultra Avançado - Sistema de Deploy em Produção iniciado")

    async def deploy(self) -> bool:
        """
        Executa deploy completo em produção
        
        Returns:
            True se deploy bem-sucedido
        """
        try:
            logger.info("=" * 80)
            logger.info("🎯 INICIANDO DEPLOY EM PRODUÇÃO - SEMANA 4")
            logger.info("🤖 Bot LoL V3 Ultra Avançado")
            logger.info("=" * 80)
            
            # 1. Inicializa Production Manager
            logger.info("🏗️ Fase 1: Inicializando Production Manager...")
            self.production_manager = ProductionManager(config=self.config)
            
            success = await self.production_manager.start_production_system()
            if not success:
                logger.error("❌ Falha ao inicializar Production Manager")
                return False
            
            logger.info("✅ Production Manager iniciado com sucesso")
            
            # 2. Inicializa API REST + WebSocket
            logger.info("🌐 Fase 2: Inicializando API de Produção...")
            self.production_api = ProductionAPI(
                production_manager=self.production_manager,
                host=self.config["api_host"],
                port=self.config["api_port"]
            )
            
            success = await self.production_api.start_api_server()
            if not success:
                logger.error("❌ Falha ao inicializar API de Produção")
                return False
            
            logger.info("✅ API de Produção iniciada com sucesso")
            
            # 3. Exibe informações de acesso
            self._display_deployment_info()
            
            # 4. Sistema pronto
            self.is_running = True
            logger.info("🎉 DEPLOY EM PRODUÇÃO CONCLUÍDO COM SUCESSO!")
            logger.info("🚀 Sistema Bot LoL V3 Ultra Avançado está ONLINE")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro durante o deploy: {e}")
            await self.shutdown()
            return False

    async def run_forever(self):
        """Mantém o sistema rodando indefinidamente"""
        try:
            logger.info("🔄 Sistema rodando... (Ctrl+C para parar)")
            
            # Loop principal - mantém o sistema vivo
            while self.is_running:
                await asyncio.sleep(10)
                
                # Verificação de saúde básica
                if self.production_manager:
                    status = await self.production_manager.get_system_status()
                    if status.get("system_status") == "critical":
                        logger.warning("⚠️ Sistema em estado crítico detectado")
            
        except KeyboardInterrupt:
            logger.info("🛑 Interrupção do usuário detectada (Ctrl+C)")
        except Exception as e:
            logger.error(f"❌ Erro no loop principal: {e}")
        finally:
            await self.shutdown()

    async def shutdown(self):
        """Para o sistema gracefully"""
        try:
            if not self.is_running:
                return
            
            logger.info("🛑 Iniciando shutdown do sistema de produção...")
            self.is_running = False
            
            # Para API
            if self.production_api:
                await self.production_api.stop_api_server()
                logger.info("✅ API de produção parada")
            
            # Para Production Manager
            if self.production_manager:
                await self.production_manager.stop_production_system()
                logger.info("✅ Production Manager parado")
            
            logger.info("🏁 Shutdown completo. Sistema parado com sucesso.")
            
        except Exception as e:
            logger.error(f"❌ Erro durante shutdown: {e}")

    def _display_deployment_info(self):
        """Exibe informações do deploy"""
        api_info = self.production_api.get_api_info()
        
        logger.info("")
        logger.info("🎯 INFORMAÇÕES DO DEPLOY")
        logger.info("=" * 50)
        logger.info(f"🌐 Base URL: {api_info['base_url']}")
        logger.info(f"📊 Dashboard: {api_info['dashboard_url']}")
        logger.info(f"🔌 WebSocket: {api_info['websocket_url']}")
        logger.info("")
        logger.info("📡 ENDPOINTS PRINCIPAIS:")
        for endpoint in api_info['endpoints']:
            logger.info(f"   • {endpoint['method']} {endpoint['path']} - {endpoint['description']}")
        logger.info("")
        logger.info("🛠️ COMANDOS ÚTEIS:")
        logger.info(f"   • Status: curl {api_info['base_url']}/api/status")
        logger.info(f"   • Health: curl {api_info['base_url']}/api/health")
        logger.info(f"   • Relatório 7d: curl {api_info['base_url']}/api/report/7")
        logger.info("")
        logger.info("🔧 COMPONENTES ATIVOS:")
        logger.info("   • Performance Monitor (métricas em tempo real)")
        logger.info("   • Dashboard Generator (visualização web)")
        logger.info("   • Health Checks (monitoramento contínuo)")
        logger.info("   • Auto Recovery (recuperação automática)")
        logger.info("   • Resource Monitor (CPU, RAM, Disk)")
        logger.info("   • WebSocket Streaming (dados ao vivo)")
        logger.info("")
        logger.info("💡 RECURSOS AVANÇADOS:")
        logger.info("   • ROI e Win Rate em tempo real")
        logger.info("   • Alertas automáticos")
        logger.info("   • Relatórios detalhados")
        logger.info("   • Análise de composições")
        logger.info("   • Análise de patch notes")
        logger.info("   • Sistema híbrido ML + Algoritmos")
        logger.info("")

    def setup_signal_handlers(self):
        """Configura handlers para sinais do sistema"""
        def signal_handler(signum, frame):
            logger.info(f"🛑 Sinal {signum} recebido, iniciando shutdown...")
            asyncio.create_task(self.shutdown())
        
        try:
            signal.signal(signal.SIGINT, signal_handler)
            signal.signal(signal.SIGTERM, signal_handler)
        except ValueError:
            # Em alguns ambientes os signals não podem ser configurados
            pass


async def main():
    """Função principal do deploy"""
    try:
        # Banner de início
        print("\n" + "="*80)
        print("🚀 BOT LOL V3 ULTRA AVANÇADO - DEPLOY EM PRODUÇÃO")
        print("📅 SEMANA 4: Sistema de Monitoramento Completo")
        print("="*80)
        
        # Inicializa sistema de deploy
        deployment = ProductionDeployment()
        deployment.setup_signal_handlers()
        
        # Executa deploy
        success = await deployment.deploy()
        
        if success:
            # Mantém sistema rodando
            await deployment.run_forever()
        else:
            logger.error("❌ Deploy falhou")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("🛑 Deploy interrompido pelo usuário")
    except Exception as e:
        logger.error(f"❌ Erro fatal no deploy: {e}")
        sys.exit(1)


if __name__ == "__main__":
    # Verifica versão do Python
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ é necessário")
        sys.exit(1)
    
    # Verifica dependências críticas
    try:
        import aiohttp
        import psutil
    except ImportError as e:
        print(f"❌ Dependência faltando: {e}")
        print("💡 Execute: pip install -r requirements.txt")
        sys.exit(1)
    
    # Cria diretórios necessários
    Path("bot/data/monitoring").mkdir(parents=True, exist_ok=True)
    Path("bot/logs").mkdir(parents=True, exist_ok=True)
    
    # Executa deploy
    asyncio.run(main()) 