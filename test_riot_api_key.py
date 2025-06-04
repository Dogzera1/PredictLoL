#!/usr/bin/env python3
"""
Teste da Nova Chave Riot API
Verifica se a chave x-api-key: 0TvQnueqKa5mxJntVWt0w4LpLfEkrV1Ta8rQBb9Z funciona
"""

import asyncio
import os
import sys
import aiohttp
from typing import Dict, Any

# Adiciona o diretório do projeto ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configurações de ambiente
os.environ["RIOT_API_KEY"] = "0TvQnueqKa5mxJntVWt0w4LpLfEkrV1Ta8rQBb9Z"
os.environ["LOG_LEVEL"] = "INFO"

from bot.api_clients.riot_api_client import RiotAPIClient

class RiotAPITester:
    """Testador da nova chave Riot API"""
    
    def __init__(self):
        self.api_key = "0TvQnueqKa5mxJntVWt0w4LpLfEkrV1Ta8rQBb9Z"
        self.base_url = "https://esports-api.lolesports.com/persisted/gw"
        
    async def test_direct_api_call(self) -> Dict[str, Any]:
        """Testa chamada direta à API com a nova chave"""
        print("🔑 Testando chave diretamente na API...")
        
        headers = {
            "User-Agent": "LoLBotV3/3.0.0 (Professional Esports Bot)",
            "Accept": "application/json",
            "x-api-key": self.api_key
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                # Testa endpoint /getLive
                url = f"{self.base_url}/getLive"
                params = {"hl": "pt-BR"}
                
                print(f"📡 Fazendo requisição para: {url}")
                print(f"🔑 Usando chave: {self.api_key}")
                
                async with session.get(url, headers=headers, params=params) as response:
                    print(f"📊 Status: {response.status}")
                    print(f"📝 Headers resposta: {dict(response.headers)}")
                    
                    response_text = await response.text()
                    print(f"📄 Resposta (primeiros 500 chars): {response_text[:500]}")
                    
                    if response.status == 200:
                        try:
                            data = await response.json()
                            events = data.get("data", {}).get("schedule", {}).get("events", [])
                            return {
                                "success": True,
                                "status": response.status,
                                "events_count": len(events),
                                "raw_response": data
                            }
                        except Exception as e:
                            return {
                                "success": False,
                                "error": f"Erro ao parsear JSON: {e}",
                                "status": response.status,
                                "raw_response": response_text
                            }
                    else:
                        return {
                            "success": False,
                            "status": response.status,
                            "error": response_text,
                            "headers": dict(response.headers)
                        }
                        
        except Exception as e:
            return {
                "success": False,
                "error": f"Erro de conexão: {e}"
            }

    async def test_via_client(self) -> Dict[str, Any]:
        """Testa usando o cliente Riot API"""
        print("\n🤖 Testando via RiotAPIClient...")
        
        try:
            client = RiotAPIClient(api_key=self.api_key)
            
            # Health check
            health_ok = await client.health_check()
            print(f"💗 Health check: {health_ok}")
            
            # Busca partidas ao vivo
            live_matches = await client.get_live_matches()
            print(f"🎮 Partidas ao vivo: {len(live_matches)}")
            
            # Busca ligas
            leagues = await client.get_leagues()
            print(f"🏆 Ligas encontradas: {len(leagues)}")
            
            return {
                "success": True,
                "health_check": health_ok,
                "live_matches": len(live_matches),
                "leagues": len(leagues),
                "sample_matches": live_matches[:2] if live_matches else [],
                "sample_leagues": leagues[:3] if leagues else []
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Erro no cliente: {e}"
            }

    async def test_multiple_endpoints(self) -> Dict[str, Any]:
        """Testa múltiplos endpoints da API"""
        print("\n🔀 Testando múltiplos endpoints...")
        
        endpoints_to_test = [
            ("/getLive", {"hl": "pt-BR"}),
            ("/getLeagues", {"hl": "pt-BR"}),
            ("/getSchedule", {"hl": "pt-BR"}),
        ]
        
        results = {}
        
        headers = {
            "User-Agent": "LoLBotV3/3.0.0 (Professional Esports Bot)",
            "Accept": "application/json",
            "x-api-key": self.api_key
        }
        
        async with aiohttp.ClientSession() as session:
            for endpoint, params in endpoints_to_test:
                try:
                    url = f"{self.base_url}{endpoint}"
                    print(f"🔍 Testando: {endpoint}")
                    
                    async with session.get(url, headers=headers, params=params) as response:
                        results[endpoint] = {
                            "status": response.status,
                            "success": response.status == 200,
                            "error": None if response.status == 200 else await response.text()
                        }
                        
                        if response.status == 200:
                            try:
                                data = await response.json()
                                results[endpoint]["data_structure"] = list(data.keys()) if isinstance(data, dict) else type(data).__name__
                            except:
                                results[endpoint]["data_structure"] = "invalid_json"
                        
                except Exception as e:
                    results[endpoint] = {
                        "status": None,
                        "success": False,
                        "error": str(e)
                    }
        
        return results

    async def run_complete_test(self):
        """Executa teste completo da chave API"""
        print("🚀 TESTE COMPLETO DA NOVA CHAVE RIOT API")
        print("=" * 60)
        print(f"🔑 Chave testada: {self.api_key}")
        print("=" * 60)
        
        # Teste 1: Chamada direta
        print("\n📍 TESTE 1: Chamada Direta à API")
        direct_result = await self.test_direct_api_call()
        
        if direct_result["success"]:
            print("✅ Chamada direta: SUCESSO")
            print(f"   Eventos encontrados: {direct_result.get('events_count', 0)}")
        else:
            print("❌ Chamada direta: FALHA")
            print(f"   Erro: {direct_result.get('error', 'Desconhecido')}")
            print(f"   Status: {direct_result.get('status', 'N/A')}")
        
        # Teste 2: Via cliente
        print("\n📍 TESTE 2: Via RiotAPIClient")
        client_result = await self.test_via_client()
        
        if client_result["success"]:
            print("✅ Cliente: SUCESSO")
            print(f"   Health check: {client_result.get('health_check', False)}")
            print(f"   Partidas ao vivo: {client_result.get('live_matches', 0)}")
            print(f"   Ligas: {client_result.get('leagues', 0)}")
        else:
            print("❌ Cliente: FALHA")
            print(f"   Erro: {client_result.get('error', 'Desconhecido')}")
        
        # Teste 3: Múltiplos endpoints
        print("\n📍 TESTE 3: Múltiplos Endpoints")
        endpoints_result = await self.test_multiple_endpoints()
        
        for endpoint, result in endpoints_result.items():
            status_emoji = "✅" if result["success"] else "❌"
            print(f"   {status_emoji} {endpoint}: {result['status']} - {'OK' if result['success'] else result.get('error', 'Erro')}")
        
        # Resumo final
        print("\n" + "=" * 60)
        print("📋 RESUMO FINAL")
        print("=" * 60)
        
        overall_success = (
            direct_result["success"] or 
            client_result["success"] or 
            any(r["success"] for r in endpoints_result.values())
        )
        
        if overall_success:
            print("🎉 CHAVE API: FUNCIONANDO!")
            print("✅ A nova chave Riot API está operacional")
            
            if direct_result["success"]:
                print(f"📊 Dados disponíveis: {direct_result.get('events_count', 0)} eventos ao vivo")
            
            if client_result["success"] and client_result.get('health_check'):
                print("💗 Health check: PASSOU")
                
        else:
            print("❌ CHAVE API: NÃO FUNCIONANDO")
            print("⚠️  A nova chave não está operacional")
            
            # Detalhes dos erros
            if not direct_result["success"]:
                print(f"   Erro direto: {direct_result.get('error', 'Desconhecido')}")
            
            if not client_result["success"]:
                print(f"   Erro cliente: {client_result.get('error', 'Desconhecido')}")

async def main():
    """Função principal"""
    tester = RiotAPITester()
    await tester.run_complete_test()

if __name__ == "__main__":
    asyncio.run(main()) 
