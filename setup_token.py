#!/usr/bin/env python3
"""
Script para configurar o token do Telegram Bot
"""

import os
import sys

def setup_telegram_token():
    """Configura o token do Telegram de forma interativa"""
    print("🤖 CONFIGURAÇÃO DO TOKEN TELEGRAM")
    print("=" * 50)
    
    # Verificar token atual
    current_token = os.environ.get("TELEGRAM_TOKEN")
    if current_token:
        print(f"🔍 Token atual: {current_token[:10]}...{current_token[-10:] if len(current_token) > 20 else current_token}")
    else:
        print("❌ Nenhum token configurado")
    
    print("\n📋 COMO OBTER UM TOKEN VÁLIDO:")
    print("1. Abra o Telegram e procure por @BotFather")
    print("2. Digite /start para iniciar")
    print("3. Digite /newbot para criar um novo bot")
    print("4. Siga as instruções (nome do bot, username)")
    print("5. Copie o token fornecido")
    print("\nFormato do token: 1234567890:ABCdefGHIjklMNOpqrSTUvwxYZ")
    
    # Solicitar novo token
    print("\n" + "=" * 50)
    new_token = input("📝 Cole seu novo token aqui (ou Enter para cancelar): ").strip()
    
    if not new_token:
        print("❌ Configuração cancelada")
        return False
    
    # Validar formato do token
    if not validate_token_format(new_token):
        print("❌ Formato de token inválido!")
        print("✅ Formato correto: NÚMEROS:LETRAS_E_NUMEROS")
        return False
    
    # Configurar token
    if configure_token(new_token):
        print("✅ Token configurado com sucesso!")
        print("🚀 Agora você pode executar o bot normalmente")
        return True
    else:
        print("❌ Erro ao configurar token")
        return False

def validate_token_format(token):
    """Valida se o token tem o formato correto"""
    if not token:
        return False
    
    parts = token.split(":")
    if len(parts) != 2:
        return False
    
    # Primeira parte deve ser números (bot ID)
    if not parts[0].isdigit():
        return False
    
    # Segunda parte deve ter pelo menos 20 caracteres
    if len(parts[1]) < 20:
        return False
    
    return True

def configure_token(token):
    """Configura o token nas variáveis de ambiente"""
    try:
        # Para Windows
        if os.name == 'nt':
            os.system(f'setx TELEGRAM_TOKEN "{token}"')
            print("💻 Token configurado no Windows (permanente)")
        
        # Para Unix/Linux/Mac
        else:
            # Adicionar ao .bashrc ou .zshrc
            shell_config = os.path.expanduser("~/.bashrc")
            if not os.path.exists(shell_config):
                shell_config = os.path.expanduser("~/.zshrc")
            
            with open(shell_config, "a") as f:
                f.write(f'\nexport TELEGRAM_TOKEN="{token}"\n')
            
            print(f"🐧 Token adicionado a {shell_config}")
            print("⚠️ Execute: source ~/.bashrc (ou ~/.zshrc)")
        
        # Configurar para esta sessão
        os.environ["TELEGRAM_TOKEN"] = token
        print("✅ Token configurado para esta sessão")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro ao configurar: {e}")
        return False

def test_token():
    """Testa se o token atual é válido"""
    print("🧪 TESTANDO TOKEN...")
    
    token = os.environ.get("TELEGRAM_TOKEN")
    if not token:
        print("❌ Nenhum token encontrado")
        return False
    
    try:
        import asyncio
        import aiohttp
        
        async def check_token():
            url = f"https://api.telegram.org/bot{token}/getMe"
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        bot_info = data.get('result', {})
                        print(f"✅ Token válido!")
                        print(f"🤖 Bot: @{bot_info.get('username', 'N/A')}")
                        print(f"📛 Nome: {bot_info.get('first_name', 'N/A')}")
                        return True
                    else:
                        print(f"❌ Token inválido (Status: {response.status})")
                        return False
        
        return asyncio.run(check_token())
        
    except ImportError:
        print("⚠️ Dependências não encontradas para teste")
        print("💡 Execute o bot para verificar se o token funciona")
        return True
    except Exception as e:
        print(f"❌ Erro no teste: {e}")
        return False

def main():
    """Função principal"""
    print("🚀 CONFIGURADOR DE TOKEN - BOT LOL V3")
    print("=" * 50)
    
    while True:
        print("\n📋 OPÇÕES:")
        print("1. ⚙️ Configurar novo token")
        print("2. 🧪 Testar token atual") 
        print("3. 📄 Ver token atual")
        print("4. ❌ Sair")
        
        choice = input("\n👉 Escolha uma opção (1-4): ").strip()
        
        if choice == "1":
            setup_telegram_token()
        elif choice == "2":
            test_token()
        elif choice == "3":
            token = os.environ.get("TELEGRAM_TOKEN")
            if token:
                print(f"🔍 Token: {token[:15]}...{token[-10:]}")
            else:
                print("❌ Nenhum token configurado")
        elif choice == "4":
            print("👋 Até logo!")
            break
        else:
            print("❌ Opção inválida")
        
        input("\n⏸️ Pressione Enter para continuar...")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 Configuração interrompida")
        sys.exit(0)
    except Exception as e:
        print(f"\n💥 Erro: {e}")
        sys.exit(1) 