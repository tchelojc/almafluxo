# modules/intervalo.py
import math 
import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st
from typing import Dict
from dataclasses import dataclass
from frontend.modules.quantum import QuantumProcessor
from frontend.config import (
    CenarioIntervalo,
    CENARIOS,
    TipoAposta,
    PrevisaoPartida,
    MetricasIntervalo
)

@dataclass
class ResultadoIntervalo:
    """Armazena os resultados e decisões do intervalo"""
    placar_1t: str
    cenario: CenarioIntervalo
    capital_disponivel: float
    apostas_ativas: Dict[TipoAposta, float]
    odds_2t: Dict[TipoAposta, float]
    distribuicao_2t: Dict[TipoAposta, float]
    risco_atual: float

class GerenciadorIntervalo:
    """Classe para gerenciar as apostas durante o intervalo da partida"""
    
    def __init__(self, previsao: PrevisaoPartida, capital_total: float):
        self.previsao = previsao
        self.capital_total = capital_total
        self.metricas = MetricasIntervalo()
        self.quantum = QuantumProcessor()  # Adiciona o processador quântico
        self._inicializar_estado()

    def _get_quantum_flux(self, placar: str) -> Dict[str, float]:
        """Obtém os parâmetros quânticos para cálculo"""
        return self.quantum.get_quantum_flux(placar)

    def _inicializar_estado(self):
        """Inicializa o estado da sessão para o intervalo"""
        if 'resultado_1t' not in st.session_state:
            st.session_state.resultado_1t = None
        if 'cenario' not in st.session_state:
            st.session_state.cenario = None
        if 'odds_2t' not in st.session_state:
            st.session_state.odds_2t = {}
        if 'distribuicao_2t' not in st.session_state:
            st.session_state.distribuicao_2t = {}
            
    def _armazenar_distribuicao(self, distribuicao, odds_2t):
        """Armazena a distribuição na session_state"""
        st.session_state.distribuicao_intervalo = distribuicao
        st.session_state.odds_2t = odds_2t
        st.session_state.analise_intervalo = True

    def mostrar_interface(self) -> ResultadoIntervalo:
        """Mostra a interface completa para o intervalo"""
        st.title("⏱ Gerenciamento do Intervalo")

        # Verificação de dados necessários
        if not all(k in st.session_state for k in ['placar_1t', 'cenario', 'capital_disponivel']):
            st.error("Dados incompletos! Volte para o 1º tempo.")
            return None

        # Mostra resumo do 1º tempo
        st.subheader("📋 Resumo do 1º Tempo")
        cols = st.columns(3)
        cols[0].metric("Placar", st.session_state.placar_1t)
        cols[1].metric("Cenário", CENARIOS[st.session_state.cenario])
        cols[2].metric("Capital Disponível", f"R$ {st.session_state.capital_disponivel:.2f}")

        # Mostra configuração do 2º tempo
        return self._mostrar_configuracao_2t()

    def _mostrar_registro_1t(self):
        """Interface para registro do resultado do 1º tempo"""
        st.subheader("📋 Resultado do 1º Tempo")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Seleção do placar com cenários pré-definidos
            placar = st.selectbox(
                "Placar do 1º Tempo",
                options=list(CENARIOS.keys()),
                format_func=lambda x: f"{x} - {CENARIOS[x]}",
                key="select_placar_1t"
            )
            
            # Botão para confirmar o placar
            if st.button("Confirmar Placar", type="primary"):
                st.session_state.resultado_1t = placar
                st.session_state.cenario = self._determinar_cenario(placar)
                st.rerun()
        
        with col2:
            if placar:
                self._mostrar_analise_placar(placar)

    def _mostrar_analise_placar(self, placar):
        """Mostra análise visual do placar"""
        if isinstance(placar, str) and 'x' in placar:
            try:
                gols_casa, gols_fora = map(int, placar.strip().split('x'))
            except ValueError:
                st.error("❌ Erro ao interpretar o placar. Formato esperado: '1x0'")
                return
        else:
            st.error("❌ Placar inválido. Esperado string no formato '1x0'.")
            return

        total_gols = gols_casa + gols_fora
    
        st.metric("Total de Gols 1ºT", total_gols)
        st.metric("Saldo", abs(gols_casa - gols_fora))
    
        # Análise visual baseada no cenário
        if total_gols == 0:
            st.warning("🔵 Jogo sem gols - Estratégia defensiva recomendada")
        elif total_gols >= 2:
            st.success("🟢 Jogo movimentado - Oportunidades de ataque")
        else:
            st.info("🟡 Jogo equilibrado - Estratégia balanceada")
            
    def _mostrar_configuracao_2t(self) -> ResultadoIntervalo:
        """Interface de configuração do 2º tempo com todas apostas ativadas"""
        if 'cenario' not in st.session_state:
            st.error("Cenário não definido!")
            return None

        cenario = st.session_state.cenario
        cenario_nome = CENARIOS.get(cenario, "Cenário Desconhecido")

        st.subheader(f"📊 Configuração do 2º Tempo - {cenario_nome}")
        st.write(f"💵 Capital disponível: R$ {st.session_state.capital_disponivel:.2f}")

        # Configuração de odds com todas apostas ativadas corretamente
        odds_2t = {}
        cols = st.columns(2)

        with cols[0]:
            # Campo fixo para todos os cenários
            odds_2t[TipoAposta.MAIS_15_SEGUNDO_TEMPO] = st.number_input(
                "➕ Mais 1.5 gols 2º tempo",
                min_value=1.01, value=1.8, step=0.1)

            # Mostrar "Não sair mais gols" para todos os cenários
            odds_2t[TipoAposta.NAO_SAIR_MAIS_GOLS] = st.number_input(
                "🚫 Não sair mais gols",
                min_value=1.01, value=4.0, step=0.1)

            # Mostrar "Próximo gol azarão" para cenários com gols em ambos lados
            if cenario in [CenarioIntervalo.EMPATE_0X0, CenarioIntervalo.EMPATE_1X1,
                          CenarioIntervalo.FAVORITO_GANHANDO_2X1, CenarioIntervalo.FAVORITO_PERDENDO_1X2]:
                odds_2t[TipoAposta.PROXIMO_GOL_AZARAO] = st.number_input(
                    "🎯 Próximo gol azarão",
                    min_value=1.01, value=3.5, step=0.1)

        with cols[1]:
            # Mostrar "Ambas Marcam" para cenários relevantes
            if cenario in [CenarioIntervalo.FAVORITO_GANHANDO_1X0, CenarioIntervalo.FAVORITO_GANHANDO_2X0,
                          CenarioIntervalo.FAVORITO_PERDENDO_0X1, CenarioIntervalo.FAVORITO_PERDENDO_0X2,
                          CenarioIntervalo.EMPATE_0X0, CenarioIntervalo.EMPATE_1X1,
                          CenarioIntervalo.FAVORITO_GANHANDO_2X1, CenarioIntervalo.FAVORITO_PERDENDO_1X2]:
                odds_2t[TipoAposta.AMBAS_MARCAM_SIM] = st.number_input(
                    "✅ Ambas Marcam - Sim",
                    min_value=1.01, value=2.5, step=0.1)
    
                odds_2t[TipoAposta.AMBAS_MARCAM_NAO] = st.number_input(
                    "🔴 Ambas Marcam - Não",
                    min_value=1.01, value=3.5, step=0.1)

        # Botão de cálculo com análise quântica
        if st.button("🔮 Calcular Distribuição Quântica", type="primary", key="btn_calcular_distribuicao"):
            with st.spinner("Analisando probabilidades quânticas..."):
                distribuicao = self._calcular_distribuicao_2t(
                    cenario,
                    st.session_state.capital_disponivel,
                    odds_2t
                )
    
                if distribuicao:
                    st.session_state.distribuicao_intervalo = distribuicao
                    st.session_state.odds_2t = odds_2t
                    st.rerun()
                else:
                    st.error("O sistema quântico não conseguiu calcular uma distribuição ideal")

        # Mostrar resultados da análise quântica
        if 'distribuicao_intervalo' in st.session_state:
            self._mostrar_resultados_analise()
    
            if st.button("✅ Confirmar Distribuição Quântica", type="primary", key="btn_confirmar_distribuicao"):
                return self._gerar_resultado_intervalo()

        return None

    def _configurar_odds_2t(self, cenario):
        """Configura as odds do 2º tempo baseado no cenário"""
        odds_2t = {}
        cols = st.columns(2)
    
        with cols[0]:
            # Apostas sempre disponíveis
            odds_2t[TipoAposta.MAIS_15_SEGUNDO_TEMPO] = st.number_input(
                "➕ Mais 1.5 gols 2º tempo",
                min_value=1.01, value=1.8, step=0.1, key="odd_mais_15_2t")
        
            odds_2t[TipoAposta.NAO_SAIR_MAIS_GOLS] = st.number_input(
                "🚫 Não sair mais gols",
                min_value=1.01, value=4.0, step=0.1, key="odd_nao_sair_gols")
        
            # Apostas condicionais
            if cenario in [CenarioIntervalo.EMPATE_0X0, CenarioIntervalo.FAVORITO_GANHANDO_1X0,
                          CenarioIntervalo.FAVORITO_GANHANDO_2X0, CenarioIntervalo.FAVORITO_PERDENDO_0X1,
                          CenarioIntervalo.FAVORITO_PERDENDO_0X2]:
                odds_2t[TipoAposta.AMBAS_MARCAM_NAO] = st.number_input(
                    "🔴 Ambas Marcam - Não",
                    min_value=1.01, value=3.5, step=0.1, key="odd_ambas_nao")
    
        with cols[1]:
            odds_2t[TipoAposta.PROXIMO_GOL_AZARAO] = st.number_input(
                "🎯 Próximo gol azarão",
                min_value=1.01, value=3.5, step=0.1, key="odd_proximo_azarao")
        
            if cenario in [CenarioIntervalo.EMPATE_0X0, CenarioIntervalo.EMPATE_1X1,
                          CenarioIntervalo.FAVORITO_GANHANDO_2X1, CenarioIntervalo.FAVORITO_PERDENDO_1X2]:
                odds_2t[TipoAposta.AMBAS_MARCAM_SIM] = st.number_input(
                    "🟢 Ambas Marcam - Sim",
                    min_value=1.01, value=2.5, step=0.1, key="odd_ambas_sim")
    
        return odds_2t

    def _mostrar_resultados_analise(self):
        """Exibe os resultados da análise de forma elegante"""
        st.subheader("📊 Distribuição Quântica Recomendada")
    
        # Tabela interativa
        df = pd.DataFrame({
            "Aposta": [aposta.value for aposta in st.session_state.distribuicao_intervalo.keys()],
            "Valor (R$)": st.session_state.distribuicao_intervalo.values(),
            "Odd": [st.session_state.odds_2t.get(aposta, 1.0) for aposta in st.session_state.distribuicao_intervalo.keys()],
            "% Capital": [(val/st.session_state.capital_disponivel)*100 for val in st.session_state.distribuicao_intervalo.values()]
        })
    
        st.dataframe(
            df.style.format({
                "Valor (R$)": "{:.2f}",
                "Odd": "{:.2f}",
                "% Capital": "{:.1f}%"
            }).apply(self._colorizar_linhas, axis=1),
            hide_index=True
        )
    
        # Visualização quântica
        with st.expander("🌌 Visualização Quântica Avançada"):
            self._mostrar_grafico_quantico(df)

    def _colorizar_linhas(self, row):
        """Coloriza as linhas baseado no tipo de aposta"""
        colors = {
            "MAIS_15_SEGUNDO_TEMPO": "background-color: #ffeda0",
            "NAO_SAIR_MAIS_GOLS": "background-color: #fde0dd",
            "AMBAS_MARCAM_NAO": "background-color: #e0f3db",
            "AMBAS_MARCAM_SIM": "background-color: #fee0d2",
            "PROXIMO_GOL_AZARAO": "background-color: #d0d1e6"
        }
    
        aposta = row["Aposta"]
        for key in colors:
            if key in aposta:
                return [colors[key]] * len(row)
        return [""] * len(row)

    def _mostrar_grafico_quantico(self, df):
        """Mostra visualização quântica da distribuição"""
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 6))
    
        # Gráfico de pizza
        ax1.pie(
            df["Valor (R$)"],
            labels=df["Aposta"],
            autopct='%1.1f%%',
            startangle=90,
            colors=['#ffeda0','#fde0dd','#e0f3db','#fee0d2','#d0d1e6']
        )
        ax1.set_title("Distribuição Quântica")
        ax1.axis('equal')
    
        # Gráfico de barras
        ax2.barh(df["Aposta"], df["Valor (R$)"], color='#2b8cbe')
        ax2.set_title("Alocação de Capital")
        ax2.set_xlabel("Valor (R$)")
    
        st.pyplot(fig)

    def _gerar_resultado_intervalo(self):
        """Gera o objeto ResultadoIntervalo com dados quânticos"""
        return ResultadoIntervalo(
            placar_1t=st.session_state.placar_1t,
            cenario=st.session_state.cenario,
            capital_disponivel=st.session_state.capital_disponivel,
            apostas_ativas={},
            odds_2t=st.session_state.odds_2t,
            distribuicao_2t=st.session_state.distribuicao_intervalo,
            risco_atual=self._calcular_risco_quantico()
        )

    def _calcular_risco_quantico(self):
        """Calcula o risco com ajustes quânticos"""
        placar = st.session_state.placar_1t
        gols_casa, gols_fora = map(int, placar.split('x'))
        total_gols = gols_casa + gols_fora
    
        # Fator quântico baseado no placar
        quantum_factor = 1 + (total_gols / 10) - (abs(gols_casa - gols_fora) / 5)
    
        # Risco base ajustado pelo fator quântico
        risco_base = self.metricas.FATOR_RISCO * quantum_factor
    
        return min(max(risco_base, 0.5), 1.5)  # Limites entre 0.5 e 1.5

    def _mostrar_interface_ajuste(self, distribuicao: Dict[TipoAposta, float], capital_max: float):
        """Mostra interface para ajuste manual das apostas"""
        st.subheader("💰 Distribuição de Capital")
        
        cols = st.columns(2)
        total_distribuido = 0
        
        with cols[0]:
            st.markdown("**📈 Apostas Principais**")
            for aposta, valor in distribuicao.items():
                if aposta in [TipoAposta.MAIS_15_SEGUNDO_TEMPO, TipoAposta.PROXIMO_GOL_AZARAO]:
                    novo_valor = st.number_input(
                        f"{aposta.value} (Odd: {st.session_state.odds_2t[aposta]:.2f})",
                        min_value=0.0,
                        max_value=capital_max,
                        value=valor,
                        step=10.0,
                        key=f"dist_{aposta.name}"
                    )
                    distribuicao[aposta] = novo_valor
                    total_distribuido += novo_valor
        
        with cols[1]:
            st.markdown("**🛡️ Apostas de Proteção**")
            for aposta, valor in distribuicao.items():
                if aposta in [TipoAposta.NAO_SAIR_MAIS_GOLS]:
                    novo_valor = st.number_input(
                        f"{aposta.value} (Odd: {st.session_state.odds_2t[aposta]:.2f})",
                        min_value=0.0,
                        max_value=capital_max,
                        value=valor,
                        step=10.0,
                        key=f"dist_{aposta.name}"
                    )
                    distribuicao[aposta] = novo_valor
                    total_distribuido += novo_valor
        
        # Mostra resumo
        st.progress(min(total_distribuido / capital_max, 1.0))
        st.metric("Total Distribuído", f"R$ {total_distribuido:.2f}")
        st.metric("Saldo Disponível", f"R$ {capital_max - total_distribuido:.2f}")

    def _determinar_cenario(self, placar: str) -> CenarioIntervalo:
        """Determina o cenário com precisão absoluta"""
        gols_casa, gols_fora = map(int, placar.split('x'))
    
        # Mapeamento exato dos cenários
        if gols_casa == 0 and gols_fora == 0:
            return CenarioIntervalo.EMPATE_0X0
        elif gols_casa == 1 and gols_fora == 1:
            return CenarioIntervalo.EMPATE_1X1
        elif gols_casa == 1 and gols_fora == 0:
            return CenarioIntervalo.FAVORITO_GANHANDO_1X0
        elif gols_casa == 0 and gols_fora == 1:
            return CenarioIntervalo.FAVORITO_PERDENDO_0X1
        elif gols_casa == 2 and gols_fora == 0:
            return CenarioIntervalo.FAVORITO_GANHANDO_2X0
        elif gols_casa == 2 and gols_fora == 1:
            return CenarioIntervalo.FAVORITO_GANHANDO_2X1
        elif gols_casa == 0 and gols_fora == 2:
            return CenarioIntervalo.FAVORITO_PERDENDO_0X2
        elif gols_casa == 1 and gols_fora == 2:
            return CenarioIntervalo.FAVORITO_PERDENDO_1X2
        else:
            return CenarioIntervalo.EMPATE_1X1  # Default para cenários não mapeados
        
    def _calcular_odds_recomendadas(self, cenario: CenarioIntervalo, total_gols: int) -> Dict[TipoAposta, float]:
        """Calcula as odds recomendadas baseadas no cenário"""
        if self.previsao == PrevisaoPartida.MUITOS_GOLS:
            # Odds mais baixas para cenários com muitos gols esperados
            if total_gols == 0:
                return {
                    TipoAposta.MAIS_15_SEGUNDO_TEMPO: 1.4,  # Mais agressivo
                    TipoAposta.PROXIMO_GOL_AZARAO: 2.5,
                    TipoAposta.NAO_SAIR_MAIS_GOLS: 3.5
                }
            elif total_gols < 1.5:
                return {
                    TipoAposta.MAIS_15_SEGUNDO_TEMPO: 1.5,
                    TipoAposta.PROXIMO_GOL_AZARAO: 2.3,
                    TipoAposta.NAO_SAIR_MAIS_GOLS: 3.0
                }
            else:
                return {
                    TipoAposta.MAIS_15_SEGUNDO_TEMPO: 1.3,  # Muito provável
                    TipoAposta.PROXIMO_GOL_AZARAO: 2.0,
                    TipoAposta.NAO_SAIR_MAIS_GOLS: 2.5
                }
        else:
            # Mantém as odds originais para poucos gols
            if total_gols > 1.5:
                return {
                    TipoAposta.MAIS_15_SEGUNDO_TEMPO: 1.7,
                    TipoAposta.PROXIMO_GOL_AZARAO: 2.6,
                    TipoAposta.NAO_SAIR_MAIS_GOLS: 2.8
                }
            elif total_gols > 0.5:
                return {
                    TipoAposta.MAIS_15_SEGUNDO_TEMPO: 1.9,
                    TipoAposta.PROXIMO_GOL_AZARAO: 3.2,
                    TipoAposta.NAO_SAIR_MAIS_GOLS: 3.0
                }
            else:
                return {
                    TipoAposta.MAIS_15_SEGUNDO_TEMPO: 2.1,
                    TipoAposta.PROXIMO_GOL_AZARAO: 3.5,
                    TipoAposta.NAO_SAIR_MAIS_GOLS: 3.8
                }

    def _calcular_distribuicao_2t(self, cenario: CenarioIntervalo, capital: float, 
                                 odds: Dict[TipoAposta, float]) -> Dict[TipoAposta, float]:
        """Calcula a distribuição quântica para o 2º tempo com análise de valor"""
        import math
        import numpy as np

        try:
            # Estratégias base com proporções quânticas ajustáveis
            estrategias = {
                # MUITOS_GOLS
                PrevisaoPartida.MUITOS_GOLS: {
                    CenarioIntervalo.EMPATE_0X0: {
                        TipoAposta.MAIS_15_SEGUNDO_TEMPO: 0.6,
                        TipoAposta.PROXIMO_GOL_AZARAO: 0.3,
                        TipoAposta.NAO_SAIR_MAIS_GOLS: 0.1
                    },
                    CenarioIntervalo.EMPATE_1X1: {
                        TipoAposta.MAIS_15_SEGUNDO_TEMPO: 0.7,
                        TipoAposta.PROXIMO_GOL_AZARAO: 0.2,
                        TipoAposta.NAO_SAIR_MAIS_GOLS: 0.1
                    },
                    CenarioIntervalo.FAVORITO_GANHANDO_1X0: {
                        TipoAposta.MAIS_15_SEGUNDO_TEMPO: 0.5,
                        TipoAposta.AMBAS_MARCAM_SIM: 0.3,
                        TipoAposta.AMBAS_MARCAM_NAO: 0.2
                    },
                    CenarioIntervalo.FAVORITO_GANHANDO_2X0: {
                        TipoAposta.MAIS_15_SEGUNDO_TEMPO: 0.5,
                        TipoAposta.AMBAS_MARCAM_SIM: 0.3,
                        TipoAposta.AMBAS_MARCAM_NAO: 0.2
                    },
                    CenarioIntervalo.FAVORITO_GANHANDO_2X1: {
                        TipoAposta.MAIS_15_SEGUNDO_TEMPO: 0.7,
                        TipoAposta.PROXIMO_GOL_AZARAO: 0.3
                    },
                    CenarioIntervalo.FAVORITO_PERDENDO_0X1: {
                        TipoAposta.MAIS_15_SEGUNDO_TEMPO: 0.4,
                        TipoAposta.AMBAS_MARCAM_NAO: 0.3,
                        TipoAposta.AMBAS_MARCAM_SIM: 0.3
                    },
                    CenarioIntervalo.FAVORITO_PERDENDO_0X2: {
                        TipoAposta.MAIS_15_SEGUNDO_TEMPO: 0.5,
                        TipoAposta.AMBAS_MARCAM_NAO: 0.2,
                        TipoAposta.AMBAS_MARCAM_SIM: 0.3
                    },
                    CenarioIntervalo.FAVORITO_PERDENDO_1X2: {
                        TipoAposta.MAIS_15_SEGUNDO_TEMPO: 0.5,
                        TipoAposta.PROXIMO_GOL_AZARAO: 0.3,
                        TipoAposta.NAO_SAIR_MAIS_GOLS: 0.2                    
                    }
                },
                # POUCOS_GOLS
                PrevisaoPartida.POUCOS_GOLS: {
                    CenarioIntervalo.EMPATE_0X0: {
                        TipoAposta.NAO_SAIR_MAIS_GOLS: 0.3,
                        TipoAposta.MAIS_15_SEGUNDO_TEMPO: 0.5,
                        TipoAposta.PROXIMO_GOL_AZARAO: 0.2
                    },
                    CenarioIntervalo.EMPATE_1X1: {
                        TipoAposta.NAO_SAIR_MAIS_GOLS: 0.3,
                        TipoAposta.MAIS_15_SEGUNDO_TEMPO: 0.4,
                        TipoAposta.PROXIMO_GOL_AZARAO: 0.3
                    },
                    CenarioIntervalo.FAVORITO_GANHANDO_1X0: {
                        TipoAposta.AMBAS_MARCAM_NAO: 0.3,
                        TipoAposta.MAIS_15_SEGUNDO_TEMPO: 0.4,
                        TipoAposta.AMBAS_MARCAM_SIM: 0.3
                    },
                    CenarioIntervalo.FAVORITO_GANHANDO_2X0: {
                        TipoAposta.AMBAS_MARCAM_NAO: 0.4,
                        TipoAposta.MAIS_15_SEGUNDO_TEMPO: 0.3,
                        TipoAposta.AMBAS_MARCAM_SIM: 0.3
                    },
                    CenarioIntervalo.FAVORITO_GANHANDO_2X1: {
                        TipoAposta.MAIS_15_SEGUNDO_TEMPO: 0.4,
                        TipoAposta.PROXIMO_GOL_AZARAO: 0.3,
                        TipoAposta.NAO_SAIR_MAIS_GOLS: 0.3
                    },
                    CenarioIntervalo.FAVORITO_PERDENDO_0X1: {
                        TipoAposta.MAIS_15_SEGUNDO_TEMPO: 0.3,
                        TipoAposta.AMBAS_MARCAM_NAO: 0.3,
                        TipoAposta.AMBAS_MARCAM_SIM: 0.4
                    },
                    CenarioIntervalo.FAVORITO_PERDENDO_0X2: {
                        TipoAposta.MAIS_15_SEGUNDO_TEMPO: 0.3,
                        TipoAposta.AMBAS_MARCAM_NAO: 0.3,
                        TipoAposta.AMBAS_MARCAM_SIM: 0.4
                    },
                    CenarioIntervalo.FAVORITO_PERDENDO_1X2: {
                        TipoAposta.MAIS_15_SEGUNDO_TEMPO: 0.4,
                        TipoAposta.PROXIMO_GOL_AZARAO: 0.3,
                        TipoAposta.NAO_SAIR_MAIS_GOLS: 0.3           
                    }
                }
            }

            # Obter estratégia base
            estrategia_base = estrategias[self.previsao].get(cenario, {})
        
            # Fator quântico de ajuste baseado no placar
            gols_casa, gols_fora = map(int, st.session_state.placar_1t.split('x'))
            total_gols = gols_casa + gols_fora
            fator_quantico = 1 + (total_gols / 10) - (abs(gols_casa - gols_fora)) / 5

            # Calcular distribuição com análise de valor
            distribuicao = {}
            for aposta, proporcao_base in estrategia_base.items():
                if aposta in odds:
                    odd = odds[aposta]
                
                    # Análise quântica de valor (QVA)
                    qva = self._calcular_valor_quântico(aposta, odd, total_gols)

                    # Ajuste dinâmico baseado no valor quântico
                    proporcao_ajustada = proporcao_base * qva * fator_quantico
                    valor = capital * proporcao_ajustada
                
                    if valor >= 1.0:  # Só considera valores acima de 1 real
                        distribuicao[aposta] = round(float(valor), 2)

            # Normalização quântica
            total = sum(distribuicao.values())
            if total > capital:
                fator = capital / total
                distribuicao = {k: round(v * fator, 2) for k, v in distribuicao.items()}

            return distribuicao

        except Exception as e:
            print(f"Erro na distribuição quântica: {str(e)}")
            # Fallback seguro
            return {
                TipoAposta.MAIS_15_SEGUNDO_TEMPO: round(capital * 0.7, 2),
                TipoAposta.PROXIMO_GOL_AZARAO: round(capital * 0.3, 2)
            }

    def _calcular_valor_quântico(self, aposta: TipoAposta, odd: float, total_gols: int) -> float:
        """Calcula o valor quântico de uma aposta baseado em múltiplos fatores"""
        # Fatores de ponderação
        peso_odd = 0.6
        peso_historico = 0.3
        peso_gols = 0.1
    
        # Componente de odd (logarítmico para suavizar variações)
        comp_odd = 1 / math.log(odd) if odd > 1 else 0
    
        # Componente histórico
        comp_historico = self._obter_historico_aposta(aposta)
    
        # Componente de gols (ajusta com base no placar atual)
        if aposta == TipoAposta.MAIS_15_SEGUNDO_TEMPO:
            comp_gols = 1 + (total_gols / 10)
        elif aposta == TipoAposta.NAO_SAIR_MAIS_GOLS:
            comp_gols = 1 - (total_gols / 15)
        else:
            comp_gols = 1 - (total_gols / 20)
    
        # Cálculo do valor quântico
        valor = (peso_odd * comp_odd + 
                 peso_historico * comp_historico + 
                 peso_gols * comp_gols)
    
        # Garante valor entre 0.5 e 1.5 para não distorcer muito
        return max(0.5, min(1.5, valor))

    def _obter_historico_aposta(self, aposta: TipoAposta) -> float:
        """Retorna o desempenho histórico de cada tipo de aposta"""
        historico = {
            TipoAposta.MAIS_15_SEGUNDO_TEMPO: 0.75,
            TipoAposta.NAO_SAIR_MAIS_GOLS: 0.65,
            TipoAposta.PROXIMO_GOL_AZARAO: 0.7,
            TipoAposta.AMBAS_MARCAM_SIM: 0.68,
            TipoAposta.AMBAS_MARCAM_NAO: 0.72
        }
        return historico.get(aposta, 0.7)
        
    def _determinar_apostas_ativas(self) -> Dict[TipoAposta, float]:
        """Determina quais apostas do 1º tempo ainda estão ativas"""
        # Esta implementação deve ser complementada com dados reais do analytics
        return {}
    
    def _get_odd_padrao(self, aposta: TipoAposta) -> float:
        """Retorna odds padrão para cada tipo de aposta"""
        odds_padrao = {
            TipoAposta.MAIS_15_SEGUNDO_TEMPO: 1.8,
            TipoAposta.NAO_SAIR_MAIS_GOLS: 4.0,
            TipoAposta.AMBAS_MARCAM_NAO: 3.5,
            TipoAposta.PROXIMO_GOL_AZARAO: 3.5,
            TipoAposta.AMBAS_MARCAM_SIM: 2.5
        }
        return odds_padrao.get(aposta, 2.0)

    def _calcular_risco_atual(self, total_gols: int) -> float:
        """Calcula o risco atual baseado no placar do 1º tempo"""
        if self.previsao == PrevisaoPartida.MUITOS_GOLS:
            if total_gols == 0:
                return self.metricas.FATOR_RISCO * 2.0
            elif total_gols < 1.5:
                return self.metricas.FATOR_RISCO * 1.5
            else:
                return self.metricas.FATOR_SEGURANCA
        else:
            if total_gols > 1.5:
                return self.metricas.FATOR_RISCO * 1.8
            elif total_gols > 0.5:
                return self.metricas.FATOR_RISCO * 1.2
            else:
                return self.metricas.FATOR_SEGURANCA