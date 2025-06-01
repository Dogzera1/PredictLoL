"""
API REST de Produção - Semana 4
API para controle remoto do Bot LoL V3 Ultra Avançado em produção

Funcionalidades:
- Endpoints de status e controle
- API para dashboard remoto
- Comandos de deploy e restart
- Relatórios em tempo real
- Autenticação e segurança
"""

from __future__ import annotations

import asyncio
import json
import time
from typing import Dict, Any, Optional
from datetime import datetime
import traceback

from aiohttp import web, WSMsgType
from aiohttp.web import Request, Response, WebSocketResponse
import aiohttp_cors

from .production_manager import ProductionManager
from ..utils.logger_config import get_logger

logger = get_logger(__name__)


class ProductionAPI:
    """
    API REST para Gerenciamento de Produção
    
    Funcionalidades:
    - Endpoints REST para status e controle
    - WebSocket para métricas em tempo real
    - Dashboard web integrado
    - API para deploy e restart
    - Logs e relatórios via API
    """

    def __init__(self, production_manager: ProductionManager, host: str = "0.0.0.0", port: int = 8080):
        """
        Inicializa a API de produção
        
        Args:
            production_manager: Instância do ProductionManager
            host: Host da API
            port: Porta da API
        """
        self.production_manager = production_manager
        self.host = host
        self.port = port
        
        # WebSocket connections para streaming de dados
        self.websocket_connections = set()
        
        # Configuração do servidor
        self.app = None
        self.runner = None
        self.site = None
        
        logger.info(f"ProductionAPI inicializada para Semana 4 - {host}:{port}")

    async def start_api_server(self) -> bool:
        """
        Inicia o servidor da API
        
        Returns:
            True se iniciado com sucesso
        """
        try:
            logger.info("🌐 Iniciando servidor API de produção...")
            
            # Cria aplicação aiohttp
            self.app = web.Application()
            
            # Configura CORS
            cors = aiohttp_cors.setup(self.app, defaults={
                "*": aiohttp_cors.ResourceOptions(
                    allow_credentials=True,
                    expose_headers="*",
                    allow_headers="*",
                    allow_methods="*"
                )
            })
            
            # Configura rotas
            self._setup_routes()
            
            # Adiciona CORS a todas as rotas
            for route in list(self.app.router.routes()):
                cors.add(route)
            
            # Inicia servidor
            self.runner = web.AppRunner(self.app)
            await self.runner.setup()
            
            self.site = web.TCPSite(self.runner, self.host, self.port)
            await self.site.start()
            
            logger.info(f"✅ API de produção iniciada em http://{self.host}:{self.port}")
            logger.info(f"📡 Endpoints disponíveis:")
            logger.info(f"   • GET  /api/status - Status do sistema")
            logger.info(f"   • GET  /api/health - Health check")
            logger.info(f"   • POST /api/restart/{{component}} - Restart componente")
            logger.info(f"   • POST /api/emergency-recovery - Recuperação de emergência")
            logger.info(f"   • GET  /api/report/{{days}} - Relatório de performance")
            logger.info(f"   • GET  /dashboard - Dashboard web")
            logger.info(f"   • WS   /ws/metrics - Métricas em tempo real")
            
            # Inicia streaming de métricas
            asyncio.create_task(self._metrics_streaming_loop())
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro ao iniciar API de produção: {e}")
            return False

    async def stop_api_server(self):
        """Para o servidor da API"""
        try:
            logger.info("🛑 Parando servidor API de produção...")
            
            # Fecha todas as conexões WebSocket
            for ws in list(self.websocket_connections):
                await ws.close()
            
            # Para servidor
            if self.site:
                await self.site.stop()
            if self.runner:
                await self.runner.cleanup()
            
            logger.info("✅ API de produção parada")
            
        except Exception as e:
            logger.error(f"❌ Erro ao parar API: {e}")

    def _setup_routes(self):
        """Configura as rotas da API"""
        
        # Rotas de status e controle
        self.app.router.add_get('/api/status', self._handle_status)
        self.app.router.add_get('/api/health', self._handle_health)
        self.app.router.add_post('/api/restart/{component}', self._handle_restart_component)
        self.app.router.add_post('/api/emergency-recovery', self._handle_emergency_recovery)
        
        # Rotas de relatórios
        self.app.router.add_get('/api/report/{days}', self._handle_performance_report)
        self.app.router.add_get('/api/predictions', self._handle_predictions_data)
        self.app.router.add_get('/api/metrics/current', self._handle_current_metrics)
        
        # Dashboard web
        self.app.router.add_get('/dashboard', self._handle_dashboard)
        self.app.router.add_get('/api/dashboard/data', self._handle_dashboard_data)
        
        # WebSocket para métricas em tempo real
        self.app.router.add_get('/ws/metrics', self._handle_websocket_metrics)
        
        # Rotas de arquivos estáticos
        self.app.router.add_get('/', self._handle_home)
        
        # Rota para endpoints não encontrados - removendo para evitar conflito
        # self.app.router.add_route('*', '/{path:.*}', self._handle_not_found)

    async def _handle_status(self, request: Request) -> Response:
        """Endpoint: GET /api/status - Status completo do sistema"""
        try:
            status = await self.production_manager.get_system_status()
            
            return web.json_response({
                "success": True,
                "data": status,
                "timestamp": datetime.now().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Erro no endpoint /api/status: {e}")
            return web.json_response({
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }, status=500)

    async def _handle_health(self, request: Request) -> Response:
        """Endpoint: GET /api/health - Health check simples"""
        try:
            system_status = self.production_manager.system_status
            
            return web.json_response({
                "success": True,
                "status": system_status.value,
                "uptime": time.time() - self.production_manager.start_time,
                "timestamp": datetime.now().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Erro no endpoint /api/health: {e}")
            return web.json_response({
                "success": False,
                "error": str(e)
            }, status=500)

    async def _handle_restart_component(self, request: Request) -> Response:
        """Endpoint: POST /api/restart/{component} - Reinicia componente"""
        try:
            component = request.match_info['component']
            
            logger.info(f"🔄 Solicitação de restart via API: {component}")
            
            success = await self.production_manager.restart_component(component)
            
            if success:
                return web.json_response({
                    "success": True,
                    "message": f"Componente {component} reiniciado com sucesso",
                    "timestamp": datetime.now().isoformat()
                })
            else:
                return web.json_response({
                    "success": False,
                    "message": f"Falha ao reiniciar componente {component}",
                    "timestamp": datetime.now().isoformat()
                }, status=400)
                
        except Exception as e:
            logger.error(f"Erro no endpoint restart: {e}")
            return web.json_response({
                "success": False,
                "error": str(e)
            }, status=500)

    async def _handle_emergency_recovery(self, request: Request) -> Response:
        """Endpoint: POST /api/emergency-recovery - Recuperação de emergência"""
        try:
            logger.warning("🚨 Solicitação de recuperação de emergência via API")
            
            success = await self.production_manager.perform_emergency_recovery()
            
            if success:
                return web.json_response({
                    "success": True,
                    "message": "Recuperação de emergência executada com sucesso",
                    "timestamp": datetime.now().isoformat()
                })
            else:
                return web.json_response({
                    "success": False,
                    "message": "Falha na recuperação de emergência",
                    "timestamp": datetime.now().isoformat()
                }, status=500)
                
        except Exception as e:
            logger.error(f"Erro na recuperação de emergência: {e}")
            return web.json_response({
                "success": False,
                "error": str(e)
            }, status=500)

    async def _handle_performance_report(self, request: Request) -> Response:
        """Endpoint: GET /api/report/{days} - Relatório de performance"""
        try:
            days = int(request.match_info['days'])
            
            if days < 1 or days > 30:
                return web.json_response({
                    "success": False,
                    "error": "Número de dias deve estar entre 1 e 30"
                }, status=400)
            
            report = await self.production_manager.performance_monitor.get_performance_report(days)
            
            return web.json_response({
                "success": True,
                "data": report,
                "timestamp": datetime.now().isoformat()
            })
            
        except ValueError:
            return web.json_response({
                "success": False,
                "error": "Parâmetro 'days' deve ser um número"
            }, status=400)
        except Exception as e:
            logger.error(f"Erro no relatório de performance: {e}")
            return web.json_response({
                "success": False,
                "error": str(e)
            }, status=500)

    async def _handle_predictions_data(self, request: Request) -> Response:
        """Endpoint: GET /api/predictions - Dados das predições"""
        try:
            # Parâmetros opcionais
            limit = int(request.query.get('limit', 50))
            resolved_only = request.query.get('resolved_only', 'false').lower() == 'true'
            
            predictions = self.production_manager.performance_monitor.predictions
            
            # Filtra predições se necessário
            if resolved_only:
                filtered_predictions = {
                    pid: pred for pid, pred in predictions.items() 
                    if pred.is_resolved
                }
            else:
                filtered_predictions = predictions
            
            # Limita número de resultados
            limited_predictions = dict(list(filtered_predictions.items())[-limit:])
            
            # Converte para formato JSON serializável
            predictions_data = []
            for pred_id, pred in limited_predictions.items():
                predictions_data.append({
                    "prediction_id": pred_id,
                    "match_id": pred.match_id,
                    "timestamp": datetime.fromtimestamp(pred.timestamp).isoformat(),
                    "predicted_winner": pred.predicted_winner,
                    "actual_winner": pred.actual_winner,
                    "win_probability": pred.win_probability,
                    "confidence_level": pred.confidence_level,
                    "method_used": pred.method_used,
                    "odds_used": pred.odds_used,
                    "stake_amount": pred.stake_amount,
                    "potential_return": pred.potential_return,
                    "actual_return": pred.actual_return,
                    "profit_loss": pred.calculate_profit_loss(),
                    "is_resolved": pred.is_resolved,
                    "processing_time_ms": pred.processing_time_ms
                })
            
            return web.json_response({
                "success": True,
                "data": {
                    "predictions": predictions_data,
                    "total_count": len(predictions),
                    "filtered_count": len(filtered_predictions),
                    "returned_count": len(predictions_data)
                },
                "timestamp": datetime.now().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Erro no endpoint predictions: {e}")
            return web.json_response({
                "success": False,
                "error": str(e)
            }, status=500)

    async def _handle_current_metrics(self, request: Request) -> Response:
        """Endpoint: GET /api/metrics/current - Métricas atuais"""
        try:
            metrics = await self.production_manager.performance_monitor.get_current_metrics()
            
            metrics_data = {
                "timestamp": datetime.fromtimestamp(metrics.timestamp).isoformat(),
                "total_predictions": metrics.total_predictions,
                "correct_predictions": metrics.correct_predictions,
                "win_rate_percentage": metrics.win_rate_percentage,
                "total_staked": metrics.total_staked,
                "total_returned": metrics.total_returned,
                "net_profit": metrics.net_profit,
                "roi_percentage": metrics.roi_percentage,
                "uptime_hours": metrics.uptime_hours,
                "alerts_generated": metrics.alerts_generated,
                "avg_processing_time_ms": metrics.avg_processing_time_ms
            }
            
            return web.json_response({
                "success": True,
                "data": metrics_data,
                "timestamp": datetime.now().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Erro no endpoint current metrics: {e}")
            return web.json_response({
                "success": False,
                "error": str(e)
            }, status=500)

    async def _handle_dashboard(self, request: Request) -> Response:
        """Endpoint: GET /dashboard - Dashboard web"""
        try:
            # Gera dashboard HTML atualizado
            dashboard_data = self.production_manager.performance_monitor.get_live_dashboard_data()
            html_content = self.production_manager.dashboard_generator.generate_html_dashboard(dashboard_data)
            
            return web.Response(
                text=html_content,
                content_type='text/html',
                charset='utf-8'
            )
            
        except Exception as e:
            logger.error(f"Erro no dashboard: {e}")
            return web.Response(
                text=f"<html><body><h1>Erro no Dashboard</h1><p>{e}</p></body></html>",
                content_type='text/html',
                status=500
            )

    async def _handle_dashboard_data(self, request: Request) -> Response:
        """Endpoint: GET /api/dashboard/data - Dados do dashboard em JSON"""
        try:
            dashboard_data = self.production_manager.performance_monitor.get_live_dashboard_data()
            
            return web.json_response({
                "success": True,
                "data": dashboard_data,
                "timestamp": datetime.now().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Erro nos dados do dashboard: {e}")
            return web.json_response({
                "success": False,
                "error": str(e)
            }, status=500)

    async def _handle_websocket_metrics(self, request: Request) -> WebSocketResponse:
        """WebSocket: /ws/metrics - Streaming de métricas em tempo real"""
        ws = web.WebSocketResponse()
        await ws.prepare(request)
        
        self.websocket_connections.add(ws)
        logger.info(f"🔌 Nova conexão WebSocket para métricas ({len(self.websocket_connections)} total)")
        
        try:
            async for msg in ws:
                if msg.type == WSMsgType.TEXT:
                    # Mensagem de ping/pong para manter conexão viva
                    if msg.data == 'ping':
                        await ws.send_str('pong')
                elif msg.type == WSMsgType.ERROR:
                    logger.error(f'Erro no WebSocket: {ws.exception()}')
                    break
        except Exception as e:
            logger.error(f"Erro na conexão WebSocket: {e}")
        finally:
            self.websocket_connections.discard(ws)
            logger.info(f"🔌 Conexão WebSocket encerrada ({len(self.websocket_connections)} restantes)")
        
        return ws

    async def _handle_home(self, request: Request) -> Response:
        """Endpoint: GET / - Página inicial"""
        html = f"""
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Bot LoL V3 Ultra Avançado - Produção</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
</head>
<body class="bg-light">
    <div class="container mt-5">
        <div class="text-center">
            <h1 class="display-4"><i class="fas fa-robot text-primary"></i> Bot LoL V3 Ultra Avançado</h1>
            <p class="lead">Sistema de Produção - Semana 4</p>
            <hr class="my-4">
            
            <div class="row mt-5">
                <div class="col-md-6 mb-3">
                    <div class="card">
                        <div class="card-body">
                            <h5 class="card-title"><i class="fas fa-tachometer-alt"></i> Dashboard</h5>
                            <p class="card-text">Visualização completa das métricas e performance</p>
                            <a href="/dashboard" class="btn btn-primary">Acessar Dashboard</a>
                        </div>
                    </div>
                </div>
                
                <div class="col-md-6 mb-3">
                    <div class="card">
                        <div class="card-body">
                            <h5 class="card-title"><i class="fas fa-heartbeat"></i> Status do Sistema</h5>
                            <p class="card-text">Verificar saúde e status dos componentes</p>
                            <a href="/api/status" class="btn btn-success">Ver Status</a>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="row">
                <div class="col-12">
                    <h3>API Endpoints</h3>
                    <div class="list-group">
                        <div class="list-group-item">
                            <strong>GET /api/status</strong> - Status completo do sistema
                        </div>
                        <div class="list-group-item">
                            <strong>GET /api/health</strong> - Health check rápido
                        </div>
                        <div class="list-group-item">
                            <strong>GET /api/report/{{days}}</strong> - Relatório de performance
                        </div>
                        <div class="list-group-item">
                            <strong>GET /api/predictions</strong> - Dados das predições
                        </div>
                        <div class="list-group-item">
                            <strong>POST /api/restart/{{component}}</strong> - Reiniciar componente
                        </div>
                        <div class="list-group-item">
                            <strong>WS /ws/metrics</strong> - Métricas em tempo real
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</body>
</html>
        """
        
        return web.Response(
            text=html,
            content_type='text/html',
            charset='utf-8'
        )

    async def _metrics_streaming_loop(self):
        """Loop para streaming de métricas via WebSocket"""
        try:
            logger.info("📡 Iniciando streaming de métricas via WebSocket...")
            
            while True:
                await asyncio.sleep(5)  # Atualiza a cada 5 segundos
                
                if not self.websocket_connections:
                    continue
                
                try:
                    # Obtém métricas atuais
                    dashboard_data = self.production_manager.performance_monitor.get_live_dashboard_data()
                    
                    # Prepara dados para envio
                    metrics_update = {
                        "type": "metrics_update",
                        "data": dashboard_data,
                        "timestamp": datetime.now().isoformat()
                    }
                    
                    # Envia para todas as conexões WebSocket ativas
                    disconnected_connections = set()
                    
                    for ws in self.websocket_connections:
                        try:
                            if ws.closed:
                                disconnected_connections.add(ws)
                            else:
                                await ws.send_str(json.dumps(metrics_update))
                        except Exception as e:
                            logger.warning(f"Erro ao enviar métricas via WebSocket: {e}")
                            disconnected_connections.add(ws)
                    
                    # Remove conexões desconectadas
                    for ws in disconnected_connections:
                        self.websocket_connections.discard(ws)
                    
                except Exception as e:
                    logger.error(f"Erro no streaming de métricas: {e}")
                
        except asyncio.CancelledError:
            logger.info("📡 Streaming de métricas cancelado")
        except Exception as e:
            logger.error(f"Erro fatal no streaming de métricas: {e}")

    def get_api_info(self) -> Dict[str, Any]:
        """Retorna informações da API"""
        return {
            "host": self.host,
            "port": self.port,
            "base_url": f"http://{self.host}:{self.port}",
            "dashboard_url": f"http://{self.host}:{self.port}/dashboard",
            "websocket_url": f"ws://{self.host}:{self.port}/ws/metrics",
            "active_connections": len(self.websocket_connections),
            "endpoints": [
                {"method": "GET", "path": "/", "description": "Página inicial"},
                {"method": "GET", "path": "/dashboard", "description": "Dashboard web"},
                {"method": "GET", "path": "/api/status", "description": "Status completo"},
                {"method": "GET", "path": "/api/health", "description": "Health check"},
                {"method": "GET", "path": "/api/report/{{days}}", "description": "Relatório de performance"},
                {"method": "GET", "path": "/api/predictions", "description": "Dados das predições"},
                {"method": "GET", "path": "/api/metrics/current", "description": "Métricas atuais"},
                {"method": "POST", "path": "/api/restart/{{component}}", "description": "Reiniciar componente"},
                {"method": "POST", "path": "/api/emergency-recovery", "description": "Recuperação de emergência"},
                {"method": "WS", "path": "/ws/metrics", "description": "Métricas em tempo real"}
            ]
        } 