# frontend/modules/multiplas_avancadas_partida.py (CORRIGIDO)
import streamlit as st
import pandas as pd
from typing import Dict, List
import plotly.express as px
from backend.otimizador_avancado_partida import OtimizadorMultiplasPartida

class GerenciadorMultiplasPartida:
    def __init__(self):
        self.otimizador = OtimizadorMultiplasPartida()
        
    def mostrar_interface(self):
        st.title("🔢 Múltiplas Avançadas (Por Partida)")
        
        # O texto da estratégia foi atualizado para corresponder exatamente à sua imagem.
        with st.expander("⚙️ Estratégia Automatizada por Partida", expanded=True):
            st.markdown("""
            **ESTRATÉGIA PRINCIPAL:**
            - 2 Blocos de Combinações Independentes
            - Distribuição igualitária de retorno em cada bloco
            - Abrange todos os cenários possíveis
            - Pode simular múltiplos cenários
            - Aprimorar o ganho com outros Módulos
            
            **BLOCOS DE APOSTAS:**
            1. **Bloco Favorito:**
                - Favorito 
                - Combinações com Mais/Menos 0,5 gols no 1º tempo
            
            2. **Bloco Próximo gol Azarão Ou Empate/Azarão:**
                - Próximo gol Azarão Ou Empate/Azarão 
                - Combinações com Menos/Mais 2,5 gols partida e Mais/Menos 0,5 gols no 1º Tempo
            """)
            
        self._mostrar_controles()
        
    def _mostrar_controles(self):
        tab1, tab2 = st.tabs(["📊 Configurar Partida", "🎯 Distribuição de Apostas"])
        
        with tab1:
            self._coletar_dados_partida()
            
        with tab2:
            if 'partida_configurada' in st.session_state and st.session_state.partida_configurada:
                self._mostrar_distribuicao_avancada(st.session_state.partida_configurada)
            else:
                st.info("Por favor, configure e confirme a partida na primeira aba.")

    def _coletar_dados_partida(self) -> Dict:
        st.markdown("### 📋 Informe as Odds da Partida")
    
        with st.container():
            # Os nomes dos inputs foram mantidos, mas a exibição será corrigida no output.
            cols = st.columns(6)
            odds = {
                'partida': 'Partida Única',
                'favorito': cols[0].number_input("Time Favorito/Mais 0,5 1ºT", 1.01, 50.0, 1.80, 0.01, key='favorito'),
                'dupla_chance': cols[1].number_input("Time Favorito/Menos 0,5 1ºT", 1.01, 50.0, 2.05, 0.01, key='dupla'),
                'mais25': cols[2].number_input("Próximo gol Azarão/Empate/Azarão", 1.01, 50.0, 1.90, 0.01, key='over25'),
                'menos25': cols[3].number_input("Favorito", 1.01, 50.0, 1.68, 0.01, key='under25'),
                'mais15_1t': cols[4].number_input("Mais 0.5 1º Tempo/Mais 2,5 Gols", 1.01, 50.0, 3.00, 0.01, key='over15_1t'),
                'menos15_1t': cols[5].number_input("Menos 0.5 1º Tempo/Menos 2,5 Gols", 1.01, 50.0, 1.40, 0.01, key='under15_1t')
            }

            if st.button("✅ Confirmar Partida", type="primary"):
                st.session_state.partida_configurada = odds
                st.success("Partida confirmada! Prossiga para a aba 'Distribuição de Apostas'.")
                # Não precisa retornar, o session_state cuida disso.

    def _mostrar_distribuicao_avancada(self, partida: Dict):
        st.markdown("### 💰 Configuração de Capital")
        capital = st.number_input("Valor Total para Apostas (R$)", min_value=10.0, value=20.0, step=5.0)
        
        if st.button("🔄 Calcular Múltiplas", type="primary"):
            with st.spinner("Calculando estratégia ótima..."):
                try:
                    self.otimizador = OtimizadorMultiplasPartida()
                    self.otimizador.adicionar_partida(partida)
                    
                    resultado = self.otimizador.calcular_distribuicao(capital_total=capital)
                    st.session_state.resultado_partida = resultado # Salva em session_state
                    
                except Exception as e:
                    st.error(f"Erro nos cálculos: {str(e)}")
                    st.exception(e) # Adiciona mais detalhes do erro para depuração
        
        # Exibe o resultado se ele existir no estado da sessão
        if 'resultado_partida' in st.session_state:
            self._exibir_resultados(st.session_state.resultado_partida)
            
    def _exibir_resultados(self, resultado: Dict):
        multiplas = resultado.get('multiplas', [])
        if len(multiplas) < 4:
            st.warning("O backend não retornou o número esperado de múltiplas para exibição.")
            return

        bloco_favorito = multiplas[:2]
        bloco_azarão = multiplas[2:]
        
        st.markdown("---")
        st.markdown("## 🎯 Bloco Favorito")
        cols_fav = st.columns(2)
        for i, multipla in enumerate(bloco_favorito):
            with cols_fav[i]:
                self._mostrar_multipla(multipla, i + 1)
        
        # Título do segundo bloco corrigido para corresponder à imagem.
        st.markdown("---")
        st.markdown("## 🎯 Bloco Empate/Azarão")
        cols_aza = st.columns(2)
        for i, multipla in enumerate(bloco_azarão):
            with cols_aza[i]:
                self._mostrar_multipla(multipla, i + 3)
        
        self._mostrar_alocacao_capital(resultado)
    
    def _mostrar_multipla(self, multipla: Dict, numero: int):
        """
        Função RECONSTRUÍDA para exibir o texto exato da imagem de exemplo,
        usando o número da múltipla para determinar o que mostrar.
        """
        prob_percent = multipla.get('probabilidade', 0) * 100
        
        # Garante que a lista de apostas exista antes de tentar acessá-la
        apostas = multipla.get('apostas', [])
        if len(apostas) < 2:
            st.error("Dados da múltipla incompletos.")
            return

        aposta1 = apostas[0]
        aposta2 = apostas[1]
        
        with st.expander(f"**Múltipla {numero}️⃣** ({prob_percent:.1f}% chance)", expanded=True):
            
            # Lógica de exibição baseada no número da múltipla para garantir 100% de acerto
            if numero == 1:
                st.write(f"• Favorito @ {aposta1.get('odd', 0):.2f}")
                st.write(f"• Favorito/Mais 0,5 1ºT @ {aposta2.get('odd', 0):.2f}")
            elif numero == 2:
                st.write(f"• Favorito @ {aposta1.get('odd', 0):.2f}")
                st.write(f"• Favorito/Menos 0,5 1ºT @ {aposta2.get('odd', 0):.2f}")
            elif numero == 3:
                st.write(f"• Empate/Azarão/Próximo gol @ {aposta1.get('odd', 0):.2f}")
                st.write(f"• Mais 0,5 Gols 1T/Mais 2,5 gols @ {aposta2.get('odd', 0):.2f}")
            elif numero == 4:
                st.write(f"• Empate/Azarão/Próximo gol @ {aposta1.get('odd', 0):.2f}")
                st.write(f"• Menos 0,5 Gols 1T/Menos 2,5 gols @ {aposta2.get('odd', 0):.2f}")
            
            valor = multipla.get('valor', 0)
            retorno = multipla.get('retorno', 0)
            roi = ((retorno - valor) / valor * 100) if valor > 0 else 0
            
            st.metric(
                "Retorno", 
                f"R$ {retorno:.2f}", 
                f"Invest: R$ {valor:.2f} | ROI: {roi:.0f}%"
            )

    def _mostrar_alocacao_capital(self, resultado: Dict):
        st.markdown("---")
        st.markdown("## 📊 Alocação de Capital")
        
        multiplas = resultado.get('multiplas', [])
        nomes = [f"Múltipla {i+1}" for i in range(len(multiplas))]
        valores = [m.get('valor', 0) for m in multiplas]

        if sum(valores) > 0:
            fig = px.pie(
                names=nomes,
                values=valores,
                hole=0.4,
                title="Distribuição do Valor por Múltipla",
                color_discrete_sequence=['#636EFA', '#EF553B', '#00CC96', '#AB63FA', '#FFA15A', '#19D3F3']
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("Não foi possível gerar o gráfico de alocação.")