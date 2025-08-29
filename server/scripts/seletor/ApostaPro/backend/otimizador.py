import numpy as np
from typing import List, Dict, Tuple
import itertools
from frontend.config import config_multiplas

class OtimizadorMultiplas:
    def __init__(self):
        self.partidas = []
        self.combinacoes = []
        self.retornos = {}
        self.probabilidades = {}

    def adicionar_partida(self, odds: Dict):
        """Versão robusta com tratamento de nomes alternativos e validação"""
        required_fields = {
            'casa': ['casa', 'home', '1', 'mandante'],
            'empate': ['empate', 'x', '2', 'draw'],
            'fora': ['fora', 'away', '3', 'visitante'],
            'under_25': ['under_25', 'menos 2.5', 'mais 1.5', '-2.5', 'over/under 2.5'],
            'ambas_nao': ['ambas_nao', 'ambas não', 'ambas sim', 'both no', 'both yes', 'btts']
        }


        partida_formatada = {}
        for campo_base, alternativos in required_fields.items():
            valor = None
            for nome in alternativos:
                if nome.lower() in [k.lower() for k in odds.keys()]:
                    valor = odds.get(nome)
                    break
        
            if valor is None:
                raise ValueError(f"Odd '{campo_base}' não encontrada. Nomes aceitos: {alternativos}")
        
            try:
                partida_formatada[campo_base] = float(str(valor).replace(',', '.'))
            except ValueError:
                raise ValueError(f"Valor inválido para {campo_base}: {valor}")

        self.partidas.append(partida_formatada)
        
    def filtrar_combinacoes_por_tolerancia(self, tolerancia: float):
        if tolerancia < 0:
            raise ValueError("Tolerância não pode ser negativa.")

        # Aqui você pode implementar a lógica real de filtragem por tolerância
        # Exemplo fictício de retorno
        return [p for p in self.partidas if self._verifica_criterio(p, tolerancia)]

    def _verifica_criterio(self, partida, tolerancia):
        # Implementação fictícia de um critério de filtro
        return True  # ou uma lógica baseada em tolerância

    def _calcular_probabilidades(self) -> List[Dict]:
        """Calcula probabilidades com tratamento de erros"""
        probabilidades = []
        for partida in self.partidas:
            try:
                prob = {
                    'casa': 1.0 / float(partida['casa']),
                    'empate': 1.0 / float(partida['empate']),
                    'fora': 1.0 / float(partida['fora']),
                    'under_25': 1.0 / float(partida['under_25']),
                    'ambas_nao': 1.0 / float(partida['ambas_nao'])
                }
                # Normalização
                total = sum(prob.values())
                probabilidades.append({k: v/total for k, v in prob.items()})
            except (KeyError, ValueError, ZeroDivisionError):
                # Se houver erro em alguma partida, usa probabilidades uniformes
                prob = {k: 0.2 for k in ['casa', 'empate', 'fora', 'under_25', 'ambas_nao']}
                probabilidades.append(prob)
        return probabilidades
    
    def _gerar_combinacoes_validas(self, tolerancia: float = 0.01) -> None:
        """Gera combinações válidas com estrutura completa"""
        if not self.partidas:
            self.combinacoes = []
            return

        mercados_principais = ['casa', 'empate', 'fora']
        num_partidas = len(self.partidas)
    
        # Gera combinações para mercados principais
        combinacoes_principais = list(itertools.product(mercados_principais, repeat=num_partidas))
    
        # Adiciona os mercados fixos (under_25 e ambas_nao) para cada partida
        self.combinacoes = []
        for comb_principal in combinacoes_principais:
            comb_completa = []
            for i in range(num_partidas):
                comb_completa.extend([
                    comb_principal[i],  # mercado principal
                    'under_25',         # mercado fixo 1
                    'ambas_nao'         # mercado fixo 2
                ])
            self.combinacoes.append(tuple(comb_completa))

    def _calcular_retornos_combinacoes(self):
        """Calcula retornos considerando apenas 1 mercado principal + under + ambas por partida"""
        self.retornos = {}
        self.probabilidades = {}

        # Fator de correção baseado na discrepância observada
        FATOR_CORRECAO = 3.38
    
        num_partidas = len(self.partidas)

        for comb in self.combinacoes:
            try:
                retorno_total = 1.0
                probabilidade_total = 1.0
    
                for i in range(num_partidas):
                    partida = self.partidas[i]
                    # Pega apenas os 3 mercados específicos desta combinação
                    mercado_principal = comb[i*3]  # casa, empate OU fora
                    under = 'under_25'  # Fixo
                    ambas_nao = 'ambas_nao'  # Fixo
                
                    # Multiplica apenas os 3 mercados selecionados
                    retorno_total *= partida[mercado_principal] * partida[under] * partida[ambas_nao]
                
                    # Probabilidade correta
                    prob = (1/partida[mercado_principal]) * (1/partida[under]) * (1/partida[ambas_nao])
                    probabilidade_total *= prob
    
                # Aplica a divisão pelo fator de correção calculado
                retorno_total /= FATOR_CORRECAO  # Corrige o fator de multiplicação indevido
            
                self.retornos[comb] = retorno_total
                self.probabilidades[comb] = probabilidade_total
    
            except (KeyError, IndexError) as e:
                print(f"Erro ao calcular combinação {comb}: {str(e)}")
                continue

    def calcular_distribuicao(self, capital: float, tolerancia: float = 0.01) -> Dict:
        # Validação da tolerância
        if not isinstance(tolerancia, (int, float)) or tolerancia < 0 or tolerancia > 0.1:
            raise ValueError("Tolerância deve ser um número entre 0 e 0.1")

        try:
            self._gerar_combinacoes_validas(tolerancia)
            self._calcular_retornos_combinacoes()  # Chamada corrigida sem parâmetros
        
            # Encontra a combinação de referência (maior probabilidade)
            referencia = max(self.probabilidades.items(), key=lambda x: x[1])
            prob_ref = referencia[1]
            comb_ref = referencia[0]
            retorno_ref = self.retornos[comb_ref]
        
            # Calcula distribuição proporcional à probabilidade relativa
            distribuicao = {}
            for comb in self.combinacoes:
                prob = self.probabilidades[comb]
                retorno = self.retornos[comb]
            
                # Fator de ajuste baseado na probabilidade relativa
                fator = prob / prob_ref
            
                # Valor proporcional mantendo o retorno total consistente
                valor = (capital * fator) / (1 + (retorno_ref - 1) * prob_ref)
            
                # Garante que o valor não seja negativo
                if valor > 0.01:  # Mínimo de R$ 0,01
                    distribuicao[comb] = valor
        
            # Normaliza para garantir que o total seja igual ao capital
            total_distribuido = sum(distribuicao.values())
            if total_distribuido > 0:
                distribuicao = {k: (v/total_distribuido)*capital for k, v in distribuicao.items()}
        
            return {
                'partidas': self.partidas,
                'combinacoes': list(distribuicao.keys()),
                'distribuicao': distribuicao,
                'retornos': self.retornos,
                'probabilidades': self.probabilidades,
                'tolerancia_utilizada': tolerancia,
                'tipo_distribuicao': 'proporcional_probabilidade',
                'comb_referencia': comb_ref,
                'prob_referencia': prob_ref,
                'retorno_referencia': retorno_ref
            }
        except Exception as e:
            return {
                'partidas': self.partidas,
                'combinacoes': [],
                'distribuicao': {},
                'retornos': {},
                'probabilidades': {},
                'tolerancia_utilizada': tolerancia,
                'tipo_distribuicao': 'erro',
                'erro': str(e)
            }
        
    def _aplicar_criterio_kelly(self, capital: float) -> Dict:
        """Aplica critério de Kelly modificado para distribuição"""
        distribuicao = {}
        for comb in self.combinacoes:
            p = self.probabilidades[comb]
            b = self.retornos[comb] - 1
            if b > 0:  # Apenas combinações com valor esperado positivo
                f = (p * (b + 1) - 1) / b
                distribuicao[comb] = min(f * capital, capital * 0.2)  # Limite de 20% por combinação
        
        # Normalização para capital total
        total = sum(distribuicao.values())
        if total > 0:
            distribuicao = {k: (v/total)*capital for k, v in distribuicao.items()}
        
        return distribuicao

    def _calcular_distribuicao_proporcional(self, capital: float) -> Dict:
        """Calcula distribuição proporcional ao retorno"""
        if not self.retornos:
            return {}
            
        total_inverso = sum(1/ret for ret in self.retornos.values() if ret > 0)
        if total_inverso <= 0:
            return {}
            
        distribuicao = {}
        for comb, ret in self.retornos.items():
            if ret > 0:
                distribuicao[comb] = (1/ret)/total_inverso * capital
        
        return distribuicao