#!/usr/bin/env python3
"""
Teste do Sistema de Predição Dinâmico - Bot LoL V3 Ultra Avançado

Script para testar predições ML + Algoritmos e geração de tips profissionais.
"""

import os
import sys
import asyncio
from typing import Dict, Any

# Adiciona o diretório atual ao path para importar módulos
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from bot.core_logic import (
    LoLGameAnalyzer, 
    ProfessionalUnitsSystem,
    DynamicPredictionSystem,
    PredictionMethod,
    PredictionConfidence
)
from bot.data_models.match_data import MatchData, TeamStats, GameEvent, DraftData
from bot.utils.logger_config import setup_logging, get_logger
from bot.utils.constants import UNITS_CONFIG

# Configuração de logging
logger = setup_logging(log_level="INFO", log_file=None)
test_logger = get_logger("test_prediction")


def create_test_match_data(scenario: str, game_time_minutes: int = 20) -> MatchData:
    """Cria dados de teste para diferentes cenários"""
    
    base_match = MatchData(
        match_id=f"pred_test_{scenario}_{game_time_minutes}min",
        team1_name="T1",
        team2_name="Gen.G",
        league="LCK",
        tournament="LCK Summer 2024",
        status="in_progress",
        game_time_seconds=game_time_minutes * 60
    )
    
    if scenario == "balanced_early":
        base_match.team1_stats = TeamStats(
            total_gold=12000, total_kills=2, total_cs=100,
            towers_destroyed=0, dragons_taken=1, barons_taken=0,
            heralds_taken=1, wards_placed=20, wards_destroyed=5
        )
        base_match.team2_stats = TeamStats(
            total_gold=11500, total_kills=3, total_cs=95,
            towers_destroyed=1, dragons_taken=0, barons_taken=0,
            heralds_taken=0, wards_placed=18, wards_destroyed=7
        )
        base_match.events = [
            GameEvent("DRAGON", "T1", 6*60),
            GameEvent("TOWER_DESTROYED", "Gen.G", 8*60),
            GameEvent("HERALD", "T1", 12*60)
        ]
    
    elif scenario == "t1_advantage":
        base_match.team1_stats = TeamStats(
            total_gold=28000, total_kills=8, total_cs=160,
            towers_destroyed=4, dragons_taken=3, barons_taken=1,
            heralds_taken=1, wards_placed=40, wards_destroyed=15
        )
        base_match.team2_stats = TeamStats(
            total_gold=21000, total_kills=3, total_cs=140,
            towers_destroyed=1, dragons_taken=0, barons_taken=0,
            heralds_taken=0, wards_placed=25, wards_destroyed=8
        )
        base_match.events = [
            GameEvent("DRAGON", "T1", 8*60),
            GameEvent("BARON_NASHOR", "T1", 20*60),
            GameEvent("TEAMFIGHT_WIN", "T1", 22*60),
            GameEvent("DRAGON", "T1", 25*60)
        ]
    
    elif scenario == "geng_comeback":
        base_match.team1_stats = TeamStats(
            total_gold=32000, total_kills=6, total_cs=220,
            towers_destroyed=2, dragons_taken=1, barons_taken=0,
            heralds_taken=1, wards_placed=50, wards_destroyed=20
        )
        base_match.team2_stats = TeamStats(
            total_gold=35000, total_kills=9, total_cs=235,
            towers_destroyed=5, dragons_taken=4, barons_taken=2,
            heralds_taken=1, wards_placed=55, wards_destroyed=25
        )
        base_match.events = [
            GameEvent("BARON_NASHOR", "Gen.G", 28*60),
            GameEvent("ACE", "Gen.G", 30*60),
            GameEvent("DRAGON_SOUL", "Gen.G", 32*60),
            GameEvent("BARON_NASHOR", "Gen.G", 35*60)
        ]
    
    # Draft padrão para todos os cenários
    base_match.draft_data = DraftData(
        team1_picks=["azir", "graves", "gnar", "jinx", "thresh"],
        team2_picks=["viktor", "lee", "camille", "caitlyn", "nautilus"],
        team1_bans=["yasuo", "zed", "akali"],
        team2_bans=["leblanc", "syndra", "orianna"]
    )
    
    return base_match


def create_test_odds_data(scenario: str) -> Dict[str, float]:
    """Cria dados de odds para testes"""
    odds_scenarios = {
        "balanced_early": {"team1_odds": 1.85, "team2_odds": 1.95},
        "t1_advantage": {"team1_odds": 1.45, "team2_odds": 2.75},
        "geng_comeback": {"team1_odds": 2.20, "team2_odds": 1.65},
        "high_value": {"team1_odds": 2.50, "team2_odds": 1.50},
        "low_value": {"team1_odds": 1.25, "team2_odds": 3.80}
    }
    return odds_scenarios.get(scenario, {"team1_odds": 2.0, "team2_odds": 2.0})


