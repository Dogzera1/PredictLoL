"""
Serviço de integração com a API de LoL Esports.

Fornece funções para buscar partidas ao vivo, status e detalhes de eventos.
"""

import requests
import logging
import json
from datetime import datetime
import sys
import os

# Adicionar diretório raiz ao path para importar de config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import RIOT_API_KEY, RIOT_API_BASE_URL, TWITCH_URL

# Configuração de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def _make_request(endpoint, params=None):
    """
    Faz requisição à API Lolesports
    
    Args:
        endpoint: Endpoint da API
        params: Parâmetros da requisição
        
    Returns:
        Dados da resposta ou None em caso de erro
    """
    headers = {
        "x-api-key": RIOT_API_KEY,
        "Content-Type": "application/json"
    }
    
    url = f"{RIOT_API_BASE_URL}/{endpoint}"
    
    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Erro ao fazer requisição para {endpoint}: {str(e)}")
        return None

def get_live_matches():
    """
    Busca partidas ao vivo na API Lolesports
    
    Returns:
        Lista de partidas ao vivo
    """
    try:
        # Tentar obter eventos ao vivo
        result = _make_request("getLive", {"hl": "pt-BR"})
        
        if not result or "data" not in result or "schedule" not in result["data"]:
            logger.warning("Resposta inválida da API ao buscar partidas ao vivo")
            return []
        
        # Extrair eventos ao vivo
        live_events = []
        events = result["data"]["schedule"]["events"]
        
        for event in events:
            # Verificar se o evento está ao vivo
            if event["state"] != "inProgress":
                continue
                
            match_data = {
                "match_id": event["id"],
                "league": event["league"]["name"],
                "tournament": event.get("tournament", {}).get("name", "Competição"),
                "teamA": event["match"]["teams"][0]["name"],
                "teamB": event["match"]["teams"][1]["name"],
                "teamA_code": event["match"]["teams"][0]["code"],
                "teamB_code": event["match"]["teams"][1]["code"],
                "start_time": event["startTime"],
                "state": event["state"],
                "stream_url": TWITCH_URL,
                "team_a_result": event["match"]["teams"][0].get("result", {}),
                "team_b_result": event["match"]["teams"][1].get("result", {})
            }
            
            # Tentar obter detalhes adicionais da partida
            match_details = get_match_details(event["id"])
            if match_details:
                match_data.update(match_details)
                
            live_events.append(match_data)
            
        return live_events
    except Exception as e:
        logger.error(f"Erro ao processar partidas ao vivo: {str(e)}")
        return []

def get_match_details(match_id):
    """
    Busca detalhes de uma partida específica
    
    Args:
        match_id: ID da partida
        
    Returns:
        Detalhes da partida ou None em caso de erro
    """
    try:
        # Buscar detalhes do evento
        result = _make_request("getEventDetails", {"id": match_id})
        
        if not result or "data" not in result or "event" not in result["data"]:
            logger.warning(f"Resposta inválida da API ao buscar detalhes da partida {match_id}")
            return None
            
        event = result["data"]["event"]
        match = event["match"]
        
        # Extrair os games da partida
        games = match.get("games", [])
        current_game = None
        
        # Encontrar o jogo atual
        for game in games:
            if game["state"] == "inProgress":
                current_game = game
                break
                
        if not current_game:
            # Se não há jogo em andamento, pegar o último jogo
            for game in games:
                if game["state"] == "completed":
                    current_game = game
                    
        # Se não há jogo corrente nem completado, retornar dados básicos
        if not current_game:
            return {
                "games": games,
                "status": "Aguardando início"
            }
            
        # Extrair composições se disponíveis
        composition_a = []
        composition_b = []
        
        if "picks" in current_game:
            for pick in current_game["picks"]:
                if pick["side"] == "blue":
                    composition_a.append(pick["champion"])
                else:
                    composition_b.append(pick["champion"])
        
        # Obter mais dados para jogo em andamento, se disponíveis
        current_game_stats = {}
        if current_game.get("state") == "inProgress" and "gameInProgressStats" in current_game:
            stats = current_game["gameInProgressStats"]
            
            current_game_stats = {
                "team_a": {
                    "gold": stats.get("blueTeamGold", 0),
                    "kills": stats.get("blueTeamKills", 0),
                    "towers": stats.get("blueTeamTowers", 0),
                    "dragons": stats.get("blueTeamDragons", []),
                    "barons": stats.get("blueTeamBarons", 0)
                },
                "team_b": {
                    "gold": stats.get("redTeamGold", 0),
                    "kills": stats.get("redTeamKills", 0),
                    "towers": stats.get("redTeamTowers", 0),
                    "dragons": stats.get("redTeamDragons", []),
                    "barons": stats.get("redTeamBarons", 0)
                },
                "game_time": stats.get("gameTime", "00:00")
            }
        
        # Montar objeto de detalhes
        details = {
            "games": games,
            "composition_a": composition_a,
            "composition_b": composition_b,
            "current_game": current_game["number"] if current_game else 1,
            "current_game_stats": current_game_stats if current_game_stats else {},
            "status": "Ao vivo" if current_game and current_game["state"] == "inProgress" else "Aguardando"
        }
        
        return details
    except Exception as e:
        logger.error(f"Erro ao processar detalhes da partida {match_id}: {str(e)}")
        return None

