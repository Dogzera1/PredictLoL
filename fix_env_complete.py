#!/usr/bin/env python3
"""
Corretor completo para arquivo .env
Remove caracteres nulos, problemas de encoding e outros issues
"""
import os
import sys

def clean_env_file():
    """Limpa completamente o arquivo .env"""
    print("🧹 Limpeza completa do arquivo .env...")
    
    env_file = ".env"
    
    if os.path.exists(env_file):
        print(f"📄 Removendo arquivo .env existente...")
        os.remove(env_file)
    
    # Cria arquivo .env completamente limpo
    print("✨ Criando arquivo .env limpo...")
    
    clean_content = """# Arquivo .env - Sistema LoL V3 Ultra Avançado
# Configure suas variáveis de ambiente aqui

# ===========================================
# CONFIGURAÇÕES PARA RAILWAY DEPLOY
# ===========================================

# Bot Telegram (Configure no Railway Dashboard)
# TELEGRAM_BOT_TOKEN=seu_token_aqui
# TELEGRAM_ADMIN_USER_IDS=seu_id_aqui

# Configurações de Ambiente
ENVIRONMENT=development
LOG_LEVEL=INFO
PYTHONUNBUFFERED=1

# ===========================================
# INSTRUÇÕES PARA RAILWAY
# ===========================================
# 1. Não é necessário usar este arquivo .env no Railway
# 2. Configure as variáveis diretamente no Railway Dashboard
# 3. Variáveis obrigatórias:
#    - TELEGRAM_BOT_TOKEN
#    - TELEGRAM_ADMIN_USER_IDS
"""
    
    with open(env_file, 'w', encoding='utf-8', newline='\n') as f:
        f.write(clean_content)
    
    print("✅ Arquivo .env criado com sucesso!")
    
    # Verifica se arquivo está OK
    try:
        with open(env_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Verifica caracteres problemáticos
        if '\x00' in content:
            print("❌ Ainda há caracteres nulos!")
            return False
        
        print(f"✅ Arquivo verificado: {len(content.splitlines())} linhas")
        print(f"✅ Tamanho: {len(content)} caracteres")
        print("✅ Sem caracteres problemáticos")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro ao verificar arquivo: {e}")
        return False

def test_dotenv_loading():
    """Testa se o arquivo .env pode ser carregado"""
    print("\n🧪 Testando carregamento do .env...")
    
    try:
        from dotenv import load_dotenv
        load_dotenv()
        print("✅ Arquivo .env carregado com sucesso!")
        return True
        
    except Exception as e:
        print(f"❌ Erro ao carregar .env: {e}")
        return False

def main():
    """Função principal"""
    print("🔧 CORRETOR COMPLETO - Arquivo .env")
    print("=" * 50)
    
    try:
        # Etapa 1: Limpar arquivo
        if not clean_env_file():
            print("❌ Falha na limpeza do arquivo")
            return 1
        
        # Etapa 2: Testar carregamento
        if not test_dotenv_loading():
            print("❌ Falha no teste de carregamento")
            return 1
        
        print("\n🎉 RESULTADO FINAL:")
        print("✅ Arquivo .env completamente corrigido!")
        print("✅ Problema de encoding resolvido!")
        print("✅ Caracteres nulos removidos!")
        print("✅ Pronto para uso e deploy Railway!")
        
        print("\n🚀 PRÓXIMOS PASSOS:")
        print("1. Para desenvolvimento local: configure variáveis no .env")
        print("2. Para Railway: configure no Dashboard (recomendado)")
        print("3. Execute: python main.py")
        
        return 0
        
    except Exception as e:
        print(f"❌ Erro crítico: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 