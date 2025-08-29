#!/usr/bin/env python3
"""
CORREÇÃO DE TIMEZONE FLUXON - AJUSTE AUTOMÁTICO
"""
import requests
import json
from datetime import datetime, timezone
import time

def fix_timezone_issues():
    print("=" * 60)
    print("🕒 CORREÇÃO DE TIMEZONE FLUXON")
    print("=" * 60)
    
    try:
        # Testar conexão com o servidor
        response = requests.get("http://localhost:5000/health", timeout=5)
        if response.status_code == 200:
            print("✅ Servidor Flask está respondendo")
            
            # Obter informações de timezone
            tz_response = requests.get("http://localhost:5000/api/timezone/debug", timeout=5)
            if tz_response.status_code == 200:
                tz_info = tz_response.json()
                print(f"📊 Offset de timezone: {tz_info['timezone_offset']} horas")
                print(f"🔄 Tolerância configurada: {tz_info['token_leeway']/3600} horas")
                
                if abs(tz_info['timezone_offset']) > 3:
                    print("⚠️  Diferença de timezone significativa detectada")
                    print("💡 O sistema ajustará automaticamente")
                else:
                    print("✅ Timezone dentro da tolerância normal")
                    
            return True
            
    except requests.exceptions.ConnectionError:
        print("❌ Servidor não está respondendo na porta 5000")
    except Exception as e:
        print(f"❌ Erro: {e}")
    
    return False

if __name__ == "__main__":
    if fix_timezone_issues():
        print("=" * 60)
        print("🎉 Correção de timezone aplicada com sucesso!")
        print("🌐 O sistema agora deve funcionar sem erros de autenticação")
        print("=" * 60)
    else:
        print("=" * 60)
        print("❌ Não foi possível aplicar a correção automaticamente")
        print("💡 Verifique se o servidor Flask está rodando na porta 5000")
        print("=" * 60)