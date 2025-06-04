#!/usr/bin/env python3
"""
Teste do Analisador de Jogos LoL - Bot LoL V3 Ultra Avançado

Script para testar a análise de partidas em diferentes cenários.
"""

import os
import sys
from typing import List, Dict, Any

# Adiciona o diretório atual ao path para importar módulos
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from bot.core_logic import LoLGameAnalyzer, GamePhase, TeamAdvantage
from bot.data_models.match_data import MatchData, TeamStats, GameEvent, DraftData
from bot.utils.logger_config import setup_logging, get_logger

# Configuração de logging para testes
logger = setup_logging(log_level="INFO", log_file=None)
test_logger = get_logger("test_analyzer")


def create_sample_match_data(scenario_name: str, game_time_minutes: int = 20) -> MatchData:
    """Cria dados de partida para teste"""
    
    # Dados base
    match_data = MatchData(
        match_id=f"test_{scenario_name}_{game_time_minutes}min",
        team1_name="Team Liquid",
        team2_name="Dignitas",
        league="LCS",
        game_time_seconds=game_time_minutes * 60,
        status="in_progress"
    )
    
    # Cenários específicos
    if scenario_name == "early_game_even":
        # Early game balanceado
        match_data.team1_stats = TeamStats(
            total_gold=15000,
            total_kills=3,
            total_cs=120,
            towers_destroyed=0,
            dragons_taken=1,
            barons_taken=0,
            heralds_taken=1,
            wards_placed=25,
            wards_destroyed=8
        )
        match_data.team2_stats = TeamStats(
            total_gold=14500,
            total_kills=2,
            total_cs=115,
            towers_destroyed=1,
            dragons_taken=0,
            barons_taken=0,
            heralds_taken=0,
            wards_placed=22,
            wards_destroyed=6
        )
        match_data.events = [
            GameEvent("KILL", "Team Liquid", 5 * 60),
            GameEvent("DRAGON", "Team Liquid", 8 * 60),
            GameEvent("TOWER_DESTROYED", "Dignitas", 12 * 60),
            GameEvent("HERALD", "Team Liquid", 15 * 60)
        ]
    
    elif scenario_name == "mid_game_advantage":
        # Mid game com vantagem clara
        match_data.team1_stats = TeamStats(
            total_gold=35000,
            total_kills=8,
            total_cs=180,
            towers_destroyed=3,
            dragons_taken=2,
            barons_taken=1,
            heralds_taken=1,
            wards_placed=45,
            wards_destroyed=18
        )
        match_data.team2_stats = TeamStats(
            total_gold=28000,
            total_kills=4,
            total_cs=165,
            towers_destroyed=1,
            dragons_taken=1,
            barons_taken=0,
            heralds_taken=0,
            wards_placed=38,
            wards_destroyed=12
        )
        match_data.events = [
            GameEvent("DRAGON", "Team Liquid", 8 * 60),
            GameEvent("TEAMFIGHT_WIN", "Team Liquid", 15 * 60),
            GameEvent("BARON_NASHOR", "Team Liquid", 20 * 60),
            GameEvent("TOWER_DESTROYED", "Team Liquid", 22 * 60),
            GameEvent("DRAGON", "Team Liquid", 24 * 60)
        ]
    
    elif scenario_name == "late_game_close":
        # Late game equilibrado
        match_data.team1_stats = TeamStats(
            total_gold=52000,
            total_kills=12,
            total_cs=285,
            towers_destroyed=6,
            dragons_taken=3,
            barons_taken=2,
            heralds_taken=1,
            wards_placed=75,
            wards_destroyed=35
        )
        match_data.team2_stats = TeamStats(
            total_gold=50000,
            total_kills=11,
            total_cs=280,
            towers_destroyed=5,
            dragons_taken=2,
            barons_taken=1,
            heralds_taken=1,
            wards_placed=70,
            wards_destroyed=32
        )
        match_data.events = [
            GameEvent("BARON_NASHOR", "Team Liquid", 25 * 60),
            GameEvent("DRAGON_SOUL", "Team Liquid", 30 * 60),
            GameEvent("ACE", "Dignitas", 35 * 60),
            GameEvent("BARON_NASHOR", "Dignitas", 37 * 60),
            GameEvent("INHIBITOR_DESTROYED", "Team Liquid", 40 * 60)
        ]
    
    elif scenario_name == "stomp":
        # Partida dominada
        match_data.team1_stats = TeamStats(
            total_gold=22000,
            total_kills=15,
            total_cs=150,
            towers_destroyed=6,
            dragons_taken=3,
            barons_taken=1,
            heralds_taken=2,
            wards_placed=35,
            wards_destroyed=20
        )
        match_data.team2_stats = TeamStats(
            total_gold=12000,
            total_kills=2,
            total_cs=105,
            towers_destroyed=0,
            dragons_taken=0,
            barons_taken=0,
            heralds_taken=0,
            wards_placed=18,
            wards_destroyed=5
        )
        match_data.events = [
            GameEvent("ACE", "Team Liquid", 8 * 60),
            GameEvent("DRAGON", "Team Liquid", 10 * 60),
            GameEvent("HERALD", "Team Liquid", 12 * 60),
            GameEvent("BARON_NASHOR", "Team Liquid", 18 * 60),
            GameEvent("ACE", "Team Liquid", 20 * 60)
        ]
    
    # Draft data para todos os cenários
    match_data.draft_data = DraftData(
        team1_picks=["jinx", "thresh", "azir", "graves", "gnar"],
        team2_picks=["caitlyn", "nautilus", "orianna", "lee", "malphite"],
        team1_bans=["yasuo", "zed", "katarina"],
        team2_bans=["vayne", "lux", "jax"]
    )
    
    return match_data