async def test_prediction_methods(prediction_system: DynamicPredictionSystem):
    """Testa diferentes métodos de predição"""
    print(f"\n{'='*70}")
    print("🧠 TESTE: MÉTODOS DE PREDIÇÃO")
    print(f"{'='*70}")
    
    # Cenário de teste
    match_data = create_test_match_data("t1_advantage", 22)
    odds_data = create_test_odds_data("t1_advantage")
    
    methods = [
        PredictionMethod.MACHINE_LEARNING,
        PredictionMethod.ALGORITHM_BASED,
        PredictionMethod.HYBRID
    ]
    
    for method in methods:
        print(f"\n🔧 Testando método: {method.value.upper()}")
        
        result = await prediction_system.predict_live_match(
            match_data, odds_data, method
        )
        
        print(f"   • Vencedor: {result.predicted_winner}")
        print(f"   • Probabilidade: {result.win_probability:.1%}")
        print(f"   • Confiança: {result.confidence_level.value}")
        print(f"   • Força da Predição: {result.prediction_strength:.1%}")
        print(f"   • Acordo entre Modelos: {result.model_agreement:.1%}")
        print(f"   • Tempo de Processamento: {result.processing_time_ms:.1f}ms")
        
        if result.ml_prediction:
            print(f"   • ML Score: {result.ml_prediction.get('confidence', 0):.1%}")
        if result.algorithm_prediction:
            print(f"   • Algorithm Score: {result.algorithm_prediction.get('confidence', 0):.1%}")


async def test_tip_generation(prediction_system: DynamicPredictionSystem):
    """Testa geração de tips profissionais"""
    print(f"\n{'='*70}")
    print("💰 TESTE: GERAÇÃO DE TIPS PROFISSIONAIS")
    print(f"{'='*70}")
    
    test_scenarios = [
        ("balanced_early", "Jogo equilibrado no early game"),
        ("t1_advantage", "T1 com vantagem clara"),
        ("geng_comeback", "Gen.G fazendo comeback"),
        ("high_value", "Cenário de alto value"),
        ("low_value", "Cenário de baixo value")
    ]
    
    for scenario, description in test_scenarios:
        print(f"\n🧪 Cenário: {description}")
        
        match_data = create_test_match_data(scenario.replace("_value", "_advantage"), 25)
        odds_data = create_test_odds_data(scenario)
        
        tip_result = await prediction_system.generate_professional_tip(
            match_data, odds_data
        )
        
        print(f"   📊 Validação:")
        print(f"   • Tip Válida: {'✅' if tip_result.is_valid else '❌'}")
        print(f"   • Confiança OK: {'✅' if tip_result.meets_confidence_threshold else '❌'}")
        print(f"   • EV OK: {'✅' if tip_result.meets_ev_threshold else '❌'}")
        print(f"   • Odds OK: {'✅' if tip_result.meets_odds_criteria else '❌'}")
        print(f"   • Timing OK: {'✅' if tip_result.meets_timing_criteria else '❌'}")
        
        if tip_result.is_valid and tip_result.tip:
            tip = tip_result.tip
            print(f"\n   🎯 TIP GERADA:")
            print(f"   • Aposta: {tip.tip_on_team}")
            print(f"   • Odds: {tip.odds}")
            print(f"   • Unidades: {tip.units} ({tip.risk_level})")
            print(f"   • Confiança: {tip.confidence_percentage:.1f}%")
            print(f"   • EV: +{tip.ev_percentage:.1f}%")
            print(f"   • Fonte: {tip.prediction_source}")
        else:
            print(f"   ❌ Motivo da Rejeição: {tip_result.rejection_reason}")


async def test_confidence_levels(prediction_system: DynamicPredictionSystem):
    """Testa diferentes níveis de confiança"""
    print(f"\n{'='*70}")
    print("📊 TESTE: NÍVEIS DE CONFIANÇA")
    print(f"{'='*70}")
    
    confidence_scenarios = [
        ("balanced_early", 10, "Low confidence - Early game"),
        ("t1_advantage", 22, "Medium-High confidence - Clear advantage"),
        ("geng_comeback", 35, "High confidence - Late game dominance")
    ]
    
    for scenario, time_min, description in confidence_scenarios:
        print(f"\n🎯 {description}")
        
        match_data = create_test_match_data(scenario, time_min)
        odds_data = create_test_odds_data(scenario)
        
        result = await prediction_system.predict_live_match(match_data, odds_data)
        
        print(f"   • Nível: {result.confidence_level.value.title()}")
        print(f"   • Score: {result.prediction_strength:.1%}")
        print(f"   • Qualidade dos Dados: {result.data_quality:.1%}")
        print(f"   • Vencedor: {result.predicted_winner}")
        print(f"   • Probabilidade: {result.win_probability:.1%}")


