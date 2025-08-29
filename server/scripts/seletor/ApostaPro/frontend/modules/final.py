# modules/final.py
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from typing import Dict
from dataclasses import dataclass
from frontend.config import TipoAposta, CenarioIntervalo
from modules.analytics import QuantumAnalyzer

@dataclass
class ResultadoFinal:
    """Armazena os resultados finais da partida com métricas quânticas"""
    placar_final: str
    retornos_1t: Dict[TipoAposta, float]
    retornos_2t: Dict[TipoAposta, float]
    total_investido: float
    total_retorno: float
    lucro_prejuizo: float
    fase_quantica: float
    eficiencia_estrategia: float

class GerenciadorFinal:
    """Classe para gerenciar a análise final com otimização quântica"""
    
    def __init__(self):
        self.quantum = QuantumAnalyzer(phi=6)
        self._inicializar_estado()
        
    def _inicializar_estado(self):
        """Inicializa o estado da sessão para o resultado final"""
        if 'analise_completa' not in st.session_state:
            st.session_state.analise_completa = False
    
    def calcular_resultados_finais(self, placar_final: str) -> ResultadoFinal:
        """Calcula os resultados finais com a nova lógica progressiva quântica"""
        # Análise do placar
        gols_1t = list(map(int, st.session_state.placar_1t.split('x')))
        gols_final = list(map(int, placar_final.split('x')))
        gols_2t = [gols_final[0]-gols_1t[0], gols_final[1]-gols_1t[1]]
        total_gols_2t = sum(gols_2t)
        
        # Cálculo quântico
        flux_data = self.quantum.calculate_flux(placar_final)
        phase = self.quantum.fluid_percentage(
            flux_data['current'],
            flux_data['resonance'],
            flux_data['base']
        )
        
        # Fator de ajuste quântico
        fator_quantico = 1 + (phase - 100) / 200  # Normaliza entre 0.75 e 1.25
        
        # Cálculo dos retornos do 2º tempo com otimização quântica
        retornos_2t = {}
        for aposta, valor in st.session_state.distribuicao_intervalo.items():
            odd = st.session_state.odds_2t.get(aposta, 1.0)
            
            if aposta == TipoAposta.MAIS_15_SEGUNDO_TEMPO:
                ganhou = (total_gols_2t > 1.5)
                retornos_2t[aposta] = (valor * (odd - 1) * fator_quantico) if ganhou else (-valor)
                
            elif aposta == TipoAposta.AMBAS_MARCAM_SIM:
                ganhou = (gols_2t[0] > 0 and gols_2t[1] > 0)
                # Ajuste para odds entre 1.5 e 3.0
                fator_odd = min(3.0, max(1.5, odd)) / 2.25
                retornos_2t[aposta] = (valor * (odd - 1) * fator_odd * fator_quantico) if ganhou else (-valor)
                
            elif aposta == TipoAposta.AMBAS_MARCAM_NAO:
                ganhou = not (gols_2t[0] > 0 and gols_2t[1] > 0)
                # Ajuste para odds entre 1.5 e 3.5
                fator_odd = min(3.5, max(1.5, odd)) / 2.5
                retornos_2t[aposta] = (valor * (odd - 1) * fator_odd * fator_quantico) if ganhou else (-valor)
        
        # Cálculos totais
        total_investido = (sum(st.session_state.distribuicao_pre_partida.values()) + 
                          sum(st.session_state.distribuicao_intervalo.values()))
        
        total_retorno = (sum(st.session_state.retornos_1t.values()) + 
                        sum(retornos_2t.values()) +
                        total_investido)
        
        lucro_prejuizo = total_retorno - total_investido
        
        # Eficiência da estratégia (0 a 100)
        eficiencia = max(0, min(100, 50 + (phase - 100) + (lucro_prejuizo * 10)))
        
        return ResultadoFinal(
            placar_final=placar_final,
            retornos_1t=st.session_state.retornos_1t,
            retornos_2t=retornos_2t,
            total_investido=total_investido,
            total_retorno=total_retorno,
            lucro_prejuizo=lucro_prejuizo,
            fase_quantica=phase,
            eficiencia_estrategia=eficiencia
        )

    def mostrar_interface(self):
        """Mostra a interface completa para o resultado final com análise quântica"""
        st.title("🏁 Resultado Final - Análise Quântica")
        
        if not st.session_state.get('placar_final'):
            placar = st.text_input("Digite o placar final (ex: 2x1):")
            if st.button("Calcular Resultados", type="primary"):
                st.session_state.placar_final = placar
                resultado = self.calcular_resultados_finais(placar)
                st.session_state.resultado_final = resultado
                st.session_state.analise_completa = True
                st.rerun()
            return None
            
        resultado = st.session_state.resultado_final
        
        # Métricas principais
        cols = st.columns(4)
        cols[0].metric("Placar Final", resultado.placar_final)
        cols[1].metric("Total Investido", f"R$ {resultado.total_investido:.2f}")
        cols[2].metric("Total Retorno", f"R$ {resultado.total_retorno:.2f}")
        cols[3].metric("Resultado", f"R$ {resultado.lucro_prejuizo:.2f}",
                      delta=f"{resultado.lucro_prejuizo/resultado.total_investido*100:.1f}%")
        
        # Análise quântica
        st.subheader("🔮 Análise Quântica")
        st.write(f"**Fase Quântica:** {resultado.fase_quantica:.2f}%")
        st.write(f"**Eficiência da Estratégia:** {resultado.eficiencia_estrategia:.1f}/100")
        
        # Detalhamento dos retornos
        st.subheader("📊 Detalhamento dos Retornos")
        
        # Retornos do 1º tempo
        df_1t = pd.DataFrame({
            "Aposta": [aposta.value for aposta in resultado.retornos_1t.keys()],
            "Retorno (R$)": resultado.retornos_1t.values()
        })
        
        # Retornos do 2º tempo
        df_2t = pd.DataFrame({
            "Aposta": [aposta.value for aposta in resultado.retornos_2t.keys()],
            "Retorno (R$)": resultado.retornos_2t.values()
        })
        
        tab1, tab2 = st.tabs(["1º Tempo", "2º Tempo"])
        with tab1:
            st.dataframe(df_1t.style.format({"Retorno (R$)": "{:.2f}"}))
        with tab2:
            st.dataframe(df_2t.style.format({"Retorno (R$)": "{:.2f}"}))
        
        # Gráfico de desempenho
        fig, ax = plt.subplots()
        ax.bar(["1º Tempo", "2º Tempo"], 
              [sum(resultado.retornos_1t.values()), sum(resultado.retornos_2t.values())],
              color=['#1f77b4', '#ff7f0e'])
        ax.set_title("Retorno por Fase da Partida")
        st.pyplot(fig)
        
        return resultado