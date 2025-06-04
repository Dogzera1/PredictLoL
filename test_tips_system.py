#!/usr/bin/env python3
"""
Teste do Sistema Profissional de Tips - Bot LoL V3 Ultra Avançado

Script para testar o motor principal de monitoramento e geração automática de tips.
"""

import os
import sys
import asyncio
from typing import Dict, Any

# Adiciona o diretório atual ao path para importar módulos
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from bot.systems import (
    ProfessionalTipsSystem,
    TipStatus,
    GeneratedTip,
    MonitoringStats
)
from bot.core_logic import (
    LoLGameAnalyzer,
    ProfessionalUnitsSystem, 
    DynamicPredictionSystem
)
from bot.api_clients import (
    PandaScoreAPIClient,
    RiotAPIClient
)
from bot.data_models.match_data import MatchData, TeamStats, GameEvent, DraftData
from bot.utils.logger_config import setup_logging, get_logger
from bot.utils.constants import PANDASCORE_API_KEY, RIOT_API_KEY

# Configuração de logging
logger = setup_logging(log_level="INFO", log_file=None)
test_logger = get_logger("test_tips_system")


class MockPandaScoreClient:
    """Cliente mock do PandaScore para testes"""
    
    def __init__(self):
        self.mock_live_matches = []
        self.mock_odds = {"team1_odds": 1.75, "team2_odds": 2.10}
    
    async def get_live_matches(self):
        """Retorna partidas mock"""
        return self.mock_live_matches.copy()
    
    async def get_match_odds(self, match_id: str):
        """Retorna odds mock"""
        return self.mock_odds.copy()
    
    def set_mock_matches(self, matches):
        """Define partidas mock"""
        self.mock_live_matches = matches
    
    def set_mock_odds(self, odds):
        """Define odds mock"""
        self.mock_odds = odds


class MockRiotClient:
    """Cliente mock da Riot API para testes"""
    
    async def get_live_matches(self):
        """Retorna lista vazia para testes"""
        return []


def create_mock_match(
    match_id: str,
    team1: str = "T1",
    team2: str = "Gen.G", 
    league: str = "LCK",
    game_time_minutes: int = 20,
    scenario: str = "balanced"
) -> MatchData:
    """Cria partida mock para testes"""
    
    match = MatchData(
        match_id=match_id,
        team1_name=team1,
        team2_name=team2,
        league=league,
        tournament=f"{league} Summer 2024",
        status="in_progress",
        game_time_seconds=game_time_minutes * 60
    )
    
    if scenario == "balanced":
        match.team1_stats = TeamStats(
            total_gold=15000, total_kills=5, total_cs=120,
            towers_destroyed=2, dragons_taken=1, barons_taken=0,
            heralds_taken=1, wards_placed=25, wards_destroyed=8
        )
        match.team2_stats = TeamStats(
            total_gold=14500, total_kills=4, total_cs=115,
            towers_destroyed=1, dragons_taken=1, barons_taken=0,
            heralds_taken=0, wards_placed=22, wards_destroyed=6
        )
    elif scenario == "advantage":
        match.team1_stats = TeamStats(
            total_gold=25000, total_kills=8, total_cs=160,
            towers_destroyed=4, dragons_taken=3, barons_taken=1,
            heralds_taken=1, wards_placed=40, wards_destroyed=15
        )
        match.team2_stats = TeamStats(
            total_gold=18000, total_kills=3, total_cs=140,
            towers_destroyed=1, dragons_taken=0, barons_taken=0,
            heralds_taken=0, wards_placed=25, wards_destroyed=8
        )
    
    # Eventos mock
    match.events = [
        GameEvent("DRAGON", team1, 6*60),
        GameEvent("TOWER_DESTROYED", team1, 8*60),
        GameEvent("HERALD", team1, 12*60),
        GameEvent("TEAMFIGHT_WIN", team1, 15*60)
    ]
    
    # Draft mock
    match.draft_data = DraftData(
        team1_picks=["azir", "graves", "gnar", "jinx", "thresh"],
        team2_picks=["viktor", "lee", "camille", "caitlyn", "nautilus"],
        team1_bans=["yasuo", "zed", "akali"],
        team2_bans=["leblanc", "syndra", "orianna"]
    )
    
    return match


