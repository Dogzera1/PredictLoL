#!/usr/bin/env python3
"""
Teste das APIs do Bot LoL V3 Ultra Avançado

Script para testar conectividade e funcionalidade das APIs:
- PandaScore API (odds de esports)
- Riot/Lolesports API (dados de partidas)
"""

import asyncio
import os
import sys
from typing import Dict, Any

# Adiciona o diretório atual ao path para importar módulos
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from bot.api_clients import RiotAPIClient, PandaScoreAPIClient
from bot.utils.logger_config import setup_logging, get_logger

# Configuração de logging para testes
logger = setup_logging(log_level="DEBUG", log_file=None)
test_logger = get_logger("test_apis")


async def test_pandascore_api() -> Dict[str, Any]:
    """
    Testa a conectividade e funcionalidade do PandaScore API
    
    Returns:
        Resultado dos testes
    """
    test_logger.info("🔍 Testando PandaScore API...")
    
    results = {
        "service": "PandaScore",
        "status": "unknown",
        "health_check": False,
        "leagues": [],
        "live_matches": [],
        "upcoming_matches": [],
        "odds": [],
        "errors": []
    }
    
    try:
        # Inicializa cliente
        client = PandaScoreAPIClient()
        await client.start_session()
        
        # 1. Health Check
        test_logger.info("📡 Testando health check...")
        health_ok = await client.health_check()
        results["health_check"] = health_ok
        
        if not health_ok:
            results["status"] = "failed"
            results["errors"].append("Health check falhou")
            return results
        
        # 2. Buscar ligas de LoL
        test_logger.info("🏆 Buscando ligas de LoL...")
        leagues = await client.get_leagues()
        results["leagues"] = leagues[:3]  # Apenas as 3 primeiras
        test_logger.info(f"✅ Encontradas {len(leagues)} ligas")
        
        # 3. Buscar partidas ao vivo
        test_logger.info("⚡ Buscando partidas ao vivo...")
        live_matches = await client.get_lol_live_matches()
        results["live_matches"] = live_matches[:2]  # Apenas as 2 primeiras
        test_logger.info(f"✅ Encontradas {len(live_matches)} partidas ao vivo")
        
        # 4. Buscar partidas futuras
        test_logger.info("📅 Buscando partidas futuras...")
        upcoming_matches = await client.get_lol_upcoming_matches(hours_ahead=12)
        results["upcoming_matches"] = upcoming_matches[:2]  # Apenas as 2 primeiras
        test_logger.info(f"✅ Encontradas {len(upcoming_matches)} partidas futuras")
        
        # 5. Buscar odds se houver partidas
        all_matches = live_matches + upcoming_matches
        if all_matches:
            test_logger.info("💰 Buscando odds para partidas...")
            for match in all_matches[:1]:  # Apenas para a primeira partida
                try:
                    match_id = match.get("id")
                    if match_id:
                        odds = await client.get_match_odds(match_id)
                        if odds:
                            opponents = match.get("opponents", [])
                            team1 = opponents[0].get("opponent", {}).get("name", "N/A") if len(opponents) > 0 else "N/A"
                            team2 = opponents[1].get("opponent", {}).get("name", "N/A") if len(opponents) > 1 else "N/A"
                            
                            results["odds"].append({
                                "match_id": match_id,
                                "teams": [team1, team2],
                                "odds_available": bool(odds)
                            })
                            test_logger.info(f"✅ Odds encontradas para partida {match_id}")
                except Exception as e:
                    test_logger.warning(f"⚠️ Erro ao buscar odds para partida {match_id}: {e}")
        
        results["status"] = "success"
        test_logger.info("✅ PandaScore API funcionando corretamente!")
        
    except Exception as e:
        results["status"] = "error"
        results["errors"].append(str(e))
        test_logger.error(f"❌ Erro no PandaScore API: {e}")
    
    finally:
        try:
            await client.close_session()
        except:
            pass
    
    return results


