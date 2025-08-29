# tests/test_tolerancia.py
import pytest
from backend.otimizador import OtimizadorMultiplas
from typing import List, Dict

class TestTolerancia:
    @pytest.fixture
    def partidas_exemplo(self) -> List[Dict]:
        return [
            {
                'casa': 1.8, 'empate': 3.2, 'fora': 4.5,
                'under_25': 1.75, 'ambas_nao': 1.85
            },
            {
                'casa': 1.8, 'empate': 3.2, 'fora': 4.5,
                'under_25': 1.7, 'ambas_nao': 2.1
            }
        ]

    def test_tolerancia_padrao(self, partidas_exemplo):
        """Testa se a tolerância padrão (0.01) funciona corretamente"""
        otimizador = OtimizadorMultiplas()
        for partida in partidas_exemplo:
            otimizador.adicionar_partida(partida)
    
        resultado = otimizador.calcular_distribuicao(100.0)
    
        assert 'tolerancia_utilizada' in resultado
        assert resultado['tolerancia_utilizada'] == 0.01
    
        # Verifica se tem combinações ou se usou fallback
        if not resultado['combinacoes']:
            assert resultado['tipo_distribuicao'] in ['sem_combinacoes_validas', 'fallback_emergencial']
        else:
            # Verifica estrutura das combinações
            for comb in resultado['combinacoes']:
                assert len(comb) == len(partidas_exemplo) * 3
                for i in range(0, len(comb), 3):
                    assert comb[i] in ['casa', 'empate', 'fora']
                    assert comb[i+1] == 'under_25'
                    assert comb[i+2] == 'ambas_nao'
            
    def test_tolerancia_zero(self, partidas_exemplo):
        """Teste com tolerância zero usando dados do fixture diretamente"""
        otimizador = OtimizadorMultiplas()
        for partida in partidas_exemplo:
            otimizador.adicionar_partida(partida)  # Usa o dicionário diretamente
    
        resultado = otimizador.calcular_distribuicao(100.0, tolerancia=0.0)
        assert len(resultado['combinacoes']) > 0

    def test_tolerancia_alta(self, partidas_exemplo):
        """Testa tolerância alta (0.1)"""
        otimizador = OtimizadorMultiplas()
        for partida in partidas_exemplo:
            otimizador.adicionar_partida(partida)
        
        resultado = otimizador.calcular_distribuicao(100.0, tolerancia=0.1)
        assert resultado['tolerancia_utilizada'] == 0.1
        assert len(resultado['combinacoes']) > 0

    def test_tolerancia_invalida(self, partidas_exemplo):
        """Testa valores de tolerância inválidos"""
        otimizador = OtimizadorMultiplas()
        for partida in partidas_exemplo:
            otimizador.adicionar_partida(partida)
        
        # Tolerância negativa
        with pytest.raises(ValueError):
            otimizador.calcular_distribuicao(100.0, tolerancia=-0.1)
        
        # Tolerância maior que 0.1
        with pytest.raises(ValueError):
            otimizador.calcular_distribuicao(100.0, tolerancia=0.2)

    def test_filtro_combinacoes_por_tolerancia(self, partidas_exemplo):
        """Testa se as combinações são filtradas corretamente pela tolerância"""
        otimizador = OtimizadorMultiplas()
        for partida in partidas_exemplo:
            otimizador.adicionar_partida(partida)
        
        # Baixa tolerância (0.01) - menos combinações
        resultado_baixa = otimizador.calcular_distribuicao(100.0, tolerancia=0.01)
        # Alta tolerância (0.1) - mais combinações
        resultado_alta = otimizador.calcular_distribuicao(100.0, tolerancia=0.1)
        
        assert len(resultado_alta['combinacoes']) >= len(resultado_baixa['combinacoes'])
        
    def test_nomes_alternativos(self):
        """Testa se aceita nomes alternativos de campos"""
        otimizador = OtimizadorMultiplas()
        partida = {
            'home': 1.8,  # Alternativo para 'casa'
            'empata': 3.2,  # Alternativo para 'empate'
            'away': 4.5,  # Alternativo para 'fora'
            'menos de 2.5': 1.75,
            'ambas marcam não': 1.85
        }
        otimizador.adicionar_partida(partida)  # Não deve levantar exceção