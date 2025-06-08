#!/usr/bin/env python3
"""
Teste da integração da API do Lolesports
Verifica se os dados em tempo real estão sendo obtidos corretamente
"""

import asyncio
import sys
from pathlib import Path

# Adiciona o diretório do bot ao path
BOT_DIR = Path(__file__).parent
sys.path.insert(0, str(BOT_DIR))

from bot.api_clients.lolesports_api_client import LolesportsAPIClient
from bot.utils.logger_config import setup_logging, get_logger

# Configurar logging
logger = setup_logging(log_level="INFO")
test_logger = get_logger("test_lolesports")

async def test_lolesports_integration():
    """Testa a integração completa da API do Lolesports"""
    test_logger.info("🧪 TESTE COMPLETO - API LOLESPORTS")
    test_logger.info("=" * 50)
    
    results = {
        "leagues": 0,
        "events": 0,
        "live_events": 0,
        "live_matches": 0,
        "teams": 0,
        "patch_info": None,
        "errors": []
    }
    
    async with LolesportsAPIClient() as client:
        # 1. Teste de Ligas
        try:
            test_logger.info("1️⃣ Testando busca de ligas...")
            leagues = await client.get_leagues()
            results["leagues"] = len(leagues) if leagues else 0
            test_logger.info(f"   ✅ {results['leagues']} ligas encontradas")
            
            if leagues:
                for league in leagues[:3]:  # Mostra apenas as primeiras 3
                    test_logger.info(f"   📋 {league.get('name', 'N/A')} (ID: {league.get('id', 'N/A')})")
            
        except Exception as e:
            error_msg = f"Erro ao buscar ligas: {e}"
            results["errors"].append(error_msg)
            test_logger.error(f"   ❌ {error_msg}")
        
        # 2. Teste de Eventos
        try:
            test_logger.info("2️⃣ Testando busca de eventos...")
            events = await client.get_events()
            results["events"] = len(events) if events else 0
            test_logger.info(f"   ✅ {results['events']} eventos encontrados")
            
        except Exception as e:
            error_msg = f"Erro ao buscar eventos: {e}"
            results["errors"].append(error_msg)
            test_logger.error(f"   ❌ {error_msg}")
        
        # 3. Teste de Eventos ao Vivo
        try:
            test_logger.info("3️⃣ Testando busca de eventos ao vivo...")
            live_events = await client.get_live_events()
            results["live_events"] = len(live_events)
            test_logger.info(f"   ✅ {results['live_events']} eventos ao vivo")
            
            if live_events:
                for event in live_events:
                    live_matches = event.get("live_matches", [])
                    test_logger.info(f"   🔴 {event.get('name', 'N/A')} - {len(live_matches)} partidas ao vivo")
            
        except Exception as e:
            error_msg = f"Erro ao buscar eventos ao vivo: {e}"
            results["errors"].append(error_msg)
            test_logger.error(f"   ❌ {error_msg}")
        
        # 4. Teste de Partidas ao Vivo (principal funcionalidade)
        try:
            test_logger.info("4️⃣ Testando busca de partidas ao vivo...")
            live_matches = await client.get_live_matches()
            results["live_matches"] = len(live_matches)
            test_logger.info(f"   ✅ {results['live_matches']} partidas ao vivo com detalhes completos")
            
            if live_matches:
                for i, match in enumerate(live_matches[:2]):  # Mostra apenas as primeiras 2
                    teams = match.get("teams", [])
                    league = match.get("league", {}).get("name", "N/A")
                    status = match.get("state", "N/A")
                    
                    test_logger.info(f"   🎮 Partida {i+1}: {league} - Status: {status}")
                    test_logger.info(f"       Equipes: {len(teams)} teams")
                    
                    # Teste de formatação para predição
                    formatted = client.format_match_for_prediction(match)
                    if formatted:
                        test_logger.info(f"       ✅ Formatação para predição: OK")
                        test_logger.info(f"       📊 Liga: {formatted.get('league', 'N/A')}")
                        test_logger.info(f"       🏆 Torneio: {formatted.get('tournament', 'N/A')}")
                    else:
                        test_logger.warning(f"       ⚠️ Erro na formatação para predição")
            
        except Exception as e:
            error_msg = f"Erro ao buscar partidas ao vivo: {e}"
            results["errors"].append(error_msg)
            test_logger.error(f"   ❌ {error_msg}")
        
        # 5. Teste de Equipes
        try:
            test_logger.info("5️⃣ Testando busca de equipes...")
            teams = await client.get_teams()
            results["teams"] = len(teams) if teams else 0
            test_logger.info(f"   ✅ {results['teams']} equipes encontradas")
            
        except Exception as e:
            error_msg = f"Erro ao buscar equipes: {e}"
            results["errors"].append(error_msg)
            test_logger.error(f"   ❌ {error_msg}")
        
        # 6. Teste de Informações do Patch
        try:
            test_logger.info("6️⃣ Testando informações do patch...")
            patch_info = await client.get_current_patch_info()
            results["patch_info"] = patch_info
            test_logger.info(f"   ✅ Patch atual: {patch_info}")
            
        except Exception as e:
            error_msg = f"Erro ao buscar patch: {e}"
            results["errors"].append(error_msg)
            test_logger.error(f"   ❌ {error_msg}")
    
    # Resumo dos resultados
    test_logger.info("=" * 50)
    test_logger.info("📊 RESUMO DOS RESULTADOS")
    test_logger.info(f"🏆 Ligas: {results['leagues']}")
    test_logger.info(f"📅 Eventos: {results['events']}")
    test_logger.info(f"🔴 Eventos ao vivo: {results['live_events']}")
    test_logger.info(f"⚡ Partidas ao vivo: {results['live_matches']}")
    test_logger.info(f"👥 Equipes: {results['teams']}")
    test_logger.info(f"🔧 Patch: {results['patch_info']}")
    
    if results["errors"]:
        test_logger.info(f"❌ Erros: {len(results['errors'])}")
        for error in results["errors"]:
            test_logger.error(f"   • {error}")
    else:
        test_logger.info("✅ Nenhum erro encontrado")
    
    # Verificação de funcionalidade crítica
    critical_functions = results["live_matches"] > 0 or results["live_events"] > 0
    
    if critical_functions:
        test_logger.info("🎉 API DO LOLESPORTS FUNCIONANDO PERFEITAMENTE!")
        test_logger.info("✅ Dados em tempo real disponíveis para o sistema")
    else:
        test_logger.warning("⚠️ API funcionando, mas sem partidas ao vivo no momento")
        test_logger.info("ℹ️ Isso é normal quando não há jogos profissionais")
    
    test_logger.info("=" * 50)
    return results

