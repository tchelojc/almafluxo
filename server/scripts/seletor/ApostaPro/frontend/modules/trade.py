import streamlit as st
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
from scipy.stats import entropy
from datetime import datetime, timedelta
import yfinance as yf
import ccxt
from collections import defaultdict

# =============================================================================
# 1. MODELOS DE DADOS PARA MERCADOS FINANCEIROS
# =============================================================================

@dataclass
class Ativo:
    id: str
    nome: str
    tipo: str  # 'acao', 'cripto', 'indice', 'commodity'
    estatisticas: Dict = field(default_factory=lambda: {
        'volatilidade': 0.05,
        'correlacao_dolar': 0.0,
        'correlacao_juros': 0.0,
        'beta': 1.0,
        'retorno_esperado': {
            'alta_1d': 1.85,
            'baixa_1d': 2.05,
            'alta_semana': 2.20,
            'baixa_semana': 1.90,
            'alta_mes': 2.50,
            'baixa_mes': 1.75
        }
    })

@dataclass
class Estrategia:
    """Representa uma estratégia de investimento com todos os atributos necessários."""
    nome: str
    retorno_ajustado: float  # Potencial de retorno ajustado ao risco
    categoria: str  # 'principal' ou 'protecao'
    probabilidade: float = 0.0
    peso_alocacao: float = 0.0
    ativo_id: Optional[str] = None
    ultima_atualizacao: Optional[datetime] = None
    valor_esperado: Optional[float] = None
    correlacoes: Dict[str, float] = field(default_factory=dict)

# =============================================================================
# 2. MOTOR DE ANÁLISE DE MERCADO
# =============================================================================

class MarketEngine:
    """Motor de análise de mercado com padrões macroeconômicos"""
    
    def __init__(self):
        self.correlacoes = self._carregar_correlacoes_padrao()
        self.historico = pd.DataFrame(columns=['ativo', 'retorno', 'timestamp'])
        self.ultima_atualizacao = None
    
    def _carregar_correlacoes_padrao(self) -> Dict[str, float]:
        """Carrega a matriz de correlações padrão entre classes de ativos"""
        return {
            # Relações entre ativos principais
            'dolar_ouro': -0.82,
            'dolar_btc': -0.75,
            'dolar_nasdaq': -0.68,
            'btc_altcoins': 0.92,
            'btc_nasdaq': 0.65,
            'ouro_juros': -0.70,
            
            # Relações macroeconômicas
            'juros_acoes': -0.88,
            'juros_ouro': -0.60,
            'juros_cripto': -0.85,
            'inflacao_ouro': 0.78,
            'inflacao_commodities': 0.85
        }
    
    def atualizar_correlacoes(self, dados_mercado: pd.DataFrame):
        """Atualiza as correlações com dados recentes do mercado"""
        try:
            correl = dados_mercado.corr()
            for par in self.correlacoes:
                ativo1, ativo2 = par.split('_')
                if ativo1 in correl.columns and ativo2 in correl.columns:
                    self.correlacoes[par] = correl.at[ativo1, ativo2]
            self.ultima_atualizacao = datetime.now()
        except Exception as e:
            st.error(f"Erro ao atualizar correlações: {str(e)}")
    
    def determinar_cenario_macro(self) -> str:
        """Identifica o cenário macroeconômico atual"""
        # Implementação simplificada - na prática usaria APIs de dados macro
        return "risk_on"  # ou "risk_off", "aperto_monetario", etc
    
    def calcular_retorno_ajustado(self, ativo: Ativo, cenario: str) -> Dict[str, float]:
        """Calcula retornos esperados ajustados ao cenário atual"""
        stats = ativo.estatisticas
        retornos = stats['retorno_esperado']
        
        if cenario == "risk_on":
            ajuste = {
                'btc': 1.2, 'altcoins': 1.3, 'nasdaq': 1.15,
                'ouro': 0.9, 'dolar': 0.8, 'tesouro': 0.7
            }.get(ativo.tipo, 1.0)
        elif cenario == "risk_off":
            ajuste = {
                'btc': 0.7, 'altcoins': 0.6, 'nasdaq': 0.8,
                'ouro': 1.1, 'dolar': 1.2, 'tesouro': 1.15
            }.get(ativo.tipo, 1.0)
        else:  # cenário neutro
            ajuste = 1.0
        
        return {k: v * ajuste for k, v in retornos.items()}
    
    def gerar_estrategias(self, ativo: Ativo) -> Dict[str, float]:
        """Gera estratégias de investimento para um ativo"""
        cenario = self.determinar_cenario_macro()
        retornos = self.calcular_retorno_ajustado(ativo, cenario)
        
        estrategias = {
            # Estratégias principais
            f"Alta {ativo.nome} (1D)": retornos['alta_1d'],
            f"Alta {ativo.nome} (Semana)": retornos['alta_semana'],
            f"Tendência {ativo.nome}": retornos['alta_mes'] * 0.9,
            
            # Estratégias de proteção
            f"Hedge {ativo.nome}/Dolar": 1.85 if ativo.tipo in ['cripto', 'acao'] else 2.20,
            f"Proteção Volatilidade {ativo.nome}": 2.05,
            f"Stablecoin Yield {ativo.nome}": 1.15
        }
        
        # Adiciona estratégias específicas para cripto
        if ativo.tipo == 'cripto':
            estrategias.update({
                f"BTC Dominance {ativo.nome}": 1.75,
                f"Altcoin Season {ativo.nome}": 2.30
            })
        
        return estrategias

