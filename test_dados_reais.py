#!/usr/bin/env python3
"""
Teste para verificar remoção de dados fictícios das funcionalidades principais
Mantendo apenas demonstrações para testes
"""

import sys
import re
import os

def test_dados_reais():
    """Testa se dados fictícios foram removidos das funcionalidades principais"""
    
    print("🔍 TESTE: Verificação de Dados Reais vs Fictícios")
    print("=" * 60)
    
    # Ler o arquivo do bot
    try:
        with open('bot_v13_railway.py', 'r', encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        print("❌ Arquivo bot_v13_railway.py não encontrado!")
        return False
    
    # Verificar se random foi removido das importações
    print("\n1. 📦 Verificando importações...")
    if "import random" in content:
        print("❌ ERRO: 'import random' ainda presente!")
        return False
    else:
        print("✅ OK: 'import random' removido")
    
    # Verificar funções principais sem dados fictícios
    print("\n2. 🚨 Verificando sistema de alertas...")
    
    # Verificar _check_live_matches
    if "random.random()" in content and "_check_live_matches" in content:
        # Verificar se random está na função de alertas
        lines = content.split('\n')
        in_check_live = False
        for line in lines:
            if "def _check_live_matches" in line:
                in_check_live = True
            elif in_check_live and "def " in line and not line.strip().startswith("#"):
                in_check_live = False
            elif in_check_live and "random.random()" in line:
                print("❌ ERRO: random.random() ainda presente em _check_live_matches!")
                return False
    
    print("✅ OK: _check_live_matches sem dados fictícios")
    
    # Verificar _check_value_opportunities
    lines = content.split('\n')
    in_check_value = False
    for line in lines:
        if "def _check_value_opportunities" in line:
            in_check_value = True
        elif in_check_value and "def " in line and not line.strip().startswith("#"):
            in_check_value = False
        elif in_check_value and "random.random()" in line:
            print("❌ ERRO: random.random() ainda presente em _check_value_opportunities!")
            return False
    
    print("✅ OK: _check_value_opportunities sem dados fictícios")
    
    # Verificar _get_scheduled_matches
    print("\n3. 📅 Verificando agenda de partidas...")
    lines = content.split('\n')
    in_scheduled = False
    has_simulation = False
    for line in lines:
        if "def _get_scheduled_matches" in line:
            in_scheduled = True
        elif in_scheduled and "def " in line and not line.strip().startswith("#"):
            in_scheduled = False
        elif in_scheduled and ("random." in line or "simular" in line.lower()):
            has_simulation = True
            break
    
    if has_simulation:
        print("❌ ERRO: _get_scheduled_matches ainda tem simulação!")
        return False
    else:
        print("✅ OK: _get_scheduled_matches sem dados fictícios")
    
    # Verificar get_live_stats
    print("\n4. 📊 Verificando estatísticas ao vivo...")
    lines = content.split('\n')
    in_live_stats = False
    has_simulation = False
    for line in lines:
        if "def get_live_stats" in line:
            in_live_stats = True
        elif in_live_stats and "def " in line and not line.strip().startswith("#"):
            in_live_stats = False
        elif in_live_stats and ("random." in line or "simular" in line.lower()):
            has_simulation = True
            break
    
    if has_simulation:
        print("❌ ERRO: get_live_stats ainda tem simulação!")
        return False
    else:
        print("✅ OK: get_live_stats sem dados fictícios")
    
    # Verificar se demonstrações foram mantidas
    print("\n5. 🎲 Verificando demonstrações...")
    if "get_demo_value_analysis" in content:
        print("✅ OK: get_demo_value_analysis mantida para demonstração")
    else:
        print("⚠️ AVISO: get_demo_value_analysis não encontrada")
    
    if "format_value_demo" in content:
        print("✅ OK: format_value_demo mantida para demonstração")
    else:
        print("⚠️ AVISO: format_value_demo não encontrada")
    
    # Verificar comentários atualizados
    print("\n6. 💬 Verificando comentários...")
    if "# TODO: Implementar integração com API real da Riot Games" in content:
        print("✅ OK: Comentários atualizados para API real")
    else:
        print("⚠️ AVISO: Comentários TODO não encontrados")
    
    # Verificar se ainda há uso de random nas funções principais
    print("\n7. 🔍 Verificação final de random...")
    
    # Funções que NÃO devem ter random
    main_functions = [
        "_check_live_matches",
        "_check_value_opportunities", 
        "_get_scheduled_matches",
        "get_live_stats",
        "partidas",
        "stats",
        "agenda"
    ]
    
    for func_name in main_functions:
        lines = content.split('\n')
        in_function = False
        for i, line in enumerate(lines):
            if f"def {func_name}" in line:
                in_function = True
            elif in_function and "def " in line and not line.strip().startswith("#"):
                in_function = False
            elif in_function and "random." in line:
                print(f"❌ ERRO: random encontrado em {func_name} na linha {i+1}")
                print(f"   Linha: {line.strip()}")
                return False
    
    print("✅ OK: Nenhum uso de random nas funções principais")
    
    print("\n" + "=" * 60)
    print("🎉 TESTE CONCLUÍDO COM SUCESSO!")
    print("✅ Todos os dados fictícios foram removidos das funcionalidades principais")
    print("✅ Demonstrações mantidas para testes")
    print("✅ Sistema preparado para dados reais da API")
    
    return True

def test_readme_updated():
    """Testa se o README foi atualizado corretamente"""
    
    print("\n🔍 TESTE: Verificação do README")
    print("=" * 60)
    
    try:
        with open('README.md', 'r', encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        print("❌ Arquivo README.md não encontrado!")
        return False
    
    # Verificar se changelog foi atualizado
    if "v3.0.1 - Dados Reais Apenas" in content:
        print("✅ OK: Changelog atualizado com v3.0.1")
    else:
        print("❌ ERRO: Changelog não atualizado")
        return False
    
    # Verificar se seção de status foi atualizada
    if "FUNCIONALIDADES PRINCIPAIS (Aguardando API Real)" in content:
        print("✅ OK: Status da API atualizado")
    else:
        print("⚠️ AVISO: Status da API pode não estar atualizado")
    
    print("✅ README verificado com sucesso!")
    return True

if __name__ == "__main__":
    print("🚀 INICIANDO TESTES DE DADOS REAIS")
    print("=" * 60)
    
    success = True
    
    # Teste principal
    if not test_dados_reais():
        success = False
    
    # Teste do README
    if not test_readme_updated():
        success = False
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 TODOS OS TESTES PASSARAM!")
        print("✅ Sistema pronto para dados reais")
        print("✅ Demonstrações funcionais mantidas")
        print("✅ Documentação atualizada")
    else:
        print("❌ ALGUNS TESTES FALHARAM!")
        print("⚠️ Verifique os erros acima")
        sys.exit(1) 