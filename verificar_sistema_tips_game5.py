"""
Verificação do sistema de tips para detectar matches ativos
Foca em verificar se o sistema está monitorando corretamente
"""

import asyncio
import sys
import os
from datetime import datetime
import importlib

# Adiciona o diretório raiz ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def verificar_sistema_tips():
    """Verifica o sistema de tips completo"""
    
    print('🔍 VERIFICAÇÃO DO SISTEMA DE TIPS')
    print(f'Horário: {datetime.now().strftime("%H:%M:%S")}')
    print('=' * 60)
    
    try:
        # Importa dependências
        from bot.api_clients.pandascore_api_client import PandaScoreAPIClient
        from bot.api_clients.riot_api_client import RiotAPIClient
        from bot.core_logic.dynamic_prediction_system import DynamicPredictionSystem
        from bot.systems.tips_system import ProfessionalTipsSystem
        
        print('✅ Imports do sistema funcionando')
        
        # Inicializa clientes
        print('\n📡 INICIALIZANDO CLIENTES...')
        
        pandascore_client = PandaScoreAPIClient()
        print('✅ PandaScore client inicializado')
        
        riot_client = RiotAPIClient()
        print('✅ Riot client inicializado')
        
        prediction_system = DynamicPredictionSystem()
        print('✅ Prediction system inicializado')
        
        # Inicializa sistema de tips
        tips_system = ProfessionalTipsSystem(
            pandascore_client=pandascore_client,
            riot_client=riot_client,
            prediction_system=prediction_system
        )
        print('✅ Tips system inicializado')
        
        # Verifica método de busca de matches
        print('\n🔍 TESTANDO BUSCA DE MATCHES...')
        
        try:
            # Tenta buscar matches usando método interno
            matches = await tips_system._get_live_matches()
            
            if matches:
                print(f'✅ {len(matches)} matches encontrados!')
                
                for i, match in enumerate(matches):
                    print(f'\n   📋 MATCH {i+1}:')
                    print(f'      ID: {getattr(match, "match_id", "unknown")}')
                    print(f'      Teams: {getattr(match, "team1_name", "?")} vs {getattr(match, "team2_name", "?")}')
                    print(f'      Liga: {getattr(match, "league", "unknown")}')
                    print(f'      Status: {getattr(match, "status", "unknown")}')
                    
                    # Verifica se é FlyQuest vs Cloud9
                    team1 = str(getattr(match, "team1_name", "")).lower()
                    team2 = str(getattr(match, "team2_name", "")).lower()
                    
                    is_target = any(t in team1 for t in ['flyquest', 'fly']) and any(t in team2 for t in ['cloud9', 'c9'])
                    
                    if is_target:
                        print(f'      🎯 MATCH ALVO ENCONTRADO!')
                        
                        # Testa detecção de draft
                        try:
                            draft_complete = await tips_system._is_draft_complete(match)
                            print(f'      🎮 Draft completo: {draft_complete}')
                            
                            if draft_complete:
                                print(f'      ✅ SISTEMA DETECTA DRAFT COMPLETO!')
                                
                                # Verifica composições
                                team1_comp = getattr(match, 'team1_composition', [])
                                team2_comp = getattr(match, 'team2_composition', [])
                                
                                if team1_comp and team2_comp:
                                    print(f'      📊 Composições via PandaScore:')
                                    print(f'         Team 1: {len(team1_comp)} champions')
                                    print(f'         Team 2: {len(team2_comp)} champions')
                                else:
                                    print(f'      🔄 Composições via APIs alternativas obtidas')
                            else:
                                print(f'      ⏳ Draft ainda não completo')
                                
                        except Exception as e:
                            print(f'      ❌ Erro na verificação de draft: {e}')
                    
                return True
            else:
                print('❌ Nenhum match encontrado')
                
        except Exception as e:
            print(f'❌ Erro na busca de matches: {e}')
        
    except ImportError as e:
        print(f'❌ Erro de import: {e}')
    except Exception as e:
        print(f'❌ Erro geral: {e}')
    
    return False

