# admin_tool.py (atualizado)
import sqlite3
import secrets
import argparse
from datetime import datetime, timedelta
import requests  # Para integração com API de pagamentos

# Configurações do Gateway de Pagamento (exemplo com Mercado Pago)
PAYMENT_GATEWAY = {
    'API_URL': 'https://api.mercadopago.com',
    'ACCESS_TOKEN': 'SEU_ACCESS_TOKEN_AQUI',
    'WEBHOOK_SECRET': 'SEU_WEBHOOK_SECRET'
}

def generate_payment_link(email, months=1, value=99.90):
    """Gera um link de pagamento para a licença mensal."""
    try:
        headers = {
            'Authorization': f'Bearer {PAYMENT_GATEWAY["ACCESS_TOKEN"]}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            "items": [
                {
                    "title": f"Licença PRO ({months} meses)",
                    "quantity": 1,
                    "unit_price": value * months,
                    "currency_id": "BRL"
                }
            ],
            "payer": {
                "email": email
            },
            "back_urls": {
                "success": "http://seusite.com/success",
                "pending": "http://seusite.com/pending",
                "failure": "http://seusite.com/failure"
            },
            "auto_return": "approved",
            "notification_url": "http://seusite.com/webhook",
            "metadata": {
                "product_type": "software_license",
                "months": months,
                "customer_email": email
            }
        }
        
        response = requests.post(
            f"{PAYMENT_GATEWAY['API_URL']}/checkout/preferences",
            headers=headers,
            json=payload
        )
        
        if response.status_code == 201:
            payment_data = response.json()
            return payment_data['init_point'], payment_data['id']
        else:
            print(f"❌ Erro ao gerar link de pagamento: {response.text}")
            return None, None
            
    except Exception as e:
        print(f"❌ Erro na comunicação com o gateway: {str(e)}")
        return None, None

def generate_key(email, months=1, payment_id=None, value=None):
    """Gera uma nova chave de licença mensal."""
    conn = sqlite3.connect('licenses.db')
    cursor = conn.cursor()
    
    new_key = f"PRO-{secrets.token_hex(4).upper()}-{secrets.token_hex(4).upper()}"
    expiration_date = (datetime.now() + timedelta(days=30*months)).isoformat()
    
    try:
        cursor.execute(
            "INSERT INTO licenses (key, email, expiration_date, payment_id, value, status) VALUES (?, ?, ?, ?, ?, ?)", 
            (new_key, email, expiration_date, payment_id, value, 'pendente' if payment_id else 'disponivel')
        )
        conn.commit()
        print(f"✅ Chave gerada com sucesso para '{email}'!")
        print(f"   🔑 Chave: {new_key}")
        print(f"   ⏳ Expira em: {expiration_date[:10]} ({months} meses)")
        if payment_id:
            print(f"   💳 ID Pagamento: {payment_id}")
        return new_key
    except sqlite3.IntegrityError:
        print("❌ Erro: Chave gerada já existe. Tente novamente.")
        return None
    finally:
        conn.close()

def process_payment_notification(payment_id):
    """Processa notificação de pagamento confirmado."""
    conn = sqlite3.connect('licenses.db')
    cursor = conn.cursor()
    
    try:
        # Verifica o status do pagamento
        headers = {
            'Authorization': f'Bearer {PAYMENT_GATEWAY["ACCESS_TOKEN"]}',
            'Content-Type': 'application/json'
        }
        
        response = requests.get(
            f"{PAYMENT_GATEWAY['API_URL']}/v1/payments/{payment_id}",
            headers=headers
        )
        
        if response.status_code == 200:
            payment_data = response.json()
            
            if payment_data['status'] == 'approved':
                # Atualiza a licença associada a este pagamento
                cursor.execute(
                    "UPDATE licenses SET status='ativo' WHERE payment_id=?",
                    (payment_id,)
                )
                conn.commit()
                
                # Obtém os dados para enviar por email
                cursor.execute(
                    "SELECT key, email FROM licenses WHERE payment_id=?",
                    (payment_id,)
                )
                license_data = cursor.fetchone()
                
                if license_data:
                    print(f"✅ Pagamento {payment_id} confirmado!")
                    print(f"   📩 Enviando chave para: {license_data[1]}")
                    # Aqui você implementaria o envio do email
                    return True
        return False
    except Exception as e:
        print(f"❌ Erro ao processar pagamento: {str(e)}")
        return False
    finally:
        conn.close()