async def test_riot_api() -> Dict[str, Any]:
    """
    Testa a conectividade e funcionalidade da Riot/Lolesports API
    
    Returns:
        Resultado dos testes
    """
    test_logger.info("🔍 Testando Riot/Lolesports API...")
    
    results = {
        "service": "Riot/Lolesports",
        "status": "unknown",
        "health_check": False,
        "leagues": [],
        "events": [],
        "live_matches": [],
        "errors": []
    }
    
    try:
        # Inicializa cliente
        client = RiotAPIClient()
        await client.start_session()
        
        # 1. Health Check
        test_logger.info("📡 Testando health check...")
        health_ok = await client.health_check()
        results["health_check"] = health_ok
        
        if not health_ok:
            results["status"] = "failed"
            results["errors"].append("Health check falhou - verifique a API key")
            await client.close_session()
            return results
        
        # 2. Buscar ligas disponíveis
        test_logger.info("🏆 Buscando ligas disponíveis...")
        try:
            leagues = await client.get_leagues()
            results["leagues"] = [
                {
                    "name": league.get("name", "N/A"),
                    "slug": league.get("slug", "N/A"),
                    "region": league.get("region", "N/A")
                } 
                for league in leagues[:5]  # Apenas as 5 primeiras
            ]
            test_logger.info(f"✅ Encontradas {len(leagues)} ligas")
        except Exception as e:
            test_logger.warning(f"⚠️ Erro ao buscar ligas: {e}")
            results["errors"].append(f"Erro ao buscar ligas: {e}")
        
        # 3. Buscar eventos/partidas
        test_logger.info("📅 Buscando eventos ativos...")
        try:
            events = await client.get_live_events()
            results["events"] = [
                {
                    "league": event.get("league", {}).get("name", "N/A"),
                    "status": event.get("status", "N/A"),
                    "teams": [team.get("name", "N/A") for team in event.get("teams", [])][:2]
                }
                for event in events[:3]  # Apenas os 3 primeiros
            ]
            test_logger.info(f"✅ Encontrados {len(events)} eventos")
        except Exception as e:
            test_logger.warning(f"⚠️ Erro ao buscar eventos: {e}")
            results["errors"].append(f"Erro ao buscar eventos: {e}")
            events = []
        
        # 4. Buscar dados ao vivo se houver eventos
        if events:
            test_logger.info("⚡ Buscando dados ao vivo...")
            for event in events[:1]:  # Apenas o primeiro evento
                try:
                    event_id = event.get("id")
                    if event_id:
                        live_data = await client.get_live_match_data(event_id)
                        if live_data:
                            results["live_matches"].append({
                                "event_id": event_id,
                                "game_state": live_data.get("gameState", "N/A"),
                                "game_time": live_data.get("gameTime", 0)
                            })
                            test_logger.info(f"✅ Dados ao vivo encontrados para evento {event_id}")
                except Exception as e:
                    test_logger.warning(f"⚠️ Erro ao buscar dados ao vivo para evento {event_id}: {e}")
        
        results["status"] = "success"
        test_logger.info("✅ Riot/Lolesports API funcionando corretamente!")
        
    except Exception as e:
        results["status"] = "error"
        results["errors"].append(str(e))
        test_logger.error(f"❌ Erro na Riot/Lolesports API: {e}")
    
    finally:
        try:
            await client.close_session()
        except:
            pass
    
    return results


