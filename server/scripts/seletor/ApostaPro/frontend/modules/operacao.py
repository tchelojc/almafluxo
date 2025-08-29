import streamlit as st
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
from scipy.stats import entropy
from datetime import datetime
from streamlit_tags import st_tags

# =============================================================================
# 1. MODELOS DE DADOS (ESTRUTURA PRINCIPAL)
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
        'odds_referencia': {
            'alta_1d': 1.85,
            'baixa_1d': 2.05,
            'alta_semana': 2.20,
            'baixa_semana': 1.90,
            'alta_mes': 2.50,
            'baixa_mes': 1.75
        }
    })

@dataclass
class Mercado:
    """Representa um mercado de investimento com todos os atributos necessários."""
    nome: str
    odd: float  # Aqui "odd" representa o potencial de retorno ajustado ao risco
    categoria: str  # 'principal' ou 'protecao'
    probabilidade: float = 0.0
    peso_alocacao: float = 0.0
    ativo_id: Optional[str] = None
    ultima_atualizacao: Optional[datetime] = None
    valor_esperado: Optional[float] = None

# =============================================================================
# 2. MOTOR QUÂNTICO (CÁLCULOS E OTIMIZAÇÃO) - ADAPTADO PARA MERCADOS FINANCEIROS
# =============================================================================