def list_keys():
    """Lista todas as chaves de licença no banco de dados."""
    conn = sqlite3.connect('licenses.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM licenses")
    rows = cursor.fetchall()
    conn.close()
    
    if not rows:
        print("Nenhuma licença encontrada.")
        return
        
    print("-" * 90)
    print(f"{'CHAVE':<25} {'EMAIL':<25} {'STATUS':<12} {'EXPIRAÇÃO':<12} {'ID DISPOSITIVO'}")
    print("-" * 90)
    for row in rows:
        device_id = row['device_id'] if row['device_id'] else "N/A"
        exp_date = row['expiration_date'][:10] if row['expiration_date'] else "N/A"
        print(f"{row['key']:<25} {row['email']:<25} {row['status']:<12} {exp_date:<12} {device_id}")
    print("-" * 90)

def activate_key(key, device_id):
    """Ativa uma chave associando-a a um dispositivo."""
    conn = sqlite3.connect('licenses.db')
    cursor = conn.cursor()
    
    try:
        # Verifica se a chave existe e está disponível
        cursor.execute("SELECT expiration_date FROM licenses WHERE key=? AND status='disponivel'", (key,))
        result = cursor.fetchone()
        
        if not result:
            print("❌ Erro: Chave inválida ou já utilizada.")
            return
        
        # Atualiza a licença
        activation_date = datetime.now().isoformat()
        cursor.execute(
            "UPDATE licenses SET status='ativo', device_id=?, activation_date=? WHERE key=?", 
            (device_id, activation_date, key))
        conn.commit()
        print(f"✅ Chave {key} ativada para o dispositivo {device_id}!")
        print(f"   ⏳ Expira em: {result[0][:10]}")
    except sqlite3.Error as e:
        print(f"❌ Erro ao ativar chave: {e}")
    finally:
        conn.close()

def renew_key(key, months=1):
    """Renova uma licença existente por mais meses."""
    conn = sqlite3.connect('licenses.db')
    cursor = conn.cursor()
    
    try:
        # Obtém a data de expiração atual
        cursor.execute("SELECT expiration_date FROM licenses WHERE key=?", (key,))
        result = cursor.fetchone()
        
        if not result:
            print("❌ Erro: Chave não encontrada.")
            return
        
        # Calcula nova data de expiração
        current_exp = datetime.fromisoformat(result[0]) if result[0] else datetime.now()
        new_expiration = (current_exp + timedelta(days=30*months)).isoformat()
        
        # Atualiza no banco de dados
        cursor.execute(
            "UPDATE licenses SET expiration_date=?, status='ativo' WHERE key=?", 
            (new_expiration, key))
        conn.commit()
        print(f"✅ Licença {key} renovada por mais {months} mês(es)!")
        print(f"   🆕 Nova data de expiração: {new_expiration[:10]}")
    except sqlite3.Error as e:
        print(f"❌ Erro ao renovar licença: {e}")
    finally:
        conn.close()

if __name__ == '__main__':
    # Inicializa o banco de dados
    conn = sqlite3.connect('licenses.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS licenses (
            key TEXT PRIMARY KEY,
            email TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'disponivel',
            device_id TEXT,
            activation_date TEXT,
            expiration_date TEXT,
            payment_id TEXT,
            value REAL
        )
    ''')
    conn.close()

    parser = argparse.ArgumentParser(description="Ferramenta de Administração de Licenças Mensais")
    subparsers = parser.add_subparsers(dest='command', required=True)

    # Comando para gerar uma chave
    parser_gen = subparsers.add_parser('generate', help='Gera uma nova chave de licença.')
    parser_gen.add_argument('--email', required=True, help='Email do cliente para associar à chave.')
    parser_gen.add_argument('--months', type=int, default=1, help='Número de meses de validade.')

    # Comando para listar chaves
    parser_list = subparsers.add_parser('list', help='Lista todas as chaves existentes.')

    # Comando para ativar uma chave
    parser_activate = subparsers.add_parser('activate', help='Ativa uma chave para um dispositivo.')
    parser_activate.add_argument('--key', required=True, help='Chave de licença a ser ativada.')
    parser_activate.add_argument('--device-id', required=True, help='ID do dispositivo do cliente.')

    # Comando para renovar uma chave
    parser_renew = subparsers.add_parser('renew', help='Renova uma licença existente.')
    parser_renew.add_argument('--key', required=True, help='Chave de licença a ser renovada.')
    parser_renew.add_argument('--months', type=int, default=1, help='Número de meses para adicionar.')

    # Comando para vender via link de pagamento (NOVO)
    parser_sell = subparsers.add_parser('sell', help='Vende uma nova licença via link de pagamento.')
    parser_sell.add_argument('--email', required=True, help='Email do cliente.')
    parser_sell.add_argument('--months', type=int, default=1, help='Duração em meses.')
    parser_sell.add_argument('--value', type=float, default=99.90, help='Valor mensal.')

    args = parser.parse_args()

    if args.command == 'generate':
        generate_key(args.email, args.months)
    elif args.command == 'list':
        list_keys()
    elif args.command == 'activate':
        activate_key(args.key, args.device_id)
    elif args.command == 'renew':
        renew_key(args.key, args.months)
    elif args.command == 'sell':  # NOVO COMANDO
        payment_link, payment_id = generate_payment_link(args.email, args.months, args.value)
        if payment_link:
            print(f"🛒 Link de pagamento gerado para {args.email}:")
            print(payment_link)
            print("\n📝 Esta licença será gerada automaticamente após confirmação do pagamento.")
            
            # Pré-cadastra a licença (status ficará como 'pendente' até confirmação)
            generate_key(args.email, args.months, payment_id)