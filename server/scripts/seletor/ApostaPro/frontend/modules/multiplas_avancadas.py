# frontend/modules/multiplas_avancadas.py (ATUALIZADO)
import streamlit as st
import pandas as pd
from typing import Dict, List
import plotly.express as px
import datetime
import math
from backend.otimizador_avancado import OtimizadorMultiplasAvancado

class GerenciadorMultiplasAvancadas:
    def __init__(self):
        self.otimizador = OtimizadorMultiplasAvancado()

    def mostrar_interface(self):
        st.title("🔢 Múltiplas Avançadas - Otimizador de Hedge")
        
        with st.expander("⚙️ Estratégia Automatizada", expanded=True):
            st.markdown("""
            **ESTRATÉGIA PRINCIPAL:**
            - **Hedge Perfeito:** O sistema calcula a distribuição de capital para que o retorno da **última proteção** cubra o **investimento total**.
            - **Recuperação de Risco:** A aposta **múltipla mais arriscada** é calculada para também retornar o **investimento total**.
            - **Cobertura Progressiva:** Cada aposta de proteção é dimensionada para cobrir o investimento acumulado até aquele momento.
            
            **COMO FUNCIONA:**
            1. Configure as partidas, odds e horários.
            2. Defina o capital total e seu nível de risco no slider.
            3. O sistema **resolve** a alocação de capital ideal para atender a todos os objetivos.
            """)
        self._mostrar_controles()

    def _mostrar_controles(self):
        tab1, tab2 = st.tabs(["📊 Configurar Partidas", "🎯 Distribuição de Apostas"])
        with tab1:
            self._coletar_dados_partidas()
        with tab2:
            if 'partidas_configuradas' in st.session_state and st.session_state.partidas_configuradas:
                self._mostrar_distribuicao_avancada(st.session_state.partidas_configuradas)
            else:
                st.info("Por favor, configure e confirme as partidas na primeira aba.")
                
    def _coletar_dados_partidas(self) -> List[Dict]:
        st.sidebar.markdown("### ⚙️ Configurações Avançadas")
        num_partidas = st.sidebar.selectbox("Número de Partidas", [2, 3, 4, 5, 6], index=2)
        partidas = []
        st.markdown("### 📋 Informe as Odds e Horários para Cada Partida")
        
        for i in range(num_partidas):
            with st.container(border=True):
                st.subheader(f"⚽ Partida {i+1}")
                cols = st.columns([2, 2, 2, 2, 1])
                odds = {
                    'partida': f'Partida {i+1}',
                    'favorito': cols[0].number_input("Odd Favorito", 1.01, 50.0, 1.80, 0.01, key=f'favorito_{i}'),
                    'dupla_chance': cols[1].number_input("Odd Dupla Chance", 1.01, 50.0, 2.05, 0.01, key=f'dupla_{i}'),
                    'mais15': cols[2].number_input("Odd Mais 1.5", 1.01, 50.0, 1.45, 0.01, key=f'over15_{i}'),
                    'under15': cols[3].number_input("Odd Menos 1.5", 1.01, 50.0, 2.60, 0.01, key=f'under15_{i}'),
                    'horario': cols[4].time_input("Horário", value=datetime.time(12 + i*3, 0), key=f'hora_{i}', 
                                                help="A ordem dos horários define a sequência da proteção.")
                }
                partidas.append(odds)

        if st.button("✅ Confirmar Partidas", type="primary"):
            st.session_state.partidas_configuradas = partidas
            st.success(f"{len(partidas)} partida(s) confirmada(s)! Prossiga para a aba 'Distribuição de Apostas'.")
        return partidas

    def _mostrar_distribuicao_avancada(self, partidas: List[Dict]):
        st.markdown("### 💰 Configuração de Capital")
        cols = st.columns(2)
        capital = cols[0].number_input("Valor Total para Apostas (R$)", min_value=10.0, value=20.0, step=5.0)
        protecao_slider = cols[1].slider("% Risco (Múltiplas vs Proteção)", 10, 50, 30, 
                                        help="Define o ponto de partida para o otimizador. O resultado final pode variar para atender às regras de hedge.")
        
        if st.button("🔄 Calcular Distribuição Otimizada", type="primary"):
            with st.spinner("Resolvendo a alocação ideal de capital..."):
                try:
                    self.otimizador = OtimizadorMultiplasAvancado()
                    for p in partidas:
                        self.otimizador.adicionar_partida(p)
                    resultado = self.otimizador.calcular_distribuicao(
                        capital_total=capital, 
                        percentual_protecao=protecao_slider/100
                    )
                    st.session_state.resultado = resultado
                except Exception as e:
                    st.error(f"Erro nos cálculos: {str(e)}")
                    st.exception(e)

        if 'resultado' in st.session_state:
            self._exibir_resultados(st.session_state.resultado, partidas)
    
    def _exibir_resultados(self, resultado: Dict, partidas: List[Dict]):
        # Seção de Múltiplas
        st.markdown("---")
        st.markdown("## 🎯 Estratégia de Múltiplas")
    
        multiplas = resultado.get('multiplas', [])
        cols = st.columns(3)
    
        for i, multipla in enumerate(multiplas):
            with cols[i % 3]:
                prob_percent = multipla.get('probabilidade', 0) * 100
                with st.expander(f"**Múltipla {i+1}** ({prob_percent:.1f}% de chance)", expanded=(i < 3)):
                    # Lista de apostas da múltipla
                    for aposta in multipla.get('apostas', []):
                        st.write(f"• {aposta['tipo']} @ {aposta['odd']:.2f}")
                
                    # Métricas de retorno
                    valor = float(multipla.get('valor', 0))
                    retorno = float(multipla.get('retorno', 0))
                    roi = ((retorno - valor) / valor * 100) if valor > 0 else 0
                    st.metric("Retorno Potencial", 
                             f"R$ {retorno:.2f}", 
                             f"Invest: R$ {valor:.2f} | ROI: {roi:.0f}%")

        # Seção de Proteção (Hedge)
        st.markdown("## 🛡️ Estratégia de Proteção (Hedge)")
    
        protecao = resultado.get('protecao', {})
        df_protecao = pd.DataFrame(protecao.get('distribuicao', []))
    
        if not df_protecao.empty:
            # Preparação dos dados
            df_protecao = df_protecao.rename(columns={
                'partida': 'Partida',
                'valor_investido': 'Investimento (R$)',
                'odd_protecao': 'Odd',
                'retorno_potencial': 'Retorno (R$)',
                'cobertura_necessaria': 'Cobertura (R$)'
            })
        
            # Adiciona horários
            if 'Partida' in df_protecao.columns:
                horarios = {
                    f'Partida {i+1}': p.get('horario', '').strftime('%H:%M') 
                    if hasattr(p.get('horario', ''), 'strftime') 
                    else str(p.get('horario', ''))
                    for i, p in enumerate(partidas)
                }
                df_protecao['Horário'] = df_protecao['Partida'].map(horarios)
        
            # Formatação da tabela
            st.dataframe(
                df_protecao.style.format({
                    'Investimento (R$)': '{:.2f}',
                    'Odd': '{:.2f}',
                    'Retorno (R$)': '{:.2f}',
                    'Cobertura (R$)': '{:.2f}'
                }).bar(subset=['Retorno (R$)'], color='#5fba7d'),
                hide_index=True
            )
        
            # Proteção em camadas
            self._mostrar_protecao_camadas(df_protecao)

        # Resumo Financeiro
        st.markdown("## 💰 Resumo Financeiro")
    
        capital_total = float(resultado.get('capital_total', 20.00))
        total_multiplas = sum(float(m.get('valor', 0)) for m in multiplas)
        total_protecao = float(protecao.get('valor_total', 0))
        capital_utilizado = total_multiplas + total_protecao
    
        # Cálculo de diferença
        diferenca = capital_total - capital_utilizado
        percentual_diferenca = (abs(diferenca) / capital_total * 100) if capital_total > 0 else 0
    
        # Layout em colunas
        col1, col2, col3, col4 = st.columns(4)
    
        with col1:
            st.metric("Total de Capital", 
                     f"R$ {capital_total:.2f}",
                     delta=f"Diferença: R$ {abs(diferenca):.2f}" if abs(diferenca) > 0.01 else "✅ Consistente",
                     delta_color="normal" if abs(diferenca) <= 0.01 else "inverse")
    
        with col2:
            st.metric("Total Investido", 
                     f"R$ {capital_utilizado:.2f}",
                     f"{min(100, (capital_utilizado/capital_total)*100):.1f}%")
    
        with col3:
            st.metric("Em Múltiplas", 
                     f"R$ {total_multiplas:.2f}",
                     f"{(total_multiplas/capital_total*100):.1f}%")
    
        with col4:
            st.metric("Em Proteção", 
                     f"R$ {total_protecao:.2f}",
                     f"{(total_protecao/capital_total*100):.1f}%")

        # Gráfico de Alocação
        st.markdown("## 📊 Alocação de Capital")
    
        if capital_total > 0:
            # Dados para o gráfico
            labels = [f"Múltipla {i+1}" for i in range(len(multiplas))] + ["Proteção"]
            values = [float(m.get('valor', 0)) for m in multiplas] + [total_protecao]
        
            # Verificação de consistência
            if abs(sum(values) - capital_total) > 0.01:
                st.warning(
                    f"**Atenção:** Diferença de R$ {abs(diferenca):.2f} "
                    f"({percentual_diferenca:.1f}%) entre o capital total e a alocação"
                )
        
            # Criação do gráfico
            fig = px.pie(
                names=labels,
                values=values,
                hole=0.4,
                title=f"Distribuição do Capital (Total: R$ {capital_total:.2f})",
                color_discrete_sequence=px.colors.qualitative.Pastel
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("Capital total não definido - não é possível exibir o gráfico")
        
    def _mostrar_protecao_camadas(self, df_protecao):
        st.markdown("### 🛡️ Proteção em Camadas")
    
        try:
            # Cria DataFrame com as camadas de proteção
            df_camadas = df_protecao.copy()
    
            # Calcula os valores para cada camada (30% + 30% + 40%)
            df_camadas['Menos 1.5 (30%)'] = df_camadas['Investimento (R$)'] * 0.3
            df_camadas['Menos 0.5 (30%)'] = df_camadas['Investimento (R$)'] * 0.3
            df_camadas['Futuro (40%)'] = df_camadas['Investimento (R$)'] * 0.4
    
            # Formatação dos valores
            for col in ['Menos 1.5 (30%)', 'Menos 0.5 (30%)', 'Futuro (40%)']:
                df_camadas[col] = df_camadas[col].apply(lambda x: f"R$ {max(0, x):.2f}")
    
            st.dataframe(df_camadas[['Partida', 'Horário', 'Menos 1.5 (30%)', 'Menos 0.5 (30%)', 'Futuro (40%)']],
                        hide_index=True)
    
            # Controle interativo de proteção - Versão simplificada e estática
            with st.expander("🔍 Controle de Proteção em Tempo Real", expanded=True):
                partida_selecionada = st.selectbox(
                    "Selecione a partida para análise:", 
                    df_camadas['Partida'].unique()
                )
        
                st.markdown(f"**Partida {partida_selecionada} - Ações de Proteção:**")
            
                # Exibição estática das opções
                st.markdown("""
                **Opções no intervalo:**
                - Mais 0,5 gols  
                ✅ Aplique 40% do valor em NÃO SAIR GOLS para {partida_selecionada}
            
                - Menos 0,5 gols  
                  ✅ Aplique 40% do valor em MENOS 1,5 GOLS para {partida_selecionada}
            
                **Esta ação protegerá seu investimento conforme a evolução do jogo.**
                """)
            
        except Exception as e:
            st.error(f"Erro ao exibir proteção em camadas: {str(e)}")