# =============================================================================
# 3. OTIMIZADOR QUÂNTICO PARA PORTFÓLIO
# =============================================================================

class QuantumOptimizer:
    """Otimizador de portfólio com estratégias quânticas"""
    
    def __init__(self, market_engine: MarketEngine):
        self.engine = market_engine
    
    def calcular_valor_esperado(self, probabilidade: float, retorno: float) -> float:
        """Calcula o valor esperado de uma estratégia"""
        return (probabilidade * (retorno - 1)) - (1 - probabilidade)
    
    def calcular_risco_portfolio(self, estrategias: List[Estrategia]) -> float:
        """Calcula o risco do portfólio considerando correlações"""
        if not estrategias:
            return 0.0

        try:
            prob = np.array([e.probabilidade for e in estrategias])
            retornos = np.array([e.retorno_ajustado for e in estrategias])
            
            # Matriz de correlações
            correl_matrix = np.ones((len(estrategias), len(estrategias)))
            for i, e1 in enumerate(estrategias):
                for j, e2 in enumerate(estrategias):
                    if i != j:
                        key = f"{e1.nome.split(' ')[0]}_{e2.nome.split(' ')[0]}".lower()
                        correl_matrix[i,j] = self.engine.correlacoes.get(key, 0)
            
            # Cálculo de risco com covariância
            cov_matrix = np.outer(retornos, retornos) * correl_matrix
            risco = np.sqrt(np.dot(prob.T, np.dot(cov_matrix, prob)))
            
            return min(1.0, max(0.0, risco))
        except:
            return 0.5
    
    def otimizar_portfolio(self, estrategias: List[Estrategia], perfil_risco: str) -> List[Estrategia]:
        """Otimiza a alocação do portfólio"""
        if not estrategias:
            return []

        # 1. Calcula probabilidades e valores esperados
        for e in estrategias:
            e.probabilidade = 1 / e.retorno_ajustado
            e.valor_esperado = self.calcular_valor_esperado(e.probabilidade, e.retorno_ajustado)

        # 2. Fatores de perfil de risco
        fatores = {
            'Conservador': {'exposicao_max': 0.5, 'protecao_min': 0.3, 'fator_risco': 0.7},
            'Moderado': {'exposicao_max': 0.7, 'protecao_min': 0.2, 'fator_risco': 1.0},
            'Agressivo': {'exposicao_max': 0.9, 'protecao_min': 0.1, 'fator_risco': 1.3}
        }.get(perfil_risco, 'Moderado')

        # 3. Cálculo dos pesos com correlações
        prob_array = np.array([e.probabilidade for e in estrategias])
        ve_array = np.array([max(0, e.valor_esperado) for e in estrategias])
        
        # Ajuste por correlação
        correl_factors = np.ones(len(estrategias))
        for i, e in enumerate(estrategias):
            if 'proteção' in e.nome.lower() or 'hedge' in e.nome.lower():
                correl_factors[i] = 0.8
        
        pesos = prob_array * (1 + ve_array * fatores['fator_risco']) * correl_factors
        pesos = pesos / pesos.sum()

        # 4. Aplicação dos pesos com limites
        for i, e in enumerate(estrategias):
            peso_bruto = pesos[i]
            if e.categoria == 'protecao':
                e.peso_alocacao = max(fatores['protecao_min'], min(0.5, peso_bruto))
            else:
                e.peso_alocacao = min(fatores['exposicao_max'], max(0.05, peso_bruto))

        # 5. Normalização final
        total = sum(e.peso_alocacao for e in estrategias)
        if total > 0:
            for e in estrategias:
                e.peso_alocacao = e.peso_alocacao / total

        return estrategias