class QuantumEngine:
    """Motor de otimização quântica avançado para mercados financeiros."""
    
    def __init__(self):
        self.correlacoes = self._carregar_correlacoes()
        self.historico = pd.DataFrame(columns=['mercado', 'odd', 'timestamp'])
    
    def _carregar_correlacoes(self) -> Dict[str, float]:
        """Carrega a matriz de correlações entre diferentes classes de ativos."""
        return {
            'acao_cripto': 0.65,
            'dolar_ouro': -0.82,
            'dolar_cripto': -0.75,
            'juros_acoes': -0.88,
            'cripto_altcoins': 0.92,
            'petroleo_dolar': -0.68
        }
    
    def _calcular_odds_dinamicas(self, ativo: Ativo) -> Dict[str, float]:
        stats = ativo.estatisticas
        odds_ref = stats['odds_referencia']
        
        # Probabilidades baseadas nas odds de referência
        prob_alta_1d = 1 / odds_ref['alta_1d']
        prob_baixa_1d = 1 / odds_ref['baixa_1d']
        
        # Mercados principais com odds reais
        odds = {
            # Mercados de curto prazo
            "Alta 1 Dia": odds_ref['alta_1d'],
            "Baixa 1 Dia": odds_ref['baixa_1d'],
            
            # Mercados por prazo
            "Alta Semana": odds_ref['alta_semana'],
            "Baixa Semana": odds_ref['baixa_semana'],
            "Alta Mês": odds_ref['alta_mes'],
            "Baixa Mês": odds_ref['baixa_mes'],
            
            # Proteções
            "Proteção Dolar": 1.85 if ativo.tipo in ['acao', 'cripto'] else 2.20,
            "Proteção Juros": 2.05 if ativo.tipo in ['acao', 'cripto'] else 1.75,
            
            # Hedge entre ativos
            f"Hedge {ativo.nome} x Dolar": 1.95,
            f"Hedge {ativo.nome} x Ouro": 2.15
        }
        
        return odds
    
    def _calcular_prob_alta(self, stats: Dict) -> float:
        """Calcula probabilidade para movimentos de alta com base em múltiplos fatores."""
        volatilidade = stats.get('volatilidade', 0.05)
        correlacao_dolar = stats.get('correlacao_dolar', 0.0)
        
        # Fórmula base ajustada por volatilidade e correlação com dólar
        prob_base = 0.5 + (0.3 - volatilidade) - (correlacao_dolar * 0.2)
        
        # Limites mínimos e máximos para probabilidade
        return min(0.85, max(0.15, prob_base))
    
    def calcular_valor_esperado(self, probabilidade: float, odd: float) -> float:
        """Calcula o valor esperado de um investimento."""
        return (probabilidade * (odd - 1)) - (1 - probabilidade)
    
    def calcular_risco_portfolio(self, mercados: List[Mercado]) -> float:
        """
        Calcula um índice de risco normalizado entre 0 e 1 para o portfólio
        """
        if not mercados:
            return 0.0

        try:
            prob = np.array([m.probabilidade for m in mercados if hasattr(m, 'probabilidade')])
            odds = np.array([m.odd for m in mercados if hasattr(m, 'odd')])

            # Fatores de risco
            vol = np.std(odds) if len(odds) > 1 else 0  # Volatilidade
            ent = entropy(prob) if len(prob) > 1 else 0  # Entropia
            equilibrio = 1 - np.sum(prob**2)  # Equilíbrio

            # Cálculo do risco bruto com limites
            risco_bruto = min(100, max(0, vol * ent * equilibrio))
        
            # Normalização sigmoide para garantir [0, 1]
            risco_normalizado = 1 / (1 + np.exp(-risco_bruto))
        
            return min(1.0, max(0.0, risco_normalizado))
        except:
            return 0.5  # Valor padrão seguro
    
    def _distribuicao_quantica(self, prob: np.ndarray, odds: np.ndarray, fases: np.ndarray) -> np.ndarray:
        """
        Algoritmo de projeção quântica para otimização de pesos que considera:
        - Probabilidades ajustadas
        - Potencial de retorno
        - Fases de interferência (para mercados correlacionados)
        """
        amplitudes = np.sqrt(prob) * np.exp(1j * fases)
        vetor_retorno = np.real(amplitudes * (odds - 1))
        norma = np.linalg.norm(vetor_retorno)
        
        if norma == 0:
            return prob / prob.sum() if prob.sum() > 0 else np.zeros_like(prob)
        
        pesos = (vetor_retorno / norma) ** 2
        return pesos / pesos.sum() if pesos.sum() > 0 else np.zeros_like(pesos)
    
    def otimizar_portfolio(self, mercados: List[Mercado], perfil_risco: str) -> List[Mercado]:
        """
        Executa o processo completo de otimização do portfólio de investimentos:
        1. Calcula probabilidades implícitas dos retornos
        2. Ajusta por valor esperado e correlações
        3. Distribui proporcionalmente conforme perfil de risco
        """
        if not mercados:
            return []

        # 1. Cálculo das probabilidades implícitas e valores esperados
        for m in mercados:
            m.probabilidade = 1 / m.odd
            m.valor_esperado = self.calcular_valor_esperado(m.probabilidade, m.odd)

        # 2. Fatores de ajuste por perfil de risco
        fatores_perfil = {
            'Conservador': {
                'exposicao_max': 0.5,  # Máximo alocado em um único mercado
                'protecao_min': 0.3,   # Mínimo em mercados de proteção
                'fator_risco': 0.7     # Fator de redução de risco
            },
            'Moderado': {
                'exposicao_max': 0.7,
                'protecao_min': 0.2,
                'fator_risco': 1.0
            },
            'Agressivo': {
                'exposicao_max': 0.9,
                'protecao_min': 0.1,
                'fator_risco': 1.3
            }
        }
        fatores = fatores_perfil.get(perfil_risco, fatores_perfil['Moderado'])

        # 3. Cálculo dos pesos baseado em:
        #    - Probabilidade implícita
        #    - Valor esperado
        #    - Correlações entre mercados
        prob_array = np.array([m.probabilidade for m in mercados])
        ve_array = np.array([max(0, m.valor_esperado) for m in mercados])  # Considera apenas VE positivo
    
        # Ajuste por correlação (reduz peso em mercados altamente correlacionados)
        correl_factors = np.ones(len(mercados))
        for i, m in enumerate(mercados):
            if any(x in m.nome.lower() for x in ['proteção', 'hedge']):
                correl_factors[i] = 0.8  # Redução de 20% para mercados correlacionados
    
        # Cálculo dos pesos brutos
        pesos = prob_array * (1 + ve_array * fatores['fator_risco']) * correl_factors
    
        # Normalização
        pesos = pesos / pesos.sum()

        # 4. Aplicação dos pesos com limites por perfil
        for i, m in enumerate(mercados):
            peso_bruto = pesos[i]
        
            # Ajuste por categoria (proteção ou principal)
            if m.categoria == 'protecao':
                m.peso_alocacao = max(fatores['protecao_min'], min(0.5, peso_bruto))
            else:
                m.peso_alocacao = min(fatores['exposicao_max'], max(0.05, peso_bruto))

        # 5. Rebalanceamento final para garantir soma = 1
        total = sum(m.peso_alocacao for m in mercados)
        if total > 0:
            for m in mercados:
                m.peso_alocacao = m.peso_alocacao / total

        return mercados

# =============================================================================
# 3. INTERFACE DO USUÁRIO (STREAMLIT) - ADAPTADA PARA MERCADOS FINANCEIROS
# =============================================================================