async def test_scenario(analyzer: LoLGameAnalyzer, scenario_name: str, game_time_minutes: int = 20) -> None:
    """Testa um cenário específico"""
    print(f"\n{'='*70}")
    print(f"🧪 TESTE: {scenario_name.upper().replace('_', ' ')} ({game_time_minutes}min)")
    print(f"{'='*70}")
    
    # Cria dados da partida
    match_data = create_sample_match_data(scenario_name, game_time_minutes)
    
    print(f"📊 Dados da Partida:")
    print(f"   • {match_data.team1_name} vs {match_data.team2_name}")
    print(f"   • Liga: {match_data.league}")
    print(f"   • Tempo: {game_time_minutes}min")
    print(f"   • Status: {match_data.status}")
    
    print(f"\n📈 Estatísticas:")
    print(f"   Team Liquid: {match_data.team1_stats.total_gold} gold, {match_data.team1_stats.total_kills} kills")
    print(f"   Dignitas: {match_data.team2_stats.total_gold} gold, {match_data.team2_stats.total_kills} kills")
    print(f"   Eventos: {len(match_data.events)} registrados")
    
    # Executa análise
    analysis = await analyzer.analyze_live_match(match_data)
    
    # Mostra resultados
    print(f"\n✅ ANÁLISE CONCLUÍDA:")
    print(f"   • Fase do Jogo: {analysis.current_phase.value}")
    print(f"   • Vencedor Previsto: {analysis.predicted_winner}")
    print(f"   • Probabilidade: {analysis.win_probability:.1%}")
    print(f"   • Confiança: {analysis.confidence_score:.1%}")
    print(f"   • Momentum: {analysis.momentum_team or 'Neutro'}")
    print(f"   • Eventos Cruciais: {analysis.crucial_events_count}")
    
    print(f"\n🎯 Vantagens Team Liquid:")
    team1_adv = analysis.team1_advantage
    print(f"   • Ouro: {team1_adv.gold_advantage:+.0f}")
    print(f"   • Torres: {team1_adv.tower_advantage:+d}")
    print(f"   • Dragões: {team1_adv.dragon_advantage:+d}")
    print(f"   • Barons: {team1_adv.baron_advantage:+d}")
    print(f"   • Kills: {team1_adv.kill_advantage:+d}")
    print(f"   • Controle Objetivos: {team1_adv.objective_control:.1%}")
    print(f"   • Score Geral: {team1_adv.overall_advantage:+.1%}")
    
    print(f"\n📝 Resumo da Análise:")
    summary = analyzer.get_analysis_summary(analysis)
    print(summary)


async def test_draft_analysis(analyzer: LoLGameAnalyzer) -> None:
    """Testa análise de draft especificamente"""
    print(f"\n{'='*70}")
    print("🎮 TESTE: ANÁLISE DE DRAFT")
    print(f"{'='*70}")
    
    draft_scenarios = [
        {
            "name": "Draft Balanceado",
            "team1": ["jinx", "thresh", "azir", "graves", "gnar"],
            "team2": ["caitlyn", "nautilus", "orianna", "lee", "malphite"]
        },
        {
            "name": "Comp de Dive vs Protect",
            "team1": ["yasuo", "alistar", "zed", "lee", "malphite"],  # Dive
            "team2": ["jinx", "lulu", "orianna", "graves", "maokai"]  # Protect
        },
        {
            "name": "Meta vs Off-meta",
            "team1": ["jinx", "thresh", "azir", "graves", "gnar"],  # Meta
            "team2": ["vayne", "soraka", "yasuo", "master_yi", "fiora"]  # Off-meta
        }
    ]
    
    for scenario in draft_scenarios:
        print(f"\n🧪 Testando: {scenario['name']}")
        
        draft_data = DraftData(
            team1_picks=scenario["team1"],
            team2_picks=scenario["team2"],
            team1_bans=["yasuo", "zed", "katarina"],
            team2_bans=["vayne", "lux", "jax"]
        )
        
        # Cria dados mínimos para teste
        match_data = MatchData(
            match_id=f"draft_test_{scenario['name'].lower().replace(' ', '_')}",
            team1_name="Team A",
            team2_name="Team B",
            league="TEST",
            game_time_seconds=5 * 60,  # 5 minutos
            status="in_progress"
        )
        
        match_data.team1_stats = TeamStats(total_gold=5000, total_kills=0, total_cs=30)
        match_data.team2_stats = TeamStats(total_gold=5000, total_kills=0, total_cs=30)
        match_data.draft_data = draft_data
        match_data.events = []
        
        analysis = await analyzer.analyze_live_match(match_data)
        
        print(f"   Team A: {scenario['team1']}")
        print(f"   Team B: {scenario['team2']}")
        print(f"   Vantagem de Draft Team A: {analysis.team1_advantage.draft_advantage:+.1%}")
        print(f"   Vencedor Previsto: {analysis.predicted_winner}")


