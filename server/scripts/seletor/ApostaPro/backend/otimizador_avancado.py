# backend/otimizador_avancado.py (ATUALIZADO)
import numpy as np
from typing import Dict, List, Tuple
from itertools import product
import math

class OtimizadorMultiplasAvancado:
    def __init__(self):
        self.partidas = []

    def adicionar_partida(self, odds: Dict):
        """Adiciona uma partida com todas as odds e horário"""
        self.partidas.append({
            'favorito': float(odds['favorito']),
            'dupla_chance': float(odds['dupla_chance']),
            'mais15': float(odds['mais15']),
            'under15': float(odds['under15']),
            'horario': odds.get('horario'),
            'nome': odds.get('partida', f'Partida {len(self.partidas)+1}')
        })

    def _calcular_custo_protecao(self, valor_para_multiplas: float, capital_total: float) -> float:
        """Calcula o custo total necessário para a proteção em camadas"""
        partidas_ordenadas = sorted(self.partidas, key=lambda x: x.get('horario', 0))
        num_partidas = len(partidas_ordenadas)
        if num_partidas == 0:
            return 0

        # Cálculo simplificado e mais preciso da proteção
        custo_total = 0
        valor_a_cobrir = valor_para_multiplas
    
        for i, partida in enumerate(partidas_ordenadas):
            odd = partida['under15']
            if odd <= 1:
                return float('inf')
        
            # Cálculo principal (30%)
            stake_principal = (valor_a_cobrir * 0.3) / (odd - 1)
        
            # Cálculo secundário (30%)
            stake_secundario = (valor_a_cobrir * 0.3) / (odd * 0.8 - 1)
        
            custo_total += stake_principal + stake_secundario
            valor_a_cobrir += stake_principal + stake_secundario  # Atualiza o valor a cobrir
        
        return custo_total

    def _encontrar_alocacao_ideal(self, capital_total: float, percentual_risco_slider: float) -> Tuple[float, float]:
        """Encontra a divisão ideal entre múltiplas e proteção"""
        # Ajuste inicial baseado no slider
        valor_multiplas = capital_total * (1 - percentual_risco_slider)
        valor_protecao = capital_total * percentual_risco_slider
    
        # Ajuste fino para garantir cobertura total
        for _ in range(50):  # Aumentei o número de iterações
            custo_protecao = self._calcular_custo_protecao(valor_multiplas, capital_total)
            total_calculado = valor_multiplas + custo_protecao
        
            if math.isclose(total_calculado, capital_total, rel_tol=1e-4):
                break
                
            # Ajusta proporcionalmente
            fator_ajuste = capital_total / total_calculado
            valor_multiplas *= fator_ajuste
    
        # Garante que não ultrapasse o capital total
        valor_multiplas = min(valor_multiplas, capital_total)
        valor_protecao = self._calcular_custo_protecao(valor_multiplas, capital_total)
    
        return valor_multiplas, valor_protecao

    def _distribuir_stake_multiplas_otimizado(self, multiplas: List[Dict], valor_total_multiplas: float, capital_total: float) -> List[Dict]:
        """Distribui o stake das múltiplas mantendo a regra de retorno total"""
        if not multiplas:
            return []
        
        num_selecionar = min(len(multiplas), 6)
        top_multiplas = sorted(multiplas, key=lambda x: x['probabilidade'], reverse=True)[:num_selecionar]

        if not top_multiplas:
            return []

        multipla_risco = top_multiplas[-1]
        odd_risco = multipla_risco['odd_combinada']
        stake_risco = capital_total / odd_risco if odd_risco > 0 else 0
            
        multipla_risco['valor'] = min(stake_risco, valor_total_multiplas)
        multipla_risco['retorno'] = multipla_risco['valor'] * odd_risco

        valor_restante = valor_total_multiplas - multipla_risco['valor']
        outras_multiplas = top_multiplas[:-1]
        soma_prob = sum(m['probabilidade'] for m in outras_multiplas)
        
        if soma_prob > 0 and valor_restante > 0:
            for m in outras_multiplas:
                proporcao = m['probabilidade'] / soma_prob
                m['valor'] = valor_restante * proporcao
                m['retorno'] = m['valor'] * m['odd_combinada']
        
        return top_multiplas

    def _gerar_distribuicao_protecao_final(self, valor_multiplas: float, capital_total: float) -> Dict:
        """Gera a distribuição final da proteção com camadas"""
        partidas_ordenadas = sorted(self.partidas, key=lambda x: x.get('horario', 0))
        distribuicao = []
        custo_acumulado = 0
        
        for i, partida in enumerate(partidas_ordenadas):
            odd = partida['under15']
            
            if i == len(partidas_ordenadas) - 1:
                stake_principal = (capital_total / odd) * 0.3
                stake_secundario = (capital_total / (odd * 0.8)) * 0.3
            else:
                valor_a_cobrir = (valor_multiplas + custo_acumulado) * 0.3
                stake_principal = valor_a_cobrir / (odd - 1) if odd > 1 else 0
                stake_secundario = valor_a_cobrir / (odd * 0.8 - 1) if odd * 0.8 > 1 else 0

            distribuicao.append({
                'partida': partida['nome'],
                'valor_investido': stake_principal + stake_secundario,
                'odd_protecao': odd,
                'retorno_potencial': (stake_principal * odd) + (stake_secundario * odd * 0.8),
                'cobertura_necessaria': (valor_multiplas + custo_acumulado) * 0.6,
                'horario': partida.get('horario')
            })
            custo_acumulado += stake_principal + stake_secundario
        
        return {
            'valor_total': custo_acumulado,
            'distribuicao': distribuicao,
            'valor_futuro': capital_total * 0.4
        }

    def calcular_distribuicao(self, capital_total: float, percentual_protecao: float) -> Dict:
        """Orquestra todo o processo de otimização"""
        if not self.partidas:
            return {}
            
        valor_multiplas, valor_protecao = self._encontrar_alocacao_ideal(
            capital_total, percentual_protecao
        )

        combinacoes = self._gerar_combinacoes_otimizadas()
        multiplas_finais = self._distribuir_stake_multiplas_otimizado(
            combinacoes, valor_multiplas, capital_total
        )
        
        protecao_final = self._gerar_distribuicao_protecao_final(
            valor_multiplas, capital_total
        )

        return {
            'multiplas': multiplas_finais,
            'protecao': protecao_final,
            'total_multiplas': valor_multiplas,
            'retorno_maximo_multiplas': sum(m['retorno'] for m in multiplas_finais if m.get('retorno')),
            'capital_total': capital_total,
            'capital_utilizado': valor_multiplas + valor_protecao + (capital_total * 0.4),
            'valor_futuro': capital_total * 0.4
        }

    def _gerar_combinacoes_otimizadas(self) -> List[Dict]:
        """Gera combinações de apostas múltiplas"""
        num_partidas = len(self.partidas)
        combinacoes = []
        for comb in product([0, 1], repeat=num_partidas):
            multipla = self._calcular_multipla(comb)
            combinacoes.append(multipla)
        return combinacoes

    def _calcular_multipla(self, comb: tuple) -> Dict:
        """Calcula os dados de uma múltipla específica"""
        apostas = []
        odd_combinada = 1.0
        probabilidade = 1.0
        for i, tipo in enumerate(comb):
            partida = self.partidas[i]
            if tipo == 0:
                odd_aposta = partida['favorito'] * partida['mais15']
                prob = (1/partida['favorito']) * (1/partida['mais15'])
                tipo_aposta = 'Favorito + Mais 1.5'
            else:
                odd_aposta = partida['dupla_chance'] * partida['mais15']
                prob = (1/partida['dupla_chance']) * (1/partida['mais15'])
                tipo_aposta = 'Empate/Azarão + Mais 1.5'
            
            apostas.append({'tipo': tipo_aposta, 'odd': odd_aposta})
            odd_combinada *= odd_aposta
            probabilidade *= prob
        
        return {
            'apostas': apostas,
            'odd_combinada': odd_combinada,
            'probabilidade': probabilidade,
        }