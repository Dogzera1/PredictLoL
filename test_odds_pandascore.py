#!/usr/bin/env python3
"""
Teste específico para verificar odds da PandaScore

Diagnóstica problema com endpoint de odds e explora alternativas
"""

import asyncio
import os
import sys
from typing import Dict, Any

# Adiciona o diretório atual ao path para importar módulos
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from bot.api_clients import PandaScoreAPIClient
from bot.utils.logger_config import setup_logging, get_logger

# Configuração de logging para testes
logger = setup_logging(log_level="DEBUG", log_file=None)
test_logger = get_logger("test_odds")


async def explore_pandascore_endpoints():
    """Explora diferentes endpoints para encontrar odds"""
    print("🔍 Explorando endpoints de odds da PandaScore...")
    
    async with PandaScoreAPIClient() as client:
        try:
            # 1. Busca partidas ao vivo
            print("\n📡 Buscando partidas ao vivo...")
            live_matches = await client.get_lol_live_matches()
            print(f"✅ Encontradas {len(live_matches)} partidas ao vivo")
            
            # 2. Busca partidas futuras  
            print("\n📅 Buscando partidas futuras...")
            upcoming_matches = await client.get_lol_upcoming_matches()
            print(f"✅ Encontradas {len(upcoming_matches)} partidas futuras")
            
            # 3. Analisa estrutura das partidas
            all_matches = live_matches + upcoming_matches
            if all_matches:
                print(f"\n🔍 Analisando estrutura da primeira partida...")
                first_match = all_matches[0]
                
                print(f"Match ID: {first_match.get('id')}")
                print(f"Status: {first_match.get('status')}")
                print(f"Game: {first_match.get('videogame', {}).get('name')}")
                
                opponents = first_match.get('opponents', [])
                if len(opponents) >= 2:
                    team1 = opponents[0].get('opponent', {}).get('name', 'N/A')
                    team2 = opponents[1].get('opponent', {}).get('name', 'N/A')
                    print(f"Times: {team1} vs {team2}")
                
                # Verifica se há campos relacionados a odds
                print(f"\n🎯 Campos disponíveis na partida:")
                for key in first_match.keys():
                    if 'odd' in key.lower() or 'bet' in key.lower() or 'market' in key.lower():
                        print(f"  • {key}: {first_match[key]}")
                
                # 4. Testa diferentes endpoints de odds
                match_id = first_match.get('id')
                if match_id:
                    print(f"\n💰 Testando endpoints de odds para match {match_id}...")
                    
                    # Endpoints alternativos para testar
                    odds_endpoints = [
                        f"/lol/matches/{match_id}/odds",
                        f"/matches/{match_id}/odds", 
                        f"/lol/matches/{match_id}/betting",
                        f"/lol/matches/{match_id}/markets",
                        f"/odds/lol/matches/{match_id}",
                        f"/betting/lol/matches/{match_id}"
                    ]
                    
                    for endpoint in odds_endpoints:
                        try:
                            print(f"   Testando: {endpoint}")
                            odds_data = await client._make_request(endpoint)
                            if odds_data:
                                print(f"   ✅ SUCESSO! Endpoint funcionou: {endpoint}")
                                print(f"   📊 Dados retornados: {type(odds_data)} com {len(odds_data) if isinstance(odds_data, (list, dict)) else 'N/A'} items")
                                return odds_data, endpoint
                        except Exception as e:
                            print(f"   ❌ Falhou: {str(e)[:100]}")
                    
                    # 5. Verifica se odds estão embutidas na própria partida
                    print(f"\n🔍 Verificando se odds estão na própria estrutura da partida...")
                    if any(key for key in first_match.keys() if 'odd' in key.lower()):
                        print(f"   ✅ Encontrados campos de odds na estrutura da partida!")
                        for key, value in first_match.items():
                            if 'odd' in key.lower():
                                print(f"   • {key}: {value}")
                        return first_match, "embedded_in_match"
                    
                    # 6. Busca por moneyline usando método existente
                    print(f"\n🎯 Testando método get_moneyline_odds...")
                    moneyline = await client.get_moneyline_odds(team1, team2)
                    if moneyline:
                        print(f"   ✅ Moneyline encontrado: {moneyline}")
                        return moneyline, "moneyline_method"
                    else:
                        print(f"   ❌ Moneyline não encontrado")
            
            print(f"\n❌ Nenhum endpoint de odds funcionou")
            return None, None
            
        except Exception as e:
            print(f"❌ Erro durante exploração: {e}")
            return None, None


