import os
import subprocess
import sys
from pathlib import Path
from flask import Flask, request, jsonify
import logging
import uuid
import shlex

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("FLUXON_SERVER")

app = Flask(__name__)

# Configurações de caminhos - CORRIGIDO
BASE_DIR = Path(__file__).parent.absolute()

# Verifica múltiplas possibilidades para o Python do venv - CORRIGIDO
VENV_PYTHON = None
possible_venv_paths = [
    BASE_DIR.parent / "flux_on" / "venv" / "Scripts" / "python.exe",  # Windows
    BASE_DIR.parent / "flux_on" / "venv" / "bin" / "python",          # Linux/Mac
]

for path in possible_venv_paths:
    if path.exists():
        VENV_PYTHON = path
        break

if not VENV_PYTHON:
    logger.error("Erro: Python do venv não encontrado. Procurou em:")
    for path in possible_venv_paths:
        logger.error(f" - {path}")
    sys.exit(1)
    
SCRIPTS_DIR = BASE_DIR / "scripts"
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)

# Scripts autorizados (ajuste os caminhos conforme necessário)
AUTHORIZED_SCRIPTS = {
    "trading": {
        "path": "day_trade/project/main.py",
        "type": "streamlit",
        "port": 8501,
        "desc": "Sistema de Day Trading"
    },
    "betting": {
        "path": "project/main.py",
        "type": "streamlit",
        "port": 8502,
        "desc": "Apostas Esportivas"
    },
    "apostapro": {
        "path": "ApostaPro/main.py",
        "type": "streamlit",
        "port": 8503,
        "desc": "ApostaPro (backend/CLI)"
    }
}

def get_script_config(script_id):
    """Retorna a configuração completa do script"""
    config = AUTHORIZED_SCRIPTS.get(script_id, {}).copy()
    if not config:
        return None
        
    script_path = (SCRIPTS_DIR / config["path"]).absolute()
    if not script_path.exists():
        raise FileNotFoundError(f"Script não encontrado: {script_path}")
    
    config.update({
        "abs_path": script_path,
        "cwd": script_path.parent
    })
    return config

def run_script(script_id):
    """Executa um script autorizado com todas as configurações necessárias"""
    config = get_script_config(script_id)
    if not config:
        raise ValueError("Script não autorizado ou configuração inválida")
    
    # Cria arquivo de log único
    log_file = LOG_DIR / f"{script_id}_{uuid.uuid4().hex}.log"
    
    # Monta o comando de forma segura para Windows
    cmd = [
        str(VENV_PYTHON),
        "-m", "streamlit", "run",
        str(config["abs_path"]),
        f"--server.port={config['port']}",
        "--server.headless=true",
        "--browser.serverAddress=0.0.0.0"
    ]
    
    # Ambiente com PATH correto
    env = os.environ.copy()
    env.update({
        "PYTHONPATH": str(BASE_DIR),
        "PATH": f"{VENV_PYTHON.parent};{env.get('PATH', '')}"
    })
    
    # Execução segura em Windows
    try:
        with open(log_file, 'w') as log:
            process = subprocess.Popen(
                cmd,
                cwd=str(config["cwd"]),
                env=env,
                stdout=log,
                stderr=subprocess.STDOUT,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
            )
        return process.pid, log_file
    except Exception as e:
        logger.error(f"Erro ao executar script: {e}")
        raise

@app.route('/api/execute', methods=['POST'])
def execute_script():
    """Endpoint para execução remota"""
    try:
        data = request.get_json()
        script_id = data.get('script')
        
        if not script_id or script_id not in AUTHORIZED_SCRIPTS:
            return jsonify({
                'status': 'error',
                'message': 'Script não autorizado ou não especificado'
            }), 400
        
        pid, log_file = run_script(script_id)
        
        return jsonify({
            'status': 'success',
            'pid': pid,
            'log_file': str(log_file.relative_to(LOG_DIR)),
            'message': f'Script {script_id} iniciado com sucesso'
        })
        
    except Exception as e:
        logger.error(f"Erro na execução: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

if __name__ == '__main__':
    # Verificações iniciais
    if not VENV_PYTHON.exists():
        logger.error(f"Erro: Python do venv não encontrado em {VENV_PYTHON}")
        sys.exit(1)
    
    if not SCRIPTS_DIR.exists():
        logger.error(f"Erro: Diretório de scripts não encontrado em {SCRIPTS_DIR}")
        sys.exit(1)
    
    logger.info("Iniciando servidor FLUX-ON...")
    app.run(host='0.0.0.0', port=5000)