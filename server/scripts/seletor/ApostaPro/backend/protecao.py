from typing import Dict, List
from dataclasses import dataclass
from enum import Enum
import numpy as np

class TipoProtecao(Enum):
    """Tipos de estratégias de proteção disponíveis"""
    HEDGE = "Proteção por Hedge"
    CASHOUT = "Cashout Parcial"
    DUPLA_CHANCE = "Dupla Chance"
    UNDER_OVER = "Ajuste Under/Over"
    AMBAS_MARCAM = "Ajuste Ambas Marcam"

@dataclass
class EstrategiaProtecao:
    tipo: TipoProtecao
    valor: float
    odd: float
    descricao: str
    partidas_afetadas: List[int]

class GerenciadorProtecoes:
    def __init__(self):
        self.estrategias = []
    
    def calcular_protecoes(self, partidas: List[Dict], capital_disponivel: float) -> List[EstrategiaProtecao]:
        """Calcula estratégias de proteção baseadas nas partidas"""
        estrategias = []
        
        # 1. Proteção para Under 2.5 global
        odd_under = np.prod([p['under_25'] for p in partidas])
        estrategias.append(EstrategiaProtecao(
            tipo=TipoProtecao.UNDER_OVER,
            valor=capital_disponivel * 0.3,
            odd=odd_under,
            descricao="Proteção global para menos de 2.5 gols em todas partidas",
            partidas_afetadas=list(range(len(partidas)))
        ))
        
        # 2. Proteção para Ambas Marcam Não
        odd_ambas_nao = np.prod([p['ambas_marcam'] for p in partidas])
        estrategias.append(EstrategiaProtecao(
            tipo=TipoProtecao.AMBAS_MARCAM,
            valor=capital_disponivel * 0.3,
            odd=odd_ambas_nao,
            descricao="Proteção global para ambas NÃO marcarem",
            partidas_afetadas=list(range(len(partidas)))
        ))
        
        # 3. Cashout parcial
        estrategias.append(EstrategiaProtecao(
            tipo=TipoProtecao.CASHOUT,
            valor=capital_disponivel * 0.2,
            odd=1.0,
            descricao="Reserva para cashout parcial",
            partidas_afetadas=[]
        ))
        
        # 4. Hedge para partidas com odds mais desbalanceadas
        for i, p in enumerate(partidas):
            if max(p['casa'], p['empate'], p['fora']) > 2.5:
                estrategias.append(EstrategiaProtecao(
                    tipo=TipoProtecao.DUPLA_CHANCE,
                    valor=capital_disponivel * 0.2 / len(partidas),
                    odd=min(p['casa'] + p['empate'], p['empate'] + p['fora']),
                    descricao=f"Dupla chance na partida {i+1}",
                    partidas_afetadas=[i]
                ))
        
        self.estrategias = estrategias
        return estrategias
    
    def aplicar_protecao(self, resultados: Dict[int, str]) -> Dict:
        """Aplica as proteções com base nos resultados parciais"""
        retorno_total = 0
        detalhes = []
        
        for estrategia in self.estrategias:
            if estrategia.tipo == TipoProtecao.UNDER_OVER:
                gols_total = sum(resultados.values())
                ganhou = gols_total < 2.5 * len(resultados)
                retorno = estrategia.valor * (estrategia.odd - 1) if ganhou else -estrategia.valor
                
            elif estrategia.tipo == TipoProtecao.AMBAS_MARCAM:
                ambas_marcaram = all(v > 0 for v in resultados.values())
                retorno = estrategia.valor * (estrategia.odd - 1) if not ambas_marcaram else -estrategia.valor
                
            elif estrategia.tipo == TipoProtecao.DUPLA_CHANCE:
                # Implementação simplificada - precisa ser ajustada
                retorno = -estrategia.valor * 0.5  # Exemplo simplificado
                
            else:  # CASHOUT
                retorno = -estrategia.valor * 0.1  # Pequena perda no cashout
                
            retorno_total += retorno
            detalhes.append({
                'tipo': estrategia.tipo.value,
                'retorno': retorno,
                'descricao': estrategia.descricao
            })
        
        return {
            'retorno_total': retorno_total,
            'detalhes': detalhes
        }