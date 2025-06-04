#!/usr/bin/env python3
"""
Teste para demonstrar cálculo de Expected Value (EV) com odds simuladas

Este teste mostra como o bot encontra EV positivo usando:
1. Odds estimadas baseadas em análise da partida
2. Probabilidades calculadas via ML + algoritmos
3. Comparação para encontrar value bets
"""

import asyncio
import os
import sys
from typing import Dict, Any
from datetime import datetime

# Adiciona o diretório atual ao path para importar módulos
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from bot.utils.logger_config import setup_logging, get_logger

# Configuração de logging para testes
logger = setup_logging(log_level="INFO", log_file=None)
test_logger = get_logger("test_ev")


def simulate_market_odds() -> Dict[str, float]:
    """Simula odds de mercado (casas de apostas)"""
    # Simula cenários diferentes de odds do mercado
    scenarios = {
        "cenario_1_equilibrado": {
            "team_a_odds": 1.85,  # 54.1% implied
            "team_b_odds": 1.95,  # 51.3% implied
            "description": "Partida equilibrada no mercado"
        },
        "cenario_2_favorito": {
            "team_a_odds": 1.45,  # 69.0% implied
            "team_b_odds": 2.75,  # 36.4% implied
            "description": "Team A é favorito no mercado"
        },
        "cenario_3_underdog": {
            "team_a_odds": 2.20,  # 45.5% implied
            "team_b_odds": 1.65,  # 60.6% implied
            "description": "Team B é favorito, A é underdog"
        },
        "cenario_4_value_bet": {
            "team_a_odds": 3.20,  # 31.3% implied
            "team_b_odds": 1.33,  # 75.2% implied
            "description": "Possível value bet no underdog"
        }
    }
    
    return scenarios


def calculate_implied_probability(odds: float) -> float:
    """Calcula probabilidade implícita das odds"""
    return 1 / odds


def calculate_true_probability_via_analysis(team_a_name: str, team_b_name: str, scenario: str) -> Dict[str, float]:
    """
    Simula cálculo de probabilidade real via análise profunda
    
    Na implementação real, isso seria feito por:
    - Machine Learning com dados históricos
    - Análise de performance atual dos times
    - Fatores contextuais (meta, patches, etc.)
    """
    
    # Simula diferentes cenários de análise
    analysis_scenarios = {
        "cenario_1_equilibrado": {
            "team_a_true_prob": 0.52,  # Nossa análise dá 52% para Team A
            "analysis": "Análise mostra ligeira vantagem para Team A baseado em form atual"
        },
        "cenario_2_favorito": {
            "team_a_true_prob": 0.65,  # Nossa análise confirma favoritismo (65%)
            "analysis": "Team A realmente está em forma superior, odds corretas"
        },
        "cenario_3_underdog": {
            "team_a_true_prob": 0.55,  # Nossa análise dá 55% para o 'underdog'
            "analysis": "Team A é subestimado pelo mercado - VALOR DETECTADO!"
        },
        "cenario_4_value_bet": {
            "team_a_true_prob": 0.42,  # Nossa análise dá 42% (vs 31% implícita)
            "analysis": "Team A tem chances maiores que mercado sugere - GRANDE VALOR!"
        }
    }
    
    scenario_data = analysis_scenarios.get(scenario, {
        "team_a_true_prob": 0.50,
        "analysis": "Análise neutra"
    })
    
    return {
        "team_a_probability": scenario_data["team_a_true_prob"],
        "team_b_probability": 1 - scenario_data["team_a_true_prob"],
        "analysis_note": scenario_data["analysis"]
    }


def calculate_expected_value(true_probability: float, market_odds: float) -> float:
    """
    Calcula Expected Value (EV)
    
    Fórmula: EV = (True_Probability × Odds) - 1
    
    Se EV > 0: Aposta tem valor positivo
    Se EV < 0: Aposta tem valor negativo
    """
    ev = (true_probability * market_odds) - 1
    return ev * 100  # Retorna em percentual


