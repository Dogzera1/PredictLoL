#!/usr/bin/env python3
"""
Testes automatizados para Bot LoL V3 Ultra Avançado
Verifica todas as funcionalidades principais
"""

import pytest
import asyncio
import os
import json
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

# Configurar environment para testes
os.environ['TELEGRAM_TOKEN'] = 'test-token-for-testing'
os.environ['ENVIRONMENT'] = 'test'

# Imports do sistema
import main_v3_riot_integrated
from main_v3_riot_integrated import (
    TelegramBotV3Improved,
    DynamicPredictionSystem,
    ImprovedRiotAPI,
    ChampionAnalyzer
)
import value_bet_system
from value_bet_system import ValueBetDetector, OddsSimulator, ValueBet


class TestRiotAPIIntegration:
    """Testes para integração com API da Riot"""
    
    @pytest.fixture
    def riot_api(self):
        return ImprovedRiotAPI()
    
    @pytest.mark.asyncio
    async def test_get_live_matches(self, riot_api):
        """Testa busca de partidas ao vivo"""
        matches = await riot_api.get_all_live_matches()
        
        assert isinstance(matches, list)
        assert len(matches) > 0
        
        # Verificar estrutura das partidas
        for match in matches:
            assert 'id' in match
            assert 'teams' in match
            assert len(match['teams']) >= 2
            
    def test_fallback_matches_generation(self, riot_api):
        """Testa geração de partidas fallback"""
        fallback_matches = riot_api._generate_fallback_live_matches()
        
        assert isinstance(fallback_matches, list)
        assert len(fallback_matches) >= 3
        
        for match in fallback_matches:
            assert 'id' in match
            assert 'league' in match
            assert 'teams' in match
            assert 'status' in match
            

class TestPredictionSystem:
    """Testes para sistema de predições"""
    
    @pytest.fixture
    def prediction_system(self):
        return DynamicPredictionSystem()
    
    @pytest.fixture
    def sample_match(self):
        return {
            'id': 'test_match_1',
            'teams': [
                {'name': 'T1', 'code': 'T1'},
                {'name': 'Gen.G', 'code': 'GEN'}
            ],
            'league': 'LCK',
            'status': 'inProgress'
        }
    
    @pytest.mark.asyncio
    async def test_predict_match(self, prediction_system, sample_match):
        """Testa predição de partida"""
        prediction = await prediction_system.predict_live_match(sample_match)
        
        # Verificar estrutura da predição
        assert 'team1' in prediction
        assert 'team2' in prediction
        assert 'team1_win_probability' in prediction
        assert 'team2_win_probability' in prediction
        assert 'confidence' in prediction
        assert 'analysis' in prediction
        
        # Verificar valores válidos
        prob1 = prediction['team1_win_probability']
        prob2 = prediction['team2_win_probability']
        
        assert 0 <= prob1 <= 1
        assert 0 <= prob2 <= 1
        assert abs((prob1 + prob2) - 1.0) < 0.01  # Soma deve ser ~1
        
    def test_team_data_retrieval(self, prediction_system):
        """Testa busca de dados dos times"""
        team_data = prediction_system._get_team_data('T1')
        
        assert isinstance(team_data, dict)
        assert 'name' in team_data
        assert 'region' in team_data
        assert 'rating' in team_data
        
    def test_confidence_calculation(self, prediction_system):
        """Testa cálculo de confiança"""
        team1_data = {'rating': 90, 'region': 'LCK'}
        team2_data = {'rating': 85, 'region': 'LCK'}
        
        confidence = prediction_system._calculate_confidence(team1_data, team2_data)
        assert confidence in ['muito baixa', 'baixa', 'média', 'alta', 'muito alta']


class TestChampionAnalyzer:
    """Testes para análise de campeões"""
    
    @pytest.fixture
    def champion_analyzer(self):
        return ChampionAnalyzer()
    
    @pytest.fixture
    def sample_compositions(self):
        return (
            ['Aatrox', 'Graves', 'Azir', 'Jinx', 'Thresh'],
            ['Camille', 'Lee Sin', 'LeBlanc', 'Lucian', 'Leona']
        )
    
    def test_draft_analysis(self, champion_analyzer, sample_compositions):
        """Testa análise completa de draft"""
        team1_comp, team2_comp = sample_compositions
        
        draft_analysis = champion_analyzer.analyze_draft(team1_comp, team2_comp)
        
        assert 'team1' in draft_analysis
        assert 'team2' in draft_analysis
        assert 'draft_advantage' in draft_analysis
        assert 'phase_analysis' in draft_analysis
        
    def test_composition_analysis(self, champion_analyzer):
        """Testa análise de composição individual"""
        composition = ['Aatrox', 'Graves', 'Azir', 'Jinx', 'Thresh']
        
        analysis = champion_analyzer._analyze_team_composition(composition)
        
        assert 'composition_types' in analysis
        assert 'synergy_score' in analysis
        assert 'power_spikes' in analysis
        assert 'early_game_strength' in analysis
        

