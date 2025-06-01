#!/usr/bin/env python3
"""
Teste Simples de Funcionalidade - Bot LoL V3 Ultra Avançado
Verifica se todos os componentes principais estão funcionando

Execução:
    python test_bot_funcional_simples.py
"""

import asyncio
import time
import sys
from pathlib import Path

# Adiciona o diretório raiz ao path
sys.path.append(str(Path(__file__).parent))

from bot.deployment.production_manager import ProductionManager
from bot.deployment.production_api import ProductionAPI
from bot.monitoring.performance_monitor import PerformanceMonitor
from bot.monitoring.dashboard_generator import DashboardGenerator
from bot.utils.logger_config import get_logger

logger = get_logger(__name__)


class SimpleFunctionalTest:
    """Teste simplificado de funcionalidade"""

    def __init__(self):
        """Inicializa o teste"""
        self.results = []
        
    async def run_tests(self):
        """Executa todos os testes básicos"""
        print("\n" + "="*80)
        print("🧪 BOT LOL V3 ULTRA AVANÇADO - TESTE DE FUNCIONALIDADE")
        print("📅 SEMANA 4: Verificação Simples dos Componentes")
        print("="*80)
        
        tests = [
            ("📦 Importações e Dependências", self.test_imports),
            ("📊 Performance Monitor", self.test_performance_monitor),
            ("📱 Dashboard Generator", self.test_dashboard_generator),
            ("🏗️ Production Manager - Básico", self.test_production_manager_basic),
            ("🌐 Production API - Básico", self.test_production_api_basic),
            ("📈 Simulação de Predição Completa", self.test_prediction_flow),
            ("💾 Persistência de Dados", self.test_data_persistence),
        ]
        
        all_passed = True
        
        for test_name, test_func in tests:
            print(f"\n🔍 {test_name}...")
            
            try:
                start_time = time.time()
                result = await test_func()
                duration = time.time() - start_time
                
                if result:
                    print(f"✅ {test_name} - PASSOU ({duration:.2f}s)")
                    self.results.append({"test": test_name, "status": "PASS", "duration": duration})
                else:
                    print(f"❌ {test_name} - FALHOU ({duration:.2f}s)")
                    self.results.append({"test": test_name, "status": "FAIL", "duration": duration})
                    all_passed = False
                    
            except Exception as e:
                print(f"💥 {test_name} - ERRO: {e}")
                self.results.append({"test": test_name, "status": "ERROR", "error": str(e)})
                all_passed = False
        
        # Relatório final
        self.print_final_report()
        return all_passed

    async def test_imports(self):
        """Testa importações críticas"""
        try:
            # Testa importações básicas
            import aiohttp
            import psutil
            import aiohttp_cors
            import json
            
            # Testa importações do bot
            from bot.monitoring.performance_monitor import PerformanceMonitor, PredictionMetrics
            from bot.monitoring.dashboard_generator import DashboardGenerator
            from bot.deployment.production_manager import ProductionManager
            from bot.deployment.production_api import ProductionAPI
            
            print("   ✓ Todas as dependências importadas com sucesso")
            return True
            
        except ImportError as e:
            print(f"   ✗ Falha na importação: {e}")
            return False

    async def test_performance_monitor(self):
        """Testa PerformanceMonitor básico"""
        try:
            monitor = PerformanceMonitor()
            
            # Cria dados de teste
            fake_prediction = type('obj', (object,), {
                'match_id': 'test_001',
                'predicted_winner': 'Team A',
                'win_probability': 0.75,
                'confidence_level': type('enum', (object,), {'value': 'high'})(),
                'method_used': type('enum', (object,), {'value': 'hybrid'})(),
                'processing_time_ms': 1500.0,
                'ml_prediction': {'features': {'composition_analysis': 0.3}}
            })()
            
            fake_odds = {"outcomes": [{"name": "Team A", "odd": 1.80}]}
            
            # Testa tracking
            pred_id = await monitor.track_prediction(fake_prediction, fake_odds, 10.0)
            if not pred_id:
                print("   ✗ Falha ao trackear predição")
                return False
            
            # Testa resolução
            success = await monitor.resolve_prediction(pred_id, "Team A")
            if not success:
                print("   ✗ Falha ao resolver predição")
                return False
            
            # Testa métricas
            metrics = await monitor.get_current_metrics()
            if metrics.total_predictions < 1:
                print("   ✗ Métricas não atualizadas")
                return False
            
            print(f"   ✓ PerformanceMonitor OK - {metrics.total_predictions} predições, ROI: {metrics.roi_percentage:.1f}%")
            return True
            
        except Exception as e:
            print(f"   ✗ Erro no PerformanceMonitor: {e}")
            return False

    async def test_dashboard_generator(self):
        """Testa DashboardGenerator"""
        try:
            dashboard_gen = DashboardGenerator()
            
            # Dados de teste
            test_data = {
                "timestamp": "2024-01-01T12:00:00",
                "current_metrics": {"total_predictions": 50, "win_rate": 80.0, "roi": 15.5, "net_profit": 125.0},
                "last_24h": {"predictions": 10, "resolved": 8, "pending": 2, "profit": 25.0},
                "method_performance": {"ml": {"predictions": 20, "win_rate": 85.0}},
                "active_alerts": [],
                "analysis_usage": {"composition_analyses": 30, "avg_processing_time": 1200},
                "trend": {"win_rate_trend": [78, 80], "roi_trend": [14, 15.5]}
            }
            
            # Gera HTML
            html = dashboard_gen.generate_html_dashboard(test_data)
            if len(html) < 5000:
                print("   ✗ HTML gerado muito pequeno")
                return False
            
            # Verifica elementos essenciais
            if "80.0%" not in html or "125.0" not in html:
                print("   ✗ Dados não encontrados no HTML")
                return False
            
            print(f"   ✓ Dashboard HTML gerado ({len(html)} chars)")
            return True
            
        except Exception as e:
            print(f"   ✗ Erro no DashboardGenerator: {e}")
            return False

    async def test_production_manager_basic(self):
        """Testa ProductionManager básico (sem inicialização completa)"""
        try:
            # Testa apenas criação e configuração
            config = {
                "monitoring_interval": 60,
                "health_check_interval": 30,
                "auto_recovery": True
            }
            
            manager = ProductionManager(config=config)
            
            # Verifica se foi criado corretamente
            if not hasattr(manager, 'performance_monitor'):
                print("   ✗ PerformanceMonitor não foi criado")
                return False
            
            if not hasattr(manager, 'dashboard_generator'):
                print("   ✗ DashboardGenerator não foi criado")
                return False
            
            # Testa método de recursos sem inicializar sistema completo
            resources = manager._get_current_resources()
            if resources.cpu_percent < 0 or resources.memory_percent < 0:
                print("   ✗ Recursos do sistema inválidos")
                return False
            
            print(f"   ✓ ProductionManager criado - CPU: {resources.cpu_percent:.1f}%, MEM: {resources.memory_percent:.1f}%")
            return True
            
        except Exception as e:
            print(f"   ✗ Erro no ProductionManager: {e}")
            return False

    async def test_production_api_basic(self):
        """Testa ProductionAPI básico (apenas criação)"""
        try:
            # Cria um manager mock simples
            mock_manager = type('MockManager', (), {
                'performance_monitor': PerformanceMonitor(),
                'dashboard_generator': DashboardGenerator(),
                'get_system_status': lambda: {"status": "healthy"}
            })()
            
            # Testa criação da API
            api = ProductionAPI(
                production_manager=mock_manager,
                host="localhost",
                port=8082
            )
            
            # Verifica se foi criado corretamente
            if not hasattr(api, 'production_manager'):
                print("   ✗ ProductionManager não foi associado")
                return False
            
            if api.host != "localhost" or api.port != 8082:
                print("   ✗ Configuração de host/port incorreta")
                return False
            
            print(f"   ✓ ProductionAPI criada - {api.host}:{api.port}")
            return True
            
        except Exception as e:
            print(f"   ✗ Erro na ProductionAPI: {e}")
            return False

    async def test_prediction_flow(self):
        """Testa fluxo completo de predição"""
        try:
            monitor = PerformanceMonitor()
            dashboard_gen = DashboardGenerator()
            
            # Simula múltiplas predições
            predictions_data = [
                ("T1", "Gen.G", 0.65, 1.75, "T1"),
                ("DWG", "DRX", 0.72, 1.55, "DWG"),
                ("FNC", "G2", 0.58, 1.95, "G2"),  # Esta perdeu
            ]
            
            total_profit = 0
            
            for i, (team1, team2, prob, odds, winner) in enumerate(predictions_data):
                # Cria predição
                fake_pred = type('obj', (object,), {
                    'match_id': f'flow_test_{i}',
                    'predicted_winner': team1,
                    'win_probability': prob,
                    'confidence_level': type('enum', (object,), {'value': 'high'})(),
                    'method_used': type('enum', (object,), {'value': 'hybrid'})(),
                    'processing_time_ms': 1200.0 + (i * 100),
                    'ml_prediction': {'features': {'composition_analysis': 0.3 + (i * 0.1)}}
                })()
                
                fake_odds = {"outcomes": [{"name": team1, "odd": odds}]}
                
                # Trackea
                pred_id = await monitor.track_prediction(fake_pred, fake_odds, 15.0)
                
                # Resolve
                await monitor.resolve_prediction(pred_id, winner)
                
                # Calcula profit
                is_correct = team1 == winner
                if is_correct:
                    total_profit += (15.0 * odds) - 15.0
                else:
                    total_profit -= 15.0
            
            # Verifica métricas finais
            metrics = await monitor.get_current_metrics()
            if metrics.total_predictions < 3:
                print("   ✗ Não processou todas as predições")
                return False
            
            # Gera dashboard com dados reais
            dashboard_data = monitor.get_live_dashboard_data()
            html = dashboard_gen.generate_html_dashboard(dashboard_data)
            
            if len(html) < 5000:
                print("   ✗ Dashboard não gerado corretamente")
                return False
            
            print(f"   ✓ Fluxo completo - {metrics.total_predictions} predições, Win Rate: {metrics.win_rate_percentage:.1f}%, ROI: {metrics.roi_percentage:.1f}%")
            return True
            
        except Exception as e:
            print(f"   ✗ Erro no fluxo de predição: {e}")
            return False

    async def test_data_persistence(self):
        """Testa persistência de dados"""
        try:
            # Cria diretórios se não existem
            Path("bot/data/monitoring").mkdir(parents=True, exist_ok=True)
            
            monitor = PerformanceMonitor()
            
            # Adiciona uma predição para ter dados
            fake_pred = type('obj', (object,), {
                'match_id': 'persistence_test',
                'predicted_winner': 'Test Team',
                'win_probability': 0.80,
                'confidence_level': type('enum', (object,), {'value': 'very_high'})(),
                'method_used': type('enum', (object,), {'value': 'hybrid'})(),
                'processing_time_ms': 1000.0,
                'ml_prediction': {'features': {'composition_analysis': 0.4}}
            })()
            
            fake_odds = {"outcomes": [{"name": "Test Team", "odd": 2.0}]}
            pred_id = await monitor.track_prediction(fake_pred, fake_odds, 20.0)
            await monitor.resolve_prediction(pred_id, "Test Team")
            
            # Salva dados
            await monitor._save_performance_data()
            
            # Verifica se arquivos foram criados
            files_to_check = [
                "bot/data/monitoring/predictions.json",
                "bot/data/monitoring/system_metrics.json",
                "bot/data/monitoring/alerts.json"
            ]
            
            for file_path in files_to_check:
                if not Path(file_path).exists():
                    print(f"   ✗ Arquivo não criado: {file_path}")
                    return False
            
            # Testa carregamento
            new_monitor = PerformanceMonitor()
            await new_monitor._load_historical_data()
            
            if len(new_monitor.predictions) == 0:
                print("   ✗ Dados não foram carregados")
                return False
            
            print(f"   ✓ Persistência OK - {len(new_monitor.predictions)} predições salvas/carregadas")
            return True
            
        except Exception as e:
            print(f"   ✗ Erro na persistência: {e}")
            return False

    def print_final_report(self):
        """Imprime relatório final"""
        print("\n" + "="*80)
        print("📊 RELATÓRIO FINAL DE FUNCIONALIDADE")
        print("="*80)
        
        total = len(self.results)
        passed = sum(1 for r in self.results if r["status"] == "PASS")
        failed = sum(1 for r in self.results if r["status"] == "FAIL")
        errors = sum(1 for r in self.results if r["status"] == "ERROR")
        
        print(f"📈 Total de testes: {total}")
        print(f"✅ Passou: {passed}")
        print(f"❌ Falhou: {failed}")
        print(f"💥 Erro: {errors}")
        print(f"📊 Taxa de sucesso: {(passed/total)*100:.1f}%")
        
        print(f"\n📋 DETALHES:")
        for result in self.results:
            status_icon = {"PASS": "✅", "FAIL": "❌", "ERROR": "💥"}[result["status"]]
            duration = result.get("duration", 0)
            print(f"   {status_icon} {result['test']} ({duration:.2f}s)")
        
        if failed == 0 and errors == 0:
            print(f"\n🎉 BOT 100% FUNCIONAL!")
            print("🚀 Todos os componentes principais estão funcionando perfeitamente!")
            print("✨ Sistema pronto para produção!")
        else:
            print(f"\n⚠️ {failed + errors} componente(s) com problemas")
            print("🔧 Verificar logs acima para detalhes")
        
        print("="*80)


async def main():
    """Função principal"""
    try:
        test = SimpleFunctionalTest()
        success = await test.run_tests()
        
        if success:
            print("\n🎉 SISTEMA 100% FUNCIONAL!")
            return 0
        else:
            print("\n⚠️ ALGUNS COMPONENTES PRECISAM DE ATENÇÃO")
            return 1
            
    except KeyboardInterrupt:
        print("\n🛑 Teste interrompido")
        return 1
    except Exception as e:
        print(f"\n💥 Erro fatal: {e}")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code) 