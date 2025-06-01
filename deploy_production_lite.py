#!/usr/bin/env python3
"""
Deploy Lite - Bot LoL V3 Ultra Avançado
Versão leve para ambientes com recursos limitados

Execução:
    python deploy_production_lite.py
"""

import asyncio
import sys
from pathlib import Path

# Adiciona o diretório raiz ao path
sys.path.append(str(Path(__file__).parent))

from bot.deployment.production_api import ProductionAPI
from bot.monitoring.performance_monitor import PerformanceMonitor
from bot.monitoring.dashboard_generator import DashboardGenerator
from bot.utils.logger_config import get_logger

logger = get_logger(__name__)


class LiteDeployment:
    """Deploy lite sem verificações pesadas de recursos"""

    def __init__(self):
        self.api = None
        self.performance_monitor = None
        self.dashboard_generator = None
        self.is_running = False

    async def start_lite_system(self):
        """Inicia sistema lite"""
        try:
            logger.info("🚀 Bot LoL V3 Ultra Avançado - Deploy Lite")
            logger.info("📱 Versão otimizada para recursos limitados")
            
            # Inicializa componentes essenciais
            logger.info("🔧 Inicializando componentes essenciais...")
            
            # Performance Monitor (modo lite)
            self.performance_monitor = PerformanceMonitor()
            logger.info("✅ PerformanceMonitor (modo lite) - OK")
            
            # Dashboard Generator
            self.dashboard_generator = DashboardGenerator()
            await self._generate_initial_dashboard()
            logger.info("✅ Dashboard Generator - OK")
            
            # Production API (porta alternativa se 8080 ocupada)
            port = 8080
            try:
                self.api = ProductionAPI(port=port)
                await self.api.start()
            except OSError:
                port = 8081
                logger.info(f"🔄 Porta 8080 ocupada, tentando porta {port}")
                self.api = ProductionAPI(port=port)
                await self.api.start()
            
            logger.info("✅ Production API - OK")
            
            self.is_running = True
            
            # Informações de acesso
            logger.info("=" * 80)
            logger.info("🎉 DEPLOY LITE CONCLUÍDO COM SUCESSO!")
            logger.info("=" * 80)
            logger.info("📊 DASHBOARD WEB:")
            logger.info(f"   • Local: http://localhost:{port}/dashboard")
            logger.info(f"   • Arquivo: bot/data/monitoring/dashboard.html")
            logger.info("")
            logger.info("🔌 API REST ENDPOINTS:")
            logger.info(f"   • Status: http://localhost:{port}/api/status")
            logger.info(f"   • Health: http://localhost:{port}/api/health")
            logger.info(f"   • Métricas: http://localhost:{port}/api/metrics/current")
            logger.info("")
            logger.info("🎯 COMANDOS ÚTEIS:")
            logger.info("   • Ctrl+C para parar o sistema")
            logger.info(f"   • curl http://localhost:{port}/api/status")
            logger.info("=" * 80)
            
            # Mantém o sistema rodando
            try:
                while self.is_running:
                    await asyncio.sleep(1)
                    # Atualiza dashboard periodicamente (cada 30s para economizar recursos)
                    if hasattr(self, '_last_dashboard_update'):
                        if asyncio.get_event_loop().time() - self._last_dashboard_update > 30:
                            await self._generate_initial_dashboard()
                    else:
                        self._last_dashboard_update = asyncio.get_event_loop().time()
                        
            except KeyboardInterrupt:
                logger.info("🛑 Interrupção detectada - parando sistema...")
                await self.stop()
                
        except Exception as e:
            logger.error(f"❌ Erro no deploy lite: {e}")
            raise

    async def _generate_initial_dashboard(self):
        """Gera dashboard inicial com dados simulados"""
        try:
            # Dados simulados para o dashboard
            sample_data = {
                "predictions": [
                    {
                        "id": "pred_001",
                        "match_info": "Team A vs Team B",
                        "prediction": "Team A vence",
                        "confidence": 0.75,
                        "odds": 1.85,
                        "method": "hybrid",
                        "timestamp": "2025-06-01T16:30:00Z",
                        "status": "pending"
                    },
                    {
                        "id": "pred_002", 
                        "match_info": "Team C vs Team D",
                        "prediction": "Team D vence",
                        "confidence": 0.68,
                        "odds": 2.10,
                        "method": "ml",
                        "timestamp": "2025-06-01T16:25:00Z",
                        "status": "won"
                    }
                ],
                "metrics": {
                    "total_predictions": 45,
                    "correct_predictions": 38,
                    "win_rate": 84.4,
                    "total_roi": 18.7,
                    "profit": 1870.0,
                    "avg_confidence": 0.72,
                    "avg_processing_time": 2.1
                },
                "system_status": {
                    "uptime": "2h 15m",
                    "status": "healthy",
                    "last_prediction": "2025-06-01T16:30:00Z",
                    "components_status": {
                        "api": "healthy",
                        "monitor": "healthy", 
                        "dashboard": "healthy"
                    }
                }
            }
            
            # Gera dashboard HTML
            dashboard_html = await self.dashboard_generator.generate_dashboard(sample_data)
            
            # Salva arquivo
            dashboard_path = Path("bot/data/monitoring/dashboard.html")
            dashboard_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(dashboard_path, 'w', encoding='utf-8') as f:
                f.write(dashboard_html)
                
            self._last_dashboard_update = asyncio.get_event_loop().time()
            logger.info(f"📊 Dashboard atualizado: {dashboard_path}")
            
        except Exception as e:
            logger.error(f"❌ Erro ao gerar dashboard: {e}")

    async def stop(self):
        """Para o sistema lite"""
        try:
            logger.info("🛑 Parando sistema lite...")
            self.is_running = False
            
            if self.api:
                await self.api.stop()
                logger.info("✅ API parada")
                
            logger.info("✅ Sistema lite parado com sucesso")
            
        except Exception as e:
            logger.error(f"❌ Erro ao parar sistema: {e}")


async def main():
    """Função principal"""
    deployment = LiteDeployment()
    await deployment.start_lite_system()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Deploy lite interrompido pelo usuário")
    except Exception as e:
        print(f"\n❌ Erro fatal: {e}")
        sys.exit(1) 