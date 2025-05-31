#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SCRIPT DE EMERGÊNCIA - RESET DO WEBHOOK
Para ser executado no Railway se comando /start não funcionar
"""

import os
import asyncio
import logging
from telegram import Bot
from telegram.error import TelegramError

async def emergency_webhook_reset():
    """Reset de emergência do webhook"""
    print('🚨 RESET DE EMERGÊNCIA DO WEBHOOK')
    print('=' * 40)
    
    # Token do bot
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not token:
        print('❌ TELEGRAM_BOT_TOKEN não encontrado!')
        return
    
    bot = Bot(token=token)
    
    try:
        # 1. Remover webhook atual
        print('\n1️⃣ Removendo webhook atual...')
        await bot.delete_webhook()
        print('   ✅ Webhook removido')
        
        # 2. Aguardar
        print('\n2️⃣ Aguardando 5 segundos...')
        await asyncio.sleep(5)
        
        # 3. Configurar novo webhook
        print('\n3️⃣ Configurando novo webhook...')
        
        # URL do Railway (dinâmica)
        railway_url = os.getenv('RAILWAY_URL', 'https://your-app.railway.app')
        webhook_url = f"{railway_url}/webhook"
        
        await bot.set_webhook(
            url=webhook_url,
            allowed_updates=["message", "callback_query"],
            drop_pending_updates=True
        )
        print(f'   ✅ Webhook configurado: {webhook_url}')
        
        # 4. Verificar status
        print('\n4️⃣ Verificando status...')
        webhook_info = await bot.get_webhook_info()
        print(f'   • URL: {webhook_info.url}')
        print(f'   • Pending updates: {webhook_info.pending_update_count}')
        print(f'   • Last error: {webhook_info.last_error_message or "Nenhum"}')
        
        # 5. Testar comando /start
        print('\n5️⃣ Teste do bot...')
        me = await bot.get_me()
        print(f'   ✅ Bot ativo: @{me.username}')
        
        print('\n🎉 RESET CONCLUÍDO!')
        print('🔧 Teste o comando /start agora')
        
    except TelegramError as e:
        print(f'❌ Erro do Telegram: {e}')
    except Exception as e:
        print(f'❌ Erro geral: {e}')

if __name__ == "__main__":
    # Configurar logging
    logging.basicConfig(level=logging.INFO)
    
    # Executar reset
    asyncio.run(emergency_webhook_reset()) 