async def test_game_phases(analyzer: LoLGameAnalyzer) -> None:
    """Testa análise em diferentes fases do jogo"""
    print(f"\n{'='*70}")
    print("⏰ TESTE: FASES DO JOGO")
    print(f"{'='*70}")
    
    phases = [
        {"time": 8, "phase": "Early Game", "scenario": "early_game_even"},
        {"time": 22, "phase": "Mid Game", "scenario": "mid_game_advantage"},
        {"time": 40, "phase": "Late Game", "scenario": "late_game_close"}
    ]
    
    for phase_data in phases:
        await test_scenario(analyzer, phase_data["scenario"], phase_data["time"])


async def test_momentum_calculation(analyzer: LoLGameAnalyzer) -> None:
    """Testa cálculo de momentum"""
    print(f"\n{'='*70}")
    print("⚡ TESTE: CÁLCULO DE MOMENTUM")
    print(f"{'='*70}")
    
    # Cenário com momentum para Team Liquid
    match_data = create_sample_match_data("momentum_test", 25)
    
    # Adiciona eventos recentes favoráveis ao Team Liquid
    recent_events = [
        GameEvent("TEAMFIGHT_WIN", "Team Liquid", 23 * 60),
        GameEvent("BARON_NASHOR", "Team Liquid", 24 * 60),
        GameEvent("TOWER_DESTROYED", "Team Liquid", 24.5 * 60),
        GameEvent("DRAGON", "Team Liquid", 25 * 60)
    ]
    
    match_data.events.extend(recent_events)
    
    analysis = await analyzer.analyze_live_match(match_data)
    
    print(f"📊 Eventos Recentes (últimos 5min):")
    for event in recent_events:
        minutes = event.timestamp // 60
        print(f"   • {event.event_type} por {event.team} aos {minutes:.0f}min")
    
    print(f"\n⚡ Resultado do Momentum:")
    print(f"   • Time com Momentum: {analysis.momentum_team or 'Nenhum'}")
    print(f"   • Confiança da Análise: {analysis.confidence_score:.1%}")


async def main():
    """Função principal de teste"""
    print("🚀 Iniciando testes do Analisador de Jogos LoL...")
    print(f"🔧 Python: {sys.version}")
    print(f"📁 Diretório: {os.getcwd()}")
    
    # Inicializa analisador
    analyzer = LoLGameAnalyzer()
    
    print(f"\n🧠 Analisador inicializado com:")
    print(f"   • {len(analyzer.champion_win_rates)} campeões no database")
    print(f"   • Cache de análises: {len(analyzer.match_analyses_cache)} entradas")
    
    # Executa testes de cenários principais
    scenarios = [
        ("early_game_even", 12),
        ("mid_game_advantage", 25),
        ("late_game_close", 42),
        ("stomp", 18)
    ]
    
    for scenario, time_min in scenarios:
        await test_scenario(analyzer, scenario, time_min)
    
    # Testa análise de draft
    await test_draft_analysis(analyzer)
    
    # Testa fases do jogo
    await test_game_phases(analyzer)
    
    # Testa cálculo de momentum
    await test_momentum_calculation(analyzer)
    
    # Teste de cache
    print(f"\n{'='*70}")
    print("💾 TESTE: SISTEMA DE CACHE")
    print(f"{'='*70}")
    
    print(f"Cache após testes: {len(analyzer.match_analyses_cache)} análises")
    
    # Recupera uma análise do cache
    cache_test_id = "test_early_game_even_12min"
    cached_analysis = analyzer.get_match_analysis(cache_test_id)
    
    if cached_analysis:
        print(f"✅ Análise recuperada do cache: {cache_test_id}")
        print(f"   Timestamp: {cached_analysis.analysis_timestamp}")
        print(f"   Vencedor: {cached_analysis.predicted_winner}")
    else:
        print(f"❌ Análise não encontrada no cache: {cache_test_id}")
    
    # Limpa cache antigo
    analyzer.clear_old_analyses(max_age_hours=0)  # Remove todas para teste
    print(f"Cache após limpeza: {len(analyzer.match_analyses_cache)} análises")
    
    print(f"\n{'='*70}")
    print("🎉 TODOS OS TESTES CONCLUÍDOS!")
    print(f"{'='*70}")


if __name__ == "__main__":
    try:
        import asyncio
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n🛑 Teste interrompido pelo usuário")
    except Exception as e:
        print(f"\n\n❌ Erro fatal durante os testes: {e}")
        sys.exit(1) 
