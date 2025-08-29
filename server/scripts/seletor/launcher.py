import sys
import os
import subprocess
import signal
from pathlib import Path
import time

def kill_streamlit_processes(port=None):
    """Mata processos Streamlit específicos ou todos"""
    try:
        if os.name == 'nt':  # Windows
            if port:
                # Método mais preciso para Windows com portas específicas
                subprocess.run(f'netstat -ano | findstr :{port}', shell=True, check=True)
                subprocess.run(f'taskkill /F /FI "PID eq {port}"', shell=True)
            else:
                subprocess.run(['taskkill', '/F', '/IM', 'streamlit.exe'], shell=True)
        else:  # Unix/Linux/Mac
            if port:
                subprocess.run(['pkill', '-f', f'streamlit.*{port}'], shell=True)
            else:
                subprocess.run(['pkill', '-f', 'streamlit'], shell=True)
    except subprocess.CalledProcessError:
        print("Nenhum processo Streamlit encontrado para encerrar")
    except Exception as e:
        print(f"Erro ao encerrar processos: {e}")

def launch_platform(platform):
    BASE_DIR = Path(__file__).parent.resolve()
    
    # Encontra o Python do venv - CORRIGIDO
    VENV_PYTHON = None
    possible_venv_paths = [
        BASE_DIR.parent / "flux_on" / "venv" / "Scripts" / "python.exe",
        BASE_DIR.parent / "flux_on" / "venv" / "bin" / "python",
    ]
    
    for path in possible_venv_paths:
        if path.exists():
            VENV_PYTHON = path
            break
    
    if not VENV_PYTHON:
        print("ERRO: Python do venv não encontrado")
        sys.exit(1)
    
    try:
        if platform == "trading":
            working_dir = BASE_DIR / "day_trade" / "project"
            port = 8501
        elif platform == "betting":
            working_dir = BASE_DIR / "project"
            port = 8502
        elif platform == "apostapro":
            working_dir = BASE_DIR / "ApostaPro"
            port = 8503
        else:
            raise ValueError("Plataforma inválida")

        # Fecha qualquer instância anterior na mesma porta
        kill_streamlit_processes(port)
        time.sleep(1)

        # Inicia o novo processo usando o Python do venv explicitamente
        os.chdir(working_dir)
        subprocess.Popen([
            str(VENV_PYTHON), "-m", "streamlit", "run", "main.py",
            "--server.port", str(port),
            "--browser.serverAddress", "localhost",
            "--server.headless", "true"
        ], cwd=working_dir)
        
        print(f"{platform.capitalize()} iniciado na porta {port}")
        
    except Exception as e:
        print(f"Erro ao iniciar plataforma {platform}: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        launch_platform(sys.argv[1])
    else:
        print("Uso: python launcher.py [trading|betting]")