async def test_system_initialization():
    """Testa inicialização do sistema"""
    print(f"\n{'='*70}")
    print("🔧 TESTE: INICIALIZAÇÃO DO SISTEMA")
    print(f"{'='*70}")
    
    # Cria componentes
    pandascore_client = MockPandaScoreClient()
    riot_client = MockRiotClient()
    game_analyzer = LoLGameAnalyzer()
    units_system = ProfessionalUnitsSystem()
    prediction_system = DynamicPredictionSystem(game_analyzer, units_system)
    
    # Inicializa sistema de tips
    tips_system = ProfessionalTipsSystem(
        pandascore_client=pandascore_client,
        riot_client=riot_client,
        prediction_system=prediction_system
    )
    
    print("✅ Componentes inicializados:")
    print(f"   • PandaScore Client: Mock configurado")
    print(f"   • Riot Client: Mock configurado")
    print(f"   • Game Analyzer: {len(game_analyzer.champion_win_rates)} campeões")
    print(f"   • Units System: R${units_system.bankroll:.2f} bankroll")
    print(f"   • Prediction System: {prediction_system.ml_config['model_version']}")
    print(f"   • Tips System: {tips_system.max_tips_per_hour} tips/hora máx")
    
    return tips_system, pandascore_client


async def test_match_filtering(tips_system: ProfessionalTipsSystem, mock_client: MockPandaScoreClient):
    """Testa filtros de qualidade de partidas"""
    print(f"\n{'='*70}")
    print("🔍 TESTE: FILTROS DE QUALIDADE")
    print(f"{'='*70}")
    
    # Cria diferentes tipos de partidas
    test_matches = [
        create_mock_match("valid_lck", "T1", "Gen.G", "LCK", 20, "balanced"),
        create_mock_match("invalid_league", "TeamA", "TeamB", "UNKNOWN", 20, "balanced"),
        create_mock_match("too_early", "SKT", "KT", "LCK", 3, "balanced"),
        create_mock_match("too_late", "DRX", "DK", "LCK", 50, "balanced"),
        create_mock_match("valid_lec", "G2", "FNC", "LEC", 25, "advantage"),
    ]
    
    # Remove eventos para simular baixa qualidade
    test_matches[1].events = []  # Sem eventos cruciais
    
    mock_client.set_mock_matches(test_matches)
    
    # Busca e filtra partidas
    live_matches = await tips_system._get_live_matches()
    suitable_matches = tips_system._filter_suitable_matches(live_matches)
    
    print(f"📊 Resultado da Filtragem:")
    print(f"   • Partidas encontradas: {len(live_matches)}")
    print(f"   • Partidas adequadas: {len(suitable_matches)}")
    
    print(f"\n🔍 Análise Individual:")
    for match in live_matches:
        meets_criteria = tips_system._match_meets_quality_criteria(match)
        game_time = match.get_game_time_minutes()
        data_quality = match.calculate_data_quality()
        
        print(f"   • {match.team1_name} vs {match.team2_name} ({match.league}):")
        print(f"     - Tempo: {game_time}min")
        print(f"     - Qualidade: {data_quality:.1%}")
        print(f"     - Eventos: {len(match.events)}")
        print(f"     - Válida: {'✅' if meets_criteria else '❌'}")
    
    return suitable_matches