# =============================================================================
# 4. INTERFACE DO USUÁRIO
# =============================================================================

class TradingInterface:
    """Interface completa para operação em bolsas e criptomoedas"""
    
    def __init__(self, license_manager=None):  # Adicionado parâmetro opcional
        self.market_engine = MarketEngine()
        self.optimizer = QuantumOptimizer(self.market_engine)
        self.ativos = []
        self.estrategias = []
        self._carregar_ativos_padrao()
        self.license_manager = license_manager  # Armazena o gerenciador de licença
    
    def _carregar_ativos_padrao(self):
        """Carrega ativos padrão com estatísticas realistas"""
        self.ativos = [
            Ativo(
                id="btc",
                nome="BTC/USD",
                tipo="cripto",
                estatisticas={
                    'volatilidade': 0.08,
                    'correlacao_dolar': -0.75,
                    'correlacao_juros': -0.85,
                    'beta': 1.8,
                    'retorno_esperado': {
                        'alta_1d': 1.85, 'baixa_1d': 2.05,
                        'alta_semana': 2.20, 'baixa_semana': 1.90,
                        'alta_mes': 2.50, 'baixa_mes': 1.75
                    }
                }
            ),
            Ativo(
                id="nasdaq",
                nome="NASDAQ",
                tipo="indice",
                estatisticas={
                    'volatilidade': 0.05,
                    'correlacao_dolar': -0.65,
                    'correlacao_juros': -0.90,
                    'beta': 1.0,
                    'retorno_esperado': {
                        'alta_1d': 1.75, 'baixa_1d': 2.15,
                        'alta_semana': 2.00, 'baixa_semana': 1.85,
                        'alta_mes': 2.30, 'baixa_mes': 1.65
                    }
                }
            ),
            Ativo(
                id="ouro",
                nome="Ouro",
                tipo="commodity",
                estatisticas={
                    'volatilidade': 0.03,
                    'correlacao_dolar': -0.82,
                    'correlacao_juros': -0.70,
                    'beta': 0.5,
                    'retorno_esperado': {
                        'alta_1d': 1.65, 'baixa_1d': 2.25,
                        'alta_semana': 1.85, 'baixa_semana': 2.00,
                        'alta_mes': 2.10, 'baixa_mes': 1.90
                    }
                }
            )
        ]
    
    def mostrar_interface(self):
        """Renderiza a interface principal"""
        # Verificação de licença
        if hasattr(self, 'license_manager') and self.license_manager:
            if not self.license_manager.verify():
                st.error("Licença inválida")
                st.stop()
    
        st.title("⚡ Quantum Trading Pro")  # Removido set_page_config daqui
        st.caption("Sistema Inteligente para Operação em Bolsas e Criptomoedas")
    
        with st.sidebar:
            self._construir_sidebar()
    
        tab1, tab2, tab3 = st.tabs(["📊 Configurar Portfólio", "📈 Análise de Mercado", "🛡️ Gerenciar Riscos"])
    
        with tab1:
            self._construir_aba_portfolio()
    
        with tab2:
            self._construir_aba_analise()
    
        with tab3:
            self._construir_aba_riscos()
    
    def _construir_sidebar(self):
        """Constroi a barra lateral com configurações"""
        st.sidebar.header("⚙️ Configurações Globais")
        
        # Perfil de risco
        st.session_state.perfil_risco = st.sidebar.selectbox(
            "Perfil de Risco",
            ["Conservador", "Moderado", "Agressivo"],
            index=1
        )
        
        # Capital disponível
        st.session_state.capital = st.sidebar.number_input(
            "Capital Total (R$)",
            min_value=1000.0,
            value=10000.0,
            step=1000.0,
            format="%.2f"
        )
        
        # Atualização de dados
        if st.sidebar.button("🔄 Atualizar Dados de Mercado"):
            with st.spinner("Obtendo dados atualizados..."):
                self._atualizar_dados_mercado()
                st.success("Dados atualizados com sucesso!")
    
    def _atualizar_dados_mercado(self):
        """Simula a atualização de dados de mercado"""
        # Na prática, integraria com APIs como Yahoo Finance, CCXT, etc
        self.market_engine.ultima_atualizacao = datetime.now()
    
    def _construir_aba_portfolio(self):
        """Interface para configuração do portfólio"""
        st.header("📊 Configurar Portfólio")
        
        # Seleção de ativos
        st.subheader("📈 Selecionar Ativos")
        ativos_selecionados = st.multiselect(
            "Escolha os ativos para operar:",
            options=[a.nome for a in self.ativos],
            default=["BTC/USD", "NASDAQ"]
        )
        
        if not ativos_selecionados:
            st.warning("Selecione pelo menos um ativo")
            return
        
        # Gerar estratégias para os ativos selecionados
        estrategias = []
        for ativo_nome in ativos_selecionados:
            ativo = next(a for a in self.ativos if a.nome == ativo_nome)
            estrategias_geradas = self.market_engine.gerar_estrategias(ativo)
            
            for nome, retorno in estrategias_geradas.items():
                categoria = 'protecao' if 'proteção' in nome.lower() or 'hedge' in nome.lower() else 'principal'
                estrategias.append(Estrategia(
                    nome=nome,
                    retorno_ajustado=retorno,
                    categoria=categoria,
                    ativo_id=ativo.id
                ))
        
        # Seleção de estratégias
        st.subheader("🎯 Selecionar Estratégias")
        estrategias_principais = [e for e in estrategias if e.categoria == 'principal']
        estrategias_protecao = [e for e in estrategias if e.categoria == 'protecao']
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 📈 Estratégias Principais")
            for e in estrategias_principais:
                selecionado = st.checkbox(
                    f"{e.nome} (Retorno: {e.retorno_ajustado:.2f}x)", 
                    value=True,
                    key=f"principal_{e.nome}"
                )
                if not selecionado:
                    estrategias.remove(e)
        
        with col2:
            st.markdown("#### 🛡️ Estratégias de Proteção")
            for e in estrategias_protecao:
                selecionado = st.checkbox(
                    f"{e.nome} (Retorno: {e.retorno_ajustado:.2f}x)", 
                    value=True,
                    key=f"protecao_{e.nome}"
                )
                if not selecionado:
                    estrategias.remove(e)
        
        # Otimização do portfólio
        if st.button("⚡ Otimizar Portfólio", type="primary"):
            with st.spinner("Calculando alocação ideal..."):
                estrategias_otimizadas = self.optimizer.otimizar_portfolio(
                    estrategias,
                    st.session_state.perfil_risco
                )
                self._mostrar_resultados_otimizacao(estrategias_otimizadas)
    
    def _mostrar_resultados_otimizacao(self, estrategias: List[Estrategia]):
        """Exibe os resultados da otimização"""
        if not estrategias:
            st.error("Nenhuma estratégia selecionada")
            return
        
        capital = st.session_state.capital
        
        # Preparar dados para exibição
        dados = []
        for e in estrategias:
            investimento = e.peso_alocacao * capital
            retorno = investimento * e.retorno_ajustado
            dados.append({
                "Estratégia": e.nome,
                "Ativo": next(a.nome for a in self.ativos if a.id == e.ativo_id),
                "Tipo": e.categoria.capitalize(),
                "Retorno Ajustado": e.retorno_ajustado,
                "Probabilidade": f"{1/e.retorno_ajustado:.1%}",
                "Alocação (%)": e.peso_alocacao * 100,
                "Investimento (R$)": investimento,
                "Retorno Potencial (R$)": retorno
            })
        
        df = pd.DataFrame(dados)
        
        # Gráfico de alocação
        st.subheader("📊 Alocação de Capital")
        fig = px.pie(
            df,
            names='Estratégia',
            values='Alocação (%)',
            color='Tipo',
            color_discrete_map={'Principal': '#3498db', 'Protecao': '#e74c3c'},
            hole=0.4
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Tabela detalhada
        st.subheader("📋 Detalhes das Estratégias")
        st.dataframe(
            df.sort_values('Alocação (%)', ascending=False),
            column_config={
                "Alocação (%)": st.column_config.NumberColumn(format="%.2f%%"),
                "Investimento (R$)": st.column_config.NumberColumn(format="R$ %.2f"),
                "Retorno Potencial (R$)": st.column_config.NumberColumn(format="R$ %.2f"),
                "Retorno Ajustado": st.column_config.NumberColumn(format="%.2fx")
            },
            hide_index=True,
            use_container_width=True
        )
        
        # Resumo financeiro
        st.subheader("💰 Resumo Financeiro")
        total_investido = df['Investimento (R$)'].sum()
        retorno_total = df['Retorno Potencial (R$)'].sum()
        lucro_esperado = retorno_total - total_investido
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Investido", f"R$ {total_investido:,.2f}")
        col2.metric("Retorno Esperado", f"R$ {retorno_total:,.2f}")
        col3.metric("Lucro Esperado", f"R$ {lucro_esperado:,.2f}", 
                   f"{(lucro_esperado/total_investido*100):.1f}%" if total_investido > 0 else "0%")
    
    def _construir_aba_analise(self):
        """Interface para análise de mercado"""
        st.header("📈 Análise de Mercado")
        
        # Correlações entre ativos
        st.subheader("🔗 Correlações entre Ativos")
        correl_data = []
        for par, valor in self.market_engine.correlacoes.items():
            ativo1, ativo2 = par.split('_')
            correl_data.append({
                "Ativo 1": ativo1.upper(),
                "Ativo 2": ativo2.upper(),
                "Correlação": valor,
                "Tipo": "Positiva" if valor > 0 else "Negativa"
            })
        
        df_correl = pd.DataFrame(correl_data)
        if not df_correl.empty:
            fig = px.bar(
                df_correl,
                x="Ativo 1",
                y="Correlação",
                color="Ativo 2",
                barmode="group",
                title="Correlações entre Ativos"
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Padrões cíclicos
        st.subheader("🔄 Padrões Cíclicos do Mercado")
        
        ciclos = {
            "Risk-On (Liquidez Alta)": ["BTC", "ALTCOINS", "NASDAQ", "Commodities"],
            "Risk-Off (Aversão a Risco)": ["DOLAR", "OURO", "TESOURO"],
            "Inflação Alta": ["OURO", "COMMODITIES", "BTC"],
            "Juros Altos": ["DOLAR", "TESOURO"]
        }
        
        for ciclo, ativos in ciclos.items():
            with st.expander(f"📌 {ciclo}", expanded=False):
                st.markdown(f"**Ativos que se beneficiam:** {', '.join(ativos)}")
                st.markdown("**Estratégias recomendadas:**")
                if ciclo == "Risk-On":
                    st.markdown("- Long em criptomoedas e tech")
                    st.markdown("- Alavancagem moderada")
                elif ciclo == "Risk-Off":
                    st.markdown("- Hedge com ouro e dólar")
                    st.markdown("- Posições defensivas")
        
        # Dados históricos
        st.subheader("📅 Comportamento Histórico")
        periodo = st.selectbox("Período", ["1M", "3M", "6M", "1A"], index=2)
        
        # Simulação de dados históricos
        dates = pd.date_range(end=datetime.now(), periods=30)
        dados_historicos = pd.DataFrame({
            "Data": dates,
            "BTC": np.cumsum(np.random.normal(0.5, 2, 30)),
            "NASDAQ": np.cumsum(np.random.normal(0.3, 1.5, 30)),
            "DOLAR": np.cumsum(np.random.normal(-0.1, 0.8, 30)),
            "OURO": np.cumsum(np.random.normal(0.2, 1.2, 30))
        }).set_index("Data")
        
        fig = px.line(
            dados_historicos,
            title="Desempenho Histórico dos Principais Ativos",
            labels={"value": "Retorno (%)", "variable": "Ativo"}
        )
        st.plotly_chart(fig, use_container_width=True)
    
    def _construir_aba_riscos(self):
        """Interface para gerenciamento de riscos"""
        st.header("🛡️ Gerenciamento de Riscos")
        
        # Radar de correlações dinâmico
        st.subheader("📡 Radar de Correlação Dinâmica")
        
        col1, col2 = st.columns(2)
        with col1:
            ativo_base = st.selectbox(
                "Ativo Base para Correlação",
                ["BTC", "NASDAQ", "DOLAR", "OURO"],
                index=0
            )
        
        with col2:
            periodo_correl = st.selectbox(
                "Período de Análise",
                ["1D", "1W", "1M", "3M"],
                index=2
            )
        
        # Simulação de dados de correlação
        correl_data = {
            "BTC": {"DOLAR": -0.75, "NASDAQ": 0.65, "OURO": 0.45},
            "NASDAQ": {"DOLAR": -0.68, "BTC": 0.65, "OURO": 0.30},
            "DOLAR": {"BTC": -0.75, "NASDAQ": -0.68, "OURO": -0.82},
            "OURO": {"BTC": 0.45, "NASDAQ": 0.30, "DOLAR": -0.82}
        }
        
        df_correl = pd.DataFrame(correl_data[ativo_base].items(), columns=["Ativo", "Correlação"])
        
        fig = px.bar_polar(
            df_correl,
            r="Correlação",
            theta="Ativo",
            color="Correlação",
            template="plotly_dark",
            color_continuous_scale=px.colors.diverging.RdYlGn,
            title=f"Correlações com {ativo_base}"
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Alertas de risco
        st.subheader("⚠️ Alertas de Risco Atuais")
        
        riscos = {
            "BTC": "Dominância em alta pode indicar rotação para risco",
            "DOLAR": "Forte correlação inversa com ativos de risco",
            "NASDAQ": "Sensível a mudanças nas taxas de juros",
            "OURO": "Proteção contra inflação, mas sensível ao dólar"
        }
        
        for ativo, alerta in riscos.items():
            with st.container(border=True):
                cols = st.columns([1, 4])
                cols[0].metric(ativo, "")
                cols[1].write(f"**Alerta:** {alerta}")
        
        # Estratégias de proteção
        st.subheader("🛡️ Estratégias de Proteção Recomendadas")
        
        estrategias_protecao = [
            {"nome": "Hedge BTC/DOLAR", "descricao": "Proteção contra queda do BTC com posição em dólar"},
            {"nome": "Opções PUT NASDAQ", "descricao": "Proteção contra queda do mercado acionário"},
            {"nome": "Alocação em Stablecoins", "descricao": "Reduzir exposição em momentos de alta volatilidade"},
            {"nome": "Ouro vs Dólar", "descricao": "Proteção contra inflação e queda do dólar"}
        ]
        
        for estrategia in estrategias_protecao:
            with st.expander(f"🔒 {estrategia['nome']}", expanded=False):
                st.markdown(estrategia['descricao'])
                if st.button("Adicionar ao Portfólio", key=f"add_{estrategia['nome']}"):
                    st.success(f"Estratégia {estrategia['nome']} adicionada!")
