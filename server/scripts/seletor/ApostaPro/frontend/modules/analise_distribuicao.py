import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
from frontend.config import config

class AnalisadorDistribuicao:
    def __init__(self, resultado_otimizacao: dict):
        """Inicialização com validação robusta"""
        self._validar_entrada(resultado_otimizacao)
        self.resultado = resultado_otimizacao
        self.distribuicao = resultado_otimizacao.get('distribuicao', {})
        self.partidas = resultado_otimizacao.get('partidas', [])
        self.combinacoes = resultado_otimizacao.get('combinacoes', [])
        self.retornos = resultado_otimizacao.get('retornos', {})
        self.probabilidades = resultado_otimizacao.get('probabilidades', {})

    def _validar_entrada(self, dados: Dict):
        """Validação completa dos dados de entrada"""
        required = ['partidas', 'combinacoes', 'distribuicao', 'retornos', 'probabilidades']
        missing = [k for k in required if k not in dados]
        if missing:
            raise ValueError(f"Campos obrigatórios faltantes: {missing}")

        # Verifica consistência no número de elementos
        num_partidas = len(dados['partidas'])
        for comb in dados['combinacoes']:
            if len(comb) != num_partidas * 3:
                raise ValueError(
                    f"Número de partidas incompatível. Esperado {num_partidas*3} "
                    f"elementos, obtido {len(comb)} na combinação {comb}"
                )

    def analisar_distribuicao(self) -> dict:
        """Análise principal com tratamento de erros"""
        try:
            return {
                'distribuicao_principal': self._gerar_dataframe_principal(),
                'por_tipo_mercado': self._analisar_por_tipo_mercado(),
                'estatisticas': self._calcular_estatisticas()
            }
        except Exception as e:
            return {'erro': str(e), 'tipo': 'erro_analise'}

    def _gerar_dataframe_principal(self) -> pd.DataFrame:
        """Gera dataframe com as principais combinações"""
        dados = []
        for comb, valor in self.distribuicao.items():
            if valor > 0:
                retorno_total = self.retornos.get(comb, 1)  # Multiplicação das odds (incluindo stake)
                prob = self.probabilidades.get(comb, 0)

                dados.append({
                    'Combinação': str(comb),
                    'Valor (R$)': valor,
                    'Retorno Potencial': retorno_total,
                    'Retorno Esperado (R$)': valor * retorno_total,  # CORREÇÃO AQUI
                    'Lucro Potencial (R$)': valor * (retorno_total - 1),
                    'Probabilidade': prob,
                    'ROI Esperado': (retorno_total - 1) * prob  # ROI com base em probabilidade e odd
                })

        return pd.DataFrame(dados).sort_values('Valor (R$)', ascending=False)

    def _analisar_por_tipo_mercado(self) -> pd.DataFrame:
        """Agrupa análise por tipo de mercado com nomes exibidos ao usuário"""
        nomes_amigaveis = {
            'casa': 'Time Casa',
            'empate': 'Empate',
            'fora': 'Time Fora',
            'under_25': 'Menos de 2.5 Gols ou Mais de 1.5 Gols',
            'ambas_nao': 'Ambas Não ❌ ou Ambas Sim ✅'
        }

        dados = []
        for tipo in ['casa', 'empate', 'fora', 'under_25', 'ambas_nao']:
            total_valor = 0
            total_retorno = 0
            total_prob = 0
            count = 0

            for comb in self.distribuicao:
                if tipo in comb:
                    valor = self.distribuicao[comb]
                    total_valor += valor
                    total_retorno += valor * (self.retornos.get(comb, 1) - 1)
                    total_prob += self.probabilidades.get(comb, 0)
                    count += 1

            if count > 0:
                dados.append({
                    'Tipo Mercado': nomes_amigaveis[tipo],
                    'Valor (R$)': total_valor,
                    'Retorno Esperado (R$)': total_retorno,
                    'Probabilidade': total_prob / count,
                    'Nº Combinações': count
                })

        return pd.DataFrame(dados).sort_values('Valor (R$)', ascending=False)

    def _calcular_estatisticas(self) -> dict:
        """Calcula estatísticas gerais com tratamento seguro"""
        try:
            total_investido = sum(self.distribuicao.values())
            retorno_esperado = sum(
                valor * (self.retornos.get(comb, 1) - 1)
                for comb, valor in self.distribuicao.items()
            )
            
            return {
                'total_partidas': len(self.partidas),
                'combinacoes_validas': len([v for v in self.distribuicao.values() if v > 0]),
                'capital_total': total_investido,
                'retorno_esperado_total': retorno_esperado,
                'roi_esperado': retorno_esperado / total_investido if total_investido > 0 else 0
            }
        except Exception as e:
            return {'erro': str(e)}
    
    def _analisar_distribuicao_principal(self) -> pd.DataFrame:
        """Cria dataframe com análise detalhada"""
        dados = []
        for comb, valor in self.resultado['distribuicao'].items():
            retorno = self.resultado['retornos'][comb]
            prob = self.resultado['probabilidades'][comb]
            roi = (retorno * prob / valor - 1) if valor > 0 else 0
            
            dados.append({
                'Combinação': self._formatar_combinacao(comb),
                'Valor (R$)': valor,
                'Retorno Esperado (R$)': retorno * prob,
                'Probabilidade': prob,
                'ROI Esperado': roi,
                'Odd Justa': 1/prob if prob > 0 else 0,
                'Tipo': self._identificar_tipo_combinacao(comb)
            })
        
        df = pd.DataFrame(dados)
        return df.sort_values('Retorno Esperado (R$)', ascending=False)
    
    def _calcular_metricas_risco(self) -> Dict:
        """Calcula métricas de risco consolidado"""
        df = self._analisar_distribuicao_principal()
        capital_total = df['Valor (R$)'].sum()
        
        return {
            'var_95': np.percentile(df['Retorno Esperado (R$)'], 5),
            'retorno_esperado_total': df['Retorno Esperado (R$)'].sum(),
            'drawdown_esperado': (df['Valor (R$)'] * (1 - df['Probabilidade'])).sum(),
            'diversificacao': len(df) / len(self.resultado['combinacoes'])
        }
    
    def _calcular_distribuicao_ideal(self) -> Dict:
        """Calcula a distribuição proporcional ideal baseada no retorno esperado"""
        total_inverso = sum(1/ret for ret in self.resultado['retornos'].values())
        capital_total = sum(self.resultado['distribuicao'].values())
        
        distribuicao_ideal = {}
        for comb, ret in self.resultado['retornos'].items():
            distribuicao_ideal[comb] = (1/ret)/total_inverso * capital_total
        
        return distribuicao_ideal
    
    def _formatar_combinacao(self, combinacao: tuple) -> str:
        """Formata a combinação para exibição incluindo os mercados fixos"""
        if not isinstance(combinacao, tuple):
            return str(combinacao)

        num_partidas = len(combinacao)
        partes = []

        for i in range(num_partidas):
            principal = combinacao[i]
            partes.append(f"P{i+1}: {principal} + Under2.5 + AmbasNão")

        return " | ".join(partes)
    
    def _identificar_tipo_combinacao(self, combinacao: Tuple) -> str:
        """Identifica o tipo predominante na combinação"""
        tipos = []
        for mercado in combinacao:
            if mercado.startswith('ambas'):
                tipos.append(mercado)
            elif mercado == 'under_25':
                tipos.append(mercado)
        
        return ', '.join(tipos) if tipos else 'Resultados Principais'
    
    def identificar_top_combinacoes(self, n: int = 10, capital_total: float = 20.0) -> Dict:
        """Versão CORRIGIDA com cálculo preciso de retornos"""
        if not self.combinacoes:
            return {}

        # Encontra a combinação de maior probabilidade como referência
        comb_ref = max(self.combinacoes, key=lambda x: self.probabilidades.get(x, 0))
        prob_ref = self.probabilidades.get(comb_ref, 1e-10)
        retorno_ref = self.retornos.get(comb_ref, 1)

        combinacoes_com_metricas = []
        for comb in self.combinacoes:
            prob = self.probabilidades.get(comb, 0)
            retorno = self.retornos.get(comb, 1)  # Já é o multiplicador TOTAL de todas as partidas
            valor_atual = self.distribuicao.get(comb, 0)
    
            # Distribuição proporcional ao capital
            valor_otimizado = (prob / prob_ref) * (capital_total / n)
    
            # Cálculos CORRETOS:
            retorno_total = valor_otimizado * retorno
            lucro_potencial = retorno_total - valor_otimizado
            roi = (retorno_total - valor_otimizado) / valor_otimizado if valor_otimizado > 0 else 0

            combinacoes_com_metricas.append({
                'combinacao': comb,
                'probabilidade': prob,
                'retorno_potencial': retorno,  # Multiplicador total de odds (ex: 10.05x)
                'valor_otimizado': valor_otimizado,
                'retorno_total': retorno_total,
                'lucro_potencial': lucro_potencial,
                'roi': roi
            })

        # Ordena e ajusta para o capital total
        top_combinacoes = sorted(combinacoes_com_metricas, key=lambda x: -x['probabilidade'])[:n]

        # Normaliza os valores para o capital total
        total = sum(c['valor_otimizado'] for c in top_combinacoes)
        if total > 0:
            for c in top_combinacoes:
                c['valor_otimizado'] = (c['valor_otimizado'] / total) * capital_total
                c['retorno_total'] = c['valor_otimizado'] * c['retorno_potencial']
                c['lucro_potencial'] = c['retorno_total'] - c['valor_otimizado']
                c['roi'] = (c['retorno_total'] - c['valor_otimizado']) / c['valor_otimizado'] if c['valor_otimizado'] > 0 else 0

        return {
            'por_probabilidade': top_combinacoes,
            'referencia': {
                'combinacao': comb_ref,
                'probabilidade': prob_ref,
                'retorno': retorno_ref
            }
        }
        
    def calcular_metricas_avancadas(self, top_combinacoes: List) -> Dict:
        """Calcula métricas avançadas para as top combinações"""
        if not top_combinacoes:
            return {}

        # Cálculo do valor esperado total
        valor_esperado_total = sum(c['valor_esperado'] for c in top_combinacoes)
    
        # Cálculo da probabilidade agregada
        prob_agregada = 1 - np.prod([1 - c['probabilidade'] for c in top_combinacoes])
    
        return {
            'valor_esperado_total': valor_esperado_total,
            'probabilidade_agregada': prob_agregada,
            'retorno_medio': sum(c['retorno'] * c['probabilidade'] for c in top_combinacoes) / len(top_combinacoes),
            'investimento_total_sugerido': sum(c['valor_otimizado'] for c in top_combinacoes)
        }