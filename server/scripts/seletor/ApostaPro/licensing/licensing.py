import os
import sys
import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import pytz
import requests
import socket
import struct
from datetime import datetime, timedelta, timezone
from timezonefinder import TimezoneFinder
import geocoder
import hashlib
import uuid
import csv
import json
import pandas as pd
import pyperclip
from tkcalendar import DateEntry
import hmac
import platform
import time
from typing import Optional, Dict, Tuple, Any

try:
    import streamlit as st
except ImportError:
    st = None  # Permite que o código execute sem Streamlit

# Configurações globais
INIT_MODE = None
SECRET_KEY = "sua-chave-secreta-muito-longa-e-complexa-aqui"
SERVER_URL = "http://localhost:5000"
MAX_OFFLINE_DAYS = 7  # Máximo de dias para operar offline

class QuantumTimeValidator:
    """Validador de tempo com tolerância quântica para sincronização"""
    def __init__(self):
        self.allowed_drift = timedelta(minutes=5)
        self.last_sync = None
        self.sync_interval = 300000  # 5 minutos
        self.root.after(self.sync_interval, self.sync_with_server)
        
    def sync_with_server(self):
        """Sincroniza dados locais com o servidor"""
        try:
            # Obtém todas as licenças modificadas localmente
            self.cursor.execute("""
                SELECT key, status, device_id, expiration_date, last_modified
                FROM licenses
                WHERE last_modified > datetime('now', '-1 hour')
            """)
            modified_licenses = [dict(zip(
                ['key', 'status', 'device_id', 'expiration_date', 'last_modified'], 
                row
            )) for row in self.cursor.fetchall()]
            
            # Envia para o servidor
            if modified_licenses:
                result = self.server._make_request("api/admin/sync_data", data={
                    'licenses': modified_licenses,
                    'last_sync': self.get_last_sync_time()
                })
                
                if result and result.get('success'):
                    self.update_local_with_server_changes(result.get('changes', []))
            
            # Agenda próxima sincronização
            self.root.after(self.sync_interval, self.sync_with_server)
            
        except Exception as e:
            print(f"Erro na sincronização: {e}")
            # Tenta novamente em 1 minuto em caso de erro
            self.root.after(60000, self.sync_with_server)
            
    def get_last_sync_time(self):
        """Obtém o último horário de sincronização bem-sucedida"""
        try:
            self.cursor.execute("SELECT value FROM settings WHERE key = 'last_sync'")
            result = self.cursor.fetchone()
            return result[0] if result else "2000-01-01T00:00:00"
        except:
            return "2000-01-01T00:00:00"
            
    def update_local_with_server_changes(self, changes):
        """Atualiza o banco local com alterações do servidor"""
        try:
            self.cursor.execute("BEGIN TRANSACTION")
            
            for change in changes:
                self.cursor.execute("""
                    UPDATE licenses SET
                        status = ?,
                        device_id = ?,
                        expiration_date = ?,
                        last_modified = ?
                    WHERE key = ?
                """, (
                    change['status'],
                    change['device_id'],
                    change['expiration_date'],
                    change['last_modified'],
                    change['key']
                ))
                
            # Atualiza último sync
            self.cursor.execute("""
                INSERT OR REPLACE INTO settings (key, value)
                VALUES ('last_sync', ?)
            """, (datetime.now().isoformat(),))
            
            self.conn.commit()
            
        except Exception as e:
            self.conn.rollback()
            print(f"Erro ao aplicar alterações do servidor: {e}")
            
    def get_adjusted_time(self) -> datetime:
        if self.last_sync and (datetime.now() - self.last_sync) < timedelta(hours=1):
            return datetime.now() + self.time_diff
        return datetime.now()