async def test_tip_generation(tips_system: ProfessionalTipsSystem, mock_client: MockPandaScoreClient):
    """Testa geração de tips"""
    print(f"\n{'='*70}")
    print("💰 TESTE: GERAÇÃO DE TIPS")
    print(f"{'='*70}")
    
    # Cria partida com vantagem clara para T1
    advantage_match = create_mock_match(
        "tip_test_match", "T1", "Gen.G", "LCK", 22, "advantage"
    )
    
    # Define odds favoráveis
    mock_client.set_mock_odds({"team1_odds": 1.65, "team2_odds": 2.25})
    
    print(f"🎮 Partida de Teste:")
    print(f"   • {advantage_match.team1_name} vs {advantage_match.team2_name}")
    print(f"   • Liga: {advantage_match.league}")
    print(f"   • Tempo: {advantage_match.get_game_time_minutes()}min")
    print(f"   • Gold: {advantage_match.team1_stats.total_gold} vs {advantage_match.team2_stats.total_gold}")
    print(f"   • Odds: {mock_client.mock_odds['team1_odds']} vs {mock_client.mock_odds['team2_odds']}")
    
    # Gera tip
    print(f"\n🧠 Gerando tip...")
    generated_tip = await tips_system._generate_tip_for_match(advantage_match)
    
    if generated_tip:
        print(f"✅ Tip gerada com sucesso:")
        print(f"   • Equipe: {generated_tip.tip_on_team}")
        print(f"   • Odds: {generated_tip.odds}")
        print(f"   • Unidades: {generated_tip.units}")
        print(f"   • Confiança: {generated_tip.confidence_percentage:.1f}%")
        print(f"   • EV: +{generated_tip.ev_percentage:.1f}%")
        print(f"   • Risco: {generated_tip.risk_level}")
        print(f"   • Fonte: {generated_tip.prediction_source}")
        
        # Processa a tip
        await tips_system._handle_generated_tip(generated_tip, advantage_match)
        print(f"✅ Tip processada e armazenada no sistema")
        
        return generated_tip
    else:
        print(f"❌ Nenhuma tip foi gerada")
        return None


async def test_rate_limiting(tips_system: ProfessionalTipsSystem):
    """Testa sistema de rate limiting"""
    print(f"\n{'='*70}")
    print("⚡ TESTE: RATE LIMITING")
    print(f"{'='*70}")
    
    # Simula várias tips em sequência
    print(f"📊 Limite atual: {tips_system.max_tips_per_hour} tips/hora")
    print(f"📊 Tips recentes: {len(tips_system.last_tip_times)}")
    
    initial_can_generate = tips_system._can_generate_tip()
    print(f"   • Pode gerar tip: {'✅' if initial_can_generate else '❌'}")
    
    # Simula atingir o limite
    import time
    current_time = time.time()
    
    # Adiciona tips no limite
    for i in range(tips_system.max_tips_per_hour):
        tips_system.last_tip_times.append(current_time - (i * 60))  # 1 por minuto
    
    can_generate_after_limit = tips_system._can_generate_tip()
    print(f"   • Após {tips_system.max_tips_per_hour} tips: {'✅' if can_generate_after_limit else '❌'}")
    
    # Testa limpeza de tips antigas
    tips_system.last_tip_times = [current_time - 3700]  # Tip de 1 hora atrás
    can_generate_after_cleanup = tips_system._can_generate_tip()
    print(f"   • Após limpeza: {'✅' if can_generate_after_cleanup else '❌'}")


async def test_monitoring_status(tips_system: ProfessionalTipsSystem):
    """Testa relatório de status"""
    print(f"\n{'='*70}")
    print("📊 TESTE: STATUS DE MONITORAMENTO")
    print(f"{'='*70}")
    
    # Simula algumas estatísticas
    tips_system.stats.matches_scanned = 15
    tips_system.stats.tips_generated = 3
    tips_system.stats.tips_sent = 2
    tips_system.stats.tips_expired = 1
    
    # Obtém status
    status = tips_system.get_monitoring_status()
    
    print(f"🔧 Estado do Sistema:")
    print(f"   • Monitorando: {'✅' if status['is_monitoring'] else '❌'}")
    print(f"   • Uptime: {status['uptime_hours']:.2f} horas")
    
    print(f"\n📈 Estatísticas:")
    stats = status['statistics']
    print(f"   • Partidas scaneadas: {stats['matches_scanned']}")
    print(f"   • Tips geradas: {stats['tips_generated']}")
    print(f"   • Tips enviadas: {stats['tips_sent']}")
    print(f"   • Tips expiradas: {stats['tips_expired']}")
    print(f"   • Taxa de sucesso: {stats['success_rate']:.1f}%")
    
    print(f"\n🎯 Estado Atual:")
    current_state = status['current_state']
    print(f"   • Partidas monitoradas: {current_state['monitored_matches']}")
    print(f"   • Tips ativas: {current_state['active_tips']}")
    
    print(f"\n⚡ Rate Limiting:")
    rate_limit = status['rate_limiting']
    print(f"   • Tips recentes: {rate_limit['recent_tips']}/{rate_limit['max_per_hour']}")
    print(f"   • Pode gerar: {'✅' if rate_limit['can_generate'] else '❌'}")


