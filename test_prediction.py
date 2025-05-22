"""
Script para testar o modelo de previsão em uma partida de demonstração.

Este script demonstra como o modelo faz previsões com e sem dados ao vivo.
"""

import logging
import sys
from services.predictor import PredictorService

# Configuração de logging para console
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def main():
    """Função principal para testar o modelo"""
    print("="*80)
    print("TESTE DO MODELO DE PREVISÃO PARA PARTIDAS DE LOL")
    print("="*80)
    
    # Inicializar o serviço de previsão (usa seu próprio mecanismo de fallback)
    predictor = PredictorService()
    
    # Definir times para teste
    team_a = "T1"
    team_b = "GenG"
    
    # Testar previsão básica (sem dados ao vivo)
    print(f"\n[1] Previsão básica para {team_a} vs {team_b}:")
    print("-"*50)
    # Não passamos composição nem match_data para a previsão básica
    basic_prediction = predictor.get_prediction(team_a, team_b)
    
    print(f"Probabilidade de vitória para {team_a}: {basic_prediction['probaA']*100:.2f}%")
    print(f"Probabilidade de vitória para {team_b}: {basic_prediction['probaB']*100:.2f}%")
    print(f"Time favorito: {basic_prediction['favorite_team']}")
    print(f"Nível de confiança: {basic_prediction['confidence']}")
    print(f"Dica de aposta: {basic_prediction['bet_tip']}")
    
    # Simular dados de uma partida ao vivo
    live_stats = {
        "game_time": "22:15",  # Mid-game
        "team_a": {
            "gold": 38500,
            "kills": 12,
            "towers": 5,
            "dragons": ["ocean", "infernal", "cloud"],
            "barons": 0
        },
        "team_b": {
            "gold": 35200,
            "kills": 8,
            "towers": 2,
            "dragons": ["mountain"],
            "barons": 0
        }
    }
    
    # Criar dados de match para simulação
    match_data = {
        "teamA": team_a,
        "teamB": team_b,
        "composition_a": ["Aatrox", "Viego", "Azir", "Jinx", "Thresh"],
        "composition_b": ["Jax", "Lee Sin", "Ahri", "Xayah", "Pyke"],
        "current_game_stats": live_stats
    }
    
    # Testar previsão com dados ao vivo
    print(f"\n[2] Previsão com dados ao vivo para {team_a} vs {team_b}:")
    print("-"*50)
    # O serviço predictor tem sua própria lógica para processar campos
    compositions = {
        "composition_a": match_data["composition_a"],
        "composition_b": match_data["composition_b"]
    }
    live_prediction = predictor.get_prediction(team_a, team_b, compositions, match_data)
    
    print(f"Probabilidade de vitória para {team_a}: {live_prediction['probaA']*100:.2f}%")
    print(f"Probabilidade de vitória para {team_b}: {live_prediction['probaB']*100:.2f}%")
    print(f"Time favorito: {live_prediction['favorite_team']}")
    print(f"Nível de confiança: {live_prediction['confidence']}")
    print(f"Dica de aposta: {live_prediction['bet_tip']}")
    
    # Obter análise completa da partida
    print(f"\n[3] Análise detalhada da partida {team_a} vs {team_b}:")
    print("-"*50)
    analysis = predictor.get_match_analysis(match_data)
    
    print(f"Time favorito: {analysis['favorite_team']}")
    print(f"Probabilidade de vitória:")
    print(f"  {team_a}: {analysis['win_probability']['team_a']*100:.2f}%")
    print(f"  {team_b}: {analysis['win_probability']['team_b']*100:.2f}%")
    print(f"Odds justas:")
    print(f"  {team_a}: {analysis['current_odds']['team_a']:.2f}")
    print(f"  {team_b}: {analysis['current_odds']['team_b']:.2f}")
    print(f"Nível de confiança: {analysis['confidence']}")
    print(f"Análise: {analysis['analysis']}")
    print(f"Dica de aposta: {analysis['bet_tip']}")
    print(f"Fatores-chave: {', '.join(analysis['key_factors'][:3])}")
    
    print("\nTeste do modelo concluído com sucesso!")
    print("="*80)

if __name__ == "__main__":
    main() 