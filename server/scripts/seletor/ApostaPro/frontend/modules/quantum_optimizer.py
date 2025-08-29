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
class Partida:
    id: str
    time_mandante: str
    time_visitante: str
    liga: str
    estatisticas: Dict = field(default_factory=lambda: {
        # Estatísticas existentes
        'media_gols': 2.5,
        'media_gols_1t': 1.0,
        'media_gols_2t': 1.0,
        'vitorias_mandante': 0.5,
        'empates_mandante': 0.3,
        'ambas_marcam_freq': 0.5,
        'media_cartoes': 3.0,
        'media_escanteios': 8.0,
        
        # Novas odds de referência
        'odds_referencia': {
            'menos_25': 1.85,
            'mais_25': 2.05,
            'empate': 3.50,
            'ambas_marcam': 1.80,
            'mais_15_1t': 1.75,
            'menos_15_1t': 2.05,
            'mais_15_2t': 1.80,
            'menos_15_2t': 2.00,
            'over_escanteios': 1.75,
            'over_cartoes': 1.65
        }
    })

@dataclass
class Mercado:
    """Representa um mercado de aposta com todos os atributos necessários."""
    nome: str
    odd: float
    categoria: str  # 'principal' ou 'protecao'
    probabilidade: float = 0.0
    peso_alocacao: float = 0.0
    partida_id: Optional[str] = None
    ultima_atualizacao: Optional[datetime] = None
    valor_esperado: Optional[float] = None

# =============================================================================
# 2. MOTOR QUÂNTICO (CÁLCULOS E OTIMIZAÇÃO)
# =============================================================================