async def test_force_scan(tips_system: ProfessionalTipsSystem, mock_client: MockPandaScoreClient):
    """Testa scan manual"""
    print(f"\n{'='*70}")
    print("🔍 TESTE: SCAN MANUAL")
    print(f"{'='*70}")
    
    # Prepara dados mock
    test_match = create_mock_match("force_scan_test", "DK", "T1", "LCK", 18, "advantage")
    mock_client.set_mock_matches([test_match])
    mock_client.set_mock_odds({"team1_odds": 2.10, "team2_odds": 1.72})
    
    print("🔄 Executando scan forçado...")
    
    result = await tips_system.force_scan()
    
    print(f"📊 Resultado do Scan:")
    print(f"   • Duração: {result['scan_duration_seconds']}s")
    print(f"   • Partidas encontradas: {result['live_matches_found']}")
    print(f"   • Partidas adequadas: {result['suitable_matches']}")
    print(f"   • Tip gerada: {'✅' if result['tip_generated'] else '❌'}")
    print(f"   • Pode gerar mais: {'✅' if result['can_generate_more'] else '❌'}")
    print(f"   • Timestamp: {result['timestamp']}")


async def test_tips_expiration(tips_system: ProfessionalTipsSystem):
    """Testa expiração de tips"""
    print(f"\n{'='*70}")
    print("⏰ TESTE: EXPIRAÇÃO DE TIPS")
    print(f"{'='*70}")
    
    import time
    from bot.data_models.tip_data import ProfessionalTip
    
    # Cria tip mock expirada
    expired_tip_data = ProfessionalTip(
        match_id="expired_test",
        team_a="TeamA",
        team_b="TeamB",
        league="LCK",
        tournament="Test Tournament",
        tip_on_team="TeamA",
        odds=1.85,
        units=2.0,
        risk_level="Risco Médio",
        confidence_percentage=75.0,
        ev_percentage=8.5,
        analysis_reasoning="Teste de expiração",
        game_time_at_tip="15min",
        game_time_seconds=900,
        prediction_source="TEST"
    )
    
    # Cria tip com tempo expirado
    expired_generated_tip = GeneratedTip(
        tip=expired_tip_data,
        match_data=create_mock_match("expired_match"),
        status=TipStatus.SENT,
        generated_at=time.time() - 1800,  # 30 minutos atrás
        sent_at=time.time() - 1800
    )
    
    # Adiciona ao sistema
    tips_system.generated_tips["expired_test"] = expired_generated_tip
    
    print(f"🧪 Estado antes da limpeza:")
    print(f"   • Tips ativas: {len(tips_system.generated_tips)}")
    print(f"   • Tip expirada: {'✅' if expired_generated_tip.is_expired else '❌'}")
    
    # Executa limpeza
    tips_system._cleanup_expired_tips()
    
    print(f"\n🧹 Estado após limpeza:")
    print(f"   • Tips ativas: {len(tips_system.generated_tips)}")
    print(f"   • Tips expiradas: {tips_system.stats.tips_expired}")


