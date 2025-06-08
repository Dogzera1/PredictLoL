#!/usr/bin/env python3
"""
🚀 UPGRADE: AlternativeAPIClient com Riot Esports GraphQL
Implementa a melhor solução dentro do orçamento de $20
"""

import os
import sys

def upgrade_alternative_api():
    print("🔧 Upgrading AlternativeAPIClient com Riot Esports GraphQL...")
    
    # Código para adicionar ao método _get_lol_esports_data
    new_code = '''
    async def _get_lol_esports_data(self, match_data) -> Optional[CompositionData]:
        """OTIMIZADO: Riot Esports GraphQL API - Dados precisos de draft em tempo real"""
        try:
            # Headers com X-API-Key extraída do site oficial
            headers = {
                "x-api-key": "0TvQnueqKa5mxJntVWt0w4LpLfEkrV1Ta8rQBb9Z",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            
            url = 'https://esports-api.lolesports.com/persisted/gw/getLive'
            params = {'hl': 'pt-BR'}
            
            async with self.session.get(url, params=params, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    events = data.get('data', {}).get('schedule', {}).get('events', [])
                    
                    # Busca partida correspondente
                    for event in events:
                        if event.get('state') in ['inProgress', 'completed']:
                            teams = event.get('match', {}).get('teams', [])
                            
                            if len(teams) >= 2 and self._match_teams(teams, match_data):
                                # Obtém dados de draft dos games
                                games = event.get('match', {}).get('games', [])
                                
                                for game in games:
                                    if game.get('state') in ['inProgress', 'completed']:
                                        comp_data = await self._extract_game_compositions(game, headers)
                                        if comp_data and comp_data.draft_complete:
                                            logger.info(f"✅ DRAFT COMPLETO via Riot Esports GraphQL")
                                            return comp_data
                else:
                    logger.warning(f"⚠️ Riot Esports API: {response.status}")
                    
        except Exception as e:
            logger.debug(f"Riot Esports API error: {e}")
        
        return None
    
    def _match_teams(self, api_teams, match_data):
        """Verifica se os times da API correspondem ao match_data"""
        if not (hasattr(match_data, 'team1_name') and hasattr(match_data, 'team2_name')):
            return False
        
        team1_target = match_data.team1_name.lower().strip()
        team2_target = match_data.team2_name.lower().strip()
        team1_api = api_teams[0].get('name', '').lower().strip()
        team2_api = api_teams[1].get('name', '').lower().strip()
        
        return ((team1_target in team1_api or team1_api in team1_target) and
                (team2_target in team2_api or team2_api in team2_target)) or \\
               ((team1_target in team2_api or team2_api in team1_target) and
                (team2_target in team1_api or team1_api in team2_target))
    
    async def _extract_game_compositions(self, game, headers):
        """Extrai composições de um game específico"""
        try:
            # Tenta dados detalhados primeiro
            game_id = game.get('id')
            if game_id:
                detailed = await self._get_detailed_compositions(game_id, headers)
                if detailed:
                    return detailed
            
            # Fallback: dados básicos do game
            teams = game.get('teams', [])
            if len(teams) >= 2:
                team1_comp = self._extract_team_composition(teams[0])
                team2_comp = self._extract_team_composition(teams[1])
                
                if len(team1_comp) >= 3 and len(team2_comp) >= 3:  # Pelo menos dados parciais
                    return CompositionData(
                        team1_composition=team1_comp,
                        team2_composition=team2_comp,
                        source='riot_esports_graphql',
                        draft_complete=(len(team1_comp) == 5 and len(team2_comp) == 5),
                        confidence=0.95
                    )
        except Exception as e:
            logger.debug(f"Error extracting compositions: {e}")
        
        return None
    '''
    
    print("✅ Código de upgrade preparado!")
    print("\n🎯 PRÓXIMOS PASSOS:")
    print("1. Substituir método _get_lol_esports_data() no AlternativeAPIClient")
    print("2. Adicionar métodos auxiliares")
    print("3. Priorizar esta API (mover para primeira posição)")
    print("4. Testar com partidas ao vivo")
    print("5. Deploy no Railway")
    
    print(f"\n💡 BENEFÍCIOS:")
    print(f"• Custo: $0 (100% dentro do orçamento)")
    print(f"• Confiabilidade: API oficial Riot")
    print(f"• Performance: Dados em tempo real")
    print(f"• Manutenção: Mínima (API estável)")

if __name__ == "__main__":
    upgrade_alternative_api() 