import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from typing import List, Dict
from backend.otimizador import ApostaMultipla

class VisualizadorResultados:
    @staticmethod
    def mostrar_resultados(estrategia: Dict):
        """Versão com tratamento para dados serializados"""
        # Converter strings de volta para tuplas se necessário
        if isinstance(next(iter(estrategia['apostas'][0].combinacao), str)):
            for aposta in estrategia['apostas']:
                aposta.combinacao = tuple(aposta.combinacao.strip("()").replace("'","").split(", "))
        """Mostra os resultados da estratégia de forma organizada"""
        
        st.header("📊 Resultados da Estratégia")
        
        total_investido = sum(x.valor_apostado for x in estrategia['apostas'])
        retorno_esperado = sum(x.retorno_potencial * x.probabilidade for x in estrategia['apostas'])
        roi_medio = (sum(x.roi for x in estrategia['apostas']) / len(estrategia['apostas'])) * 100

        # Métricas resumidas
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Investido", f"R$ {total_investido:.2f}")
        col2.metric("Retorno Esperado", f"R$ {retorno_esperado:.2f}")
        col3.metric("ROI Médio", f"{roi_medio:.2f}%")
        
        # Tabela de apostas
        st.subheader("📝 Detalhes das Apostas")
        df = pd.DataFrame([{
            'Combinação': ' - '.join(x.combinacao),
            'Valor (R$)': x.valor_apostado,
            'Retorno (R$)': x.retorno_potencial,
            'Probabilidade': f"{x.probabilidade * 100:.2f}%",
            'ROI Esperado': f"{x.roi * 100:.2f}%"
        } for x in estrategia['apostas']])
        
        st.dataframe(df.style.format({
            'Valor (R$)': "{:.2f}",
            'Retorno (R$)': "{:.2f}"
        }))
        
        # Gráficos
        st.subheader("📈 Visualizações")
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
        
        # Gráfico 1: Distribuição de valor
        ax1.pie(
            [x.valor_apostado for x in estrategia['apostas']],
            labels=[f"Combinação {i+1}" for i in range(len(estrategia['apostas']))],
            autopct='%1.1f%%'
        )
        ax1.set_title("Distribuição do Valor Apostado")
        
        # Gráfico 2: Retorno vs Probabilidade
        ax2.scatter(
            [x.probabilidade for x in estrategia['apostas']],
            [x.retorno_potencial for x in estrategia['apostas']],
            s=[x.valor_apostado * 10 for x in estrategia['apostas']],
            alpha=0.7,
            color='green'
        )
        ax2.set_xlabel("Probabilidade")
        ax2.set_ylabel("Retorno Potencial (R$)")
        ax2.set_title("Relação Risco-Retorno")
        
        st.pyplot(fig)
        
        # Proteções
        if estrategia.get('protecoes'):
            st.subheader("🛡️ Estratégias de Proteção")
            df_protecoes = pd.DataFrame(estrategia['protecoes'])
            st.dataframe(df_protecoes.style.format({
                'Valor': "{:.2f}",
                'Odd': "{:.2f}"
            }))
