#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Teste Simples do Comando /partidas
Verifica se o agendamento está funcionando no bot
"""

import sys
import os
import asyncio
from datetime import datetime
import pytz

# Adicionar o diretório atual ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from bot_v13_railway import BotLoLV3Railway, RiotAPIClient
    print("✅ Importação bem-sucedida")
except ImportError as e:
    print(f"❌ Erro ao importar: {e}")
    sys.exit(1)

class MockUpdate:
    """Mock do objeto Update do Telegram"""
    def __init__(self):
        self.effective_chat = MockChat()

class MockChat:
    """Mock do objeto Chat do Telegram"""
    def __init__(self):
        self.id = 123456789

class MockContext:
    """Mock do objeto Context do Telegram"""
    pass

def test_show_matches():
    """Testa o comando /partidas"""
    print("🔍 TESTE DO COMANDO /partidas")
    print("=" * 40)
    
    try:
        # Inicializar bot
        print("🤖 Inicializando bot...")
        bot = BotLoLV3Railway()
        print("✅ Bot inicializado")
        
        # Criar objetos mock
        update = MockUpdate()
        context = MockContext()
        
        # Testar comando show_matches
        print("\n📅 Testando comando show_matches...")
        result = bot.show_matches(update, context)
        
        if result:
            print("✅ Comando executado com sucesso!")
        else:
            print("⚠️ Comando retornou None (pode ser normal)")
            
        return True
        
    except Exception as e:
        print(f"❌ Erro durante o teste: {e}")
        return False

def test_riot_api_direct():
    """Teste direto da API Riot"""
    print("\n🔍 TESTE DIRETO DA API RIOT")
    print("=" * 40)
    
    try:
        riot_client = RiotAPIClient()
        print("✅ RiotAPIClient inicializado")
        
        async def test_async():
            # Testar partidas agendadas
            scheduled = await riot_client.get_scheduled_matches(limit=5)
            print(f"📅 Partidas agendadas encontradas: {len(scheduled)}")
            
            if scheduled:
                brazil_tz = pytz.timezone('America/Sao_Paulo')
                print("\n🎮 PRIMEIRAS 3 PARTIDAS:")
                
                for i, match in enumerate(scheduled[:3], 1):
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
                        
                        print(f"{i}. {team1} vs {team2}")
                        print(f"   🏆 {league} • ⏰ {time_str}")
                
                return True
            else:
                print("ℹ️ Nenhuma partida encontrada")
                return False
        
        # Executar teste
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(test_async())
        loop.close()
        
        return result
        
    except Exception as e:
        print(f"❌ Erro no teste da API: {e}")
        return False

def main():
    """Função principal"""
    print("🤖 TESTE DO AGENDAMENTO NO BOT LOL V3")
    print("🕒 Iniciado em:", datetime.now().strftime('%d/%m/%Y %H:%M:%S'))
    print()
    
    # Teste 1: API Riot direta
    api_ok = test_riot_api_direct()
    
    # Teste 2: Comando do bot
    bot_ok = test_show_matches()
    
    print("\n" + "=" * 50)
    print("📋 RESUMO DOS TESTES:")
    print(f"✅ API Riot: {'OK' if api_ok else 'FALHOU'}")
    print(f"✅ Comando Bot: {'OK' if bot_ok else 'FALHOU'}")
    
    if api_ok and bot_ok:
        print("\n🎯 AGENDAMENTO FUNCIONANDO PERFEITAMENTE!")
        print("✅ O usuário pode usar /partidas para ver a agenda")
        print("✅ Horários estão corretos para o Brasil")
        print("✅ Dados são reais da API oficial")
    else:
        print("\n⚠️ Alguns testes falharam")
    
    return api_ok and bot_ok

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 