class QuantumInterface:
    """Sistema completo de gestão quântica de investimentos"""
    
    def __init__(self, license_manager=None):  # Adicionado parâmetro opcional
        self.engine = QuantumEngine()
        self.mercados = []
        self._carregar_mercados_padrao()
        self.license_manager = license_manager  # Armazena o gerenciador de licença
    
    def _inicializar_estado(self):
        """Inicializa todos os estados necessários na sessão."""
        if 'ativo_selecionado' not in st.session_state:
            st.session_state.ativo_selecionado = None
        if 'mercados_selecionados' not in st.session_state:
            st.session_state.mercados_selecionados = []
        if 'odds_dinamicas' not in st.session_state:
            st.session_state.odds_dinamicas = {}
        if 'relatorio' not in st.session_state:
            st.session_state.relatorio = {
                "risco": 0.0,
                "dataframe": pd.DataFrame(),
                "grafico_alocacao": go.Figure(),
                "analise_correlacao": None,
                "recomendacoes": []
            }
        if 'perfil_risco' not in st.session_state:
            st.session_state.perfil_risco = "Moderado"
        if 'capital' not in st.session_state:
            st.session_state.capital = 10000.0
        if 'modo_entrada' not in st.session_state:
            st.session_state.modo_entrada = "Manual"
    
    def mostrar_interface(self):
        """Renderiza a interface principal"""
        # Verificação de licença
        if hasattr(self, 'license_manager') and self.license_manager:
            if not self.license_manager.verify():
                st.error("Licença inválida")
                st.stop()
    
        self._inicializar_estado()
    
        st.title("⚡ Quantum Finance Pro")
        st.caption("Sistema Inteligente de Otimização de Portfólio para Ações e Criptomoedas")
    
        with st.sidebar:
            self._construir_sidebar()
    
        tab1, tab2, tab3 = st.tabs(["🎯 Configurar", "📊 Análise", "💾 Histórico"])
    
        with tab1:
            self._construir_aba_configuracao()
    
        with tab2:
            self._construir_aba_analise()
    
        with tab3:
            self._construir_aba_historico()
            
    def mostrar_ajuda(self):
        """Exibe um guia completo de como usar o sistema."""
        with st.expander("❓ Guia Completo - Como Usar", expanded=False):
            st.markdown("""
            ## 📚 Guia do Quantum Finance Pro
        
            ### 🔍 Configurando seu Ativo
            1. **Tipo de Ativo**: Escolha entre ações, criptomoedas, índices ou commodities
            2. **Estatísticas**:
               - Volatilidade: Medida de risco do ativo (ex: 0.05 para 5%)
               - Correlação Dolar: Como o ativo se move em relação ao dólar (-1 a 1)
               - Beta: Sensibilidade ao mercado (1 = mercado, >1 = mais volátil)
            
            ### 📊 Mercados de Investimento
            - **Principais**: Mercados com maior potencial de retorno (Alta 1D, Alta Semana)
            - **Proteção**: Mercados para hedge (Proteção Dolar, Hedge)
            - **Personalizados**: Adicione estratégias específicas com retornos manuais
        
            ### ⚡ Otimização Quântica
            O sistema calcula:
            - Valor esperado de cada estratégia
            - Correlações entre ativos
            - Distribuição ideal do capital
            - Nível de risco do portfólio
        
            ### 💡 Dicas Profissionais
            - Diversifique entre 3-5 ativos principais
            - Use 1-2 estratégias de proteção
            - Ajuste o perfil de risco conforme o cenário macro
            - Monitore correlações entre ativos
            """)
            
    def _carregar_mercados_padrao(self):
        """Carrega templates de mercados com retornos sugeridos"""
        self.mercados_principais = {
            "Alta 1 Dia": 1.85,
            "Alta Semana": 2.20,
            "Alta Mês": 2.50,
            "BTC Dominance Aumenta": 1.75,
            "ETH/BTC Ratio Aumenta": 1.90
        }

        self.mercados_protecao = {
            "Baixa 1 Dia": 2.05,
            "Proteção Dolar": 1.85,
            "Proteção Juros": 2.10,
            "Hedge Ouro": 2.25,
            "Stablecoin Yield": 1.65
        }
    
        from datetime import datetime

        self.mercados = []

        # Adiciona mercados principais
        for nome, odd in self.mercados_principais.items():
            mercado = Mercado(
                nome=nome,
                odd=odd,
                categoria='principal',
                probabilidade=0.5,
                ultima_atualizacao=datetime.now()
            )
            self.mercados.append(mercado)

        # Adiciona mercados de proteção
        for nome, odd in self.mercados_protecao.items():
            mercado = Mercado(
                nome=nome,
                odd=odd,
                categoria='protecao',
                probabilidade=0.5,
                ultima_atualizacao=datetime.now()
            )
            self.mercados.append(mercado)

    def _construir_sidebar(self):
        """Constroi a barra lateral com configurações globais."""
        st.header("⚙️ Configurações Globais")
    
        if st.button("❓ Guia Rápido", help="Clique para ver instruções de uso"):
            self.mostrar_ajuda()
    
        with st.expander("🔍 Sobre Perfis de Risco", expanded=False):
            st.markdown("""
            - **Conservador**: Maior proteção, menor exposição
            - **Moderado**: Equilíbrio entre risco e retorno
            - **Agressivo**: Maior potencial de ganho, mais risco
            """)
    
        st.session_state.perfil_risco = st.selectbox(
            "Perfil de Risco",
            ["Conservador", "Moderado", "Agressivo"],
            index=1
        )
    
        st.session_state.capital = st.number_input(
            "Capital Total (R$)",
            min_value=1000.0,
            value=10000.0,
            step=1000.0,
            format="%.2f",
            help="Valor total disponível para investimento"
        )
    
        with st.expander("💾 Gerenciar Perfis", expanded=False):
            st.info("Salve suas configurações favoritas para uso futuro")
            perfil_nome = st.text_input("Nome do Perfil")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Salvar Configuração"):
                    self._salvar_perfil(perfil_nome)
            with col2:
                if st.button("Carregar Configuração"):
                    self._carregar_perfil(perfil_nome)

    def _selecionar_ativo(self):
        """Componente para seleção ou entrada manual do ativo."""
        st.subheader("📈 Configurar Ativo")
        with st.expander("ℹ️ Como configurar", expanded=False):
            st.markdown("""
            **Para melhores resultados:**
            1. Use dados históricos reais quando possível
            2. Considere o cenário macroeconômico atual
            3. Analise correlações com outros ativos
            """)

        st.session_state.modo_entrada = st.radio(
            "Modo de Entrada:",
            ["Manual", "Exemplos Prontos"],
            horizontal=True
        )

        if st.session_state.modo_entrada == "Manual":
            # Entrada manual dos dados do ativo
            col1, col2 = st.columns(2)
            with col1:
                nome = st.text_input("Nome do Ativo", value="")
            with col2:
                tipo = st.selectbox("Tipo", ["Ação", "Criptomoeda", "Índice", "Commodity"])

            # Seção de Retornos de Referência
            st.subheader("📊 Retornos de Referência (Obrigatórios)")
        
            col_odd1, col_odd2, col_odd3, col_odd4 = st.columns(4)
            with col_odd1:
                odd_alta_1d = st.number_input("Alta 1 Dia", min_value=1.01, value=1.85, step=0.01,
                                           help="Retorno ajustado para alta em 1 dia")
            with col_odd2:
                odd_baixa_1d = st.number_input("Baixa 1 Dia", min_value=1.01, value=2.05, step=0.01,
                                            help="Retorno ajustado para baixa em 1 dia")
            with col_odd3:
                odd_alta_semana = st.number_input("Alta Semana", min_value=1.01, value=2.20, step=0.01,
                                               help="Retorno ajustado para alta em 1 semana")
            with col_odd4:
                odd_baixa_semana = st.number_input("Baixa Semana", min_value=1.01, value=1.90, step=0.01,
                                                help="Retorno ajustado para baixa em 1 semana")

            col_odd5, col_odd6 = st.columns(2)
            with col_odd5:
                odd_alta_mes = st.number_input("Alta Mês", min_value=1.01, value=2.50, step=0.01,
                                            help="Retorno ajustado para alta em 1 mês")
            with col_odd6:
                odd_baixa_mes = st.number_input("Baixa Mês", min_value=1.01, value=1.75, step=0.01,
                                             help="Retorno ajustado para baixa em 1 mês")

            # Seção de Estatísticas
            st.subheader("📈 Estatísticas do Ativo")
            col1, col2, col3 = st.columns(3)
            with col1:
                volatilidade = st.number_input("Volatilidade (%)", min_value=0.0, max_value=100.0, value=5.0, step=0.1,
                                           help="Volatilidade histórica anualizada")
                correlacao_dolar = st.number_input("Correlação Dolar", min_value=-1.0, max_value=1.0, value=0.0, step=0.05,
                                                help="Correlação com movimento do dólar (-1 a 1)")
            with col2:
                correlacao_juros = st.number_input("Correlação Juros", min_value=-1.0, max_value=1.0, value=0.0, step=0.05,
                                                help="Correlação com taxa de juros (-1 a 1)")
                beta = st.number_input("Beta", min_value=0.0, value=1.0, step=0.1,
                                    help="Sensibilidade ao mercado (1 = mercado)")
            with col3:
                sharpe = st.number_input("Índice Sharpe", min_value=-5.0, max_value=5.0, value=1.0, step=0.1,
                                      help="Retorno ajustado ao risco")

            # Botão para criar o ativo
            if st.button("🔍 Criar Ativo e Calcular Retornos"):
                if not nome:
                    st.error("❌ Por favor, insira o nome do ativo")
                elif any(odd <= 1.0 for odd in [odd_alta_1d, odd_baixa_1d, odd_alta_semana, odd_baixa_semana, odd_alta_mes, odd_baixa_mes]):
                    st.error("❌ Todos os retornos devem ser maiores que 1.00")
                else:
                    ativo = Ativo(
                        id=str(datetime.now().timestamp()),
                        nome=nome,
                        tipo=tipo.lower(),
                        estatisticas={
                            'volatilidade': volatilidade / 100,
                            'correlacao_dolar': correlacao_dolar,
                            'correlacao_juros': correlacao_juros,
                            'beta': beta,
                            'sharpe': sharpe,
                            'odds_referencia': {
                                'alta_1d': odd_alta_1d,
                                'baixa_1d': odd_baixa_1d,
                                'alta_semana': odd_alta_semana,
                                'baixa_semana': odd_baixa_semana,
                                'alta_mes': odd_alta_mes,
                                'baixa_mes': odd_baixa_mes
                            }
                        }
                    )

                    # Atualiza estado da sessão
                    st.session_state.ativo_selecionado = ativo
                    st.session_state.odds_dinamicas = self.engine._calcular_odds_dinamicas(ativo)
                    st.session_state.mercados_selecionados = []

                    st.toast(f"✅ Ativo criado: {nome} ({tipo})")

    def _construir_aba_configuracao(self):
        """Interface para configuração da estratégia de investimento."""
        st.header("🎯 Configurar Estratégia")
        
        self._selecionar_ativo()
        
        if st.session_state.ativo_selecionado is None:
            st.info("Configure um ativo para começar")
            return
        
        ativo = st.session_state.ativo_selecionado
        st.success(f"Ativo configurado: {ativo.nome} ({ativo.tipo.capitalize()})")
        
        col1, col2 = st.columns(2)
        
        with col1:
            self._selecionar_mercados('principal', "📈 Mercados Principais")
        
        with col2:
            self._selecionar_mercados('protecao', "🛡️ Mercados de Proteção")
        
        st.divider()
        
        with st.expander("➕ Adicionar Estratégias Personalizadas", expanded=False):
            self._adicionar_mercados_personalizados()
        
        self._mostrar_resumo_mercados()
        
        if st.button("⚡ Otimizar Portfólio", type="primary", use_container_width=True):
            with st.spinner("Executando otimização quântica..."):
                mercados_otimizados = self.engine.otimizar_portfolio(
                    st.session_state.mercados_selecionados,
                    st.session_state.perfil_risco
                )
                self._gerar_relatorio(mercados_otimizados)
            st.success("Otimização concluída!")
            st.rerun()
    
    def _selecionar_mercados(self, categoria: str, titulo: str):
        """Componente reutilizável para seleção de mercados."""
        st.subheader(titulo)
    
        if categoria == 'principal':
            st.caption("Estratégias com maior potencial de retorno")
        else:
            st.caption("Estratégias para proteção do capital")
        
        if not st.session_state.odds_dinamicas:
            st.warning("Analise um ativo primeiro")
            return
        
        mercados_filtrados = {
            k: v for k, v in st.session_state.odds_dinamicas.items() 
            if self._mapear_categoria(k) == categoria
        }
        
        selecionados = [m.nome for m in st.session_state.mercados_selecionados if m.categoria == categoria]
        
        novos_selecionados = st.multiselect(
            f"Selecione estratégias de {categoria}:",
            options=list(mercados_filtrados.keys()),
            default=selecionados,
            key=f"multiselect_{categoria}"
        )
        
        self._atualizar_mercados_selecionados(categoria, novos_selecionados)
    
    def _atualizar_mercados_selecionados(self, categoria: str, selecionados: List[str]):
        """Mantém a lista de mercados selecionados atualizada."""
        st.session_state.mercados_selecionados = [
            m for m in st.session_state.mercados_selecionados 
            if not (m.categoria == categoria and m.nome not in selecionados)
        ]
        
        for nome in selecionados:
            if nome not in [m.nome for m in st.session_state.mercados_selecionados]:
                st.session_state.mercados_selecionados.append(Mercado(
                    nome=nome,
                    odd=st.session_state.odds_dinamicas[nome],
                    categoria=categoria,
                    ativo_id=st.session_state.ativo_selecionado.id if st.session_state.ativo_selecionado else None,
                    ultima_atualizacao=datetime.now()
                ))
    
    def _adicionar_mercados_personalizados(self):
        """Permite ao usuário adicionar estratégias customizadas."""
        st.markdown("""
        **Quando usar estratégias personalizadas:**
        - Estratégias especiais não listadas
        - Retornos promocionais
        - Hedge personalizado
        """)
    
        col1, col2 = st.columns(2)
    
        with col1:
            nome = st.text_input("Nome da Estratégia", placeholder="Ex: Hedge BTC x ETH")
    
        with col2:
            odd = st.number_input("Retorno Ajustado", min_value=1.01, step=0.1, value=2.0, format="%.2f")
    
        categoria = st.radio(
            "Categoria:",
            ["principal", "protecao"],
            horizontal=True,
            key="radio_categoria_personalizado"
        )
    
        if st.button("Adicionar Estratégia Personalizada"):
            if nome:
                st.session_state.mercados_selecionados.append(Mercado(
                    nome=nome,
                    odd=odd,
                    categoria=categoria,
                    ativo_id=st.session_state.ativo_selecionado.id if st.session_state.ativo_selecionado else None,
                    ultima_atualizacao=datetime.now()
                ))
                st.success(f"Estratégia '{nome}' adicionada!")
            else:
                st.error("Por favor, insira um nome para a estratégia")
    
    def _mostrar_resumo_mercados(self):
        """Exibe um resumo das estratégias selecionadas."""
        st.subheader("📋 Resumo da Estratégia")
        
        if not st.session_state.mercados_selecionados:
            st.warning("Nenhuma estratégia selecionada")
            return
        
        df = pd.DataFrame([{
            "Estratégia": m.nome,
            "Retorno": m.odd,
            "Probabilidade": f"{1/m.odd:.1%}",
            "Categoria": m.categoria.capitalize(),
            "Atualizado": m.ultima_atualizacao.strftime("%H:%M:%S") if m.ultima_atualizacao else "-"
        } for m in st.session_state.mercados_selecionados])
        
        st.dataframe(
            df.style.format({"Retorno": "{:.2f}"}),
            column_config={
                "Estratégia": "Estratégia",
                "Retorno": st.column_config.NumberColumn("Retorno", format="%.2f"),
                "Probabilidade": "Probabilidade",
                "Categoria": st.column_config.TextColumn("Categoria"),
                "Atualizado": "Últ. Atualização"
            },
            hide_index=True,
            use_container_width=True
        )
    
    def _gerar_relatorio(self, mercados: List[Mercado]):
        """Gera um relatório completo após a otimização."""
        if not mercados:
            st.error("Nenhuma estratégia selecionada para otimização")
            return

        capital = st.session_state.capital
        if capital <= 0:
            st.error("Capital deve ser maior que zero")
            return

        dados = []
        retorno_principal = investimento_principal = 0
        retorno_protecao = investimento_protecao = 0

        for m in mercados:
            try:
                alocacao = getattr(m, 'peso_alocacao', 0)
                investimento = alocacao * capital
                retorno_potencial = investimento * m.odd
        
                if m.categoria == 'principal':
                    retorno_principal += retorno_potencial
                    investimento_principal += investimento
                else:
                    retorno_protecao += retorno_potencial
                    investimento_protecao += investimento
        
                dados.append({
                    "Estratégia": m.nome,
                    "Retorno": m.odd,
                    "Probabilidade": f"{1/m.odd:.1%}",
                    "Alocação (%)": round(alocacao * 100, 2),
                    "Investimento (R$)": round(investimento, 2),
                    "Retorno Potencial (R$)": round(retorno_potencial, 2),
                    "Categoria": m.categoria.capitalize()
                })
            except Exception as e:
                continue

        df_alocacao = pd.DataFrame(dados)
    
        if not df_alocacao.empty and 'Categoria' in df_alocacao.columns:
            fig_alocacao = px.pie(
                df_alocacao,
                names='Estratégia',
                values='Alocação (%)',
                title='Distribuição de Capital Otimizada',
                color='Categoria',
                color_discrete_map={'Principal': '#3498db', 'Protecao': '#e74c3c'},
                hole=0.3
            )
        else:
            df_alocacao = pd.DataFrame(columns=["Estratégia", "Retorno", "Probabilidade", "Alocação (%)", 
                                             "Investimento (R$)", "Retorno Potencial (R$)", "Categoria"])
            fig_alocacao = go.Figure()

        st.session_state.relatorio = {
            "risco": min(1.0, max(0.0, self.engine.calcular_risco_portfolio(mercados))),
            "dataframe": df_alocacao,
            "grafico_alocacao": fig_alocacao,
            "retorno_principal": retorno_principal,
            "retorno_protecao": retorno_protecao,
            "investimento_principal": investimento_principal,
            "investimento_protecao": investimento_protecao,
            "total_investido": investimento_principal + investimento_protecao
        }

    def _construir_aba_analise(self):
        """Exibe os resultados da otimização e análises detalhadas."""
        st.header("📊 Análise das Estratégias")
    
        if not hasattr(st.session_state, 'relatorio') or not st.session_state.relatorio:
            st.warning("Execute a otimização na aba 'Configurar' primeiro")
            return

        relatorio = st.session_state.relatorio
        capital = st.session_state.capital
    
        if 'dataframe' not in relatorio or relatorio['dataframe'].empty:
            st.warning("Nenhum dado disponível para análise")
            return

        tab1, tab2, tab3 = st.tabs(["📈 Estratégias Principais", "🛡️ Estratégias de Proteção", "📊 Visão Geral"])
    
        with tab1:
            self._mostrar_detalhes_mercados('principal', relatorio, capital)
    
        with tab2:
            self._mostrar_detalhes_mercados('protecao', relatorio, capital)
    
        with tab3:
            self._mostrar_visao_geral(relatorio, capital)

    def _mostrar_detalhes_mercados(self, categoria: str, relatorio: dict, capital: float):
        """Componente reutilizável para mostrar detalhes das estratégias."""
        st.subheader(f"Estratégias {categoria.capitalize()}")
    
        df = relatorio['dataframe']
        df_filtrado = df[df['Categoria'] == categoria.capitalize()]
    
        if df_filtrado.empty:
            st.warning(f"Nenhuma estratégia {categoria} selecionada")
            return
    
        st.dataframe(
            df_filtrado,
            column_config={
                "Estratégia": "Estratégia",
                "Retorno": st.column_config.NumberColumn("Retorno", format="%.2f"),
                "Probabilidade": "Prob. Implícita",
                "Alocação (%)": st.column_config.NumberColumn("Alocação %", format="%.1f%%"),
                "Investimento (R$)": st.column_config.NumberColumn("Investimento", format="R$ %.2f"),
                "Retorno Potencial (R$)": st.column_config.NumberColumn("Retorno", format="R$ %.2f"),
            },
            hide_index=True,
            use_container_width=True
        )
    
        total_investido = df_filtrado['Investimento (R$)'].sum()
        total_retorno = df_filtrado['Retorno Potencial (R$)'].sum()
        lucro_liquido = total_retorno - total_investido
    
        col1, col2 = st.columns(2)
        col1.metric("Total Investido", f"R$ {total_investido:,.2f}")
        col2.metric("Retorno Potencial", f"R$ {total_retorno:,.2f}", 
                   f"R$ {lucro_liquido:,.2f} (Líquido)")

    def _mostrar_visao_geral(self, relatorio: dict, capital: float):
        """Mostra a visão consolidada dos resultados."""
        st.subheader("Visão Geral Consolidada")
    
        total_investido = relatorio.get('total_investido', 0)
        total_principal = relatorio.get('investimento_principal', 0)
        total_protecao = relatorio.get('investimento_protecao', 0)
        retorno_principal = relatorio.get('retorno_principal', 0)
        retorno_protecao = relatorio.get('retorno_protecao', 0)
    
        perc_total = (total_investido / capital * 100) if capital > 0 else 0
        perc_principal = (total_principal / capital * 100) if capital > 0 else 0
        perc_protecao = (total_protecao / capital * 100) if capital > 0 else 0
    
        lucro_principal = retorno_principal - total_principal
        lucro_protecao = retorno_protecao - total_protecao
        lucro_total = (retorno_principal + retorno_protecao) - total_investido
    
        st.markdown("### 💰 Alocação de Capital")
        cols = st.columns(3)
        cols[0].metric("Total Investido", f"R$ {total_investido:,.2f}", 
                      f"{perc_total:.1f}% do capital")
        cols[1].metric("Principal", f"R$ {total_principal:,.2f}", 
                      f"{perc_principal:.1f}%")
        cols[2].metric("Proteção", f"R$ {total_protecao:,.2f}", 
                      f"{perc_protecao:.1f}%")
    
        st.markdown("### 📈 Retorno Esperado")
        ret_cols = st.columns(2)
        ret_cols[0].metric("Principal", f"R$ {retorno_principal:,.2f}", 
                          f"R$ {lucro_principal:,.2f} (Líquido)")
        ret_cols[1].metric("Proteção", f"R$ {retorno_protecao:,.2f}", 
                          f"R$ {lucro_protecao:,.2f} (Líquido)")
    
        st.markdown("### 🎯 Resultado Consolidado")
        st.metric("Lucro Líquido Total", f"R$ {lucro_total:,.2f}", 
                 f"{(lucro_total/capital*100):.1f}%" if capital > 0 else "0%")
    
        if 'grafico_alocacao' in relatorio and relatorio['grafico_alocacao']:
            st.plotly_chart(relatorio['grafico_alocacao'], use_container_width=True)
        
    def _construir_aba_historico(self):
        """Exibe o histórico de performance das estratégias."""
        st.header("📈 Histórico de Performance")
        
        # Simulação de dados históricos com padrões de mercado
        dados = pd.DataFrame({
            "Data": pd.date_range(end=datetime.now(), periods=90),
            "Retorno (%)": np.cumsum(np.random.normal(0.5, 1.5, 90)),
            "Exposição Risco": np.cumsum(np.random.normal(0.3, 0.1, 90)),
            "Correlação Dolar": np.sin(np.linspace(0, 4*np.pi, 90)) * 0.5 + 0.5,
            "BTC Dominance": np.linspace(40, 55, 90) + np.random.normal(0, 2, 90)
        })
        
        fig = px.line(
            dados, 
            x="Data", 
            y=["Retorno (%)", "Exposição Risco", "Correlação Dolar", "BTC Dominance"],
            title="Evolução do Portfólio e Fatores de Mercado",
            labels={"value": "Valor", "variable": "Métrica"},
            color_discrete_map={
                "Retorno (%)": "#2ecc71",
                "Exposição Risco": "#e74c3c",
                "Correlação Dolar": "#3498db",
                "BTC Dominance": "#f39c12"
            }
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        st.dataframe(
            dados.tail(15),
            column_config={
                "Data": "Data",
                "Retorno (%)": st.column_config.NumberColumn("Retorno (%)", format="%.2f%%"),
                "Exposição Risco": st.column_config.NumberColumn("Risco", format="%.2f"),
                "Correlação Dolar": st.column_config.NumberColumn("Correlação Dolar", format="%.2f"),
                "BTC Dominance": st.column_config.NumberColumn("BTC Dominance", format="%.1f%%")
            },
            hide_index=True
        )
    
    def _mapear_categoria(self, nome_mercado: str) -> str:
        """Mapeia automaticamente o nome do mercado para principal ou proteção."""
        nome = nome_mercado.lower()
        if ('proteção' in nome or 
            'hedge' in nome or 
            'baixa' in nome or 
            'stablecoin' in nome):
            return 'protecao'
        return 'principal'
    
    def _carregar_ativos_exemplo(self) -> List[Ativo]:
        """Carrega ativos de exemplo com estatísticas simuladas."""
        return [
            Ativo(
                id="1",
                nome="BTC/USD",
                tipo="cripto",
                estatisticas={
                    'volatilidade': 0.08,
                    'correlacao_dolar': -0.75,
                    'correlacao_juros': -0.85,
                    'beta': 1.8,
                    'odds_referencia': {
                        'alta_1d': 1.85,
                        'baixa_1d': 2.05,
                        'alta_semana': 2.20,
                        'baixa_semana': 1.90,
                        'alta_mes': 2.50,
                        'baixa_mes': 1.75
                    }
                }
            ),
            Ativo(
                id="2",
                nome="NASDAQ",
                tipo="indice",
                estatisticas={
                    'volatilidade': 0.05,
                    'correlacao_dolar': -0.65,
                    'correlacao_juros': -0.90,
                    'beta': 1.0,
                    'odds_referencia': {
                        'alta_1d': 1.75,
                        'baixa_1d': 2.15,
                        'alta_semana': 2.00,
                        'baixa_semana': 1.85,
                        'alta_mes': 2.30,
                        'baixa_mes': 1.65
                    }
                }
            ),
            Ativo(
                id="3",
                nome="Ouro",
                tipo="commodity",
                estatisticas={
                    'volatilidade': 0.03,
                    'correlacao_dolar': -0.82,
                    'correlacao_juros': -0.70,
                    'beta': 0.5,
                    'odds_referencia': {
                        'alta_1d': 1.65,
                        'baixa_1d': 2.25,
                        'alta_semana': 1.85,
                        'baixa_semana': 2.00,
                        'alta_mes': 2.10,
                        'baixa_mes': 1.90
                    }
                }
            )
        ]
    
    def _salvar_perfil(self, nome: str):
        """Simula o salvamento de um perfil de configurações."""
        if not nome:
            st.error("Digite um nome para o perfil")
            return
        
        st.success(f"Perfil '{nome}' salvo com sucesso!")
    
    def _carregar_perfil(self, nome: str):
        """Simula o carregamento de um perfil de configurações."""
        if not nome:
            st.error("Digite um nome de perfil válido")
            return
        
        st.warning("Funcionalidade em desenvolvimento - use as configurações atuais")
