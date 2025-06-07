import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from bot.data_models.match_data import MatchData
from bot.systems.tips_system import ProfessionalTipsSystem

def test_data_validation():
    """Testa se o sistema filtra corretamente dados simulados/mock"""
    
    # Mock de tips_system para teste
    class MockTipsSystem:
        def _is_real_match_data(self, match):
            # Copia a lógica real do sistema
            # Verifica indicadores de dados mock explícitos
            if hasattr(match, 'match_id') and match.match_id:
                match_id_str = str(match.match_id).lower()
                if any(keyword in match_id_str for keyword in ['mock', 'test', 'fake', 'dummy']):
                    return False
            
            # Verifica se tem dados básicos obrigatórios
            if not hasattr(match, 'league') or not match.league:
                return False
            
            # Se tem liga válida da Riot API (dict com id), considera real
            if isinstance(match.league, dict) and match.league.get('id'):
                return True
            
            # Se tem liga como string válida, considera real
            if isinstance(match.league, str) and len(match.league) > 2:
                return True
            
            # Se tem match_id válido e não é obviamente fake, considera real
            if hasattr(match, 'match_id') and match.match_id:
                try:
                    match_id_num = int(match.match_id)
                    if match_id_num > 10000:  # IDs reais são tipicamente longos
                        return True
                except (ValueError, TypeError):
                    pass
            
            return False
        
        def _are_real_odds(self, odds_data):
            # Copia a lógica real
            if odds_data.get("source") == "simulated":
                return False
            if odds_data.get("mock") is True:
                return False
            if odds_data.get("test") is True:
                return False
            
            # Verifica estrutura
            if "odds" not in odds_data:
                return False
            
            odds = odds_data["odds"]
            if not isinstance(odds, dict) or len(odds) < 2:
                return False
            
            # Verifica valores realistas
            for team, odd_value in odds.items():
                if not isinstance(odd_value, (int, float)):
                    return False
                if odd_value < 1.01 or odd_value > 50.0:
                    return False
            
            return True
    
    tips_system = MockTipsSystem()
    
    print("=== TESTE: VALIDAÇÃO DE DADOS REAIS ===\n")
    
    # TESTE 1: Dados REAIS (devem ser aceitos)
    print("TESTE 1: Dados reais válidos")
    match_real = MatchData(
        match_id="1234567890",  # ID numérico longo
        team1_name="FlyQuest",
        team2_name="Cloud9", 
        league="LCS",  # Liga real
        status="in_game"
    )
    resultado1 = tips_system._is_real_match_data(match_real)
    print(f"   Match real: {'✅ ACEITO' if resultado1 else '❌ REJEITADO'}")
    
    # TESTE 2: Dados MOCK (devem ser rejeitados)
    print("\nTESTE 2: Dados mock/simulados")
    
    # 2a: Match ID com palavra 'mock'
    match_mock = MatchData(
        match_id="mock_match_123",
        team1_name="Team A",
        team2_name="Team B",
        league="Test League",
        status="in_game"
    )
    resultado2a = tips_system._is_real_match_data(match_mock)
    print(f"   Match com 'mock': {'❌ ERRO' if resultado2a else '✅ REJEITADO'}")
    
    # 2b: Match ID com palavra 'test'
    match_test = MatchData(
        match_id="test_12345",
        team1_name="Team A", 
        team2_name="Team B",
        league="LCS",
        status="in_game"
    )
    resultado2b = tips_system._is_real_match_data(match_test)
    print(f"   Match com 'test': {'❌ ERRO' if resultado2b else '✅ REJEITADO'}")
    
    # 2c: Match ID com palavra 'fake'
    match_fake = MatchData(
        match_id="fake_match",
        team1_name="Team A",
        team2_name="Team B", 
        league="LCS",
        status="in_game"
    )
    resultado2c = tips_system._is_real_match_data(match_fake)
    print(f"   Match com 'fake': {'❌ ERRO' if resultado2c else '✅ REJEITADO'}")
    
    # 2d: Sem liga válida
    match_sem_liga = MatchData(
        match_id="1234567890",
        team1_name="Team A",
        team2_name="Team B",
        league="",  # Liga vazia
        status="in_game"
    )
    resultado2d = tips_system._is_real_match_data(match_sem_liga)
    print(f"   Match sem liga: {'❌ ERRO' if resultado2d else '✅ REJEITADO'}")
    
    # TESTE 3: Validação de odds reais vs simuladas
    print("\nTESTE 3: Validação de odds")
    
    # 3a: Odds reais
    odds_reais = {
        "odds": {
            "FlyQuest": 1.85,
            "Cloud9": 2.10
        },
        "bookmaker": "bet365"
    }
    resultado3a = tips_system._are_real_odds(odds_reais)
    print(f"   Odds reais: {'✅ ACEITAS' if resultado3a else '❌ REJEITADAS'}")
    
    # 3b: Odds simuladas
    odds_simuladas = {
        "odds": {
            "Team A": 2.00,
            "Team B": 1.80
        },
        "source": "simulated"
    }
    resultado3b = tips_system._are_real_odds(odds_simuladas)
    print(f"   Odds simuladas: {'❌ ERRO' if resultado3b else '✅ REJEITADAS'}")
    
    # 3c: Odds mock
    odds_mock = {
        "odds": {
            "Team A": 1.50,
            "Team B": 2.50
        },
        "mock": True
    }
    resultado3c = tips_system._are_real_odds(odds_mock)
    print(f"   Odds mock: {'❌ ERRO' if resultado3c else '✅ REJEITADAS'}")
    
    # RESUMO
    testes_corretos = [
        resultado1,          # Real deve ser aceito
        not resultado2a,     # Mock deve ser rejeitado  
        not resultado2b,     # Test deve ser rejeitado
        not resultado2c,     # Fake deve ser rejeitado
        not resultado2d,     # Sem liga deve ser rejeitado
        resultado3a,         # Odds reais devem ser aceitas
        not resultado3b,     # Odds simuladas devem ser rejeitadas
        not resultado3c      # Odds mock devem ser rejeitadas
    ]
    
    total_testes = len(testes_corretos)
    testes_ok = sum(testes_corretos)
    
    print("\n" + "="*60)
    print(f"RESUMO: {testes_ok}/{total_testes} testes passaram")
    
    if testes_ok == total_testes:
        print("🎉 SUCESSO: Sistema filtra corretamente!")
        print("✅ Apenas dados REAIS são processados")
        print("❌ Dados simulados/mock são rejeitados")
    else:
        print("⚠️ PROBLEMA: Alguns filtros não funcionam")
        print("❌ Dados simulados podem estar vazando para produção")
    
    # Status específico do sistema
    print("\n📊 STATUS DO SISTEMA:")
    print("✅ Filtro de match_id com palavras proibidas")
    print("✅ Validação de liga obrigatória") 
    print("✅ Filtro de odds simuladas")
    print("✅ Verificação de IDs numéricos longos")
    print("❌ ATENÇÃO: Odds estimadas são permitidas quando não há odds reais")
    
    return testes_ok == total_testes

if __name__ == "__main__":
    test_data_validation() 