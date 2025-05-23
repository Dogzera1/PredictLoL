#!/usr/bin/env python3
"""
FASE 5 - INFRAESTRUTURA, DEPLOY E MONITORAMENTO
Sistema completo de infraestrutura, CI/CD e monitoramento de produção
"""

import os
import json
import time
import pickle
import logging
import threading
import schedule
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, asdict
import numpy as np
import pandas as pd
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# Monitoramento e métricas
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

# FastAPI para servir modelos
try:
    from fastapi import FastAPI, HTTPException
    from fastapi.middleware.cors import CORSMiddleware
    from pydantic import BaseModel
    import uvicorn
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False

# Docker e containerização
try:
    import docker
    DOCKER_AVAILABLE = True
except ImportError:
    DOCKER_AVAILABLE = False

# Redis para cache (opcional)
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False


@dataclass
class InfraConfig:
    """Configuração de infraestrutura"""
    model_cache_ttl: int = 3600  # 1 hora
    monitoring_interval: int = 60  # 1 minuto
    max_inference_time_ms: float = 100.0
    max_memory_usage_mb: float = 1024.0
    enable_drift_detection: bool = True
    retrain_threshold: float = 0.05  # 5% drop in performance
    backup_interval_hours: int = 24
    log_level: str = "INFO"


class ModelRegistry:
    """Registro de modelos com versionamento"""
    
    def __init__(self, registry_path: str = "models/registry"):
        self.registry_path = Path(registry_path)
        self.registry_path.mkdir(parents=True, exist_ok=True)
        self.models = {}
        self.active_model = None
        self.model_metadata = {}
        
        self._load_registry()
        
    def register_model(self, model_name: str, model_object: Any, 
                      metadata: Dict[str, Any]) -> str:
        """Registra um novo modelo"""
        
        version = datetime.now().strftime("%Y%m%d_%H%M%S")
        model_id = f"{model_name}_v{version}"
        
        # Salvar modelo
        model_path = self.registry_path / f"{model_id}.pkl"
        with open(model_path, 'wb') as f:
            pickle.dump(model_object, f)
        
        # Salvar metadata
        metadata.update({
            'model_name': model_name,
            'version': version,
            'model_id': model_id,
            'created_at': datetime.now().isoformat(),
            'model_path': str(model_path),
            'status': 'registered'
        })
        
        metadata_path = self.registry_path / f"{model_id}_metadata.json"
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        self.models[model_id] = model_object
        self.model_metadata[model_id] = metadata
        
        logging.info(f"✅ Modelo {model_id} registrado com sucesso")
        return model_id
    
    def set_active_model(self, model_id: str):
        """Define o modelo ativo para produção"""
        if model_id not in self.models:
            raise ValueError(f"Modelo {model_id} não encontrado")
        
        self.active_model = model_id
        self.model_metadata[model_id]['status'] = 'active'
        self.model_metadata[model_id]['activated_at'] = datetime.now().isoformat()
        
        # Salvar estado do registry
        self._save_registry_state()
        
        logging.info(f"✅ Modelo {model_id} ativado para produção")
    
    def get_active_model(self) -> Any:
        """Retorna o modelo ativo"""
        if not self.active_model:
            raise ValueError("Nenhum modelo ativo")
        return self.models[self.active_model]
    
    def list_models(self) -> List[Dict[str, Any]]:
        """Lista todos os modelos registrados"""
        return list(self.model_metadata.values())
    
    def _load_registry(self):
        """Carrega registry existente"""
        registry_state_path = self.registry_path / "registry_state.json"
        
        if registry_state_path.exists():
            with open(registry_state_path, 'r') as f:
                state = json.load(f)
                self.active_model = state.get('active_model')
        
        # Carregar modelos existentes
        for metadata_file in self.registry_path.glob("*_metadata.json"):
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)
                model_id = metadata['model_id']
                
                # Carregar modelo
                model_path = Path(metadata['model_path'])
                if model_path.exists():
                    with open(model_path, 'rb') as mf:
                        model = pickle.load(mf)
                    
                    self.models[model_id] = model
                    self.model_metadata[model_id] = metadata
    
    def _save_registry_state(self):
        """Salva estado do registry"""
        state = {
            'active_model': self.active_model,
            'last_updated': datetime.now().isoformat()
        }
        
        registry_state_path = self.registry_path / "registry_state.json"
        with open(registry_state_path, 'w') as f:
            json.dump(state, f, indent=2)


