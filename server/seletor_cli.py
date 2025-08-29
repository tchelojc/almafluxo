# ===== ATIVAÇÃO DO AMBIENTE VIRTUAL =====
import sys
import os
import subprocess
from pathlib import Path
import logging
import shlex

# Configuração de logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("FLUXON_SELECTOR")

# Caminho absoluto para o Python do venv - CORRIGIDO
VENV_PYTHON = Path(__file__).parents[1] / "flux_on" / "venv" / "Scripts" / "python.exe"
if not VENV_PYTHON.exists():
    VENV_PYTHON = Path(__file__).parents[1] / "flux_on" / "venv" / "bin" / "python"  # Para Linux/Mac

def ensure_virtualenv():
    current_python = Path(sys.executable)
    
    # Verifica múltiplas possibilidades de caminhos para o venv - CORRIGIDO
    possible_venv_paths = [
        Path(__file__).parents[1] / "flux_on" / "venv" / "Scripts" / "python.exe",  # Windows
        Path(__file__).parents[1] / "flux_on" / "venv" / "bin" / "python",         # Linux/Mac
    ]
    
    for venv_python in possible_venv_paths:
        if venv_python.exists():
            if current_python != venv_python:
                print(f"Ativando ambiente virtual: {venv_python}")
                subprocess.run([str(venv_python), *sys.argv])
                sys.exit(0)
            return
    
    print("ERRO: Ambiente virtual não encontrado nos locais:")
    for path in possible_venv_paths:
        print(f" - {path}")
    sys.exit(1)

ensure_virtualenv()
# ===== FIM ATIVAÇÃO VENV =====

# Configuração dos caminhos
BASE_DIR = Path(__file__).parent.resolve()
SCRIPTS_DIR = BASE_DIR.parent / "scripts_disponiveis"

AUTHORIZED_SCRIPTS = {
    "trading": {
        "path": "day_trade/project/main.py",
        "type": "streamlit",
        "port": 8501,
        "desc": "Sistema de Day Trading",
        "env_vars": {}  # Variáveis de ambiente específicas
    },
    "betting": {
        "path": "project/main.py",
        "type": "streamlit",
        "port": 8502,
        "desc": "Apostas Esportivas",
        "env_vars": {}
    },
    "apostapro": {
        "path": "ApostaPro/main.py",
        "type": "streamlit",
        "port": 8503,
        "desc": "ApostaPro (backend/CLI)",
        "env_vars": {}
    }
}

def validate_script(script_id: str) -> bool:
    if script_id not in AUTHORIZED_SCRIPTS:
        logger.error(f"Script ID '{script_id}' não autorizado")
        return False
    return True

def get_abs_path(script_id: str) -> Path:
    rel_path = AUTHORIZED_SCRIPTS[script_id]["path"]
    abs_path = (SCRIPTS_DIR / rel_path).absolute()
    
    if not abs_path.exists():
        logger.error(f"Script não encontrado: {abs_path}")
        logger.info(f"Procurando em: {SCRIPTS_DIR}")
        logger.info(f"Arquivos disponíveis: {list(SCRIPTS_DIR.glob('**/*.py'))}")
        raise FileNotFoundError(f"Script principal não encontrado em: {abs_path}")
    
    return abs_path

def build_command(script_id: str):
    cfg = AUTHORIZED_SCRIPTS[script_id]
    script_path = get_abs_path(script_id)
    cwd = script_path.parent
    
    logger.info(f"Preparando comando para {script_id}...")
    logger.info(f"Script path: {script_path}")
    logger.info(f"Working dir: {cwd}")

    if cfg["type"] == "streamlit":
        cmd = [
            str(VENV_PYTHON), "-m", "streamlit", "run",
            str(script_path),
            f"--server.port={cfg.get('port', 8501)}",
            "--server.headless=true",
            "--browser.serverAddress=0.0.0.0",
            "--logger.level=debug"
        ]
    else:
        cmd = [str(VENV_PYTHON), str(script_path)]
    
    return cmd, str(cwd)

def main():
    if len(sys.argv) < 2:
        logger.error("Uso: python seletor_cli.py <script_id>")
        logger.error("Scripts disponíveis: " + ", ".join(AUTHORIZED_SCRIPTS.keys()))
        sys.exit(2)

    script_id = sys.argv[1].lower()
    
    if not validate_script(script_id):
        sys.exit(3)

    try:
        cmd, cwd = build_command(script_id)
        logger.info(f"Executando [{script_id}] => {shlex.join(cmd)}")
        logger.info(f"Diretório de trabalho: {cwd}")
        
        # Configura ambiente
        env = os.environ.copy()
        env["PYTHONPATH"] = str(SCRIPTS_DIR.parent)
        env.update(AUTHORIZED_SCRIPTS[script_id].get("env_vars", {}))
        
        # Verifica se o diretório existe
        if not Path(cwd).exists():
            raise FileNotFoundError(f"Diretório de trabalho não existe: {cwd}")

        # Executa o processo
        proc = subprocess.Popen(
            cmd,
            cwd=cwd,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Log inicial
        logger.info(f"Processo iniciado com PID: {proc.pid}")
        print(proc.pid)  # Para captura pelo navegador
        
        # Monitora a saída
        while True:
            stdout = proc.stdout.readline()
            stderr = proc.stderr.readline()
            
            if stdout:
                logger.info(f"[{script_id}][stdout]: {stdout.strip()}")
            if stderr:
                logger.error(f"[{script_id}][stderr]: {stderr.strip()}")
            
            if proc.poll() is not None:
                break
                
        logger.info(f"Processo finalizado com código: {proc.returncode}")
        sys.exit(proc.returncode)
        
    except Exception as e:
        logger.exception(f"Falha crítica ao iniciar {script_id}")
        print(f"ERRO: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()