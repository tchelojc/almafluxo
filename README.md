cat > README.md << 'EOL'
# ALMA Fluxo Platform

Sistema completo de análise de dados com múltiplos módulos integrados.

## 🚀 Funcionalidades

- **Dashboard Principal**: Visualização de dados e métricas
- **Day Trade**: Análise de mercado financeiro em tempo real
- **Análise Esportiva**: Estatísticas e previsões esportivas
- **Aposta Pro**: Plataforma de apostas profissionais

## 🛠️ Tecnologias

- Python 3.10+
- Streamlit 1.48.1
- FastAPI 0.116.1
- Flask 3.1.1
- Pandas 2.3.1
- Plotly 6.3.0

## 📦 Instalação

```bash
# Clone o repositório
git clone https://github.com/tchelojc/almafluxo.git
cd almafluxo

# Crie ambiente virtual
python -m venv venv

# Ative o ambiente
# Linux/Mac:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# Instale dependências
pip install -r requirements.txt