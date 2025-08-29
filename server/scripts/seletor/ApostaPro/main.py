# ADICIONE ESTAS LINHAS NO MUITO INÍCIO do main.py
import sys
import io
import os
from pathlib import Path

# Solução definitiva para encoding no Windows
try:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
except:
    # Fallback seguro se não conseguir alterar o encoding
    pass

# Configuração absoluta dos caminhos
def setup_paths():
    try:
        project_root = Path(__file__).parent.parent.parent
        core_path = project_root / "core"
        frontend_path = project_root / "frontend"
        apps_path = project_root / "apps"
        
        for path in [project_root, core_path, frontend_path, apps_path]:
            if str(path) not in sys.path:
                sys.path.insert(0, str(path))
    except Exception as e:
        print(f"Erro na configuração de caminhos: {e}")

setup_paths()

# Verificação segura (sem emojis se necessário)
try:
    print("✅ Caminhos configurados:")
    print(f"PYTHONPATH: {sys.path}")
    print(f"Diretório atual: {os.getcwd()}")
except UnicodeEncodeError:
    print("[OK] Caminhos configurados:")
    print(f"PYTHONPATH: {sys.path}")
    print(f"Diretorio atual: {os.getcwd()}")

import re
import time
import streamlit as st
import traceback
from datetime import datetime, timedelta
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from typing import List, Optional, Dict, Any, Union, Tuple
from dataclasses import asdict
import hashlib
import requests
import uuid
import json  # Adicione no topo do arquivo com os outros imports

# Altere todos os imports para o caminho completo
from frontend.modules.pre_partida import PrePartida
from frontend.modules.intervalo import GerenciadorIntervalo, ResultadoIntervalo
from frontend.modules.analytics import AnalisadorPrimeiroTempo, ResultadoPrimeiroTempo
from frontend.modules.quantum import QuantumProcessor, QuantumLearner
from frontend.modules.final import GerenciadorFinal, ResultadoFinal
from frontend.modules.multiplas import GerenciadorMultiplas, TipoMultipla, ProjecaoMultipla
from backend.otimizador import OtimizadorMultiplas
from frontend.modules.analise_distribuicao import AnalisadorDistribuicao
from frontend.modules.operacao import QuantumInterface
from frontend.modules.trade import TradingInterface
from backend.protecao import GerenciadorProtecoes
from frontend.config import (
    PrevisaoPartida,
    Config,
    FasePartida,
    TipoAposta,
    CenarioIntervalo,
    CENARIOS,
    MetricasIntervalo
)
        
