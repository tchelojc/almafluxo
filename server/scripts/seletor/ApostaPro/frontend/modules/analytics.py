# modules/analytics.py
from dataclasses import dataclass
from enum import Enum
from typing import Dict, Tuple
import math
from frontend.config import (
    PrevisaoPartida,
    TipoAposta,
    CenarioIntervalo,
    CENARIOS,
    MetricasIntervalo,
    ConstantesAposta
)

class StatusAposta(Enum):
    """Status das apostas realizadas no 1º tempo"""
    GANHA = "Ganhou"
    PERDIDA = "Perdeu"
    EM_ABERTO = "Em aberto"
    PARCIAL = "Retorno parcial"

class QuantumAnalyzer:
    """Analisador quântico independente"""
    def __init__(self, phi=6):
        self.phi = phi  # Fator quântico para futebol
    
    def calculate_flux(self, placar):
        """Calcula os parâmetros quânticos do fluxo"""
        try:
            casa, fora = map(int, placar.split('x'))
            return {
                'current': casa + fora,
                'resonance': min(1.0, abs(casa - fora)),
                'base': 2.5  # Média de gols esperada
            }
        except:
            # Fallback seguro em caso de erro
            return {'current': 0, 'resonance': 1.0, 'base': 1.0}
    
    def fluid_percentage(self, V_a, V_r, V_b):
        """Calcula a porcentagem fluida quântica"""
        return ((V_a - V_r) / (V_b + 1e-6)) * 100 * self.phi

@dataclass
class ResultadoPrimeiroTempo:
    """Armazena os resultados do primeiro tempo"""
    placar: str
    capital_investido: float
    capital_ganho: float
    apostas_ganhas: Dict[TipoAposta, float]
    apostas_perdidas: Dict[TipoAposta, float]
    apostas_em_aberto: Dict[TipoAposta, float]
    risco_atual: float
    cenario: CenarioIntervalo = None
    observacoes: str = ""

    def to_dict(self):
        """Converte para dicionário"""
        return {
            'placar': self.placar,
            'cenario': CENARIOS[self.cenario] if self.cenario else "Não definido",
            'capital_investido': self.capital_investido,
            'capital_ganho': self.capital_ganho,
            'apostas_ganhas': self.apostas_ganhas,
            'apostas_perdidas': self.apostas_perdidas,
            'apostas_em_aberto': self.apostas_em_aberto,
            'risco_atual': self.risco_atual,
            'observacoes': self.observacoes
        }

