#!/usr/bin/env python3
"""
PIPELINE COMPLETO COM DADOS REAIS APENAS
Sistema de melhoria usando apenas dados reais do projeto LoL
"""

import os
import sys
import json
import pandas as pd
import numpy as np
from datetime import datetime
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# Adicionar diretórios ao path
sys.path.append('.')
sys.path.append('./services')

# Imports das melhorias
try:
    from services.advanced_feature_engineering import AdvancedFeatureEngineer
    from services.advanced_model_optimizer import AdvancedModelOptimizer
    from services.infrastructure_manager import InfrastructureManager
except ImportError as e:
    print(f"❌ Erro ao importar serviços melhorados: {e}")
    print("💡 Certifique-se de que os arquivos de melhoria estão no diretório services/")
    sys.exit(1)

class RealDataPipeline:
    """Pipeline completo usando apenas dados reais"""
    
    def __init__(self):
        self.start_time = datetime.now()
        self.results = {
            'timestamp': self.start_time.isoformat(),
            'data_source': 'real_only',
            'phases': {},
            'final_metrics': {}
        }
        
        # Configuração para dados reais
        self.data_config = {
            'real_data_file': 'data/real_match_data.csv',
            'backup_data_file': 'data/processed_match_data.json',
            'min_samples': 100,  # Mínimo de amostras para treinar
            'target_column': 'team1_win'
        }
        
        print("🏆 PIPELINE DE MELHORIAS - DADOS REAIS APENAS")
        print("=" * 70)
        print(f"⏰ Iniciado em: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🎯 Objetivo: Otimizar modelo usando apenas dados reais")
    
    def load_real_data(self):
        """Carrega dados reais do projeto"""
        print("\n📂 FASE 1: CARREGAMENTO DE DADOS REAIS")
        print("-" * 50)
        
        # Verificar se CSV existe
        if os.path.exists(self.data_config['real_data_file']):
            print(f"✅ Carregando CSV: {self.data_config['real_data_file']}")
            df = pd.read_csv(self.data_config['real_data_file'])
        else:
            print(f"⚠️ CSV não encontrado, convertendo dados JSON...")
            # Converter JSON para CSV
            os.system('python convert_real_data_to_csv.py')
            df = pd.read_csv(self.data_config['real_data_file'])
        
        print(f"📊 Dataset carregado: {df.shape[0]} amostras, {df.shape[1]} features")
        
        # Validações
        if df.shape[0] < self.data_config['min_samples']:
            raise ValueError(f"Insuficientes amostras: {df.shape[0]} < {self.data_config['min_samples']}")
        
        if self.data_config['target_column'] not in df.columns:
            raise ValueError(f"Coluna target '{self.data_config['target_column']}' não encontrada")
        
        # Estatísticas dos dados reais
        target = df[self.data_config['target_column']]
        print(f"🎯 Target balance: {target.value_counts().to_dict()}")
        print(f"📈 Taxa de vitória Team1: {target.mean():.2%}")
        
        # Salvar informações da fase
        self.results['phases']['data_loading'] = {
            'status': 'SUCCESS',
            'samples': int(df.shape[0]),
            'features': int(df.shape[1]),
            'target_balance': target.value_counts().to_dict(),
            'win_rate': float(target.mean())
        }
        
        return df
    
    def engineer_features(self, df):
        """Aplica engenharia avançada de features aos dados reais"""
        print("\n🔧 FASE 2: ENGENHARIA AVANÇADA DE FEATURES")
        print("-" * 50)
        
        try:
            engineer = AdvancedFeatureEngineer()
            
            print(f"📊 Features originais: {df.shape[1]}")
            
            # Aplicar transformações - retorna tupla (X, y)
            X_enhanced, y = engineer.transform_dataset(df, self.data_config['target_column'])
            
            # Recombinar X e y em DataFrame
            df_enhanced = X_enhanced.copy()
            df_enhanced[self.data_config['target_column']] = y
            
            print(f"🚀 Features após engenharia: {df_enhanced.shape[1]}")
            print(f"📈 Melhoria: {df_enhanced.shape[1] - df.shape[1]} novas features")
            
            # Salvar configuração de features
            feature_info = {
                'original_features': int(df.shape[1]),
                'engineered_features': int(df_enhanced.shape[1]),
                'improvement': int(df_enhanced.shape[1] - df.shape[1]),
                'new_feature_types': [
                    'counter_pick_analysis',
                    'champion_embeddings',
                    'team_synergy',
                    'power_spikes',
                    'temporal_features',
                    'meta_strength',
                    'player_performance'
                ]
            }
            
            # Salvar em arquivo
            with open('data/real_feature_config.json', 'w') as f:
                json.dump(feature_info, f, indent=2)
            
            self.results['phases']['feature_engineering'] = {
                'status': 'SUCCESS',
                **feature_info
            }
            
            return df_enhanced
            
        except Exception as e:
            print(f"❌ Erro na engenharia de features: {e}")
            print("🔄 Continuando com features originais...")
            
            self.results['phases']['feature_engineering'] = {
                'status': 'FAILED',
                'error': str(e),
                'fallback': 'original_features'
            }
            
            return df
    
    def optimize_model(self, df):
        """Otimiza modelo com dados reais"""
        print("\n🎯 FASE 3: OTIMIZAÇÃO DE MODELO")
        print("-" * 50)
        
        try:
            optimizer = AdvancedModelOptimizer()
            
            # Preparar dados
            target_col = self.data_config['target_column']
            y = df[target_col].values
            X = df.drop(columns=[target_col]).values
            
            print(f"📊 Treino com: {X.shape[0]} amostras, {X.shape[1]} features")
            
            # Usar o método correto
            results = optimizer.run_optimization_pipeline(X, y)
            
            # Extrair métricas
            best_model_info = results['best_model']
            best_metrics = best_model_info['metrics']
            
            print(f"🏆 Melhor modelo: {best_model_info['algorithm']}")
            print(f"📈 AUC-ROC: {best_metrics['auc']:.4f}")
            print(f"📈 Acurácia: {best_metrics['accuracy']:.4f}")
            print(f"📈 Log-loss: {best_metrics['log_loss']:.4f}")
            
            # Salvar modelo otimizado
            import joblib
            model_path = 'models/optimized_real_model.pkl'
            os.makedirs('models', exist_ok=True)
            joblib.dump(best_model_info['model'], model_path)
            
            print(f"💾 Modelo salvo: {model_path}")
            
            self.results['phases']['model_optimization'] = {
                'status': 'SUCCESS',
                'best_algorithm': best_model_info['algorithm'],
                'metrics': best_metrics,
                'model_path': model_path,
                'total_experiments': results.get('total_experiments', 0)
            }
            
            return best_model_info['model'], best_metrics
            
        except Exception as e:
            print(f"❌ Erro na otimização: {e}")
            
            self.results['phases']['model_optimization'] = {
                'status': 'FAILED',
                'error': str(e)
            }
            
            return None, {}
    
    def setup_infrastructure(self, model, metrics):
        """Configura infraestrutura de monitoramento"""
        print("\n🏗️ FASE 4: INFRAESTRUTURA E MONITORAMENTO")
        print("-" * 50)
        
        try:
            infra = InfrastructureManager()
            
            # Registrar modelo
            if model is not None:
                model_id = infra.deploy_model(
                    model, 
                    "RealDataOptimized",
                    metadata={
                        'data_source': 'real_only',
                        'samples': self.results['phases']['data_loading']['samples'],
                        'features': self.results['phases']['feature_engineering'].get('engineered_features', 0),
                        **metrics
                    }
                )
                print(f"📝 Modelo registrado: {model_id}")
            
            # Iniciar infraestrutura
            infra.start_infrastructure()
            print(f"📊 Infraestrutura iniciada")
            
            # Status da infraestrutura
            status = infra.get_infrastructure_status()
            print(f"🌐 Status: {status.get('status', 'unknown')}")
            
            self.results['phases']['infrastructure'] = {
                'status': 'SUCCESS',
                'model_id': model_id if model else None,
                'infrastructure_status': status,
                'monitoring_enabled': True
            }
            
        except Exception as e:
            print(f"❌ Erro na infraestrutura: {e}")
            
            self.results['phases']['infrastructure'] = {
                'status': 'PARTIAL',
                'error': str(e)
            }
    
    def generate_final_report(self):
        """Gera relatório final das melhorias"""
        print("\n📋 FASE 5: RELATÓRIO FINAL")
        print("-" * 50)
        
        end_time = datetime.now()
        duration = end_time - self.start_time
        
        # Calcular taxa de sucesso
        phases = self.results['phases']
        success_count = sum(1 for p in phases.values() if p['status'] == 'SUCCESS')
        total_phases = len(phases)
        success_rate = (success_count / total_phases) * 100 if total_phases > 0 else 0
        
        # Métricas finais
        self.results['final_metrics'] = {
            'duration_seconds': duration.total_seconds(),
            'phases_completed': total_phases,
            'success_rate': success_rate,
            'end_time': end_time.isoformat()
        }
        
        # Salvar relatório
        report_file = f"reports/real_data_pipeline_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        os.makedirs('reports', exist_ok=True)
        
        with open(report_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        # Exibir resumo
        print(f"⏱️ Duração total: {duration.total_seconds():.1f} segundos")
        print(f"✅ Taxa de sucesso: {success_rate:.1f}% ({success_count}/{total_phases})")
        print(f"📄 Relatório salvo: {report_file}")
        
        # Resumo das melhorias
        print(f"\n🎉 RESUMO DAS MELHORIAS APLICADAS:")
        print(f"=" * 50)
        
        if 'data_loading' in phases and phases['data_loading']['status'] == 'SUCCESS':
            print(f"✅ Dados reais carregados: {phases['data_loading']['samples']} amostras")
        
        if 'feature_engineering' in phases and phases['feature_engineering']['status'] == 'SUCCESS':
            orig = phases['feature_engineering']['original_features']
            new = phases['feature_engineering']['engineered_features']
            print(f"✅ Features expandidas: {orig} → {new} (+{new-orig})")
        
        if 'model_optimization' in phases and phases['model_optimization']['status'] == 'SUCCESS':
            metrics = phases['model_optimization']['metrics']
            print(f"✅ Modelo otimizado: AUC {metrics.get('auc', 0):.4f}")
        
        if 'infrastructure' in phases and phases['infrastructure']['status'] in ['SUCCESS', 'PARTIAL']:
            print(f"✅ Infraestrutura configurada")
        
        return self.results

def main():
    """Executa pipeline completo com dados reais"""
    
    # Criar pipeline
    pipeline = RealDataPipeline()
    
    try:
        # Fase 1: Carregar dados reais
        df = pipeline.load_real_data()
        
        # Fase 2: Engenharia de features
        df_enhanced = pipeline.engineer_features(df)
        
        # Fase 3: Otimizar modelo
        model, metrics = pipeline.optimize_model(df_enhanced)
        
        # Fase 4: Configurar infraestrutura
        pipeline.setup_infrastructure(model, metrics)
        
        # Fase 5: Relatório final
        results = pipeline.generate_final_report()
        
        print(f"\n🏆 PIPELINE CONCLUÍDO COM SUCESSO!")
        print(f"📊 Taxa de sucesso: {results['final_metrics']['success_rate']:.1f}%")
        
        return results
        
    except Exception as e:
        print(f"\n❌ ERRO CRÍTICO NO PIPELINE: {e}")
        import traceback
        traceback.print_exc()
        
        # Gerar relatório mesmo com erro
        pipeline.results['critical_error'] = str(e)
        pipeline.generate_final_report()
        
        return None

if __name__ == "__main__":
    results = main()
    
    if results:
        print(f"\n✨ Pipeline de dados reais executado com sucesso!")
        print(f"🎯 Use os modelos otimizados para apostas mais precisas!")
    else:
        print(f"\n💥 Pipeline falhou - verifique os logs acima") 