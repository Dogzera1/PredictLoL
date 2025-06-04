#!/usr/bin/env python3
"""
🔧 CORREÇÃO DIRETA: Ordem das variáveis no __init__ do bot_interface.py
Resolve o erro AttributeError: 'LoLBotV3UltraAdvanced' object has no attribute 'handlers_configured'
"""

import re

def corrigir_bot_interface():
    """Corrige a ordem das variáveis no __init__"""
    
    arquivo = "bot/telegram_bot/bot_interface.py"
    
    print("🔧 Corrigindo ordem das variáveis em bot_interface.py...")
    
    # Lê o arquivo
    with open(arquivo, 'r', encoding='utf-8') as f:
        conteudo = f.read()
    
    # Padrão a procurar e substituir
    padrao_antigo = '''        # Referências diretas aos sistemas via ScheduleManager
        self.tips_system = schedule_manager.tips_system
        self.telegram_alerts = schedule_manager.telegram_alerts
        self.pandascore_client = schedule_manager.pandascore_client
        self.riot_client = schedule_manager.riot_client
        
        # Cria aplicação do Telegram imediatamente para uso no main.py
        try:
            self.application = Application.builder().token(self.bot_token).build()
            logger.info("✅ Aplicação Telegram criada com sucesso")
            
            # Configura handlers imediatamente
            self._setup_all_handlers()
            logger.info("✅ Handlers configurados")
            
        except Exception as e:
            logger.error(f"❌ Erro ao criar aplicação Telegram: {e}")
            self.application = None
            raise
        
        # Estado do bot
        self.is_running = False
        self.handlers_configured = False  # Flag para evitar configuração dupla
        self.stats = BotStats(start_time=time.time())'''
    
    # Novo padrão corrigido
    padrao_novo = '''        # Referências diretas aos sistemas via ScheduleManager
        self.tips_system = schedule_manager.tips_system
        self.telegram_alerts = schedule_manager.telegram_alerts
        self.pandascore_client = schedule_manager.pandascore_client
        self.riot_client = schedule_manager.riot_client
        
        # Estado do bot (DEFINIDO ANTES de criar application)
        self.is_running = False
        self.handlers_configured = False  # Flag para evitar configuração dupla
        self.stats = BotStats(start_time=time.time())
        
        # Cria aplicação do Telegram imediatamente para uso no main.py
        try:
            self.application = Application.builder().token(self.bot_token).build()
            logger.info("✅ Aplicação Telegram criada com sucesso")
            
            # Configura handlers imediatamente
            self._setup_all_handlers()
            logger.info("✅ Handlers configurados")
            
        except Exception as e:
            logger.error(f"❌ Erro ao criar aplicação Telegram: {e}")
            self.application = None
            raise'''
    
    # Faz a substituição
    if padrao_antigo in conteudo:
        conteudo_corrigido = conteudo.replace(padrao_antigo, padrao_novo)
        
        # Salva o arquivo corrigido
        with open(arquivo, 'w', encoding='utf-8') as f:
            f.write(conteudo_corrigido)
        
        print("✅ Arquivo corrigido com sucesso!")
        print("🎯 Variáveis de estado movidas para ANTES da criação da application")
        return True
    else:
        print("❌ Padrão não encontrado - arquivo pode já estar corrigido")
        return False

def verificar_correcao():
    """Verifica se a correção foi aplicada corretamente"""
    
    arquivo = "bot/telegram_bot/bot_interface.py"
    
    with open(arquivo, 'r', encoding='utf-8') as f:
        conteudo = f.read()
    
    # Procura por padrões problemáticos
    linhas = conteudo.split('\n')
    
    setup_handlers_line = None
    handlers_configured_line = None
    
    for i, linha in enumerate(linhas):
        if 'self._setup_all_handlers()' in linha:
            setup_handlers_line = i + 1
        if 'self.handlers_configured = False' in linha:
            handlers_configured_line = i + 1
    
    print(f"\n📊 VERIFICAÇÃO:")
    print(f"🔍 self._setup_all_handlers() na linha: {setup_handlers_line}")
    print(f"🔍 self.handlers_configured = False na linha: {handlers_configured_line}")
    
    if handlers_configured_line and setup_handlers_line:
        if handlers_configured_line < setup_handlers_line:
            print("✅ ORDEM CORRETA: handlers_configured definido ANTES de _setup_all_handlers()")
            return True
        else:
            print("❌ ORDEM INCORRETA: handlers_configured definido DEPOIS de _setup_all_handlers()")
            return False
    else:
        print("❌ Não foi possível localizar as linhas")
        return False

if __name__ == "__main__":
    print("🔧 CORREÇÃO: Ordem das variáveis em bot_interface.py")
    print("=" * 60)
    
    # Faz a correção
    success = corrigir_bot_interface()
    
    if success:
        # Verifica se deu certo
        verificacao = verificar_correcao()
        
        if verificacao:
            print("\n🎉 CORREÇÃO APLICADA COM SUCESSO!")
            print("✅ Problema do AttributeError resolvido")
            print("🚀 Bot interface deve funcionar corretamente agora")
        else:
            print("\n⚠️ Correção pode não ter sido aplicada corretamente")
    else:
        print("\n🤔 Arquivo pode já estar correto")
        verificar_correcao() 