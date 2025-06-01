#!/usr/bin/env python3
"""
Testes de Integração do Sistema de Produção - Semana 4
Testa todos os componentes integrados do Bot LoL V3 Ultra Avançado

Execução:
    python test_production_integration.py

Funcionalidades:
- Teste de integração completa
- Validação de todos os componentes
- Teste de API e WebSocket
- Simulação de cenários reais
- Verificação de performance
"""

import asyncio
import aiohttp
import json
import time
import pytest
from pathlib import Path
from typing import Dict, Any, List

from bot.deployment.production_manager import ProductionManager
from bot.deployment.production_api import ProductionAPI
from bot.monitoring.performance_monitor import PerformanceMonitor, PredictionMetrics
from bot.monitoring.dashboard_generator import DashboardGenerator
from bot.utils.logger_config import get_logger

logger = get_logger(__name__)


class ProductionIntegrationTests:
    """
    Suite completa de testes de integração
    
    Testa:
    - ProductionManager
    - ProductionAPI
    - PerformanceMonitor
    - DashboardGenerator
    - Integração completa
    """

    def __init__(self):
        """Inicializa os testes"""
        self.production_manager = None
        self.production_api = None
        self.test_results = []
        
        # Configuração de teste
        self.config = {
            "api_host": "localhost",
            "api_port": 8081,  # Porta diferente para testes
            "monitoring_interval": 5,
            "health_check_interval": 10,
            "dashboard_update_interval": 5,
            "auto_recovery": True
        }
        
        logger.info("🧪 Sistema de Testes de Integração - Semana 4 iniciado")

    async def run_all_tests(self) -> bool:
        """
        Executa todos os testes de integração
        
        Returns:
            True se todos os testes passaram
        """
        try:
            logger.info("=" * 80)
            logger.info("🧪 INICIANDO TESTES DE INTEGRAÇÃO - SEMANA 4")
            logger.info("🤖 Bot LoL V3 Ultra Avançado - Sistema Completo")
            logger.info("=" * 80)
            
            tests = [
                ("Setup do Sistema", self._test_system_setup),
                ("Production Manager", self._test_production_manager),
                ("Performance Monitor", self._test_performance_monitor),
                ("Dashboard Generator", self._test_dashboard_generator),
                ("Production API", self._test_production_api),
                ("Health Checks", self._test_health_checks),
                ("Resource Monitoring", self._test_resource_monitoring),
                ("WebSocket Streaming", self._test_websocket_streaming),
                ("Emergency Recovery", self._test_emergency_recovery),
                ("Integração Completa", self._test_full_integration),
                ("Cleanup", self._test_cleanup)
            ]
            
            all_passed = True
            
            for test_name, test_func in tests:
                logger.info(f"\n🔍 Executando teste: {test_name}")
                
                try:
                    start_time = time.time()
                    result = await test_func()
                    duration = time.time() - start_time
                    
                    if result:
                        logger.info(f"✅ {test_name} PASSOU ({duration:.2f}s)")
                        self.test_results.append({
                            "test": test_name,
                            "status": "PASS",
                            "duration": duration
                        })
                    else:
                        logger.error(f"❌ {test_name} FALHOU ({duration:.2f}s)")
                        self.test_results.append({
                            "test": test_name,
                            "status": "FAIL",
                            "duration": duration
                        })
                        all_passed = False
                        
                except Exception as e:
                    logger.error(f"❌ {test_name} ERRO: {e}")
                    self.test_results.append({
                        "test": test_name,
                        "status": "ERROR",
                        "error": str(e),
                        "duration": 0
                    })
                    all_passed = False
            
            # Relatório final
            self._generate_test_report()
            
            return all_passed
            
        except Exception as e:
            logger.error(f"❌ Erro fatal nos testes: {e}")
            return False

    async def _test_system_setup(self) -> bool:
        """Teste: Setup inicial do sistema"""
        try:
            # Verifica diretórios
            required_dirs = [
                "bot/data",
                "bot/data/monitoring",
                "bot/logs"
            ]
            
            for dir_path in required_dirs:
                Path(dir_path).mkdir(parents=True, exist_ok=True)
                if not Path(dir_path).exists():
                    logger.error(f"Falha ao criar diretório: {dir_path}")
                    return False
            
            # Verifica dependências
            try:
                import aiohttp
                import psutil
            except ImportError as e:
                logger.error(f"Dependência faltando: {e}")
                return False
            
            logger.info("✅ Setup do sistema validado")
            return True
            
        except Exception as e:
            logger.error(f"Erro no setup: {e}")
            return False

    async def _test_production_manager(self) -> bool:
        """Teste: ProductionManager"""
        try:
            # Inicializa ProductionManager
            self.production_manager = ProductionManager(config=self.config)
            
            # Testa inicialização
            success = await self.production_manager.start_production_system()
            if not success:
                logger.error("Falha ao inicializar ProductionManager")
                return False
            
            # Testa status
            status = await self.production_manager.get_system_status()
            if not status or status.get("system_status") != "healthy":
                logger.error(f"Status inválido: {status}")
                return False
            
            # Testa componentes
            expected_components = [
                "system_resources",
                "performance_monitor",
                "file_system"
            ]
            
            component_health = status.get("component_health", {})
            for component in expected_components:
                if not component_health.get(component, False):
                    logger.error(f"Componente {component} não saudável")
                    return False
            
            logger.info("✅ ProductionManager funcionando corretamente")
            return True
            
        except Exception as e:
            logger.error(f"Erro no ProductionManager: {e}")
            return False

    async def _test_performance_monitor(self) -> bool:
        """Teste: PerformanceMonitor"""
        try:
            monitor = self.production_manager.performance_monitor
            
            # Testa tracking de predição simulada
            fake_prediction = type('obj', (object,), {
                'match_id': 'test_match_123',
                'predicted_winner': 'Team A',
                'win_probability': 0.65,
                'confidence_level': type('enum', (object,), {'value': 'high'})(),
                'method_used': type('enum', (object,), {'value': 'hybrid'})(),
                'processing_time_ms': 1250.5,
                'ml_prediction': {
                    'features': {
                        'composition_analysis': 0.3,
                        'patch_meta_analysis': 0.2,
                        'overall_advantage': 0.4
                    }
                }
            })()
            
            fake_odds = {
                "outcomes": [
                    {"name": "Team A", "odd": 1.85},
                    {"name": "Team B", "odd": 2.10}
                ]
            }
            
            # Track predição
            prediction_id = await monitor.track_prediction(fake_prediction, fake_odds, 10.0)
            if not prediction_id:
                logger.error("Falha ao trackear predição")
                return False
            
            # Resolve predição
            success = await monitor.resolve_prediction(prediction_id, "Team A")
            if not success:
                logger.error("Falha ao resolver predição")
                return False
            
            # Verifica métricas
            metrics = await monitor.get_current_metrics()
            if metrics.total_predictions < 1:
                logger.error("Métricas não atualizadas")
                return False
            
            # Testa relatório
            report = await monitor.get_performance_report(1)
            if not report or report.get("overall", {}).get("total_predictions", 0) < 1:
                logger.error("Relatório inválido")
                return False
            
            logger.info("✅ PerformanceMonitor funcionando corretamente")
            return True
            
        except Exception as e:
            logger.error(f"Erro no PerformanceMonitor: {e}")
            return False

    async def _test_dashboard_generator(self) -> bool:
        """Teste: DashboardGenerator"""
        try:
            dashboard_gen = self.production_manager.dashboard_generator
            
            # Gera dados de teste
            test_data = {
                "timestamp": "2024-01-01T12:00:00",
                "system_status": "online",
                "uptime_hours": 24.5,
                "current_metrics": {
                    "total_predictions": 100,
                    "win_rate": 85.5,
                    "roi": 22.3,
                    "net_profit": 156.78
                },
                "last_24h": {
                    "predictions": 15,
                    "resolved": 12,
                    "pending": 3,
                    "profit": 45.67
                },
                "method_performance": {
                    "ml": {"predictions": 40, "win_rate": 87.5},
                    "algorithm": {"predictions": 35, "win_rate": 82.9},
                    "hybrid": {"predictions": 25, "win_rate": 88.0}
                },
                "active_alerts": [],
                "analysis_usage": {
                    "composition_analyses": 85,
                    "patch_analyses": 95,
                    "avg_processing_time": 1250
                },
                "trend": {
                    "win_rate_trend": [82.1, 83.5, 84.2, 85.5],
                    "roi_trend": [18.5, 19.8, 21.2, 22.3]
                }
            }
            
            # Gera dashboard HTML
            html = dashboard_gen.generate_html_dashboard(test_data)
            if not html or len(html) < 5000:
                logger.error("HTML do dashboard muito pequeno ou inválido")
                return False
            
            # Verifica elementos essenciais no HTML
            required_elements = [
                "Bot LoL V3 Ultra Avançado",
                "85.5%",  # Win rate
                "22.3%",  # ROI
                "156.78", # Net profit
                "Chart.js",
                "bootstrap"
            ]
            
            for element in required_elements:
                if element not in html:
                    logger.error(f"Elemento ausente no HTML: {element}")
                    return False
            
            # Exporta para arquivo
            success = dashboard_gen.export_dashboard_to_file(
                test_data, 
                "bot/data/monitoring/test_dashboard.html"
            )
            if not success:
                logger.error("Falha ao exportar dashboard")
                return False
            
            # Verifica arquivo criado
            if not Path("bot/data/monitoring/test_dashboard.html").exists():
                logger.error("Arquivo de dashboard não foi criado")
                return False
            
            logger.info("✅ DashboardGenerator funcionando corretamente")
            return True
            
        except Exception as e:
            logger.error(f"Erro no DashboardGenerator: {e}")
            return False

    async def _test_production_api(self) -> bool:
        """Teste: ProductionAPI"""
        try:
            # Inicializa API
            self.production_api = ProductionAPI(
                production_manager=self.production_manager,
                host=self.config["api_host"],
                port=self.config["api_port"]
            )
            
            success = await self.production_api.start_api_server()
            if not success:
                logger.error("Falha ao inicializar ProductionAPI")
                return False
            
            # Aguarda API estar pronta
            await asyncio.sleep(2)
            
            base_url = f"http://{self.config['api_host']}:{self.config['api_port']}"
            
            # Testa endpoints
            async with aiohttp.ClientSession() as session:
                # Test GET /api/health
                async with session.get(f"{base_url}/api/health") as resp:
                    if resp.status != 200:
                        logger.error(f"Health endpoint falhou: {resp.status}")
                        return False
                    
                    data = await resp.json()
                    if not data.get("success"):
                        logger.error("Health endpoint retornou success=false")
                        return False
                
                # Test GET /api/status
                async with session.get(f"{base_url}/api/status") as resp:
                    if resp.status != 200:
                        logger.error(f"Status endpoint falhou: {resp.status}")
                        return False
                    
                    data = await resp.json()
                    if not data.get("success") or not data.get("data"):
                        logger.error("Status endpoint retornou dados inválidos")
                        return False
                
                # Test GET /api/metrics/current
                async with session.get(f"{base_url}/api/metrics/current") as resp:
                    if resp.status != 200:
                        logger.error(f"Metrics endpoint falhou: {resp.status}")
                        return False
                
                # Test GET /dashboard
                async with session.get(f"{base_url}/dashboard") as resp:
                    if resp.status != 200:
                        logger.error(f"Dashboard endpoint falhou: {resp.status}")
                        return False
                    
                    html = await resp.text()
                    if len(html) < 1000:
                        logger.error("Dashboard HTML muito pequeno")
                        return False
                
                # Test GET /api/predictions
                async with session.get(f"{base_url}/api/predictions") as resp:
                    if resp.status != 200:
                        logger.error(f"Predictions endpoint falhou: {resp.status}")
                        return False
                
                # Test endpoint não existente
                async with session.get(f"{base_url}/api/nonexistent") as resp:
                    if resp.status != 404:
                        logger.error("Endpoint inexistente deveria retornar 404")
                        return False
            
            logger.info("✅ ProductionAPI funcionando corretamente")
            return True
            
        except Exception as e:
            logger.error(f"Erro na ProductionAPI: {e}")
            return False

    async def _test_health_checks(self) -> bool:
        """Teste: Sistema de Health Checks"""
        try:
            # Verifica se health checks estão rodando
            if not self.production_manager.health_check_task:
                logger.error("Health check task não iniciada")
                return False
            
            # Verifica componentes
            status = await self.production_manager.get_system_status()
            recent_checks = status.get("recent_health_checks", [])
            
            if len(recent_checks) == 0:
                logger.error("Nenhum health check executado")
                return False
            
            # Verifica se todos os componentes foram verificados
            checked_components = set(check["component"] for check in recent_checks)
            required_components = {"system_resources", "performance_monitor", "file_system"}
            
            if not required_components.issubset(checked_components):
                missing = required_components - checked_components
                logger.error(f"Componentes não verificados: {missing}")
                return False
            
            logger.info("✅ Health Checks funcionando corretamente")
            return True
            
        except Exception as e:
            logger.error(f"Erro nos Health Checks: {e}")
            return False

    async def _test_resource_monitoring(self) -> bool:
        """Teste: Monitoramento de Recursos"""
        try:
            # Verifica se resource monitor está rodando
            if not self.production_manager.resource_monitor_task:
                logger.error("Resource monitor task não iniciada")
                return False
            
            # Aguarda coleta de recursos
            await asyncio.sleep(3)
            
            # Verifica histórico de recursos
            if len(self.production_manager.resource_history) == 0:
                logger.error("Nenhum dado de recurso coletado")
                return False
            
            # Verifica dados válidos
            latest_resource = self.production_manager.resource_history[-1]
            
            if latest_resource.cpu_percent < 0 or latest_resource.cpu_percent > 100:
                logger.error(f"CPU percent inválido: {latest_resource.cpu_percent}")
                return False
            
            if latest_resource.memory_percent < 0 or latest_resource.memory_percent > 100:
                logger.error(f"Memory percent inválido: {latest_resource.memory_percent}")
                return False
            
            logger.info("✅ Resource Monitoring funcionando corretamente")
            return True
            
        except Exception as e:
            logger.error(f"Erro no Resource Monitoring: {e}")
            return False

    async def _test_websocket_streaming(self) -> bool:
        """Teste: WebSocket Streaming"""
        try:
            import websockets
            
            ws_url = f"ws://{self.config['api_host']}:{self.config['api_port']}/ws/metrics"
            
            # Conecta ao WebSocket
            async with websockets.connect(ws_url) as websocket:
                # Envia ping
                await websocket.send("ping")
                
                # Aguarda resposta
                response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                if response != "pong":
                    logger.error(f"Resposta inválida do WebSocket: {response}")
                    return False
                
                # Aguarda stream de métricas
                metrics_data = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                
                try:
                    data = json.loads(metrics_data)
                    if data.get("type") != "metrics_update":
                        logger.error("Tipo de mensagem inválido")
                        return False
                    
                    if not data.get("data"):
                        logger.error("Dados de métricas ausentes")
                        return False
                        
                except json.JSONDecodeError:
                    logger.error("JSON inválido recebido via WebSocket")
                    return False
            
            logger.info("✅ WebSocket Streaming funcionando corretamente")
            return True
            
        except ImportError:
            logger.warning("⚠️ websockets não instalado, pulando teste WebSocket")
            return True
        except Exception as e:
            logger.error(f"Erro no WebSocket: {e}")
            return False

    async def _test_emergency_recovery(self) -> bool:
        """Teste: Sistema de Emergency Recovery"""
        try:
            # Executa recovery de emergência
            success = await self.production_manager.perform_emergency_recovery()
            if not success:
                logger.error("Emergency recovery falhou")
                return False
            
            # Aguarda estabilização
            await asyncio.sleep(5)
            
            # Verifica se sistema voltou ao normal
            status = await self.production_manager.get_system_status()
            if status.get("system_status") not in ["healthy", "warning"]:
                logger.error(f"Sistema não se recuperou: {status.get('system_status')}")
                return False
            
            logger.info("✅ Emergency Recovery funcionando corretamente")
            return True
            
        except Exception as e:
            logger.error(f"Erro no Emergency Recovery: {e}")
            return False

    async def _test_full_integration(self) -> bool:
        """Teste: Integração completa do sistema"""
        try:
            # Simula fluxo completo de predição
            
            # 1. Cria predição via PerformanceMonitor
            monitor = self.production_manager.performance_monitor
            
            fake_prediction = type('obj', (object,), {
                'match_id': 'integration_test_456',
                'predicted_winner': 'T1',
                'win_probability': 0.78,
                'confidence_level': type('enum', (object,), {'value': 'very_high'})(),
                'method_used': type('enum', (object,), {'value': 'hybrid'})(),
                'processing_time_ms': 2150.0,
                'ml_prediction': {
                    'features': {
                        'composition_analysis': 0.4,
                        'patch_meta_analysis': 0.35,
                        'overall_advantage': 0.6
                    }
                }
            })()
            
            fake_odds = {
                "outcomes": [
                    {"name": "T1", "odd": 1.65},
                    {"name": "Gen.G", "odd": 2.35}
                ]
            }
            
            prediction_id = await monitor.track_prediction(fake_prediction, fake_odds, 15.0)
            
            # 2. Verifica via API
            base_url = f"http://{self.config['api_host']}:{self.config['api_port']}"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{base_url}/api/predictions") as resp:
                    data = await resp.json()
                    predictions = data.get("data", {}).get("predictions", [])
                    
                    found_prediction = None
                    for pred in predictions:
                        if pred["prediction_id"] == prediction_id:
                            found_prediction = pred
                            break
                    
                    if not found_prediction:
                        logger.error("Predição não encontrada via API")
                        return False
            
            # 3. Resolve predição
            await monitor.resolve_prediction(prediction_id, "T1")
            
            # 4. Verifica métricas atualizadas
            metrics = await monitor.get_current_metrics()
            if metrics.total_predictions < 2:  # Deve ter pelo menos 2 predições agora
                logger.error("Métricas não atualizaram corretamente")
                return False
            
            # 5. Verifica dashboard atualizado
            dashboard_data = monitor.get_live_dashboard_data()
            if not dashboard_data or dashboard_data.get("current_metrics", {}).get("total_predictions", 0) < 2:
                logger.error("Dashboard não atualizou corretamente")
                return False
            
            logger.info("✅ Integração completa funcionando corretamente")
            return True
            
        except Exception as e:
            logger.error(f"Erro na integração completa: {e}")
            return False

    async def _test_cleanup(self) -> bool:
        """Teste: Cleanup do sistema"""
        try:
            # Para API
            if self.production_api:
                await self.production_api.stop_api_server()
            
            # Para Production Manager
            if self.production_manager:
                await self.production_manager.stop_production_system()
            
            # Remove arquivos de teste
            test_files = [
                "bot/data/monitoring/test_dashboard.html",
                "bot/data/monitoring/health_check_test.txt"
            ]
            
            for file_path in test_files:
                try:
                    Path(file_path).unlink(missing_ok=True)
                except:
                    pass
            
            logger.info("✅ Cleanup concluído")
            return True
            
        except Exception as e:
            logger.error(f"Erro no cleanup: {e}")
            return False

    def _generate_test_report(self):
        """Gera relatório final dos testes"""
        logger.info("\n" + "=" * 80)
        logger.info("📊 RELATÓRIO FINAL DOS TESTES DE INTEGRAÇÃO")
        logger.info("=" * 80)
        
        total_tests = len(self.test_results)
        passed = sum(1 for r in self.test_results if r["status"] == "PASS")
        failed = sum(1 for r in self.test_results if r["status"] == "FAIL")
        errors = sum(1 for r in self.test_results if r["status"] == "ERROR")
        
        logger.info(f"📈 Total de testes: {total_tests}")
        logger.info(f"✅ Passou: {passed}")
        logger.info(f"❌ Falhou: {failed}")
        logger.info(f"🔥 Erro: {errors}")
        logger.info(f"📊 Taxa de sucesso: {(passed/total_tests)*100:.1f}%")
        
        logger.info("\n📋 DETALHES DOS TESTES:")
        for result in self.test_results:
            status_icon = {"PASS": "✅", "FAIL": "❌", "ERROR": "🔥"}[result["status"]]
            duration = result.get("duration", 0)
            logger.info(f"   {status_icon} {result['test']} ({duration:.2f}s)")
            
            if result["status"] == "ERROR":
                logger.info(f"      💥 Erro: {result.get('error', 'N/A')}")
        
        if failed == 0 and errors == 0:
            logger.info("\n🎉 TODOS OS TESTES PASSARAM! Sistema está funcionando perfeitamente!")
        else:
            logger.info(f"\n⚠️ {failed + errors} teste(s) falharam. Verifique os logs acima.")
        
        logger.info("=" * 80)


async def main():
    """Função principal dos testes"""
    try:
        # Banner
        print("\n" + "="*80)
        print("🧪 BOT LOL V3 ULTRA AVANÇADO - TESTES DE INTEGRAÇÃO")
        print("📅 SEMANA 4: Validação Completa do Sistema")
        print("="*80)
        
        # Executa testes
        tests = ProductionIntegrationTests()
        success = await tests.run_all_tests()
        
        if success:
            print("\n🎉 TODOS OS TESTES PASSARAM!")
            return 0
        else:
            print("\n❌ ALGUNS TESTES FALHARAM!")
            return 1
            
    except KeyboardInterrupt:
        logger.info("🛑 Testes interrompidos pelo usuário")
        return 1
    except Exception as e:
        logger.error(f"❌ Erro fatal nos testes: {e}")
        return 1


if __name__ == "__main__":
    # Verifica dependências
    try:
        import aiohttp
        import psutil
    except ImportError as e:
        print(f"❌ Dependência faltando: {e}")
        print("💡 Execute: pip install -r requirements.txt")
        exit(1)
    
    # Executa testes
    exit_code = asyncio.run(main())
    exit(exit_code) 