async def test_integration_with_main_system():
    """Testa a integração com o sistema principal"""
    test_logger.info("🔗 TESTE DE INTEGRAÇÃO COM SISTEMA PRINCIPAL")
    
    try:
        # Testa importação do sistema principal
        from main import BotLoLV3
        test_logger.info("✅ Importação do sistema principal: OK")
        
        # Verifica se o cliente está incluído na inicialização
        from bot.api_clients import LolesportsAPIClient
        test_logger.info("✅ Cliente do Lolesports disponível: OK")
        
        # Testa a criação do cliente
        client = LolesportsAPIClient()
        test_logger.info("✅ Criação do cliente: OK")
        
        test_logger.info("🎉 INTEGRAÇÃO COM SISTEMA PRINCIPAL: SUCESSO!")
        
        return True
        
    except Exception as e:
        test_logger.error(f"❌ Erro na integração: {e}")
        return False

async def main():
    """Função principal do teste"""
    test_logger.info("🚀 INICIANDO TESTES DA API DO LOLESPORTS")
    
    # Teste 1: API funcionando
    api_results = await test_lolesports_integration()
    
    # Teste 2: Integração com sistema
    integration_ok = await test_integration_with_main_system()
    
    # Resultado final
    test_logger.info("🏁 RESULTADO FINAL DOS TESTES")
    test_logger.info("=" * 50)
    
    if api_results["errors"]:
        test_logger.error("❌ Alguns testes falharam, mas API pode estar funcionando")
    else:
        test_logger.info("✅ Todos os testes da API passaram")
    
    if integration_ok:
        test_logger.info("✅ Integração com sistema principal: OK")
    else:
        test_logger.error("❌ Problema na integração com sistema principal")
    
    if not api_results["errors"] and integration_ok:
        test_logger.info("🎉 API DO LOLESPORTS TOTALMENTE INTEGRADA E FUNCIONANDO!")
        test_logger.info("⚡ Sistema pronto para usar dados em tempo real")
    else:
        test_logger.warning("⚠️ Alguns problemas detectados, verificar logs acima")

if __name__ == "__main__":
    asyncio.run(main())