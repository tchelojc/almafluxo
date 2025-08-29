# modules/quantum.py
import numpy as np
import time
from datetime import datetime
from typing import List, Dict, Optional, Tuple, Any
from core.quantum_universe import QuantumUniverseOperator, QuantumStateType
import math
import sys
from pathlib import Path

try:
    from core.quantum_universe import QuantumUniverseOperator, QuantumStateType
except ImportError:
    # Fallback: import relativo (se core estiver dentro de frontend)
    from ..core.quantum_universe import QuantumUniverseOperator, QuantumStateType

class QuantumLearner:
    def __init__(self, phi=3):
        self.phi = phi
        self.time_anchor = 12 - (datetime.now().year % 12)
    
    def fluid_percentage(self, current: float, resonance: float, base: float) -> float:
        try:
            adjusted_base = max(0.1, base)
            value = ((current - resonance) / (adjusted_base + 1e-6)) * 100 * self.phi
            return float(np.real(value))  # Evita números complexos
        except:
            return 100.0
    
    def predict(self, X):
        return np.mean(X) * self.phi

class QuantumProcessor:
    def __init__(self):
        self.learner = QuantumLearner()
        self.universe_operator = QuantumUniverseOperator(dimensions=100)
        self.current_universe = None
        self.quantum_state = None

    def _safe_float(self, value) -> float:
        """Conversão segura para float, tratando todos os casos"""
        try:
            if isinstance(value, (int, float)):
                return float(value)
            elif isinstance(value, complex):
                return float(np.real(value))  # Pega apenas parte real
            elif isinstance(value, str):
                return float(value.split()[0]) if value else 0.0
            else:
                return 0.0
        except:
            return 0.0  # Fallback seguro

    def initialize_market_universe(self, market_data: Dict[str, Any]):
        """Inicialização quântica robusta com verificação de dados e controle de tempo"""
        try:
            # ⏱️ Início do tempo de execução
            start_time = time.time()
            max_duration = 2  # segundos

            # ✅ Verificação básica dos dados de entrada
            if not market_data or 'odds' not in market_data:
                raise ValueError("Dados de mercado inválidos")

            # ✅ Garante valores positivos e válidos para odds
            odds = {k: max(1.01, self._safe_float(v)) 
                    for k, v in market_data.get('odds', {}).items()}

            # ✅ Processamento seguro do placar
            placar = market_data.get('placar', '0x0')
            if isinstance(placar, str):
                try:
                    casa, fora = map(int, placar.split('x'))
                except:
                    casa, fora = 0, 0
            else:
                casa, fora = 0, 0

            total_gols = max(0, casa + fora)
            diff_gols = max(0, abs(casa - fora))

            # ✅ Matriz quântica com salvaguardas
            quantum_matrix = np.array([
                [self._safe_float(np.sqrt(total_gols + 1))],  # +1 evita raiz de zero
                [self._safe_float(np.log(diff_gols + 1))]     # +1 evita log(0)
            ])

            # ✅ Normalização
            quantum_matrix = quantum_matrix / np.sum(quantum_matrix)

            # ✅ Fatores derivados do estado quântico
            self.quantum_state = {
                'matrix': quantum_matrix,
                'factors': {
                    'momentum': min(1.5, max(0.5, total_gols / (diff_gols + 0.1))),
                    'balance': min(1.2, max(0.8, 1 / (diff_gols + 0.1)))
                }
            }

            # ⏱️ Verificação de tempo
            if time.time() - start_time > max_duration:
                raise TimeoutError("Inicialização quântica excedeu o tempo máximo permitido")

            return self.quantum_state

        except Exception as e:
            # 🔁 Estado de fallback seguro
            self.quantum_state = {
                'matrix': np.array([[0.5], [0.5]]),
                'factors': {'momentum': 1.0, 'balance': 1.0}
            }
            raise ValueError(f"Initialization safe mode: {str(e)}")

    def _parse_placar(self, placar_raw: Any) -> Dict[str, int]:
        if isinstance(placar_raw, str):
            try:
                casa, fora = map(int, placar_raw.split('x'))
                return {'casa': casa, 'fora': fora}
            except:
                return {'casa': 0, 'fora': 0}
        elif isinstance(placar_raw, dict):
            return {
                'casa': int(placar_raw.get('casa', 0)),
                'fora': int(placar_raw.get('fora', 0))
            }
        return {'casa': 0, 'fora': 0}

    def _validate_quantum_data(self, data: Dict[str, Any]):
        if 'odds' not in data or not data['odds']:
            raise ValueError("Dados de odds ausentes")
        if not isinstance(data.get('placar', {}), dict):
            raise ValueError("Formato de placar inválido")

    def get_quantum_flux(self, placar: str) -> Dict[str, float]:
        try:
            gols_casa, gols_fora = map(int, placar.split('x'))
            total_gols = gols_casa + gols_fora
            diferenca = abs(gols_casa - gols_fora)
            return {
                'current': total_gols * 1.5,
                'resonance': diferenca * 2.0,
                'base': max(1, total_gols - diferenca)
            }
        except:
            return {'current': 1.0, 'resonance': 1.0, 'base': 1.0}

    def get_universe_state(self):
        if self.current_universe is None:
            return {
                'probability_matrix': np.eye(2),
                'recommendations': {
                    'over_2.5': 0.5,
                    'under_2.5': 0.5,
                    'both_score': 0.5,
                    'clean_sheet': 0.5
                }
            }
        
        universe = self.universe_operator.parallel_universes[self.current_universe]
        return self._convert_to_market_state(universe['current_state'])

    def _convert_to_market_state(self, quantum_state):
        prob_matrix = np.abs(quantum_state.tensor) ** 2
        normalized = prob_matrix / np.sum(prob_matrix)
        return {
            'probability_matrix': normalized,
            'recommendations': self._extract_recommendations(normalized)
        }

    def _extract_recommendations(self, prob_matrix):
        rec = {}
        if prob_matrix.shape[0] >= 2 and prob_matrix.shape[1] >= 2:
            rec['over_2.5'] = float(prob_matrix[0, 0])
            rec['under_2.5'] = float(prob_matrix[0, 1])
            rec['both_score'] = float(prob_matrix[1, 0])
            rec['clean_sheet'] = float(prob_matrix[1, 1])
        else:
            for i in range(prob_matrix.shape[0]):
                rec[f'option_{i}'] = float(prob_matrix[i, 0])
        return rec

    def get_probabilidade_combinacao(self, combinacao: Tuple[str, ...]) -> float:
        if not hasattr(self, 'current_universe') or not self.current_universe:
            return 0.5

        prob_matrix = self.get_universe_state().get('probability_matrix', np.eye(2))
        indices = {'casa': 0, 'empate': 1, 'fora': 2}
        try:
            return np.prod([
                prob_matrix[i][indices[result]] if result in indices else 0.5
                for i, result in enumerate(combinacao)
            ])
        except:
            return 0.5

    def get_correlacao(self, partida_i: int, partida_j: int, tipo_multipla: int) -> float:
        return 0.5 * np.sin((partida_i + partida_j) * np.pi / tipo_multipla)

    def calcular_entropia(self, partidas: List[Dict]) -> float:
        probs = np.array([
            [self._safe_float(odd)/sum(map(self._safe_float, p.values())) for odd in p.values()]
            for p in partidas
        ])
        return -np.sum(probs * np.log(probs + 1e-10))

    def calcular_alinhamento_fase(self, partidas: List[Dict]) -> float:
        fases = [np.angle(complex(p.get('casa', 0), p.get('fora', 0))) for p in partidas]
        return np.mean(fases)
