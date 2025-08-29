import numpy as np
from typing import Dict, List, Tuple
from dataclasses import dataclass
from enum import Enum

class Resultado(Enum):
    CASA = "casa"
    EMPATE = "empate"
    FORA = "fora"

@dataclass
class Partida:
    id: str
    hora: str
    casa: float
    empate: float
    fora: float
    under_25: float
    ambas_marcam: float

@dataclass
class ApostaMultipla:
    partidas: List[Partida]
    combinacao: List[Resultado]
    valor: float
    retorno: float
    probabilidade: float

class CalculadoraApostas:
    def __init__(self):
        self.partidas = []
        self.multiplicador_seguranca = 0.7  # 70% do capital para apostas iniciais
    
    def adicionar_partida(self, partida: Partida):
        self.partidas.append(partida)
    
    def calcular_combinacoes(self, num_partidas: int) -> List[List[Resultado]]:
        resultados = list(Resultado)
        return list(itertools.product(resultados, repeat=num_partidas))
    
    def calcular_retorno(self, combinacao: List[Resultado], valor: float) -> float:
        odd_total = 1.0
        for i, resultado in enumerate(combinacao):
            partida = self.partidas[i]
            odd = getattr(partida, resultado.value)
            odd_total *= odd
        return valor * odd_total
    
    def calcular_probabilidade(self, combinacao: List[Resultado]) -> float:
        prob_total = 1.0
        for i, resultado in enumerate(combinacao):
            partida = self.partidas[i]
            odd = getattr(partida, resultado.value)
            prob_total *= 1 / odd
        return prob_total
    
    def gerar_estrategia_otimizada(self, capital_total: float) -> Dict:
        # 1. Distribuição inicial (70% do capital)
        capital_inicial = capital_total * self.multiplicador_seguranca
        capital_protecao = capital_total - capital_inicial
        
        # 2. Gerar todas combinações possíveis
        combinacoes = self.calcular_combinacoes(len(self.partidas))
        
        # 3. Calcular retornos e probabilidades
        apostas = []
        for combinacao in combinacoes:
            retorno = self.calcular_retorno(combinacao, capital_inicial)
            probabilidade = self.calcular_probabilidade(combinacao)
            apostas.append({
                'combinacao': combinacao,
                'retorno': retorno,
                'probabilidade': probabilidade,
                'roi': (retorno * probabilidade) / capital_inicial - 1
            })
        
        # 4. Ordenar por ROI esperado
        apostas.sort(key=lambda x: -x['roi'])
        
        # 5. Selecionar as melhores distribuídas
        num_apostas = min(10, len(apostas))
        selecionadas = []
        for i in range(num_apostas):
            idx = int(i * len(apostas) / num_apostas)
            selecionadas.append(apostas[idx])
        
        # 6. Distribuir o capital proporcionalmente
        total_inverso = sum(1/x['retorno'] for x in selecionadas)
        for aposta in selecionadas:
            aposta['valor_apostado'] = (1/aposta['retorno'])/total_inverso * capital_inicial
            aposta['retorno_proporcional'] = aposta['valor_apostado'] * (aposta['retorno'] / capital_inicial)
        
        # 7. Preparar estratégia de proteção
        protecoes = self._calcular_protecoes(capital_protecao)
        
        return {
            'apostas_principais': selecionadas,
            'estrategia_protecao': protecoes,
            'capital_total': capital_total,
            'capital_alocado': sum(x['valor_apostado'] for x in selecionadas) + sum(x['valor'] for x in protecoes)
        }
    
    def _calcular_protecoes(self, capital: float) -> List[Dict]:
        """Calcula apostas de proteção baseadas em under/over e ambas marcam"""
        protecoes = []
        
        # Under 2.5 para todas partidas
        odd_under_total = 1.0
        for partida in self.partidas:
            odd_under_total *= partida.under_25
        
        protecoes.append({
            'tipo': 'under_25_multipla',
            'odd': odd_under_total,
            'valor': capital * 0.4,
            'descricao': 'Menos de 2.5 gols em todas partidas'
        })
        
        # Ambas marcam "Não" para todas partidas
        odd_ambas_nao_total = 1.0
        for partida in self.partidas:
            odd_ambas_nao_total *= partida.ambas_marcam
        
        protecoes.append({
            'tipo': 'ambas_nao_multipla',
            'odd': odd_ambas_nao_total,
            'valor': capital * 0.4,
            'descricao': 'Ambas NÃO marcam em todas partidas'
        })
        
        # Cashout parcial (20%)
        protecoes.append({
            'tipo': 'reserva_cashout',
            'valor': capital * 0.2,
            'descricao': 'Reserva para cashout ou ajustes'
        })
        
        return protecoes