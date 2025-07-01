#!/usr/bin/env python3
"""
Script de inicialização do Bot de Tickets Avançado
Este script verifica as configurações antes de iniciar o bot
"""

import os
import sys
import subprocess
import psutil
import time
from dotenv import load_dotenv

def verificar_e_fechar_sessoes_existentes():
    """Verifica e fecha outras sessões do bot automaticamente"""
    print("🔍 Verificando sessões existentes do bot...")
    
    # Pega o PID do processo atual
    current_pid = os.getpid()
    bot_processes = []
    
    try:
        # Procura por processos Python executando arquivos relacionados ao bot
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                # Verifica se é um processo Python
                if proc.info['name'] and 'python' in proc.info['name'].lower():
                    cmdline = proc.info['cmdline']
                    if cmdline:
                        cmdline_str = ' '.join(cmdline).lower()
                        # Verifica se está executando o bot (main.py, start_bot.py ou contém 'bot')
                        if any(keyword in cmdline_str for keyword in ['main.py', 'start_bot.py', 'discord', 'ticket']):
                            if proc.info['pid'] != current_pid:  # Não inclui o processo atual
                                bot_processes.append(proc.info['pid'])
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
    except Exception as e:
        print(f"⚠️ Erro ao verificar processos: {e}")
    
    if bot_processes:
        print(f"🔄 Encontradas {len(bot_processes)} sessão(ões) existente(s) do bot")
        print("🛑 Fechando sessões anteriores automaticamente...")
        
        for pid in bot_processes:
            try:
                proc = psutil.Process(pid)
                proc.terminate()  # Tentativa gentil de encerrar
                print(f"   ✅ Processo {pid} encerrado")
            except psutil.NoSuchProcess:
                continue
            except Exception as e:
                print(f"   ⚠️ Erro ao encerrar processo {pid}: {e}")
        
        # Aguarda um pouco para os processos serem encerrados
        time.sleep(2)
        
        # Força o encerramento dos processos restantes
        for pid in bot_processes:
            try:
                proc = psutil.Process(pid)
                if proc.is_running():
                    proc.kill()  # Força o encerramento
                    print(f"   🔥 Processo {pid} forçado a encerrar")
            except psutil.NoSuchProcess:
                continue
            except Exception as e:
                print(f"   ⚠️ Erro ao forçar encerramento do processo {pid}: {e}")
        
        print("✅ Sessões anteriores encerradas com sucesso!")
    else:
        print("✅ Nenhuma sessão anterior encontrada")
    
    # Limpa arquivos temporários de áudio
    try:
        temp_audio_dir = "temp_audio"
        if os.path.exists(temp_audio_dir):
            for filename in os.listdir(temp_audio_dir):
                if filename.startswith("voice_") and filename.endswith(".mp3"):
                    os.remove(os.path.join(temp_audio_dir, filename))
            print("🧹 Arquivos temporários de áudio limpos")
    except Exception as e:
        print(f"⚠️ Erro ao limpar arquivos temporários: {e}")

def verificar_configuracoes():
    """Verifica se todas as configurações necessárias estão presentes"""
    print("🔍 Verificando configurações...")
    
    # Cria arquivo .env se não existir
    if not os.path.exists('.env'):
        print("📝 Arquivo .env não encontrado. Criando arquivo básico...")
        env_content = """# Configurações do Bot Discord FavelaZ
BOT_TOKEN=seu_bot_token_aqui

# Configurações de Servidor  
TICKET_CATEGORY_ID=0
SUPPORT_ROLE_ID=0
AUDIO_CHANNEL_ID=0

# Configurações do ElevenLabs (Voz)
ELEVENLABS_API_KEY=sua_api_key_aqui
VOICE_ID=sua_voice_id_aqui

# IDs Administrativos (Configurados automaticamente pelo !setup_servidor)
ADMIN_CATEGORY_ID=0
TICKETS_CHANNEL_ID=0
INFO_CHANNEL_ID=0
"""
        try:
            with open('.env', 'w', encoding='utf-8') as f:
                f.write(env_content)
            print("✅ Arquivo .env criado! Configure-o com seus dados.")
        except Exception as e:
            print(f"❌ Erro ao criar .env: {e}")
    
    # Carrega as variáveis de ambiente
    load_dotenv()
    
    # Configurações obrigatórias
    configs_obrigatorias = [
        ("BOT_TOKEN", "Token do bot Discord"),
        ("TICKET_CATEGORY_ID", "ID da categoria de tickets"),
        ("SUPPORT_ROLE_ID", "ID do cargo de suporte"),
        ("AUDIO_CHANNEL_ID", "ID do canal de áudio")
    ]
    
    # Configurações opcionais
    configs_opcionais = [
        ("ELEVENLABS_API_KEY", "Chave da API ElevenLabs"),
        ("VOICE_ID", "ID da voz para clonagem")
    ]
    
    missing_configs = []
    
    # Verifica configurações obrigatórias
    for config, descricao in configs_obrigatorias:
        if not os.getenv(config):
            missing_configs.append(f"❌ {config} - {descricao}")
        else:
            print(f"✅ {config} - Configurado")
    
    # Verifica configurações opcionais
    for config, descricao in configs_opcionais:
        if not os.getenv(config):
            print(f"⚠️  {config} - {descricao} (opcional)")
        else:
            print(f"✅ {config} - Configurado")
    
    if missing_configs:
        print("\n❌ CONFIGURAÇÕES FALTANDO:")
        for config in missing_configs:
            print(f"  {config}")
        print("\n📝 Crie um arquivo .env com as configurações necessárias.")
        print("   Consulte o README.md para mais informações.")
        return False
    
    print("\n✅ Todas as configurações obrigatórias estão presentes!")
    return True

