# config.py
from enum import Enum, auto
from dataclasses import dataclass

class PrevisaoPartida(Enum):
    """Enumeração para tipos de previsão de partida baseada em gols."""
    MUITOS_GOLS = "Muitos Gols (+2.5)"
    POUCOS_GOLS = "Poucos Gols (-2.5)"

class FasePartida(Enum):
    """Fases em que uma partida pode se encontrar."""
    ANTES_PARTIDA = auto()
    INTERVALO = auto()
    FINALIZADA = auto()

class TipoAposta(Enum):
    """Tipos de apostas disponíveis na plataforma."""
    MENOS_25_GOLS = "Menos 2,5 gols partida"
    MAIS_25_GOLS = "Mais 2,5 gols partida"
    MENOS_15_GOLS = "Menos 1,5 gols partida"
    MENOS_05_GOLS = "Menos 0,5 gols partida (0x0)"
    MAIS_15_PRIMEIRO_TEMPO = "Mais 1,5 gols 1º Tempo"
    MENOS_15_PRIMEIRO_TEMPO = "Menos 1.5 gols (1º tempo)"  # Adicione esta linha
    MAIS_05_PRIMEIRO_TEMPO = "Mais 0,5 gols 1º Tempo"
    MAIS_15_SEGUNDO_TEMPO = "Mais 1,5 gols 2º Tempo"
    MENOS_15_SEGUNDO_TEMPO = "Menos 1.5 gols (2º tempo)"  # Adicione esta linha
    MAIS_05_SEGUNDO_TEMPO = "Mais 0,5 gols 2º Tempo"
    AMBAS_MARCAM = "Ambas marcam"
    AMBAS_MARCAM_SIM = "Ambas Marcam (Sim)"
    AMBAS_MARCAM_NAO = "Ambas Marcam (Não)"
    VENCEDOR_FAVORITO = "Vencedor Partida (Favorito)"
    GOLEADA_UNILATERAL = "Goleada Unilateral (+2,5 Gols e Ambas Não)"
    PROXIMO_GOL_AZARAO = "Próximo Gol Time Não-Favorito"
    NAO_SAIR_MAIS_GOLS = "Não Sair Mais Gols (Após Intervalo)"
    AMBAS_MARCAM_2T_SIM = "Ambas marcam 2º tempo (Sim)"
    AMBAS_MARCAM_2T_NAO = "Ambas marcam 2º tempo (Não)"
    VANTAGEM_UNILATERAL = "Vantagem unilateral (time com mais gols)"

class CenarioIntervalo(Enum):
    """Cenários possíveis durante o intervalo da partida."""
    FAVORITO_GANHANDO_1X0 = auto()
    FAVORITO_GANHANDO_2X0 = auto()
    FAVORITO_GANHANDO_2X1 = auto()
    EMPATE_0X0 = auto()
    EMPATE_1X1 = auto()
    FAVORITO_PERDENDO_0X1 = auto()
    FAVORITO_PERDENDO_0X2 = auto()
    FAVORITO_PERDENDO_1X2 = auto()

# Dicionário de descrições para cenários de intervalo
CENARIOS = {
    CenarioIntervalo.FAVORITO_GANHANDO_1X0: "1x0 (Favorito ganhando)",
    CenarioIntervalo.FAVORITO_GANHANDO_2X0: "2x0 (Favorito dominando)",
    CenarioIntervalo.FAVORITO_GANHANDO_2X1: "2x1 (Favorito ganhando)",
    CenarioIntervalo.EMPATE_0X0: "0x0 (Jogo equilibrado)",
    CenarioIntervalo.EMPATE_1X1: "1x1 (Jogo movimentado)",
    CenarioIntervalo.FAVORITO_PERDENDO_0X1: "0x1 (Favorito perdendo)",
    CenarioIntervalo.FAVORITO_PERDENDO_0X2: "0x2 (Favorito sofrendo)",
    CenarioIntervalo.FAVORITO_PERDENDO_1X2: "1x2 (Favorito perdendo)"
}

class MetricasIntervalo:
    """Métricas e parâmetros para análise durante o intervalo."""
    FATOR_RISCO = 1.5
    FATOR_SEGURANCA = 0.8
    LIMIAR_GOLS = 2.7  # Média global de gols por partida
    EQUILIBRIO_MAXIMO = 1.0
    EQUILIBRIO_MINIMO = -0.5

class ConstantesAposta:
    """Constantes relacionadas a cálculos de apostas e odds."""
    # Relação entre odds e probabilidade implícita
    RELACAO_ODDS_PROB = {
        1.01: 0.99,
        1.5: 0.6667,
        2.0: 0.5,
        3.0: 0.3333,
        5.0: 0.2,
        10.0: 0.1
    }
    
    # Fatores de ajuste para distribuição
    FATOR_PRINCIPAL = 0.8
    FATOR_PROTECAO = 0.5
    FATOR_RETORNO = 1.2

@dataclass
class Config:
    """Configurações gerais da plataforma."""
    CAPITAL_INICIAL: float = 20.00
    DEBUG_MODE = False  # Adicione esta linha
    DISTRIBUICAO_INICIAL: float = 0.6  # 60% antes da partida
    DISTRIBUICAO_INTERVALO: float = 0.4  # 40% no intervalo
    PLANILHA_ID: str = "1VN55T_2FykOZEL2WJab2HObV9BlNGpqCRaQoAgBUIAo"
    CREDENCIAIS: str = "credenciais.json"

# Configuração global instanciada
config = Config()

# Adicione ao final do arquivo existente
QUANTUM_PARAMS = {
    'phi_values': [3, 6, 9],
    'base_time': 1.12,  # ΔT𝒢 base
    'scenarios': {
        'high_energy': {'min_phase': 150},
        'low_energy': {'max_phase': 50}
    }
}

QUANTUM_SAFETY = {
    'min_phase': 0,
    'max_phase': 200,
    'min_factor': 0.7,
    'max_factor': 1.3,
    'default_values': {
        'current': 1.0,
        'resonance': 1.0,
        'base': 1.0,
        'phase': 100,
        'factor': 1.0
    }
}

class TipoMultipla(Enum):
    """Tipos de apostas múltiplas disponíveis."""
    SIMPLES = auto()
    DUPLA = auto()
    TRIPLA = auto()
    QUADRA = auto()
    QUINTA = auto()

@dataclass
class ConfigMultiplas:
    """Configurações específicas para apostas múltiplas."""
    MAX_PARTIDAS: int = 10
    MIN_PARTIDAS: int = 2
    CAPITAL_MINIMO: float = 10.0
    DISTRIBUICAO_PRINCIPAL: float = 0.7  # 70% para apostas principais
    DISTRIBUICAO_PROTECAO: float = 0.3  # 30% para proteções

# Adicione ao final do arquivo
config_multiplas = ConfigMultiplas()