def simulate_bot_analysis():
    """Simula processo completo de análise do bot"""
    print("🤖 DEMONSTRAÇÃO: COMO O BOT ENCONTRA EV COM ODDS SIMULADAS")
    print("=" * 80)
    
    # 1. Obtém cenários de odds de mercado
    market_scenarios = simulate_market_odds()
    
    for scenario_name, market_data in market_scenarios.items():
        print(f"\n📊 {scenario_name.upper()}")
        print("-" * 50)
        print(f"💬 {market_data['description']}")
        
        team_a_odds = market_data['team_a_odds']
        team_b_odds = market_data['team_b_odds']
        
        # 2. Calcula probabilidades implícitas do mercado
        team_a_implied = calculate_implied_probability(team_a_odds)
        team_b_implied = calculate_implied_probability(team_b_odds)
        
        print(f"\n🏪 ODDS DO MERCADO:")
        print(f"   Team A: {team_a_odds:.2f} (implica {team_a_implied:.1%} chance)")
        print(f"   Team B: {team_b_odds:.2f} (implica {team_b_implied:.1%} chance)")
        
        # 3. Nossa análise calcula probabilidades "reais"
        true_probs = calculate_true_probability_via_analysis("Team A", "Team B", scenario_name)
        
        print(f"\n🧠 NOSSA ANÁLISE:")
        print(f"   Team A: {true_probs['team_a_probability']:.1%} chance real")
        print(f"   Team B: {true_probs['team_b_probability']:.1%} chance real")
        print(f"   💡 {true_probs['analysis_note']}")
        
        # 4. Calcula Expected Value para ambos os teams
        ev_team_a = calculate_expected_value(true_probs['team_a_probability'], team_a_odds)
        ev_team_b = calculate_expected_value(true_probs['team_b_probability'], team_b_odds)
        
        print(f"\n📈 EXPECTED VALUE (EV):")
        print(f"   Team A: {ev_team_a:+.2f}% EV")
        print(f"   Team B: {ev_team_b:+.2f}% EV")
        
        # 5. Determina se há value bet
        min_ev_threshold = 3.0  # Mínimo 3% EV para recomendar
        
        print(f"\n🎯 RECOMENDAÇÃO:")
        
        if ev_team_a >= min_ev_threshold:
            print(f"   ✅ APOSTAR EM TEAM A!")
            print(f"   💰 Odds: {team_a_odds:.2f}")
            print(f"   📊 EV: +{ev_team_a:.2f}%")
            print(f"   🔥 Motivo: Mercado subestima Team A")
            
        elif ev_team_b >= min_ev_threshold:
            print(f"   ✅ APOSTAR EM TEAM B!")
            print(f"   💰 Odds: {team_b_odds:.2f}")
            print(f"   📊 EV: +{ev_team_b:.2f}%")
            print(f"   🔥 Motivo: Mercado subestima Team B")
            
        else:
            print(f"   ❌ NENHUMA APOSTA RECOMENDADA")
            print(f"   💡 Ambos os EVs abaixo do mínimo ({min_ev_threshold}%)")
        
        print(f"\n{'='*50}")