async def demonstrate_full_workflow(tips_system: ProfessionalTipsSystem, mock_client: MockPandaScoreClient):
    """Demonstra workflow completo"""
    print(f"\n{'='*70}")
    print("🚀 DEMONSTRAÇÃO: WORKFLOW COMPLETO")
    print(f"{'='*70}")
    
    # Prepara cenário realista
    lck_matches = [
        create_mock_match("lck_game1", "T1", "Gen.G", "LCK", 23, "advantage"),
        create_mock_match("lck_game2", "DK", "KT", "LCK", 18, "balanced"),
    ]
    
    lec_match = create_mock_match("lec_game1", "G2", "FNC", "LEC", 28, "advantage")
    
    # Adiciona partida com liga não suportada (será filtrada)
    invalid_match = create_mock_match("invalid_game", "TeamA", "TeamB", "MINOR_LEAGUE", 20, "balanced")
    
    all_matches = lck_matches + [lec_match, invalid_match]
    
    mock_client.set_mock_matches(all_matches)
    mock_client.set_mock_odds({"team1_odds": 1.55, "team2_odds": 2.45})
    
    print(f"🎮 Cenário de Teste:")
    print(f"   • Total de partidas: {len(all_matches)}")
    print(f"   • LCK: {len(lck_matches)} partidas")
    print(f"   • LEC: 1 partida")
    print(f"   • Liga menor: 1 partida (será filtrada)")
    
    # Simula ciclo completo de monitoramento
    print(f"\n🔄 Executando ciclo de monitoramento...")
    
    # 1. Busca partidas
    live_matches = await tips_system._get_live_matches()
    print(f"   • Partidas encontradas: {len(live_matches)}")
    
    # 2. Filtra partidas
    suitable_matches = tips_system._filter_suitable_matches(live_matches)
    print(f"   • Partidas adequadas: {len(suitable_matches)}")
    
    # 3. Atualiza cache
    tips_system._update_monitored_matches(suitable_matches)
    print(f"   • Cache atualizado: {len(tips_system.monitored_matches)} partidas")
    
    # 4. Processa tips
    if suitable_matches:
        await tips_system._process_matches_for_tips(suitable_matches)
    
    # 5. Resultado final
    print(f"\n📈 Resultado Final:")
    print(f"   • Tips geradas: {tips_system.stats.tips_generated}")
    print(f"   • Tips enviadas: {tips_system.stats.tips_sent}")
    print(f"   • Taxa de sucesso: {(tips_system.stats.tips_sent / max(tips_system.stats.tips_generated, 1)) * 100:.1f}%")
    
    # 6. Mostra tips recentes
    recent_tips = tips_system.get_recent_tips(5)
    if recent_tips:
        print(f"\n🎯 Tips Recentes:")
        for tip in recent_tips:
            print(f"   • {tip['match']} - {tip['tip_on']} @ {tip['odds']} ({tip['units']}u)")


async def main():
    """Função principal de teste"""
    print("🚀 Iniciando testes do Sistema Profissional de Tips...")
    print(f"🔧 Python: {sys.version}")
    print(f"📁 Diretório: {os.getcwd()}")
    
    try:
        # Inicialização
        tips_system, mock_client = await test_system_initialization()
        
        # Executa testes sequenciais
        test_functions = [
            lambda: test_match_filtering(tips_system, mock_client),
            lambda: test_tip_generation(tips_system, mock_client),
            lambda: test_rate_limiting(tips_system),
            lambda: test_monitoring_status(tips_system),
            lambda: test_force_scan(tips_system, mock_client),
            lambda: test_tips_expiration(tips_system),
            lambda: demonstrate_full_workflow(tips_system, mock_client)
        ]
        
        for test_func in test_functions:
            try:
                await test_func()
            except Exception as e:
                print(f"\n❌ Erro no teste: {e}")
        
        # Estatísticas finais
        print(f"\n{'='*70}")
        print("📈 ESTATÍSTICAS FINAIS")
        print(f"{'='*70}")
        
        final_status = tips_system.get_monitoring_status()
        stats = final_status['statistics']
        
        print(f"Total de partidas scaneadas: {stats['matches_scanned']}")
        print(f"Tips geradas: {stats['tips_generated']}")
        print(f"Tips enviadas: {stats['tips_sent']}")
        print(f"Taxa de sucesso: {stats['success_rate']:.1f}%")
        print(f"Uptime: {final_status['uptime_hours']:.3f} horas")
        
        print(f"\n🎉 TODOS OS TESTES CONCLUÍDOS COM SUCESSO!")
        
    except Exception as e:
        print(f"\n❌ Erro fatal durante os testes: {e}")
        sys.exit(1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n🛑 Teste interrompido pelo usuário")
    except Exception as e:
        print(f"\n\n❌ Erro fatal: {e}")
        sys.exit(1) 
