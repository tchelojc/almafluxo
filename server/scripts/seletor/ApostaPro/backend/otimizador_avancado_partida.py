# backend/otimizador_avancado_partida.py
import numpy as np
from typing import Dict, List
import math

# backend/otimizador_avancado_partida.py (versão corrigida)
class OtimizadorMultiplasPartida:
    def __init__(self):
        self.partida = None
    
    def adicionar_partida(self, odds: Dict):
        self.partida = {
            'favorito': float(odds['favorito']),
            'dupla_chance': float(odds['dupla_chance']),
            'mais25': float(odds['mais25']),
            'menos25': float(odds['menos25']),
            'mais15_1t': float(odds['mais15_1t']),
            'menos15_1t': float(odds['menos15_1t'])
        }
    
    def calcular_distribuicao(self, capital_total: float) -> Dict:
        # Divide o capital igualmente entre os dois blocos
        capital_por_bloco = capital_total / 2
        
        # Gera as combinações para cada bloco
        bloco_under = self._gerar_bloco_under()
        bloco_over = self._gerar_bloco_over()
        
        # Balanceia cada bloco independentemente
        under_balanceado = self._balancear_bloco(bloco_under, capital_por_bloco)
        over_balanceado = self._balancear_bloco(bloco_over, capital_por_bloco)
        
        return {
            'multiplas': under_balanceado + over_balanceado,
            'capital_total': capital_total
        }
    
    def _gerar_bloco_under(self) -> List[Dict]:
        """Gera as combinações do bloco Under 2.5"""
        p = self.partida
        return [
            {
                'apostas': [
                    {'tipo': 'Menos 2.5 Gols/Favorito', 'odd': p['menos25']},
                    {'tipo': 'Favorito/Mais 0,5 1ºT', 'odd': p['favorito']}
                ],
                'odd_combinada': p['menos25'] * p['favorito'],
                'probabilidade': (1/p['menos25']) * (1/p['favorito'])
            },
            {
                'apostas': [
                    {'tipo': 'Menos 2.5 Gols/Favorito', 'odd': p['menos25']},
                    {'tipo': 'Empate/Azarão/Menos 0,5 1ºT', 'odd': p['dupla_chance']}
                ],
                'odd_combinada': p['menos25'] * p['dupla_chance'],
                'probabilidade': (1/p['menos25']) * (1/p['dupla_chance'])
            }
        ]
    
    def _gerar_bloco_over(self) -> List[Dict]:
        """Gera as combinações do bloco Over 2.5"""
        p = self.partida
        return [
            {
                'apostas': [
                    {'tipo': 'Mais 2.5 Gols/Empate/Azarão', 'odd': p['mais25']},
                    {'tipo': 'Mais 1.5 Gols 1T/Par', 'odd': p['mais15_1t']}
                ],
                'odd_combinada': p['mais25'] * p['mais15_1t'],
                'probabilidade': (1/p['mais25']) * (1/p['mais15_1t'])
            },
            {
                'apostas': [
                    {'tipo': 'Mais 2.5 Gols/Empate/Azarão', 'odd': p['mais25']},
                    {'tipo': 'Menos 1.5 Gols 1T/Ímpar', 'odd': p['menos15_1t']}
                ],
                'odd_combinada': p['mais25'] * p['menos15_1t'],
                'probabilidade': (1/p['mais25']) * (1/p['menos15_1t'])
            }
        ]
    
    def _balancear_bloco(self, multiplas: List[Dict], capital_bloco: float) -> List[Dict]:
        """Balanceia um bloco para que todas as múltiplas tenham o MESMO RETORNO"""
        retorno_alvo = capital_bloco / len(multiplas) * 2  # Retorno igual para todas
    
        for m in multiplas:
            m['valor'] = retorno_alvo / m['odd_combinada']
            m['retorno'] = m['valor'] * m['odd_combinada']
            m['lucro'] = m['retorno'] - m['valor']
            m['roi'] = (m['lucro'] / m['valor']) * 100
    
        return multiplas