async def test_cache_system(prediction_system: DynamicPredictionSystem):
    """Testa sistema de cache"""
    print(f"\n{'='*70}")
    print("💾 TESTE: SISTEMA DE CACHE")
    print(f"{'='*70}")
    
    # Primeira predição (sem cache)
    match_data = create_test_match_data("t1_advantage", 20)
    odds_data = create_test_odds_data("t1_advantage")
    
    print("🔄 Primeira predição (cria cache)...")
    result1 = await prediction_system.predict_live_match(match_data, odds_data)
    print(f"   • Tempo: {result1.processing_time_ms:.1f}ms")
    print(f"   • Cache size: {len(prediction_system.predictions_cache)}")
    
    # Segunda predição (com cache)
    print("\n⚡ Segunda predição (usa cache)...")
    result2 = await prediction_system.predict_live_match(match_data, odds_data)
    print(f"   • Tempo: {result2.processing_time_ms:.1f}ms")
    print(f"   • Mesmo resultado: {'✅' if result1.match_id == result2.match_id else '❌'}")
    
    # Estatísticas do cache
    stats = prediction_system.get_prediction_stats()
    print(f"\n📈 Estatísticas:")
    print(f"   • Total de Predições: {stats['total_predictions']}")
    print(f"   • Predições ML: {stats['ml_predictions']}")
    print(f"   • Predições Híbridas: {stats['hybrid_predictions']}")
    print(f"   • Tips Geradas: {stats['tips_generated']}")
    print(f"   • Taxa de Sucesso: {stats['success_rate']:.1f}%")


async def test_edge_cases(prediction_system: DynamicPredictionSystem):
    """Testa casos extremos"""
    print(f"\n{'='*70}")
    print("⚠️ TESTE: CASOS EXTREMOS")
    print(f"{'='*70}")
    
    # Dados incompletos
    print("🧪 Teste 1: Dados incompletos")
    incomplete_match = MatchData(
        match_id="incomplete_test",
        team1_name="Team A",
        team2_name="Team B", 
        league="TEST",
        status="in_progress",
        game_time_seconds=0  # Sem tempo
    )
    
    try:
        result = await prediction_system.predict_live_match(incomplete_match, {})
        print(f"   • Resultado: {result.predicted_winner or 'N/A'}")
        print(f"   • Confiança: {result.confidence_level.value}")
    except Exception as e:
        print(f"   • Erro tratado: {e}")
    
    # Odds extremas
    print("\n🧪 Teste 2: Odds extremas")
    normal_match = create_test_match_data("t1_advantage", 20)
    extreme_odds = {"team1_odds": 1.01, "team2_odds": 50.0}  # Odds inválidas
    
    tip_result = await prediction_system.generate_professional_tip(
        normal_match, extreme_odds
    )
    print(f"   • Tip aceita: {'✅' if tip_result.is_valid else '❌'}")
    print(f"   • Motivo: {tip_result.rejection_reason or 'Aceita'}")
    
    # Jogo muito cedo
    print("\n🧪 Teste 3: Jogo muito cedo")
    early_match = create_test_match_data("balanced_early", 2)  # 2 minutos
    normal_odds = create_test_odds_data("balanced_early")
    
    tip_result = await prediction_system.generate_professional_tip(
        early_match, normal_odds
    )
    print(f"   • Tip aceita: {'✅' if tip_result.is_valid else '❌'}")
    print(f"   • Timing OK: {'✅' if tip_result.meets_timing_criteria else '❌'}")


