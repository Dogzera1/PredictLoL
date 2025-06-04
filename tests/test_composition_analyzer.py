#!/usr/bin/env python3
"""
Testes Unitários para CompositionAnalyzer

Suite completa de testes para verificar:
- Análise de força individual
- Cálculo de sinergias 
- Análise de matchups
- Flexibilidade estratégica
- Performance e edge cases
"""

import asyncio
import pytest
import sys
import os
from unittest.mock import patch, MagicMock

# Adiciona o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bot.analyzers.composition_analyzer import CompositionAnalyzer


class TestCompositionAnalyzer:
    """Classe principal de testes para CompositionAnalyzer"""
    
    @pytest.fixture
    async def analyzer(self):
        """Fixture que cria uma instância do analisador"""
        analyzer = CompositionAnalyzer()
        await asyncio.sleep(1)  # Aguarda inicialização das databases
        return analyzer
    
    @pytest.fixture
    def sample_team_picks(self):
        """Fixture com composição de exemplo"""
        return [
            {"champion": "Azir", "position": "mid", "pick_order": 1},
            {"champion": "Graves", "position": "jungle", "pick_order": 2},
            {"champion": "Gnar", "position": "top", "pick_order": 3},
            {"champion": "Jinx", "position": "adc", "pick_order": 4},
            {"champion": "Thresh", "position": "support", "pick_order": 5}
        ]
    
    @pytest.fixture
    def sample_enemy_picks(self):
        """Fixture com composição inimiga de exemplo"""
        return [
            {"champion": "Viktor", "position": "mid", "pick_order": 1},
            {"champion": "Kindred", "position": "jungle", "pick_order": 2},
            {"champion": "Jayce", "position": "top", "pick_order": 3},
            {"champion": "Aphelios", "position": "adc", "pick_order": 4},
            {"champion": "Leona", "position": "support", "pick_order": 5}
        ]

    @pytest.mark.asyncio
    async def test_analyzer_initialization(self, analyzer):
        """Testa inicialização correta do analisador"""
        assert analyzer is not None
        assert hasattr(analyzer, 'champions_db')
        assert hasattr(analyzer, 'synergies_db')
        assert hasattr(analyzer, 'counters_db')
        
        # Verifica se databases não estão vazias
        assert len(analyzer.champions_db) > 0
        assert len(analyzer.synergies_db) > 0
        assert len(analyzer.counters_db) > 0

    @pytest.mark.asyncio
    async def test_full_composition_analysis(self, analyzer, sample_team_picks, sample_enemy_picks):
        """Testa análise completa de composição"""
        result = await analyzer.analyze_team_composition(
            team_picks=sample_team_picks,
            enemy_picks=sample_enemy_picks,
            patch_version="14.10"
        )
        
        # Verifica estrutura do resultado
        assert isinstance(result, dict)
        assert "overall_score" in result
        assert "individual_strength" in result
        assert "team_synergies" in result
        assert "matchup_advantages" in result
        assert "strategic_flexibility" in result
        assert "game_phase_strength" in result
        assert "detailed_analysis" in result
        assert "composition_summary" in result
        
        # Verifica tipos e ranges dos valores
        assert 0.0 <= result["overall_score"] <= 10.0
        assert 0.0 <= result["individual_strength"] <= 10.0
        assert 0.0 <= result["team_synergies"] <= 10.0
        assert 0.0 <= result["matchup_advantages"] <= 10.0
        assert 0.0 <= result["strategic_flexibility"] <= 10.0
        
        # Verifica game phases
        phases = result["game_phase_strength"]
        assert isinstance(phases, dict)
        assert "early" in phases
        assert "mid" in phases
        assert "late" in phases
        assert 0.0 <= phases["early"] <= 10.0
        assert 0.0 <= phases["mid"] <= 10.0
        assert 0.0 <= phases["late"] <= 10.0

    @pytest.mark.asyncio
    async def test_individual_strength_calculation(self, analyzer):
        """Testa cálculo de força individual"""
        picks = [
            {"champion": "Azir", "position": "mid", "pick_order": 1},
            {"champion": "Graves", "position": "jungle", "pick_order": 2}
        ]
        
        strength = await analyzer._calculate_individual_strength(picks, "14.10")
        
        assert isinstance(strength, float)
        assert 1.0 <= strength <= 10.0

    @pytest.mark.asyncio
    async def test_team_synergies_calculation(self, analyzer):
        """Testa cálculo de sinergias do time"""
        picks = [
            {"champion": "Azir", "position": "mid", "pick_order": 1},
            {"champion": "Graves", "position": "jungle", "pick_order": 2},
            {"champion": "Thresh", "position": "support", "pick_order": 3}
        ]
        
        synergies = await analyzer._calculate_team_synergies(picks)
        
        assert isinstance(synergies, float)
        assert 1.0 <= synergies <= 10.0

    @pytest.mark.asyncio
    async def test_matchup_advantages_calculation(self, analyzer):
        """Testa cálculo de vantagens de matchup"""
        team_picks = [
            {"champion": "Azir", "position": "mid", "pick_order": 1},
            {"champion": "Graves", "position": "jungle", "pick_order": 2}
        ]
        enemy_picks = [
            {"champion": "LeBlanc", "position": "mid", "pick_order": 1},
            {"champion": "Kindred", "position": "jungle", "pick_order": 2}
        ]
        
        advantages = await analyzer._calculate_matchup_advantages(team_picks, enemy_picks)
        
        assert isinstance(advantages, float)
        assert 1.0 <= advantages <= 10.0

    @pytest.mark.asyncio
    async def test_strategic_flexibility_calculation(self, analyzer):
        """Testa cálculo de flexibilidade estratégica"""
        picks = [
            {"champion": "Azir", "position": "mid", "pick_order": 1},
            {"champion": "Yasuo", "position": "top", "pick_order": 2},
            {"champion": "Malphite", "position": "jungle", "pick_order": 3}
        ]
        
        flexibility = await analyzer._calculate_strategic_flexibility(picks)
        
        assert isinstance(flexibility, float)
        assert 1.0 <= flexibility <= 10.0

    @pytest.mark.asyncio
    async def test_game_phase_strength_calculation(self, analyzer):
        """Testa cálculo de força por fase do jogo"""
        picks = [
            {"champion": "Graves", "position": "jungle", "pick_order": 1},  # Strong early
            {"champion": "Azir", "position": "mid", "pick_order": 2},      # Strong late
            {"champion": "Thresh", "position": "support", "pick_order": 3}  # Balanced
        ]
        
        phases = await analyzer._calculate_game_phase_strength(picks)
        
        assert isinstance(phases, dict)
        assert "early" in phases
        assert "mid" in phases
        assert "late" in phases
        
        for phase_value in phases.values():
            assert isinstance(phase_value, float)
            assert 0.0 <= phase_value <= 10.0

    @pytest.mark.asyncio
    async def test_win_conditions_identification(self, analyzer):
        """Testa identificação de win conditions"""
        # Composição teamfight
        teamfight_picks = [
            {"champion": "Malphite", "position": "top", "pick_order": 1},
            {"champion": "Yasuo", "position": "mid", "pick_order": 2},
            {"champion": "Graves", "position": "jungle", "pick_order": 3},
            {"champion": "Jinx", "position": "adc", "pick_order": 4},
            {"champion": "Thresh", "position": "support", "pick_order": 5}
        ]
        
        win_conditions = await analyzer._identify_win_conditions(teamfight_picks)
        
        assert isinstance(win_conditions, list)
        assert len(win_conditions) > 0
        assert "teamfight" in win_conditions or "teamfight_engage" in win_conditions

    @pytest.mark.asyncio
    async def test_composition_type_identification(self, analyzer):
        """Testa identificação do tipo de composição"""
        picks = [
            {"champion": "Malphite", "position": "top", "pick_order": 1},
            {"champion": "Sejuani", "position": "jungle", "pick_order": 2},
            {"champion": "Azir", "position": "mid", "pick_order": 3},
            {"champion": "Jinx", "position": "adc", "pick_order": 4},
            {"champion": "Thresh", "position": "support", "pick_order": 5}
        ]
        
        comp_type = await analyzer._identify_composition_type(picks)
        
        assert isinstance(comp_type, str)
        assert comp_type in [
            "engage_composition", 
            "poke_composition", 
            "protect_the_carry", 
            "balanced_composition"
        ]

    @pytest.mark.asyncio
    async def test_empty_picks_handling(self, analyzer):
        """Testa handling de picks vazios"""
        result = await analyzer.analyze_team_composition(
            team_picks=[],
            enemy_picks=[],
            patch_version="14.10"
        )
        
        # Deve retornar análise padrão sem erro
        assert isinstance(result, dict)
        assert "overall_score" in result

    @pytest.mark.asyncio
    async def test_invalid_champion_handling(self, analyzer):
        """Testa handling de campeões inválidos"""
        picks_with_invalid = [
            {"champion": "InvalidChampion", "position": "mid", "pick_order": 1},
            {"champion": "Azir", "position": "mid", "pick_order": 2}
        ]
        
        result = await analyzer.analyze_team_composition(
            team_picks=picks_with_invalid,
            enemy_picks=[],
            patch_version="14.10"
        )
        
        # Não deve dar crash, deve tratar gracefully
        assert isinstance(result, dict)
        assert "overall_score" in result

    @pytest.mark.asyncio
    async def test_synergy_calculation_edge_cases(self, analyzer):
        """Testa edge cases no cálculo de sinergias"""
        # Teste com 1 pick apenas
        single_pick = [{"champion": "Azir", "position": "mid", "pick_order": 1}]
        synergy = await analyzer._calculate_team_synergies(single_pick)
        assert synergy == 5.0  # Deve retornar valor neutro
        
        # Teste com picks conhecidos que têm sinergia
        synergistic_picks = [
            {"champion": "Azir", "position": "mid", "pick_order": 1},
            {"champion": "Graves", "position": "jungle", "pick_order": 2}
        ]
        synergy = await analyzer._calculate_team_synergies(synergistic_picks)
        assert synergy > 5.0  # Deve ter sinergia positiva

    @pytest.mark.asyncio
    async def test_matchup_advantage_edge_cases(self, analyzer):
        """Testa edge cases na análise de matchups"""
        team_picks = [{"champion": "Azir", "position": "mid", "pick_order": 1}]
        
        # Sem inimigos
        advantage = await analyzer._calculate_matchup_advantages(team_picks, [])
        assert advantage == 5.0  # Valor neutro
        
        # Com inimigo conhecido counter
        enemy_picks = [{"champion": "LeBlanc", "position": "mid", "pick_order": 1}]
        advantage = await analyzer._calculate_matchup_advantages(team_picks, enemy_picks)
        assert advantage < 5.0  # Deve ter desvantagem

    @pytest.mark.asyncio
    async def test_performance_with_large_compositions(self, analyzer):
        """Testa performance com composições grandes"""
        import time
        
        large_picks = [
            {"champion": f"Champion{i}", "position": "mid", "pick_order": i}
            for i in range(10)  # Mais picks que o normal
        ]
        
        start_time = time.time()
        result = await analyzer.analyze_team_composition(
            team_picks=large_picks,
            enemy_picks=large_picks,
            patch_version="14.10"
        )
        end_time = time.time()
        
        # Deve completar em tempo razoável (< 5 segundos)
        assert (end_time - start_time) < 5.0
        assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_fallback_analysis_activation(self, analyzer):
        """Testa ativação da análise de fallback em caso de erro"""
        # Mock para forçar erro interno
        with patch.object(analyzer, '_calculate_individual_strength', side_effect=Exception("Erro simulado")):
            result = await analyzer.analyze_team_composition(
                team_picks=[{"champion": "Azir", "position": "mid", "pick_order": 1}],
                enemy_picks=[],
                patch_version="14.10"
            )
            
            # Deve retornar análise de fallback
            assert result["overall_score"] == 5.0
            assert result["composition_summary"] == "ANÁLISE INDISPONÍVEL"

    @pytest.mark.asyncio
    async def test_database_integrity(self, analyzer):
        """Testa integridade das databases"""
        # Verifica estrutura da database de campeões
        for champion, data in analyzer.champions_db.items():
            assert isinstance(champion, str)
            assert isinstance(data, dict)
            assert "base_strength" in data
            assert "type" in data
            assert "positions" in data
            assert "early_game" in data
            assert "mid_game" in data
            assert "late_game" in data
            
            # Verifica ranges de valores
            assert 1.0 <= data["base_strength"] <= 10.0
            assert 1.0 <= data["early_game"] <= 10.0
            assert 1.0 <= data["mid_game"] <= 10.0
            assert 1.0 <= data["late_game"] <= 10.0
        
        # Verifica estrutura da database de sinergias
        for combo, data in analyzer.synergies_db.items():
            if combo.startswith("_"):  # Pula metadados
                continue
            assert isinstance(data, dict)
            assert "synergy_score" in data
            assert "category" in data
            assert "reason" in data
            assert 1.0 <= data["synergy_score"] <= 10.0
        
        # Verifica estrutura da database de counters
        for matchup, data in analyzer.counters_db.items():
            if matchup.startswith("_"):  # Pula metadados
                continue
            assert isinstance(data, dict)
            assert "advantage" in data
            assert "confidence" in data
            assert "reason" in data
            assert -1.0 <= data["advantage"] <= 1.0
            assert 0.0 <= data["confidence"] <= 1.0

    @pytest.mark.asyncio
    async def test_composition_summary_generation(self, analyzer):
        """Testa geração de resumos de composição"""
        picks = [{"champion": "Azir", "position": "mid", "pick_order": 1}]
        
        # Testa diferentes scores
        summary_high = analyzer._generate_composition_summary(9.0, picks)
        assert "SUPERIOR" in summary_high
        
        summary_medium = analyzer._generate_composition_summary(7.0, picks)
        assert "FORTE" in summary_medium
        
        summary_balanced = analyzer._generate_composition_summary(5.5, picks)
        assert "EQUILIBRADA" in summary_balanced
        
        summary_weak = analyzer._generate_composition_summary(3.0, picks)
        assert "FRACA" in summary_weak


