import gspread
from google.oauth2.service_account import Credentials
from config import Config

class GerenciadorPlanilha:
    def __init__(self):
        # Configuração das credenciais e da planilha
        self.CREDENTIALS_FILE = r"C:\Users\Marcelo\Downloads\chaves google\credenciais.json"
        self.PLANILHA_ID = "1VN55T_2FykOZEL2WJab2HObV9BlNGpqCRaQoAgBUIAo"
        self.TAB_NAME = "Finalização"
        
        # Escopos necessários para acessar o Google Sheets
        self.scope = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        
        # Autenticação
        self.creds = Credentials.from_service_account_file(
            self.CREDENTIALS_FILE, scopes=self.scope
        )
        self.client = gspread.authorize(self.creds)
        
        # Abertura da planilha e da aba
        self.planilha = self.client.open_by_key(self.PLANILHA_ID)
        self.worksheet = self.planilha.worksheet(self.TAB_NAME)

    def registrar_apostas(self, dados):
        try:
            self.worksheet.append_row(dados)
            print("Dados registrados com sucesso.")
            return True
        except Exception as e:
            print(f"Erro ao registrar: {e}")
            return False