async def demonstrate_full_workflow(prediction_system: DynamicPredictionSystem):
    """Demonstra workflow completo do sistema"""
    print(f"\n{'='*70}")
    print("🚀 DEMONSTRAÇÃO: WORKFLOW COMPLETO")
    print(f"{'='*70}")
    
    # Simula partida real
    match_data = MatchData(
        match_id="lck_t1_vs_geng_game1",
        team1_name="T1",
        team2_name="Gen.G",
        league="LCK",
        tournament="LCK Summer 2024 Finals",
        status="in_progress",
        game_time_seconds=1320  # 22 minutos
    )
    
    match_data.team1_stats = TeamStats(
        total_gold=32500, total_kills=7, total_cs=165,
        towers_destroyed=3, dragons_taken=2, barons_taken=1,
        heralds_taken=1, wards_placed=42, wards_destroyed=18
    )
    
    match_data.team2_stats = TeamStats(
        total_gold=28200, total_kills=4, total_cs=148,
        towers_destroyed=1, dragons_taken=1, barons_taken=0,
        heralds_taken=0, wards_placed=35, wards_destroyed=12
    )
    
    match_data.draft_data = DraftData(
        team1_picks=["azir", "graves", "gnar", "jinx", "thresh"],
        team2_picks=["viktor", "lee", "camille", "caitlyn", "nautilus"]
    )
    
    match_data.events = [
        GameEvent("DRAGON", "T1", 6*60),
        GameEvent("HERALD", "T1", 8*60),
        GameEvent("TEAMFIGHT_WIN", "T1", 15*60),
        GameEvent("BARON_NASHOR", "T1", 20*60),
        GameEvent("DRAGON", "T1", 22*60)
    ]
    
    # Odds das casas
    odds_data = {"team1_odds": 1.52, "team2_odds": 2.48}
    
    print("📊 Dados da Partida:")
    print(f"   • {match_data.team1_name} vs {match_data.team2_name}")
    print(f"   • Liga: {match_data.league}")
    print(f"   • Tempo: {match_data.get_game_time_minutes()}min")
    print(f"   • Gold: {match_data.team1_stats.total_gold} vs {match_data.team2_stats.total_gold}")
    print(f"   • Kills: {match_data.team1_stats.total_kills} vs {match_data.team2_stats.total_kills}")
    print(f"   • Odds: {odds_data['team1_odds']} vs {odds_data['team2_odds']}")
    
    # Executa predição
    print(f"\n🧠 Executando predição híbrida...")
    prediction_result = await prediction_system.predict_live_match(
        match_data, odds_data, PredictionMethod.HYBRID
    )
    
    print(f"   ✅ Predição concluída em {prediction_result.processing_time_ms:.1f}ms")
    
    # Gera tip profissional
    print(f"\n💰 Gerando tip profissional...")
    tip_result = await prediction_system.generate_professional_tip(
        match_data, odds_data, prediction_result
    )
    
    if tip_result.is_valid and tip_result.tip:
        tip = tip_result.tip
        print(f"\n🎯 TIP PROFISSIONAL GERADA:")
        print(f"{'='*50}")
        print(tip.format_telegram_message())
        print(f"{'='*50}")
    else:
        print(f"\n❌ Tip rejeitada: {tip_result.rejection_reason}")


async def main():
    """Função principal de teste"""
    print("🚀 Iniciando testes do Sistema de Predição Dinâmico...")
    print(f"🔧 Python: {sys.version}")
    print(f"📁 Diretório: {os.getcwd()}")
    
    # Inicializa componentes
    print("\n🔧 Inicializando componentes...")
    game_analyzer = LoLGameAnalyzer()
    units_system = ProfessionalUnitsSystem()
    prediction_system = DynamicPredictionSystem(game_analyzer, units_system)
    
    print("✅ Componentes inicializados:")
    print(f"   • Game Analyzer: {len(game_analyzer.champion_win_rates)} campeões")
    print(f"   • Units System: {len(UNITS_CONFIG)} níveis de risco")
    print(f"   • Prediction System: {prediction_system.ml_config['model_version']}")
    
    # Executa testes
    test_functions = [
        test_prediction_methods,
        test_confidence_levels, 
        test_tip_generation,
        test_cache_system,
        test_edge_cases,
        demonstrate_full_workflow
    ]
    
    for test_func in test_functions:
        try:
            await test_func(prediction_system)
        except Exception as e:
            print(f"\n❌ Erro no teste {test_func.__name__}: {e}")
    
    # Estatísticas finais
    print(f"\n{'='*70}")
    print("📈 ESTATÍSTICAS FINAIS")
    print(f"{'='*70}")
    
    stats = prediction_system.get_prediction_stats()
    print(f"Total de Predições: {stats['total_predictions']}")
    print(f"Tips Geradas: {stats['tips_generated']}")
    print(f"Tips Rejeitadas: {stats['tips_rejected']}")
    print(f"Taxa de Sucesso: {stats['success_rate']:.1f}%")
    print(f"Cache Size: {stats['cache_size']}")
    
    print(f"\n🎉 TODOS OS TESTES CONCLUÍDOS!")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n🛑 Teste interrompido pelo usuário")
    except Exception as e:
        print(f"\n\n❌ Erro fatal durante os testes: {e}")
        sys.exit(1) 