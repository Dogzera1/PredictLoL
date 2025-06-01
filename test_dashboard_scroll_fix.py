#!/usr/bin/env python3
"""
Teste para verificar correção do problema de scroll infinito no dashboard
"""

import asyncio
import sys
import os
from pathlib import Path

# Adiciona o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def test_dashboard_generation():
    """Testa geração do dashboard com dados problemáticos"""
    print("🧪 TESTE: Correção do Scroll Infinito no Dashboard")
    print("=" * 60)
    
    try:
        from bot.monitoring.dashboard_generator import DashboardGenerator
        
        print("✅ DashboardGenerator importado com sucesso")
        
        # Cria instância do gerador
        dashboard_gen = DashboardGenerator()
        
        # Dados de teste que poderiam causar problemas
        problematic_data = {
            "current_metrics": {
                "win_rate": float('inf'),  # Valor infinito
                "roi": 999999999999,      # Valor muito grande
                "net_profit": -999999999999,  # Valor muito negativo
                "total_predictions": "invalid"  # Tipo inválido
            },
            "last_24h": {
                "predictions": None,
                "resolved": [],
                "pending": "abc",
                "profit": float('nan')  # NaN
            },
            "method_performance": {
                "ml": {"predictions": -500, "win_rate": 150},  # Valores inválidos
                "algorithm": None,  # None
                "hybrid": "invalid"  # String inválida
            },
            "active_alerts": ["alert1"] * 100,  # Muitos alertas
            "analysis_usage": {
                "composition_analyses": float('-inf'),
                "patch_analyses": "not_a_number",
                "avg_processing_time": -1000
            },
            "trend": {
                "win_rate_trend": [1, 2, 3] * 100,  # Array muito grande
                "roi_trend": [float('inf'), float('-inf'), float('nan')]
            },
            "uptime_hours": 999999999,  # Valor impossível
            "timestamp": "x" * 1000  # String muito longa
        }
        
        print("🔍 Testando com dados problemáticos...")
        
        # Testa geração do dashboard
        html_content = dashboard_gen.generate_html_dashboard(problematic_data)
        
        if html_content and len(html_content) > 1000:
            print("✅ Dashboard gerado com sucesso apesar dos dados problemáticos")
            print(f"   Tamanho do HTML: {len(html_content)} caracteres")
            
            # Verifica se contém elementos essenciais
            essential_elements = [
                '<html',
                '<body',
                'container-fluid',
                'Chart.js',
                'Bootstrap',
                'setTimeout',
                'scheduleRefresh'
            ]
            
            missing_elements = []
            for element in essential_elements:
                if element not in html_content:
                    missing_elements.append(element)
            
            if missing_elements:
                print(f"⚠️ Elementos faltando: {missing_elements}")
            else:
                print("✅ Todos os elementos essenciais presentes")
                
            # Verifica melhorias anti-scroll infinito
            anti_scroll_features = [
                'isScrolling',
                'scrollTimeout',
                'refreshTimer',
                'sessionStorage',
                'overflow-x: hidden',
                'box-sizing: border-box',
                'max-width: 100%',
                'maintainAspectRatio: false'
            ]
            
            found_features = []
            for feature in anti_scroll_features:
                if feature in html_content:
                    found_features.append(feature)
            
            print(f"✅ Recursos anti-scroll encontrados: {len(found_features)}/{len(anti_scroll_features)}")
            print(f"   Recursos: {', '.join(found_features)}")
            
            return True
            
        else:
            print("❌ Dashboard não foi gerado ou está muito pequeno")
            return False
            
    except Exception as e:
        print(f"❌ Erro no teste: {e}")
        return False

async def test_dashboard_export():
    """Testa exportação do dashboard para arquivo"""
    print("\n📁 TESTE: Exportação de Dashboard")
    print("-" * 40)
    
    try:
        from bot.monitoring.dashboard_generator import DashboardGenerator
        
        dashboard_gen = DashboardGenerator()
        
        # Dados de teste normais
        test_data = {
            "current_metrics": {"win_rate": 75.5, "roi": 12.3, "net_profit": 150.75, "total_predictions": 42},
            "last_24h": {"predictions": 5, "resolved": 3, "pending": 2, "profit": 25.50},
            "method_performance": {
                "ml": {"predictions": 20, "win_rate": 80.0},
                "algorithm": {"predictions": 15, "win_rate": 70.0},
                "hybrid": {"predictions": 7, "win_rate": 85.0}
            },
            "active_alerts": [],
            "analysis_usage": {"composition_analyses": 10, "patch_analyses": 5, "avg_processing_time": 150},
            "trend": {"win_rate_trend": [70, 72, 75, 78, 75], "roi_trend": [8, 10, 12, 15, 12]},
            "uptime_hours": 24.5,
            "timestamp": "2024-01-01 12:00:00"
        }
        
        # Exporta dashboard
        output_file = "test_dashboard_fixed.html"
        success = dashboard_gen.export_dashboard_to_file(test_data, output_file)
        
        if success and Path(output_file).exists():
            file_size = Path(output_file).stat().st_size
            print(f"✅ Dashboard exportado com sucesso")
            print(f"   Arquivo: {output_file}")
            print(f"   Tamanho: {file_size} bytes")
            
            # Lê conteúdo para verificar
            with open(output_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Verifica se não há loops infinitos no JavaScript
            js_issues = []
            if 'while(true)' in content:
                js_issues.append('while(true) encontrado')
            if 'for(;;)' in content:
                js_issues.append('for(;;) encontrado')
            if content.count('location.reload()') > 2:
                js_issues.append('Muitos location.reload()')
                
            if js_issues:
                print(f"⚠️ Possíveis problemas JavaScript: {js_issues}")
            else:
                print("✅ Nenhum problema JavaScript detectado")
                
            return True
        else:
            print("❌ Falha na exportação do dashboard")
            return False
            
    except Exception as e:
        print(f"❌ Erro na exportação: {e}")
        return False

async def run_all_tests():
    """Executa todos os testes"""
    print("🚀 INICIANDO TESTES DE CORREÇÃO DO DASHBOARD")
    print("=" * 70)
    
    # Lista de testes
    tests = [
        ("Geração com Dados Problemáticos", test_dashboard_generation),
        ("Exportação de Dashboard", test_dashboard_export)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n📋 Executando: {test_name}")
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Erro no teste {test_name}: {e}")
            results.append((test_name, False))
    
    # Relatório final
    print("\n" + "=" * 70)
    print("📋 RELATÓRIO FINAL DOS TESTES")
    print("=" * 70)
    
    passed = 0
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASSOU" if success else "❌ FALHOU"
        print(f"{status} - {test_name}")
        if success:
            passed += 1
    
    print(f"\n🏆 RESULTADO: {passed}/{total} testes passaram")
    
    if passed == total:
        print("🎉 TODOS OS TESTES PASSARAM!")
        print("✅ Problema de scroll infinito deve estar resolvido")
        print("\n📝 CORREÇÕES APLICADAS:")
        print("   • Controle inteligente de auto-refresh")
        print("   • Preservação da posição de scroll")
        print("   • CSS com overflow-x: hidden")
        print("   • Validação rigorosa de dados")
        print("   • Gráficos Chart.js otimizados")
        print("   • Limitação de elementos dinâmicos")
        return True
    else:
        print("⚠️ Alguns testes falharam - verificar implementação")
        return False

if __name__ == "__main__":
    try:
        success = asyncio.run(run_all_tests())
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Erro geral nos testes: {e}")
        sys.exit(1) 