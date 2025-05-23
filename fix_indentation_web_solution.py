#!/usr/bin/env python3
"""
Correção de Indentação Python - Baseado em Melhores Práticas Web
Fontes: GeeksforGeeks, Appuals, PEP8 Guidelines
"""

import re
import os

def fix_python_indentation_web_method():
    """
    Corrige problemas de indentação usando métodos recomendados na web
    """
    
    print("🔧 Iniciando correção de indentação (Método Web)...")
    
    # Ler arquivo original
    try:
        with open('main_v3_riot_integrated.py', 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"❌ Erro ao ler arquivo: {e}")
        return False
    
    # Backup do arquivo original
    with open('main_v3_riot_integrated_backup.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("📁 Backup criado: main_v3_riot_integrated_backup.py")
    
    # 1. CONVERTER TABS PARA ESPAÇOS (Recomendação PEP8)
    content = content.expandtabs(4)  # Converte tabs para 4 espaços
    print("✅ Tabs convertidas para espaços")
    
    # 2. REMOVER TRAILING WHITESPACE
    lines = content.split('\n')
    lines = [line.rstrip() for line in lines]
    print("✅ Espaços em branco no final removidos")
    
    # 3. CORRIGIR INDENTAÇÃO INCONSISTENTE
    corrected_lines = []
    for i, line in enumerate(lines):
        if line.strip():  # Se não for linha vazia
            # Contar espaços no início
            leading_spaces = len(line) - len(line.lstrip())
            
            # Se não é múltiplo de 4, corrigir
            if leading_spaces % 4 != 0:
                # Arredondar para o múltiplo de 4 mais próximo
                correct_spaces = (leading_spaces // 4) * 4
                if leading_spaces % 4 >= 2:
                    correct_spaces += 4
                
                # Aplicar correção
                line = ' ' * correct_spaces + line.lstrip()
                print(f"🔧 Linha {i+1}: {leading_spaces} → {correct_spaces} espaços")
        
        corrected_lines.append(line)
    
    # 4. CORRIGIR ESTRUTURAS ESPECÍFICAS PROBLEMÁTICAS
    content = '\n'.join(corrected_lines)
    
    # Corrigir blocos try sem except
    try_pattern = r'(\s*)try:\s*\n((?:\1[ ]{4}.*\n)*?)(\1)(?![ ]{4}|except|finally)'
    
    def fix_try_block(match):
        indent = match.group(1)
        try_content = match.group(2)
        after_try = match.group(3)
        
        # Adicionar except genérico se não existir
        return f"{indent}try:\n{try_content}{indent}except Exception as e:\n{indent}    logger.error(f'Erro: {{e}}')\n{after_try}"
    
    content = re.sub(try_pattern, fix_try_block, content, flags=re.MULTILINE)
    print("✅ Blocos try/except corrigidos")
    
    # 5. VALIDAR ESTRUTURA DE CLASSES E FUNÇÕES
    # Garantir que métodos de classe tenham indentação correta
    class_method_pattern = r'^(class\s+\w+.*?:)\s*\n((?:^[ ]*def\s+.*?:.*?\n(?:(?:^[ ]{8,}.*?\n)*?))*)'
    
    def fix_class_methods(match):
        class_def = match.group(1)
        methods = match.group(2)
        
        if methods:
            # Reidentar métodos com 4 espaços
            method_lines = methods.split('\n')
            fixed_methods = []
            
            for line in method_lines:
                if line.strip():
                    if line.strip().startswith('def '):
                        # Método deve ter 4 espaços
                        fixed_methods.append('    ' + line.strip())
                    elif line.strip():
                        # Conteúdo do método deve ter 8+ espaços
                        current_indent = len(line) - len(line.lstrip())
                        if current_indent < 8:
                            fixed_methods.append('        ' + line.strip())
                        else:
                            fixed_methods.append(line)
                else:
                    fixed_methods.append(line)
            
            return class_def + '\n' + '\n'.join(fixed_methods)
        
        return match.group(0)
    
    content = re.sub(class_method_pattern, fix_class_methods, content, flags=re.MULTILINE)
    print("✅ Estruturas de classe corrigidas")
    
    # 6. SALVAR ARQUIVO CORRIGIDO
    try:
        with open('main_v3_riot_integrated.py', 'w', encoding='utf-8') as f:
            f.write(content)
        print("✅ Arquivo corrigido salvo")
        return True
        
    except Exception as e:
        print(f"❌ Erro ao salvar: {e}")
        return False

def validate_python_syntax():
    """Valida se o arquivo tem sintaxe Python válida"""
    try:
        import ast
        with open('main_v3_riot_integrated.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        ast.parse(content)
        print("✅ Sintaxe Python válida!")
        return True
        
    except SyntaxError as e:
        print(f"❌ Erro de sintaxe na linha {e.lineno}: {e.msg}")
        return False
    except Exception as e:
        print(f"❌ Erro de validação: {e}")
        return False

def main():
    """Função principal com método recomendado pela web"""
    
    print("=" * 60)
    print("🐍 CORREÇÃO DE INDENTAÇÃO PYTHON - MÉTODO WEB")
    print("Baseado em: GeeksforGeeks, Appuals, PEP8")
    print("=" * 60)
    
    # Etapa 1: Corrigir indentação
    if fix_python_indentation_web_method():
        print("\n🎯 Correção de indentação concluída!")
        
        # Etapa 2: Validar sintaxe
        print("\n🔍 Validando sintaxe...")
        if validate_python_syntax():
            print("\n🎉 SUCESSO! Arquivo corrigido e validado!")
        else:
            print("\n⚠️ Arquivo corrigido mas ainda há problemas de sintaxe")
            print("💡 Recomendação: Verificar manualmente as linhas indicadas")
    else:
        print("\n❌ Falha na correção de indentação")
    
    print("\n📋 PRÓXIMOS PASSOS RECOMENDADOS:")
    print("1. Configurar IDE para mostrar espaços em branco")
    print("2. Usar 4 espaços por nível de indentação (PEP8)")
    print("3. Nunca misturar tabs e espaços")
    print("4. Ativar guias de indentação no editor")

if __name__ == "__main__":
    main() 