"""
Interface web para health check

Este módulo contém:
- app: Aplicação Flask com rotas de monitoramento
"""

from .app import create_flask_app, run_health_check_server

__all__ = ['create_flask_app', 'run_health_check_server'] 