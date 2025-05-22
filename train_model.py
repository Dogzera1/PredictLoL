"""
Script para treinar o modelo preditivo de LoL

Este script independente coleta dados históricos de partidas e treina o modelo
de machine learning para previsões mais precisas.
"""

import os
import logging
from services.model_trainer import ModelTrainer

# Configuração de logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def main():
    """Função principal para treinar o modelo"""
    logger.info("Iniciando treinamento do modelo com dados de 2023-2025...")
    
    # Inicializar o treinador de modelo
    trainer = ModelTrainer()
    
    # Coletar dados históricos
    logger.info("Coletando dados históricos...")
    success = trainer.collect_historical_data()
    
    if not success:
        logger.error("Falha ao coletar dados históricos. Verifique a chave da API e conexão.")
        return False
    
    # Treinar modelo
    logger.info("Treinando modelo...")
    success = trainer.train_model()
    
    if success:
        logger.info("Modelo treinado com sucesso!")
        return True
    else:
        logger.error("Falha ao treinar modelo.")
        return False

if __name__ == "__main__":
    logger.info("Iniciando script de treinamento...")
    main() 