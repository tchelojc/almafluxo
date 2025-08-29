# ===== ATIVAÇÃO DO AMBIENTE VIRTUAL =====
import sys
import subprocess
from pathlib import Path

VENV_PYTHON = Path(__file__).parents[2] / "venv" / "Scripts" / "python.exe"

def ensure_virtualenv():
    current_python = Path(sys.executable)
    if current_python != VENV_PYTHON:
        subprocess.run([str(VENV_PYTHON), *sys.argv])
        sys.exit(0)

ensure_virtualenv()
# ===== FIM ATIVAÇÃO VENV =====

import os
import logging
import shlex
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("FLUXON_SELECTOR")

BASE_DIR = Path(__file__).parent.resolve()

# Mapeamento autorizado (igual ao seletor.py)
AUTHORIZED_SCRIPTS = {
    "trading": {
        "path": "scripts/day_trade/project/MAIN.py",
        "type": "streamlit",
        "port": 8501,
        "desc": "Sistema de Day Trading"
    },
    "betting": {
        "path": "scripts/project/MAIN.py",
        "type": "streamlit",
        "port": 8502,
        "desc": "Apostas Esportivas"
    },
    "apostapro": {
        "path": "scripts/ApostaPro/main.py",
        "type": "python",
        "desc": "ApostaPro (backend/CLI)"
    }
}

def validate_script(script_id: str) -> bool:
    return script_id in AUTHORIZED_SCRIPTS

def get_abs_path(script_id: str) -> Path:
    return BASE_DIR / AUTHORIZED_SCRIPTS[script_id]["path"]

def build_command(script_id: str):
    cfg = AUTHORIZED_SCRIPTS[script_id]
    script_path = get_abs_path(script_id)
    
    if not script_path.exists():
        raise FileNotFoundError(f"Script não encontrado: {script_path}")

    if cfg["type"] == "streamlit":
        cmd = [
            str(VENV_PYTHON), "-m", "streamlit", "run",
            str(script_path),
            f"--server.port={cfg.get('port', 8501)}"
        ]
    else:
        cmd = [str(VENV_PYTHON), str(script_path)]
    
    return cmd, str(script_path.parent)

def main():
    if len(sys.argv) < 2:
        print("ERRO: informe o script_id (trading|betting|apostapro)")
        sys.exit(2)

    script_id = sys.argv[1]
    if not validate_script(script_id):
        print("ERRO: script não autorizado")
        sys.exit(3)

    try:
        cmd, cwd = build_command(script_id)
        logger.info(f"Executando [{script_id}] => {shlex.join(cmd)} (cwd={cwd})")
        
        # Executa diretamente com o Python do venv
        proc = subprocess.Popen(cmd, cwd=cwd)
        print(proc.pid)
        sys.exit(0)
    except Exception as e:
        logger.exception("Falha ao iniciar o script")
        print(f"ERRO: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()