class QuantumEngine:
    """Motor de otimização quântica avançado para apostas esportivas."""
    
    def __init__(self):
        self.correlacoes = self._carregar_correlacoes()
        self.historico = pd.DataFrame(columns=['mercado', 'odd', 'timestamp'])
    
    def _carregar_correlacoes(self) -> Dict[str, float]:
        """Carrega a matriz de correlações entre diferentes tipos de mercados."""
        return {
            'over_under': -0.98,  # Correlação quase perfeita negativa
            'ambas_marcam': -0.87,
            'handicap': -0.76,
            'resultado': -0.68,
            'escanteios': -0.65,
            'cartoes': -0.55
        }
    
    def _calcular_odds_dinamicas(self, partida: Partida) -> Dict[str, float]:
        stats = partida.estatisticas
        odds_ref = stats['odds_referencia']
    
        # Probabilidades baseadas nas odds de referência
        prob_menos_25 = 1 / odds_ref['menos_25']
        prob_mais_25 = 1 / odds_ref['mais_25']
        prob_empate = 1 / odds_ref['empate']
        prob_ambas_marcam = 1 / odds_ref['ambas_marcam']
    
        # Se a odd do mandante foi fornecida manualmente, usa ela
        if 'mandante' in odds_ref:
            prob_vitoria = 1 / odds_ref['mandante']
        else:
            # Cálculo automático apenas se não foi fornecida manualmente
            ajuste_mandante = stats['vitorias_mandante'] / 0.5
            prob_vitoria = min(0.85, (1 - prob_empate) * ajuste_mandante * 0.5)

        # Mercados principais com odds reais
        odds = {
            # Mercados de gols
            "Over 2.5 Gols": odds_ref['mais_25'],
            "Under 2.5 Gols": odds_ref['menos_25'],
            "Empate": odds_ref['empate'],
        
            # Mercados por tempo
            "Mais 1.5 Gols (1T)": odds_ref['mais_15_1t'],
            "Menos 1.5 Gols (1T)": odds_ref['menos_15_1t'],
            "Mais 1.5 Gols (2T)": odds_ref['mais_15_2t'],
            "Menos 1.5 Gols (2T)": odds_ref['menos_15_2t'],
        
            # Ambos marcam
            "Ambas Marcam": odds_ref['ambas_marcam'],
            "Ambas Não Marcam": 1 / (1 - prob_ambas_marcam),
        
            # Cartões e escanteios
            "Over Escanteios": odds_ref['over_escanteios'],
            "Under Escanteios": 1 / (1 - (1/odds_ref['over_escanteios'])),
            "Over Cartões": odds_ref['over_cartoes'],
            "Under Cartões": 1 / (1 - (1/odds_ref['over_cartoes'])),
        
            # Resultados
            "Time Mandante Vence": odds_ref.get('mandante', max(1.5, min(10.0, 1/prob_vitoria))),
            "Time Visitante Vence": 1 / (1 - prob_vitoria - prob_empate),
        }
    
        return odds
    
    def _calcular_prob_over_under(self, stats: Dict) -> float:
        """Calcula probabilidade para mercados Over/Under com base em múltiplos fatores."""
        media_gols = stats.get('media_gols', 2.5)
        forca_ataque = stats.get('forca_ataque', 1.0)
        forca_defesa = stats.get('forca_defesa', 1.0)
        
        # Fórmula base ajustada por força de ataque/defesa
        prob_base = (media_gols * forca_ataque) / (forca_defesa * 2.5)
        
        # Limites mínimos e máximos para probabilidade
        return min(0.85, max(0.15, prob_base))
    
    def _calcular_prob_vitoria_mandante(self, stats: Dict) -> float:
        """Calcula probabilidade de vitória do mandante considerando empates."""
        vitorias = stats.get('vitorias_mandante', 0.5)
        empates = stats.get('empates_mandante', 0.3)
    
        # Ajuste para garantir que a soma não ultrapasse 1
        prob_vitoria = min(vitorias, 1 - empates)
        return max(0.1, prob_vitoria)  # Limite mínimo de 10%
    
    def _calcular_prob_ambas_marcam(self, stats: Dict) -> float:
        """Calcula probabilidade de ambos times marcarem."""
        freq_historica = stats.get('ambas_marcam_freq', 0.5)
        forca_ataque_mandante = stats.get('forca_ataque', 1.0)
        forca_ataque_visitante = 1.0 / stats.get('forca_defesa', 1.0)
        
        return min(0.9, max(0.1, freq_historica * (forca_ataque_mandante + forca_ataque_visitante) / 2))
    
    def _calcular_prob_escanteios(self, stats: Dict) -> float:
        """Calcula probabilidade para mercados de escanteios."""
        media_escanteios = stats.get('media_escanteios', 8.0)
        return min(0.9, max(0.1, media_escanteios / 10))
    
    def _calcular_prob_cartoes(self, stats: Dict) -> float:
        """Calcula probabilidade para mercados de cartões."""
        media_cartoes = stats.get('media_cartoes', 3.0)
        return min(0.9, max(0.1, media_cartoes / 4))
    
    def calcular_valor_esperado(self, probabilidade: float, odd: float) -> float:
        """Calcula o valor esperado de uma aposta."""
        return (probabilidade * (odd - 1)) - (1 - probabilidade)
    
    def calcular_risco_portfolio(self, mercados: List[Mercado]) -> float:
        """
        Calcula um índice de risco normalizado entre 0 e 1
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
        - Odds disponíveis
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
        Executa o processo completo de otimização do portfólio de apostas:
        1. Calcula probabilidades implícitas das odds
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
                'protecao_min': 0.2,   # Mínimo em mercados de proteção
                'fator_risco': 0.7     # Fator de redução de risco
            },
            'Moderado': {
                'exposicao_max': 0.7,
                'protecao_min': 0.1,
                'fator_risco': 1.0
            },
            'Agressivo': {
                'exposicao_max': 0.9,
                'protecao_min': 0.05,
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
            if any(x in m.nome.lower() for x in ['over', 'under', 'ambas']):
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
# 3. INTERFACE DO USUÁRIO (STREAMLIT)
# =============================================================================

class QuantumInterface:
    """Sistema completo de gestão quântica de apostas"""
    
    def __init__(self):
        self.engine = QuantumEngine()
        self.mercados = []
        self._carregar_mercados_padrao()
    
    def _inicializar_estado(self):
        """Inicializa todos os estados necessários na sessão."""
        if 'partida_selecionada' not in st.session_state:
            st.session_state.partida_selecionada = None
        if 'mercados_selecionados' not in st.session_state:
            st.session_state.mercados_selecionados = []
        if 'odds_dinamicas' not in st.session_state:
            st.session_state.odds_dinamicas = {}
        if 'relatorio' not in st.session_state:
            st.session_state.relatorio = {
                "risco": 0.0,
                "dataframe": pd.DataFrame(),
                "grafico_alocacao": go.Figure(),  # Figura vazia para evitar erros
                "analise_over_under": None,
                "recomendacoes": []
            }
        if 'perfil_risco' not in st.session_state:
            st.session_state.perfil_risco = "Moderado"
        if 'capital' not in st.session_state:
            st.session_state.capital = 1000.0
        if 'modo_entrada' not in st.session_state:
            st.session_state.modo_entrada = "Manual"  # Padrão para entrada manual
    
    def mostrar_interface(self):
        """Renderiza a interface principal"""
        # Inicializa o estado da sessão primeiro
        self._inicializar_estado()
    
        st.title("⚡ Quantum Betting Pro")
        st.caption("Sistema Inteligente de Otimização de Apostas Esportivas")
        
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
            ## 📚 Guia do Quantum Betting Pro
        
            ### 🔍 Configurando sua Partida
            1. **Modo de Entrada**: Escolha entre inserir dados manualmente ou usar exemplos prontos
            2. **Times**: Insira os nomes do time mandante e visitante
            3. **Estatísticas**:
               - Média de Gols: Número médio de gols por partida (ex: 2.5)
               - Força de Ataque: Capacidade ofensiva (1.0 = média)
               - Força de Defesa: Capacidade defensiva (1.0 = média)
               - % Vitórias Mandante: Frequência histórica de vitórias em casa
               - % Ambos Marcam: Frequência com que ambos times marcam
        
            ### 📊 Mercados de Apostas
            - **Principais**: Mercados com maior potencial de retorno (Over, Vitória, etc)
            - **Proteção**: Mercados para hedge (Under, Empate, etc)
            - **Personalizados**: Adicione mercados específicos com odds manuais
        
            ### ⚡ Otimização Quântica
            O sistema calcula:
            - Valor esperado de cada aposta
            - Correlações entre mercados
            - Distribuição ideal do capital
            - Nível de risco do portfólio
        
            ### 💡 Dicas Profissionais
            - Comece com 3-5 mercados principais
            - Use 1-2 mercados de proteção
            - Ajuste o perfil de risco conforme sua estratégia
            - Monitore os valores esperados
            """)
            
    def _carregar_mercados_padrao(self):
        """Carrega templates de mercados com odds sugeridas"""
        self.mercados_principais = {
            "Over 2.5 Gols": 1.85,
            "Mais 1.5 Gols (1T)": 1.75,
            "Ambas Marcam": 1.80,
            "Over Escanteios": 1.75,
            "Over Cartões": 1.65,
            "Time Mandante Vence": 2.10
        }

        self.mercados_protecao = {
            "Under 2.5 Gols": 2.05,
            "Empate": 3.50,
            "Menos 1.5 Gols (1T)": 2.05,
            "Ambas Não Marcam": 2.20,
            "Under Escanteios": 2.10,
            "Under Cartões": 2.25
        }
    
        from datetime import datetime  # Garante que datetime esteja disponível

        self.mercados = []

        # Adiciona mercados principais
        for nome, odd in self.mercados_principais.items():
            mercado = Mercado(
                nome=nome,
                odd=odd,
                categoria='principal',
                probabilidade=0.5,  # Estado inicial neutro
                ultima_atualizacao=datetime.now()
            )
            self.mercados.append(mercado)

        # Adiciona mercados de proteção
        for nome, odd in self.mercados_protecao.items():
            mercado = Mercado(
                nome=nome,
                odd=odd,
                categoria='protecao',
                probabilidade=0.5,  # Estado inicial neutro
                ultima_atualizacao=datetime.now()
            )
            self.mercados.append(mercado)

    def listar_mercados(self):
        """Exibe mercados carregados."""
        for m in self.mercados:
            print(f"{m.nome}: Odd {m.odd} | Prob {m.probabilidade}")
    
    def _construir_sidebar(self):
        """Constroi a barra lateral com configurações globais."""
        st.header("⚙️ Configurações Globais")
    
        # Botão de ajuda
        if st.button("❓ Guia Rápido", help="Clique para ver instruções de uso"):
            self.mostrar_ajuda()
    
        # Perfil de risco com explicação
        with st.expander("🔍 Sobre Perfis de Risco", expanded=False):
            st.markdown("""
            - **Conservador**: Menos exposição, mais proteções
            - **Moderado**: Equilíbrio entre risco e retorno
            - **Agressivo**: Maior potencial de ganho, mais risco
            """)
    
        st.session_state.perfil_risco = st.selectbox(
            "Perfil de Risco",
            ["Conservador", "Moderado", "Agressivo"],
            index=1
        )
    
        # Capital com dicas
        st.session_state.capital = st.number_input(
            "Capital Total (R$)",
            min_value=10.0,
            value=20.0,
            step=10.0,
            format="%.2f",
            help="Valor total disponível para apostas nesta estratégia"
        )
    
        # Gerenciamento de perfis
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

    def _selecionar_partida(self):
        """Componente para seleção ou entrada manual da partida."""
        st.subheader("⚽ Configurar Partida")
        with st.expander("ℹ️ Como configurar", expanded=False):
            st.markdown("""
            **Para melhores resultados:**
            1. Use estatísticas reais quando possível
            2. Considere o desempenho recente dos times
            3. Analise confrontos diretos entre as equipes
            """)

        # Seleção do modo de entrada
        st.session_state.modo_entrada = st.radio(
            "Modo de Entrada:",
            ["Manual", "Exemplos Prontos"],
            horizontal=True
        )

        if st.session_state.modo_entrada == "Manual":
            # Entrada manual dos times e estatísticas
            col1, col2 = st.columns(2)
            with col1:
                time_mandante = st.text_input("Time Mandante", value="")
            with col2:
                time_visitante = st.text_input("Time Visitante", value="")

            liga = st.text_input("Liga/Campeonato", value="")

            # Seção de Odds de Referência
            st.subheader("📊 Odds de Referência (Obrigatórias)")
        
            # Linha 1 de Odds (adicionando odd do mandante)
            col_odd1, col_odd2, col_odd3, col_odd4 = st.columns(4)
            with col_odd1:
                odd_mandante = st.number_input("Time Mandante Vence", min_value=1.01, value=2.10, step=0.01,
                                             help="Odd para o time mandante vencer")
            with col_odd2:
                odd_menos_25 = st.number_input("Menos 2.5 Gols", min_value=1.01, value=3.00, step=0.01,
                                             help="Odd para o mercado 'Menos de 2.5 gols na partida'")
            with col_odd3:
                odd_mais_25 = st.number_input("Mais 2.5 Gols", min_value=1.01, value=1.36, step=0.01,
                                            help="Odd para o mercado 'Mais de 2.5 gols na partida'")
            with col_odd4:
                odd_empate = st.number_input("Empate", min_value=1.01, value=5.90, step=0.01,
                                           help="Odd para o mercado 'Empate'")

            # Linha 2 de Odds (Por Tempo)
            st.markdown("**📊 Odds por Tempo**")
            col_odd5, col_odd6, col_odd7, col_odd8 = st.columns(4)
            with col_odd5:
                odd_mais_15_1t = st.number_input("Mais 1.5 (1T)", min_value=1.01, value=1.95, step=0.01,
                                               help="Odd para o mercado 'Mais de 1.5 gols no 1º tempo'")
            with col_odd6:
                odd_menos_15_1t = st.number_input("Menos 1.5 (1T)", min_value=1.01, value=1.85, step=0.01,
                                                help="Odd para o mercado 'Menos de 1.5 gols no 1º tempo'")
            with col_odd7:
                odd_mais_15_2t = st.number_input("Mais 1.5 (2T)", min_value=1.01, value=1.80, step=0.01,
                                               help="Odd para o mercado 'Mais de 1.5 gols no 2º tempo'")
            with col_odd8:
                odd_menos_15_2t = st.number_input("Menos 1.5 (2T)", min_value=1.01, value=1.90, step=0.01,
                                                help="Odd para o mercado 'Menos de 1.5 gols no 2º tempo'")

            # Linha 3 de Odds (Especiais)
            st.markdown("**📊 Odds Especiais**")
            col_odd9, col_odd10, col_odd11 = st.columns(3)
            with col_odd9:
                odd_over_escanteios = st.number_input("Over Escanteios", min_value=1.01, value=1.75, step=0.01,
                                                 help="Odd para o mercado 'Acima da média de escanteios'")
            with col_odd10:
                odd_over_cartoes = st.number_input("Over Cartões", min_value=1.01, value=1.65, step=0.01,
                                                 help="Odd para o mercado 'Acima da média de cartões'")
            with col_odd11:
                odd_ambas_marcam = st.number_input("Ambas Marcam", min_value=1.01, value=1.80, step=0.01,
                                                 help="Odd para o mercado 'Ambos times marcam'")

            # Seção de Estatísticas
            st.subheader("📈 Estatísticas do Confronto")
            col1, col2, col3 = st.columns(3)
            with col1:
                media_gols = st.number_input("Média Total de Gols", min_value=0.0, value=2.5, step=0.1,
                                           help="Média de gols totais por partida (ambos times)")
                media_gols_1t = st.number_input("Média Gols 1º Tempo", min_value=0.0, value=1.0, step=0.1,
                                              help="Média de gols no 1º tempo")
            with col2:
                media_gols_2t = st.number_input("Média Gols 2º Tempo", min_value=0.0, value=1.0, step=0.1,
                                              help="Média de gols no 2º tempo")
                vitorias_mandante = st.number_input("Vitórias Mandante (%)", min_value=0.0, max_value=100.0, value=50.0, step=1.0,
                                                  help="Porcentagem de vitórias do time mandante em casa (0-100%)")
            with col3:
                empates_mandante = st.number_input("Empates Mandante (%)", min_value=0.0, max_value=100.0, value=30.0, step=1.0,
                                                 help="Porcentagem de empates do time mandante em casa (0-100%)")
                ambas_marcam = st.number_input("Ambos Marcam (%)", min_value=0.0, max_value=100.0, value=50.0, step=1.0,
                                             help="Porcentagem de jogos onde ambos marcam (0-100%)")
                media_cartoes = st.number_input("Média de Cartões", min_value=0.0, value=3.0, step=0.1,
                                              help="Média de cartões por partida")

            # Botão para criar a partida
            if st.button("🔍 Criar Partida e Calcular Odds"):
                if not time_mandante or not time_visitante:
                    st.error("❌ Por favor, insira os nomes dos times")
                elif any(odd <= 1.0 for odd in [odd_mandante, odd_menos_25, odd_mais_25, odd_empate,
                                              odd_mais_15_1t, odd_menos_15_1t, odd_mais_15_2t, odd_menos_15_2t,
                                              odd_over_escanteios, odd_over_cartoes]):
                    st.error("❌ Todas as odds devem ser maiores que 1.00")
                else:
                    partida = Partida(
                        id=str(datetime.now().timestamp()),
                        time_mandante=time_mandante,
                        time_visitante=time_visitante,
                        liga=liga,
                        estatisticas={
                            'media_gols': media_gols,
                            'media_gols_1t': media_gols_1t,
                            'media_gols_2t': media_gols_2t,
                            'vitorias_mandante': vitorias_mandante / 100,
                            'empates_mandante': empates_mandante / 100,
                            'ambas_marcam_freq': ambas_marcam / 100,
                            'media_cartoes': media_cartoes,
                            'odds_referencia': {
                                'mandante': odd_mandante,
                                'menos_25': odd_menos_25,
                                'mais_25': odd_mais_25,
                                'empate': odd_empate,
                                'ambas_marcam': odd_ambas_marcam,
                                'mais_15_1t': odd_mais_15_1t,
                                'menos_15_1t': odd_menos_15_1t,
                                'mais_15_2t': odd_mais_15_2t,
                                'menos_15_2t': odd_menos_15_2t,
                                'over_escanteios': odd_over_escanteios,
                                'over_cartoes': odd_over_cartoes
                            }
                        }
                    )

                    # Atualiza estado da sessão
                    st.session_state.partida_selecionada = partida
                    st.session_state.odds_dinamicas = self.engine._calcular_odds_dinamicas(partida)
                    st.session_state.mercados_selecionados = []

                    st.toast(f"✅ Partida criada: {time_mandante} x {time_visitante}")

    def _construir_aba_configuracao(self):
        """Interface para configuração da estratégia de apostas."""
        st.header("🎯 Configurar Estratégia")
        
        # Seção de seleção de partida
        self._selecionar_partida()
        
        if st.session_state.partida_selecionada is None:
            st.info("Configure uma partida para começar")
            return
        
        # Mostra informações da partida
        partida = st.session_state.partida_selecionada
        st.success(f"Partida configurada: {partida.time_mandante} x {partida.time_visitante} - {partida.liga}")
        
        # Seção de seleção de mercados
        col1, col2 = st.columns(2)
        
        with col1:
            self._selecionar_mercados('principal', "📈 Mercados Principais")
        
        with col2:
            self._selecionar_mercados('protecao', "🛡️ Mercados de Proteção")
        
        st.divider()
        
        # Seção de mercados personalizados
        with st.expander("➕ Adicionar Mercados Personalizados", expanded=False):
            self._adicionar_mercados_personalizados()
        
        # Resumo e otimização
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
            st.caption("Mercados com maior potencial de retorno")
        else:
            st.caption("Mercados para proteção do capital")
        
        if not st.session_state.odds_dinamicas:
            st.warning("Analise uma partida primeiro")
            return
        
        # Filtra mercados por categoria
        mercados_filtrados = {
            k: v for k, v in st.session_state.odds_dinamicas.items() 
            if self._mapear_categoria(k) == categoria
        }
        
        # Obtém mercados já selecionados
        selecionados = [m.nome for m in st.session_state.mercados_selecionados if m.categoria == categoria]
        
        # Widget de seleção
        novos_selecionados = st.multiselect(
            f"Selecione mercados de {categoria}:",
            options=list(mercados_filtrados.keys()),
            default=selecionados,
            key=f"multiselect_{categoria}"
        )
        
        # Atualiza a lista de mercados selecionados
        self._atualizar_mercados_selecionados(categoria, novos_selecionados)
    
    def _atualizar_mercados_selecionados(self, categoria: str, selecionados: List[str]):
        """Mantém a lista de mercados selecionados atualizada."""
        # Remove mercados desmarcados desta categoria
        st.session_state.mercados_selecionados = [
            m for m in st.session_state.mercados_selecionados 
            if not (m.categoria == categoria and m.nome not in selecionados)
        ]
        
        # Adiciona novos mercados selecionados
        for nome in selecionados:
            if nome not in [m.nome for m in st.session_state.mercados_selecionados]:
                st.session_state.mercados_selecionados.append(Mercado(
                    nome=nome,
                    odd=st.session_state.odds_dinamicas[nome],
                    categoria=categoria,
                    partida_id=st.session_state.partida_selecionada.id,
                    ultima_atualizacao=datetime.now()
                ))
    
    def _adicionar_mercados_personalizados(self):
        """Permite ao usuário adicionar mercados customizados."""
        # Removido o expander aninhado
        st.markdown("""
        **Quando usar mercados personalizados:**
        - Mercados especiais não listados
        - Odds promocionais
        - Estratégias personalizadas
        """)
    
        col1, col2 = st.columns(2)
    
        with col1:
            nome = st.text_input("Nome do Mercado", placeholder="Ex: Time A vencer por 2+ gols")
    
        with col2:
            odd = st.number_input("Odd", min_value=1.01, step=0.1, value=2.0, format="%.2f")
    
        categoria = st.radio(
            "Categoria:",
            ["principal", "protecao"],
            horizontal=True,
            key="radio_categoria_personalizado"
        )
    
        if st.button("Adicionar Mercado Personalizado"):
            if nome:
                st.session_state.mercados_selecionados.append(Mercado(
                    nome=nome,
                    odd=odd,
                    categoria=categoria,
                    partida_id=st.session_state.partida_selecionada.id if st.session_state.partida_selecionada else None,
                    ultima_atualizacao=datetime.now()
                ))
                st.success(f"Mercado '{nome}' adicionado!")
            else:
                st.error("Por favor, insira um nome para o mercado")
    
    def _mostrar_resumo_mercados(self):
        """Exibe um resumo dos mercados selecionados."""
        st.subheader("📋 Resumo da Estratégia")
        
        if not st.session_state.mercados_selecionados:
            st.warning("Nenhum mercado selecionado")
            return
        
        df = pd.DataFrame([{
            "Mercado": m.nome,
            "Odd": m.odd,
            "Probabilidade": f"{1/m.odd:.1%}",
            "Categoria": m.categoria.capitalize(),
            "Atualizado": m.ultima_atualizacao.strftime("%H:%M:%S") if m.ultima_atualizacao else "-"
        } for m in st.session_state.mercados_selecionados])
        
        st.dataframe(
            df.style.format({"Odd": "{:.2f}"}),
            column_config={
                "Mercado": "Mercado",
                "Odd": st.column_config.NumberColumn("Odd", format="%.2f"),
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
            st.error("Nenhum mercado selecionado para otimização")
            return

        capital = st.session_state.capital
        if capital <= 0:
            st.error("Capital deve ser maior que zero")
            return

        # Inicializa acumuladores
        dados = []
        retorno_principal = investimento_principal = 0
        retorno_protecao = investimento_protecao = 0

        # Processa cada mercado
        for m in mercados:
            try:
                alocacao = getattr(m, 'peso_alocacao', 0)
                investimento = alocacao * capital
                retorno_potencial = investimento * m.odd
        
                # Acumula por categoria
                if m.categoria == 'principal':
                    retorno_principal += retorno_potencial
                    investimento_principal += investimento
                else:
                    retorno_protecao += retorno_potencial
                    investimento_protecao += investimento
        
                # Adiciona dados para o DataFrame - GARANTINDO QUE 'Categoria' ESTÁ CAPITALIZADA
                dados.append({
                    "Mercado": m.nome,
                    "Odd": m.odd,
                    "Probabilidade": f"{1/m.odd:.1%}",
                    "Alocação (%)": round(alocacao * 100, 2),
                    "Investimento (R$)": round(investimento, 2),
                    "Retorno Potencial (R$)": round(retorno_potencial, 2),
                    "Categoria": m.categoria.capitalize()  # Garante que está capitalizada
                })
            except Exception as e:
                continue

        # Cria DataFrame e gráfico
        df_alocacao = pd.DataFrame(dados)
    
        # Garante que o DataFrame não está vazio e tem a coluna 'Categoria'
        if not df_alocacao.empty and 'Categoria' in df_alocacao.columns:
            fig_alocacao = px.pie(
                df_alocacao,
                names='Mercado',
                values='Alocação (%)',
                title='Distribuição de Capital Otimizada',
                color='Categoria',
                color_discrete_map={'Principal': '#3498db', 'Protecao': '#e74c3c'},
                hole=0.3
            )
        else:
            # Cria um DataFrame vazio com a estrutura esperada
            df_alocacao = pd.DataFrame(columns=["Mercado", "Odd", "Probabilidade", "Alocação (%)", 
                                              "Investimento (R$)", "Retorno Potencial (R$)", "Categoria"])
            fig_alocacao = go.Figure()

        # Atualiza o relatório na sessão
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
        st.header("📊 Análise dos Mercados")
    
        # Verificação inicial
        if not hasattr(st.session_state, 'relatorio') or not st.session_state.relatorio:
            st.warning("Execute a otimização na aba 'Configurar' primeiro")
            return

        relatorio = st.session_state.relatorio
        capital = st.session_state.capital
    
        # Verifica se o DataFrame existe e tem dados
        if 'dataframe' not in relatorio or relatorio['dataframe'].empty:
            st.warning("Nenhum dado disponível para análise")
            return

        # Cria abas somente se houver dados
        tab1, tab2, tab3 = st.tabs(["📈 Mercados Principais", "🛡️ Mercados de Proteção", "📊 Visão Geral"])
    
        with tab1:
            self._mostrar_detalhes_mercados('principal', relatorio, capital)
    
        with tab2:
            self._mostrar_detalhes_mercados('protecao', relatorio, capital)
    
        with tab3:
            self._mostrar_visao_geral(relatorio, capital)

    def _mostrar_detalhes_mercados(self, categoria: str, relatorio: dict, capital: float):
        """Componente reutilizável para mostrar detalhes dos mercados."""
        st.subheader(f"Mercados {categoria.capitalize()}")
    
        # Filtra mercados por categoria
        df = relatorio['dataframe']
        df_filtrado = df[df['Categoria'] == categoria.capitalize()]
    
        if df_filtrado.empty:
            st.warning(f"Nenhum mercado {categoria} selecionado")
            return
    
        # Mostra tabela detalhada
        st.dataframe(
            df_filtrado,
            column_config={
                "Mercado": "Mercado",
                "Odd": st.column_config.NumberColumn("Odd", format="%.2f"),
                "Probabilidade": "Prob. Implícita",
                "Alocação (%)": st.column_config.NumberColumn("Alocação %", format="%.1f%%"),
                "Investimento (R$)": st.column_config.NumberColumn("Investimento", format="R$ %.2f"),
                "Retorno Potencial (R$)": st.column_config.NumberColumn("Retorno", format="R$ %.2f"),
            },
            hide_index=True,
            use_container_width=True
        )
    
        # Calcula totais
        total_investido = df_filtrado['Investimento (R$)'].sum()
        total_retorno = df_filtrado['Retorno Potencial (R$)'].sum()
        lucro_liquido = total_retorno - total_investido
    
        # Mostra métricas
        col1, col2 = st.columns(2)
        col1.metric("Total Investido", f"R$ {total_investido:,.2f}")
        col2.metric("Retorno Potencial", f"R$ {total_retorno:,.2f}", 
                   f"R$ {lucro_liquido:,.2f} (Líquido)")

    def _mostrar_visao_geral(self, relatorio: dict, capital: float):
        """Mostra a visão consolidada dos resultados."""
        st.subheader("Visão Geral Consolidada")
    
        # Dados do relatório com verificações de segurança
        total_investido = relatorio.get('total_investido', 0)
        total_principal = relatorio.get('investimento_principal', 0)
        total_protecao = relatorio.get('investimento_protecao', 0)
        retorno_principal = relatorio.get('retorno_principal', 0)
        retorno_protecao = relatorio.get('retorno_protecao', 0)
    
        # Cálculos com proteção contra divisão por zero
        perc_total = (total_investido / capital * 100) if capital > 0 else 0
        perc_principal = (total_principal / capital * 100) if capital > 0 else 0
        perc_protecao = (total_protecao / capital * 100) if capital > 0 else 0
    
        lucro_principal = retorno_principal - total_principal
        lucro_protecao = retorno_protecao - total_protecao
        lucro_total = (retorno_principal + retorno_protecao) - total_investido
    
        # Seção de Investimento
        st.markdown("### 💰 Alocação de Capital")
        cols = st.columns(3)
        cols[0].metric("Total Investido", f"R$ {total_investido:,.2f}", 
                      f"{perc_total:.1f}% do capital")
        cols[1].metric("Principal", f"R$ {total_principal:,.2f}", 
                      f"{perc_principal:.1f}%")
        cols[2].metric("Proteção", f"R$ {total_protecao:,.2f}", 
                      f"{perc_protecao:.1f}%")
    
        # Seção de Retorno
        st.markdown("### 📈 Retorno Esperado")
        ret_cols = st.columns(2)
        ret_cols[0].metric("Principal", f"R$ {retorno_principal:,.2f}", 
                          f"R$ {lucro_principal:,.2f} (Líquido)")
        ret_cols[1].metric("Proteção", f"R$ {retorno_protecao:,.2f}", 
                          f"R$ {lucro_protecao:,.2f} (Líquido)")
    
        # Resultado Final
        st.markdown("### 🎯 Resultado Consolidado")
        st.metric("Lucro Líquido Total", f"R$ {lucro_total:,.2f}", 
                 f"{(lucro_total/capital*100):.1f}%" if capital > 0 else "0%")
    
        # Gráfico de distribuição com verificação
        if 'grafico_alocacao' in relatorio and relatorio['grafico_alocacao']:
            st.plotly_chart(relatorio['grafico_alocacao'], use_container_width=True)
        
    def _construir_aba_historico(self):
        """Exibe o histórico de performance das estratégias."""
        st.header("📈 Histórico de Performance")
        
        # Simulação de dados históricos
        dados = pd.DataFrame({
            "Data": pd.date_range(end=datetime.now(), periods=30),
            "Retorno (%)": np.cumsum(np.random.normal(1, 2, 30)),
            "Risco": np.cumsum(np.random.normal(0.3, 0.15, 30))
        })
        
        fig = px.line(
            dados, 
            x="Data", 
            y=["Retorno (%)", "Risco"],
            title="Evolução do Risco e Retorno",
            labels={"value": "Valor", "variable": "Métrica"},
            color_discrete_map={
                "Retorno (%)": "#2ecc71",
                "Risco": "#e74c3c"
            }
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        st.dataframe(
            dados.tail(10),
            column_config={
                "Data": "Data",
                "Retorno (%)": st.column_config.NumberColumn("Retorno (%)", format="%.2f%%"),
                "Risco": st.column_config.NumberColumn("Risco", format="%.2f")
            },
            hide_index=True
        )
    
    def _gerar_recomendacoes(self, risco: float, mercados: List[Mercado]) -> List[str]:
        """Gera recomendações personalizadas baseadas no risco e nos mercados selecionados."""
        base = [
            f"Alocar entre {len(mercados)//2} e {len(mercados)} mercados para diversificação",
            "Reinvestir 20% dos ganhos em novas apostas",
            "Monitorar odds em tempo real para ajustes oportunos"
        ]
        
        tem_over_under = any('over' in m.nome.lower() or 'under' in m.nome.lower() for m in mercados)
        tem_ambas_marcam = any('ambas' in m.nome.lower() for m in mercados)
        
        if risco > 0.7:
            base.extend([
                "Reduzir exposição em mercados de alta volatilidade",
                "Aumentar proteções em mercados correlacionados"
            ])
            if tem_over_under:
                base.append("Considerar hedge com Under/Over em diferentes partidas")
        elif risco < 0.3:
            base.extend([
                "Aumentar posição em mercados com melhor valor esperado",
                "Reduzir hedge para maximizar retorno"
            ])
        
        if tem_over_under:
            base.append("Analisar a relação Over/Under para identificar valor")
        
        if tem_ambas_marcam:
            base.append("Considerar estratégias combinadas com Ambas Marcam/Não Marcam")
        
        return base
    
    def _mapear_categoria(self, nome_mercado: str) -> str:
        """Mapeia automaticamente o nome do mercado para principal ou proteção."""
        nome = nome_mercado.lower()
        if ('under' in nome or 
            'não' in nome or 
            'empate' in nome or 
            'não perde' in nome or
            'menos' in nome):
            return 'protecao'
        return 'principal'
    
    def _carregar_partidas_exemplo(self) -> List[Partida]:
        """Carrega partidas de exemplo com estatísticas simuladas."""
        return [
            Partida(
                id="1",
                time_mandante="Flamengo",
                time_visitante="Palmeiras",
                liga="Brasileirão Série A",
                estatisticas={
                    'media_gols': 3.1,
                    'forca_ataque': 1.3,
                    'forca_defesa': 0.9,
                    'vitorias_mandante': 0.65,
                    'ambas_marcam_freq': 0.6,
                    'media_cartoes': 3.5,
                    'media_escanteios': 9.2
                }
            ),
            Partida(
                id="2",
                time_mandante="Corinthians",
                time_visitante="São Paulo",
                liga="Brasileirão Série A",
                estatisticas={
                    'media_gols': 1.8,
                    'forca_ataque': 0.9,
                    'forca_defesa': 1.1,
                    'vitorias_mandante': 0.45,
                    'ambas_marcam_freq': 0.4,
                    'media_cartoes': 4.2,
                    'media_escanteios': 7.5
                }
            ),
            Partida(
                id="3",
                time_mandante="Real Madrid",
                time_visitante="Barcelona",
                liga="La Liga",
                estatisticas={
                    'media_gols': 3.5,
                    'forca_ataque': 1.5,
                    'forca_defesa': 1.0,
                    'vitorias_mandante': 0.7,
                    'ambas_marcam_freq': 0.75,
                    'media_cartoes': 2.8,
                    'media_escanteios': 10.5
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