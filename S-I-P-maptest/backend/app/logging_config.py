import logging
import sys
import os

def configurar_logs():
    """
    Configura o sistema de logging da aplicação.
    Suprime logs verbosos de bibliotecas externas.
    """
    
    # Configuração do root logger
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Suprimir logs verbosos de bibliotecas
    logging.getLogger('selenium').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('WDM').setLevel(logging.ERROR)
    logging.getLogger('PIL').setLevel(logging.WARNING)
    logging.getLogger('matplotlib').setLevel(logging.WARNING)
    
    # Variáveis de ambiente para suprimir ChromeDriver
    os.environ['WDM_LOG_LEVEL'] = '0'
    os.environ['WDM_PRINT_FIRST_LINE'] = 'False'
    os.environ['WDM_LOG'] = 'false'
    
    logging.info("Sistema de logs configurado")


def get_logger(name: str) -> logging.Logger:
    """
    Retorna um logger configurado para o módulo especificado.
    
    Args:
        name: Nome do módulo
        
    Returns:
        Logger configurado
    """
    return logging.getLogger(name)