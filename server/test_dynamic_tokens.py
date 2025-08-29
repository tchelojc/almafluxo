# test_dynamic_tokens.py
from token_manager import token_manager, validate_token, generate_token, get_dynamic_url

def test_dynamic_tokens():
    print("🧪 Testando sistema de tokens dinâmicos...")
    
    # Teste 1: Geração de token
    token = generate_token(1, "admin@fluxon.com", True)
    print(f"✅ Token gerado: {token[:50]}...")
    
    # Teste 2: Validação de token
    payload = validate_token(token)
    if payload:
        print(f"✅ Token válido: {payload}")
    else:
        print("❌ Token inválido")
        return
    
    # Teste 3: URL dinâmica
    dynamic_url, new_token = get_dynamic_url(1, "admin@fluxon.com", True)
    print(f"✅ URL dinâmica: {dynamic_url}")
    print(f"✅ Novo token: {new_token[:50]}...")
    
    # Teste 4: Validação do novo token
    new_payload = validate_token(new_token)
    if new_payload:
        print(f"✅ Novo token válido: {new_payload}")
    else:
        print("❌ Novo token inválido")

if __name__ == "__main__":
    test_dynamic_tokens()