def get_upcoming_matches(count=5):
    """
    Busca próximas partidas agendadas
    
    Args:
        count: Número de partidas a retornar
        
    Returns:
        Lista de próximas partidas
    """
    try:
        # Obter agenda
        result = _make_request("getSchedule", {"hl": "pt-BR"})
        
        if not result or "data" not in result or "schedule" not in result["data"]:
            logger.warning("Resposta inválida da API ao buscar agenda")
            return []
            
        events = result["data"]["schedule"]["events"]
        upcoming = []
        
        # Filtrar eventos futuros
        now = datetime.now().isoformat() + "Z"
        
        for event in events:
            # Verificar se o evento é futuro e ainda não começou
            if event["state"] == "unstarted" and event["startTime"] > now:
                match_data = {
                    "match_id": event["id"],
                    "league": event["league"]["name"],
                    "tournament": event.get("tournament", {}).get("name", "Competição"),
                    "teamA": event["match"]["teams"][0]["name"],
                    "teamB": event["match"]["teams"][1]["name"],
                    "teamA_code": event["match"]["teams"][0]["code"],
                    "teamB_code": event["match"]["teams"][1]["code"],
                    "start_time": event["startTime"],
                    "state": event["state"],
                    "stream_url": TWITCH_URL
                }
                
                upcoming.append(match_data)
                
                # Limitar ao número solicitado
                if len(upcoming) >= count:
                    break
                    
        return upcoming
    except Exception as e:
        logger.error(f"Erro ao processar próximas partidas: {str(e)}")
        return []

# Função auxiliar para simular dados quando API não estiver disponível
def get_mock_live_matches():
    """
    Retorna dados mockados para teste quando API não está disponível
    
    Returns:
        Lista de partidas simuladas
    """
    return [
        {
            "match_id": "mock1",
            "league": "LCK",
            "tournament": "Summer Split",
            "teamA": "T1",
            "teamB": "GenG",
            "teamA_code": "T1",
            "teamB_code": "GEN",
            "start_time": datetime.now().isoformat(),
            "state": "inProgress",
            "stream_url": TWITCH_URL,
            "team_a_result": {"gameWins": 1},
            "team_b_result": {"gameWins": 0},
            "games": [{"number": 1, "state": "inProgress"}],
            "composition_a": ["Aatrox", "Viego", "Azir", "Jinx", "Thresh"],
            "composition_b": ["Jax", "Lee Sin", "Ahri", "Xayah", "Pyke"],
            "current_game": 1,
            "current_game_stats": {
                "team_a": {
                    "gold": 25600,
                    "kills": 8,
                    "towers": 3,
                    "dragons": ["ocean", "infernal"],
                    "barons": 0
                },
                "team_b": {
                    "gold": 23400,
                    "kills": 5,
                    "towers": 1,
                    "dragons": [],
                    "barons": 0
                },
                "game_time": "18:45"
            },
            "status": "Ao vivo"
        }
    ]

# Executar como script para testar
if __name__ == "__main__":
    print("Testando API...")
    matches = get_live_matches()
    print(f"Partidas ao vivo encontradas: {len(matches)}")
    
    if matches:
        match_id = matches[0]["match_id"]
        print(f"Detalhes da primeira partida (ID: {match_id}):")
        details = get_match_details(match_id)
        print(json.dumps(details, indent=2))
    else:
        print("Sem partidas ao vivo. Mostrando dados de exemplo:")
        mock_data = get_mock_live_matches()
        print(json.dumps(mock_data, indent=2)) 