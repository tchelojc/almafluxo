import streamlit as st
import numpy as np
import pandas as pd
import itertools
from typing import Dict, List, Tuple
from dataclasses import dataclass
from enum import Enum
from io import BytesIO
from backend.otimizador import OtimizadorMultiplas
from modules.analise_distribuicao import AnalisadorDistribuicao

class TipoMultipla(Enum):
    SIMPLES = 1
    DUPLA = 2
    TRIPLA = 3
    QUADRA = 4
    QUINTA = 5

@dataclass
class ProjecaoMultipla:
    partidas: List[Dict[str, float]]
    valor_aposta: float
    tipo: TipoMultipla
    combinacoes: List[Tuple[str, ...]]
    retornos: Dict[Tuple[str, ...], float]
    probabilidades: Dict[Tuple[str, ...], float]
    roi: Dict[Tuple[str, ...], float]

class GerenciadorMultiplas:
    def __init__(self):
        self.quantum_processor = None
        self.combinacoes_otimizadas = []
        self.distribuicao_otimizada = []
        self.todas_combinacoes = []
        self.otimizador = OtimizadorMultiplas()
        
        if 'projecao_atual' not in st.session_state:
            st.session_state.projecao_atual = None
        if 'calculos_realizados' not in st.session_state:
            st.session_state.calculos_realizados = False

    def mostrar_interface(self):
        st.title("🔢 Apostas Múltiplas Avançadas")
        
        # Abas para operação normal e testes
        tab_principal, tab_testes = st.tabs(["Operação", "Testes de Tolerância"])
        
        with tab_principal:
            self._mostrar_interface_principal()
            
        with tab_testes:
            self._mostrar_interface_testes()

    def _mostrar_interface_principal(self):
        """Interface principal para apostas múltiplas"""
        partidas = self._coletar_dados_partidas()
    
        valor_total = st.number_input("💰 Valor Total para Distribuição (R$)", 
                                    min_value=10.0, max_value=10000.0, 
                                    value=20.0, step=5.0, format="%.2f")
    
        tolerancia = st.slider("🎯 Tolerância", 0.0, 0.1, 0.01, 0.01,
                             help="Define o nível de tolerância para combinações válidas")
    
        if st.button("🔄 Calcular Distribuição Ótima"):
            with st.spinner(f"Otimizando distribuição com tolerância {tolerancia}..."):
                try:
                    # Limpa resultados anteriores
                    if 'resultado_multiplas' in st.session_state:
                        del st.session_state.resultado_multiplas
                
                    # Calcula nova distribuição
                    resultado = self.otimizar_distribuicao(partidas, valor_total, tolerancia)
                
                    # Armazena na sessão
                    st.session_state.resultado_multiplas = resultado
                    st.session_state.calculos_realizados = True
                
                    # Força atualização
                    st.rerun()
                
                except Exception as e:
                    st.error(f"Erro na otimização: {str(e)}")
                    st.session_state.calculos_realizados = False

        # Mostra resultados se existirem
        if st.session_state.get('calculos_realizados', False):
            self._mostrar_resultados(st.session_state.resultado_multiplas)

    def _mostrar_interface_testes(self):
        """Interface para testes de tolerância"""
        st.subheader("🧪 Testes de Validação de Tolerância")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Teste Automático**")
            if st.button("Executar Testes Automáticos"):
                try:
                    self._executar_testes_automaticos()
                    st.success("✅ Todos os testes de tolerância passaram!")
                except AssertionError as e:
                    st.error(f"❌ Falha no teste: {str(e)}")
                except Exception as e:
                    st.error(f"Erro inesperado: {str(e)}")
        
        with col2:
            st.markdown("**Teste Manual**")
            tolerancia_teste = st.number_input("Tolerância para teste", 
                                              min_value=0.0, max_value=0.1, 
                                              value=0.05, step=0.01)
            
            if st.button("Testar Tolerância Específica"):
                resultado = self._testar_tolerancia_especifica(tolerancia_teste)
                st.json(resultado)

    def _executar_testes_automaticos(self):
        """Executa testes automatizados de tolerância"""
        # Teste com tolerância zero
        resultado_zero = self._testar_tolerancia_especifica(0.0)
        assert resultado_zero['tolerancia_utilizada'] == 0.0
        assert len(resultado_zero['combinacoes']) > 0
        
        # Teste com tolerância padrão
        resultado_padrao = self._testar_tolerancia_especifica(0.01)
        assert resultado_padrao['tolerancia_utilizada'] == 0.01
        assert len(resultado_padrao['combinacoes']) >= len(resultado_zero['combinacoes'])
        
        # Teste com tolerância alta
        resultado_alta = self._testar_tolerancia_especifica(0.1)
        assert resultado_alta['tolerancia_utilizada'] == 0.1
        assert len(resultado_alta['combinacoes']) >= len(resultado_padrao['combinacoes'])

    def _testar_tolerancia_especifica(self, tolerancia: float) -> Dict:
        """Executa um teste com uma tolerância específica"""
        partidas_teste = [
            {
                'casa': 1.8, 'empate': 3.2, 'fora': 4.5,
                'under_25': 2.1, 'ambas_nao': 1.85
            },
            {
                'casa': 1.8, 'empate': 3.2, 'fora': 4.5,
                'under_25': 1.85, 'ambas_nao': 2.1
            }
        ]
        
        otimizador = OtimizadorMultiplas()
        for partida in partidas_teste:
            otimizador.adicionar_partida(partida)
        
        return otimizador.calcular_distribuicao(100.0, tolerancia)

    def _coletar_dados_partidas(self) -> List[Dict]:
        num_partidas = st.slider("Número de Partidas", 2, 10, 2)
        partidas = []

        for i in range(num_partidas):
            with st.expander(f"⚽ Partida {i+1}", expanded=True):
                cols = st.columns(3)
                odds = {
                    'casa': cols[0].number_input(f"Time Casa ⚽ {i+1}", 1.01, 50.0, 1.8, 0.01, format="%.2f"),
                    'empate': cols[1].number_input(f"Empate ➖ {i+1}", 1.01, 50.0, 3.2, 0.01, format="%.2f"),
                    'fora': cols[2].number_input(f"Time Fora 🏃 {i+1}", 1.01, 50.0, 4.5, 0.01, format="%.2f"),
                    'under_25': st.number_input(f"Menos de 2.5 Gols 🔻 ou Mais de 1.5 Gols 🔺 {i+1}", 1.01, 50.0, 1.75, 0.01, format="%.2f"),
                    'ambas_nao': st.number_input(f"Ambas Não ❌ ou Ambas Sim ✅ {i+1}", 1.01, 50.0, 1.85, 0.01, format="%.2f")
                }
                partidas.append(odds)

        for p in partidas:
            if not all(k in p for k in ['casa', 'empate', 'fora', 'under_25', 'ambas_nao']):
                st.error(f"Partida {partidas.index(p)+1} está incompleta")
                return []

        return partidas

    def _mostrar_configuracoes(self):
        st.markdown("Configure abaixo as opções de múltiplas e veja as perspectivas possíveis.")
        
        num_partidas = st.slider("🎯 Número de Partidas", 1, 10, 5)
        tipo = st.selectbox("📊 Tipo de Múltipla", list(TipoMultipla), 
                          format_func=lambda x: x.name.title())
        valor_aposta = st.number_input("💰 Valor da Aposta (R$)", 
                                     min_value=1.0, value=20.0, step=1.0)

        partidas = []
        for i in range(num_partidas):
            st.markdown(f"### Partida {i+1}")
            casa = st.number_input(f"⚽ Odd Casa {i+1}", min_value=1.01, value=1.8, key=f"casa_{i}")
            empate = st.number_input(f"➖ Odd Empate {i+1}", min_value=1.01, value=3.2, key=f"empate_{i}")
            fora = st.number_input(f"🏃 Odd Fora {i+1}", min_value=1.01, value=4.5, key=f"fora_{i}")
            partidas.append({'casa': casa, 'empate': empate, 'fora': fora})

        if st.button("🔍 Calcular Múltiplas"):
            # Realiza os cálculos e armazena no session_state
            st.session_state.projecao_atual = self.projetar_retornos(partidas, valor_aposta, tipo)
            st.session_state.projecao_atual = self.aplicar_analise_quantica(st.session_state.projecao_atual)
            st.session_state.calculos_realizados = True
            
            # Força a atualização das outras abas
            st.success("Cálculos realizados com sucesso!")
            st.rerun()
            
    def _formatar_combinacao(self, combinacao: tuple) -> str:
        """Formata a combinação para exibição amigável"""
        if not isinstance(combinacao, (tuple, list)):
            return str(combinacao)
    
        num_partidas = len(combinacao) // 3
        partes = []
    
        for i in range(num_partidas):
            principal = combinacao[i*3]
            under = combinacao[i*3+1]
            ambas = combinacao[i*3+2]
        
            partes.append(f"P{i+1}: {principal} + Under2.5 + AmbasNão")
        
        return " | ".join(partes)

    def _mostrar_projecao(self):
        if st.session_state.calculos_realizados and st.session_state.projecao_atual:
            self._mostrar_resultados(st.session_state.projecao_atual)
        else:
            st.warning("Configure as apostas e clique em 'Calcular Múltiplas' para ver os resultados")

    def _mostrar_otimizacao(self):
        if st.session_state.calculos_realizados and st.session_state.projecao_atual:
            self.mostrar_otimizacao(st.session_state.projecao_atual)
        else:
            st.warning("Configure as apostas e clique em 'Calcular Múltiplas' para ver a otimização")

    def otimizar_distribuicao(self, partidas: List[Dict], capital: float, tolerancia: float = 0.01) -> Dict:
        try:
            self.otimizador = OtimizadorMultiplas()
        
            for odds in partidas:
                self.otimizador.adicionar_partida(odds)
        
            resultado = self.otimizador.calcular_distribuicao(capital, tolerancia)
        
            # Adiciona análise ao resultado
            analisador = AnalisadorDistribuicao(resultado)
            resultado['analise'] = analisador.analisar_distribuicao()
        
            return resultado
        except Exception as e:
            return {
                'tipo_distribuicao': 'erro',
                'erro': str(e),
                'tolerancia_utilizada': tolerancia
            }

    def _mostrar_resultados(self, resultado: Dict):
        """Exibe os resultados com verificação de consistência"""
        if resultado.get('tipo_distribuicao') == 'erro':
            st.error(f"Erro nos cálculos: {resultado.get('erro', 'Erro desconhecido')}")
            return

        st.subheader("📊 Distribuição Ótima do Capital")

        tab1, tab2, tab3 = st.tabs(["Visão Geral", "Por Tipo de Mercado", "Top Combinações"])

        with tab1:
            try:
                if 'analise' in resultado and 'distribuicao_principal' in resultado['analise']:
                    df = resultado['analise']['distribuicao_principal'].copy()

                    df['Combinação'] = df['Combinação'].apply(
                        lambda x: self._formatar_combinacao(eval(x) if isinstance(x, str) else x)
                    )

                    if 'Retorno Total (R$)' not in df.columns:
                        retornos = resultado.get('retornos', {})
                        df['Retorno Total (R$)'] = df['Valor (R$)'].apply(lambda x: x * retornos.get(x, 1))
                        df['Lucro Potencial (R$)'] = df['Retorno Total (R$)'] - df['Valor (R$)']

                    st.dataframe(
                        df.style.format({
                            'Valor (R$)': 'R$ {:.2f}',
                            'Retorno Total (R$)': 'R$ {:.2f}',
                            'Lucro Potencial (R$)': 'R$ {:.2f}',
                            'Probabilidade': '{:.2%}',
                            'ROI Esperado': '{:.2%}'
                        }),
                        height=600
                    )
                else:
                    st.warning("Nenhuma combinação válida foi encontrada com os parâmetros atuais")
            except Exception as e:
                st.error(f"Ocorreu um erro ao processar a aba Visão Geral: {e}")

        with tab2:
            try:
                df = resultado['analise']['por_tipo_mercado']
                if 'Valor (R$)' in df.columns and 'Tipo Mercado' in df.columns:
                    df['Valor (R$)'] = pd.to_numeric(df['Valor (R$)'], errors='coerce')
                    st.dataframe(df)
                    st.bar_chart(df.set_index('Tipo Mercado')['Valor (R$)'])
                else:
                    st.warning("Dados insuficientes para exibir gráfico por tipo de mercado")

            except Exception as e:
                st.error(f"Ocorreu um erro na aba Por Tipo de Mercado: {e}")

        with tab3:
            try:
                self._mostrar_top_combinacoes(resultado)
            except Exception as e:
                st.error(f"Ocorreu um erro na aba Top Combinações: {e}")

    def _mostrar_distribuicao_geral(self, resultado: Dict):
        if not resultado.get('combinacoes'):
            st.warning("Nenhuma combinação válida encontrada")
            return
    
        dados = []
        for comb in resultado['combinacoes']:
            valor = resultado['distribuicao'].get(comb, 0)
            retorno = resultado['retornos'].get(comb, 1)
            prob = resultado['probabilidades'].get(comb, 0)
        
            # Formata a descrição da combinação
            descricao = []
            num_partidas = len(resultado['partidas'])
            for i in range(num_partidas):
                part_comb = comb[i*3 : (i+1)*3]  # Pega os 3 mercados desta partida
                principal = [m for m in part_comb if m in ['casa', 'empate', 'fora']][0]
                descricao.append(f"P{i+1}: {principal.title()} + Under 2.5 + Ambas Não")
        
            dados.append({
                'Combinação': " | ".join(descricao),
                'Valor (R$)': valor,
                'Retorno Potencial (R$)': valor * retorno,
                'Lucro Potencial (R$)': valor * (retorno - 1),
                'Probabilidade': f"{prob*100:.2f}%",
                'ROI Esperado': f"{((retorno - 1) * 100):.2f}%"
            })
    
        df = pd.DataFrame(dados).sort_values('Probabilidade', ascending=False)
    
        st.dataframe(
            df.style.format({
                'Valor (R$)': 'R$ {:.2f}',
                'Retorno Potencial (R$)': 'R$ {:.2f}',
                'Lucro Potencial (R$)': 'R$ {:.2f}'
            }),
            height=600
        )
        
    def _mostrar_por_tipo_mercado(self, df: pd.DataFrame):
        st.dataframe(
            df.style.format({
                'Valor (R$)': 'R$ {:.2f}',
                'Retorno Esperado (R$)': 'R$ {:.2f}',
                'Probabilidade': '{:.2%}',
                'ROI Esperado': '{:.2%}'
            }).background_gradient(
                subset=['Valor (R$)'],
                cmap='Blues'
            )
        )
        
        st.bar_chart(df['Valor (R$)'])
        
    def _mostrar_top_combinacoes(self, resultado: Dict):
        if 'analise' not in resultado:
            st.warning("Análise não disponível")
            return

        analisador = AnalisadorDistribuicao(resultado)
        resultado_analise = analisador.identificar_top_combinacoes(10, 20.0)
        top_combinacoes = resultado_analise['por_probabilidade']
        referencia = resultado_analise['referencia']

        st.subheader("🔝 Top Combinações por Probabilidade")
        st.markdown(f"**Combinação de referência (maior probabilidade):** {self._formatar_combinacao(referencia['combinacao'])}")
        st.markdown(f"**Probabilidade de referência:** {referencia['probabilidade']:.6f}")
        st.markdown(f"**Retorno de referência:** {referencia['retorno']:.2f}x")

        dados = []
        for item in top_combinacoes:
            dados.append({
                'Combinação': self._formatar_combinacao(item['combinacao']),
                'Probabilidade': item['probabilidade'],
                'Multiplicador Odds': item['retorno_potencial'],
                'Valor Investido (R$)': item['valor_otimizado'],
                'Retorno Total (R$)': item['retorno_total'],
                'Lucro Potencial (R$)': item['lucro_potencial'],
                'ROI': item['roi'] * 100  # para deixar pronto para formatação em '%'
            })

        df = pd.DataFrame(dados)
    
        st.dataframe(
            df.style.format({
                'Probabilidade': '{:.6f}',
                'Multiplicador Odds': '{:.2f}x',
                'Valor Investido (R$)': 'R$ {:.2f}',
                'Retorno Total (R$)': 'R$ {:.2f}',
                'Lucro Potencial (R$)': 'R$ {:.2f}',
                'ROI': '{:.2%}'
            }),
            height=600
        )
        
    def mostrar_otimizacao(self, projecao: ProjecaoMultipla):
        """Exibe a distribuição otimizada em abas separadas"""
        if not self.distribuicao_otimizada:
            self.otimizar_distribuicao(projecao)
        
        tab_dist, tab_analise, tab_detalhes = st.tabs(["📊 Distribuição", "📈 Análise", "⚙️ Detalhes"])
        
        with tab_dist:
            st.subheader("Distribuição Otimizada")
            
            # Tabela de distribuição aprimorada
            dados_tabela = []
            for item in self.distribuicao_otimizada:
                dados_tabela.append({
                    'Combinação': ' - '.join(item['combinacao']),
                    'Valor Apostado': f"R$ {item['valor_apostado']:.2f}",
                    'Retorno Potencial': f"R$ {item['retorno_potencial']:.2f}",
                    'Probabilidade': f"{item['probabilidade']*100:.2f}%",
                    'ROI Esperado': f"{item['roi_esperado']:.2f}%",
                    'Lucro Potencial': f"R$ {item['retorno_potencial'] - item['valor_apostado']:.2f}"
                })
            
            st.dataframe(pd.DataFrame(dados_tabela), hide_index=True)
            
            # Gráficos de alocação
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("Alocação de Capital")
                df_plot = pd.DataFrame({
                    'Combinação': [d['Combinação'][:15] + '...' for d in dados_tabela],
                    'Valor Apostado': [float(d['Valor Apostado'][3:]) for d in dados_tabela]
                })
                st.bar_chart(df_plot.set_index('Combinação'))
            
            with col2:
                st.subheader("Distribuição de Probabilidade")
                df_prob = pd.DataFrame({
                    'Combinação': [d['Combinação'][:15] + '...' for d in dados_tabela],
                    'Probabilidade': [float(d['Probabilidade'][:-1]) for d in dados_tabela]
                })
                st.bar_chart(df_prob.set_index('Combinação'))
        
        with tab_analise:
            st.subheader("Análise de Risco-Retorno")
            
            # Métricas resumidas
            retorno_esperado = sum(item['retorno_potencial'] * item['probabilidade'] 
                                 for item in self.distribuicao_otimizada)
            risco_total = sum(item['valor_apostado'] * (1 - item['probabilidade'])
                                 for item in self.distribuicao_otimizada)
            
            col1, col2, col3 = st.columns(3)
            col1.metric("Retorno Esperado Total", f"R$ {retorno_esperado:.2f}")
            col2.metric("Risco Total Estimado", f"R$ {risco_total:.2f}")
            col3.metric("ROI Médio", f"{retorno_esperado / projecao.valor_aposta * 100:.2f}%")
            
            # Gráficos de análise
            dados_analise = []
            for item in self.distribuicao_otimizada:
                dados_analise.append({
                    'Probabilidade': item['probabilidade'],
                    'Retorno': item['retorno_potencial'],
                    'ROI': item['roi_esperado'],
                    'Combinação': ' - '.join(item['combinacao'])[:20] + '...',
                    'Lucro': item['retorno_potencial'] - item['valor_apostado']
                })
            
            df_analise = pd.DataFrame(dados_analise)
            
            st.scatter_chart(df_analise, x='Probabilidade', y='Lucro', color='Combinação')
        
        with tab_detalhes:
            st.subheader("Detalhes Técnicos")
            st.markdown("**Cálculos Realizados:**")
            
            # Mostrar a lógica de cálculo como no código React
            st.code("""
            // Lógica de cálculo (implementada em Python)
            probabilidade_total = 1.0
            retorno_total = 1.0
            for partida in partidas:
                odd_media = sum(partida.values()) / len(partida)
                probabilidade_total *= 1 / odd_media
                retorno_total *= odd_media
            
            lucro_potencial = retorno_total * valor_aposta - valor_aposta
            retorno_esperado = valor_aposta * (1 - probabilidade_total)
            """, language='python')
            
            # Mostrar todas as combinações calculadas
            st.markdown("**Todas as Combinações Calculadas**")
            dados_detalhes = []
            for comb, ret, prob, roi in self.todas_combinacoes[:100]:  # Limitar a 100 para performance
                dados_detalhes.append({
                    'Combinação': ' - '.join(comb),
                    'Odd Total': f"{ret/projecao.valor_aposta:.2f}",
                    'Probabilidade': f"{prob*100:.2f}%",
                    'Retorno Potencial': f"R$ {ret:.2f}",
                    'ROI Esperado': f"{roi*100:.2f}%",
                    'Lucro Potencial': f"R$ {ret - projecao.valor_aposta:.2f}"
                })
            
            st.dataframe(pd.DataFrame(dados_detalhes), hide_index=True, height=400)
        
        # Botões de exportação
        st.divider()
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("📤 Exportar como CSV"):
                csv = self.exportar_otimizacao('csv')
                st.download_button(
                    label="Baixar CSV",
                    data=csv,
                    file_name="otimizacao_apostas.csv",
                    mime="text/csv"
                )
        with col2:
            if st.button("📊 Exportar como Excel"):
                excel = self.exportar_otimizacao('excel')
                st.download_button(
                    label="Baixar Excel",
                    data=excel,
                    file_name="otimizacao_apostas.xlsx",
                    mime="application/vnd.ms-excel"
                )
        with col3:
            if st.button("🔄 Reotimizar"):
                self.reiniciar_otimizacao()
                st.rerun()

    def calcular_combinacoes(self, num_partidas: int, tipo: TipoMultipla) -> List[Tuple[str, ...]]:
        resultados = ['casa', 'empate', 'fora']
        return list(itertools.product(resultados, repeat=num_partidas))

    def projetar_retornos(self, partidas: List[Dict[str, float]], valor_aposta: float, tipo: TipoMultipla) -> ProjecaoMultipla:
        try:
            combinacoes = self.calcular_combinacoes(len(partidas), tipo)
            retornos = {}
            probabilidades = {}
            roi = {}
            
            for combinacao in combinacoes:
                odd_total = 1.0
                prob_total = 1.0
                
                for i, resultado in enumerate(combinacao):
                    odd = max(1.01, float(partidas[i].get(resultado, 1.01)))
                    odd_total *= odd
                    prob_total *= 1 / odd
                
                retornos[combinacao] = valor_aposta * odd_total
                probabilidades[combinacao] = prob_total
                roi[combinacao] = (retornos[combinacao] * prob_total / valor_aposta) - 1

            return ProjecaoMultipla(
                partidas=partidas,
                valor_aposta=valor_aposta,
                tipo=tipo,
                combinacoes=combinacoes,
                retornos=retornos,
                probabilidades=probabilidades,
                roi=roi
            )

        except Exception as e:
            st.error(f"Erro ao projetar retornos: {e}")
            return ProjecaoMultipla(
                partidas=[],
                valor_aposta=0,
                tipo=tipo,
                combinacoes=[],
                retornos={},
                probabilidades={},
                roi={}
            )
            
    def aplicar_analise_quantica(self, projecao: ProjecaoMultipla) -> ProjecaoMultipla:
        if not self.quantum_processor:
            return projecao

        try:
            quantum_data = {
                'partidas': projecao.partidas,
                'tipo_multa': projecao.tipo.value,
                'valor_aposta': projecao.valor_aposta
            }
            self.quantum_processor.initialize_market_universe(quantum_data)

            for combinacao in projecao.combinacoes:
                prob = self.quantum_processor.get_probabilidade_combinacao(combinacao)
                projecao.retornos[combinacao] *= (1 + prob * 0.5)

        except Exception as e:
            st.warning(f"⚠️ Ajuste quântico não aplicado: {e}")

        return projecao

    def _handle_quantum_error(self, error):
        error_msg = str(error)
        if "float()" in error_msg and "complex" in error_msg:
            st.warning("""
            🔄 Recalibrando parâmetros quânticos...
            O sistema detectou uma inconsistência matemática temporária.
            Todos os cálculos foram resetados para valores padrão seguros.
            """)
            if hasattr(self, 'quantum_processor'):
                self.quantum_processor = None
            return True
        return False
    
    def calcular_probabilidade_implicita(self, odd: float) -> float:
        """Calcula a probabilidade implícita de uma odd"""
        return 1 / odd
    
    def filtrar_por_probabilidade(self, projecao: ProjecaoMultipla, limite_prob: float = 0.01) -> List[Tuple[Tuple[str, ...], float]]:
        """Filtra combinações com probabilidade acima do limite"""
        combinacoes_filtradas = []
        
        for combinacao, retorno in projecao.retornos.items():
            prob = 1.0
            for i, resultado in enumerate(combinacao):
                odd = projecao.partidas[i].get(resultado, 1.01)
                prob *= self.calcular_probabilidade_implicita(odd)
            
            if prob >= limite_prob:
                combinacoes_filtradas.append((combinacao, retorno))
        
        return combinacoes_filtradas
    
    def calcular_roi(self, projecao: ProjecaoMultipla) -> List[Tuple[Tuple[str, ...], float, float, float]]:
        """Calcula o ROI (Return on Investment) para cada combinação"""
        combinacoes_roi = []
        
        for combinacao, retorno in projecao.retornos.items():
            prob = 1.0
            for i, resultado in enumerate(combinacao):
                odd = projecao.partidas[i].get(resultado, 1.01)
                prob *= self.calcular_probabilidade_implicita(odd)
            
            roi = retorno * prob / projecao.valor_aposta
            combinacoes_roi.append((combinacao, retorno, prob, roi))
        
        return sorted(combinacoes_roi, key=lambda x: -x[3])

    def exportar_otimizacao(self, formato: str = 'csv'):
        """Exporta a distribuição otimizada para diferentes formatos"""
        if not self.distribuicao_otimizada:
            return None
        
        dados = []
        for item in self.distribuicao_otimizada:
            dados.append({
                'combinacao': ' - '.join(item['combinacao']),
                'valor_apostado': item['valor_apostado'],
                'retorno_potencial': item['retorno_potencial'],
                'probabilidade': item['probabilidade'],
                'roi_esperado': item['roi_esperado']
            })
        
        df = pd.DataFrame(dados)
        
        if formato == 'csv':
            return df.to_csv(index=False)
        elif formato == 'json':
            return df.to_json(orient='records')
        elif formato == 'excel':
            output = BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df.to_excel(writer, index=False)
            return output.getvalue()
        else:
            return df

    def reiniciar_otimizacao(self):
        """Reseta as otimizações anteriores"""
        self.combinacoes_otimizadas = []
        self.distribuicao_otimizada = []