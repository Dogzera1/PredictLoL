#!/usr/bin/env python3
"""
TESTE RÁPIDO DAS MELHORIAS IMPLEMENTADAS
Script para demonstrar e validar as melhorias do Bot V3
"""

import os
import sys
import numpy as np
import pandas as pd
from datetime import datetime

# Adicionar diretório ao path
sys.path.append('.')

def test_phase_3_feature_engineering():
    """Testa feature engineering avançado"""
    print("🔧 TESTANDO FEATURE ENGINEERING AVANÇADO")
    print("-" * 50)
    
    try:
        from services.advanced_feature_engineering import AdvancedFeatureEngineer, FeatureConfig
        
        # Configuração de teste
        config = FeatureConfig(max_features=50)
        feature_engineer = AdvancedFeatureEngineer(config)
        
        # Dados sintéticos
        np.random.seed(42)
        data = {
            'team1_kills': np.random.poisson(15, 100),
            'team1_gold': np.random.normal(50000, 10000, 100),
            'team2_kills': np.random.poisson(15, 100),
            'team2_gold': np.random.normal(50000, 10000, 100),
            'game_duration': np.random.normal(1800, 300, 100),
            'team1_comp': [['Aatrox', 'Graves', 'Azir', 'Jinx', 'Thresh']] * 100,
            'team2_comp': [['Gnar', 'Elise', 'LeBlanc', 'Lucian', 'Lulu']] * 100,
            'patch': ['14.23'] * 100,
            'team1_win': np.random.binomial(1, 0.5, 100)
        }
        
        df = pd.DataFrame(data)
        print(f"✅ Dataset criado: {df.shape}")
        
        # Aplicar feature engineering
        X, y = feature_engineer.transform_dataset(df)
        print(f"✅ Features geradas: {X.shape[1]} (de {df.shape[1]} originais)")
        print(f"📈 Melhoria: {X.shape[1] / df.shape[1]:.1f}x")
        
        # Mostrar top features
        top_features = list(feature_engineer.feature_importance.keys())[:5]
        print(f"🏆 Top 5 features: {top_features}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        return False

def test_phase_4_model_optimization():
    """Testa otimização de modelos"""
    print("\n🤖 TESTANDO OTIMIZAÇÃO DE MODELOS")
    print("-" * 50)
    
    try:
        from services.advanced_model_optimizer import AdvancedModelOptimizer, ModelConfig
        
        # Configuração de teste (rápida)
        config = ModelConfig(
            enable_traditional_ml=True,
            enable_deep_learning=False,
            optimization_budget=10  # Rápido para teste
        )
        
        optimizer = AdvancedModelOptimizer(config)
        
        # Dados sintéticos
        X = np.random.randn(200, 20)
        y = np.random.binomial(1, 0.5, 200)
        print(f"✅ Dataset criado: {X.shape}")
        
        # Executar otimização
        results = optimizer.run_optimization_pipeline(X, y)
        
        best_model = results['best_model']
        print(f"✅ Otimização concluída!")
        print(f"🏆 Melhor modelo: {best_model['name']}")
        print(f"📊 AUC: {best_model['auc_roc']:.4f}")
        print(f"📉 Log-loss: {best_model['log_loss']:.4f}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        return False

def test_phase_5_infrastructure():
    """Testa infraestrutura e monitoramento"""
    print("\n🏗️ TESTANDO INFRAESTRUTURA")
    print("-" * 50)
    
    try:
        from services.infrastructure_manager import InfrastructureManager, InfraConfig
        from sklearn.ensemble import RandomForestClassifier
        
        # Configuração de teste
        config = InfraConfig(monitoring_interval=5)
        infra_manager = InfrastructureManager(config)
        
        # Modelo mock
        model = RandomForestClassifier(n_estimators=10, random_state=42)
        X_mock = np.random.randn(50, 10)
        y_mock = np.random.binomial(1, 0.5, 50)
        model.fit(X_mock, y_mock)
        
        # Deploy
        metadata = {
            'test_model': True,
            'performance': {'auc_roc': 0.85}
        }
        
        model_id = infra_manager.deploy_model(model, "test_model", metadata)
        print(f"✅ Modelo deployado: {model_id}")
        
        # Iniciar infraestrutura
        infra_manager.start_infrastructure()
        print("✅ Infraestrutura iniciada")
        
        # Status
        status = infra_manager.get_infrastructure_status()
        print(f"📊 Status: {status['infrastructure']['status']}")
        print(f"🔍 Monitoramento: {status['infrastructure']['components']['monitoring']}")
        
        # Parar
        infra_manager.stop_infrastructure()
        print("✅ Infraestrutura parada")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        return False

def test_existing_diagnostics():
    """Testa sistema de diagnóstico existente"""
    print("\n📋 TESTANDO DIAGNÓSTICO EXISTENTE")
    print("-" * 50)
    
    try:
        from services.model_evaluator import ModelEvaluator
        from services.goals_manager import GoalsManager
        
        # Dados sintéticos
        data = {
            'auc_roc': 0.85,
            'log_loss': 0.45,
            'accuracy': 0.82,
            'precision': 0.80,
            'recall': 0.84
        }
        df = pd.DataFrame([data] * 100)  # Simular histórico
        
        # Diagnóstico
        evaluator = ModelEvaluator()
        report = evaluator.generate_report(df)
        print(f"✅ Relatório gerado")
        print(f"📊 Métricas: {list(report['performance_metrics'].keys())}")
        
        # Metas
        goals_manager = GoalsManager()
        goals = goals_manager.define_advanced_goals(report['performance_metrics'])
        print(f"✅ Metas definidas: {len(goals)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        return False

def main():
    """Executa todos os testes"""
    print("🚀 TESTANDO MELHORIAS DO BOT V3")
    print("=" * 60)
    print(f"⏰ Iniciado em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    tests = [
        ("Diagnóstico Existente", test_existing_diagnostics),
        ("Feature Engineering", test_phase_3_feature_engineering),
        ("Otimização de Modelos", test_phase_4_model_optimization),
        ("Infraestrutura", test_phase_5_infrastructure)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            success = test_func()
            results[test_name] = success
            status = "✅ PASSOU" if success else "❌ FALHOU"
            print(f"\n{status}: {test_name}")
        except Exception as e:
            results[test_name] = False
            print(f"\n❌ FALHOU: {test_name} - {e}")
    
    # Resumo final
    print("\n" + "=" * 60)
    print("📋 RESUMO DOS TESTES")
    print("=" * 60)
    
    passed = sum(results.values())
    total = len(results)
    
    for test_name, success in results.items():
        status = "✅" if success else "❌"
        print(f"{status} {test_name}")
    
    print(f"\n📊 RESULTADO: {passed}/{total} testes passaram ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("🎉 TODOS OS TESTES PASSARAM!")
        print("🚀 As melhorias estão funcionando corretamente!")
    elif passed >= total * 0.75:
        print("⚠️ Maioria dos testes passou - algumas dependências opcionais podem estar faltando")
    else:
        print("❌ Muitos testes falharam - verifique as dependências")
    
    print(f"\n💡 Para instalar dependências: pip install -r requirements_improved.txt")
    print(f"🏃 Para executar pipeline completo: python run_full_improvement_pipeline.py")

if __name__ == "__main__":
    main() 