def demonstrate_odds_estimation_process():
    """Demonstra como o bot estima odds quando não há dados reais"""
    print(f"\n🎯 DEMONSTRAÇÃO: ESTIMAÇÃO DE ODDS QUANDO NÃO HÁ DADOS REAIS")
    print("=" * 80)
    
    print("📝 PROCESSO DO BOT:")
    print("1. 📊 Analisa dados da partida em tempo real")
    print("2. 🧮 Calcula vantagens (gold, towers, dragons, etc.)")
    print("3. 🤖 Aplica ML para probabilidades")
    print("4. 💱 Converte probabilidades em odds estimadas")
    print("5. 📈 Compara com nossa análise para encontrar EV")
    
    # Simula dados de uma partida real
    match_data = {
        "team_a": "T1",
        "team_b": "Gen.G", 
        "league": "LCK",
        "game_time": 1200,  # 20 minutos
        "gold_advantage": 2500,  # T1 +2500 gold
        "tower_advantage": 2,    # T1 +2 towers
        "dragon_advantage": 1,   # T1 +1 dragon
        "kills_advantage": 3     # T1 +3 kills
    }
    
    print(f"\n🎮 EXEMPLO - PARTIDA REAL:")
    print(f"   Teams: {match_data['team_a']} vs {match_data['team_b']}")
    print(f"   Liga: {match_data['league']}")
    print(f"   Tempo: {match_data['game_time']/60:.0f} minutos")
    
    print(f"\n📊 VANTAGENS ATUAIS ({match_data['team_a']}):")
    print(f"   💰 Gold: +{match_data['gold_advantage']:,}")
    print(f"   🏗️  Torres: +{match_data['tower_advantage']}")
    print(f"   🐉 Dragões: +{match_data['dragon_advantage']}")
    print(f"   ⚔️  Kills: +{match_data['kills_advantage']}")
    
    # Simula cálculo de probabilidade baseado nas vantagens
    base_prob = 0.50
    
    # Ajustes baseados nas vantagens
    gold_impact = match_data['gold_advantage'] / 10000  # Max 10k = +10%
    tower_impact = match_data['tower_advantage'] * 0.05  # Cada torre = +5%
    dragon_impact = match_data['dragon_advantage'] * 0.03  # Cada dragão = +3%
    kills_impact = match_data['kills_advantage'] * 0.02   # Cada kill = +2%
    
    t1_probability = base_prob + gold_impact + tower_impact + dragon_impact + kills_impact
    t1_probability = max(0.20, min(0.80, t1_probability))  # Limita entre 20-80%
    
    geng_probability = 1 - t1_probability
    
    print(f"\n🧠 NOSSA ANÁLISE ML:")
    print(f"   {match_data['team_a']}: {t1_probability:.1%} chance")
    print(f"   {match_data['team_b']}: {geng_probability:.1%} chance")
    
    # Converte em odds estimadas
    t1_estimated_odds = 1 / t1_probability
    geng_estimated_odds = 1 / geng_probability
    
    print(f"\n💱 ODDS ESTIMADAS PELO BOT:")
    print(f"   {match_data['team_a']}: {t1_estimated_odds:.2f}")
    print(f"   {match_data['team_b']}: {geng_estimated_odds:.2f}")
    
    # Simula odds de mercado (se existissem)
    market_t1_odds = 1.75  # Mercado dá T1 como ligeiro favorito
    market_geng_odds = 2.05
    
    print(f"\n🏪 SE HOUVESSE ODDS DE MERCADO:")
    print(f"   {match_data['team_a']}: {market_t1_odds:.2f}")
    print(f"   {match_data['team_b']}: {market_geng_odds:.2f}")
    
    # Calcula EV comparando nossa análise com mercado hipotético
    ev_t1 = calculate_expected_value(t1_probability, market_t1_odds)
    ev_geng = calculate_expected_value(geng_probability, market_geng_odds)
    
    print(f"\n📈 EXPECTED VALUE vs MERCADO:")
    print(f"   {match_data['team_a']}: {ev_t1:+.2f}% EV")
    print(f"   {match_data['team_b']}: {ev_geng:+.2f}% EV")
    
    if ev_t1 >= 3.0:
        print(f"   ✅ VALUE BET: {match_data['team_a']} @ {market_t1_odds:.2f}")
    elif ev_geng >= 3.0:
        print(f"   ✅ VALUE BET: {match_data['team_b']} @ {market_geng_odds:.2f}")
    else:
        print(f"   ❌ Nenhum value bet detectado (EV insuficiente)")


def main():
    """Função principal"""
    print("🚀 COMO O BOT ENCONTRA EV COM ODDS SIMULADAS")
    print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    print("💡 O bot usa um sistema sofisticado para encontrar value bets mesmo")
    print("   quando não há odds reais disponíveis das casas de apostas.")
    print("\n📋 PROCESSO:")
    print("   1️⃣  Analisa dados em tempo real da partida")
    print("   2️⃣  Calcula probabilidades usando ML + algoritmos")
    print("   3️⃣  Estima odds baseado na análise") 
    print("   4️⃣  Compara com dados de mercado (quando disponíveis)")
    print("   5️⃣  Identifica discrepâncias = VALUE BETS")
    
    # Demonstração com cenários de mercado
    simulate_bot_analysis()
    
    # Demonstração de estimação de odds
    demonstrate_odds_estimation_process()
    
    print(f"\n" + "=" * 80)
    print("🎉 CONCLUSÃO: SISTEMA DE EV COM ODDS SIMULADAS")
    print("=" * 80)
    
    print("✅ O bot consegue encontrar value bets mesmo sem odds reais porque:")
    print("   • 🧠 Usa ML avançado para calcular probabilidades reais")
    print("   • 📊 Analisa dados em tempo real (gold, towers, etc.)")
    print("   • 🎯 Compara com estimativas de mercado") 
    print("   • 💰 Identifica discrepâncias = oportunidades de valor")
    
    print(f"\n💡 MÉTODOS DE COMPARAÇÃO:")
    print("   1. 📈 Odds históricas de partidas similares")
    print("   2. 🔍 Patterns de mercado em situações parecidas")
    print("   3. 🧮 Modelos estatísticos de probabilidade")
    print("   4. 🤖 Machine Learning treinado em dados históricos")
    
    print(f"\n🚀 RESULTADO: Sistema funcional para tips profissionais!")


if __name__ == "__main__":
    main() 
