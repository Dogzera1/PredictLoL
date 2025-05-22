"""
Script simplificado para testar o modelo de previsão.

Este script demonstra o básico do funcionamento do sistema de previsão para partidas de LoL.
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
    """Função principal para testar o modelo de forma simples"""
    print("="*80)
    print("DEMONSTRAÇÃO SIMPLES DO MODELO DE PREVISÃO PARA LOL")
    print("="*80)
    
    # Inicializar o serviço de previsão
    predictor = PredictorService()
    
    # Definir times para teste
    team_a = "T1"
    team_b = "GenG"
    
    # Testar previsão básica (sem dados ao vivo)
    print(f"\n[1] Previsão básica para {team_a} vs {team_b}:")
    print("-"*50)
    basic_prediction = predictor.get_prediction(team_a, team_b)
    
    print(f"Probabilidade de vitória para {team_a}: {basic_prediction['probaA']*100:.2f}%")
    print(f"Probabilidade de vitória para {team_b}: {basic_prediction['probaB']*100:.2f}%")
    print(f"Time favorito: {basic_prediction['favorite_team']}")
    print(f"Nível de confiança: {basic_prediction['confidence']}")
    print(f"Dica de aposta: {basic_prediction['bet_tip']}")
    
    # Simular dados de uma partida ao vivo com vantagem para T1
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
    
    # Criar dados de partida simplificados
    match_data = {
        "teamA": team_a,
        "teamB": team_b,
        "current_game_stats": live_stats
    }
    
    # Testar previsão com dados ao vivo
    print(f"\n[2] Previsão com dados ao vivo para {team_a} vs {team_b}:")
    print("-"*50)
    live_prediction = predictor.get_prediction(team_a, team_b, None, match_data)
    
    print(f"Probabilidade de vitória para {team_a}: {live_prediction['probaA']*100:.2f}%")
    print(f"Probabilidade de vitória para {team_b}: {live_prediction['probaB']*100:.2f}%")
    print(f"Time favorito: {live_prediction['favorite_team']}")
    print(f"Nível de confiança: {live_prediction['confidence']}")
    print(f"Dica de aposta: {live_prediction['bet_tip']}")
    
    print("\nDemonstração concluída com sucesso!")
    print("="*80)

if __name__ == "__main__":
    main() 