class PerformanceMonitor:
    """Monitor de performance em tempo real"""
    
    def __init__(self, config: InfraConfig):
        self.config = config
        self.metrics_history = []
        self.alerts = []
        self.is_monitoring = False
        self.baseline_metrics = {}
        
        # Configurar logging
        logging.basicConfig(
            level=getattr(logging, config.log_level),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
    
    def start_monitoring(self):
        """Inicia monitoramento contínuo"""
        self.is_monitoring = True
        
        def monitor_loop():
            while self.is_monitoring:
                try:
                    metrics = self.collect_metrics()
                    self.analyze_metrics(metrics)
                    time.sleep(self.config.monitoring_interval)
                except Exception as e:
                    self.logger.error(f"Erro no monitoramento: {e}")
        
        monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
        monitor_thread.start()
        
        self.logger.info("🔍 Monitoramento iniciado")
    
    def stop_monitoring(self):
        """Para monitoramento"""
        self.is_monitoring = False
        self.logger.info("⏹️ Monitoramento parado")
    
    def collect_metrics(self) -> Dict[str, Any]:
        """Coleta métricas do sistema"""
        metrics = {
            'timestamp': datetime.now().isoformat(),
            'system': {},
            'application': {}
        }
        
        # Métricas do sistema
        if PSUTIL_AVAILABLE:
            metrics['system'] = {
                'cpu_percent': psutil.cpu_percent(),
                'memory_percent': psutil.virtual_memory().percent,
                'memory_used_mb': psutil.virtual_memory().used / 1024 / 1024,
                'disk_percent': psutil.disk_usage('/').percent,
                'network_io': dict(psutil.net_io_counters()._asdict()) if hasattr(psutil, 'net_io_counters') else {}
            }
        
        # Métricas da aplicação (simuladas)
        metrics['application'] = {
            'predictions_per_minute': np.random.randint(50, 200),
            'avg_inference_time_ms': np.random.uniform(10, 50),
            'cache_hit_rate': np.random.uniform(0.7, 0.95),
            'active_connections': np.random.randint(10, 100),
            'error_rate': np.random.uniform(0.001, 0.01)
        }
        
        self.metrics_history.append(metrics)
        
        # Manter apenas últimas 1000 métricas
        if len(self.metrics_history) > 1000:
            self.metrics_history = self.metrics_history[-1000:]
        
        return metrics
    
    def analyze_metrics(self, metrics: Dict[str, Any]):
        """Analisa métricas e gera alertas"""
        alerts = []
        
        # Verificar uso de memória
        if PSUTIL_AVAILABLE and 'memory_used_mb' in metrics['system']:
            memory_used = metrics['system']['memory_used_mb']
            if memory_used > self.config.max_memory_usage_mb:
                alerts.append({
                    'type': 'memory_high',
                    'severity': 'warning',
                    'message': f"Uso de memória alto: {memory_used:.1f}MB",
                    'timestamp': metrics['timestamp']
                })
        
        # Verificar tempo de inferência
        inference_time = metrics['application']['avg_inference_time_ms']
        if inference_time > self.config.max_inference_time_ms:
            alerts.append({
                'type': 'inference_slow',
                'severity': 'warning',
                'message': f"Tempo de inferência alto: {inference_time:.1f}ms",
                'timestamp': metrics['timestamp']
            })
        
        # Verificar taxa de erro
        error_rate = metrics['application']['error_rate']
        if error_rate > 0.05:  # 5%
            alerts.append({
                'type': 'error_rate_high',
                'severity': 'critical',
                'message': f"Taxa de erro alta: {error_rate:.2%}",
                'timestamp': metrics['timestamp']
            })
        
        for alert in alerts:
            self.alerts.append(alert)
            self.logger.warning(f"⚠️ ALERTA: {alert['message']}")
        
        # Manter apenas últimos 100 alertas
        if len(self.alerts) > 100:
            self.alerts = self.alerts[-100:]
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """Retorna dados para dashboard"""
        if not self.metrics_history:
            return {'status': 'no_data'}
        
        latest_metrics = self.metrics_history[-1]
        
        # Calcular médias das últimas 10 métricas
        recent_metrics = self.metrics_history[-10:]
        
        avg_cpu = np.mean([m['system'].get('cpu_percent', 0) for m in recent_metrics])
        avg_memory = np.mean([m['system'].get('memory_percent', 0) for m in recent_metrics])
        avg_inference = np.mean([m['application'].get('avg_inference_time_ms', 0) for m in recent_metrics])
        
        return {
            'status': 'healthy',
            'timestamp': latest_metrics['timestamp'],
            'system': {
                'cpu_percent': avg_cpu,
                'memory_percent': avg_memory,
                'status': 'healthy' if avg_cpu < 80 and avg_memory < 80 else 'warning'
            },
            'application': {
                'avg_inference_time_ms': avg_inference,
                'predictions_count': len(self.metrics_history),
                'error_rate': latest_metrics['application'].get('error_rate', 0),
                'status': 'healthy' if avg_inference < self.config.max_inference_time_ms else 'warning'
            },
            'recent_alerts': self.alerts[-5:],  # Últimos 5 alertas
            'metrics_history': [
                {
                    'timestamp': m['timestamp'],
                    'cpu': m['system'].get('cpu_percent', 0),
                    'memory': m['system'].get('memory_percent', 0),
                    'inference_time': m['application'].get('avg_inference_time_ms', 0)
                }
                for m in recent_metrics
            ]
        }


class DriftDetector:
    """Detector de drift de dados e modelo"""
    
    def __init__(self, baseline_data: np.ndarray = None):
        self.baseline_data = baseline_data
        self.baseline_stats = None
        self.drift_history = []
        
        if baseline_data is not None:
            self._calculate_baseline_stats()
    
    def _calculate_baseline_stats(self):
        """Calcula estatísticas baseline"""
        self.baseline_stats = {
            'mean': np.mean(self.baseline_data, axis=0),
            'std': np.std(self.baseline_data, axis=0),
            'min': np.min(self.baseline_data, axis=0),
            'max': np.max(self.baseline_data, axis=0)
        }
    
    def detect_drift(self, new_data: np.ndarray, threshold: float = 0.1) -> Dict[str, Any]:
        """Detecta drift nos dados"""
        if self.baseline_stats is None:
            return {'drift_detected': False, 'reason': 'no_baseline'}
        
        drift_scores = []
        
        # Comparar estatísticas
        new_mean = np.mean(new_data, axis=0)
        mean_diff = np.abs(new_mean - self.baseline_stats['mean']) / (self.baseline_stats['std'] + 1e-8)
        
        drift_score = np.mean(mean_diff)
        drift_detected = drift_score > threshold
        
        result = {
            'drift_detected': drift_detected,
            'drift_score': float(drift_score),
            'threshold': threshold,
            'timestamp': datetime.now().isoformat(),
            'features_with_drift': []
        }
        
        # Identificar features com drift
        if drift_detected:
            high_drift_features = np.where(mean_diff > threshold)[0]
            result['features_with_drift'] = high_drift_features.tolist()
        
        self.drift_history.append(result)
        
        return result


class ModelInferenceAPI:
    """API FastAPI para servir modelo"""
    
    def __init__(self, model_registry: ModelRegistry, monitor: PerformanceMonitor):
        self.model_registry = model_registry
        self.monitor = monitor
        self.app = None
        
        if FASTAPI_AVAILABLE:
            self._setup_api()
    
    def _setup_api(self):
        """Configura FastAPI app"""
        self.app = FastAPI(
            title="LoL Prediction Model API",
            description="API para predições de League of Legends",
            version="1.0.0"
        )
        
        # CORS
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # Models para request/response
        class PredictionRequest(BaseModel):
            features: List[float]
            match_id: Optional[str] = None
        
        class PredictionResponse(BaseModel):
            prediction: float
            model_version: str
            inference_time_ms: float
            timestamp: str
        
        class HealthResponse(BaseModel):
            status: str
            model_status: str
            metrics: Dict[str, Any]
        
        @self.app.post("/predict", response_model=PredictionResponse)
        async def predict(request: PredictionRequest):
            """Endpoint de predição"""
            try:
                start_time = time.time()
                
                # Obter modelo ativo
                model = self.model_registry.get_active_model()
                
                # Fazer predição
                features = np.array(request.features).reshape(1, -1)
                
                if hasattr(model, 'predict_proba'):
                    prediction = model.predict_proba(features)[0, 1]
                else:
                    prediction = model.predict(features)[0]
                
                inference_time = (time.time() - start_time) * 1000
                
                return PredictionResponse(
                    prediction=float(prediction),
                    model_version=self.model_registry.active_model,
                    inference_time_ms=inference_time,
                    timestamp=datetime.now().isoformat()
                )
                
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/health", response_model=HealthResponse)
        async def health():
            """Endpoint de health check"""
            dashboard_data = self.monitor.get_dashboard_data()
            
            return HealthResponse(
                status="healthy",
                model_status="active" if self.model_registry.active_model else "no_model",
                metrics=dashboard_data
            )
        
        @self.app.get("/models")
        async def list_models():
            """Lista modelos disponíveis"""
            return {
                "models": self.model_registry.list_models(),
                "active_model": self.model_registry.active_model
            }
    
    def start_server(self, host: str = "0.0.0.0", port: int = 8000):
        """Inicia servidor FastAPI"""
        if not FASTAPI_AVAILABLE:
            raise RuntimeError("FastAPI não disponível")
        
        uvicorn.run(self.app, host=host, port=port)


class InfrastructureManager:
    """Gerenciador principal de infraestrutura"""
    
    def __init__(self, config: InfraConfig = None):
        self.config = config or InfraConfig()
        
        # Componentes
        self.model_registry = ModelRegistry()
        self.monitor = PerformanceMonitor(self.config)
        self.drift_detector = DriftDetector()
        self.inference_api = None
        
        # Estado
        self.is_running = False
        
        # Configurar logging
        logging.basicConfig(level=getattr(logging, self.config.log_level))
        self.logger = logging.getLogger(__name__)
        
        self.logger.info("🏗️ Infrastructure Manager inicializado")
    
    def deploy_model(self, model: Any, model_name: str, metadata: Dict[str, Any]) -> str:
        """Deploy de um novo modelo"""
        self.logger.info(f"🚀 Fazendo deploy do modelo {model_name}")
        
        # Registrar modelo
        model_id = self.model_registry.register_model(model_name, model, metadata)
        
        # Ativar modelo
        self.model_registry.set_active_model(model_id)
        
        self.logger.info(f"✅ Deploy concluído: {model_id}")
        return model_id
    
    def start_infrastructure(self):
        """Inicia toda a infraestrutura"""
        self.logger.info("🚀 Iniciando infraestrutura completa...")
        
        # Iniciar monitoramento
        self.monitor.start_monitoring()
        
        # Agendar backups
        self._schedule_backups()
        
        # Configurar API
        if FASTAPI_AVAILABLE:
            self.inference_api = ModelInferenceAPI(self.model_registry, self.monitor)
        
        self.is_running = True
        self.logger.info("✅ Infraestrutura iniciada com sucesso")
    
    def stop_infrastructure(self):
        """Para toda a infraestrutura"""
        self.logger.info("⏹️ Parando infraestrutura...")
        
        self.monitor.stop_monitoring()
        self.is_running = False
        
        self.logger.info("✅ Infraestrutura parada")
    
    def _schedule_backups(self):
        """Agenda backups automáticos"""
        def backup_job():
            self.logger.info("💾 Executando backup automático...")
            self._create_backup()
        
        schedule.every(self.config.backup_interval_hours).hours.do(backup_job)
        
        # Thread para executar schedules
        def scheduler_loop():
            while self.is_running:
                schedule.run_pending()
                time.sleep(60)  # Verificar a cada minuto
        
        scheduler_thread = threading.Thread(target=scheduler_loop, daemon=True)
        scheduler_thread.start()
    
    def _create_backup(self):
        """Cria backup dos modelos e dados"""
        backup_dir = Path("backups") / datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Backup do registry
        import shutil
        shutil.copytree(self.model_registry.registry_path, backup_dir / "models")
        
        # Backup das métricas
        metrics_backup = {
            'metrics_history': self.monitor.metrics_history[-100:],  # Últimas 100
            'alerts': self.monitor.alerts[-50:],  # Últimos 50 alertas
            'timestamp': datetime.now().isoformat()
        }
        
        with open(backup_dir / "metrics.json", 'w') as f:
            json.dump(metrics_backup, f, indent=2)
        
        self.logger.info(f"✅ Backup criado em: {backup_dir}")
    
    def get_infrastructure_status(self) -> Dict[str, Any]:
        """Retorna status completo da infraestrutura"""
        return {
            'timestamp': datetime.now().isoformat(),
            'infrastructure': {
                'status': 'running' if self.is_running else 'stopped',
                'components': {
                    'model_registry': 'active',
                    'monitoring': 'active' if self.monitor.is_monitoring else 'inactive',
                    'api': 'available' if FASTAPI_AVAILABLE else 'unavailable',
                    'drift_detection': 'active'
                }
            },
            'models': {
                'total_registered': len(self.model_registry.models),
                'active_model': self.model_registry.active_model,
                'models_list': self.model_registry.list_models()
            },
            'monitoring': self.monitor.get_dashboard_data(),
            'config': asdict(self.config)
        }


# Exemplo de uso
if __name__ == "__main__":
    # Configuração
    config = InfraConfig(
        monitoring_interval=30,
        max_inference_time_ms=50.0,
        enable_drift_detection=True
    )
    
    # Inicializar gerenciador
    infra_manager = InfrastructureManager(config)
    
    # Exemplo de deploy de modelo (simulado)
    try:
        # Modelo mock
        from sklearn.ensemble import RandomForestClassifier
        mock_model = RandomForestClassifier(n_estimators=10, random_state=42)
        
        # Dados mock para treinar
        X_mock = np.random.randn(100, 10)
        y_mock = np.random.binomial(1, 0.5, 100)
        mock_model.fit(X_mock, y_mock)
        
        # Metadata do modelo
        metadata = {
            'algorithm': 'RandomForest',
            'performance': {
                'auc_roc': 0.85,
                'accuracy': 0.82,
                'log_loss': 0.45
            },
            'training_data': {
                'samples': 100,
                'features': 10
            },
            'deployment_info': {
                'environment': 'development',
                'deployed_by': 'system'
            }
        }
        
        # Deploy
        model_id = infra_manager.deploy_model(mock_model, "test_model", metadata)
        
        # Iniciar infraestrutura
        infra_manager.start_infrastructure()
        
        # Status
        status = infra_manager.get_infrastructure_status()
        print("\n🏗️ STATUS DA INFRAESTRUTURA:")
        print(json.dumps(status, indent=2))
        
        # Manter rodando por um tempo para demonstração
        print("\n⏳ Infraestrutura rodando... (Ctrl+C para parar)")
        try:
            while True:
                time.sleep(10)
                dashboard = infra_manager.monitor.get_dashboard_data()
                if dashboard.get('recent_alerts'):
                    print(f"⚠️ Novos alertas: {len(dashboard['recent_alerts'])}")
        except KeyboardInterrupt:
            print("\n⏹️ Parando infraestrutura...")
            infra_manager.stop_infrastructure()
            print("✅ Infraestrutura parada com sucesso")
    
    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc() 