class SecureConnection:
    """Gerencia conexões seguras com o servidor de licenças"""
    def __init__(self, secret_key: str):
        self.secret_key = secret_key
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'LicenseManager/2.0',
            'Accept': 'application/json'
        })
        
    def generate_hmac(self, message: str) -> str:
        """Gera HMAC-SHA256 da mensagem"""
        return hmac.new(
            self.secret_key.encode(),
            message.encode(),
            'sha256'
        ).hexdigest()
        
    def make_request(self, endpoint: str, payload: Dict) -> Optional[Dict]:
        """Faz requisição segura ao servidor"""
        try:
            timestamp = datetime.now().isoformat()
            message = f"{endpoint}{timestamp}{json.dumps(payload, sort_keys=True)}"
            signature = self.generate_hmac(message)
            
            headers = {
                'X-Signature': signature,
                'X-Timestamp': timestamp,
                'X-Endpoint': endpoint
            }
            
            response = self.session.post(
                f"{SERVER_URL}/{endpoint}",
                json=payload,
                headers=headers,
                timeout=5
            )
            
            # Verifica assinatura da resposta
            if not self._verify_response(response):
                raise ValueError("Invalid server response signature")
                
            return response.json()
        except Exception as e:
            print(f"Request error: {str(e)}")
            return None
            
    def _verify_response(self, response) -> bool:
        """Verifica assinatura HMAC da resposta do servidor"""
        server_signature = response.headers.get('X-Signature')
        if not server_signature:
            return False
            
        expected = self.generate_hmac(response.text)
        return hmac.compare_digest(server_signature, expected)

class LicenseValidator:
    """Validador principal de licenças com múltiplas camadas"""
    def __init__(self, db_conn: sqlite3.Connection):
        self.conn = db_conn
        self.secure_conn = SecureConnection(SECRET_KEY)
        self.time_validator = QuantumTimeValidator()
        self.device_id = self._get_device_id()
        self.license_file = self._get_license_path()
        
    def _get_device_id(self) -> str:
        """Gera ID único do dispositivo"""
        try:
            # Windows
            if platform.system() == "Windows":
                import winreg
                with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, 
                                  r"SOFTWARE\Microsoft\Cryptography") as key:
                    return winreg.QueryValueEx(key, "MachineGuid")[0]
            # Linux/Mac
            with open("/etc/machine-id") as f:
                return f.read().strip()
        except:
            return str(uuid.getnode())
            
    def _get_license_path(self) -> str:
        """Retorna o caminho padrão do arquivo de licença"""
        system = platform.system()
        if system == "Windows":
            path = os.path.join(os.getenv('LOCALAPPDATA'), 'OperadorConquistador', 'license.json')
        elif system == "Linux":
            path = os.path.join(os.path.expanduser("~"), '.config', 'operador_conquistador', 'license.json')
        else:  # MacOS
            path = os.path.join(os.path.expanduser("~"), 'Library', 'Application Support', 'OperadorConquistador', 'license.json')
        
        os.makedirs(os.path.dirname(path), exist_ok=True)
        return path
        
    def validate_license(self, force_online: bool = False) -> Dict[str, Any]:
        """Validação principal da licença com múltiplas camadas"""
        # 1. Verificação local básica
        local_data = self._check_local_license()
        if not local_data.get('valid'):
            return {
                'valid': False,
                'reason': 'local_validation_failed',
                'message': 'Falha na verificação local da licença'
            }
            
        # 2. Verificação do banco de dados local
        db_check = self._check_database(local_data['license_key'])
        if not db_check.get('valid'):
            return db_check
            
        # 3. Verificação com servidor (condicional)
        if force_online or self._should_check_server(local_data):
            server_check = self._check_with_server(local_data['license_key'])
            if not server_check.get('valid'):
                return server_check
                
        # 4. Verificação de tempo (não bloqueante)
        if not self.time_validator.sync_with_server():
            print("Aviso: Problema na sincronização de tempo")
            
        return {
            'valid': True,
            'expiration': db_check.get('expiration'),
            'is_trial': db_check.get('is_trial', False)
        }
        
    def _check_local_license(self) -> Dict[str, Any]:
        """Verifica a licença local com assinatura digital"""
        try:
            if not os.path.exists(self.license_file):
                return {'valid': False}
                
            with open(self.license_file) as f:
                data = json.load(f)
                
            required_fields = ['license_key', 'device_id', 'expiration', 'signature']
            if not all(field in data for field in required_fields):
                return {'valid': False}
                
            # Verifica assinatura
            sign_data = f"{data['license_key']}{data['device_id']}{data['expiration']}"
            expected_sig = hmac.new(SECRET_KEY.encode(), sign_data.encode(), 'sha256').hexdigest()
            if not hmac.compare_digest(data['signature'], expected_sig):
                return {'valid': False, 'tampered': True}
                
            # Verifica dispositivo
            if data['device_id'] != self.device_id:
                return {'valid': False, 'wrong_device': True}
                
            return {
                'valid': True,
                'license_key': data['license_key'],
                'expiration': data['expiration']
            }
        except:
            return {'valid': False}
            
    def _check_database(self, license_key: str) -> Dict[str, Any]:
        """Verifica a licença no banco de dados local"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT status, expiration_date, is_trial 
                FROM licenses 
                WHERE key = ? AND (expiration_date IS NULL OR expiration_date > ?)
            """, (license_key, datetime.now().isoformat()))
            
            result = cursor.fetchone()
            if not result:
                return {'valid': False, 'reason': 'license_not_found'}
                
            status, expiration, is_trial = result
            if status != 'ativada':
                return {
                    'valid': False,
                    'reason': 'invalid_status',
                    'status': status
                }
                
            return {
                'valid': True,
                'expiration': expiration,
                'is_trial': bool(is_trial)
            }
        except sqlite3.Error as e:
            return {'valid': False, 'reason': 'database_error', 'error': str(e)}
            
    def _should_check_server(self, local_data: Dict) -> bool:
        """Determina quando verificar com o servidor"""
        # Verifica periodicamente (pelo menos uma vez por dia)
        last_check = local_data.get('last_server_check')
        if not last_check:
            return True
            
        try:
            last_check_date = datetime.fromisoformat(last_check)
            return (datetime.now() - last_check_date) > timedelta(hours=24)
        except:
            return True
            
    def _check_with_server(self, license_key: str) -> Dict[str, Any]:
        """Verifica a licença com o servidor remoto"""
        try:
            payload = {
                'license_key': license_key,
                'device_id': self.device_id,
                'local_time': datetime.now().isoformat()
            }
            
            response = self.secure_conn.make_request('api/validate', payload)
            if not response:
                return {'valid': False, 'reason': 'connection_error'}
                
            if not response.get('valid'):
                return {
                    'valid': False,
                    'reason': 'server_rejected',
                    'message': response.get('message', '')
                }
                
            # Atualiza último check no arquivo local
            self._update_last_check(license_key)
            
            return {'valid': True, 'server_validated': True}
        except Exception as e:
            return {'valid': False, 'reason': 'exception', 'error': str(e)}
            
    def _update_last_check(self, license_key: str) -> None:
        """Atualiza o último check com o servidor no arquivo local"""
        try:
            with open(self.license_file, 'r+') as f:
                data = json.load(f)
                data['last_server_check'] = datetime.now().isoformat()
                f.seek(0)
                json.dump(data, f, indent=4)
                f.truncate()
        except:
            pass

