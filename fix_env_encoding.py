#!/usr/bin/env python3
"""
Script para corrigir problema de encoding no arquivo .env
"""
import os
import sys

def fix_env_encoding():
    """Corrige problemas de encoding no arquivo .env"""
    print("🔧 Corrigindo problema de encoding no arquivo .env...")
    
    env_file = ".env"
    
    # Verifica se arquivo .env existe
    if not os.path.exists(env_file):
        print(f"❌ Arquivo {env_file} não encontrado")
        print("✅ Criando arquivo .env vazio...")
        
        # Cria arquivo .env vazio com encoding correto
        with open(env_file, 'w', encoding='utf-8') as f:
            f.write("# Arquivo .env - Configure suas variáveis aqui\n")
            f.write("# Para Railway, use as variáveis de ambiente do dashboard\n\n")
            f.write("# TELEGRAM_BOT_TOKEN=seu_token_aqui\n")
            f.write("# TELEGRAM_ADMIN_USER_IDS=seu_id_aqui\n")
        
        print("✅ Arquivo .env criado com encoding UTF-8")
        return
    
    # Tenta ler arquivo existente
    print(f"📄 Arquivo {env_file} encontrado")
    
    try:
        # Tenta ler com UTF-8 primeiro
        with open(env_file, 'r', encoding='utf-8') as f:
            content = f.read()
        print("✅ Arquivo já está em UTF-8")
        
    except UnicodeDecodeError:
        print("⚠️ Arquivo tem problema de encoding")
        
        # Tenta outros encodings
        encodings = ['latin-1', 'cp1252', 'iso-8859-1']
        content = None
        
        for encoding in encodings:
            try:
                with open(env_file, 'r', encoding=encoding) as f:
                    content = f.read()
                print(f"✅ Conseguiu ler com encoding: {encoding}")
                break
            except UnicodeDecodeError:
                continue
        
        if content is None:
            print("❌ Não conseguiu ler o arquivo com nenhum encoding")
            print("🔧 Removendo arquivo corrompido e criando novo...")
            
            # Remove arquivo corrompido
            os.remove(env_file)
            
            # Cria novo arquivo
            with open(env_file, 'w', encoding='utf-8') as f:
                f.write("# Arquivo .env recriado - Configure suas variáveis aqui\n")
                f.write("# Para Railway, use as variáveis de ambiente do dashboard\n\n")
                f.write("# TELEGRAM_BOT_TOKEN=seu_token_aqui\n")
                f.write("# TELEGRAM_ADMIN_USER_IDS=seu_id_aqui\n")
            
            print("✅ Novo arquivo .env criado com UTF-8")
            return
        
        # Reescreve arquivo com UTF-8
        print("🔧 Convertendo para UTF-8...")
        with open(env_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("✅ Arquivo convertido para UTF-8")

def main():
    """Função principal"""
    print("🔍 CORREÇÃO DE ENCODING - Arquivo .env")
    print("=" * 50)
    
    try:
        fix_env_encoding()
        
        print("\n📊 RESULTADO:")
        print("✅ Problema de encoding corrigido!")
        print("✅ Arquivo .env está pronto para uso")
        print("\n🚀 Para Railway:")
        print("   • Configure as variáveis no dashboard do Railway")
        print("   • Não é necessário arquivo .env local para deploy")
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 