def print_test_results(results: Dict[str, Any]) -> None:
    """
    Imprime os resultados dos testes de forma formatada
    
    Args:
        results: Resultados dos testes
    """
    service = results["service"]
    status = results["status"]
    
    print(f"\n{'='*60}")
    print(f"📊 RESULTADOS - {service}")
    print(f"{'='*60}")
    
    # Status geral
    status_emoji = "✅" if status == "success" else "❌" if status == "error" else "⚠️"
    print(f"Status: {status_emoji} {status.upper()}")
    print(f"Health Check: {'✅' if results['health_check'] else '❌'}")
    
    # Erros
    if results["errors"]:
        print(f"\n❌ Erros encontrados:")
        for error in results["errors"]:
            print(f"  • {error}")
    
    # Dados específicos por serviço
    if service == "PandaScore":
        print(f"\n🏆 Ligas encontradas: {len(results['leagues'])}")
        for league in results["leagues"]:
            print(f"  • {league.get('name', 'N/A')} ({league.get('slug', 'N/A')})")
        
        print(f"\n⚡ Partidas ao vivo: {len(results['live_matches'])}")
        for match in results["live_matches"]:
            opponents = match.get("opponents", [])
            team1 = opponents[0].get("opponent", {}).get("name", "N/A") if len(opponents) > 0 else "N/A"
            team2 = opponents[1].get("opponent", {}).get("name", "N/A") if len(opponents) > 1 else "N/A"
            print(f"  • {team1} vs {team2}")
        
        print(f"\n📅 Partidas futuras: {len(results['upcoming_matches'])}")
        for match in results["upcoming_matches"]:
            opponents = match.get("opponents", [])
            team1 = opponents[0].get("opponent", {}).get("name", "N/A") if len(opponents) > 0 else "N/A"
            team2 = opponents[1].get("opponent", {}).get("name", "N/A") if len(opponents) > 1 else "N/A"
            print(f"  • {team1} vs {team2}")
        
        print(f"\n💰 Odds testadas: {len(results['odds'])}")
        for odds_data in results["odds"]:
            print(f"  • {odds_data['teams'][0]} vs {odds_data['teams'][1]} - {'✅' if odds_data['odds_available'] else '❌'}")
    
    elif service == "Riot/Lolesports":
        print(f"\n🏆 Ligas encontradas: {len(results['leagues'])}")
        for league in results["leagues"]:
            print(f"  • {league['name']} ({league['region']})")
        
        print(f"\n📅 Eventos ativos: {len(results['events'])}")
        for event in results["events"]:
            teams_str = " vs ".join(event['teams']) if event['teams'] else "N/A"
            print(f"  • {event['league']}: {teams_str} ({event['status']})")
        
        print(f"\n⚡ Dados ao vivo: {len(results['live_matches'])}")
        for live_match in results["live_matches"]:
            print(f"  • Evento {live_match['event_id']}: {live_match['game_state']} ({live_match['game_time']}s)")


async def main():
    """Função principal de teste"""
    print("🚀 Iniciando testes das APIs do Bot LoL V3 Ultra Avançado...")
    print(f"🔧 Python: {sys.version}")
    print(f"📁 Diretório: {os.getcwd()}")
    
    # Testa PandaScore API
    pandascore_results = await test_pandascore_api()
    print_test_results(pandascore_results)
    
    # Testa Riot API
    riot_results = await test_riot_api()
    print_test_results(riot_results)
    
    # Resumo final
    print(f"\n{'='*60}")
    print("📋 RESUMO FINAL")
    print(f"{'='*60}")
    
    pandascore_ok = pandascore_results["status"] == "success"
    riot_ok = riot_results["status"] == "success"
    
    print(f"PandaScore API: {'✅ OK' if pandascore_ok else '❌ FALHA'}")
    print(f"Riot/Lolesports API: {'✅ OK' if riot_ok else '❌ FALHA'}")
    
    if pandascore_ok and riot_ok:
        print("\n🎉 Todas as APIs estão funcionando corretamente!")
        print("🚀 O bot está pronto para ser executado!")
    elif pandascore_ok or riot_ok:
        print("\n⚠️ Algumas APIs estão funcionando, mas outras falharam.")
        print("🔧 Verifique as configurações e chaves de API.")
        
        # Dicas específicas
        if not pandascore_ok:
            print("   📡 PandaScore: Verifique a chave API no arquivo constants.py")
        if not riot_ok:
            print("   🎮 Riot API: Chave padrão pode estar expirada ou inválida")
    else:
        print("\n❌ Todas as APIs falharam.")
        print("🔧 Verifique sua conexão com a internet e as chaves de API.")
    
    print(f"\n{'='*60}")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n🛑 Teste interrompido pelo usuário")
    except Exception as e:
        print(f"\n\n❌ Erro fatal durante os testes: {e}")
        sys.exit(1) 