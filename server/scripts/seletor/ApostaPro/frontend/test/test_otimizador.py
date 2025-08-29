import sys
import os

# Caminho até o diretório raiz do projeto: plataforma/apps/ApostaPro
projeto_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
if projeto_root not in sys.path:
    sys.path.insert(0, projeto_root)

# Importa do backend
from backend.otimizador import OtimizadorMultiplas
# (Se necessário, também poderá importar protecao e calculadora assim:
# from backend.protecao import ...
# from backend.calculadora import ...
# )

# Importa do frontend/modules
# from frontend.modules.multiplas import ...  # Se for usar depois

def criar_partidas_exemplo(qtd: int):
    """Cria uma lista de partidas fictícias para teste"""
    return [{
        'casa': 1.80,
        'empate': 3.20,
        'fora': 4.50,
        'dupla_chance': 1.60,
        'over_15': 1.75,
        'ambas_nao': 1.85
    } for _ in range(qtd)]

def testar_combinacoes_validas():
    print("\n==== TESTE 1: Validação de combinações ====")
    ot = OtimizadorMultiplas()
    partidas = criar_partidas_exemplo(2)
    for p in partidas:
        ot.adicionar_partida(p)
    
    try:
        ot._gerar_combinacoes_validas()
        ot._calcular_retornos_combinacoes()
        for comb in ot.combinacoes:
            if len(comb) != len(ot.partidas) * 2:
                print(f"[ERRO] Combinação {comb} com número de mercados inválido.")
            else:
                print(f"[OK] Combinação válida: {comb}")
    except Exception as e:
        print(f"[FALHA] Erro ao calcular combinações: {e}")

def testar_calculo_distribuicao():
    print("\n==== TESTE 2: Cálculo de Distribuição ====")
    ot = OtimizadorMultiplas()
    partidas = criar_partidas_exemplo(2)
    for p in partidas:
        ot.adicionar_partida(p)

    resultado = ot.calcular_distribuicao(capital=20.0, tolerancia=0.1)

    if resultado.get('tipo_distribuicao') == 'erro':
        print(f"[ERRO] Falha nos cálculos: {resultado['erro']}")
    else:
        print("[OK] Distribuição calculada com sucesso!")
        for comb, valor in resultado['distribuicao'].items():
            print(f"  ➤ {comb}: R$ {valor:.2f}")

def testar_validacoes_basicas():
    print("\n==== TESTE 3: Validação de entrada ====")
    ot = OtimizadorMultiplas()
    ot.adicionar_partida({'casa': 1.8, 'empate': 3.2})  # incompleto
    ot.adicionar_partida({})  # completamente vazio

    try:
        ot._gerar_combinacoes_validas()
        ot._calcular_retornos_combinacoes()
        print("[ERRO] Deveria ter falhado por falta de dados!")
    except Exception as e:
        print(f"[OK] Falha esperada: {e}")

def rodar_todos_testes():
    testar_combinacoes_validas()
    testar_calculo_distribuicao()
    testar_validacoes_basicas()

if __name__ == "__main__":
    rodar_todos_testes()
