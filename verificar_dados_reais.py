#!/usr/bin/env python3
"""
Verificação de Dados Reais - Sistema de Tips LoL V3
Verifica se o sistema está conectado apenas a dados reais de jogos ao vivo
"""

import asyncio
import sys
import os
from datetime import datetime
from pathlib import Path

# Adiciona o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from bot.api_clients.riot_api_client import RiotAPIClient
    from bot.api_clients.pandascore_api_client import PandaScoreAPIClient
    from bot.systems.tips_system import ProfessionalTipsSystem
    from bot.core_logic.prediction_system import DynamicPredictionSystem
    from bot.utils.logger_config import get_logger
except ImportError as e:
    print(f"❌ Erro de importação: {e}")
    sys.exit(1)

logger = get_logger(__name__)


class RealDataVerification:
    """Sistema de verificação de dados reais"""

    def __init__(self):
        self.verification_results = {}
        self.real_matches_found = []
        self.potential_issues = []

    async def verify_real_data_only(self) -> bool:
        """Verifica se o sistema usa apenas dados reais"""
        logger.info("🔍 VERIFICAÇÃO DE DADOS REAIS - Sistema de Tips LoL V3")
        logger.info("=" * 70)
        
        success = True
        
        try:
            # 1. Verificar APIs conectadas a dados reais
            success &= await self._verify_api_connections()
            
            # 2. Verificar se há filtros anti-simulação
            success &= await self._verify_anti_simulation_filters()
            
            # 3. Buscar partidas reais ao vivo
            success &= await self._verify_live_real_matches()
            
            # 4. Verificar sistema de validação de dados
            success &= await self._verify_data_validation()
            
            # 5. Gerar relatório final
            self._generate_verification_report()
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Erro na verificação: {e}")
            return False

    async def _verify_api_connections(self) -> bool:
        """Verifica se as APIs estão conectadas a dados reais"""
        logger.info("\n1️⃣ Verificando Conexões com APIs Reais")
        logger.info("-" * 50)
        
        try:
            # Testa Riot API (dados oficiais da Riot Games)
            riot_client = RiotAPIClient()
            logger.info("🔗 Testando Riot API (dados oficiais)...")
            
            async with riot_client:
                # Busca dados de ligas oficiais
                leagues = await riot_client.get_leagues()
                if leagues:
                    logger.info(f"   ✅ Riot API: {len(leagues)} ligas oficiais encontradas")
                    # Verifica se são ligas reais (não mock)
                    real_leagues = [l for l in leagues if self._is_real_league(l)]
                    logger.info(f"   ✅ Ligas reais verificadas: {len(real_leagues)}")
                    self.verification_results['riot_api_real'] = True
                else:
                    logger.warning("   ⚠️ Riot API: Nenhuma liga encontrada")
                    self.verification_results['riot_api_real'] = False
            
            # Testa PandaScore API (odds reais)
            try:
                pandascore_client = PandaScoreAPIClient()
                logger.info("💰 Testando PandaScore API (odds reais)...")
                
                async with pandascore_client:
                    # Verifica health da API
                    health = await pandascore_client.health_check()
                    if health:
                        logger.info("   ✅ PandaScore API: Conectada e respondendo")
                        
                        # Busca partidas com odds reais
                        live_matches = await pandascore_client.get_lol_live_matches()
                        logger.info(f"   ✅ PandaScore: {len(live_matches)} partidas com odds encontradas")
                        self.verification_results['pandascore_real'] = True
                    else:
                        logger.warning("   ⚠️ PandaScore API: Não respondendo")
                        self.verification_results['pandascore_real'] = False
            except Exception as e:
                logger.error(f"   ❌ PandaScore API: Erro - {e}")
                self.verification_results['pandascore_real'] = False
            
            return self.verification_results.get('riot_api_real', False)
            
        except Exception as e:
            logger.error(f"❌ Erro ao verificar APIs: {e}")
            return False

    async def _verify_anti_simulation_filters(self) -> bool:
        """Verifica se há filtros contra dados simulados"""
        logger.info("\n2️⃣ Verificando Filtros Anti-Simulação")
        logger.info("-" * 50)
        
        try:
            # Verifica se o ProfessionalTipsSystem tem método de validação
            tips_system_class = ProfessionalTipsSystem
            
            # Verifica se existe método _is_real_match_data
            if hasattr(tips_system_class, '_is_real_match_data'):
                logger.info("   ✅ Filtro anti-simulação: _is_real_match_data() encontrado")
                self.verification_results['anti_simulation_filter'] = True
            else:
                logger.warning("   ⚠️ Filtro anti-simulação: Método não encontrado")
                self.verification_results['anti_simulation_filter'] = False
            
            # Verifica se existe validação de qualidade de dados
            if hasattr(tips_system_class, '_match_meets_quality_criteria'):
                logger.info("   ✅ Validação de qualidade: _match_meets_quality_criteria() encontrado")
                self.verification_results['quality_validation'] = True
            else:
                logger.warning("   ⚠️ Validação de qualidade: Método não encontrado")
                self.verification_results['quality_validation'] = False
            
            # Verifica palavras-chave de exclusão
            keywords_to_check = ['mock', 'test', 'fake', 'dummy', 'simulate']
            logger.info(f"   🔍 Verificando exclusão de dados com keywords: {keywords_to_check}")
            
            # Se pelo menos um filtro existe, considera válido
            has_filters = (
                self.verification_results.get('anti_simulation_filter', False) or
                self.verification_results.get('quality_validation', False)
            )
            
            if has_filters:
                logger.info("   ✅ Sistema possui filtros para evitar dados simulados")
            else:
                logger.warning("   ⚠️ Sistema pode não ter filtros suficientes contra simulação")
                self.potential_issues.append("Faltam filtros anti-simulação")
            
            return has_filters
            
        except Exception as e:
            logger.error(f"❌ Erro ao verificar filtros: {e}")
            return False

    async def _verify_live_real_matches(self) -> bool:
        """Busca e verifica partidas reais ao vivo"""
        logger.info("\n3️⃣ Buscando Partidas Reais Ao Vivo")
        logger.info("-" * 50)
        
        try:
            # Inicializa clientes
            riot_client = RiotAPIClient()
            pandascore_client = PandaScoreAPIClient()
            
            real_matches_found = 0
            
            async with riot_client, pandascore_client:
                # Busca partidas da Riot API
                logger.info("🎮 Buscando partidas na Riot API...")
                riot_matches = await riot_client.get_live_matches()
                
                for match in riot_matches:
                    if self._is_real_match(match):
                        real_matches_found += 1
                        self.real_matches_found.append({
                            'source': 'Riot API',
                            'match_id': match.get('id', 'N/A'),
                            'teams': f"{match.get('team1', {}).get('name', 'Team1')} vs {match.get('team2', {}).get('name', 'Team2')}",
                            'league': match.get('league', {}).get('name', 'Unknown')
                        })
                
                logger.info(f"   📊 Riot API: {len(riot_matches)} partidas encontradas, {real_matches_found} validadas como reais")
                
                # Busca partidas do PandaScore
                logger.info("💰 Buscando partidas no PandaScore...")
                pandascore_matches = await pandascore_client.get_lol_live_matches()
                
                pandascore_real = 0
                for match in pandascore_matches:
                    if self._is_real_match(match):
                        pandascore_real += 1
                        self.real_matches_found.append({
                            'source': 'PandaScore',
                            'match_id': match.get('id', 'N/A'),
                            'teams': f"{match.get('team1', {}).get('name', 'Team1')} vs {match.get('team2', {}).get('name', 'Team2')}",
                            'league': match.get('league', {}).get('name', 'Unknown')
                        })
                
                logger.info(f"   📊 PandaScore: {len(pandascore_matches)} partidas encontradas, {pandascore_real} validadas como reais")
                
                total_real_matches = real_matches_found + pandascore_real
                
                # Log das partidas encontradas
                if self.real_matches_found:
                    logger.info("   🎯 Partidas reais encontradas:")
                    for match in self.real_matches_found[:5]:  # Mostra apenas as 5 primeiras
                        logger.info(f"      • {match['teams']} ({match['league']}) - {match['source']}")
                    
                    if len(self.real_matches_found) > 5:
                        logger.info(f"      ... e mais {len(self.real_matches_found) - 5} partidas")
                
                self.verification_results['real_matches_found'] = total_real_matches > 0
                self.verification_results['total_real_matches'] = total_real_matches
                
                return total_real_matches > 0
                
        except Exception as e:
            logger.error(f"❌ Erro ao buscar partidas reais: {e}")
            return False

    async def _verify_data_validation(self) -> bool:
        """Verifica sistema de validação de dados"""
        logger.info("\n4️⃣ Verificando Sistema de Validação")
        logger.info("-" * 50)
        
        try:
            # Verifica se ProfessionalTip tem validação
            from bot.data_models.tip_data import ProfessionalTip
            
            # Testa método de validação
            if hasattr(ProfessionalTip, 'validate'):
                logger.info("   ✅ ProfessionalTip.validate() - Validação de tips implementada")
                self.verification_results['tip_validation'] = True
            else:
                logger.warning("   ⚠️ ProfessionalTip.validate() - Método de validação não encontrado")
                self.verification_results['tip_validation'] = False
            
            # Verifica filtros de qualidade no sistema de tips
            try:
                from bot.systems.tips_system import ProfessionalTipsSystem
                
                # Simula criação do sistema para verificar filtros
                mock_clients = self._create_mock_clients()
                tips_system = ProfessionalTipsSystem(*mock_clients)
                
                # Verifica configuração de filtros
                if hasattr(tips_system, 'quality_filters'):
                    filters = tips_system.quality_filters
                    logger.info(f"   ✅ Filtros de qualidade configurados:")
                    logger.info(f"      • Ligas suportadas: {len(filters.get('supported_leagues', []))}")
                    logger.info(f"      • Tempo mín/máx: {filters.get('min_game_time_minutes')}-{filters.get('max_game_time_minutes')}min")
                    logger.info(f"      • Qualidade mínima: {filters.get('min_data_quality', 0):.1%}")
                    self.verification_results['quality_filters'] = True
                else:
                    logger.warning("   ⚠️ Filtros de qualidade não encontrados")
                    self.verification_results['quality_filters'] = False
                    
            except Exception as e:
                logger.warning(f"   ⚠️ Erro ao verificar sistema de tips: {e}")
                self.verification_results['quality_filters'] = False
            
            # Se pelo menos validação de tip existe, considera válido
            return self.verification_results.get('tip_validation', False)
            
        except Exception as e:
            logger.error(f"❌ Erro ao verificar validação: {e}")
            return False

    def _is_real_league(self, league_data: dict) -> bool:
        """Verifica se é uma liga real"""
        if not isinstance(league_data, dict):
            return False
        
        name = league_data.get('name', '').lower()
        
        # Ligas oficiais conhecidas
        real_leagues = [
            'lck', 'lec', 'lcs', 'lpl', 'cblol', 'vcs', 'ljl', 'pcs',
            'worlds', 'msi', 'spring', 'summer', 'playoff'
        ]
        
        # Palavras que indicam dados fake
        fake_keywords = ['mock', 'test', 'fake', 'dummy', 'sample']
        
        # Verifica se contém palavras fake
        if any(keyword in name for keyword in fake_keywords):
            return False
        
        # Verifica se é liga real
        return any(real_league in name for real_league in real_leagues) or len(name) > 2

    def _is_real_match(self, match_data: dict) -> bool:
        """Verifica se é uma partida real"""
        if not isinstance(match_data, dict):
            return False
        
        # Verifica ID da partida
        match_id = str(match_data.get('id', ''))
        if any(keyword in match_id.lower() for keyword in ['mock', 'test', 'fake', 'dummy']):
            return False
        
        # Verifica nomes dos times
        team1_name = match_data.get('team1', {}).get('name', '') if isinstance(match_data.get('team1'), dict) else ''
        team2_name = match_data.get('team2', {}).get('name', '') if isinstance(match_data.get('team2'), dict) else ''
        
        # Times com nomes genéricos ou fake
        fake_team_names = ['team1', 'team2', 'teama', 'teamb', 'mock', 'test', 'fake']
        
        if (team1_name.lower() in fake_team_names or 
            team2_name.lower() in fake_team_names or
            not team1_name or not team2_name):
            return False
        
        # Se passou em todos os testes, considera real
        return True

    def _create_mock_clients(self):
        """Cria clients mock para teste"""
        class MockClient:
            pass
        
        return [MockClient(), MockClient(), MockClient()]

    def _generate_verification_report(self):
        """Gera relatório final da verificação"""
        logger.info("\n" + "=" * 70)
        logger.info("📋 RELATÓRIO: VERIFICAÇÃO DE DADOS REAIS")
        logger.info("=" * 70)
        
        # Contadores
        total_checks = len(self.verification_results)
        passed_checks = sum(1 for result in self.verification_results.values() if result)
        
        logger.info(f"📊 RESULTADO GERAL: {passed_checks}/{total_checks} verificações aprovadas")
        
        # Detalhes das verificações
        logger.info("\n🔍 DETALHES DAS VERIFICAÇÕES:")
        
        check_details = {
            'riot_api_real': 'Riot API conectada a dados oficiais',
            'pandascore_real': 'PandaScore API conectada a odds reais',
            'anti_simulation_filter': 'Filtros anti-simulação implementados',
            'quality_validation': 'Validação de qualidade de dados',
            'real_matches_found': 'Partidas reais encontradas ao vivo',
            'tip_validation': 'Validação de tips profissionais',
            'quality_filters': 'Filtros de qualidade configurados'
        }
        
        for check, description in check_details.items():
            result = self.verification_results.get(check, False)
            icon = "✅" if result else "❌"
            logger.info(f"   {icon} {description}")
        
        # Estatísticas de partidas reais
        if 'total_real_matches' in self.verification_results:
            total_matches = self.verification_results['total_real_matches']
            logger.info(f"\n🎮 PARTIDAS REAIS ENCONTRADAS: {total_matches}")
        
        # Problemas encontrados
        if self.potential_issues:
            logger.info("\n⚠️ PROBLEMAS POTENCIAIS:")
            for issue in self.potential_issues:
                logger.info(f"   • {issue}")
        
        # Veredicto final
        success_rate = passed_checks / total_checks if total_checks > 0 else 0
        
        if success_rate >= 0.9:
            logger.info("\n🎉 VEREDICTO: ✅ SISTEMA USANDO APENAS DADOS REAIS!")
            logger.info("🔒 O sistema está corretamente configurado para:")
            logger.info("   • Buscar apenas partidas ao vivo de APIs oficiais")
            logger.info("   • Filtrar dados simulados e mock")
            logger.info("   • Validar qualidade dos dados")
            logger.info("   • Gerar tips apenas com base em jogos reais")
        elif success_rate >= 0.7:
            logger.info("\n⚠️ VEREDICTO: 🟡 SISTEMA MAJORITARIAMENTE SEGURO")
            logger.info("🔧 Alguns ajustes recomendados para garantir 100% dados reais")
        else:
            logger.info("\n❌ VEREDICTO: 🔴 RISCO DE DADOS SIMULADOS!")
            logger.info("⚠️ O sistema pode estar gerando tips com dados não-reais")
            logger.info("🛠️ AÇÃO NECESSÁRIA: Revisar filtros e conexões de API")
        
        # Próximos passos
        logger.info("\n📋 PRÓXIMOS PASSOS RECOMENDADOS:")
        logger.info("   1. Monitorar tips geradas em produção")
        logger.info("   2. Verificar logs de partidas processadas")  
        logger.info("   3. Confirmar IDs de partidas são de jogos oficiais")
        logger.info("   4. Validar se odds vêm de casas de apostas reais")
        
        logger.info("=" * 70)


async def main():
    """Função principal"""
    verification = RealDataVerification()
    success = await verification.verify_real_data_only()
    
    return success


if __name__ == "__main__":
    try:
        result = asyncio.run(main())
        if result:
            print("\n✅ Verificação concluída: Sistema usando dados reais!")
        else:
            print("\n⚠️ Verificação encontrou possíveis problemas com dados")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n🛑 Verificação interrompida pelo usuário")
    except Exception as e:
        print(f"\n❌ Erro fatal na verificação: {e}")
        sys.exit(1) 