class TestValueBettingSystem:
    """Testes para sistema de value betting"""
    
    @pytest.fixture
    def odds_simulator(self):
        return OddsSimulator()
    
    @pytest.fixture
    def mock_prediction_system(self):
        mock = AsyncMock()
        mock.predict_live_match.return_value = {
            'team1_win_probability': 0.65,
            'team2_win_probability': 0.35,
            'confidence': 'alta'
        }
        return mock
    
    @pytest.fixture
    def value_detector(self, mock_prediction_system, odds_simulator):
        return ValueBetDetector(mock_prediction_system, odds_simulator)
    
    def test_odds_simulation(self, odds_simulator):
        """Testa simulação de odds"""
        teams = ['T1', 'Gen.G']
        match_id = 'test_match'
        
        odds = odds_simulator.get_live_odds(match_id, teams)
        
        assert isinstance(odds, dict)
        assert len(odds) == 2
        assert all(1.1 <= odd <= 5.0 for odd in odds.values())
        
    @pytest.mark.asyncio
    async def test_value_bet_detection(self, value_detector):
        """Testa detecção de apostas de valor"""
        sample_match = {
            'id': 'test_match',
            'teams': [
                {'name': 'T1', 'code': 'T1'},
                {'name': 'Gen.G', 'code': 'GEN'}
            ],
            'league': 'LCK'
        }
        
        value_bets = await value_detector.analyze_match_for_value(sample_match)
        
        assert isinstance(value_bets, list)
        # Pode ou não encontrar value bets dependendo das odds simuladas
        
        for bet in value_bets:
            assert isinstance(bet, ValueBet)
            assert bet.predicted_probability > 0.55
            assert bet.value_percentage >= 0.15
            

class TestTelegramBot:
    """Testes para funcionalidades do bot Telegram"""
    
    @pytest.fixture
    def bot(self):
        bot = TelegramBotV3Improved()
        bot.application = MagicMock()
        bot.application.bot = MagicMock()
        return bot
    
    def test_bot_initialization(self, bot):
        """Testa inicialização do bot"""
        assert bot.riot_api is not None
        assert bot.prediction_system is not None
        assert bot.champion_analyzer is not None
        
    def test_authorization_system(self, bot):
        """Testa sistema de autorização"""
        # Usuário não autorizado
        assert not bot.is_user_authorized(12345)
        
        # Admin sempre autorizado
        admin_id = int(os.environ.get('ADMIN_USER_ID', '1'))
        assert bot.is_user_authorized(admin_id)
        
    def test_group_restrictions(self, bot):
        """Testa restrições de grupo"""
        # Grupos privados devem ser restritos por padrão
        assert bot.is_group_restricted('group')
        assert bot.is_group_restricted('supergroup')
        
        # Chat privado não deve ser restrito
        assert not bot.is_group_restricted('private')
        
    @pytest.mark.asyncio
    async def test_portfolio_functionality(self, bot):
        """Testa funcionalidade de portfolio"""
        # Mock update object
        mock_update = MagicMock()
        mock_update.message.reply_text = AsyncMock()
        
        await bot.show_portfolio(mock_update)
        
        # Verificar se a resposta foi enviada
        mock_update.message.reply_text.assert_called_once()
        

