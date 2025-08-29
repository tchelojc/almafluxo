# modules/distribuidor.py
from typing import Dict
from config import TipoAposta, PrevisaoPartida, CenarioIntervalo
from modules.analytics import ResultadoPrimeiroTempo

class DistribuidorCapital:
    def __init__(self, capital_total: float, estrategia: PrevisaoPartida):
        self.capital_total = capital_total
        self.estrategia = estrategia
        self.capital_gasto = 0.0
        self.capital_restante = capital_total
        
    def distribuir_pre_partida(self, odds: Dict[TipoAposta, float]) -> Dict[TipoAposta, float]:
        """Distribui 80% do capital na pré-partida (60% principais + 20% proteções)"""
        teto_principal = self.capital_total * 0.6  # 60% para apostas principais
        teto_protecao = self.capital_total * 0.2  # 20% para proteções
        distribuicao = {}
    
        if self.estrategia == PrevisaoPartida.POUCOS_GOLS:
            # Apostas principais (60%)
            distribuicao.update({
                TipoAposta.MENOS_25_GOLS: teto_principal * 0.7,  # 42% do total
                TipoAposta.AMBAS_MARCAM_NAO: teto_principal * 0.3  # 18% do total
            })
        
            # Proteções (20%)
            distribuicao.update({
                TipoAposta.MAIS_25_GOLS: teto_protecao * 0.6,  # 12% do total
                TipoAposta.MENOS_05_GOLS: teto_protecao * 0.4  # 8% do total
            })
        else:
            # Estratégia para MUITOS_GOLS
            # Apostas principais (60%)
            distribuicao.update({
                TipoAposta.MAIS_25_GOLS: teto_principal * 0.7,  # 42% do total
                TipoAposta.AMBAS_MARCAM_SIM: teto_principal * 0.3  # 18% do total
            })
        
            # Proteções (20%)
            distribuicao.update({
                TipoAposta.MENOS_25_GOLS: teto_protecao * 0.6,  # 12% do total
                TipoAposta.MAIS_15_PRIMEIRO_TEMPO: teto_protecao * 0.4  # 8% do total
            })
    
        self.capital_gasto = sum(distribuicao.values())
        self.capital_restante = self.capital_total - self.capital_gasto
    
        # Validação de segurança
        assert abs(self.capital_gasto - self.capital_total * 0.8) < 0.01, "Distribuição deve ser exatamente 80%"
    
        return distribuicao
    
    def distribuir_intervalo(self, placar: str, odds: Dict[TipoAposta, float], 
                           resultado_1t: ResultadoPrimeiroTempo) -> Dict[TipoAposta, float]:
        """Distribui até 40% do capital no intervalo"""
        teto = self.capital_total * 0.4
        cenario = self.determinar_cenario(placar)
        lucro_alvo = self.capital_total * 0.1
        
        if self.estrategia == PrevisaoPartida.POUCOS_GOLS:
            return self._distribuir_poucos_gols(cenario, odds, teto, lucro_alvo)
        else:
            return self._distribuir_muitos_gols(cenario, odds, teto, lucro_alvo)
    
    def _distribuir_poucos_gols(self, cenario: CenarioIntervalo, 
                              odds: Dict[TipoAposta, float], 
                              teto: float, lucro_alvo: float) -> Dict[TipoAposta, float]:
        distribuicao = {}
        
        if cenario in [CenarioIntervalo.EMPATE_0X0, CenarioIntervalo.EMPATE_1X1]:
            # Proteção máxima para manter o empate
            distribuicao[TipoAposta.NAO_SAIR_MAIS_GOLS] = min(teto * 0.7, self.capital_restante)
            distribuicao[TipoAposta.PROXIMO_GOL_AZARAO] = min(teto * 0.3, self.capital_restante - sum(distribuicao.values()))
        
        elif cenario in [CenarioIntervalo.FAVORITO_GANHANDO_1X0, CenarioIntervalo.FAVORITO_GANHANDO_2X0]:
            # Proteção contra empate
            distribuicao[TipoAposta.NAO_SAIR_MAIS_GOLS] = min(teto * 0.8, self.capital_restante)
            distribuicao[TipoAposta.MAIS_05_SEGUNDO_TEMPO] = min(teto * 0.2, self.capital_restante - sum(distribuicao.values()))
        
        elif cenario in [CenarioIntervalo.FAVORITO_PERDENDO_0X1, CenarioIntervalo.FAVORITO_PERDENDO_0X2]:
            # Busca de equilíbrio
            distribuicao[TipoAposta.PROXIMO_GOL_AZARAO] = min(teto * 0.6, self.capital_restante)
            distribuicao[TipoAposta.MAIS_15_SEGUNDO_TEMPO] = min(teto * 0.4, self.capital_restante - sum(distribuicao.values()))
        
        # Ajusta para não ultrapassar o capital restante
        total = sum(distribuicao.values())
        if total > self.capital_restante:
            fator = self.capital_restante / total
            distribuicao = {k: v * fator for k, v in distribuicao.items()}
        
        self.capital_gasto += sum(distribuicao.values())
        self.capital_restante = self.capital_total - self.capital_gasto
        return distribuicao
    
    def _distribuir_muitos_gols(self, cenario: CenarioIntervalo, 
                              odds: Dict[TipoAposta, float], 
                              teto: float, lucro_alvo: float) -> Dict[TipoAposta, float]:
        """Distribuição para estratégia de Muitos Gols (+2.5)"""
        distribuicao = {}
    
        if cenario in [CenarioIntervalo.EMPATE_0X0, CenarioIntervalo.EMPATE_1X1]:
            # Pressão ofensiva para sair do empate
            distribuicao[TipoAposta.MAIS_15_SEGUNDO_TEMPO] = min(teto * 0.7, self.capital_restante)
            distribuicao[TipoAposta.PROXIMO_GOL_AZARAO] = min(teto * 0.3, self.capital_restante - sum(distribuicao.values()))
    
        elif cenario in [CenarioIntervalo.FAVORITO_GANHANDO_1X0, CenarioIntervalo.FAVORITO_GANHANDO_2X0]:
            # Continuar pressionando para aumentar vantagem
            distribuicao[TipoAposta.MAIS_15_SEGUNDO_TEMPO] = min(teto * 0.6, self.capital_restante)
            distribuicao[TipoAposta.MAIS_05_SEGUNDO_TEMPO] = min(teto * 0.4, self.capital_restante - sum(distribuicao.values()))
    
        elif cenario in [CenarioIntervalo.FAVORITO_PERDENDO_0X1, CenarioIntervalo.FAVORITO_PERDENDO_0X2]:
            # Reação ofensiva para virar o jogo
            distribuicao[TipoAposta.MAIS_15_SEGUNDO_TEMPO] = min(teto * 0.8, self.capital_restante)
            distribuicao[TipoAposta.PROXIMO_GOL_AZARAO] = min(teto * 0.2, self.capital_restante - sum(distribuicao.values()))
    
        elif cenario in [CenarioIntervalo.FAVORITO_GANHANDO_2X1, CenarioIntervalo.FAVORITO_GANHANDO_3X0]:
            # Manter pressão em jogos movimentados
            distribuicao[TipoAposta.MAIS_15_SEGUNDO_TEMPO] = min(teto * 0.5, self.capital_restante)
            distribuicao[TipoAposta.MAIS_05_SEGUNDO_TEMPO] = min(teto * 0.5, self.capital_restante - sum(distribuicao.values()))
    
        # Ajuste final para não ultrapassar o capital
        total = sum(distribuicao.values())
        if total > self.capital_restante:
            fator = self.capital_restante / total
            distribuicao = {k: round(v * fator, 2) for k, v in distribuicao.items()}
    
        self.capital_gasto += sum(distribuicao.values())
        self.capital_restante = self.capital_total - self.capital_gasto
        return {k: v for k, v in distribuicao.items() if v >= 1.0}  # Filtra valores muito pequenos
    
    def determinar_cenario(self, placar: str) -> CenarioIntervalo:
        """Determina o cenário baseado no placar atual"""
        try:
            gols_casa, gols_fora = map(int, placar.split('x'))
            diferenca = gols_casa - gols_fora
        
            # Considerando que o time da casa é o favorito
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
                return CenarioIntervalo.EMPATE_1X1  # Cenário padrão para casos não mapeados
        except:
            return CenarioIntervalo.EMPATE_1X1  # Fallback em caso de erro
    
    def _validar_odds(self, odds: Dict[TipoAposta, float]) -> bool:
        """Valida se as odds são suficientes para a estratégia"""
        if self.estrategia == PrevisaoPartida.POUCOS_GOLS:
            return odds.get(TipoAposta.NAO_SAIR_MAIS_GOLS, 0) > 2.0
        else:
            return odds.get(TipoAposta.MAIS_15_SEGUNDO_TEMPO, 0) > 1.8
        
    def ajustar_distribuicao_por_odds(self, distribuicao: Dict[TipoAposta, float], 
                                     odds: Dict[TipoAposta, float]) -> Dict[TipoAposta, float]:
        """Ajusta a distribuição baseado nas odds disponíveis"""
        for aposta in list(distribuicao.keys()):
            if aposta in odds:
                # Reduz investimento em odds baixas
                if odds[aposta] < 2.0:
                    distribuicao[aposta] *= 0.7
                # Aumenta em odds altas
                elif odds[aposta] > 3.5:
                    distribuicao[aposta] *= 1.3
    
        # Rebalanceamento
        total = sum(distribuicao.values())
        if total > 0:
            fator = self.capital_restante / total
            return {k: round(v * fator, 2) for k, v in distribuicao.items()}
        return distribuicao
    
    def calcular_retorno_minimo(self, distribuicao: Dict[TipoAposta, float], odds: Dict[TipoAposta, float]) -> float:
        """Calcula o retorno mínimo garantido com hedge"""
        retorno_minimo = 0
        for aposta, valor in distribuicao.items():
            if aposta in odds:
                retorno_minimo += valor * 0.5  # Assume-se que pelo menos 50% do valor será recuperado

        return min(retorno_minimo, self.capital_total * 0.8)  # Limita a 80% para ser conservador