#!/usr/bin/env python3
"""
Debug de Partidas Reais - Ver detalhes das partidas encontradas
"""

import asyncio
import sys
import os
import json

# Adiciona o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from bot.api_clients.riot_api_client import RiotAPIClient
    from bot.api_clients.pandascore_api_client import PandaScoreAPIClient
    from bot.utils.logger_config import get_logger
except ImportError as e:
    print(f"❌ Erro de importação: {e}")
    sys.exit(1)

logger = get_logger(__name__)


async def debug_live_matches():
    """Debug detalhado das partidas ao vivo"""
    logger.info("🔍 DEBUG: Partidas ao Vivo Encontradas")
    logger.info("=" * 60)
    
    try:
        riot_client = RiotAPIClient()
        pandascore_client = PandaScoreAPIClient()
        
        async with riot_client, pandascore_client:
            # 1. Debug Riot API
            logger.info("\n🎮 RIOT API - Partidas Encontradas:")
            logger.info("-" * 40)
            
            riot_matches = await riot_client.get_live_matches()
            logger.info(f"Total: {len(riot_matches)} partidas")
            
            for i, match in enumerate(riot_matches, 1):
                logger.info(f"\n📋 Partida {i}:")
                logger.info(f"   • Raw data: {json.dumps(match, indent=2, ensure_ascii=False)}")
                
                # Analisa estrutura
                match_id = match.get('id', 'N/A')
                logger.info(f"   • ID: {match_id}")
                
                # Verifica times
                if 'opponents' in match:
                    opponents = match['opponents']
                    logger.info(f"   • Opponents: {len(opponents)} encontrados")
                    for j, opp in enumerate(opponents):
                        team_name = opp.get('opponent', {}).get('name', 'N/A')
                        logger.info(f"     - Time {j+1}: {team_name}")
                
                # Verifica liga
                league_info = match.get('league', {})
                league_name = league_info.get('name', 'N/A') if isinstance(league_info, dict) else str(league_info)
                logger.info(f"   • Liga: {league_name}")
                
                # Verifica status
                status = match.get('status', 'N/A')
                logger.info(f"   • Status: {status}")
                
                # Teste de validação manual
                is_real = _is_real_match_manual(match)
                logger.info(f"   • É partida real? {'✅ SIM' if is_real else '❌ NÃO'}")
            
            # 2. Debug PandaScore
            logger.info(f"\n💰 PANDASCORE - Partidas Encontradas:")
            logger.info("-" * 40)
            
            pandascore_matches = await pandascore_client.get_lol_live_matches()
            logger.info(f"Total: {len(pandascore_matches)} partidas")
            
            for i, match in enumerate(pandascore_matches, 1):
                logger.info(f"\n📋 Partida {i}:")
                logger.info(f"   • Raw data: {json.dumps(match, indent=2, ensure_ascii=False)}")
                
                # Analisa estrutura
                match_id = match.get('id', 'N/A')
                logger.info(f"   • ID: {match_id}")
                
                # Verifica times
                opponents = match.get('opponents', [])
                logger.info(f"   • Opponents: {len(opponents)} encontrados")
                for j, opp in enumerate(opponents):
                    team_name = opp.get('opponent', {}).get('name', 'N/A')
                    logger.info(f"     - Time {j+1}: {team_name}")
                
                # Verifica liga
                league_info = match.get('league', {})
                league_name = league_info.get('name', 'N/A') if isinstance(league_info, dict) else str(league_info)
                logger.info(f"   • Liga: {league_name}")
                
                # Verifica status
                status = match.get('status', 'N/A')
                logger.info(f"   • Status: {status}")
                
                # Teste de validação manual
                is_real = _is_real_match_manual(match)
                logger.info(f"   • É partida real? {'✅ SIM' if is_real else '❌ NÃO'}")
                
                # Se tem odds, mostra
                if 'odds' in match:
                    logger.info(f"   • Odds disponíveis: SIM")
            
        logger.info("\n" + "=" * 60)
        logger.info("🎯 CONCLUSÕES:")
        
        total_matches = len(riot_matches) + len(pandascore_matches)
        if total_matches == 0:
            logger.info("❌ Nenhuma partida ao vivo encontrada - Normal fora de horários de jogos")
        else:
            logger.info(f"✅ {total_matches} partidas encontradas - APIs funcionando")
            logger.info("💡 Partidas só são consideradas 'reais' se:")
            logger.info("   • Têm times com nomes não-genéricos")
            logger.info("   • ID da partida não contém 'mock', 'test', etc.")
            logger.info("   • Liga é reconhecida oficialmente")
            logger.info("   • Status indica jogo ao vivo")
        
    except Exception as e:
        logger.error(f"❌ Erro no debug: {e}")
        import traceback
        traceback.print_exc()


def _is_real_match_manual(match_data: dict) -> bool:
    """Validação manual de partida real (cópia da lógica do sistema)"""
    if not isinstance(match_data, dict):
        return False
    
    # Verifica ID da partida
    match_id = str(match_data.get('id', ''))
    if any(keyword in match_id.lower() for keyword in ['mock', 'test', 'fake', 'dummy']):
        print(f"   ❌ ID suspeito: {match_id}")
        return False
    
    # Verifica nomes dos times
    opponents = match_data.get('opponents', [])
    if len(opponents) >= 2:
        team1_name = opponents[0].get('opponent', {}).get('name', '') if len(opponents) > 0 else ''
        team2_name = opponents[1].get('opponent', {}).get('name', '') if len(opponents) > 1 else ''
    else:
        # Estrutura alternativa
        team1_name = match_data.get('team1', {}).get('name', '') if isinstance(match_data.get('team1'), dict) else ''
        team2_name = match_data.get('team2', {}).get('name', '') if isinstance(match_data.get('team2'), dict) else ''
    
    # Times com nomes genéricos ou fake
    fake_team_names = ['team1', 'team2', 'teama', 'teamb', 'mock', 'test', 'fake']
    
    if (team1_name.lower() in fake_team_names or 
        team2_name.lower() in fake_team_names or
        not team1_name or not team2_name):
        print(f"   ❌ Times suspeitos: '{team1_name}' vs '{team2_name}'")
        return False
    
    # Verifica liga
    league_info = match_data.get('league', {})
    league_name = league_info.get('name', '') if isinstance(league_info, dict) else str(league_info)
    
    if not league_name or len(league_name) < 2:
        print(f"   ❌ Liga suspeita: '{league_name}'")
        return False
    
    # Se passou em todos os testes, considera real
    print(f"   ✅ Partida válida: {team1_name} vs {team2_name} ({league_name})")
    return True


if __name__ == "__main__":
    try:
        asyncio.run(debug_live_matches())
    except KeyboardInterrupt:
        print("\n🛑 Debug interrompido")
    except Exception as e:
        print(f"\n❌ Erro: {e}") 
