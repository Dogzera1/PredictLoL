#!/usr/bin/env python3
"""
🔧 TESTE: Imports Corrigidos
Verifica se todos os imports problemáticos foram corrigidos
"""

import sys
import os

# Adiciona o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports_corrigidos():
    """Testa todos os imports que estavam com problema"""
    print("🔧 TESTE DOS IMPORTS CORRIGIDOS")
    print("=" * 50)
    
    erros = []
    sucessos = []
    
    # 1. Teste ProfessionalTipsSystem
    print("\n1️⃣ Testando ProfessionalTipsSystem...")
    try:
        from bot.systems.tips_system import ProfessionalTipsSystem
        print("   ✅ Import correto: bot.systems.tips_system")
        sucessos.append("ProfessionalTipsSystem")
    except ImportError as e:
        print(f"   ❌ Erro: {e}")
        erros.append(f"ProfessionalTipsSystem: {e}")
    
    # 2. Teste DynamicPredictionSystem
    print("\n2️⃣ Testando DynamicPredictionSystem...")
    try:
        from bot.core_logic.prediction_system import DynamicPredictionSystem
        print("   ✅ Import correto: bot.core_logic.prediction_system")
        sucessos.append("DynamicPredictionSystem")
    except ImportError as e:
        print(f"   ❌ Erro: {e}")
        erros.append(f"DynamicPredictionSystem: {e}")
    
    # 3. Teste LoLGameAnalyzer
    print("\n3️⃣ Testando LoLGameAnalyzer...")
    try:
        from bot.core_logic.game_analyzer import LoLGameAnalyzer
        print("   ✅ Import correto: bot.core_logic.game_analyzer")
        sucessos.append("LoLGameAnalyzer")
    except ImportError as e:
        print(f"   ❌ Erro: {e}")
        erros.append(f"LoLGameAnalyzer: {e}")
    
    # 4. Teste TipStatus (que foi corrigido anteriormente)
    print("\n4️⃣ Testando TipStatus...")
    try:
        from bot.systems import TipStatus
        print("   ✅ Import correto: bot.systems")
        sucessos.append("TipStatus")
    except ImportError as e:
        print(f"   ❌ Erro: {e}")
        erros.append(f"TipStatus: {e}")
    
    # 5. Teste outros imports importantes
    print("\n5️⃣ Testando outros imports importantes...")
    try:
        from bot.systems import ScheduleManager
        from bot.monitoring.performance_monitor import PerformanceMonitor
        from bot.core_logic.units_system import ProfessionalUnitsSystem
        print("   ✅ Todos os imports auxiliares funcionando")
        sucessos.append("Imports auxiliares")
    except ImportError as e:
        print(f"   ❌ Erro em imports auxiliares: {e}")
        erros.append(f"Imports auxiliares: {e}")
    
    # Resumo
    print("\n" + "=" * 50)
    print("📊 RESUMO DOS IMPORTS")
    print("=" * 50)
    
    print(f"\n✅ SUCESSOS ({len(sucessos)}):")
    for sucesso in sucessos:
        print(f"   ✅ {sucesso}")
    
    if erros:
        print(f"\n❌ ERROS ({len(erros)}):")
        for erro in erros:
            print(f"   ❌ {erro}")
    else:
        print(f"\n🎉 TODOS OS IMPORTS FUNCIONANDO CORRETAMENTE!")
    
    # Status final
    total = len(sucessos) + len(erros)
    porcentagem = (len(sucessos) / total) * 100 if total > 0 else 0
    
    print(f"\n📈 STATUS: {len(sucessos)}/{total} imports funcionando ({porcentagem:.1f}%)")
    
    if porcentagem == 100:
        print("🟢 TODOS OS PROBLEMAS DE IMPORT RESOLVIDOS!")
        return True
    elif porcentagem >= 80:
        print("🟡 MAIORIA DOS IMPORTS FUNCIONANDO")
        return False
    else:
        print("🔴 AINDA HÁ PROBLEMAS DE IMPORT")
        return False

if __name__ == "__main__":
    test_imports_corrigidos() 