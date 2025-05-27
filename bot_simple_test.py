#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BOT LOL V3 - Versão Simplificada para Teste
Apenas health check e agendamento, sem Telegram
"""

import os
import sys
import time
import asyncio
import logging
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import json
import pytz

# Flask para health check
from flask import Flask, jsonify
import aiohttp

# Configurações
PORT = int(os.getenv('PORT', 5000))

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Flask app para healthcheck
app = Flask(__name__)

@app.route('/health')
def health_check():
    """Endpoint de health check para o Railway"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'service': 'bot_lol_v3_simple_test',
        'version': 'test',
        'features': ['agendamento', 'health_check', 'riot_api']
    })

@app.route('/')
def root():
    """Endpoint raiz"""
    return jsonify({
        'message': 'BOT LOL V3 TESTE SIMPLES está funcionando!',
        'status': 'online',
        'features': {
            'agendamento': 'Sistema de agendamento de partidas',
            'health_check': 'Health check para Railway',
            'riot_api': 'API oficial da Riot Games'
        }
    })

@app.route('/partidas')
def get_partidas():
    """Endpoint para obter partidas agendadas"""
    try:
        # Criar cliente Riot
        riot_client = RiotAPIClient()
        
        # Buscar partidas
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        scheduled_matches = loop.run_until_complete(riot_client.get_scheduled_matches(limit=10))
        loop.close()
        
        # Formatar resposta
        partidas = []
        brazil_tz = pytz.timezone('America/Sao_Paulo')
        
        for match in scheduled_matches:
            teams = match.get('teams', [])
            if len(teams) >= 2:
                team1 = teams[0].get('name', 'Team 1')
                team2 = teams[1].get('name', 'Team 2')
                league = match.get('league', 'Unknown')
                
                # Formatar horário
                start_time_str = match.get('startTime', '')
                if start_time_str:
                    try:
                        start_time = datetime.fromisoformat(start_time_str.replace('Z', '+00:00'))
                        start_time_br = start_time.astimezone(brazil_tz)
                        time_str = start_time_br.strftime('%d/%m %H:%M')
                    except:
                        time_str = 'TBD'
                else:
                    time_str = 'TBD'
                
                partidas.append({
                    'team1': team1,
                    'team2': team2,
                    'league': league,
                    'horario': time_str,
                    'horario_completo': start_time_str
                })
        
        return jsonify({
            'status': 'success',
            'total_partidas': len(partidas),
            'partidas': partidas,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Erro ao buscar partidas: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

class RiotAPIClient:
    """Cliente para API da Riot Games com fallback"""
    
    def __init__(self):
        self.api_key = "0TvQnueqKa5mxJntVWt0w4LpLfEkrV1Ta8rQBb9Z"  # Chave oficial da documentação
        self.base_urls = {
            'esports': 'https://esports-api.lolesports.com/persisted/gw',
            'prod': 'https://prod-relapi.ewp.gg/persisted/gw'
        }
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'application/json',
            'Accept-Language': 'en-US,en;q=0.9',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'cross-site',
            'x-api-key': self.api_key
        }
        logger.info("🔗 RiotAPIClient inicializado - API oficial da Riot Games")
    
    async def get_scheduled_matches(self, league_ids=None, limit=15):
        """Buscar partidas agendadas da API oficial com múltiplas fontes"""
        logger.info("📅 Buscando partidas agendadas da API oficial...")
        
        # Lista de endpoints para tentar
        endpoints = [
            f"{self.base_urls['esports']}/getSchedule?hl=pt-BR",
            f"{self.base_urls['esports']}/getSchedule?hl=en-US",
            f"{self.base_urls['prod']}/getSchedule?hl=pt-BR"
        ]
        
        all_matches = []
        
        for endpoint in endpoints:
            try:
                logger.info(f"🌐 Tentando endpoint de agenda: {endpoint}")
                
                async with aiohttp.ClientSession() as session:
                    async with session.get(endpoint, headers=self.headers, timeout=15) as response:
                        if response.status == 200:
                            data = await response.json()
                            logger.info(f"✅ Resposta recebida: {len(str(data))} caracteres")
                            
                            matches = self._extract_scheduled_matches(data)
                            if matches:
                                logger.info(f"📅 {len(matches)} partidas agendadas encontradas em {endpoint}")
                                all_matches.extend(matches)
                                
                                if len(all_matches) >= limit:
                                    break
                            else:
                                logger.info(f"ℹ️ Nenhuma partida agendada encontrada em {endpoint}")
                        else:
                            logger.warning(f"⚠️ Endpoint retornou status {response.status}")
                            
            except Exception as e:
                logger.warning(f"❌ Erro no endpoint {endpoint}: {e}")
                continue
        
        # Se não encontrou partidas reais, gerar algumas simuladas
        if not all_matches:
            logger.info("🎭 Gerando partidas simuladas para demonstração")
            all_matches = self._generate_simulated_schedule(limit)
        
        # Remover duplicatas e limitar
        unique_matches = []
        seen_matches = set()
        
        for match in all_matches:
            teams = match.get('teams', [])
            if len(teams) >= 2:
                match_id = f"{teams[0].get('name', 'T1')}_{teams[1].get('name', 'T2')}"
                if match_id not in seen_matches:
                    seen_matches.add(match_id)
                    unique_matches.append(match)
                    
                    if len(unique_matches) >= limit:
                        break
        
        logger.info(f"📊 Total de {len(unique_matches)} partidas agendadas retornadas")
        return unique_matches
    
    def _extract_scheduled_matches(self, data: Dict) -> List[Dict]:
        """Extrai partidas agendadas dos dados da API"""
        matches = []
        
        try:
            # Tentar diferentes estruturas de dados
            possible_paths = [
                ['data', 'schedule', 'events'],
                ['data', 'events'],
                ['events'],
                ['data', 'schedule'],
                ['schedule'],
                ['matches'],
                ['data', 'matches'],
                ['scheduleItems']
            ]
            
            events = None
            for path in possible_paths:
                current = data
                for key in path:
                    if isinstance(current, dict) and key in current:
                        current = current[key]
                    else:
                        break
                else:
                    events = current
                    break
            
            if not events:
                return []
            
            if not isinstance(events, list):
                return []
            
            for event in events:
                if not isinstance(event, dict):
                    continue
                
                # Verificar se é uma partida futura
                status = self._extract_status(event)
                if status.lower() in ['scheduled', 'upcoming', 'unstarted', 'future']:
                    teams = self._extract_teams(event)
                    if len(teams) >= 2:
                        match = {
                            'teams': teams,
                            'league': self._extract_league_name(event),
                            'status': status,
                            'startTime': event.get('startTime', event.get('scheduledTime', '')),
                            'tournament': event.get('tournament', {}).get('name', 'Unknown Tournament')
                        }
                        matches.append(match)
            
            return matches
            
        except Exception as e:
            logger.error(f"Erro ao extrair partidas agendadas: {e}")
            return []
    
    def _extract_league_name(self, event: Dict) -> str:
        """Extrai nome da liga do evento"""
        possible_paths = [
            ['league', 'name'],
            ['tournament', 'league', 'name'],
            ['match', 'league', 'name'],
            ['leagueName'],
            ['league'],
            ['tournament', 'name']
        ]
        
        for path in possible_paths:
            current = event
            for key in path:
                if isinstance(current, dict) and key in current:
                    current = current[key]
                else:
                    break
            else:
                if isinstance(current, str):
                    return current
        
        return "Unknown League"
    
    def _extract_status(self, event: Dict) -> str:
        """Extrai status do evento"""
        possible_keys = ['status', 'state', 'matchStatus', 'gameState']
        
        for key in possible_keys:
            if key in event:
                return str(event[key])
        
        return "unknown"
    
    def _extract_teams(self, event: Dict) -> List[Dict]:
        """Extrai informações dos times"""
        teams = []
        
        # Tentar diferentes estruturas
        possible_paths = [
            ['teams'],
            ['match', 'teams'],
            ['competitors'],
            ['participants']
        ]
        
        teams_data = None
        for path in possible_paths:
            current = event
            for key in path:
                if isinstance(current, dict) and key in current:
                    current = current[key]
                else:
                    break
            else:
                teams_data = current
                break
        
        if teams_data and isinstance(teams_data, list):
            for team_data in teams_data:
                if isinstance(team_data, dict):
                    team = {
                        'name': team_data.get('name', team_data.get('teamName', 'Unknown Team')),
                        'code': team_data.get('code', team_data.get('tricode', '')),
                        'score': team_data.get('score', 0)
                    }
                    teams.append(team)
        
        return teams
    
    def _generate_simulated_schedule(self, limit: int) -> List[Dict]:
        """Gera agenda simulada para demonstração com horários do Brasil"""
        # Agenda fixa para demonstração com horários realistas
        demo_matches = [
            ('LCK', 'T1', 'GEN', 2),      # Hoje + 2 horas
            ('LCK', 'DK', 'KT', 5),       # Hoje + 5 horas  
            ('LPL', 'JDG', 'BLG', 8),     # Hoje + 8 horas
            ('LPL', 'WBG', 'TES', 12),    # Hoje + 12 horas
            ('LEC', 'G2', 'FNC', 18),     # Hoje + 18 horas
            ('LEC', 'MAD', 'VIT', 24),    # Amanhã
            ('LCS', 'C9', 'TL', 30),      # Amanhã + 6 horas
            ('LCS', 'TSM', '100T', 36),   # Amanhã + 12 horas
            ('CBLOL', 'LOUD', 'FURIA', 42), # Amanhã + 18 horas
            ('CBLOL', 'RED', 'KBM', 48),  # Depois de amanhã
        ]
        
        matches = []
        current_time = datetime.now()
        
        # Gerar partidas baseadas na lista fixa
        for i in range(min(limit, len(demo_matches))):
            league, team1, team2, hours_ahead = demo_matches[i]
            
            # Calcular horário futuro
            match_time = current_time + timedelta(hours=hours_ahead)
            
            match = {
                'teams': [
                    {'name': team1, 'code': team1[:3], 'score': 0},
                    {'name': team2, 'code': team2[:3], 'score': 0}
                ],
                'league': league,
                'status': 'scheduled',
                'startTime': match_time.isoformat() + 'Z',
                'tournament': f'{league} 2024 Split'
            }
            matches.append(match)
        
        # Ordenar por horário
        matches.sort(key=lambda x: x['startTime'])
        
        return matches

def start_flask_server():
    """Iniciar servidor Flask"""
    logger.info(f"🌐 Iniciando servidor Flask na porta {PORT}")
    app.run(host='0.0.0.0', port=PORT, debug=False)

def main():
    """Função principal"""
    try:
        logger.info("🚀 Iniciando BOT LOL V3 TESTE SIMPLES")
        logger.info(f"🌐 Servidor será iniciado na porta {PORT}")
        logger.info("🔗 Endpoints disponíveis:")
        logger.info("   • GET /health - Health check")
        logger.info("   • GET / - Status do serviço")
        logger.info("   • GET /partidas - Agenda de partidas")
        
        start_flask_server()
        
    except Exception as e:
        logger.error(f"❌ Erro crítico: {e}")

if __name__ == "__main__":
    main() 