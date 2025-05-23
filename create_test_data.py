#!/usr/bin/env python3
"""
Script para criar dados de teste processados a partir dos dados simulados
"""

import json
import numpy as np
import random
from datetime import datetime

def process_simulated_data():
    """Processa dados simulados para formato de teste"""
    
    # Carregar dados simulados
    with open('data/simulated_match_data.json', 'r') as f:
        raw_data = json.load(f)
    
    processed_data = []
    
    for match in raw_data:
        # Extrair features das estatísticas dos times
        stats_a = match['stats_a']
        stats_b = match['stats_b']
        
        # Determinar vencedor (1 se team_a venceu, 0 se team_b venceu)
        team1_win = 1 if match['winner'] == 'team_a' else 0
        
        # Criar features baseadas nas estatísticas
        features = {
            'match_id': match['match_id'],
            'team1_win': team1_win,
            
            # Features do time 1 (team_a)
            'team1_kills': stats_a['kills'],
            'team1_gold': stats_a['gold'],
            'team1_towers': stats_a['towers'],
            'team1_dragons': stats_a['dragons'],
            'team1_barons': stats_a['barons'],
            
            # Features do time 2 (team_b)  
            'team2_kills': stats_b['kills'],
            'team2_gold': stats_b['gold'],
            'team2_towers': stats_b['towers'],
            'team2_dragons': stats_b['dragons'],
            'team2_barons': stats_b['barons'],
            
            # Features derivadas
            'kill_diff': stats_a['kills'] - stats_b['kills'],
            'gold_diff': stats_a['gold'] - stats_b['gold'],
            'tower_diff': stats_a['towers'] - stats_b['towers'],
            'dragon_diff': stats_a['dragons'] - stats_b['dragons'],
            'baron_diff': stats_a['barons'] - stats_b['barons'],
            
            # Features de ratio
            'gold_ratio': stats_a['gold'] / (stats_a['gold'] + stats_b['gold']),
            'kill_ratio': stats_a['kills'] / max(1, stats_a['kills'] + stats_b['kills']),
            'objective_score_diff': (stats_a['towers'] + stats_a['dragons'] * 2 + stats_a['barons'] * 3) - 
                                  (stats_b['towers'] + stats_b['dragons'] * 2 + stats_b['barons'] * 3),
            
            # Features contextuais
            'tournament': match['tournament'],
            'games_count': match['games_count'],
            'team1_side': 'blue' if random.random() > 0.5 else 'red',  # Simular lado do mapa
            'game_duration': random.randint(18, 45),  # Simular duração em minutos
            'patch': f"14.{random.randint(1, 23)}",  # Simular patch
            
            # Features adicionais simuladas
            'total_kills': stats_a['kills'] + stats_b['kills'],
            'total_gold': stats_a['gold'] + stats_b['gold'],
            'first_blood': random.choice([0, 1]),
            'first_tower': random.choice([0, 1]),
            'first_dragon': random.choice([0, 1]),
            'elder_dragons': random.randint(0, 2),
            'herald_kills': random.randint(0, 2),
            
            # Meta features
            'avg_kills_per_min': (stats_a['kills'] + stats_b['kills']) / random.uniform(20, 40),
            'gold_per_min_diff': (stats_a['gold'] - stats_b['gold']) / random.uniform(25, 35),
            'vision_score_diff': random.randint(-100, 100),
            'cs_diff_15': random.randint(-50, 50),
            'gold_diff_15': random.randint(-2000, 2000),
            
            # Features de composição (simuladas)
            'team1_ad_count': random.randint(1, 3),
            'team1_ap_count': random.randint(1, 3), 
            'team1_tank_count': random.randint(0, 2),
            'team2_ad_count': random.randint(1, 3),
            'team2_ap_count': random.randint(1, 3),
            'team2_tank_count': random.randint(0, 2),
            
            # Features de early/mid/late game
            'early_game_lead': random.uniform(-1, 1),
            'mid_game_lead': random.uniform(-1, 1),
            'late_game_scaling': random.uniform(-1, 1),
            
            # Timestamp para análise temporal
            'timestamp': match['date']
        }
        
        processed_data.append(features)
    
    return processed_data

def main():
    """Função principal"""
    print("🔄 Processando dados simulados para teste...")
    
    # Processar dados
    processed_data = process_simulated_data()
    
    # Salvar dados processados
    output_file = 'data/processed_match_data.json'
    with open(output_file, 'w') as f:
        json.dump(processed_data, f, indent=2, ensure_ascii=False)
    
    print(f"✅ {len(processed_data)} registros processados e salvos em {output_file}")
    
    # Estatísticas dos dados
    total_matches = len(processed_data)
    team1_wins = sum(1 for match in processed_data if match['team1_win'] == 1)
    team1_win_rate = team1_wins / total_matches
    
    print(f"📊 Estatísticas dos dados:")
    print(f"   • Total de partidas: {total_matches}")
    print(f"   • Vitórias do time 1: {team1_wins} ({team1_win_rate:.1%})")
    print(f"   • Vitórias do time 2: {total_matches - team1_wins} ({1-team1_win_rate:.1%})")
    
    # Features disponíveis
    feature_count = len([k for k in processed_data[0].keys() if k not in ['match_id', 'team1_win', 'timestamp']])
    print(f"   • Features disponíveis: {feature_count}")
    
    print(f"\n✅ Dados de teste criados com sucesso!")

if __name__ == "__main__":
    main() 