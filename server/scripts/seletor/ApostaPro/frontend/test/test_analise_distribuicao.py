# test_analise_distribuicao.py
import sys
import os
import pytest

# Adiciona o diretório raiz ao path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

# Agora podemos importar corretamente
from apps.ApostaPro.backend.otimizador import OtimizadorMultiplas
from apps.ApostaPro.frontend.modules.analise_distribuicao import AnalisadorDistribuicao

class TestAnaliseDistribuicao:
    @pytest.fixture
    def setup_otimizador(self):
        otimizador = OtimizadorMultiplas()
        # Adiciona 2 partidas de exemplo
        partida1 = {
            'casa': 1.80,
            'empate': 3.20,
            'fora': 4.50,
            'under_25': 1.75,
            'ambas_nao': 1.85
        }
        partida2 = {
            'casa': 1.80,
            'empate': 3.20,
            'fora': 4.50,
            'under_25': 1.75,
            'ambas_nao': 1.85
        }
        otimizador.adicionar_partida(partida1)
        otimizador.adicionar_partida(partida2)
        return otimizador

    def test_estrutura_combinacoes(self, setup_otimizador):
        otimizador = setup_otimizador
        resultado = otimizador.calcular_distribuicao(20.0, 0.05)

        for comb in resultado['combinacoes']:
            assert len(comb) == 6, f"Combinação com tamanho incorreto: {comb}"

        analisador = AnalisadorDistribuicao(resultado)
        analise = analisador.analisar_distribuicao()

        assert 'distribuicao_principal' in analise
        assert 'por_tipo_mercado' in analise
        assert 'estatisticas' in analise

    def test_formato_combinacoes(self, setup_otimizador):
        otimizador = setup_otimizador
        resultado = otimizador.calcular_distribuicao(20.0, 0.05)

        for comb in resultado['combinacoes']:
            for i in range(0, len(comb), 3):
                assert comb[i] in ['casa', 'empate', 'fora']
                assert comb[i+1] == 'under_25'
                assert comb[i+2] == 'ambas_nao'
                
    def test_analise_distribuicao(self, setup_otimizador):
        otimizador = setup_otimizador
        resultado = otimizador.calcular_distribuicao(20.0, 0.05)
        
        # Testa o analisador
        analisador = AnalisadorDistribuicao(resultado)
        analise = analisador.analisar_distribuicao()
        
        # Verifica os principais resultados
        assert isinstance(analise, dict)
        assert 'distribuicao_principal' in analise
        assert 'por_tipo_mercado' in analise
        assert 'estatisticas' in analise
        
        # Verifica o formato da distribuição principal
        df_principal = analise['distribuicao_principal']
        assert not df_principal.empty
        assert 'Combinação' in df_principal.columns
        assert 'Valor (R$)' in df_principal.columns
        
        # Verifica se todas as combinações estão presentes
        assert len(df_principal) == len(resultado['combinacoes'])