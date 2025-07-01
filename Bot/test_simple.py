#!/usr/bin/env python3
# Teste simples para identificar o problema

print("🔧 Testando sistema básico...")

try:
    import discord
    print("✅ Discord.py importado")
except Exception as e:
    print(f"❌ Erro ao importar Discord: {e}")

try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✅ Dotenv carregado")
except Exception as e:
    print(f"❌ Erro ao carregar dotenv: {e}")

try:
    import os
    if os.path.exists('.env'):
        print("✅ Arquivo .env encontrado")
    else:
        print("❌ Arquivo .env não existe")
except Exception as e:
    print(f"❌ Erro ao verificar .env: {e}")

print("🏁 Teste concluído") 