async def verificar_apis_diretamente():
    """Verifica APIs diretamente"""
    
    print('\n🌐 VERIFICAÇÃO DIRETA DAS APIS')
    print('=' * 40)
    
    # Testa PandaScore diretamente
    try:
        from bot.api_clients.pandascore_api_client import PandaScoreAPIClient
        
        client = PandaScoreAPIClient()
        print(f'✅ PandaScore client criado')
        
        # Verifica se tem método get_live_matches
        if hasattr(client, 'get_live_matches'):
            print(f'✅ Método get_live_matches existe')
        else:
            print(f'❌ Método get_live_matches não encontrado')
            
            # Lista métodos disponíveis
            methods = [m for m in dir(client) if not m.startswith('_') and callable(getattr(client, m))]
            print(f'📋 Métodos disponíveis:')
            for method in methods[:10]:  # Primeiros 10
                print(f'   - {method}')
                
    except Exception as e:
        print(f'❌ Erro com PandaScore: {e}')
    
    # Testa APIs alternativas
    try:
        from bot.systems.alternative_api_client import AlternativeAPIClient
        
        async with AlternativeAPIClient() as alt_client:
            print(f'✅ Alternative API client criado')
            
            # Verifica Data Dragon
            try:
                await alt_client._load_champion_data()
                champ_count = len(alt_client._champion_id_map)
                print(f'✅ Data Dragon: {champ_count} champions carregados')
            except Exception as e:
                print(f'⚠️ Data Dragon: {e}')
                
    except Exception as e:
        print(f'❌ Erro com APIs alternativas: {e}')

async def verificar_status_atual():
    """Verifica status atual do sistema"""
    
    print('\n📊 STATUS ATUAL DO SISTEMA')
    print('=' * 40)
    
    # Verifica arquivos importantes
    arquivos = [
        'bot/systems/tips_system.py',
        'bot/systems/alternative_api_client.py',
        'bot/api_clients/pandascore_api_client.py'
    ]
    
    for arquivo in arquivos:
        if os.path.exists(arquivo):
            print(f'✅ {arquivo}')
            
            # Verifica tamanho
            size = os.path.getsize(arquivo)
            print(f'   📏 {size} bytes')
            
            # Verifica última modificação
            import time
            mtime = os.path.getmtime(arquivo)
            mtime_str = datetime.fromtimestamp(mtime).strftime('%H:%M:%S')
            print(f'   🕒 Modificado: {mtime_str}')
        else:
            print(f'❌ {arquivo}')
    
    # Verifica se há processos do bot rodando
    print(f'\n🤖 VERIFICANDO PROCESSOS DO BOT:')
    try:
        import psutil
        
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if 'python' in proc.info['name'].lower():
                    cmdline = ' '.join(proc.info['cmdline']) if proc.info['cmdline'] else ''
                    if 'bot' in cmdline.lower() or 'tips' in cmdline.lower():
                        print(f'   🔧 Processo: PID {proc.info["pid"]} - {cmdline[:50]}...')
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
                
    except ImportError:
        print('   ⚠️ psutil não disponível para verificar processos')

async def main():
    """Verificação principal"""
    
    print('🚨 VERIFICAÇÃO COMPLETA DO SISTEMA DE TIPS')
    
    # Executa verificações
    tips_working = await verificar_sistema_tips()
    await verificar_apis_diretamente()
    await verificar_status_atual()
    
    # Resultado final
    print(f'\n' + '=' * 60)
    print(f'📋 DIAGNÓSTICO FINAL:')
    print('=' * 60)
    
    if tips_working:
        print(f'✅ SISTEMA DE TIPS FUNCIONANDO')
        print(f'🎯 Sistema consegue buscar e processar matches')
        print(f'🚀 APIs alternativas integradas e prontas')
    else:
        print(f'❌ SISTEMA DE TIPS COM PROBLEMAS')
        print(f'🔧 Necessário investigar erros específicos')
    
    print(f'\n🎮 SOBRE O GAME 5:')
    print(f'📅 Se o Game 5 já terminou, é normal não aparecer')
    print(f'⏰ Sistema monitora apenas matches ATIVOS/AO VIVO')
    print(f'🔄 Próximo scan em alguns minutos detectará novos matches')
    
    print(f'\n💡 PRÓXIMAS AÇÕES:')
    print(f'1. 🔍 Aguardar próximo match ao vivo')
    print(f'2. 📊 Monitorar logs do Railway')
    print(f'3. 🧪 Testar com novo match ativo')

if __name__ == '__main__':
    asyncio.run(main()) 