def verificar_dependencias():
    """Verifica se as dependências estão instaladas"""
    print("\n🔍 Verificando dependências...")
    
    dependencias = [
        ('discord', 'discord.py'),
        ('sklearn', 'scikit-learn'),
        ('requests', 'requests'),
        ('dotenv', 'python-dotenv')
    ]
    
    missing_deps = []
    
    for module, pip_name in dependencias:
        try:
            __import__(module)
            print(f"✅ {pip_name}")
        except ImportError:
            missing_deps.append(pip_name)
            print(f"❌ {pip_name}")
    
    if missing_deps:
        print(f"\n❌ Dependências faltando: {', '.join(missing_deps)}")
        print("💡 Execute: pip install -r requirements.txt")
        return False
    
    print("\n✅ Todas as dependências estão instaladas!")
    return True

def verificar_arquivos():
    """Verifica se os arquivos necessários existem"""
    print("\n🔍 Verificando estrutura de arquivos...")
    
    arquivos_necessarios = [
        ('main.py', 'Arquivo principal do bot'),
        ('cogs/tickets.py', 'Sistema de tickets'),
        ('cogs/ai.py', 'Sistema de IA'),
        ('cogs/voice_system.py', 'Sistema de voz')
    ]
    
    arquivos_opcionais = [
        ('hold_music.mp3', 'Música de espera para o sistema de voz')
    ]
    
    missing_files = []
    
    for arquivo, descricao in arquivos_necessarios:
        if os.path.exists(arquivo):
            print(f"✅ {arquivo}")
        else:
            missing_files.append(f"❌ {arquivo} - {descricao}")
    
    for arquivo, descricao in arquivos_opcionais:
        if os.path.exists(arquivo):
            print(f"✅ {arquivo}")
        else:
            print(f"⚠️  {arquivo} - {descricao} (opcional)")
    
    if missing_files:
        print("\n❌ ARQUIVOS FALTANDO:")
        for arquivo in missing_files:
            print(f"  {arquivo}")
        return False
    
    print("\n✅ Todos os arquivos necessários estão presentes!")
    return True

def main():
    """Função principal"""
    print("🤖 Iniciando Bot de Tickets Avançado com IA")
    print("=" * 50)
    
    # PRIMEIRO: Verifica e fecha sessões existentes
    verificar_e_fechar_sessoes_existentes()
    print("")
    
    # Verifica se tudo está configurado corretamente
    if not verificar_arquivos():
        sys.exit(1)
    
    if not verificar_dependencias():
        sys.exit(1)
    
    if not verificar_configuracoes():
        sys.exit(1)
    
    print("\n🚀 Iniciando o bot...")
    print("=" * 50)
    
    # Importa e executa o bot principal
    try:
        from main import bot, BOT_TOKEN
        if BOT_TOKEN:
            bot.run(BOT_TOKEN)
        else:
            print("❌ BOT_TOKEN não encontrado")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n👋 Bot encerrado pelo usuário")
    except Exception as e:
        print(f"\n❌ Erro ao iniciar o bot: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 