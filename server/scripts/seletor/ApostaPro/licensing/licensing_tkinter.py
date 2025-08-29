import tkinter as tk
from tkinter import messagebox
from licensing_manager import LicenseManager

class LicenseTkinterApp:
    def __init__(self, master):
        self.master = master
        self.manager = LicenseManager()
        self._setup_ui()
        
    def _setup_ui(self):
        self.master.title("Ativação de Licença")
        
        tk.Label(self.master, text="Chave de Licença:").pack()
        self.license_entry = tk.Entry(self.master, width=40)
        self.license_entry.pack()
        
        tk.Button(self.master, text="Validar", command=self._validate).pack(pady=10)
        
    def _validate(self):
        key = self.license_entry.get()
        result = self.manager.verify(key, strict_check=True)
        
        if result['valid']:
            messagebox.showinfo("Sucesso", "Licença válida!")
            self.master.destroy()  # Fecha a janela após validação
        else:
            messagebox.showerror("Erro", result.get('message', 'Licença inválida'))