class TestSystemIntegration:
    """Testes de integração do sistema completo"""
    
    @pytest.mark.asyncio
    async def test_end_to_end_prediction_flow(self):
        """Testa fluxo completo de predição"""
        # Inicializar componentes
        riot_api = ImprovedRiotAPI()
        prediction_system = DynamicPredictionSystem()
        
        # Buscar partidas
        matches = await riot_api.get_all_live_matches()
        assert len(matches) > 0
        
        # Fazer predição
        prediction = await prediction_system.predict_live_match(matches[0])
        
        # Verificar resultado
        assert 'team1_win_probability' in prediction
        assert 'analysis' in prediction
        
    @pytest.mark.asyncio
    async def test_value_betting_integration(self):
        """Testa integração do sistema de value betting"""
        # Inicializar componentes
        riot_api = ImprovedRiotAPI()
        prediction_system = DynamicPredictionSystem()
        odds_simulator = OddsSimulator()
        value_detector = ValueBetDetector(prediction_system, odds_simulator)
        
        # Buscar partidas e analisar value bets
        matches = await riot_api.get_all_live_matches()
        
        for match in matches[:2]:  # Testar primeiras 2 partidas
            value_bets = await value_detector.analyze_match_for_value(match)
            assert isinstance(value_bets, list)
            

class TestErrorHandling:
    """Testes para tratamento de erros"""
    
    @pytest.mark.asyncio
    async def test_api_error_handling(self):
        """Testa tratamento de erros da API"""
        riot_api = ImprovedRiotAPI()
        
        # Simular erro de rede
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_get.side_effect = Exception("Network error")
            
            # Deve retornar partidas fallback
            matches = await riot_api.get_all_live_matches()
            assert len(matches) > 0  # Fallback deve funcionar
            
    @pytest.mark.asyncio
    async def test_prediction_error_handling(self):
        """Testa tratamento de erros de predição"""
        prediction_system = DynamicPredictionSystem()
        
        # Match inválido
        invalid_match = {'invalid': 'data'}
        
        prediction = await prediction_system.predict_live_match(invalid_match)
        
        # Deve retornar predição fallback
        assert 'team1_win_probability' in prediction
        

class TestPerformance:
    """Testes de performance"""
    
    @pytest.mark.asyncio
    async def test_prediction_speed(self):
        """Testa velocidade das predições"""
        prediction_system = DynamicPredictionSystem()
        riot_api = ImprovedRiotAPI()
        
        matches = await riot_api.get_all_live_matches()
        
        start_time = datetime.now()
        
        # Processar 5 partidas
        for match in matches[:5]:
            await prediction_system.predict_live_match(match)
            
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # Deve processar em menos de 10 segundos
        assert duration < 10.0
        
    @pytest.mark.asyncio
    async def test_concurrent_predictions(self):
        """Testa predições concorrentes"""
        prediction_system = DynamicPredictionSystem()
        riot_api = ImprovedRiotAPI()
        
        matches = await riot_api.get_all_live_matches()
        
        # Executar predições em paralelo
        tasks = [
            prediction_system.predict_live_match(match)
            for match in matches[:3]
        ]
        
        results = await asyncio.gather(*tasks)
        
        # Todas devem ter resultado válido
        assert len(results) == 3
        for result in results:
            assert 'team1_win_probability' in result


class TestDataIntegrity:
    """Testes de integridade dos dados"""
    
    def test_champion_data_completeness(self):
        """Testa completude dos dados de campeões"""
        analyzer = ChampionAnalyzer()
        
        for champion, stats in analyzer.champion_stats.items():
            assert 'lane' in stats
            assert 'type' in stats
            assert 'early' in stats
            assert 'mid' in stats
            assert 'late' in stats
            assert 'teamfight' in stats
            
            # Verificar ranges válidos
            assert 1 <= stats['early'] <= 10
            assert 1 <= stats['mid'] <= 10
            assert 1 <= stats['late'] <= 10
            assert 1 <= stats['teamfight'] <= 10
            
    def test_team_data_consistency(self):
        """Testa consistência dos dados de times"""
        prediction_system = DynamicPredictionSystem()
        
        # Verificar alguns times conhecidos
        known_teams = ['T1', 'Gen.G', 'JDG', 'BLG', 'G2']
        
        for team in known_teams:
            team_data = prediction_system._get_team_data(team)
            
            assert 'name' in team_data
            assert 'region' in team_data
            assert 'rating' in team_data
            assert 50 <= team_data['rating'] <= 100


# Fixtures globais para configuração
@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Configuração global dos testes"""
    # Configurar logging para testes
    import logging
    logging.getLogger().setLevel(logging.WARNING)
    
    # Configurar environment
    os.environ['ENVIRONMENT'] = 'test'
    os.environ['LOG_LEVEL'] = 'WARNING'
    

if __name__ == "__main__":
    # Executar testes quando rodado diretamente
    pytest.main([__file__, "-v", "--tb=short"]) 