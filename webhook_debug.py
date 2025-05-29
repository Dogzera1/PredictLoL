#!/usr/bin/env python3

# Função webhook_v13 simplificada para substituir temporariamente
# Cole esta função no seu bot_v13_railway.py na linha da função webhook_v13 original

def webhook_v13_debug():
    """Versão simplificada para diagnosticar o problema de timeout"""
    import logging
    logger = logging.getLogger(__name__)
    
    logger.info("!!! DEBUG: FUNÇÃO WEBHOOK_V13 INICIADA !!!")
    
    try:
        from flask import request
        logger.info(f"🔷 Request V13 method: {request.method}, path: {request.path}")
        
        # Teste 1: Apenas retornar OK sem processar nada
        logger.info("🔷 Teste 1: Retornando OK sem processamento")
        return "OK", 200
        
        # Se o teste 1 funcionar, descomente gradualmente as linhas abaixo:
        
        # Teste 2: Obter dados JSON
        # update_data = request.get_json(force=True)
        # logger.info(f"🔷 Teste 2: Dados JSON obtidos: {bool(update_data)}")
        # return "OK", 200
        
        # Teste 3: Criar update object
        # if update_data:
        #     from telegram import Update as TelegramUpdate
        #     update_obj = TelegramUpdate.de_json(update_data, updater.bot)
        #     logger.info(f"🔷 Teste 3: Update object criado: {update_obj.update_id if update_obj else 'None'}")
        # return "OK", 200
        
        # Teste 4: Processar update (última etapa)
        # if update_obj:
        #     logger.info("🔷 Teste 4: Processando update...")
        #     dispatcher.process_update(update_obj)
        #     logger.info("🔷 Teste 4: Update processado com sucesso!")
        # return "OK", 200
        
    except Exception as e:
        logger.error(f"❌ Erro na função webhook debug: {e}", exc_info=True)
        return "Error", 500

def webhook_v13_teste2():
    """TESTE 2: Adicionar processamento de dados JSON"""
    try:
        from flask import request
        logger.info(f"🔷 Request V13 method: {request.method}, path: {request.path}")
        
        # Teste 2: Obter dados JSON
        update_data = request.get_json(force=True)
        logger.info(f"🔷 Teste 2: Dados JSON obtidos: {bool(update_data)}")
        logger.info(f"🔷 Teste 2: Keys: {list(update_data.keys()) if update_data else 'None'}")
        
        return "OK", 200
        
    except Exception as e:
        logger.error(f"❌ Erro no Teste 2: {e}", exc_info=True)
        return "Error", 500

def webhook_v13_teste3():
    """TESTE 3: Criar objeto Update do Telegram"""
    try:
        from flask import request
        logger.info(f"🔷 Request V13 method: {request.method}, path: {request.path}")
        
        update_data = request.get_json(force=True)
        logger.info(f"🔷 Teste 3: Dados JSON obtidos: {bool(update_data)}")
        
        if update_data:
            from telegram import Update as TelegramUpdate
            # Assumindo que 'updater' está disponível no escopo
            update_obj = TelegramUpdate.de_json(update_data, updater.bot)
            logger.info(f"🔷 Teste 3: Update object criado: {update_obj.update_id if update_obj else 'None'}")
            logger.info(f"🔷 Teste 3: Tipo de update: {type(update_obj).__name__}")
        
        return "OK", 200
        
    except Exception as e:
        logger.error(f"❌ Erro no Teste 3: {e}", exc_info=True)
        return "Error", 500

def webhook_v13_teste4():
    """TESTE 4: Processar update completo (versão final)"""
    try:
        from flask import request
        logger.info(f"🔷 Request V13 method: {request.method}, path: {request.path}")
        
        update_data = request.get_json(force=True)
        logger.info(f"🔷 Teste 4: Dados JSON obtidos: {bool(update_data)}")
        
        if update_data:
            from telegram import Update as TelegramUpdate
            update_obj = TelegramUpdate.de_json(update_data, updater.bot)
            logger.info(f"🔷 Teste 4: Update object criado: {update_obj.update_id if update_obj else 'None'}")
            
            if update_obj:
                logger.info("🔷 Teste 4: Processando update...")
                dispatcher.process_update(update_obj)
                logger.info("🔷 Teste 4: Update processado com sucesso!")
        
        return "OK", 200
        
    except Exception as e:
        logger.error(f"❌ Erro no Teste 4: {e}", exc_info=True)
        return "Error", 500

print("""
📋 INSTRUÇÕES PARA CORRIGIR O PROBLEMA DE TIMEOUT:

1. No seu arquivo bot_v13_railway.py, localize a função 'webhook_v13' atual
2. Substitua o conteúdo da função pela versão 'webhook_v13_debug' acima
3. Faça deploy no Railway
4. Execute novamente: python test_webhook.py
5. Se funcionar, vá descomentando gradualmente os testes 2, 3, 4 para identificar onde trava

OBJETIVO: Identificar exatamente qual linha está causando o timeout/deadlock

🎉 TESTE 1 DEVE ESTAR FUNCIONANDO AGORA!

📋 PRÓXIMAS ETAPAS:

1. ✅ Verifique se não há mais erro 502 nos logs
2. ✅ Teste se /start funciona no bot
3. 🔄 Se funcionar, aplique gradualmente os testes 2, 3, 4

📝 INSTRUÇÕES PARA CADA TESTE:
- Teste 2: Adiciona processamento JSON (deve funcionar)
- Teste 3: Cria objeto Update do Telegram (possível problema aqui)
- Teste 4: Processamento completo (provável causa do deadlock original)

🚨 SE ALGUM TESTE CAUSAR 502 NOVAMENTE:
- Volte para o teste anterior que funcionava
- Investigue a linha específica que causa o problema
""") 