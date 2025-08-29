import sys
import os
import pytest

# Adiciona o diretório frontend ao path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'frontend')))

from frontend.modules.multiplas import GerenciadorMultiplas
from backend.otimizador import OtimizadorMultiplas

class TestGerenciadorMultiplas:

    @pytest.fixture
    def gerenciador(self):
        """Retorna uma instância do GerenciadorMultiplas."""
        return GerenciadorMultiplas()

    @pytest.fixture
    def partidas_validas(self):
        """Retorna um exemplo de dados de partidas válidas (sem 'ambas_sim')."""
        return [
            {
                'casa': 1.8, 'empate': 3.2, 'fora': 4.5,
                'under_25': 1.75, 'ambas_nao': 1.85
            }
        ]

    @pytest.fixture
    def partidas_incompletas(self):
        """Retorna um exemplo de dados de partidas incompletas (falta 'fora')."""
        return [
            {
                'casa': 1.8, 'empate': 3.2, # 'fora' está faltando
                'under_25': 1.75, 'ambas_nao': 1.85
            }
        ]

    def test_otimizar_com_dados_corretos(self, gerenciador, partidas_validas):
        """
        Testa se o método otimizar_distribuicao funciona com os dados corretos
        (depois que você corrigir o bug de validação 'ambas_sim').
        Este teste irá falhar ANTES da correção e passar DEPOIS.
        """
        capital = 100.0
        tolerancia = 0.01

        # A chamada não deve levantar uma exceção de "Odds incompletas"
        resultado = gerenciador.otimizar_distribuicao(partidas_validas, capital, tolerancia)

        # Verifica se o resultado não é um erro
        assert 'erro' not in resultado
        assert resultado.get('tipo_distribuicao') != 'erro'

    def test_otimizar_com_dados_incompletos(self, gerenciador, partidas_incompletas):
        """
        Testa se o método otimizar_distribuicao corretamente identifica
        quando uma odd essencial está faltando.
        """
        capital = 100.0
        tolerancia = 0.01

        resultado = gerenciador.otimizar_distribuicao(partidas_incompletas, capital, tolerancia)

        # Verifica se um erro apropriado foi retornado
        assert 'erro' in resultado
        assert "não encontrada" in resultado['erro'] # O erro vem do adicionar_partida no Otimizador