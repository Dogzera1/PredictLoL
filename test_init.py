#!/usr/bin/env python3
"""Script de teste para verificar inicialização"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    print("🧪 Testando inicialização...")
    from main import BotApplication
    print("✅ Import do BotApplication OK")
    
    app = BotApplication()
    print("✅ BotApplication inicializada OK")
    
    print("🔄 Testando componentes...")
    from bot.core_logic import DynamicPredictionSystem, LoLGameAnalyzer, ProfessionalUnitsSystem
    print("✅ Core Logic imports OK")
    
    units_system = ProfessionalUnitsSystem()
    print("✅ ProfessionalUnitsSystem OK")
    
    game_analyzer = LoLGameAnalyzer()
    print("✅ LoLGameAnalyzer OK")
    
    prediction_system = DynamicPredictionSystem(
        game_analyzer=game_analyzer,
        units_system=units_system
    )
    print("✅ DynamicPredictionSystem OK")
    
    print("🎉 TODOS OS TESTES PASSARAM!")
    
except ImportError as e:
    print(f"❌ Erro de import: {e}")
except Exception as e:
    print(f"❌ Erro: {e}")
    import traceback
    traceback.print_exc() 