class PlataformaApostas:
    def __init__(self):
        
        if 'etapa_atual' not in st.session_state:
            st.session_state.etapa_atual = 'config_inicial'
            st.session_state.clear()
            
        self._inicializar_estado()
        self.pre_partida = PrePartida()
        self.analisador = None
        self.gerenciador_intervalo = None
        self.gerenciador_final = None
        self.current_goals = 0
        self.avg_goals = 2.5  # Média histórica padrão
        self.base_goals = 1.0  # Base de referência
        self.quantum_enabled = True
        try:
            from frontend.modules.quantum import QuantumProcessor
            self.quantum_processor = QuantumProcessor()
            
            # Teste com dados protegidos
            test_data = {
                'odds': {'home': 1.8, 'draw': 3.4, 'away': 4.2},
                'placar': '0x0',
                'volatilidade': 0.2
            }
            self.quantum_processor.initialize_market_universe(test_data)
        except Exception as e:
            st.sidebar.error(f"⚠️ Sistema quântico em modo seguro: {str(e)}")
            self.quantum_enabled = False
            self.quantum_processor = None
        
        # Inicializa o gerenciador de múltiplas após o quantum
        self.gerenciador_multiplas = GerenciadorMultiplas()
        if hasattr(self, 'quantum_processor'):
            self.gerenciador_multiplas.quantum_processor = self.quantum_processor
        
    def _plotar_distribuicoes(self, analise):
        """Gera gráfico comparativo das distribuições"""
        import plotly.express as px
    
        # Prepara dados
        df = analise['distribuicao_original'].copy()
        df['Tipo'] = 'Kelly'
        df_prop = analise['distribuicao_proporcional'].copy()
        df_prop['Tipo'] = 'Proporcional'
        combined = pd.concat([df, df_prop])
    
        # Gráfico de barras
        fig = px.bar(
            combined,
            x='Combinação',
            y='Valor (R$)',
            color='Tipo',
            barmode='group',
            title='Comparação de Distribuições',
            hover_data=['Retorno Esperado', 'Probabilidade']
        )
    
        fig.update_layout(
            xaxis_title='Combinações',
            yaxis_title='Valor Alocado (R$)',
            legend_title='Método',
            hovermode='x unified'
        )
    
        return fig
            
    def _apply_quantum_analysis(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """Aplica análise quântica com fallback seguro"""
        if not self.quantum_enabled or not self.quantum_processor:
            return market_data
    
        try:
            # Garante que temos os campos obrigatórios
            if 'odds' not in market_data:
                market_data['odds'] = {}
        
            # Preenche dados padrão se necessário
            market_data.setdefault('placar', st.session_state.get('placar_1t', '0x0'))
            market_data.setdefault('cenario', st.session_state.get('cenario', 'pre_partida'))
        
            # Converte placar se for string
            if isinstance(market_data['placar'], str):
                try:
                    casa, fora = map(int, market_data['placar'].split('x'))
                    market_data['placar'] = {'casa': casa, 'fora': fora}
                except:
                    market_data['placar'] = {'casa': 0, 'fora': 0}
        
            return self.quantum_processor.initialize_market_universe(market_data)
    
        except Exception as e:
            print(f"Análise quântica não aplicada: {str(e)}")
            return market_data
            
    def _apply_quantum_adjustments(self):
        """Versão segura com tratamento de números complexos"""
        if not self.quantum_enabled or not hasattr(self, 'quantum_learner'):
            return {'current': 1.0, 'resonance': 1.0, 'base': 1.0, 'phase': 100, 'factor': 1.0}

        try:
            placar = st.session_state.get('placar_1t', '0x0')
            try:
                gols_casa, gols_fora = map(int, placar.split('x'))
            except:
                gols_casa, gols_fora = 0, 0
        
            # Garante valores positivos para cálculos
            total_gols = max(0, gols_casa + gols_fora)
            diferenca = max(0, abs(gols_casa - gols_fora))
        
            # Cálculo seguro da fase quântica
            phase = self.quantum_learner.fluid_percentage(
                current=max(0.1, total_gols * 1.5),
                resonance=max(0.1, diferenca * 2.0),
                base=max(1, total_gols - diferenca)
            )
        
            # Garante que o fator está entre 0.7 e 1.3
            quantum_factor = min(1.3, max(0.7, 0.7 + (phase / 166.67)))
        
            return {
                'current': float(total_gols),
                'resonance': float(diferenca),
                'base': float(max(1, total_gols - diferenca)),
                'phase': float(phase),
                'factor': float(quantum_factor)
            }
        
        except Exception as e:
            if Config.DEBUG_MODE:
                print(f"Falha no ajuste quântico: {str(e)}")
            return {'current': 1.0, 'resonance': 1.0, 'base': 1.0, 'phase': 100, 'factor': 1.0}
    
    def _inicializar_estado(self):
        """Inicializa todos os estados necessários"""
        estados_padrao = {
            'etapa_atual': 'config_inicial',
            'capital': Config.CAPITAL_INICIAL,
            'previsao': None,
            'odds': {},
            'distribuicao_pre_partida': {},
            'placar_1t': None,
            'resultado_analise_1t': None,
            'distribuicao_intervalo': {},
            'placar_final': None,
            'resultado_final': None,
            'analise_completa': False,
            'analisador': None,
            'dados_partida': {},   # ✔️ Adicionado
            'historico': []        # ✔️ Adicionado
        }

        for key, value in estados_padrao.items():
            if key not in st.session_state:
                st.session_state[key] = value
    
    def mostrar_interface(self):
        """Controla o fluxo principal da aplicação com precisão quântica"""
        try:
            if self.quantum_enabled and hasattr(self.analisador, '_get_quantum_flux'):
                quantum_data = self._apply_quantum_adjustments()
                st.session_state.quantum_data = quantum_data
        except Exception as e:
            st.sidebar.warning(f"Modo quântico temporariamente desativado: {str(e)}")
            self.quantum_enabled = False

        # Barra lateral com estado atual
        self._mostrar_barra_lateral()

        # Container principal
        with st.container():
            st.title("⚽ Operador Conquistador")
    
            # Verificação de segurança quântica
            if st.session_state.etapa_atual in ['resultado_1t', 'intervalo', 'resultado_final']:
                if not hasattr(self, 'analisador') or self.analisador is None:
                    self._recuperar_analisador()

            # Navegação por etapas com verificações reforçadas
            if st.session_state.etapa_atual == 'config_inicial':
                self._mostrar_configuracao_inicial()
            elif st.session_state.etapa_atual == 'pre_partida':
                self._mostrar_pre_partida()
            elif st.session_state.etapa_atual == 'resultado_1t':
                self._mostrar_resultado_1t()
            elif st.session_state.etapa_atual == 'intervalo':
                self._gerenciar_intervalo_com_verificacoes()
            elif st.session_state.etapa_atual == 'resultado_final':
                self._mostrar_resultado_final()

    def _gerenciar_intervalo_com_verificacoes(self):
        """Gerencia a etapa do intervalo com todas as validações necessárias"""
        # Verificação de dados do 1º tempo
        if 'placar_1t' not in st.session_state:
            st.error("⚠️ Dados do 1º tempo incompletos! Retornando...")
            st.session_state.etapa_atual = 'resultado_1t'
            st.rerun()
    
        # Extrai placar e verifica formato
        try:
            placar = st.session_state.placar_1t
            gols_casa, gols_fora = map(int, placar.split('x'))
        except:
            st.error("Formato de placar inválido! Use o formato NxN (ex: 1x0)")
            st.session_state.etapa_atual = 'resultado_1t'
            st.rerun()
    
        # Determinar cenário correto com base no placar
        cenario_correto = self._determinar_cenario_automatico(gols_casa, gols_fora)
    
        # Corrige automaticamente se o cenário estiver errado
        if cenario_correto and st.session_state.get('cenario') != cenario_correto:
            st.session_state.cenario = cenario_correto
            st.rerun()
    
        # Verificação do capital disponível
        if 'capital_disponivel' not in st.session_state:
            st.error("💰 Capital disponível não definido! Retornando...")
            st.session_state.etapa_atual = 'resultado_1t'
            st.rerun()
    
        # Inicializa o gerenciador de intervalo
        self.gerenciador_intervalo = GerenciadorIntervalo(
            previsao=st.session_state.previsao,
            capital_total=st.session_state.capital_disponivel
        )
        st.session_state.gerenciador_intervalo = self.gerenciador_intervalo
    
        # Mostra a interface do intervalo
        self._mostrar_intervalo()

    def _determinar_cenario_automatico(self, gols_casa: int, gols_fora: int) -> CenarioIntervalo:
        """Determina automaticamente o cenário correto baseado no placar"""
        # Mapeamento completo de cenários
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
            return None  # Para cenários não mapeados, mantém o atual

    def _recuperar_analisador(self):
        """Recupera o analisador da sessão ou reinicia o fluxo"""
        if 'analisador' in st.session_state:
            self.analisador = st.session_state.analisador
        else:
            st.error("⚠️ Configuração quântica incompleta! Reiniciando para pré-partida.")
            st.session_state.etapa_atual = 'pre_partida'
            st.rerun()

    def _gerenciar_intervalo(self):
        """Gerencia a etapa do intervalo com todas as validações"""
        if 'capital_disponivel' not in st.session_state:
            st.error("💰 Capital não definido! Retornando ao 1º tempo.")
            st.session_state.etapa_atual = 'resultado_1t'
            st.rerun()
    
        self.gerenciador_intervalo = GerenciadorIntervalo(
            previsao=st.session_state.previsao,
            capital_total=st.session_state.capital_disponivel
        )
        st.session_state.gerenciador_intervalo = self.gerenciador_intervalo
        self._mostrar_intervalo()
    
    def _mostrar_barra_lateral(self):
        """Barra lateral com controle de navegação e informações"""
        with st.sidebar:
            st.title("⚙ Painel de Controle")
            
            # Mapeamento de etapas
            etapas = [
                {'id': 'config_inicial', 'nome': 'Configuração Inicial'},
                {'id': 'pre_partida', 'nome': 'Pré-Partida'},
                {'id': 'resultado_1t', 'nome': 'Resultado 1º Tempo'},
                {'id': 'intervalo', 'nome': 'Intervalo'},
                {'id': 'resultado_final', 'nome': 'Resultado Final'}
            ]
            
            # Status atual
            st.subheader("Progresso")
            for etapa in etapas:
                if etapa['id'] == st.session_state.etapa_atual:
                    st.info(f"▶ {etapa['nome']}")
                else:
                    st.write(f"- {etapa['nome']}")
            
            # Botão de reiniciar
            if st.button("↻ Reiniciar Plataforma"):
                st.session_state.clear()
                st.rerun()
            
            # Informações resumidas
            if st.session_state.get('previsao'):
                st.divider()
                st.metric("💰 Capital", f"R$ {st.session_state.capital:,.2f}")
                st.metric("🔮 Estratégia", st.session_state.previsao.value)
                
                if st.session_state.get('placar_1t'):
                    st.metric("📊 Placar 1T", st.session_state.placar_1t)
    
    def _mostrar_configuracao_inicial(self):
        """Interface para configuração inicial"""
        st.subheader("🔧 Configuração Inicial")
        
        # Configuração básica usando o módulo PrePartida
        config = self.pre_partida._mostrar_selecao_inicial()
        
        # Botão para avançar
        if st.button("Iniciar Configuração de Apostas", type="primary"):
            if st.session_state.capital >= Config.CAPITAL_INICIAL and st.session_state.previsao:
                st.session_state.etapa_atual = 'pre_partida'
                st.rerun()
            else:
                st.warning("Defina o capital e a estratégia antes de continuar")
    
    def _mostrar_pre_partida(self):
        """Gerencia toda a configuração de pré-partida"""
        st.subheader("📊 Configuração de Pré-Partida")

        # Mostra a interface de pré-partida e obtém os resultados
        resultado = self.pre_partida.mostrar_interface()

        # Se a pré-partida foi concluída (retornou dados)
        if resultado:
            # Aplica ajuste quântico apenas se estiver ativado
            if hasattr(self, 'quantum_processor'):
                try:
                    resultado['odds'] = self._apply_quantum_analysis({
                        'odds': resultado['odds'],
                        'volatility': resultado.get('volatility', {})
                    })['odds']
                except Exception as e:
                    st.sidebar.warning(f"Ajuste quântico não aplicado: {str(e)}")

            st.session_state.update({
                'capital': resultado['capital'],
                'previsao': resultado['previsao'],
                'odds': resultado['odds'],
                'distribuicao_pre_partida': resultado['distribuicao']
            })
        
            # Inicializa e armazena o analisador na sessão
            st.session_state.analisador = AnalisadorPrimeiroTempo(
                previsao=st.session_state.previsao,
                odds=st.session_state.odds,
                distribuicao=st.session_state.distribuicao_pre_partida
            )
        
            # Atualiza também o atributo da instância
            self.analisador = st.session_state.analisador
        
            st.session_state.etapa_atual = 'resultado_1t'
            st.rerun()
    
    def _mostrar_resultado_1t(self):
        """Interface para registro e análise do 1º tempo"""
        st.subheader("⏱ Resultado do 1º Tempo")

        # Verificação essencial do analisador
        if not hasattr(self, 'analisador') or self.analisador is None:
            st.error("Analisador não configurado. Volte para a pré-partida.")
            if st.button("Voltar para Pré-Partida"):
                st.session_state.etapa_atual = 'pre_partida'
                st.rerun()
            return

        # Se ainda não tem placar definido, mostra seletor
        if not st.session_state.placar_1t:
            opcoes_placar = ["0x0", "1x0", "2x0", "2x1", "1x1", "0x1", "0x2", "1x2"]
            placar = st.selectbox("Selecione o placar do 1º tempo:", options=opcoes_placar)
        
            if st.button("Analisar 1º Tempo", type="primary"):
                st.session_state.placar_1t = placar
                st.rerun()
            return
    
        # Se tem placar mas não tem análise, processa
        if not st.session_state.resultado_analise_1t:
            try:
                resultado = self.analisador.analisar_placar(st.session_state.placar_1t)
                st.session_state.resultado_analise_1t = resultado
            
                # Gera e armazena o relatório na sessão
                relatorio = self.analisador.gerar_relatorio(resultado)
                st.session_state.relatorio_1t = relatorio
            
                st.rerun()
            except Exception as e:
                st.error(f"Erro na análise: {str(e)}")
                if st.button("Tentar novamente"):
                    st.rerun()
                return
    
        # Se já tem análise, mostra relatório
        if hasattr(st.session_state, 'relatorio_1t'):
            self._mostrar_relatorio_1t(st.session_state.relatorio_1t)
    
            # Botão para avançar para o intervalo
        if st.button("Avançar para Intervalo", type="primary"):
            # Calcula capital disponível considerando apostas em aberto
            capital_disponivel = st.session_state.capital - sum(st.session_state.distribuicao_pre_partida.values())
            st.session_state.capital_disponivel = capital_disponivel  # Armazena na sessão
    
            # Define o cenário
            st.session_state.cenario = self.analisador.determinar_cenario_intervalo(st.session_state.placar_1t)
    
            # Inicializa o gerenciador de intervalo
            self.gerenciador_intervalo = GerenciadorIntervalo(
                previsao=st.session_state.previsao,
                capital_total=capital_disponivel
            )
            st.session_state.gerenciador_intervalo = self.gerenciador_intervalo
            st.session_state.etapa_atual = 'intervalo'
            st.rerun()

    def _mostrar_entrada_placar_1t(self):
        """Mostra interface para entrada do placar do 1º tempo"""
        placar = st.text_input(
            "Digite o placar do 1º tempo (formato: NxN)",
            key="input_placar_1t",
            help="Exemplo: 1x0, 2x1, 0x0"
        )
        
        if st.button("Confirmar Placar", type="primary"):
            if placar and 'x' in placar:
                try:
                    gols_casa, gols_fora = map(int, placar.split('x'))
                    st.session_state.placar_1t = placar
                    st.rerun()
                except ValueError:
                    st.error("Formato inválido! Use apenas números no formato NxN")
            else:
                st.error("Digite um placar válido no formato NxN")
    
    def _processar_resultado_1t(self):
        """Processa o resultado do primeiro tempo"""
        if 'placar_1t' not in st.session_state or not st.session_state.placar_1t:
            st.error("Placar do 1º tempo não definido!")
            return None
    
        # Garante que o analisador está disponível
        if not hasattr(self, 'analisador') or self.analisador is None:
            if 'analisador' in st.session_state:
                self.analisador = st.session_state.analisador
            else:
                st.error("Analisador não inicializado! Complete a pré-partida primeiro.")
                st.session_state.etapa_atual = 'pre_partida'
                st.rerun()
                return None
    
        try:
            # Verifica o formato do placar
            if not re.match(r'^\d+x\d+$', st.session_state.placar_1t):
                st.error("Formato de placar inválido! Use o formato 0x0, 1x0, etc.")
                return None
            
            resultado = self.analisador.analisar_placar(st.session_state.placar_1t)
            st.session_state.resultado_analise_1t = resultado
        
            # Gera e exibe o relatório imediatamente
            relatorio = self.analisador.gerar_relatorio(resultado)
            self._mostrar_relatorio_1t(relatorio)
        
            return resultado
        except Exception as e:
            st.error(f"Erro ao analisar placar: {str(e)}")
            return None
    
    def _processar_resultado_1t(self):
        """Processa o resultado do 1º tempo de forma direta"""
        try:
            # Garante que o analisador está inicializado
            if not hasattr(self, 'analisador') or self.analisador is None:
                self.reiniciar_analisador()
        
            # Processa a análise
            st.session_state.resultado_analise_1t = self.analisador.analisar_placar(st.session_state.placar_1t)
            st.rerun()
        except Exception as e:
            st.error(f"Erro ao processar: {str(e)}")
            st.session_state.etapa_atual = 'pre_partida'
            st.rerun()
    
    def _mostrar_analise_1t(self):
        """Mostra a análise do 1º tempo a partir dos dados em session_state"""
        if not st.session_state.resultado_analise_1t:
            return
        
        # Converte o resultado para dict se necessário
        if not isinstance(st.session_state.resultado_analise_1t, dict):
            relatorio = asdict(st.session_state.resultado_analise_1t)
        else:
            relatorio = st.session_state.resultado_analise_1t
        
        self._mostrar_relatorio_1t(relatorio)
        
    def _mostrar_relatorio_1t(self, relatorio: dict):
        """Mostra o relatório completo do 1º tempo com distribuição para o intervalo"""
        st.subheader("📈 Relatório do 1º Tempo")
    
        # Métricas principais
        col1, col2 = st.columns(2)
        col1.metric("Placar", relatorio['placar'])
        col2.metric("Cenário", relatorio['cenario'])
    
        # Resumo financeiro
        st.subheader("💰 Resumo Financeiro")
        cols = st.columns(3)
        cols[0].metric("Investido", f"R$ {relatorio['capital_investido']:.2f}")
        cols[1].metric("Retorno 1T", f"R$ {relatorio['retorno_1t']:.2f}")
        cols[2].metric("Disponível", f"R$ {relatorio['capital_disponivel']:.2f}")
    
        # Apostas
        st.subheader("📊 Status das Apostas")
    
        tab1, tab2, tab3 = st.tabs(["✅ Ganhas", "❌ Perdidas", "⏳ Em Aberto"])
    
        with tab1:
            if relatorio['apostas_ganhas']:
                st.dataframe(pd.DataFrame.from_dict(
                    relatorio['apostas_ganhas'], 
                    orient='index',
                    columns=['Retorno (R$)']
                ).style.format("{:.2f}"))
            else:
                st.info("Nenhuma aposta ganha no 1º tempo")
    
        with tab2:
            if relatorio['apostas_perdidas']:
                st.dataframe(pd.DataFrame.from_dict(
                    relatorio['apostas_perdidas'], 
                    orient='index',
                    columns=['Perda (R$)']
                ).style.format("{:.2f}"))
            else:
                st.info("Nenhuma aposta perdida no 1º tempo")
    
        with tab3:
            if relatorio['apostas_em_aberto']:
                st.dataframe(pd.DataFrame.from_dict(
                    relatorio['apostas_em_aberto'], 
                    orient='index',
                    columns=['Valor em Risco (R$)']
                ).style.format("{:.2f}"))
            else:
                st.info("Nenhuma aposta em aberto")
    
        # Recomendações para o intervalo
        st.subheader("🎯 Distribuição Recomendada para o Intervalo")
    
        if relatorio['recomendacao_intervalo']:
            df_recomendacao = pd.DataFrame.from_dict(
                relatorio['recomendacao_intervalo'],
                orient='index',
                columns=['Valor (R$)']
            )
            st.dataframe(df_recomendacao.style.format("{:.2f}"))
        
            # Gráfico de distribuição
            fig, ax = plt.subplots()
            ax.pie(
                df_recomendacao['Valor (R$)'],
                labels=df_recomendacao.index,
                autopct='%1.1f%%',
                startangle=90
            )
            ax.axis('equal')
            st.pyplot(fig)
        else:
            st.warning("Nenhuma recomendação disponível para este cenário")
    
        # Observações estratégicas
        st.subheader("📌 Análise Estratégica")
        st.info(relatorio['observacoes'])
    
    def _mostrar_intervalo(self):
        """Interface para configuração do intervalo"""
        st.subheader("🔄 Configuração do Intervalo")

        # Verificação de segurança para o gerenciador de intervalo
        if not hasattr(self, 'gerenciador_intervalo') or self.gerenciador_intervalo is None:
            if all(k in st.session_state for k in ['previsao', 'capital_disponivel']):
                self.gerenciador_intervalo = GerenciadorIntervalo(
                    previsao=st.session_state.previsao,
                    capital_total=st.session_state.capital_disponivel
                )
            else:
                st.error("Dados incompletos para inicializar o gerenciador de intervalo!")
                if st.button("Voltar para análise do 1º tempo"):
                    st.session_state.etapa_atual = 'resultado_1t'
                    st.rerun()
                return

        # Obtém o resultado da configuração
        resultado = self.gerenciador_intervalo.mostrar_interface()

        if resultado:
            # Aplica análise quântica se disponível
            if hasattr(self, 'quantum_processor'):
                try:
                    quantum_adjusted = self._apply_quantum_analysis({
                        'odds': resultado.odds_2t,
                        'scenarios': [st.session_state.cenario]
                    })
                    resultado.odds_2t = quantum_adjusted['odds']
                except Exception as e:
                    st.sidebar.warning(f"Ajuste quântico não aplicado: {str(e)}")

            st.session_state.update({
                'distribuicao_intervalo': resultado.distribuicao_2t,
                'odds_2t': resultado.odds_2t,
                'risco_atual': resultado.risco_atual
            })
        
            # BOTÃO CRÍTICO - Deve ser o ÚLTIMO elemento da interface
            if st.button("⏩ Avançar para Resultado Final", 
                        type="primary", 
                        key="btn_avancar_final_unico",  # Chave única fixa
                        on_click=lambda: setattr(st.session_state, 'etapa_atual', 'resultado_final')):
                st.rerun()  # Força atualização imediata
    
    def _mostrar_resultado_final(self):
        """Interface completa para resultado final"""
        if not hasattr(self, 'gerenciador_final'):
            self.gerenciador_final = GerenciadorFinal()

        # Se não tem placar final definido, mostra interface de entrada
        if not st.session_state.get('placar_final'):
            self._mostrar_entrada_placar_final()
            return

        # Se tem placar mas não processou ainda, processa
        if not st.session_state.get('analise_completa', False):
            self._processar_resultado_final()
            return

        st.subheader("🏁 Resultado Final Completo")

        # Criar abas para organização
        tab1, tab2, tab3 = st.tabs(["📊 Resumo Financeiro", "📈 Detalhes das Apostas", "🔍 Análise Quântica"])

        with tab1:
            self._mostrar_resumo_financeiro()
    
        with tab2:
            self._mostrar_detalhes_apostas()
    
        with tab3:
            self._mostrar_analise_quantica()

        # Botão de reinício
        st.divider()
        if st.button("↻ Realizar Nova Análise", type="secondary"):
            st.session_state.analise_completa = False
            st.session_state.placar_final = None
            st.rerun()
            
    def _mostrar_entrada_placar_final(self):
        """Mostra interface para entrada do placar final com validação robusta"""
        placar = st.text_input(
            "Digite o placar FINAL (formato: NxN ou N x N)",
            key="input_placar_final",
            help="Exemplo: 2x1, 1x1, 0x3, 1 x 0"
        ).strip()  # Remove espaços no início e fim

        if st.button("Calcular Resultados Finais", type="primary"):
            # Padroniza o formato (remove espaços e padroniza o 'x')
            placar = placar.replace(' ', '').lower()
    
            if placar and 'x' in placar:
                try:
                    # Verifica se tem exatamente um 'x' e números válidos
                    partes = placar.split('x')
                    if len(partes) == 2 and partes[0].isdigit() and partes[1].isdigit():
                        gols_casa = int(partes[0])
                        gols_fora = int(partes[1])
                        st.session_state.placar_final = f"{gols_casa}x{gols_fora}"
                        st.rerun()
                    else:
                        st.error("Formato inválido! Use apenas números no formato NxN (ex: 1x0)")
                except ValueError:
                    st.error("Valores inválidos! Use apenas números no formato NxN (ex: 1x0)")
            else:
                st.error("Digite um placar válido no formato NxN (ex: 1x0)")
    
    def _processar_resultado_final(self):
        """Processa o resultado final com inicialização quântica"""
        try:
            # Inicializa universo quântico se disponível
            if hasattr(self, 'quantum_processor') and self.quantum_processor:
                if self.quantum_processor.current_universe is None:
                    self._initialize_quantum_analysis()
            
            # Verificação básica do placar
            if not st.session_state.get('placar_final'):
                raise ValueError("Placar final não definido")

            placar_final = st.session_state.placar_final.replace(' ', '').lower()
            if not re.match(r'^\d+x\d+$', placar_final):
                raise ValueError("Formato de placar final inválido")

            # Extração dos placares
            placar_1t = st.session_state.placar_1t.replace(' ', '').lower()

            gols_casa_final, gols_fora_final = map(int, placar_final.split('x'))
            gols_casa_1t, gols_fora_1t = map(int, placar_1t.split('x'))

            # Cálculos totais
            total_gols = gols_casa_final + gols_fora_final
            total_gols_1t = gols_casa_1t + gols_fora_1t
            total_gols_2t = total_gols - total_gols_1t

            # Validação temporal
            if total_gols < total_gols_1t:
                raise ValueError("Total de gols final não pode ser menor que o 1º tempo")

            # Cálculo dos retornos
            retornos_1t = self._calcular_retornos_1t(total_gols, total_gols_1t, gols_casa_1t, gols_fora_1t)
            retornos_2t = self._calcular_retornos_2t(total_gols_2t, gols_fora_final, gols_fora_1t)

            # Atualização do estado
            st.session_state.update({
                'retornos_1t': retornos_1t,
                'retornos_2t': retornos_2t,
                'total_investido': sum(st.session_state.distribuicao_pre_partida.values()) + 
                                 sum(st.session_state.distribuicao_intervalo.values()),
                'total_retorno': sum(retornos_1t.values()) + sum(retornos_2t.values()) +
                               sum(st.session_state.distribuicao_pre_partida.values()) +
                               sum(st.session_state.distribuicao_intervalo.values()),
                'lucro_prejuizo': sum(retornos_1t.values()) + sum(retornos_2t.values()),
                'analise_completa': True
            })

            st.rerun()

        except Exception as e:
            st.error(f"Erro na análise final: {str(e)}")
            st.session_state.analise_completa = False

            # Debug detalhado
            debug_info = {
                'placar_final': st.session_state.get('placar_final', 'NULO'),
                'placar_1t': st.session_state.get('placar_1t', 'NULO'),
                'erro': str(e),
                'distribuicao_pre_partida': st.session_state.get('distribuicao_pre_partida', {}),
                'odds': st.session_state.get('odds', {})
            }
            st.write("Estado atual para diagnóstico:", debug_info)
            
    def _formatar_placar(placar: str) -> str:
        """Padroniza o formato do placar para NxN"""
        placar = placar.strip().replace(' ', '').lower()
        if not re.match(r'^\d+[xX]\d+$', placar):
            raise ValueError("Formato inválido")
        return placar
    
    def _initialize_quantum_analysis(self):
        """Inicializa a análise quântica com dados da sessão de forma segura"""
        if not hasattr(self, 'quantum_processor') or not self.quantum_processor:
            return

        try:
            # Garante que os odds estão no formato correto
            odds = st.session_state.get('odds', {})
            processed_odds = {k: float(v) for k, v in odds.items() if isinstance(v, (int, float, str))}
        
            # Prepara dados para o universo quântico
            quantum_data = {
                'odds': processed_odds,
                'placar': self._parse_placar(st.session_state.get('placar_1t', '0x0')),
                'cenario': st.session_state.get('cenario', 'padrao'),
                'volatilidade': self._get_volatilidade()
            }
        
            # Inicialização segura com verificação de dimensões
            self.quantum_processor.initialize_market_universe(quantum_data)

        except ValueError as ve:
            st.error(f"Erro nos dados de entrada: {str(ve)}")
        except Exception as e:
            self._handle_quantum_error(e)
    
    def _calcular_retornos_1t(self, total_gols: int, total_gols_1t: int, 
                             gols_casa_1t: int, gols_fora_1t: int) -> Dict[TipoAposta, float]:
        """Calcula os retornos das apostas do 1º tempo com análise quântica completa"""
        retornos = {}
    
        # Extrai placar final com segurança
        try:
            gols_casa_final, gols_fora_final = map(int, st.session_state.placar_final.split('x'))
        except:
            gols_casa_final, gols_fora_final = gols_casa_1t, gols_fora_1t
    
        # Ajuste quântico
        quantum_factor = self._get_quantum_factor(gols_casa_1t, gols_fora_1t, gols_casa_final, gols_fora_final)
    
        for aposta, valor in st.session_state.distribuicao_pre_partida.items():
            odd = st.session_state.odds.get(aposta, 1.0)
        
            # Aplica fator quântico às odds
            adjusted_odd = odd * quantum_factor.get(aposta, 1.0)
        
            if aposta == TipoAposta.MAIS_25_GOLS:
                retorno = -valor if total_gols <= 2.5 else valor * (adjusted_odd - 1)
        
            elif aposta == TipoAposta.MENOS_25_GOLS:
                retorno = valor * (adjusted_odd - 1) if total_gols < 2.5 else -valor
        
            elif aposta == TipoAposta.AMBAS_MARCAM_NAO:
                ambas_marcaram = (gols_casa_final > 0) and (gols_fora_final > 0)
                retorno = valor * (adjusted_odd - 1) if not ambas_marcaram else -valor
        
            elif aposta == TipoAposta.AMBAS_MARCAM_SIM:
                ambas_marcaram = (gols_casa_final > 0) and (gols_fora_final > 0)
                retorno = valor * (adjusted_odd - 1) if ambas_marcaram else -valor
        
            elif aposta == TipoAposta.MENOS_15_GOLS:
                retorno = valor * (adjusted_odd - 1) if total_gols < 1.5 else -valor
        
            elif aposta == TipoAposta.VENCEDOR_FAVORITO:
                retorno = valor * (adjusted_odd - 1) if gols_casa_final > gols_fora_final else -valor
        
            elif aposta == TipoAposta.MENOS_05_GOLS:
                retorno = -valor if total_gols > 0 else valor * (adjusted_odd - 1)
        
            else:
                retorno = -valor
        
            retornos[aposta] = round(retorno, 2)
    
        return retornos
    
    def _get_quantum_factor(self, gols_casa_1t, gols_fora_1t, gols_casa_final, gols_fora_final):
        """Calcula fatores quânticos baseados na evolução do placar"""
        total_1t = gols_casa_1t + gols_fora_1t
        total_final = gols_casa_final + gols_fora_final
        diff_1t = abs(gols_casa_1t - gols_fora_1t)
        diff_final = abs(gols_casa_final - gols_fora_final)
    
        # Fator dinâmico baseado na mudança do placar
        momentum_factor = 1 + (total_final - total_1t) / 10
        balance_factor = 1 - (diff_final - diff_1t) / 20
    
        return {
            TipoAposta.MAIS_25_GOLS: min(1.3, max(0.7, momentum_factor)),
            TipoAposta.MENOS_25_GOLS: min(1.3, max(0.7, 2 - momentum_factor)),
            TipoAposta.AMBAS_MARCAM_SIM: min(1.3, max(0.7, balance_factor)),
            TipoAposta.AMBAS_MARCAM_NAO: min(1.3, max(0.7, 2 - balance_factor)),
            TipoAposta.VENCEDOR_FAVORITO: min(1.2, max(0.8, 1 + (diff_final - diff_1t)/20))
        }

    def _calcular_retornos_2t(self, total_gols_2t: int, gols_fora_final: int, gols_fora_1t: int) -> Dict[TipoAposta, float]:
        """Calcula os retornos das apostas do 2º tempo com regras corrigidas"""
        retornos = {}
    
        # Extrai os gols do placar final
        gols_casa_final, gols_fora_final = map(int, st.session_state.placar_final.split('x'))
        # Extrai os gols do 1º tempo
        gols_casa_1t, gols_fora_1t = map(int, st.session_state.placar_1t.split('x'))
    
        # Calcula se ambos marcaram na partida inteira
        ambas_marcaram_partida = (gols_casa_final > 0) and (gols_fora_final > 0)
    
        for aposta, valor in st.session_state.distribuicao_intervalo.items():
            odd = st.session_state.odds_2t.get(aposta, 1.0)
        
            if aposta == TipoAposta.MAIS_15_SEGUNDO_TEMPO:
                retorno = valor * (odd - 1) if total_gols_2t > 1.5 else -valor
        
            elif aposta == TipoAposta.MENOS_15_SEGUNDO_TEMPO:
                retorno = valor * (odd - 1) if total_gols_2t < 1.5 else -valor
        
            elif aposta == TipoAposta.MAIS_05_SEGUNDO_TEMPO:
                retorno = valor * (odd - 1) if total_gols_2t > 0.5 else -valor
        
            elif aposta == TipoAposta.NAO_SAIR_MAIS_GOLS:
                retorno = valor * (odd - 1) if total_gols_2t == 0 else -valor
        
            elif aposta == TipoAposta.PROXIMO_GOL_AZARAO:
                # Azarão é o time que marcou menos gols no 1º tempo
                azarao_1t = gols_casa_1t < gols_fora_1t
                gol_azarao_2t = (gols_casa_final > gols_casa_1t) if azarao_1t else (gols_fora_final > gols_fora_1t)
                retorno = valor * (odd - 1) if gol_azarao_2t else -valor
        
            elif aposta == TipoAposta.AMBAS_MARCAM_SIM:
                # Ambas marcam SIM se ambos marcarem em qualquer momento da partida
                retorno = valor * (odd - 1) if ambas_marcaram_partida else -valor
        
            elif aposta == TipoAposta.AMBAS_MARCAM_NAO:
                # Ambas marcam NÃO se pelo menos um não marcar na partida
                retorno = valor * (odd - 1) if not ambas_marcaram_partida else -valor
        
            else:
                retorno = -valor
        
            retornos[aposta] = round(retorno, 2)
    
        return retornos
    
    def _initialize_quantum_system(self):
        """Inicializa o sistema quântico com fallback seguro"""
        try:
            self.quantum_processor = QuantumProcessor()
            st.session_state.setdefault('quantum_initialized', True)
        except Exception as e:
            st.error(f"Erro na inicialização quântica: {str(e)}")
            self.quantum_processor = None
            st.session_state['quantum_initialized'] = False
    
    def _verificar_consistencia_quantica(self):
        """Verificação quântica completa dos dados"""
        required_keys = [
            'placar_final', 'placar_1t',
            'distribuicao_pre_partida', 'distribuicao_intervalo',
            'odds', 'odds_2t'
        ]
    
        missing_keys = [k for k in required_keys if k not in st.session_state]
        if missing_keys:
            raise ValueError(f"Dados quânticos faltando: {', '.join(missing_keys)}")
    
        if not re.match(r'^\d+x\d+$', st.session_state.placar_final.replace(" ", "")):
            raise ValueError("Formato quântico inválido para placar final")
    
        if not re.match(r'^\d+x\d+$', st.session_state.placar_1t.replace(" ", "")):
            raise ValueError("Formato quântico inválido para placar do 1º tempo")
    
    def _mostrar_analise_completa(self, resultado):
        """Exibe análise completa com consistência quântica"""
        st.subheader("📊 Análise Quântica Completa")

        # Resumo financeiro com verificação
        lucro = st.session_state.get('lucro_prejuizo', 0)
        investido = st.session_state.get('total_investido', 1)
        percentual = (lucro / investido) * 100 if investido > 0 else 0

        cols = st.columns(3)
        cols[0].metric("Total Investido", f"R$ {investido:,.2f}")
        cols[1].metric("Retorno Total", f"R$ {st.session_state.get('total_retorno', 0):,.2f}")
        cols[2].metric("Resultado Final", 
                      f"R$ {lucro:,.2f}",
                      delta=f"{percentual:.1f}%",
                      delta_color="normal" if lucro >= 0 else "inverse")

        # Tabela comparativa quântica
        self._mostrar_tabela_quantica()
        
    def _mostrar_resumo_financeiro(self):
        """Mostra o resumo financeiro completo"""
        cols = st.columns(3)
        cols[0].metric("💰 Capital Inicial", f"R$ {st.session_state.capital:,.2f}")
        cols[1].metric("💸 Total Investido", f"R$ {st.session_state.total_investido:,.2f}")
        cols[2].metric("🏆 Lucro/Prejuízo", 
                      f"R$ {st.session_state.lucro_prejuizo:,.2f}",
                      delta=f"{st.session_state.lucro_prejuizo/st.session_state.total_investido*100:.1f}%" 
                      if st.session_state.total_investido else "0%")

    def _mostrar_detalhes_apostas(self):
        """Mostra detalhes de todas as apostas"""
        st.subheader("📝 Detalhes das Apostas")
    
        # Apostas do 1º tempo
        st.markdown("**1º Tempo**")
        df_1t = pd.DataFrame({
            'Aposta': [aposta.value for aposta in st.session_state.distribuicao_pre_partida.keys()],
            'Valor (R$)': st.session_state.distribuicao_pre_partida.values(),
            'Odd': [st.session_state.odds.get(aposta, 1.0) for aposta in st.session_state.distribuicao_pre_partida.keys()],
            'Resultado': ["Ganhou" if st.session_state.retornos_1t.get(aposta, 0) >= 0 else "Perdeu" 
                          for aposta in st.session_state.distribuicao_pre_partida.keys()],
            'Retorno (R$)': [st.session_state.retornos_1t.get(aposta, 0) 
                             for aposta in st.session_state.distribuicao_pre_partida.keys()]
        })
        st.dataframe(df_1t.style.format({
            'Valor (R$)': "{:.2f}",
            'Odd': "{:.2f}",
            'Retorno (R$)': "{:+.2f}"
        }))
    
        # Apostas do Intervalo (2º tempo)
        if 'distribuicao_intervalo' in st.session_state and 'retornos_2t' in st.session_state:
            st.markdown("**2º Tempo**")
            df_2t = pd.DataFrame({
                'Aposta': [aposta.value for aposta in st.session_state.distribuicao_intervalo.keys()],
                'Valor (R$)': st.session_state.distribuicao_intervalo.values(),
                'Odd': [st.session_state.odds_2t.get(aposta, 1.0) for aposta in st.session_state.distribuicao_intervalo.keys()],
                'Resultado': ["Ganhou" if st.session_state.retornos_2t.get(aposta, 0) >= 0 else "Perdeu" 
                              for aposta in st.session_state.distribuicao_intervalo.keys()],
                'Retorno (R$)': [st.session_state.retornos_2t.get(aposta, 0) 
                                 for aposta in st.session_state.distribuicao_intervalo.keys()]
            })
            st.dataframe(df_2t.style.format({
                'Valor (R$)': "{:.2f}",
                'Odd': "{:.2f}",
                'Retorno (R$)': "{:+.2f}"
            }))
            
    def _parse_placar(self, placar: str) -> Dict[str, int]:
        """Converte o placar para formato numérico seguro"""
        try:
            gols_casa, gols_fora = map(int, placar.split('x'))
            return {'casa': gols_casa, 'fora': gols_fora}
        except:
            return {'casa': 0, 'fora': 0}

    def _get_volatilidade(self) -> Dict[str, float]:
        """Calcula a volatilidade baseada nos dados da sessão"""
        return {
            'pre_partida': st.session_state.get('volatilidade_pre_partida', 0.2),
            'intervalo': st.session_state.get('volatilidade_intervalo', 0.3),
            'final': st.session_state.get('volatilidade_final', 0.25)
        }

    def _handle_quantum_error(self, error: Exception):
        """Tratamento centralizado de erros quânticos"""
        error_msg = str(error)
    
        if "incompatibilidade de forma" in error_msg:
            st.warning("""
            🔄 Reconfigurando matrizes quânticas...
        
            O sistema detectou uma inconsistência nas dimensões dos dados.
            Isso está sendo corrigido automaticamente.
            """)
            self._reset_quantum_processor()
            st.rerun()
        else:
            st.error(f"Erro quântico: {error_msg}")
        
        if Config.DEBUG_MODE:
            st.write("Detalhes técnicos:", error_msg)

    def _mostrar_analise_quantica(self):
        """Mostra análise quântica com tratamento robusto de erros"""
        st.subheader("🌀 Análise Multiversal")
    
        # Verificação inicial mais rigorosa
        if not hasattr(self, 'quantum_processor') or not self.quantum_processor:
            st.warning("🔴 Sistema quântico não disponível - Reinicie o sistema")
            if st.button("Tentar reinicialização quântica"):
                try:
                    self.quantum_processor = QuantumProcessor()
                    st.rerun()
                except Exception as e:
                    st.error(f"Falha na reinicialização: {str(e)}")
            return

        try:
            # Verificação de dados mínimos
            required_keys = ['placar_1t', 'odds', 'previsao']
            if not all(k in st.session_state for k in required_keys):
                st.warning("⚠️ Dados insuficientes para análise quântica")
                return

            # Mostrar loader durante o processamento
            with st.spinner("🔄 Calculando probabilidades quânticas..."):
                # Verifica e inicializa se necessário
                if self.quantum_processor.current_universe is None:
                    self._initialize_quantum_analysis()
            
                # Limita o tempo de processamento
                import time
                start_time = time.time()
                timeout = 5  # segundos
            
                while self.quantum_processor.current_universe is None and (time.time() - start_time) < timeout:
                    time.sleep(0.1)
            
                if self.quantum_processor.current_universe is None:
                    raise TimeoutError("Tempo excedido na inicialização quântica")
            
                # Obtém o estado atual com verificação
                universe_state = self.quantum_processor.get_universe_state()
                if not universe_state:
                    raise ValueError("Estado quântico vazio")

            # Visualização da matriz quântica com tamanho limitado
            with st.expander("📊 Matriz de Probabilidades (Top 5x5)"):
                prob_matrix = universe_state.get('probability_matrix', np.eye(2))
                # Limita o tamanho para performance
                size = min(5, prob_matrix.shape[0])
                self._plot_quantum_matrix(prob_matrix[:size, :size])

            # Recomendações simplificadas
            with st.expander("📈 Recomendações Quânticas"):
                recs = universe_state.get('recommendations', {})
                if recs:
                    df = pd.DataFrame.from_dict(recs, orient='index', columns=['Força'])
                    st.dataframe(df.nlargest(5, 'Força').style.format("{:.4f}"))
                else:
                    st.info("Nenhuma recomendação disponível")

        except TimeoutError:
            st.error("⏱️ Análise quântica excedeu o tempo limite")
            self.quantum_processor = None  # Reseta o processador
        
        except Exception as e:
            st.error(f"❌ Erro na análise quântica: {str(e)}")
            if Config.DEBUG_MODE:
                st.exception(e)
    
    def _mostrar_tabela_quantica(self):
        """Mostra tabela com consistência entre intervalo e final"""
        dados = []

        # Processa apostas do 1º tempo
        for aposta, valor in st.session_state.distribuicao_pre_partida.items():
            resultado = "Ganhou" if st.session_state.retornos_1t.get(aposta, 0) >= 0 else "Perdeu"
            dados.append({
                "Fase": "1º Tempo",
                "Aposta": aposta.value,
                "Valor": f"R$ {valor:.2f}",
                "Resultado": resultado,
                "Retorno": f"R$ {st.session_state.retornos_1t.get(aposta, 0):+.2f}"
            })

        # Processa apostas do 2º tempo
        for aposta, valor in st.session_state.distribuicao_intervalo.items():
            resultado = "Ganhou" if st.session_state.retornos_2t.get(aposta, 0) >= 0 else "Perdeu"
            dados.append({
                "Fase": "2º Tempo",
                "Aposta": aposta.value,
                "Valor": f"R$ {valor:.2f}",
                "Resultado": resultado,
                "Retorno": f"R$ {st.session_state.retornos_2t.get(aposta, 0):+.2f}"
            })

        df = pd.DataFrame(dados)
        st.dataframe(df, hide_index=True)
    
    def _mostrar_graficos_comparativos(self):
        """Mostra gráficos comparativos de desempenho"""
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
        
        # Gráfico 1: Comparativo Investido vs Retorno
        labels = ['1º Tempo', '2º Tempo']
        investido = [
            sum(st.session_state.distribuicao_pre_partida.values()),
            sum(st.session_state.distribuicao_intervalo.values())
        ]
        retorno = [
            sum(r + st.session_state.distribuicao_pre_partida[a] 
                for a, r in st.session_state.retornos_1t.items()),
            sum(r + st.session_state.distribuicao_intervalo[a] 
                for a, r in st.session_state.retornos_2t.items())
        ]
        
        x = range(len(labels))
        width = 0.35
        
        ax1.bar([i - width/2 for i in x], investido, width, label='Investido', color='#1f77b4')
        ax1.bar([i + width/2 for i in x], retorno, width, label='Retorno', color='#ff7f0e')
        ax1.set_ylabel('Valor (R$)')
        ax1.set_title('Investido vs Retorno por Tempo')
        ax1.set_xticks(x)
        ax1.set_xticklabels(labels)
        ax1.legend()
        
        # Gráfico 2: Lucro/Prejuízo por Tempo
        lucro = [
            sum(st.session_state.retornos_1t.values()),
            sum(st.session_state.retornos_2t.values())
        ]
        
        colors = ['green' if val >= 0 else 'red' for val in lucro]
        ax2.bar(labels, lucro, color=colors)
        ax2.axhline(0, color='black', linewidth=0.8)
        ax2.set_ylabel('Lucro/Prejuízo (R$)')
        ax2.set_title('Resultado Financeiro por Tempo')
        
        st.pyplot(fig)
        
    def _plot_quantum_matrix(self, matrix):
        """Visualização segura da matriz quântica"""
        try:
            fig, ax = plt.subplots(figsize=(8, 6))
            sns.heatmap(matrix, ax=ax, cmap="viridis", annot=True, fmt=".2f")
            ax.set_title("Matriz de Probabilidades Quânticas")
            st.pyplot(fig)
        except:
            st.warning("Visualização da matriz temporariamente indisponível")

    def _show_quantum_recommendations(self, recommendations):
        """Exibe recomendações formatadas"""
        if not recommendations:
            st.info("Nenhuma recomendação quântica disponível")
            return
    
        df = pd.DataFrame.from_dict(recommendations, orient='index', columns=['Força Quântica'])
        st.dataframe(
            df.style.format("{:.4f}").background_gradient(cmap="viridis").highlight_max(color='green')
        )
    
        # Análise interpretativa
        max_rec = df['Força Quântica'].idxmax()
        st.info(f"📌 Recomendação quântica mais forte: **{max_rec}**")
    
    def reiniciar_analisador(self):
        """Reinicia o analisador com os dados atuais da sessão"""
        if all(k in st.session_state for k in ['previsao', 'odds', 'distribuicao_pre_partida']):
            self.analisador = AnalisadorPrimeiroTempo(
                previsao=st.session_state.previsao,
                odds=st.session_state.odds,
                distribuicao=st.session_state.distribuicao_pre_partida
            )
            st.session_state.analisador = self.analisador
        else:
            self.analisador = None
            st.session_state.analisador = None
            
    def _calculate_quantum_correlation(self, projecao: ProjecaoMultipla) -> np.ndarray:
        """Calcula a correlação quântica entre partidas"""
        num_partidas = len(projecao.partidas)
        corr_matrix = np.zeros((num_partidas, num_partidas))
    
        for i in range(num_partidas):
            for j in range(num_partidas):
                if i == j:
                    corr_matrix[i,j] = 1.0
                else:
                    corr_matrix[i,j] = self.quantum_processor.get_correlacao(
                        i, j, projecao.tipo.value
                    )
    
        return corr_matrix

    def _gerar_estrategias_quanticas(self, projecao: ProjecaoMultipla) -> List[Dict]:
        """Gera estratégias baseadas em análise quântica"""
        estrategias = []
    
        # Estratégia 1: Maximizar entropia
        entropia = self.quantum_processor.calcular_entropia(projecao.partidas)
        estrategias.append({
            'nome': "Maximização de Entropia",
            'descricao': f"Distribuição que maximiza a diversificação (entropia: {entropia:.2f})",
            'confianca': min(0.9, entropia/10)
        })
    
        # Estratégia 2: Alinhamento de Fase
        fase = self.quantum_processor.calcular_alinhamento_fase(projecao.partidas)
        estrategias.append({
            'nome': "Alinhamento de Fase Quântica",
            'descricao': f"Combinações com alinhamento de fase ideal ({fase:.2f} rad)",
            'confianca': min(0.8, abs(fase)/np.pi)
        })
    
        return estrategias
    
    def _mostrar_modulo_multiplas(self):
        # Substituir a chamada direta ao otimizador por:
        self.gerenciador_multiplas = GerenciadorMultiplas()
        self.gerenciador_multiplas.mostrar_interface()

    def _mostrar_resultados_multiplas(self, resultado):
        """Exibe os resultados da otimização de forma organizada"""
        try:
            # Verificação de dados
            if not resultado.get('distribuicao'):
                st.warning("Nenhuma distribuição válida encontrada")
                return

            # Preparação dos dados
            dados = []
            for comb, valor in resultado['distribuicao'].items():
                if valor > 0:
                    retorno = resultado['retornos'].get(comb, 1.0)
                    prob = resultado['probabilidades'].get(comb, 0.0)
                
                    dados.append({
                        'Combinação': " + ".join(comb),
                        'Valor (R$)': valor,
                        'Odd': retorno,
                        'Retorno Esperado (R$)': valor * (retorno - 1),
                        'Probabilidade': prob,
                        'ROI Esperado': (retorno - 1) * prob
                    })

            if not dados:
                st.warning("Nenhuma combinação válida encontrada")
                return

            df = pd.DataFrame(dados)

            # Exibição organizada
            st.subheader("📊 Distribuição Ótima")
        
            tab1, tab2 = st.tabs(["Distribuição Detalhada", "Resumo"])

            with tab1:
                st.dataframe(
                    df.style.format({
                        'Valor (R$)': 'R$ {:.2f}',
                        'Retorno Esperado (R$)': 'R$ {:.2f}',
                        'Odd': '{:.2f}',
                        'Probabilidade': '{:.2%}',
                        'ROI Esperado': '{:.2%}'
                    }).background_gradient(
                        subset=['ROI Esperado', 'Retorno Esperado (R$)'],
                        cmap='RdYlGn'
                    )
                )

            with tab2:
                total_investido = df['Valor (R$)'].sum()
                retorno_esperado = df['Retorno Esperado (R$)'].sum()
                roi_total = retorno_esperado / total_investido if total_investido > 0 else 0
            
                col1, col2 = st.columns(2)
                col1.metric("Total Investido", f"R$ {total_investido:.2f}")
                col2.metric("Retorno Esperado", f"R$ {retorno_esperado:.2f}")
                st.metric("ROI Total", f"{roi_total:.2%}")

        except Exception as e:
            st.error(f"Erro ao exibir resultados: {str(e)}")
                

def main_app():
    st.title("📈 Operador Conquistador")

    modo = st.radio(
        "Selecione o modo de operação:",
        ("Operações por Partida", "Apostas Múltiplas", "🔢 Múltiplas Avançadas", 
         "🔢 Múltiplas por Partida", "🧮 Cálculos Quânticos", "📊 Operações Financeiras",
         "⚡ Trade Automatizado"),
        horizontal=True,
        key="main_mode_selector"
    )

    # Operações por Partida
    if modo == "Operações por Partida":
        if 'plataforma' not in st.session_state:
            st.session_state.plataforma = PlataformaApostas()
        st.session_state.plataforma.mostrar_interface()

    elif modo == "Apostas Múltiplas":
        if 'plataforma_multiplas' not in st.session_state:
            st.session_state.plataforma_multiplas = PlataformaApostas()
        st.session_state.plataforma_multiplas._mostrar_modulo_multiplas()

    elif modo == "🔢 Múltiplas Avançadas":
        if 'gerenciador_avancadas' not in st.session_state:
            from frontend.modules.multiplas_avancadas import GerenciadorMultiplasAvancadas
            st.session_state.gerenciador_avancadas = GerenciadorMultiplasAvancadas()
        st.session_state.gerenciador_avancadas.mostrar_interface()

    elif modo == "🔢 Múltiplas por Partida":
        if 'gerenciador_partida' not in st.session_state:
            from frontend.modules.multiplas_avancadas_partida import GerenciadorMultiplasPartida
            st.session_state.gerenciador_partida = GerenciadorMultiplasPartida()
        st.session_state.gerenciador_partida.mostrar_interface()

    elif modo == "🧮 Cálculos Quânticos":
        if 'quantum_interface' not in st.session_state:
            from frontend.modules.quantum_optimizer import QuantumInterface
            st.session_state.quantum_interface = QuantumInterface()
        st.session_state.quantum_interface.mostrar_interface()

    elif modo == "📊 Operações Financeiras":
        if 'operacao_interface' not in st.session_state:
            from frontend.modules.operacao import QuantumInterface
            st.session_state.operacao_interface = QuantumInterface()
        st.session_state.operacao_interface.mostrar_interface()

    elif modo == "⚡ Trade Automatizado":
        if 'trade_interface' not in st.session_state:
            from frontend.modules.trade import TradingInterface
            st.session_state.trade_interface = TradingInterface()
        st.session_state.trade_interface.mostrar_interface()

if __name__ == '__main__':
    st.set_page_config(layout="wide", page_title="Operador Conquistador", page_icon="📈")
    
    try:
        main_app()
    except Exception as e:
        st.error(f"Erro crítico de execução:\n{str(e)}")
        print(traceback.format_exc())