import hashlib
import platform
import uuid

def get_hardware_id():
    # Combina informações únicas do sistema
    hw_info = f"{platform.node()}{uuid.getnode()}"
    return hashlib.sha256(hw_info.encode()).hexdigest()[:16]  # ID de 16 chars