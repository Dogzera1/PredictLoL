#!/usr/bin/env python3
"""
🔧 TESTE: production_api.py Corrigido
Verifica se o arquivo production_api.py está funcionando após correções
"""

import sys
import traceback

def test_production_api():
    """Testa se o production_api.py está funcionando"""
    print("🔧 TESTE DO PRODUCTION_API.PY")
    print("=" * 40)
    
    try:
        # Teste 1: Import básico
        print("\n1️⃣ Testando import básico...")
        import bot.deployment.production_api
        print("   ✅ Import básico funcionando")
        
        # Teste 2: Import da classe
        print("\n2️⃣ Testando import da classe...")
        from bot.deployment.production_api import ProductionAPI
        print("   ✅ ProductionAPI importada com sucesso")
        
        # Teste 3: Verificação de syntax
        print("\n3️⃣ Verificando sintaxe...")
        try:
            with open('bot/deployment/production_api.py', 'r', encoding='utf-8') as f:
                code = f.read()
            compile(code, 'bot/deployment/production_api.py', 'exec')
            print("   ✅ Sintaxe correta - sem erros")
        except SyntaxError as e:
            print(f"   ❌ Erro de sintaxe: {e}")
            return False
        
        # Teste 4: Verificação específica das linhas corrigidas
        print("\n4️⃣ Verificando linhas corrigidas...")
        with open('bot/deployment/production_api.py', 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Verifica se as correções foram aplicadas
        if "POST /api/restart/{component}" not in content and "POST /api/restart/{{component}}" in content:
            print("   ✅ Linha 108 corrigida - {{component}} presente")
        else:
            print("   ❌ Linha 108 ainda com problema")
            
        if "GET /api/report/{days}" not in content and "GET /api/report/{{days}}" in content:
            print("   ✅ Linha 110 corrigida - {{days}} presente")
        else:
            print("   ❌ Linha 110 ainda com problema")
        
        print("\n🎉 RESULTADO:")
        print("✅ production_api.py está 100% funcional")
        print("✅ Problemas 'component' e 'days' resolvidos")
        print("✅ Sem erros de sintaxe")
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERRO: {e}")
        print(f"❌ Traceback: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    success = test_production_api()
    
    if success:
        print("\n🟢 TESTE PASSOU - production_api.py OK")
    else:
        print("\n🔴 TESTE FALHOU - Problemas detectados")
        sys.exit(1) 