class LicenseManagerApp:
    """Interface gráfica para gerenciamento de licenças"""
    def __init__(self, root):
        self.root = root
        self.root.title("Gerenciador de Licenças")
        self.root.geometry("800x600")
        
        # Inicializa componentes
        self.db_conn = self._init_database()
        self.validator = LicenseValidator(self.db_conn)
        
        self._setup_ui()
        self._check_initial_license()
        
    def _init_database(self) -> sqlite3.Connection:
        """Inicializa/Conexão com o banco de dados"""
        try:
            conn = sqlite3.connect('licenses.db')
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA foreign_keys=ON")
            return conn
        except sqlite3.Error as e:
            messagebox.showerror("Erro de Banco de Dados", f"Não foi possível conectar ao banco: {str(e)}")
            raise
            
    def _setup_ui(self):
        """Configura a interface do usuário"""
        self.notebook = ttk.Notebook(self.root)
        
        # Aba de validação
        self.validation_frame = ttk.Frame(self.notebook)
        self._setup_validation_tab()
        
        # Aba de administração
        self.admin_frame = ttk.Frame(self.notebook)
        self._setup_admin_tab()
        
        self.notebook.add(self.validation_frame, text="Validação")
        self.notebook.add(self.admin_frame, text="Administração")
        self.notebook.pack(expand=True, fill='both')
        
    def _setup_validation_tab(self):
        """Configura a aba de validação de licença"""
        ttk.Label(self.validation_frame, text="Status da Licença:").pack(pady=10)
        
        self.status_var = tk.StringVar(value="Verificando...")
        ttk.Label(self.validation_frame, textvariable=self.status_var, font=('Arial', 12)).pack()
        
        self.details_var = tk.StringVar()
        ttk.Label(self.validation_frame, textvariable=self.details_var, wraplength=400).pack(pady=10)
        
        ttk.Button(self.validation_frame, text="Validar Agora", command=self._validate_license).pack(pady=20)
        ttk.Button(self.validation_frame, text="Ativar Licença", command=self._show_activation_dialog).pack()
        
    def _setup_admin_tab(self):
        """Configura a aba administrativa"""
        ttk.Label(self.admin_frame, text="Gerenciamento de Licenças", font=('Arial', 12)).pack(pady=10)
        
        # Controles administrativos
        ttk.Button(self.admin_frame, text="Sincronizar com Servidor", 
                  command=self._sync_with_server).pack(pady=5)
        ttk.Button(self.admin_frame, text="Ver Licenças Locais", 
                  command=self._show_local_licenses).pack(pady=5)
        ttk.Button(self.admin_frame, text="Exportar Relatório", 
                  command=self._export_report).pack(pady=5)
                  
    def _check_initial_license(self):
        """Verifica a licença na inicialização"""
        result = self.validator.validate_license()
        self._update_status_display(result)
        
    def _validate_license(self):
        """Executa validação completa da licença"""
        result = self.validator.validate_license(force_online=True)
        self._update_status_display(result)
        
        if not result['valid']:
            messagebox.showerror("Erro de Licença", result.get('message', 'Licença inválida'))
            
    def bloquear_licenca(self):
        selected = self.tree.focus()
        if not selected:
            messagebox.showwarning("Aviso", "Selecione uma licença na tabela!")
            return

        item = self.tree.item(selected)
        chave = item['values'][0]
        status_atual = item['values'][2]

        if status_atual == "bloqueada":
            novo_status = "disponivel"
            msg = f"Desbloquear a licença {chave}?"
        else:
            novo_status = "bloqueada"
            msg = f"Bloquear a licença {chave}?"

        if messagebox.askyesno("Confirmar", msg):
            try:
                # Comunica com o servidor
                result = self.server.block_license(chave, novo_status)
                
                if not result or not result.get('success'):
                    raise Exception(result.get('message', 'Resposta inválida do servidor'))
                    
                # Atualiza localmente
                self.cursor.execute("""
                    UPDATE licenses 
                    SET status = ?,
                        last_modified = datetime('now')
                    WHERE key = ?
                """, (novo_status, chave))
                
                self.conn.commit()
                self.carregar_dados()
                messagebox.showinfo("Sucesso", result.get('message', 'Status alterado com sucesso'))
                
            except Exception as e:
                self.conn.rollback()
                messagebox.showerror("Erro", f"Falha ao alterar status:\n{e}")
                
    def verificar_tempo_sistema(self):
        """Janela aprimorada de verificação de tempo"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Verificação de Sincronização de Tempo")
        dialog.geometry("550x400")
        
        # Frame principal
        main_frame = ttk.Frame(dialog, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Título
        ttk.Label(main_frame, text="Sincronização Temporal", font=('TkDefaultFont', 12, 'bold')).pack(pady=5)
        
        # Frame de resultados
        result_frame = ttk.LabelFrame(main_frame, text="Resultados", padding="10")
        result_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Obter tempos
        local_time = datetime.now()
        server_time = self.server.get_server_time()
        
        # Exibir comparação
        rows = [
            ("Horário Local:", local_time.strftime("%Y-%m-%d %H:%M:%S")),
            ("Horário do Servidor:", server_time.get('server_time', 'Erro ao obter')),
            ("Diferença:", self._format_time_diff(local_time, server_time)),
            ("Status:", self._get_sync_status(local_time, server_time))
        ]
        
        for i, (label, value) in enumerate(rows):
            ttk.Label(result_frame, text=label, font=('TkDefaultFont', 9, 'bold')).grid(row=i, column=0, sticky=tk.W, pady=2)
            ttk.Label(result_frame, text=value).grid(row=i, column=1, sticky=tk.W, pady=2)
            
        # Botões
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(btn_frame, text="Sincronizar Agora", command=self._force_time_sync).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Fechar", command=dialog.destroy).pack(side=tk.RIGHT, padx=5)
        
    def _format_time_diff(self, local_time, server_time):
        """Formata a diferença de tempo de forma legível"""
        if not server_time.get('success') or 'server_time' not in server_time:
            return "Não disponível"
            
        try:
            server_dt = datetime.fromisoformat(server_time['server_time']) if isinstance(server_time['server_time'], str) else server_time['server_time']
            diff = local_time - server_dt
            diff_seconds = abs(diff.total_seconds())
            
            if diff_seconds < 60:
                return f"{diff_seconds:.1f} segundos"
            elif diff_seconds < 3600:
                return f"{diff_seconds/60:.1f} minutos"
            else:
                return f"{diff_seconds/3600:.1f} horas"
        except:
            return "Erro no cálculo"
            
    def _get_sync_status(self, local_time, server_time):
        """Retorna o status de sincronização com cor"""
        if not server_time.get('success'):
            return ("Erro na conexão", "red")
            
        try:
            server_dt = datetime.fromisoformat(server_time['server_time']) if isinstance(server_time['server_time'], str) else server_time['server_time']
            diff = abs((local_time - server_dt).total_seconds())
            
            if diff < 5:
                return ("Sincronizado", "green")
            elif diff < 60:
                return ("Pequena diferença", "orange")
            else:
                return ("Fora de sincronia", "red")
        except:
            return ("Erro na verificação", "red")
            
    def _force_time_sync(self):
        """Força uma sincronização imediata"""
        self.sync_with_server()
        messagebox.showinfo("Info", "Sincronização forçada iniciada. Os dados serão atualizados em breve.")

    def excluir_licenca(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Aviso", "Selecione uma licença na tabela!")
            return
        
        item = self.tree.item(selected[0])
        chave = item['values'][0]

        if messagebox.askyesno("Confirmar", f"Excluir permanentemente a licença {chave}?"):
            try:
                # 1. Verifica se é uma chave temporária
                self.cursor.execute("SELECT is_temporary FROM licenses WHERE key = ?", (chave,))
                is_temp = self.cursor.fetchone()[0]
                
                # 2. Comunica com o servidor
                result = self.server.delete_license(chave)
                if not result or not result.get('success'):
                    raise Exception(result.get('message', 'Resposta inválida do servidor'))
                
                # 3. Exclusão local transacional
                self.cursor.execute("BEGIN TRANSACTION")
                self.cursor.execute("DELETE FROM licenses WHERE key = ?", (chave,))
                if is_temp:
                    self.cursor.execute("DELETE FROM temp_keys WHERE key = ?", (chave,))
                
                self.conn.commit()
                messagebox.showinfo("Sucesso", "Licença excluída com sucesso")
                self.carregar_dados()
                
            except Exception as e:
                self.conn.rollback()
                messagebox.showerror("Erro", f"Falha ao excluir licença:\n{str(e)}")
                
    def criar_chave_temporaria(self):
        """Janela aprimorada para criação de chaves temporárias"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Gerar Chave Temporária")
        dialog.geometry("500x400")
        
        # Variáveis
        email_var = tk.StringVar()
        duration_var = tk.StringVar(value="60")
        duration_unit = tk.StringVar(value="minutes")
        uses_var = tk.IntVar(value=1)
        notes_var = tk.StringVar()
        
        # Widgets
        ttk.Label(dialog, text="E-mail do Usuário:").pack(pady=(10, 0))
        ttk.Entry(dialog, textvariable=email_var, width=40).pack()
        
        ttk.Label(dialog, text="Duração:").pack(pady=(10, 0))
        
        duration_frame = ttk.Frame(dialog)
        duration_frame.pack()
        
        ttk.Entry(duration_frame, textvariable=duration_var, width=5).pack(side=tk.LEFT)
        ttk.Combobox(duration_frame, textvariable=duration_unit, 
                    values=["minutes", "hours", "days"], width=8).pack(side=tk.LEFT, padx=5)
        
        ttk.Label(dialog, text="Número de Usos:").pack(pady=(10, 0))
        ttk.Spinbox(dialog, from_=1, to=10, textvariable=uses_var, width=5).pack()
        
        ttk.Label(dialog, text="Observações (opcional):").pack(pady=(10, 0))
        ttk.Entry(dialog, textvariable=notes_var, width=40).pack()
        
        ttk.Button(dialog, text="Gerar Chave", 
                  command=lambda: self._generate_temp_key_advanced(
                      dialog,
                      email_var.get(),
                      duration_var.get(),
                      duration_unit.get(),
                      uses_var.get(),
                      notes_var.get()
                  )).pack(pady=15)
                  
    def _generate_temp_key_advanced(self, window, email, duration, unit, uses, notes):
        """Gera chave temporária com opções avançadas"""
        if not email or '@' not in email:
            messagebox.showwarning("Aviso", "Informe um e-mail válido!")
            return
            
        try:
            duration = int(duration)
            if duration <= 0:
                raise ValueError
                
            # Converter para minutos
            if unit == "hours":
                duration *= 60
            elif unit == "days":
                duration *= 1440
                
            # Comunica com o servidor
            result = self.server.create_temp_key(email, duration)
            
            if not result or not result.get('success'):
                raise Exception(result.get('message', 'Resposta inválida do servidor'))
                
            temp_key = result['key']
            expires_at = result['expires_at']
            
            # Atualiza localmente
            self.cursor.execute("""
                INSERT INTO licenses (key, email, status, expiration_date, is_temporary)
                VALUES (?, ?, 'disponivel', ?, 1)
            """, (temp_key, email, expires_at))

            self.cursor.execute("""
                INSERT INTO temp_keys (key, email, duration_minutes, expires_at, max_uses, notes)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (temp_key, email, duration, expires_at, uses, notes))

            self.conn.commit()
            
            # Mostra resumo
            summary = f"""
            Chave Temporária Criada:
            
            Chave: {temp_key}
            E-mail: {email}
            Validade: {duration} minutos ({expires_at})
            Usos permitidos: {uses}
            Observações: {notes or 'Nenhuma'}
            """
            
            messagebox.showinfo("Sucesso", summary)
            window.destroy()
            self.carregar_chaves_temporarias()
            
        except ValueError:
            messagebox.showerror("Erro", "Duração deve ser um número positivo!")
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao gerar chave:\n{e}")

    def mostrar_detalhes_licenca(self, event=None):
        selected = self.tree.focus()
        if not selected:
            return
            
        item = self.tree.item(selected)
        chave = item['values'][0]
        
        try:
            # Obtém detalhes do servidor
            result = self.server.get_license_details(chave)
            
            if not result or not result.get('success'):
                raise Exception(result.get('message', 'Resposta inválida do servidor'))
                
            license_data = result['license']
            
            # Atualiza a interface
            self.lbl_key.config(text=license_data.get('key', ''))
            self.lbl_email.config(text=license_data.get('email', 'N/A'))
            self.lbl_status.config(text=license_data.get('status', 'N/A'))
            self.lbl_device.config(text=license_data.get('device_id', 'Nenhum'))
            self.lbl_activation.config(text=license_data.get('activation_date', 'N/A'))
            self.lbl_expiration.config(text=license_data.get('expiration_date', 'N/A'))
            
            # Colorir status
            status = license_data.get('status')
            color = {
                "ativada": "green", 
                "bloqueada": "red", 
                "expirada": "orange", 
                "disponivel": "blue"
            }.get(status, "black")
            self.lbl_status.config(foreground=color)
            
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao carregar detalhes:\n{e}")
            
    def _update_status_display(self, validation_result: Dict) -> None:
        """Atualiza a exibição do status na UI"""
        if validation_result['valid']:
            self.status_var.set("Licença Válida")
            exp_date = validation_result.get('expiration', 'indeterminado')
            self.details_var.set(f"Expira em: {exp_date}\nTipo: {'Teste' if validation_result.get('is_trial') else 'Completa'}")
        else:
            self.status_var.set("Licença Inválida")
            reason = validation_result.get('reason', 'desconhecido')
            self.details_var.set(f"Motivo: {reason}\n{validation_result.get('message', '')}")
            
    def _show_activation_dialog(self):
        """Mostra diálogo de ativação de licença"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Ativação de Licença")
        
        ttk.Label(dialog, text="Chave de Licença:").pack(pady=5)
        self.license_entry = ttk.Entry(dialog, width=30)
        self.license_entry.pack(pady=5)
        
        ttk.Label(dialog, text="E-mail (opcional):").pack(pady=5)
        self.email_entry = ttk.Entry(dialog, width=30)
        self.email_entry.pack(pady=5)
        
        ttk.Button(dialog, text="Ativar", command=self._activate_license).pack(pady=10)
        
    def _activate_license(self):
        """Processa a ativação da licença"""
        license_key = self.license_entry.get().strip()
        email = self.email_entry.get().strip()
        
        if not license_key:
            messagebox.showerror("Erro", "Por favor, insira uma chave de licença")
            return
            
        # Verifica se a licença existe localmente
        cursor = self.db_conn.cursor()
        cursor.execute("SELECT 1 FROM licenses WHERE key = ?", (license_key,))
        if not cursor.fetchone():
            messagebox.showerror("Erro", "Chave de licença não encontrada")
            return
            
        # Cria arquivo de licença local
        license_data = {
            'license_key': license_key,
            'device_id': self.validator.device_id,
            'expiration': (datetime.now() + timedelta(days=365)).isoformat(),
            'signature': hmac.new(
                SECRET_KEY.encode(),
                f"{license_key}{self.validator.device_id}{(datetime.now() + timedelta(days=365)).isoformat()}".encode(),
                'sha256'
            ).hexdigest(),
            'last_server_check': datetime.now().isoformat()
        }
        
        try:
            with open(self.validator.license_file, 'w') as f:
                json.dump(license_data, f, indent=4)
                
            messagebox.showinfo("Sucesso", "Licença ativada com sucesso!")
            self._validate_license()
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao ativar licença: {str(e)}")
            
    def _sync_with_server(self):
        """Sincroniza licenças locais com o servidor"""
        try:
            payload = {
                'action': 'sync',
                'licenses': self._get_local_licenses()
            }
            
            response = self.validator.secure_conn.make_request('api/admin/sync', payload)
            if not response or not response.get('success'):
                raise ValueError(response.get('message', 'Resposta inválida do servidor'))
                
            messagebox.showinfo("Sucesso", "Licenças sincronizadas com sucesso!")
        except Exception as e:
            messagebox.showerror("Erro", f"Falha na sincronização: {str(e)}")
            
    def _get_local_licenses(self) -> list:
        """Obtém todas as licenças locais"""
        cursor = self.db_conn.cursor()
        cursor.execute("SELECT key, status, expiration_date FROM licenses")
        return [dict(zip(['key', 'status', 'expiration'], row)) for row in cursor.fetchall()]
        
    def _show_local_licenses(self):
        """Mostra lista de licenças locais em uma nova janela"""
        licenses = self._get_local_licenses()
        
        window = tk.Toplevel(self.root)
        window.title("Licenças Locais")
        
        tree = ttk.Treeview(window, columns=('Key', 'Status', 'Expiration'), show='headings')
        tree.heading('Key', text='Chave')
        tree.heading('Status', text='Status')
        tree.heading('Expiration', text='Expiração')
        
        for lic in licenses:
            tree.insert('', 'end', values=(lic['key'], lic['status'], lic['expiration']))
            
        tree.pack(expand=True, fill='both')
        
    def _export_report(self):
        """Exporta relatório de licenças"""
        filepath = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")]
        )
        
        if not filepath:
            return
            
        licenses = self._get_local_licenses()
        try:
            with open(filepath, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=['key', 'status', 'expiration'])
                writer.writeheader()
                writer.writerows(licenses)
                
            messagebox.showinfo("Sucesso", f"Relatório exportado para {filepath}")
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao exportar: {str(e)}")

if __name__ == '__main__':
    root = tk.Tk()
    app = LicenseManagerApp(root)
    root.mainloop()