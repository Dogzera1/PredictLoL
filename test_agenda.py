#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Teste do sistema de agendamento de partidas
"""

import sys
import os
from datetime import datetime
import pytz

# Adicionar o diretório atual ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Importar apenas as classes necessárias
from bot_v13_railway import BotLoLV3Railway

def test_agenda():
    """Testar o sistema de agendamento"""
    print("🔍 Testando sistema de agendamento...")
    
    try:
        # Criar instância do bot (sem inicializar Telegram)
        bot = BotLoLV3Railway()
        
        # Testar método de busca de partidas agendadas
        print("📅 Buscando partidas agendadas...")
        agenda_data = bot._get_scheduled_matches()
        
        print(f"\n✅ RESULTADO DO TESTE:")
        print(f"📊 Total de partidas encontradas: {agenda_data['total_found']}")
        print(f"📅 Partidas exibidas: {len(agenda_data['matches'])}")
        print(f"🕐 Última atualização: {agenda_data['last_update']}")
        print(f"🌍 Fuso horário: {agenda_data.get('timezone', 'N/A')}")
        
        if agenda_data['matches']:
            print(f"\n🎮 PRÓXIMAS PARTIDAS:")
            for i, match in enumerate(agenda_data['matches'][:5], 1):
                status_emoji = bot._get_match_status_emoji(match['status'])
                time_info = bot._format_match_time(match['scheduled_time'])
                
                print(f"{i}. {match['team1']} vs {match['team2']}")
                print(f"   🏆 {match['league']} • {match['tournament']}")
                print(f"   ⏰ {time_info} {status_emoji}")
                print(f"   📺 {match.get('stream', 'TBD')}")
                print()
        else:
            print("\n❌ Nenhuma partida encontrada")
            if 'error' in agenda_data:
                print(f"🔍 Erro: {agenda_data['error']}")
        
        print("✅ Teste concluído com sucesso!")
        return True
        
    except Exception as e:
        print(f"❌ Erro durante o teste: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_agenda() 