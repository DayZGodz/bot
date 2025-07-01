import discord
from discord.ext import commands
import os
import asyncio
import psutil
import time
from dotenv import load_dotenv

# Carrega as variáveis de ambiente
load_dotenv()

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
    
    print("="*50)

# Configurações do bot
BOT_TOKEN = os.getenv("BOT_TOKEN")
COMMAND_PREFIX = os.getenv("COMMAND_PREFIX", "!")

# Intents necessários
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.voice_states = True

# Criação do bot
bot = commands.Bot(command_prefix=COMMAND_PREFIX, intents=intents)

@bot.event
async def on_ready():
    """Evento executado quando o bot fica online"""
    print(f'🤖 Bot conectado como {bot.user}')
    print(f'📊 Presente em {len(bot.guilds)} servidor(es)')
    
    # Carrega todos os cogs automaticamente
    print('🔧 Carregando extensões...')
    for filename in os.listdir('./cogs'):
        if filename.endswith('.py') and not filename.startswith('__'):
            try:
                await bot.load_extension(f'cogs.{filename[:-3]}')
                print(f'✅ {filename} carregado com sucesso')
            except Exception as e:
                print(f'❌ Erro ao carregar {filename}: {e}')
    
    print('🚀 Bot pronto para uso!')
    
    # Define status do bot
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.watching, 
            name="tickets e atendimentos"
        )
    )

@bot.event
async def on_command_error(ctx, error):
    """Manipula erros de comandos"""
    if isinstance(error, commands.CommandNotFound):
        await ctx.send("❌ Comando não encontrado. Use `!help` para ver os comandos disponíveis.")
    elif isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ Você não tem permissão para usar este comando.")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("❌ Argumento obrigatório faltando. Verifique a sintaxe do comando.")
    else:
        print(f"Erro não tratado: {error}")

# Exporta variáveis para outros módulos
__all__ = ['bot', 'BOT_TOKEN']

# Comando para recarregar cogs (apenas para administradores)
@bot.command()
@commands.has_permissions(administrator=True)
async def reload(ctx, cog_name: str | None = None):
    """Recarrega um cog específico ou todos os cogs"""
    if cog_name:
        try:
            await bot.reload_extension(f'cogs.{cog_name}')
            await ctx.send(f"✅ Cog `{cog_name}` recarregado com sucesso!")
        except Exception as e:
            await ctx.send(f"❌ Erro ao recarregar `{cog_name}`: {e}")
    else:
        # Recarrega todos os cogs
        reloaded = []
        for filename in os.listdir('./cogs'):
            if filename.endswith('.py') and not filename.startswith('__'):
                try:
                    await bot.reload_extension(f'cogs.{filename[:-3]}')
                    reloaded.append(filename[:-3])
                except Exception as e:
                    await ctx.send(f"❌ Erro ao recarregar {filename}: {e}")
        
        if reloaded:
            await ctx.send(f"✅ Cogs recarregados: {', '.join(reloaded)}")



if __name__ == "__main__":
    # PRIMEIRO: Verifica e fecha sessões existentes
    verificar_e_fechar_sessoes_existentes()
    
    if not BOT_TOKEN:
        print("❌ ERRO: BOT_TOKEN não encontrado no arquivo .env")
        print("📝 Crie um arquivo .env com: BOT_TOKEN=seu_token_aqui")
        exit(1)
    
    # Cria diretórios necessários
    os.makedirs('cogs', exist_ok=True)
    os.makedirs('transcripts', exist_ok=True) 
    os.makedirs('nlp_model', exist_ok=True)
    os.makedirs('temp_audio', exist_ok=True)
    
    print("🚀 Iniciando bot...")
    # Garante que BOT_TOKEN não é None neste ponto
    assert BOT_TOKEN is not None, "BOT_TOKEN deve estar definido"
    bot.run(BOT_TOKEN) 