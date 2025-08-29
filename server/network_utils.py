import socket

def get_local_ip():
    """
    Obtém o IP local da máquina de forma confiável
    Retorna:
        str: IP local ou '127.0.0.1' se não conseguir determinar
    """
    try:
        # Tentativa 1: Conexão com DNS público (mais confiável)
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.settimeout(0.1)  # Timeout para não travar se offline
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except Exception:
        try:
            # Tentativa 2: Usando hostname (menos confiável)
            hostname = socket.gethostname()
            local_ip = socket.gethostbyname(hostname)
            if local_ip.startswith('127.'):
                raise ValueError("IP local inválido")
            return local_ip
        except Exception:
            # Fallback para localhost
            return "127.0.0.1"