# Função para executar testes manualmente
async def run_manual_tests():
    """Executa testes manualmente sem pytest"""
    print("🧪 EXECUTANDO TESTES MANUAIS DO COMPOSITION ANALYZER")
    print("=" * 60)
    
    analyzer = CompositionAnalyzer()
    await asyncio.sleep(2)  # Aguarda inicialização
    
    sample_picks = [
        {"champion": "Azir", "position": "mid", "pick_order": 1},
        {"champion": "Graves", "position": "jungle", "pick_order": 2},
        {"champion": "Thresh", "position": "support", "pick_order": 3}
    ]
    
    enemy_picks = [
        {"champion": "LeBlanc", "position": "mid", "pick_order": 1},
        {"champion": "Kindred", "position": "jungle", "pick_order": 2},
        {"champion": "Leona", "position": "support", "pick_order": 3}
    ]
    
    # Teste 1: Análise completa
    print("\n🔸 Teste 1: Análise Completa")
    result = await analyzer.analyze_team_composition(sample_picks, enemy_picks)
    print(f"✅ Score: {result['overall_score']}/10")
    print(f"✅ Sinergias: {result['team_synergies']}/10")
    print(f"✅ Matchups: {result['matchup_advantages']}/10")
    
    # Teste 2: Edge cases
    print("\n🔸 Teste 2: Edge Cases")
    empty_result = await analyzer.analyze_team_composition([], [])
    print(f"✅ Picks vazios: {empty_result['overall_score']}/10")
    
    # Teste 3: Performance
    print("\n🔸 Teste 3: Performance")
    import time
    start = time.time()
    for _ in range(10):
        await analyzer.analyze_team_composition(sample_picks, enemy_picks)
    end = time.time()
    print(f"✅ 10 análises em {end-start:.2f}s ({(end-start)/10:.3f}s por análise)")
    
    print("\n✅ TODOS OS TESTES MANUAIS CONCLUÍDOS COM SUCESSO!")


if __name__ == "__main__":
    asyncio.run(run_manual_tests()) 
