# test_token.py
import jwt
from config import SECURITY_CONFIG

def test_token(token):
    try:
        payload = jwt.decode(
            token,
            SECURITY_CONFIG['SECRET_KEY'],
            algorithms=['HS256'],
            options={'verify_exp': True, 'leeway': 10800}
        )
        print("✅ Token válido")
        print("Payload:", payload)
        return True
    except jwt.ExpiredSignatureError:
        print("❌ Token expirado")
        return False
    except jwt.InvalidTokenError as e:
        print(f"❌ Token inválido: {e}")
        return False
    except Exception as e:
        print(f"❌ Erro: {e}")
        return False

if __name__ == "__main__":
    # Cole seu token aqui
    token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJlbWFpbCI6ImFkbWluQGZsdXhvbi5jb20iLCJleHAiOjE3NTU2MzEzNzl9.IU4-HX2mpNDjsisBjzaLtIXPNnQf8GjnL6dCWeDAfH8"
    test_token(token)