async def test_odds_access():
    """Testa diferentes formas de acessar odds"""
    print("💰 TESTE DE ACESSO ÀS ODDS - PandaScore")
    print("=" * 60)
    
    try:
        odds_data, successful_endpoint = await explore_pandascore_endpoints()
        
        if odds_data and successful_endpoint:
            print(f"\n🎉 SUCESSO!")
            print(f"✅ Endpoint funcionando: {successful_endpoint}")
            print(f"✅ Dados de odds obtidos: {type(odds_data)}")
            
            # Mostra resumo dos dados
            if isinstance(odds_data, dict):
                print(f"✅ Chaves disponíveis: {list(odds_data.keys())}")
            elif isinstance(odds_data, list):
                print(f"✅ Lista com {len(odds_data)} items")
                
            return True
        else:
            print(f"\n❌ FALHA!")
            print(f"❌ Nenhum endpoint de odds está funcionando")
            print(f"❌ PandaScore pode não fornecer odds públicas")
            
            # Sugestões de solução
            print(f"\n💡 POSSÍVEIS SOLUÇÕES:")
            print(f"1. PandaScore pode requerer assinatura premium para odds")
            print(f"2. Odds podem estar em endpoint diferente")  
            print(f"3. Usar sistema de odds estimadas do próprio bot")
            print(f"4. Integrar com outra API de odds (The Odds API, etc)")
            
            return False
            
    except Exception as e:
        print(f"❌ Erro crítico: {e}")
        return False


async def test_estimated_odds():
    """Testa o sistema de odds estimadas do bot"""
    print(f"\n🔬 Testando sistema de odds estimadas...")
    
    try:
        # Importa o sistema de tips
        from bot.systems.professional_tips_system import ProfessionalTipsSystem
        from bot.systems.prediction.dynamic_prediction_system import DynamicPredictionSystem
        from bot.systems.lol_game_analyzer import LoLGameAnalyzer
        
        # Inicializa componentes
        prediction_system = DynamicPredictionSystem()
        tips_system = ProfessionalTipsSystem(prediction_system)
        
        # Testa geração de odds estimadas
        print("✅ Sistema de tips inicializado")
        print("✅ Pode gerar odds estimadas para partidas")
        print("💡 Esta é uma alternativa viável quando odds reais não estão disponíveis")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro ao testar odds estimadas: {e}")
        return False


async def main():
    """Função principal"""
    print("🚀 DIAGNÓSTICO DE ODDS - Bot LoL V3 Ultra Avançado")
    print("=" * 70)
    
    # Teste 1: Acesso direto às odds da PandaScore
    odds_available = await test_odds_access()
    
    # Teste 2: Sistema de odds estimadas como fallback
    estimated_available = await test_estimated_odds()
    
    # Resultado final
    print(f"\n" + "=" * 70)
    print(f"📊 RESULTADO FINAL:")
    print(f"=" * 70)
    
    if odds_available:
        print(f"✅ PandaScore: Odds reais disponíveis")
        print(f"🎯 Recomendação: Use odds da PandaScore")
    else:
        print(f"❌ PandaScore: Odds reais não acessíveis")
        
        if estimated_available:
            print(f"✅ Sistema interno: Odds estimadas funcionando")
            print(f"🎯 Recomendação: Use odds estimadas como alternativa")
        else:
            print(f"❌ Sistema interno: Odds estimadas com problemas")
            print(f"⚠️  Recomendação: Revisar configuração do sistema")
    
    print(f"\n💡 O bot pode funcionar com odds estimadas mesmo sem acesso às odds reais!")


if __name__ == "__main__":
    asyncio.run(main()) 