class AnalisadorPrimeiroTempo:
    """Classe principal de análise com integração quântica"""
    
    def __init__(self, previsao: PrevisaoPartida, odds: Dict[TipoAposta, float], distribuicao: Dict[TipoAposta, float]):
        self.previsao = previsao
        self.odds = odds
        self.distribuicao = distribuicao
        self.metricas = MetricasIntervalo()
        self.constantes = ConstantesAposta()
        self.quantum = QuantumAnalyzer()  # Instância do analisador quântico
        
        if not hasattr(self, '_calcular_risco_atual'):
            self._calcular_risco_atual = self._default_risk_calculation

    def _default_risk_calculation(self, total_gols: int, ambas_marcaram: bool) -> float:
        """Cálculo padrão de risco se o método principal faltar"""
        return self.metricas.FATOR_SEGURANCA  # Valor padrão seguro

    def _get_quantum_flux(self, placar):
        """Obtém os parâmetros quânticos para um placar"""
        return self.quantum.calculate_flux(placar)

    def _calculate_resonance(self, gols_casa, gols_fora):
        """Calcula a ressonância quântica entre os times"""
        diff = abs(gols_casa - gols_fora)
        return 0.5 if diff == 0 else 1.0 / diff

    def analisar_placar(self, placar: str) -> ResultadoPrimeiroTempo:
        """Analisa o placar do primeiro tempo e calcula resultados"""
        gols_casa, gols_fora = map(int, placar.split('x'))
        total_gols = gols_casa + gols_fora
        ambas_marcaram = gols_casa > 0 and gols_fora > 0

        # Determina o cenário primeiro
        cenario = self.determinar_cenario_intervalo(placar)
    
        resultado = ResultadoPrimeiroTempo(
            placar=placar,
            capital_investido=sum(self.distribuicao.values()),
            capital_ganho=0,
            apostas_ganhas={},
            apostas_perdidas={},
            apostas_em_aberto={},
            risco_atual=self._calcular_risco_atual(total_gols, ambas_marcaram),
            cenario=cenario,
            observacoes=self._gerar_observacoes_1t(placar, cenario)
        )

        # Restante do método permanece igual...
        for aposta, valor in self.distribuicao.items():
            status, retorno = self._avaliar_aposta(aposta, placar, total_gols, ambas_marcaram)
        
            if status == StatusAposta.GANHA:
                resultado.apostas_ganhas[aposta] = retorno
                resultado.capital_ganho += retorno
            elif status == StatusAposta.PERDIDA:
                resultado.apostas_perdidas[aposta] = valor
            else:
                resultado.apostas_em_aberto[aposta] = valor

        return resultado
    
    def _gerar_observacoes_1t(self, placar: str, cenario: CenarioIntervalo) -> str:
        """Gera observações específicas para o 1º tempo"""
        gols_casa, gols_fora = map(int, placar.split('x'))
        total_gols = gols_casa + gols_fora
    
        if self.previsao == PrevisaoPartida.MUITOS_GOLS:
            if total_gols == 0:
                return "Nenhum gol no 1º tempo - Risco elevado"
            elif total_gols < 1.5:
                return "Menos gols que o esperado - Ajuste estratégico necessário"
            else:
                return "Desempenho conforme esperado"
        else:
            if total_gols > 1.5:
                return "Mais gols que o esperado - Risco elevado"
            elif total_gols > 0.5:
                return "Desempenho dentro do esperado"
            else:
                return "Jogo muito defensivo - Bom para estratégia"

    def _avaliar_aposta(self, aposta: TipoAposta, placar: str, total_gols: int, ambas_marcaram: bool) -> Tuple[StatusAposta, float]:
        """Avalia o status de uma aposta específica com a nova lógica agregatória"""
        gols_casa, gols_fora = map(int, placar.split('x'))
    
        # Nova lógica de avaliação progressiva
        condicoes = {
            TipoAposta.MENOS_25_GOLS: total_gols < 2.5,
            TipoAposta.MAIS_25_GOLS: total_gols > 2.5,
            TipoAposta.MENOS_15_GOLS: total_gols < 1.5,
            TipoAposta.MENOS_05_GOLS: total_gols < 0.5,
            TipoAposta.MAIS_15_PRIMEIRO_TEMPO: total_gols > 1.5,
            TipoAposta.MAIS_05_PRIMEIRO_TEMPO: total_gols > 0.5,
            TipoAposta.AMBAS_MARCAM_SIM: ambas_marcaram,
            TipoAposta.AMBAS_MARCAM_NAO: not ambas_marcaram,
            TipoAposta.VENCEDOR_FAVORITO: gols_casa > gols_fora,
            # Novas condições para apostas agregadas
            TipoAposta.MAIS_15_SEGUNDO_TEMPO: total_gols > 1.5,  # Será reavaliado no 2º tempo
            TipoAposta.NAO_SAIR_MAIS_GOLS: total_gols == 0,  # Será reavaliado
            TipoAposta.PROXIMO_GOL_AZARAO: gols_fora > gols_casa  # Nova lógica
        }

        if aposta in condicoes:
            if condicoes[aposta]:
                # Fator de progressão baseado no fluxo quântico
                flux = self._get_quantum_flux(placar)
                fator_progressao = 1 + (flux['resonance'] * 0.5)  # Aumenta até 50%
                return (StatusAposta.GANHA, self.distribuicao[aposta] * self.odds[aposta] * fator_progressao)
            else:
                return (StatusAposta.PERDIDA, 0)
    
        return (StatusAposta.EM_ABERTO, 0)
    
    def _calcular_progressao_ganhos(self, resultado: ResultadoPrimeiroTempo) -> Dict[TipoAposta, float]:
        """Calcula os multiplicadores progressivos para cada aposta"""
        flux = self._get_quantum_flux(resultado.placar)
        progressao = {}
    
        for aposta in resultado.apostas_em_aberto:
            if aposta == TipoAposta.MAIS_15_SEGUNDO_TEMPO:
                # Aumenta o potencial de ganho conforme a diferença de gols
                progressao[aposta] = 1 + (flux['resonance'] * 0.3)
            elif aposta == TipoAposta.AMBAS_MARCAM_SIM:
                # Progressão mais agressiva para jogos equilibrados
                progressao[aposta] = 1 + (0.5 - flux['resonance']) * 0.4
            else:
                progressao[aposta] = 1.0
    
        return progressao

    def _calcular_risco_atual(self, total_gols: int, ambas_marcaram: bool) -> float:
        """Calcula o risco atual baseado no placar do 1º tempo"""
        if self.previsao == PrevisaoPartida.MUITOS_GOLS:
            if total_gols == 0:
                return self.metricas.FATOR_RISCO * 2.0  # Risco alto - não saíram gols
            elif total_gols < 1.5:
                return self.metricas.FATOR_RISCO * 1.5
            else:
                return self.metricas.FATOR_SEGURANCA  # Tudo conforme esperado
        else:
            if total_gols > 1.5:
                return self.metricas.FATOR_RISCO * 1.8  # Risco alto - muitos gols
            elif total_gols > 0.5:
                return self.metricas.FATOR_RISCO * 1.2
            else:
                return self.metricas.FATOR_SEGURANCA  # Tudo conforme esperado

    def determinar_cenario_intervalo(self, placar: str) -> CenarioIntervalo:
        gols_casa, gols_fora = map(int, placar.split('x'))
        diferenca = gols_casa - gols_fora
    
        # Considerando que o time da casa é sempre o favorito
        if gols_casa == 0 and gols_fora == 0:
            return CenarioIntervalo.EMPATE_0X0
        elif gols_casa == 1 and gols_fora == 1:
            return CenarioIntervalo.EMPATE_1X1
        elif diferenca == 1:
            return CenarioIntervalo.FAVORITO_GANHANDO_1X0
        elif diferenca == -1:
            return CenarioIntervalo.FAVORITO_PERDENDO_0X1
        elif diferenca == 2:
            return CenarioIntervalo.FAVORITO_GANHANDO_2X0
        elif diferenca == -2:
            return CenarioIntervalo.FAVORITO_PERDENDO_0X2
        elif diferenca >= 3:
            return CenarioIntervalo.FAVORITO_GANHANDO_3X0
        elif diferenca <= -3:
            return CenarioIntervalo.FAVORITO_PERDENDO_0X3
        elif gols_casa == 2 and gols_fora == 1:
            return CenarioIntervalo.FAVORITO_GANHANDO_2X1
        elif gols_casa == 1 and gols_fora == 2:
            return CenarioIntervalo.FAVORITO_PERDENDO_1X2
        else:
            return CenarioIntervalo.EMPATE_1X1  # Default para casos não previstos

    # No módulo analytics.py, método calcular_distribuicao_intervalo
    def calcular_distribuicao_intervalo(self, resultado: ResultadoPrimeiroTempo) -> Dict[TipoAposta, float]:
        flux_data = self._get_quantum_flux(resultado.placar)
        phase = self.quantum.fluid_percentage(
            flux_data['current'],
            flux_data['resonance'],
            flux_data['base']
        )
        """Calcula a distribuição recomendada para apostas no intervalo"""
        cenario = self.determinar_cenario_intervalo(resultado.placar)
        capital_disponivel = resultado.capital_ganho + sum(resultado.apostas_em_aberto.values()) * self.constantes.FATOR_RETORNO

        estrategias = {
            # Estratégias para MUITOS_GOLS
            PrevisaoPartida.MUITOS_GOLS: {
                CenarioIntervalo.EMPATE_0X0: {
                    TipoAposta.MAIS_15_SEGUNDO_TEMPO: 0.6,
                    TipoAposta.PROXIMO_GOL_AZARAO: 0.4
                },
                CenarioIntervalo.EMPATE_1X1: {
                    TipoAposta.MAIS_15_SEGUNDO_TEMPO: 0.8,
                    TipoAposta.MAIS_05_SEGUNDO_TEMPO: 0.2
                },
                CenarioIntervalo.FAVORITO_GANHANDO_1X0: {
                    TipoAposta.MAIS_15_SEGUNDO_TEMPO: 0.7,
                    TipoAposta.PROXIMO_GOL_AZARAO: 0.3
                },
                CenarioIntervalo.FAVORITO_GANHANDO_2X0: {
                    TipoAposta.MAIS_15_SEGUNDO_TEMPO: 0.6,
                    TipoAposta.NAO_SAIR_MAIS_GOLS: 0.4
                },
                CenarioIntervalo.FAVORITO_GANHANDO_2X1: {
                    TipoAposta.MAIS_15_SEGUNDO_TEMPO: 0.6,
                    TipoAposta.PROXIMO_GOL_AZARAO: 0.4
                },
                CenarioIntervalo.FAVORITO_PERDENDO_0X1: {
                    TipoAposta.MAIS_15_SEGUNDO_TEMPO: 0.8,
                    TipoAposta.PROXIMO_GOL_AZARAO: 0.2
                },
                CenarioIntervalo.FAVORITO_PERDENDO_0X2: {
                    TipoAposta.MAIS_15_SEGUNDO_TEMPO: 0.8,
                    TipoAposta.PROXIMO_GOL_AZARAO: 0.2
                },
                CenarioIntervalo.FAVORITO_PERDENDO_1X2: {
                    TipoAposta.MAIS_15_SEGUNDO_TEMPO: 0.7,
                    TipoAposta.PROXIMO_GOL_AZARAO: 0.3
                }
            },
            # Estratégias para POUCOS_GOLS
            PrevisaoPartida.POUCOS_GOLS: {
                CenarioIntervalo.EMPATE_0X0: {
                    TipoAposta.NAO_SAIR_MAIS_GOLS: 0.3,
                    TipoAposta.MAIS_15_SEGUNDO_TEMPO: 0.4,
                    TipoAposta.PROXIMO_GOL_AZARAO: 0.3
                },
                CenarioIntervalo.EMPATE_1X1: {
                    TipoAposta.NAO_SAIR_MAIS_GOLS: 0.7,
                    TipoAposta.PROXIMO_GOL_AZARAO: 0.3
                },
                CenarioIntervalo.FAVORITO_GANHANDO_1X0: {
                    TipoAposta.NAO_SAIR_MAIS_GOLS: 0.4,
                    TipoAposta.MAIS_15_SEGUNDO_TEMPO: 0.3,
                    TipoAposta.PROXIMO_GOL_AZARAO: 0.3
                },
                CenarioIntervalo.FAVORITO_GANHANDO_2X0: {
                    TipoAposta.NAO_SAIR_MAIS_GOLS: 0.3,
                    TipoAposta.MAIS_05_SEGUNDO_TEMPO: 0.7
                },
                CenarioIntervalo.FAVORITO_GANHANDO_2X1: {
                    TipoAposta.NAO_SAIR_MAIS_GOLS: 0.3,
                    TipoAposta.MAIS_15_SEGUNDO_TEMPO: 0.7
                },
                CenarioIntervalo.FAVORITO_PERDENDO_0X1: {
                    TipoAposta.NAO_SAIR_MAIS_GOLS: 0.4,
                    TipoAposta.MAIS_15_SEGUNDO_TEMPO: 0.3,
                    TipoAposta.PROXIMO_GOL_AZARAO: 0.3
                },
                CenarioIntervalo.FAVORITO_PERDENDO_0X2: {
                    TipoAposta.NAO_SAIR_MAIS_GOLS: 0.3,
                    TipoAposta.MAIS_15_SEGUNDO_TEMPO: 0.7
                },
                CenarioIntervalo.FAVORITO_PERDENDO_1X2: {
                    TipoAposta.NAO_SAIR_MAIS_GOLS: 0.3,
                    TipoAposta.MAIS_15_SEGUNDO_TEMPO: 0.7
                }
            }
        }

        distribuicao = {}
        estrategia = estrategias[self.previsao].get(cenario, {})
    
        for aposta, proporcao in estrategia.items():
            if aposta in self.odds:
                # Ajuste baseado na odd (quanto maior a odd, menor o investimento)
                fator_ajuste = 1 / math.log(self.odds[aposta] + 1)
                distribuicao[aposta] = capital_disponivel * proporcao * fator_ajuste * self.metricas.FATOR_SEGURANCA

        # Normalização para garantir que a soma seja igual ao capital disponível
        total = sum(distribuicao.values())
        if total > 0:
            fator_normalizacao = capital_disponivel / total
            distribuicao = {k: round(v * fator_normalizacao, 2) for k, v in distribuicao.items()}

        return {k: v for k, v in distribuicao.items() if v >= 1.0}  # Filtra valores muito pequenos
        
    def _distribuicao_fallback(self, resultado):
        """Distribuição padrão caso o cálculo quântico falhe"""
        cenario = self.determinar_cenario_intervalo(resultado.placar)
        capital = resultado.capital_ganho + sum(resultado.apostas_em_aberto.values())
        
        # Distribuição básica sem ajustes quânticos
        distribuicao = {
            TipoAposta.MAIS_15_SEGUNDO_TEMPO: capital * 0.7,
            TipoAposta.NAO_SAIR_MAIS_GOLS: capital * 0.3
        }
        
        return {k: v for k, v in distribuicao.items() if v >= 1.0}
    
    def gerar_relatorio(self, resultado: ResultadoPrimeiroTempo) -> Dict:
        """Gera um relatório completo da análise"""
        cenario = self.determinar_cenario_intervalo(resultado.placar)
        distribuicao_intervalo = self.calcular_distribuicao_intervalo(resultado)

        return {
            "placar": resultado.placar,
            "cenario": CENARIOS[cenario],
            "capital_investido": round(resultado.capital_investido, 2),
            "retorno_1t": round(resultado.capital_ganho, 2),
            "capital_disponivel": round(resultado.capital_ganho + sum(resultado.apostas_em_aberto.values()), 2),
            "risco_atual": round(resultado.risco_atual, 2),
            "apostas_ganhas": {k.name: round(v, 2) for k, v in resultado.apostas_ganhas.items()},
            "apostas_perdidas": {k.name: round(self.distribuicao[k], 2) for k in resultado.apostas_perdidas},
            "apostas_em_aberto": {k.name: round(v, 2) for k, v in resultado.apostas_em_aberto.items()},
            "recomendacao_intervalo": {k.name: v for k, v in distribuicao_intervalo.items()},
            "observacoes": self._gerar_observacoes(resultado, cenario)
        }

    def _gerar_observacoes(self, resultado: ResultadoPrimeiroTempo, cenario: CenarioIntervalo) -> str:
        """Gera observações estratégicas baseadas no cenário"""
        gols_casa, gols_fora = map(int, resultado.placar.split('x'))
        total_gols = gols_casa + gols_fora

        if self.previsao == PrevisaoPartida.MUITOS_GOLS:
            if total_gols == 0:
                return ("⚠️ Alerta: Nenhum gol no 1º tempo. "
                       "Considere proteger com 'Não sair mais gols' e "
                       "'Próximo gol azarão' para equilibrar risco.")
            elif total_gols < 1.5:
                return ("🔍 Situação: Menos gols que o esperado. "
                       "Mantenha estratégia agressiva no 2º tempo com 'Mais 1.5 gols'.")
            else:
                return ("✅ Situação conforme esperado. "
                       "Continue com estratégia ofensiva no 2º tempo.")
        else:
            if total_gols > 1.5:
                return ("⚠️ Alerta: Mais gols que o esperado. "
                       "Proteja com 'Não sair mais gols' e considere "
                       "reduzir exposição em apostas defensivas.")
            elif total_gols > 0.5:
                return ("🔍 Situação: Alguns gols no 1º tempo. "
                       "Mantenha proteções e apostas conservadoras.")
            else:
                return ("✅ Situação conforme esperado. "
                       "Continue com estratégia defensiva no 2º tempo.")