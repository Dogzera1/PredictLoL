#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Teste isolado da API oficial da Riot Games
"""

import asyncio
import logging
import requests
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import random

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_riot_api():
    """Testa a API oficial da Riot"""
    print("🔍 TESTE DA API OFICIAL DA RIOT GAMES")
    print("=" * 50)
    
    # Chave de API oficial da documentação
    api_key = "0TvQnueqKa5mxJntVWt0w4LpLfEkrV1Ta8rQBb9Z"
    
    headers = {
        'x-api-key': api_key,
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'application/json',
        'Accept-Language': 'pt-BR,pt;q=0.9,en;q=0.8'
    }
    
    print(f"🔑 Chave de API: {api_key}")
    print()
    
    # Endpoints para testar
    endpoints = [
        "https://esports-api.lolesports.com/persisted/gw/getLive?hl=pt-BR",
        "https://prod-relapi.ewp.gg/persisted/gw/getLive?hl=pt-BR",
        "https://esports-api.lolesports.com/persisted/gw/getSchedule?hl=pt-BR",
        "https://prod-relapi.ewp.gg/persisted/gw/getSchedule?hl=pt-BR"
    ]
    
    for i, url in enumerate(endpoints, 1):
        print(f"🌐 Teste {i}: {url}")
        
        try:
            response = requests.get(url, headers=headers, timeout=15)
            
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    print(f"   ✅ JSON válido recebido: {len(str(data))} caracteres")
                    
                    # Verificar estrutura básica
                    if 'data' in data:
                        print(f"   📊 Estrutura 'data' encontrada")
                        
                        if 'schedule' in data['data']:
                            schedule = data['schedule'] if 'schedule' in data else data['data']['schedule']
                            events = schedule.get('events', []) if isinstance(schedule, dict) else []
                            print(f"   🎮 {len(events)} eventos encontrados")
                            
                            # Mostrar alguns eventos
                            for j, event in enumerate(events[:3]):
                                print(f"      Evento {j+1}: {event.get('id', 'N/A')}")
                                if 'league' in event:
                                    league_name = event['league'].get('name', 'N/A')
                                    print(f"         Liga: {league_name}")
                                if 'state' in event:
                                    print(f"         Estado: {event['state']}")
                        else:
                            print(f"   ⚠️ Estrutura 'schedule' não encontrada")
                    else:
                        print(f"   ⚠️ Estrutura 'data' não encontrada")
                        print(f"   📋 Chaves disponíveis: {list(data.keys()) if isinstance(data, dict) else 'Não é dict'}")
                        
                except json.JSONDecodeError:
                    print(f"   ❌ Resposta não é JSON válido")
                    print(f"   📄 Primeiros 200 chars: {response.text[:200]}")
                    
            elif response.status_code == 403:
                print(f"   🔒 Acesso negado - chave de API pode estar inválida")
            elif response.status_code == 404:
                print(f"   🔍 Endpoint não encontrado")
            else:
                print(f"   ⚠️ Erro HTTP: {response.status_code}")
                print(f"   📄 Resposta: {response.text[:200]}")
                
        except requests.exceptions.Timeout:
            print(f"   ⏰ Timeout na requisição")
        except requests.exceptions.RequestException as e:
            print(f"   🌐 Erro de rede: {e}")
        except Exception as e:
            print(f"   ❌ Erro geral: {e}")
        
        print()

def main():
    """Função principal"""
    print("🚀 Iniciando teste da API oficial da Riot...")
    
    # Executar teste assíncrono
    asyncio.run(test_riot_api())
    
    print("✅ Teste concluído!")

if __name__ == "__main__":
    main() 