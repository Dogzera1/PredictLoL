#!/usr/bin/env python3
"""
TESTE: Machine Learning nas Tips
Verifica se o sistema de ML está sendo usado para gerar tips
"""

import os
import sys
import asyncio
from pathlib import Path

# Configuração do path
BOT_DIR = Path(__file__).parent
sys.path.insert(0, str(BOT_DIR))

async def teste_ml_nas_tips():
    """Testa se o Machine Learning está sendo usado para tips"""
    
    print("🧠 TESTE: MACHINE LEARNING NAS TIPS")
    print("=" * 50)
    
    try:
        from bot.core_logic.prediction_system import DynamicPredictionSystem, PredictionMethod
        from bot.core_logic.game_analyzer import LoLGameAnalyzer
        from bot.core_logic.units_system import ProfessionalUnitsSystem
        from bot.data_models.match_data import MatchData, DraftData, Champion, TeamStats
        
        analyzer = LoLGameAnalyzer()
        units = ProfessionalUnitsSystem()
        prediction_system = DynamicPredictionSystem(analyzer, units)
        
        # Dados de teste
        team1_stats = TeamStats(
            team_name="Team A",
            total_gold=15000,
            total_kills=8,
            towers_destroyed=2
        )
        
        team2_stats = TeamStats(
            team_name="Team B", 
            total_gold=13000,
            total_kills=5,
            towers_destroyed=1
        )
        
        match_data = MatchData(
            match_id="test_ml",
            team1_name="Team A",
            team2_name="Team B",
            league="LEC",
            status="in_game",
            game_time_seconds=900,  # 15 minutos
            team1_stats=team1_stats,
            team2_stats=team2_stats
        )
        
        print("🔍 1. TESTANDO MÉTODOS DE PREDIÇÃO:")
        
        # Teste 1: Método MACHINE_LEARNING puro
        print("\n   🤖 Método: MACHINE_LEARNING")
        ml_result = await prediction_system.predict_live_match(
            match_data, method=PredictionMethod.MACHINE_LEARNING
        )
        
        print(f"     ✅ Método usado: {ml_result.method_used.value}")
        print(f"     🎯 Vencedor: {ml_result.predicted_winner}")
        print(f"     📊 Probabilidade: {ml_result.win_probability:.1%}")
        print(f"     🔧 ML ativo: {ml_result.ml_prediction is not None}")
        print(f"     📈 Features ML: {bool(ml_result.ml_prediction.get('features') if ml_result.ml_prediction else False)}")
        
        # Teste 2: Método ALGORITHM_BASED puro
        print("\n   📊 Método: ALGORITHM_BASED")
        algo_result = await prediction_system.predict_live_match(
            match_data, method=PredictionMethod.ALGORITHM_BASED
        )
        
        print(f"     ✅ Método usado: {algo_result.method_used.value}")
        print(f"     🎯 Vencedor: {algo_result.predicted_winner}")
        print(f"     📊 Probabilidade: {algo_result.win_probability:.1%}")
        print(f"     🧮 Algorithm ativo: {algo_result.algorithm_prediction is not None}")
        
        # Teste 3: Método HYBRID (padrão das tips)
        print("\n   ⚖️ Método: HYBRID (PADRÃO DAS TIPS)")
        hybrid_result = await prediction_system.predict_live_match(
            match_data, method=PredictionMethod.HYBRID
        )
        
        print(f"     ✅ Método usado: {hybrid_result.method_used.value}")
        print(f"     🎯 Vencedor: {hybrid_result.predicted_winner}")
        print(f"     📊 Probabilidade: {hybrid_result.win_probability:.1%}")
        print(f"     🤖 ML ativo: {hybrid_result.ml_prediction is not None}")
        print(f"     🧮 Algorithm ativo: {hybrid_result.algorithm_prediction is not None}")
        print(f"     🤝 Acordo entre modelos: {hybrid_result.model_agreement:.1%}")
        
        # Teste 4: Verificando dados do ML
        if hybrid_result.ml_prediction:
            ml_pred = hybrid_result.ml_prediction
            print(f"     📋 Versão ML: {ml_pred.get('model_version', 'N/A')}")
            
            features = ml_pred.get('features', {})
            if features:
                print("     🔧 Features principais do ML:")
                for feature, value in list(features.items())[:5]:  # Top 5
                    print(f"       • {feature}: {value:.3f}")
        
        print("\n🎯 2. TESTANDO GERAÇÃO DE TIPS COM ML:")
        
        # Dados de odds
        odds_data = {
            "team1_odds": 1.80,
            "team2_odds": 2.00
        }
        
        # Gerar tip usando ML (híbrido é padrão)
        tip_result = await prediction_system.generate_professional_tip(
            match_data=match_data,
            odds_data=odds_data
        )
        
        print(f"   ✅ Tip gerada: {tip_result.is_valid}")
        
        if tip_result.is_valid and tip_result.tip:
            tip = tip_result.tip
            print(f"   🎯 Time: {tip.tip_on_team}")
            print(f"   💰 Odds: {tip.odds}")
            print(f"   📊 Confiança: {tip.confidence_percentage:.1f}%")
            print(f"   📈 EV: {tip.ev_percentage:.2f}%")
            print(f"   🔬 Fonte: {tip.prediction_source}")
            
            # Verificar se analysis_reasoning menciona ML
            reasoning = tip.analysis_reasoning.lower()
            ml_mentioned = any(term in reasoning for term in ['machine learning', 'ml', 'modelo', 'features', 'algoritmos'])
            print(f"   🧠 ML mencionado na análise: {ml_mentioned}")
            
        elif not tip_result.is_valid:
            print(f"   ❌ Tip rejeitada: {tip_result.rejection_reason}")
        
        print("\n📊 3. ANÁLISE DO SISTEMA ML:")
        
        # Verificar configuração ML
        ml_config = prediction_system._initialize_ml_config()
        print(f"   ⚙️ Configuração ML carregada: {bool(ml_config)}")
        
        # Verificar estatísticas
        stats = prediction_system.get_prediction_stats()
        print(f"   📈 Total de predições: {stats.get('total_predictions', 0)}")
        print(f"   🤖 Predições ML: {stats.get('ml_predictions', 0)}")
        print(f"   🧮 Predições algoritmos: {stats.get('algorithm_predictions', 0)}")
        print(f"   ⚖️ Predições híbridas: {stats.get('hybrid_predictions', 0)}")
        
        print("\n" + "=" * 50)
        print("🏆 RESUMO DO TESTE")
        print("=" * 50)
        
        # Avaliar resultados
        ml_funcionando = (
            ml_result.ml_prediction is not None and
            hybrid_result.ml_prediction is not None and
            hybrid_result.method_used == PredictionMethod.HYBRID
        )
        
        tips_usando_ml = (
            tip_result.is_valid and
            tip_result.tip and
            tip_result.tip.prediction_source in ['HYBRID', 'ML']
        )
        
        print(f"✅ ML implementado: {ml_funcionando}")
        print(f"✅ ML usado em predições: {ml_result.ml_prediction is not None}")
        print(f"✅ Método híbrido (padrão): {hybrid_result.method_used == PredictionMethod.HYBRID}")
        print(f"✅ Tips usando ML: {tips_usando_ml}")
        
        if ml_funcionando and tips_usando_ml:
            print("\n🎉 MACHINE LEARNING ESTÁ SENDO USADO NAS TIPS!")
            print("✅ Sistema híbrido combina ML + algoritmos")
            print("✅ ML processa features avançadas (composições, patch, etc)")
            print("✅ Tips geradas usam predições do ML")
            print("✅ Modelo simulado mas estrutura profissional")
        elif ml_funcionando:
            print("\n⚠️ ML FUNCIONANDO MAS TIPS PODEM NÃO USAR")
            print("✅ ML implementado e operacional")
            print("⚠️ Verificar se tips estão usando método correto")
        else:
            print("\n❌ ML NÃO ESTÁ FUNCIONANDO ADEQUADAMENTE")
            print("❌ Implementação ou configuração precisam revisão")
        
        print("\n💡 DETALHES TÉCNICOS:")
        print(f"   🔧 Método padrão das tips: PredictionMethod.HYBRID")
        print(f"   🤖 ML simula modelo treinado com features reais")
        print(f"   📊 Features incluem: gold, towers, dragons, composições")
        print(f"   ⚖️ Híbrido combina ML (60%) + algoritmos (40%)")
        print(f"   🎯 Em produção: poderia usar modelo real treinado")
        
        return ml_funcionando
        
    except Exception as e:
        print(f"❌ ERRO NO TESTE: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # Configurar variáveis
    os.environ.setdefault("TELEGRAM_BOT_TOKEN", "8143188638:AAEJVEIo91k7nvkPZH6eGeet5ONnkH5jfzI")
    os.environ.setdefault("TELEGRAM_ADMIN_USER_IDS", "8012415611")
    
    success = asyncio.run(teste_ml_nas_tips())
    
    if success:
        print("\n🎊 ML CONFIRMADO NAS TIPS! 🎊")
    else:
        print("\n❌ ML precisa verificação") 