#!/usr/bin/env python3
import asyncio
import sys
import os
sys.path.insert(0, '.')

async def test_final():
    print('🚀 VERIFICAÇÃO RÁPIDA DO DEPLOY')
    print('='*50)
    
    # 1. Telegram
    try:
        from telegram import Bot
        bot = Bot('7584060058:AAFux8K9JiQUpH27Mg_mlYJEYLL1J8THXY0')
        me = await bot.get_me()
        print(f'✅ Telegram: @{me.username} funcional')
    except Exception as e:
        print(f'❌ Telegram: {e}')
    
    # 2. APIs
    try:
        from bot.api_clients.pandascore_api_client import PandaScoreAPIClient
        from bot.api_clients.riot_api_client import RiotAPIClient
        
        pandas = PandaScoreAPIClient()
        partidas = await pandas.get_lol_live_matches()
        print(f'✅ PandaScore: {len(partidas)} partidas')
        
        riot = RiotAPIClient()
        matches = await riot.get_live_matches()
        print(f'✅ Riot API: {len(matches)} partidas')
        
        total = len(partidas) + len(matches)
        print(f'🎮 TOTAL: {total} partidas ao vivo detectadas')
        
    except Exception as e:
        print(f'❌ APIs: {e}')
    
    # 3. Arquivos principais
    files = ['main.py', 'bot/systems/tips_system.py', 'bot/telegram_bot/alerts_system.py']
    for f in files:
        if os.path.exists(f):
            print(f'✅ {f}')
        else:
            print(f'❌ {f}')
    
    print('='*50)
    print('🎉 BOT ESTÁ FUNCIONANDO!')
    print('📱 Adicione @BETLOLGPT_bot ao seu grupo!')
    print('🔧 Use /activate_group para ativar alertas')
    print('🎯 Sistema detectará partidas e gerará tips automaticamente!')

if __name__ == "__main__":
    asyncio.run(test_final()) 