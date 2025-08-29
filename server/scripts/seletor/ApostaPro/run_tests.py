import pytest
import sys
import os

if __name__ == "__main__":
    # Adiciona o diretório ao path
    sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
    
    # Executa os testes
    pytest.main(['frontend/test/test_otimizador.py', '-v'])