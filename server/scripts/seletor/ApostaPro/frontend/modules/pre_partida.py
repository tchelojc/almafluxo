# modules/pre_partida.py
import streamlit as st
from frontend.config import PrevisaoPartida, TipoAposta, Config, MetricasIntervalo
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class PrePartida:
    """Classe responsável pela configuração inicial da estratégia de apostas"""
    
    def __init__(self):
        self.config = Config()
        self.metricas = MetricasIntervalo()
        self._inicializar_estado()
    
    def _inicializar_estado(self):
        """Inicializa o estado da sessão para pré-partida"""
        if 'previsao' not in st.session_state:
            st.session_state.previsao = PrevisaoPartida.POUCOS_GOLS
        if 'capital' not in st.session_state:
            st.session_state.capital = self.config.CAPITAL_INICIAL
        if 'etapa' not in st.session_state:
            st.session_state.etapa = 'selecao_inicial'
        if 'odds' not in st.session_state:
            st.session_state.odds = {}
        if 'distribuicao' not in st.session_state:
            st.session_state.distribuicao = {}
    
    def mostrar_interface(self):
        """Mostra a interface completa de pré-partida"""
        st.title("⚽ Configuração de Estratégia - Pré-Partida")
        
        if st.session_state.etapa == 'selecao_inicial':
            return self._mostrar_selecao_inicial()
        
        elif st.session_state.etapa == 'entrada_odds':
            return self._mostrar_entrada_odds()
        
        elif st.session_state.etapa == 'distribuicao':
            return self._mostrar_distribuicao()
        
        return None
    
    def _mostrar_selecao_inicial(self):
        """Interface para seleção de capital e estratégia"""
        with st.container():
            st.subheader("🔹 Configuração Básica")
    
            # Seção de capital simplificada (sem modo baixos valores)
            st.session_state.capital = st.number_input(
                "💰 Capital para esta partida (R$)",
                min_value=10.0,
                max_value=10000.0,
                value=st.session_state.capital,
                step=10.0,
                format="%.2f",
                key="capital_input_unique",
                help="Insira o valor que deseja operar nesta partida (mínimo R$ 10,00)"
            )
    
            # Seleção de estratégia mantendo o radio button original
            estrategia = st.radio(
                "🎯 Estratégia Principal",
                options=[PrevisaoPartida.MUITOS_GOLS, PrevisaoPartida.POUCOS_GOLS],
                index=0 if st.session_state.previsao == PrevisaoPartida.MUITOS_GOLS else 1,
                format_func=lambda x: self._obter_descricao_estrategia(x),
                key="estrategia_radio_unique"
            )
    
            # Expander com informações sobre as estratégias (mantido igual)
            with st.expander("ℹ️ Detalhes das Estratégias"):
                st.markdown("""
                ## 🎯 Estratégias de Gols: Mais de 2.5 e Menos de 2.5 (com Proteções Inteligentes)

                ### 📈 **Estratégia para Muitos Gols (Mais de 2.5 - Necessário 3 ou mais gols no jogo)**

                - **Aposta Principal:** Mais de 2.5 gols ✅ *(Você ganha se a partida terminar com 3 ou mais gols no tempo normal)*  
                - **Proteções Automáticas:**  
                  ▸ **Menos de 2.5 gols:** Protege seu investimento caso o jogo tenha poucos gols (0, 1 ou 2)  
                  ▸ **Placar Exato 0x0 (1º tempo ou jogo todo):** Proteção adicional para jogos que fiquem zerados até o intervalo ou até o final  

                - **Cenários Estatísticos Favoráveis:**  
                  ✔ Times com **média superior a 1.5 gols por jogo** nas últimas 5 a 10 partidas  
                  ✔ Jogos entre **equipes com ataque eficiente e defesas vulneráveis**  
                  ✔ Confrontos com **probabilidade de ambas as equipes marcarem (Ambas Marcam) acima de 60%**, de acordo com estatísticas ou análise prévia  
                  ✔ **Cotações iniciais para Mais de 2.5 acima de 1.80**, indicando que o mercado está valorizando o risco de poucos gols (gerando valor no Mais de 2.5)

                - **Quando utilizar esta estratégia:**  
                  👉 Partidas de **campeonatos com alta média de gols** (exemplos: Campeonato Alemão, Campeonato Holandês, Série B do Brasil)  
                  👉 Jogos de **fim de temporada**, onde as equipes jogam mais abertas  
                  👉 Partidas onde **ambos os times precisam desesperadamente de um bom resultado** (ex: briga por título ou contra o rebaixamento)

                ---

                ### 📉 **Estratégia para Poucos Gols (Menos de 2.5 - Máximo de 2 gols no jogo)**

                - **Aposta Principal:** Menos de 2.5 gols ✅ *(Você ganha se a partida terminar com 0, 1 ou 2 gols)*  
                - **Proteções Automáticas:**  
                  ▸ **Mais de 2.5 gols:** Proteção para caso o jogo fuja do padrão e tenha muitos gols inesperados  
                  ▸ **Placar Exato 0x0 (jogo todo):** Proteção adicional para casos de empate sem gols

                - **Cenários Estatísticos Favoráveis:**  
                  ✔ Partidas com **média inferior a 2.2 gols por jogo**, considerando os últimos jogos de cada equipe  
                  ✔ Times com **defesas sólidas e ataques pouco produtivos**  
                  ✔ Confrontos de **clássicos regionais**, **jogos eliminatórios**, ou **finais de campeonato**, onde o peso do resultado normalmente trava o jogo  
                  ✔ **Cotações iniciais para Menos de 2.5 abaixo de 1.80**, sinalizando que o mercado também espera poucos gols

                - **Quando utilizar esta estratégia:**  
                  👉 Jogos de **equipes lutando contra o rebaixamento**, onde a prioridade é não sofrer gols  
                  👉 Partidas com **condições climáticas adversas (chuva, vento forte)**  
                  👉 Confrontos com **jogadores importantes do ataque suspensos ou lesionados**

                ---

                ### ⚖️ Gestão de Risco Proporcional:

                - ✅ **Distribuição Inteligente de Capital:** Todas as proteções são calculadas de forma automática, respeitando o valor total que você deseja investir  
                - ✅ **Equilíbrio entre Risco e Retorno:** O sistema busca **proteger você de perdas totais em cenários extremos**, sem comprometer o potencial de lucro  
                - ✅ **Recomendação Importante:** Antes de confirmar qualquer operação, **analise o retorno mínimo garantido versus o capital de risco nas proteções**

                *📌 Lembre-se: Não existe aposta sem risco. Nossa plataforma foi projetada para minimizar os riscos mais comuns, mas decisões conscientes sempre são essenciais.*

                """)

    
            # Botão de confirmação mantido igual
            if st.button("🔘 Definir Estratégia", 
                        type="primary", 
                        key="confirm_strategy_button"):
                st.session_state.previsao = estrategia
                st.session_state.etapa = 'entrada_odds'
                st.rerun()
            
    def _mostrar_entrada_odds(self):
        """Interface para entrada das odds conforme estratégia selecionada"""
        st.subheader(f"📊 Configurar Odds - {st.session_state.previsao.value}")
        st.caption("Ajuste as odds conforme encontradas na casa de apostas")

        odds = {}
        cols = st.columns(2)
    
        # Configuração das apostas para cada estratégia
        apostas_estrategia = {
            PrevisaoPartida.MUITOS_GOLS: {
                'principal': [
                    (TipoAposta.MAIS_25_GOLS, "Mais 2,5 gols (Principal)", 2.45),
                    (TipoAposta.MAIS_15_PRIMEIRO_TEMPO, "Mais 1,5 gols 1º Tempo", 2.10),
                    (TipoAposta.AMBAS_MARCAM_SIM, "Ambas marcam (Sim)", 1.75)
                ],
                'protecao': [
                    (TipoAposta.MENOS_25_GOLS, "Menos 2,5 gols (Proteção)", 5.71),
                    (TipoAposta.MENOS_05_GOLS, "Menos 0,5 gols 1ºT (Proteção 0x0)", 8.50),
                    (TipoAposta.VENCEDOR_FAVORITO, "Vencedor favorito", 1.65)
                ]
            },
            PrevisaoPartida.POUCOS_GOLS: {
                'principal': [
                    (TipoAposta.MENOS_25_GOLS, "Menos 2,5 gols (Principal)", 1.75),
                    (TipoAposta.AMBAS_MARCAM_NAO, "Ambas NÃO marcam", 2.10),
                    (TipoAposta.MENOS_15_GOLS, "Menos 1,5 gols", 2.40)
                ],
                'protecao': [
                    (TipoAposta.MAIS_25_GOLS, "Mais 2,5 gols (Proteção)", 2.20),
                    (TipoAposta.MENOS_05_GOLS, "Zero gols partida (Proteção 0x0)", 12.00),
                    (TipoAposta.VENCEDOR_FAVORITO, "Vencedor favorito", 1.65)
                ]
            }
        }
    
        # Exibe as odds para a estratégia selecionada
        estrategia = apostas_estrategia[st.session_state.previsao]

        with cols[0]:
            st.markdown("**📈 Apostas Principais**")
            for aposta, label, valor_padrao in estrategia['principal']:
                odds[aposta] = st.number_input(
                    label,
                    min_value=1.01,
                    value=valor_padrao,
                    step=0.05,
                    key=f"odd_{aposta.name}"
                )
    
        with cols[1]:
            st.markdown("**🛡️ Apostas de Proteção**")
            for aposta, label, valor_padrao in estrategia['protecao']:
                odds[aposta] = st.number_input(
                    label,
                    min_value=1.01,
                    value=valor_padrao,
                    step=0.05 if aposta != TipoAposta.MENOS_05_GOLS else 0.5,
                    key=f"odd_{aposta.name}"
                )
    
        # Validação e confirmação
        if st.button("✅ Confirmar Odds", type="primary"):
            if self._validar_odds(odds):
                st.session_state.odds = odds
                # CALCULA A DISTRIBUIÇÃO IMEDIATAMENTE APÓS CONFIRMAR AS ODDS
                st.session_state.distribuicao = self._calcular_distribuicao_automatica()
                st.session_state.etapa = "distribuicao"
                st.rerun()
    
    def _mostrar_distribuicao(self):
        """Mostra a distribuição corretamente classificada"""
        # Verificação de segurança reforçada
        if 'distribuicao' not in st.session_state:
            st.error("⚠️ Distribuição não calculada! Volte e confirme as odds.")
            return
    
        if not st.session_state.distribuicao:
            st.error("⚠️ Distribuição vazia! Verifique os cálculos.")
            return
        
        if 'previsao' not in st.session_state:
            st.error("⚠️ Estratégia não definida!")
            return

        # Dados necessários
        distribuicao = st.session_state.distribuicao
        previsao = st.session_state.previsao
        capital = st.session_state.get('capital', 20.00)

        # Definição clara das apostas
        estrategias = {
            PrevisaoPartida.MUITOS_GOLS: {
                'principal': [
                    (TipoAposta.MAIS_25_GOLS, "Mais 2,5 gols partida"),
                    (TipoAposta.MAIS_15_PRIMEIRO_TEMPO, "Mais 1,5 gols 1º Tempo"),
                    (TipoAposta.AMBAS_MARCAM_SIM, "Ambas Marcam (Sim)")
                ],
                'protecao': [
                    (TipoAposta.MENOS_25_GOLS, "Menos 2,5 gols partida"),
                    (TipoAposta.MENOS_05_GOLS, "Menos 0,5 gols partida (0x0)"),
                    (TipoAposta.VENCEDOR_FAVORITO, "Vencedor Partida (Favorito)")
                ]
            },
            PrevisaoPartida.POUCOS_GOLS: {
                'principal': [
                    (TipoAposta.MENOS_25_GOLS, "Menos 2,5 gols partida"),
                    (TipoAposta.AMBAS_MARCAM_NAO, "Ambas Marcam (Não)"),
                    (TipoAposta.MENOS_15_GOLS, "Menos 1,5 gols partida")
                ],
                'protecao': [
                    (TipoAposta.MAIS_25_GOLS, "Mais 2,5 gols partida"),
                    (TipoAposta.MENOS_05_GOLS, "Menos 0,5 gols partida (0x0)"),
                    (TipoAposta.VENCEDOR_FAVORITO, "Vencedor Partida (Favorito)")
                ]
            }
        }

        # Obtém a estratégia atual
        estrategia = estrategias.get(previsao, {})

        # Exibição organizada
        cols = st.columns(2)
    
        with cols[0]:
            st.markdown("**📊 Apostas Principais**")
            for aposta, descricao in estrategia.get('principal', []):
                valor = distribuicao.get(aposta, 0)
                if valor > 0:
                    st.info(f"{descricao}: R$ {valor:.2f}")
                else:
                    st.warning(f"{descricao}: Não alocado")

        with cols[1]:
            st.markdown("**🛡️ Apostas de Proteção**")
            for aposta, descricao in estrategia.get('protecao', []):
                valor = distribuicao.get(aposta, 0)
                if valor > 0:
                    st.warning(f"{descricao}: R$ {valor:.2f}")
                else:
                    st.warning(f"{descricao}: Não alocado")

        # Mostra o total distribuído
        total = sum(distribuicao.values())
        st.progress(min(total / capital, 1.0))
        st.metric("💰 Total Distribuído", f"R$ {total:.2f}")

        if st.button("🏁 Iniciar Análise da Partida", type="primary"):
            return {
                'capital': capital,
                'previsao': previsao,
                'odds': st.session_state.odds,
                'distribuicao': distribuicao
            }
            
    def _validar_odds(self, odds):
        """Valida se todas as odds necessárias foram informadas"""
        required_odds = {
            PrevisaoPartida.MUITOS_GOLS: [
                TipoAposta.MAIS_25_GOLS,
                TipoAposta.MAIS_15_PRIMEIRO_TEMPO,
                TipoAposta.AMBAS_MARCAM_SIM,
                TipoAposta.MENOS_25_GOLS,
                TipoAposta.MENOS_05_GOLS,
                TipoAposta.VENCEDOR_FAVORITO
            ],
            PrevisaoPartida.POUCOS_GOLS: [
                TipoAposta.MENOS_25_GOLS,
                TipoAposta.AMBAS_MARCAM_NAO,
                TipoAposta.MENOS_15_GOLS,
                TipoAposta.MAIS_25_GOLS,
                TipoAposta.MENOS_05_GOLS,
                TipoAposta.VENCEDOR_FAVORITO
            ]
        }   
    
        missing = [aposta.name for aposta in required_odds[st.session_state.previsao] if aposta not in odds]
        if missing:
            st.error(f"⚠️ Faltam odds para: {', '.join(missing)}")
            return False
        return True
    
    def _calcular_distribuicao_automatica(self):
        """Distribuição automática com ajustes quânticos e estratégicos perfeitos"""
        capital_total = st.session_state.capital
        previsao = st.session_state.previsao
        odds = st.session_state.odds

        # Fator de escala dinâmico
        base_capital = 20.0
        fator_escala = capital_total / base_capital
    
        # Estratégias base otimizadas
        porcentagens_base = {
            PrevisaoPartida.MUITOS_GOLS: {
                TipoAposta.MAIS_25_GOLS: 0.20,
                TipoAposta.MAIS_15_PRIMEIRO_TEMPO: 0.07,
                TipoAposta.AMBAS_MARCAM_SIM: 0.13,
                TipoAposta.MENOS_25_GOLS: 0.15,
                TipoAposta.MENOS_05_GOLS: 0.05,
                TipoAposta.VENCEDOR_FAVORITO: 0.10
            },
            PrevisaoPartida.POUCOS_GOLS: {
                TipoAposta.MENOS_25_GOLS: 0.22,      # Aumentado para 22%
                TipoAposta.AMBAS_MARCAM_NAO: 0.16,    # Aumentado para 16%
                TipoAposta.MAIS_25_GOLS: 0.08,        # Reduzido para 8%
                TipoAposta.MENOS_15_GOLS: 0.16,       # Aumento de 120%
                TipoAposta.MENOS_05_GOLS: 0.04,       # Ajuste fino
                TipoAposta.VENCEDOR_FAVORITO: 0.12    # Pequeno aumento
            }
        }

        # 1. Cálculo base com proteções dinâmicas
        distribuicao = {}
        protecoes = self._calcular_protecoes(capital_total, fator_escala, odds, previsao)
    
        for aposta in porcentagens_base[previsao]:
            base_val = capital_total * porcentagens_base[previsao][aposta]
            protecao_val = protecoes.get(aposta, 0)
        
            # Aplica redução de 20% para MAIS_25_GOLS em POUCOS_GOLS
            if previsao == PrevisaoPartida.POUCOS_GOLS and aposta == TipoAposta.MAIS_25_GOLS:
                base_val *= 0.80
        
            distribuicao[aposta] = max(base_val, protecao_val)

        # 2. Ajustes pós-distribuição
        distribuicao = self._aplicar_ajustes_finais(distribuicao, capital_total, fator_escala, odds)
    
        return distribuicao

    def _calcular_protecoes(self, capital_total, fator_escala, odds, previsao):
        """Calcula valores de proteção com lógica estratégica"""
        protecoes = {}
    
        # Proteção para Menos 0.5 gols
        if TipoAposta.MENOS_05_GOLS in odds:
            protecoes[TipoAposta.MENOS_05_GOLS] = min(
                (16.00 * fator_escala) / (odds[TipoAposta.MENOS_05_GOLS] - 1),
                capital_total * 0.05  # Limite de 5%
            )
    
        # Proteções dinâmicas baseadas na estratégia
        if previsao == PrevisaoPartida.MUITOS_GOLS:
            if odds.get(TipoAposta.MENOS_25_GOLS, 0) > odds.get(TipoAposta.MAIS_25_GOLS, 0):
                protecoes[TipoAposta.MENOS_25_GOLS] = (6.00 * fator_escala) / (odds[TipoAposta.MENOS_25_GOLS] - 1)
        else:
            if odds.get(TipoAposta.MAIS_25_GOLS, 0) > odds.get(TipoAposta.MENOS_25_GOLS, 0):
                protecoes[TipoAposta.MAIS_25_GOLS] = (3.00 * fator_escala) / (odds[TipoAposta.MAIS_25_GOLS] - 1)  # Valor reduzido
    
        return protecoes

    def _aplicar_ajustes_finais(self, distribuicao, capital_total, fator_escala, odds):
        """Aplica os ajustes finais na distribuição"""
        # Ajuste de segurança baseado nas odds
        for aposta in distribuicao:
            if aposta in odds:
                fator_odd = min(1.0, 1 / (odds[aposta] ** 0.5))
                distribuicao[aposta] *= fator_odd
    
        # Garante mínimo para VENCEDOR_FAVORITO
        if TipoAposta.VENCEDOR_FAVORITO in distribuicao:
            distribuicao[TipoAposta.VENCEDOR_FAVORITO] = max(
                2.00 * fator_escala,
                distribuicao[TipoAposta.VENCEDOR_FAVORITO]
            )
    
        # Normalização para 70% do capital
        total = sum(distribuicao.values())
        if total > capital_total * 0.70:
            fator = (capital_total * 0.70) / total
            distribuicao = {k: round(v * fator, 2) for k, v in distribuicao.items()}
        else:
            distribuicao = {k: round(v, 2) for k, v in distribuicao.items()}
    
        return distribuicao
    
    def _obter_descricao_estrategia(self, estrategia):
        """Retorna a descrição completa da estratégia"""
        if estrategia == PrevisaoPartida.MUITOS_GOLS:
            return (
                "Muitos Gols (+2.5) - Estratégia voltada para jogos com alto potencial ofensivo.\n"
                "Proteções: Menos 2.5 gols e 0x0 (Placar em branco no 1º tempo ou na partida inteira).\n"
                "📌 Importante: Embora o usuário possa escolher aplicar a proteção de 0x0 para o 1º tempo, "
                "o sistema considera o resultado final da partida para todos os cálculos. "
                "Ou seja, se ocorrerem gols no segundo tempo, a proteção será considerada perdida. "
                "Essa estrutura evita inconsistências, pois o modelo está interligado de forma quântica — "
                "modificações em uma odd ou tempo impactam toda a lógica de retorno proporcional e risco calculado."
            )
        return (
            "Poucos Gols (-2.5) - Foco em jogos com perfil defensivo ou equilibrado.\n"
            "Proteções: Mais 2.5 gols e 0x0 (partida inteira).\n"
            "📌 Importante: O cálculo da proteção 0x0 é sempre vinculado ao placar final da partida. "
            "Mesmo que o usuário acredite estar aplicando ao 1º tempo, o sistema considera o jogo completo, "
            "mantendo a consistência nos cálculos entre odds, investimentos, e retornos proporcionais."
        )
    
    def _validar_odds(self, odds):
        """Valida se todos os valores de odds são válidos"""
        if not all(v >= 1.01 for v in odds.values()):
            st.error("Todas as odds devem ser maiores que 1.01")
            return False
        
        # Validação específica para estratégia de muitos gols
        if st.session_state.previsao == PrevisaoPartida.MUITOS_GOLS:
            if odds[TipoAposta.MAIS_25_GOLS] > odds[TipoAposta.MENOS_25_GOLS]:
                st.warning("A odd de Mais 2.5 gols está maior que a de Menos 2.5 gols - Verifique!")
        
        return True