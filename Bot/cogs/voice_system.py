import discord
from discord.ext import commands
import os
import asyncio
import requests
import random
import subprocess
import glob
import hashlib
import shutil
import datetime
from dotenv import load_dotenv
import json

load_dotenv()

def get_env_id(key):
    value = os.getenv(key, "0")
    return int(value.strip('\'\"'))

# Configurações do ElevenLabs
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
VOICE_ID = os.getenv("VOICE_ID")
AUDIO_CHANNEL_ID = get_env_id("AUDIO_CHANNEL_ID")
print(f"DEBUG: AUDIO_CHANNEL_ID lido do .env: {AUDIO_CHANNEL_ID} (tipo: {type(AUDIO_CHANNEL_ID)})")

def configurar_ffmpeg():
    """Configura o FFmpeg automaticamente"""
    # Primeiro verifica se FFmpeg já está no PATH
    try:
        subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True, timeout=5)
        return True
    except:
        pass
    
    # Procura pelo FFmpeg instalado pelo winget
    ffmpeg_paths = [
        # Caminho típico do winget
        os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Microsoft', 'WinGet', 'Packages', 'Gyan.FFmpeg.Essentials_*', 'ffmpeg-*', 'bin'),
        # Outros caminhos possíveis
        'C:\\ffmpeg\\bin',
        'C:\\Program Files\\ffmpeg\\bin',
        'C:\\Program Files (x86)\\ffmpeg\\bin'
    ]
    
    for path_pattern in ffmpeg_paths:
        # Usa glob para encontrar caminhos com wildcards
        matching_paths = glob.glob(path_pattern)
        for path in matching_paths:
            ffmpeg_exe = os.path.join(path, 'ffmpeg.exe')
            if os.path.exists(ffmpeg_exe):
                # Adiciona ao PATH da sessão atual
                if path not in os.environ['PATH']:
                    os.environ['PATH'] += f';{path}'
                    print(f"🎵 FFmpeg configurado: {path}")
                    return True
    
    print("⚠️ FFmpeg não encontrado - alguns recursos de áudio podem não funcionar")
    return False

# Configura FFmpeg automaticamente na inicialização
configurar_ffmpeg()

class VoiceSystem(commands.Cog):
    """Sistema de voz com clonagem e mensagens programadas"""
    
    def __init__(self, bot):
        self.bot = bot
        self.is_playing_cycle = False
        self.voice_client = None
        self.current_task = None
        self.mensagens_task = None
        self.pausar_musica_para_mensagem = False  # Nova flag para controlar música vs mensagens
        self.tocando_mensagem = False  # Flag para indicar quando está falando
        self.primeira_mensagem = True  # Flag para sempre começar com a primeira mensagem
        
        # Arquivo de música de espera
        self.musica_espera = "jazz-lounge-elevator-music-332339.mp3"
        
        # Mensagens programadas para o sistema de telecomunicações
        self.mensagens_sistema = [
            "Bem-vindo ao melhor servidor de DayZ. FavelaZ .",
            "Sua chamada é importante para nós. Aguarde enquanto conectamos você a um atendente.",
            "Para agilizar seu atendimento, tenha em mãos o número do seu protocolo.",
            "Nosso horário de funcionamento é das nove às dezoito horas, de segunda a sexta-feira.",
            "Você pode abrir um ticket a qualquer momento digitando exclamação ticket.",
            "Obrigado por escolher nossos serviços. Aguarde na linha.",
            "Seu tempo de espera estimado é de aproximadamente dois minutos.",
            "Para emergências, entre em contato através do nosso canal prioritário."
        ]
    
    @commands.Cog.listener()
    async def on_ready(self):
        print("🎵 Sistema de Voz carregado com música jazz")
        os.makedirs('temp_audio', exist_ok=True)
        os.makedirs('cached_voices', exist_ok=True)
        os.makedirs('backup_voices', exist_ok=True)
        print("💾 Sistema de cache de voz ativado - economiza créditos ElevenLabs!")
        print("🔄 Sistema de backup de vozes ativado!")
        # Auto-conexão ao canal de voz
        await self.auto_conectar_voz()
        # Auto-download de frases se necessário
        await self.auto_download_frases()

    async def get_voice_channel(self, channel_id):
        """Busca um canal de voz pelo ID"""
        print(f"DEBUG: Tentando encontrar canal de voz {channel_id}")
        
        # Primeiro tenta pelo cache
        channel = self.bot.get_channel(channel_id)
        if channel and isinstance(channel, discord.VoiceChannel):
            print(f"DEBUG: Canal encontrado no cache: {channel.name}")
            return channel
            
        print(f"DEBUG: Canal não encontrado no cache, tentando fetch_channel")
        
        # Se não encontrar, tenta buscar pela API
        try:
            channel = await self.bot.fetch_channel(channel_id)
            if isinstance(channel, discord.VoiceChannel):
                print(f"DEBUG: Canal encontrado via fetch_channel: {channel.name}")
                return channel
        except discord.NotFound:
            print(f"DEBUG: Canal não encontrado (404): {channel_id}")
        except Exception as e:
            print(f"DEBUG: Erro ao buscar canal: {e}")

        # Se ainda não encontrou, tenta buscar em todas as guilds
        print("DEBUG: Tentando encontrar canal em todas as guilds")
        for guild in self.bot.guilds:
            # Primeiro procura pelo nome "📞 Central de Atendimento" na categoria admin
            for channel in guild.voice_channels:
                if channel.name == "📞 Central de Atendimento":
                    print(f"DEBUG: Canal encontrado pelo nome em {guild.name}: {channel.name} (ID: {channel.id})")
                    # Atualiza o .env com o ID correto
                    os.environ['AUDIO_CHANNEL_ID'] = str(channel.id)
                    return channel
            
            # Se não encontrar pelo nome, tenta pelo ID
            for channel in guild.voice_channels:
                if channel.id == channel_id:
                    print(f"DEBUG: Canal encontrado pelo ID em {guild.name}: {channel.name}")
                    return channel
        
        print("DEBUG: Canal de áudio não encontrado")
        return None

    async def auto_conectar_voz(self):
        """Conecta automaticamente ao canal de voz se configurado"""
        print(f"DEBUG: Iniciando auto_conectar_voz")
        
        if self.is_playing_cycle:
            if self.voice_client and self.voice_client.is_connected():
                print("DEBUG: Sistema já está ativo e conectado")
                return True
            self.is_playing_cycle = False
            
        # Recarrega o AUDIO_CHANNEL_ID do .env
        load_dotenv()
        channel_id = int(os.getenv('AUDIO_CHANNEL_ID', '0'))
        print(f"DEBUG: AUDIO_CHANNEL_ID = {channel_id}")
        
        # Tenta reconectar até 3 vezes
        for tentativa in range(3):
            print(f"DEBUG: Tentativa {tentativa + 1} de conectar")
            audio_channel = await self.get_voice_channel(channel_id)
            
            if not audio_channel:
                print("DEBUG: Canal de áudio não encontrado")
                await asyncio.sleep(2)  # Aguarda um pouco antes da próxima tentativa
                continue
                
            try:
                # Se já estiver conectado em outro canal, desconecta
                if self.voice_client:
                    if self.voice_client.is_connected():
                        if self.voice_client.channel.id == audio_channel.id:
                            print("DEBUG: Já conectado ao canal correto")
                            return True
                        await self.voice_client.disconnect()
                    
                # Conecta ao canal
                self.voice_client = await audio_channel.connect()
                print(f"DEBUG: Conectado ao canal: {audio_channel.name}")
                
                # Inicia a música
                await self.tocar_musica_espera()
                print("DEBUG: Música iniciada com sucesso")
                
                # Inicia o ciclo de mensagens
                self.is_playing_cycle = True
                self.mensagens_task = asyncio.create_task(self.sistema_mensagens_automaticas())
                print("DEBUG: Ciclo de mensagens iniciado")
                
                return True
                
            except Exception as e:
                print(f"DEBUG: Erro ao conectar: {e}")
                if self.voice_client:
                    try:
                        await self.voice_client.disconnect()
                    except:
                        pass
                await asyncio.sleep(2)  # Aguarda antes da próxima tentativa
        
        print("DEBUG: Todas as tentativas de conexão falharam")
        return False

    async def setup_servidor_voice(self, ctx):
        """Configura o sistema de voz após setup_servidor"""
        print("DEBUG: Iniciando setup_servidor_voice")
        
        # Tenta conectar ao canal de voz
        sucesso = await self.auto_conectar_voz()
        
        if sucesso:
            await ctx.send("✅ Sistema de voz conectado e funcionando!")
        else:
            await ctx.send("❌ Falha ao conectar ao sistema de voz. Por favor, use !iniciar_sistema para tentar novamente.")

    async def auto_download_frases(self):
        """Verifica e baixa frases se necessário ao iniciar"""
        # Verifica se todos os arquivos de voz existem no cache
        frases = self.mensagens_sistema
        faltando = []
        for i, frase in enumerate(frases):
            hash_nome = self.gerar_hash_mensagem(frase)
            arquivo = f"voice_{hash_nome}.mp3"
            if not os.path.exists(os.path.join('cached_voices', arquivo)):
                faltando.append(frase)
        if faltando:
            if VOICE_ID:
                print(f"🔄 Baixando {len(faltando)} frases de voz que faltam no cache...")
                await self.gerar_todas_frases_nova_voz(VOICE_ID)
            else:
                print("⚠️ VOICE_ID não configurado. Não é possível baixar frases de voz.")
        else:
            print("✅ Todas as frases de voz já estão no cache.")

    def criar_backup_voz_atual(self, nova_voice_id: str):
        """Cria backup das vozes atuais antes de trocar"""
        try:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            current_voice_id = VOICE_ID or "unknown"
            
            # Cria pasta de backup com timestamp
            backup_dir = f"backup_voices/backup_{current_voice_id}_{timestamp}"
            os.makedirs(backup_dir, exist_ok=True)
            
            # Copia todos os arquivos de voz atuais para o backup
            arquivos_copiados = 0
            if os.path.exists('cached_voices'):
                for arquivo in os.listdir('cached_voices'):
                    if arquivo.endswith('.mp3'):
                        src = os.path.join('cached_voices', arquivo)
                        dst = os.path.join(backup_dir, arquivo)
                        shutil.copy2(src, dst)
                        arquivos_copiados += 1
            
            # Salva informações do backup
            info_backup = f"""BACKUP DE VOZ ANTERIOR
Data: {datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")}
Voice ID Anterior: {current_voice_id}
Nova Voice ID: {nova_voice_id}
Total de Arquivos: {arquivos_copiados}
Mensagens Salvas: {len(self.mensagens_sistema)}
"""
            
            with open(os.path.join(backup_dir, "info_backup.txt"), "w", encoding="utf-8") as f:
                f.write(info_backup)
            
            print(f"💾 Backup criado: {backup_dir} ({arquivos_copiados} arquivos)")
            return backup_dir
            
        except Exception as e:
            print(f"⚠️ Erro ao criar backup: {e}")
            return None

    async def gerar_todas_frases_nova_voz(self, nova_voice_id: str, ctx=None):
        """Gera todas as frases com a nova voz"""
        try:
            if ctx:
                embed_inicial = discord.Embed(
                    title="🎤 Iniciando Download",
                    description="Iniciando download de todas as frases com a nova voz...",
                    color=discord.Color.blue()
                )
                message = await ctx.send(embed=embed_inicial)
            
            sucessos = 0
            erros = 0
            
            # Limpa cache atual (será recriado com nova voz)
            if os.path.exists('cached_voices'):
                for arquivo in os.listdir('cached_voices'):
                    if arquivo.endswith('.mp3'):
                        os.remove(os.path.join('cached_voices', arquivo))
            
            # Gera cada mensagem com a nova voz
            for i, mensagem in enumerate(self.mensagens_sistema, 1):
                try:
                    if ctx and 'message' in locals():
                        embed = discord.Embed(
                            title="🎤 Gerando Nova Voz",
                            description=f"Processando mensagem {i}/{len(self.mensagens_sistema)}...\n\n**Texto:** {mensagem[:100]}...",
                            color=discord.Color.blue()
                        )
                        await message.edit(embed=embed)
                    
                    # Gera áudio com nova voz
                    arquivo_gerado = await self.gerar_audio_elevenlabs_com_voice_id(mensagem, nova_voice_id)
                    if arquivo_gerado:
                        sucessos += 1
                        print(f"✅ Mensagem {i} gerada: {mensagem[:50]}...")
                    else:
                        erros += 1
                        print(f"❌ Erro na mensagem {i}: {mensagem[:50]}...")
                    
                    # Pausa para não sobrecarregar a API
                    await asyncio.sleep(2)
                    
                except Exception as e:
                    erros += 1
                    print(f"❌ Erro ao gerar mensagem {i}: {e}")
            
            resultado = f"✅ Download concluído!\n\n**Sucessos:** {sucessos}\n**Erros:** {erros}\n**Total:** {len(self.mensagens_sistema)}"
            
            if ctx and 'message' in locals():
                embed = discord.Embed(
                    title="🎉 Download Concluído!",
                    description=resultado,
                    color=discord.Color.green()
                )
                embed.set_footer(text="Nova voz configurada e cache atualizado!")
                await message.edit(embed=embed)
            
            print(f"🎉 {resultado}")
            return sucessos, erros
            
        except Exception as e:
            print(f"⚠️ Erro no download das frases: {e}")
            return 0, len(self.mensagens_sistema)

    async def gerar_audio_elevenlabs_com_voice_id(self, texto, voice_id):
        """Gera áudio usando ElevenLabs com voice_id específico"""
        if not ELEVENLABS_API_KEY or ELEVENLABS_API_KEY.strip() == "":
            print("⚠️ ElevenLabs não configurado")
            return None
        
        try:
            # Verifica se já existe no cache
            hash_texto = self.gerar_hash_mensagem(texto)
            arquivo_cache = f"cached_voices/voice_{hash_texto}.mp3"
            
            print(f"🌐 Gerando áudio com voice_id {voice_id}: {texto[:50]}...")
            
            # Configuração da API ElevenLabs
            url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
            
            headers = {
                "Accept": "audio/mpeg",
                "Content-Type": "application/json",
                "xi-api-key": ELEVENLABS_API_KEY
            }
            
            data = {
                "text": texto,
                "model_id": "eleven_multilingual_v2",
                "voice_settings": {
                    "stability": 0.75,
                    "similarity_boost": 0.85,
                    "style": 0.25
                }
            }
            
            response = requests.post(url, json=data, headers=headers, timeout=30)
            
            if response.status_code == 200:
                # Salva o arquivo de áudio
                with open(arquivo_cache, 'wb') as f:
                    f.write(response.content)
                
                print(f"💾 Áudio salvo: {arquivo_cache}")
                return arquivo_cache
            else:
                print(f"❌ Erro na API ElevenLabs: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ Erro ao gerar áudio: {e}")
            return None

    @commands.command(name='trocar_voz', aliases=['nova_voz', 'mudar_voz'])
    @commands.has_permissions(administrator=True)
    async def trocar_voz_completa(self, ctx, nova_voice_id: str):
        """Troca a voz do sistema criando backup e baixando todas as frases"""
        
        # Validação básica do voice_id
        if len(nova_voice_id) < 10:
            await ctx.send("❌ Voice ID inválido. Deve ter pelo menos 10 caracteres.")
            return
        
        embed_inicial = discord.Embed(
            title="🔄 Iniciando Troca de Voz",
            description="Criando backup da voz atual e preparando nova voz...",
            color=discord.Color.orange()
        )
        message = await ctx.send(embed=embed_inicial)
        
        try:
            # 1. Criar backup da voz atual
            print(f"💾 Criando backup da voz atual...")
            backup_dir = self.criar_backup_voz_atual(nova_voice_id)
            
            embed_backup = discord.Embed(
                title="💾 Backup Criado",
                description=f"Voz anterior salva em: `{backup_dir}`\n\nIniciando download com nova voz...",
                color=discord.Color.blue()
            )
            await message.edit(embed=embed_backup)
            
            # 2. Atualizar VOICE_ID no ambiente (temporariamente)
            global VOICE_ID
            old_voice_id = VOICE_ID
            VOICE_ID = nova_voice_id
            
            # 3. Gerar todas as frases com nova voz
            sucessos, erros = await self.gerar_todas_frases_nova_voz(nova_voice_id, message)
            
            # 4. Embed de sucesso final
            embed_final = discord.Embed(
                title="🎉 Troca de Voz Concluída!",
                color=discord.Color.green()
            )
            
            embed_final.add_field(
                name="📊 Resultados",
                value=f"**Sucessos:** {sucessos}\n**Erros:** {erros}\n**Total:** {len(self.mensagens_sistema)}",
                inline=True
            )
            
            old_voice_display = f"{old_voice_id[:20]}..." if old_voice_id and len(old_voice_id) > 20 else old_voice_id if old_voice_id else 'N/A'
            new_voice_display = f"{nova_voice_id[:20]}..." if nova_voice_id and len(nova_voice_id) > 20 else nova_voice_id
            embed_final.add_field(
                name="🔄 Configuração",
                value=f"**Voz Anterior:** `{old_voice_display}`\n**Nova Voz:** `{new_voice_display}`",
                inline=True
            )
            
            embed_final.add_field(
                name="💾 Backup",
                value=f"Arquivos anteriores salvos em:\n`{backup_dir}`",
                inline=False
            )
            
            embed_final.add_field(
                name="⚙️ Próximo Passo",
                value="**IMPORTANTE:** Atualize o arquivo `.env` com a nova VOICE_ID para que a mudança seja permanente!",
                inline=False
            )
            
            embed_final.set_footer(text="Sistema de voz atualizado com sucesso!")
            
            await message.edit(embed=embed_final)
            
            print(f"🎉 Troca de voz concluída: {old_voice_id} → {nova_voice_id}")
            
        except Exception as e:
            # Restaura voice_id original em caso de erro
            VOICE_ID = old_voice_id
            
            embed_erro = discord.Embed(
                title="❌ Erro na Troca de Voz",
                description=f"Erro: {str(e)}\n\nVoz original restaurada.",
                color=discord.Color.red()
            )
            await message.edit(embed=embed_erro)
            print(f"❌ Erro na troca de voz: {e}")

    @commands.command(name='restaurar_backup', aliases=['restore_voice'])
    @commands.has_permissions(administrator=True)
    async def restaurar_backup_voz(self, ctx):
        """Lista e permite restaurar backups de voz"""
        
        try:
            # Lista backups disponíveis
            backups_disponiveis = []
            if os.path.exists('backup_voices'):
                for pasta in os.listdir('backup_voices'):
                    if pasta.startswith('backup_'):
                        info_path = os.path.join('backup_voices', pasta, 'info_backup.txt')
                        if os.path.exists(info_path):
                            backups_disponiveis.append(pasta)
            
            if not backups_disponiveis:
                await ctx.send("❌ Nenhum backup de voz encontrado.")
                return
            
            # Cria embed com lista de backups
            embed = discord.Embed(
                title="💾 Backups Disponíveis",
                description="Backups de vozes encontrados:",
                color=discord.Color.blue()
            )
            
            for i, backup in enumerate(backups_disponiveis[:10], 1):  # Máximo 10
                # Lê informações do backup
                info_path = os.path.join('backup_voices', backup, 'info_backup.txt')
                try:
                    with open(info_path, 'r', encoding='utf-8') as f:
                        info = f.read()
                    
                    # Extrai data do backup
                    if 'Data:' in info:
                        data_linha = [linha for linha in info.split('\n') if 'Data:' in linha][0]
                        data = data_linha.split('Data: ')[1]
                    else:
                        data = "Data não disponível"
                    
                    embed.add_field(
                        name=f"{i}. {backup}",
                        value=f"📅 {data}",
                        inline=False
                    )
                    
                except:
                    embed.add_field(
                        name=f"{i}. {backup}",
                        value="📅 Informações não disponíveis",
                        inline=False
                    )
            
            embed.set_footer(text="Use !restaurar_backup <número> para restaurar")
            await ctx.send(embed=embed)
            
        except Exception as e:
            await ctx.send(f"❌ Erro ao listar backups: {e}")

    @commands.command(name='info_backup')
    @commands.has_permissions(administrator=True)
    async def info_backup_voz(self, ctx):
        """Mostra informações sobre o sistema de backup"""
        
        try:
            # Conta backups
            total_backups = 0
            total_arquivos = 0
            
            if os.path.exists('backup_voices'):
                for pasta in os.listdir('backup_voices'):
                    if pasta.startswith('backup_'):
                        total_backups += 1
                        backup_path = os.path.join('backup_voices', pasta)
                        total_arquivos += len([f for f in os.listdir(backup_path) if f.endswith('.mp3')])
            
            # Conta cache atual
            cache_atual = len([f for f in os.listdir('cached_voices') if f.endswith('.mp3')]) if os.path.exists('cached_voices') else 0
            
            embed = discord.Embed(
                title="📊 Sistema de Backup de Vozes",
                color=discord.Color.green()
            )
            
            embed.add_field(
                name="💾 Backups",
                value=f"**Total:** {total_backups}\n**Arquivos:** {total_arquivos}",
                inline=True
            )
            
            embed.add_field(
                name="🎵 Cache Atual",
                value=f"**Arquivos:** {cache_atual}\n**Mensagens:** {len(self.mensagens_sistema)}",
                inline=True
            )
            
            embed.add_field(
                name="🔧 Comandos",
                value="• `!trocar_voz <voice_id>` - Troca voz com backup\n• `!restaurar_backup` - Lista backups\n• `!info_backup` - Mostra esta info",
                inline=False
            )
            
            embed.set_footer(text="Sistema automático de backup e restauração")
            await ctx.send(embed=embed)
            
        except Exception as e:
            await ctx.send(f"❌ Erro ao obter informações: {e}")

    async def tocar_musica_espera(self):
        """Toca a música de espera em loop no Discord"""
        if not os.path.exists(self.musica_espera):
            print(f"⚠️ Música de espera não encontrada: {self.musica_espera}")
            return False
        
        if not self.voice_client:
            print("⚠️ Bot não está conectado a um canal de voz")
            return False
            
        try:
            # Para qualquer áudio atual
            if self.voice_client.is_playing():
                self.voice_client.stop()
            
            # Aguarda um pouco para garantir que parou
            await asyncio.sleep(0.5)
            
            # Opções mais compatíveis para o FFmpeg com fade e volume baixo
            ffmpeg_options = {
                'before_options': '-re',  # Lê em tempo real
                'options': '-vn -filter:a "volume=0.2,afade=t=in:d=2,afade=t=out:st=60:d=3"'  # Volume muito baixo + fade in/out
            }
            
            # Cria fonte de áudio para Discord
            source = discord.FFmpegPCMAudio(
                self.musica_espera,
                **ffmpeg_options
            )
            
            # Função para fazer loop da música (só se não estiver pausada para mensagem)
            def loop_music(error):
                if error:
                    print(f'⚠️ Erro na reprodução: {error}')
                else:
                    # Só reinicia se não estiver pausada para mensagem e o sistema estiver ativo
                    if (not self.pausar_musica_para_mensagem and 
                        not self.tocando_mensagem and 
                        self.is_playing_cycle and 
                        self.voice_client and 
                        not self.voice_client.is_playing()):
                        try:
                            new_source = discord.FFmpegPCMAudio(self.musica_espera, **ffmpeg_options)
                            self.voice_client.play(new_source, after=loop_music)
                            print('🔄 Música jazz reiniciada automaticamente')
                        except Exception as e:
                            print(f'⚠️ Erro ao reiniciar música: {e}')
            
            # Reproduz no canal de voz do Discord
            self.voice_client.play(source, after=loop_music)
            print(f"🎵 Música jazz iniciada no Discord: {self.musica_espera}")
            return True
            
        except Exception as e:
            print(f"⚠️ Erro ao tocar música no Discord: {e}")
            return False

    async def fade_out_musica(self):
        """Diminui a música gradualmente (fade out suave)"""
        try:
            self.pausar_musica_para_mensagem = True
            if self.voice_client and self.voice_client.is_playing():
                print("🔉 Iniciando fade out da música...")
                
                # Para a música atual (que estava em volume normal)
                self.voice_client.stop()
                await asyncio.sleep(0.3)
                
                # Toca a música com fade out de 3 segundos
                if os.path.exists(self.musica_espera):
                    ffmpeg_fade_out = {
                        'before_options': '-re',
                        'options': '-vn -filter:a "volume=0.2,afade=t=out:d=3"'  # Fade out de 3 segundos
                    }
                    source = discord.FFmpegPCMAudio(self.musica_espera, **ffmpeg_fade_out)
                    self.voice_client.play(source)
                    print("🔉 Música fazendo fade out...")
                    
                    # Aguarda o fade out completar
                    await asyncio.sleep(3.5)
                    
                    # Para completamente
                    if self.voice_client.is_playing():
                        self.voice_client.stop()
                    
                    print("🔇 Fade out concluído - música silenciada")
                    
        except Exception as e:
            print(f"⚠️ Erro no fade out da música: {e}")
    
    async def parar_musica_temporariamente(self):
        """Para a música temporariamente para tocar mensagens (com fade)"""
        await self.fade_out_musica()

    async def fade_in_musica(self):
        """Retoma a música com fade in gradual"""
        try:
            self.pausar_musica_para_mensagem = False
            if self.is_playing_cycle and self.voice_client:
                print("🔊 Iniciando fade in da música...")
                
                # Música com fade in de 4 segundos
                ffmpeg_fade_in = {
                    'before_options': '-re',
                    'options': '-vn -filter:a "volume=0.2,afade=t=in:d=4"'  # Fade in longo e suave
                }
                
                source = discord.FFmpegPCMAudio(self.musica_espera, **ffmpeg_fade_in)
                
                # Função para loop após fade in
                def loop_after_fadein(error):
                    if error:
                        print(f'⚠️ Erro no fade in: {error}')
                    else:
                        # Após fade in, volta ao loop normal
                        if (not self.pausar_musica_para_mensagem and 
                            not self.tocando_mensagem and 
                            self.is_playing_cycle and 
                            self.voice_client and 
                            not self.voice_client.is_playing()):
                            asyncio.create_task(self.tocar_musica_espera())
                
                self.voice_client.play(source, after=loop_after_fadein)
                print("🎵 Música jazz retomada com fade in suave")
                
        except Exception as e:
            print(f"⚠️ Erro no fade in da música: {e}")
    
    async def retomar_musica(self):
        """Retoma a música após tocar mensagem com fade in"""
        try:
            await asyncio.sleep(1.5)  # Pausa menor para transição suave
            await self.fade_in_musica()
        except Exception as e:
            print(f"⚠️ Erro ao retomar música: {e}")

    async def parar_musica_espera(self):
        """Para a música de espera no Discord (para comandos manuais)"""
        try:
            self.pausar_musica_para_mensagem = True
            if self.voice_client and self.voice_client.is_playing():
                self.voice_client.stop()
                print("🔇 Música jazz parada no Discord")
        except Exception as e:
            print(f"⚠️ Erro ao parar música: {e}")

    def gerar_hash_mensagem(self, texto):
        """Gera hash único para uma mensagem"""
        return hashlib.md5(texto.encode('utf-8')).hexdigest()
    
    async def gerar_audio_elevenlabs(self, texto):
        """Gera áudio usando a API do ElevenLabs com sistema de cache"""
        if not ELEVENLABS_API_KEY or not VOICE_ID or ELEVENLABS_API_KEY.strip() == "":
            print("⚠️ ElevenLabs não configurado - usando modo texto")
            return None
        
        # Verifica se já existe no cache
        hash_texto = self.gerar_hash_mensagem(texto)
        arquivo_cache = f"cached_voices/voice_{hash_texto}.mp3"
        
        if os.path.exists(arquivo_cache):
            print(f"💾 Usando áudio do cache: {texto[:50]}...")
            return arquivo_cache
            
        print(f"🌐 Gerando novo áudio via ElevenLabs: {texto[:50]}...")
        # Garante que os diretórios existem
        os.makedirs('temp_audio', exist_ok=True)
        os.makedirs('cached_voices', exist_ok=True)
            
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}"
        
        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": ELEVENLABS_API_KEY
        }
        
        data = {
            "text": texto,
            "model_id": "eleven_multilingual_v2",
            "voice_settings": {
                "stability": 0.75,
                "similarity_boost": 0.75,
                "style": 0.5,
                "use_speaker_boost": True
            }
        }
        
        try:
            response = requests.post(url, json=data, headers=headers, timeout=30)
            
            if response.status_code == 200:
                # Salva no cache permanente
                with open(arquivo_cache, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=1024):
                        if chunk:
                            f.write(chunk)
                print(f"💾 Áudio salvo no cache: {arquivo_cache}")
                return arquivo_cache
            else:
                print(f"❌ Erro na API ElevenLabs: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ Erro ao gerar áudio: {e}")
            return None

    @commands.command(name='iniciar_sistema', aliases=['start_voice', 'iniciar_voz'])
    @commands.has_permissions(manage_channels=True)
    async def iniciar_sistema_voz(self, ctx):
        """Inicia o sistema de voz automatizado no canal configurado"""
        if self.is_playing_cycle:
            if self.voice_client and self.voice_client.is_connected():
                return await ctx.send("❌ O sistema de voz já está ativo!")
            self.is_playing_cycle = False
        audio_channel = await self.get_voice_channel(AUDIO_CHANNEL_ID)
        if not audio_channel:
            return await ctx.send("❌ Canal de áudio não configurado ou não encontrado. Verifique o arquivo .env e se o canal existe.")
        if not isinstance(audio_channel, discord.VoiceChannel):
            return await ctx.send("❌ O canal configurado não é um canal de voz.")
        try:
            if self.voice_client and self.voice_client.is_connected():
                await self.voice_client.disconnect(force=True)
            embed_loading = discord.Embed(
                title="🔄 Conectando ao Canal",
                description=f"Conectando ao canal {audio_channel.mention}...",
                color=discord.Color.yellow()
            )
            message = await ctx.send(embed=embed_loading)
            self.voice_client = await audio_channel.connect()
            embed = discord.Embed(
                title="🎵 Sistema de Voz Ativado",
                description=f"Bot conectado ao canal {audio_channel.mention}",
                color=discord.Color.green()
            )
            embed.add_field(
                name="📞 Funcionalidades Ativas",
                value="• ✅ Conectado ao canal de voz\n• ✅ Clonagem de voz (ElevenLabs)\n• ✅ Sistema de música jazz\n• ✅ FFmpeg instalado",
                inline=False
            )
            embed.add_field(
                name="🎷 Comandos Disponíveis",
                value="`!falar_com_musica [texto]` - Falar com jazz\n`!controlar_jazz [play/stop]` - Controlar música",
                inline=False
            )
            await message.edit(embed=embed)
            self.is_playing_cycle = True
            self.primeira_mensagem = True
            sucesso_musica = await self.tocar_musica_espera()
            if sucesso_musica:
                embed.add_field(
                    name="🎵 Música Jazz",
                    value="✅ Tocando automaticamente",
                    inline=False
                )
            if not self.mensagens_task:
                self.mensagens_task = asyncio.create_task(self.sistema_mensagens_automaticas())
                embed.add_field(
                    name="📢 Mensagens Automáticas",
                    value="✅ Sistema de telecomunicações ativo",
                    inline=False
                )
            await message.edit(embed=embed)
        except Exception as e:
            embed_error = discord.Embed(
                title="❌ Erro ao Conectar",
                description=f"Não foi possível conectar ao canal: {e}",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed_error)

    @commands.command(name='parar_sistema', aliases=['stop_voice', 'parar_voz'])
    @commands.has_permissions(manage_channels=True)
    async def parar_sistema_voz(self, ctx):
        """Para o sistema de voz"""
        if not self.is_playing_cycle:
            return await ctx.send("❌ O sistema de voz não está ativo.")
            
        self.is_playing_cycle = False
        
        # Para as mensagens automáticas
        if self.mensagens_task:
            self.mensagens_task.cancel()
            self.mensagens_task = None
        
        if self.voice_client:
            try:
                await self.voice_client.disconnect()
            except:
                pass
            self.voice_client = None
            
        embed = discord.Embed(
            title="🔇 Sistema de Telecomunicações Desativado",
            description="Sistema completo parado: música, mensagens e conexão de voz.",
            color=discord.Color.red()
        )
        embed.add_field(
            name="🎵 Música",
            value="❌ Parada",
            inline=True
        )
        embed.add_field(
            name="📢 Mensagens",
            value="❌ Paradas",
            inline=True
        )
        embed.add_field(
            name="🔗 Conexão",
            value="❌ Desconectado",
            inline=True
        )
        await ctx.send(embed=embed)

    @commands.command(name='falar', aliases=['speak', 'voice_say'])
    @commands.has_permissions(manage_messages=True)
    async def falar_texto(self, ctx, *, texto: str):
        """Faz o bot processar um texto usando clonagem de voz"""
        if len(texto) > 500:
            return await ctx.send("❌ O texto é muito longo (máximo 500 caracteres).")
        
        embed_loading = discord.Embed(
            title="🎤 Processando Texto",
            description="Processando texto com IA...",
            color=discord.Color.yellow()
        )
        message = await ctx.send(embed=embed_loading)
        
        try:
            # Verifica se ElevenLabs está configurado
            if ELEVENLABS_API_KEY and VOICE_ID and ELEVENLABS_API_KEY.strip() != "":
                # Gera o áudio
                arquivo_audio = await self.gerar_audio_elevenlabs(texto)
                
                if arquivo_audio:
                    embed_success = discord.Embed(
                        title="✅ Áudio Gerado",
                        description=f"**Texto:** {texto}\n**Arquivo:** `{arquivo_audio}`",
                        color=discord.Color.green()
                    )
                    embed_success.add_field(
                        name="ℹ️ Nota",
                        value="Arquivo de áudio criado. Para reproduzir, instale FFmpeg.",
                        inline=False
                    )
                else:
                    embed_success = discord.Embed(
                        title="📝 Modo Texto",
                        description=f"**Texto processado:** {texto}",
                        color=discord.Color.blue()
                    )
            else:
                embed_success = discord.Embed(
                    title="📝 Modo Texto",
                    description=f"**Texto processado:** {texto}",
                    color=discord.Color.blue()
                )
                embed_success.add_field(
                    name="ℹ️ Para ativar voz",
                    value="Configure ElevenLabs API no arquivo .env",
                    inline=False
                )
                
            await message.edit(embed=embed_success)
                
        except Exception as e:
            embed_error = discord.Embed(
                title="❌ Erro",
                description=f"Ocorreu um erro: {e}",
                color=discord.Color.red()
            )
            await message.edit(embed=embed_error)

    @commands.command(name='status_voz', aliases=['voice_status'])
    async def status_sistema_voz(self, ctx):
        """Mostra o status do sistema de voz"""
        embed = discord.Embed(
            title="📊 Status do Sistema de Voz",
            color=discord.Color.blue()
        )
        
        # Status do sistema
        if self.is_playing_cycle:
            embed.add_field(
                name="🟢 Status",
                value="Sistema ativo",
                inline=True
            )
        else:
            embed.add_field(
                name="🔴 Status",
                value="Sistema inativo",
                inline=True
            )
        
        # Configurações da API
        api_status = "✅ Configurada" if ELEVENLABS_API_KEY and VOICE_ID else "❌ Não configurada"
        embed.add_field(
            name="🔧 API ElevenLabs",
            value=api_status,
            inline=True
        )
        
        embed.add_field(
            name="📞 Mensagens Disponíveis",
            value=f"{len(self.mensagens_sistema)} mensagens programadas",
            inline=True
        )
        
        # Status do FFmpeg
        try:
            # Teste simples para verificar FFmpeg
            import subprocess
            subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
            ffmpeg_status = "✅ Instalado"
        except:
            ffmpeg_status = "❌ Não instalado"
            
        embed.add_field(
            name="🎵 FFmpeg",
            value=ffmpeg_status,
            inline=True
        )
        
        embed.add_field(
            name="💡 Dica",
            value="Para áudio completo, instale FFmpeg e configure ElevenLabs",
            inline=False
        )
        
        await ctx.send(embed=embed)

    @commands.command(name='add_mensagem', aliases=['adicionar_mensagem'])
    @commands.has_permissions(administrator=True)
    async def adicionar_mensagem(self, ctx, *, mensagem: str):
        """Adiciona uma nova mensagem ao sistema (Admin apenas)"""
        if len(mensagem) > 200:
            return await ctx.send("❌ A mensagem é muito longa (máximo 200 caracteres).")
            
        self.mensagens_sistema.append(mensagem)
        
        embed = discord.Embed(
            title="✅ Mensagem Adicionada",
            description=f"Nova mensagem adicionada ao sistema:\n\n*{mensagem}*",
            color=discord.Color.green()
        )
        embed.set_footer(text=f"Total de mensagens: {len(self.mensagens_sistema)}")
        await ctx.send(embed=embed)

    @commands.command(name='falar_com_musica', aliases=['speak_music', 'falar_jazz'])
    @commands.has_permissions(manage_messages=True)
    async def falar_com_musica(self, ctx, *, texto: str):
        """Reproduz uma mensagem com clonagem de voz e música de espera jazz"""
        if len(texto) > 500:
            return await ctx.send("❌ O texto é muito longo (máximo 500 caracteres).")
        
        embed_loading = discord.Embed(
            title="🎵 Processando com Música Jazz",
            description="Iniciando música de espera e processando texto...",
            color=discord.Color.yellow()
        )
        message = await ctx.send(embed=embed_loading)
        
        try:
            # Inicia a música de espera
            musica_tocando = await self.tocar_musica_espera()
            
            if musica_tocando:
                embed_loading.description = "🎷 Música jazz tocando... Gerando áudio com ElevenLabs..."
                await message.edit(embed=embed_loading)
                
                # Aguarda um pouco para a música tocar
                await asyncio.sleep(2)
            
            # Verifica se ElevenLabs está configurado
            if ELEVENLABS_API_KEY and VOICE_ID and ELEVENLABS_API_KEY.strip() != "":
                # Para a música temporariamente para a fala
                if musica_tocando:
                    await self.parar_musica_temporariamente()
                    await asyncio.sleep(1)  # Aguarda parar completamente
                    
                # Gera o áudio da fala
                arquivo_audio = await self.gerar_audio_elevenlabs(texto)
                
                # Reproduz o áudio da fala no Discord
                if arquivo_audio and self.voice_client:
                    try:
                        # Opções de fade para a fala
                        ffmpeg_options_voice = {
                            'before_options': '-re',
                            'options': '-vn -filter:a "volume=0.9,afade=t=in:d=0.8,afade=t=out:st=4:d=1.2"'
                        }
                        source = discord.FFmpegPCMAudio(arquivo_audio, **ffmpeg_options_voice)
                        self.voice_client.play(source)
                        
                        # Aguarda a fala terminar
                        while self.voice_client.is_playing():
                            await asyncio.sleep(0.5)
                    except Exception as e:
                        print(f"Erro ao reproduzir fala: {e}")
                    
                # Volta a música de espera
                if musica_tocando:
                    await asyncio.sleep(1)  # Pausa antes de voltar música
                    await self.tocar_musica_espera()
                
                embed_success = discord.Embed(
                    title="🎵✅ Sistema Jazz Completo",
                    description=f"**Mensagem reproduzida:** {texto}",
                    color=discord.Color.green()
                )
                embed_success.add_field(
                    name="🎷 Jazz",
                    value="Música de espera tocando",
                    inline=True
                )
                embed_success.add_field(
                    name="🎤 Voz",
                    value="ElevenLabs processou",
                    inline=True
                )
            else:
                embed_success = discord.Embed(
                    title="🎷 Modo Jazz + Texto",
                    description=f"**Mensagem:** {texto}",
                    color=discord.Color.blue()
                )
                embed_success.add_field(
                    name="ℹ️ Para voz completa",
                    value="Configure ElevenLabs API no .env",
                    inline=False
                )
                
            await message.edit(embed=embed_success)
                
        except Exception as e:
            await self.parar_musica_temporariamente()
            embed_error = discord.Embed(
                title="❌ Erro",
                description=f"Ocorreu um erro: {e}",
                color=discord.Color.red()
            )
            await message.edit(embed=embed_error)

    @commands.command(name='controlar_jazz', aliases=['jazz_control', 'musica'])
    @commands.has_permissions(manage_messages=True)
    async def controlar_jazz(self, ctx, acao: str = None):
        """Controla a música jazz de espera (play/stop/status)"""
        if not acao:
            embed = discord.Embed(
                title="🎷 Controle da Música Jazz",
                description="Use: `!controlar_jazz [play/stop/status]`",
                color=discord.Color.blue()
            )
            embed.add_field(
                name="🎵 Comandos",
                value="• `play` - Inicia a música\n• `stop` - Para a música\n• `status` - Mostra status",
                inline=False
            )
            return await ctx.send(embed=embed)
        
        acao = acao.lower()
        
        if acao in ['play', 'tocar', 'iniciar']:
            sucesso = await self.tocar_musica_espera()
            if sucesso:
                embed = discord.Embed(
                    title="🎷 Música Jazz Iniciada",
                    description="Jazz lounge tocando em loop!",
                    color=discord.Color.green()
                )
            else:
                embed = discord.Embed(
                    title="❌ Erro",
                    description="Não foi possível iniciar a música. Verifique se pygame está instalado.",
                    color=discord.Color.red()
                )
            await ctx.send(embed=embed)
            
        elif acao in ['stop', 'parar', 'pauser']:
            await self.parar_musica_temporariamente()
            embed = discord.Embed(
                title="🔇 Música Jazz Parada",
                description="Música de espera pausada.",
                color=discord.Color.orange()
            )
            await ctx.send(embed=embed)
            
        elif acao in ['status', 'info']:
            if self.voice_client and self.voice_client.is_connected():
                if self.voice_client.is_playing():
                    status = "🎵 Tocando no Discord"
                elif self.voice_client.is_paused():
                    status = "⏸️ Pausada"
                else:
                    status = "🔇 Conectado mas não tocando"
            else:
                status = "❌ Bot não conectado ao canal"
                
            # Verifica FFmpeg
            try:
                subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True, timeout=3)
                ffmpeg_status = "✅ Disponível"
            except:
                ffmpeg_status = "❌ Não encontrado"
                
            embed = discord.Embed(
                title="📊 Status da Música Jazz",
                color=discord.Color.blue()
            )
            embed.add_field(name="🎵 Status", value=status, inline=True)
            embed.add_field(name="📁 Arquivo", value=self.musica_espera, inline=True)
            embed.add_field(name="📂 Existe", value="✅" if os.path.exists(self.musica_espera) else "❌", inline=True)
            embed.add_field(name="🔧 FFmpeg", value=ffmpeg_status, inline=True)
            embed.add_field(name="🔗 Canal", value=f"<#{AUDIO_CHANNEL_ID}>" if AUDIO_CHANNEL_ID else "❌", inline=True)
            embed.add_field(name="⚙️ Sistema", value="Discord Audio API", inline=True)
            await ctx.send(embed=embed)
        else:
            await ctx.send("❌ Ação inválida. Use: `play`, `stop` ou `status`")

    async def sistema_mensagens_automaticas(self):
        """Task que roda mensagens automáticas periodicamente"""
        print("📢 Sistema de mensagens automáticas iniciado")
        while self.is_playing_cycle:
            try:
                # Aguarda entre 20 a 35 segundos para dar tempo dos fades
                tempo_espera = random.randint(20, 35)
                print(f"⏰ Aguardando {tempo_espera} segundos para próxima mensagem...")
                await asyncio.sleep(tempo_espera)
                
                # Verifica se ainda está ativo e conectado
                if not self.is_playing_cycle or not self.voice_client or not self.voice_client.is_connected():
                    break
                
                # Sempre usa a primeira mensagem na primeira execução, depois aleatória
                if self.primeira_mensagem:
                    mensagem = self.mensagens_sistema[0]  # A primeira mensagem sempre
                    self.primeira_mensagem = False  # Próximas serão aleatórias
                    print(f"📢 Iniciando com primeira mensagem: {mensagem}")
                else:
                    mensagem = random.choice(self.mensagens_sistema)
                    print(f"📢 Iniciando reprodução de mensagem automática: {mensagem}")
                
                # Marca que está tocando mensagem
                self.tocando_mensagem = True
                
                # Para a música temporariamente
                await self.parar_musica_temporariamente()
                
                # Verifica se ElevenLabs está configurado
                print(f"🔍 Debug - ELEVENLABS_API_KEY: {'✅ Configurada' if ELEVENLABS_API_KEY else '❌ Vazia'}")
                print(f"🔍 Debug - VOICE_ID: {'✅ Configurada' if VOICE_ID else '❌ Vazia'}")
                
                if ELEVENLABS_API_KEY and VOICE_ID and ELEVENLABS_API_KEY.strip() != "":
                    print(f"🎤 Gerando áudio para: {mensagem}")
                    # Gera o áudio da mensagem
                    arquivo_audio = await self.gerar_audio_elevenlabs(mensagem)
                    
                    if arquivo_audio and self.voice_client:
                        print(f"✅ Arquivo de áudio gerado: {arquivo_audio}")
                        try:
                            # Reproduz a mensagem com fade in/out profissional
                            ffmpeg_options = {
                                'before_options': '-re',
                                'options': '-vn -filter:a "volume=0.85,afade=t=in:d=1.5,afade=t=out:st=6:d=2"'  # Fade mais suave e profissional
                            }
                            source = discord.FFmpegPCMAudio(arquivo_audio, **ffmpeg_options)
                            self.voice_client.play(source)
                            print(f"🔊 Reproduzindo mensagem no Discord...")
                            
                            # Aguarda a mensagem terminar completamente
                            while self.voice_client.is_playing():
                                await asyncio.sleep(0.5)
                            
                            # Aguarda um pouco mais para garantir que terminou
                            await asyncio.sleep(1.5)
                            
                            print(f"✅ Mensagem reproduzida com sucesso!")
                            
                            # NÃO remove arquivo se for do cache permanente
                            if arquivo_audio.startswith('temp_audio/'):
                                try:
                                    os.remove(arquivo_audio)
                                    print(f"🗑️ Arquivo temporário removido: {arquivo_audio}")
                                except:
                                    pass
                            else:
                                print(f"💾 Arquivo mantido no cache: {arquivo_audio}")
                            
                        except Exception as e:
                            print(f"⚠️ Erro ao reproduzir mensagem automática: {e}")
                    else:
                        if not arquivo_audio:
                            print(f"❌ Falha ao gerar arquivo de áudio")
                        if not self.voice_client:
                            print(f"❌ Voice client não disponível")
                        # Simula tempo de fala mesmo sem áudio
                        await asyncio.sleep(5)
                else:
                    # Modo texto se não tiver ElevenLabs
                    print(f"📢 [MODO TEXTO] {mensagem}")
                    await asyncio.sleep(4)  # Simula tempo de fala (um pouco menor)
                
                # Marca que terminou de tocar mensagem
                self.tocando_mensagem = False
                
                # Retoma a música de espera
                if self.is_playing_cycle and self.voice_client:
                    await self.retomar_musica()
                    
            except asyncio.CancelledError:
                print("📢 Sistema de mensagens automáticas cancelado")
                break
            except Exception as e:
                print(f"⚠️ Erro no sistema de mensagens: {e}")
                self.tocando_mensagem = False  # Reseta flag em caso de erro
                # Tenta retomar música mesmo em caso de erro
                if self.is_playing_cycle and self.voice_client:
                    await self.retomar_musica()
                await asyncio.sleep(30)  # Aguarda antes de tentar novamente

    @commands.command(name='parar_mensagens', aliases=['stop_messages'])
    @commands.has_permissions(manage_channels=True)
    async def parar_mensagens_automaticas(self, ctx):
        """Para apenas as mensagens automáticas (mantém música)"""
        if self.mensagens_task:
            self.mensagens_task.cancel()
            self.mensagens_task = None
            
            embed = discord.Embed(
                title="📢 Mensagens Automáticas Paradas",
                description="Sistema de mensagens desativado. Música continua tocando.",
                color=discord.Color.orange()
            )
            await ctx.send(embed=embed)
        else:
            await ctx.send("❌ Sistema de mensagens não estava ativo.")
    
    @commands.command(name='cache_info')
    async def info_cache(self, ctx):
        """Mostra informações sobre o cache de vozes"""
        cache_dir = 'cached_voices'
        backup_dir = 'backup_voices'
        
        # Conta arquivos no cache
        cache_files = glob.glob(os.path.join(cache_dir, '*.mp3'))
        backup_files = glob.glob(os.path.join(backup_dir, '*.mp3'))
        
        embed = discord.Embed(
            title="💾 Informações do Cache de Voz",
            description="Sistema inteligente de cache para economizar créditos ElevenLabs",
            color=discord.Color.blue()
        )
        
        embed.add_field(
            name="📊 Cache Atual",
            value=f"**Arquivos:** {len(cache_files)}\n**Pasta:** `{cache_dir}/`",
            inline=True
        )
        
        embed.add_field(
            name="🔄 Backups",
            value=f"**Arquivos:** {len(backup_files)}\n**Pasta:** `{backup_dir}/`",
            inline=True
        )
        
        embed.add_field(
            name="💰 Economia Estimada",
            value=f"**Créditos salvos:** ~{len(cache_files) * 1000} chars\n**Valor aprox:** ${len(cache_files) * 0.20:.2f}",
            inline=False
        )
        
        embed.add_field(
            name="⚙️ Configurações",
            value=f"**Voz Atual:** `{VOICE_ID[:20]}...`\n**API:** ElevenLabs\n**Formato:** MP3",
            inline=False
        )
        
        embed.set_footer(text="💡 Cache reutiliza mensagens já geradas para economizar créditos")
        
        await ctx.send(embed=embed)

    @commands.command(name='listar_backups', aliases=['list_backups'])
    @commands.has_permissions(administrator=True)
    async def listar_backups(self, ctx):
        """Lista todos os backups de voz disponíveis"""
        try:
            backup_dir = 'backup_voices'
            
            if not os.path.exists(backup_dir):
                await ctx.send("❌ Nenhum backup encontrado.")
                return
            
            backups = []
            for item in os.listdir(backup_dir):
                backup_path = os.path.join(backup_dir, item)
                if os.path.isdir(backup_path):
                    info_file = os.path.join(backup_path, 'backup_info.json')
                    if os.path.exists(info_file):
                        try:
                            with open(info_file, 'r') as f:
                                info = json.load(f)
                            backups.append({
                                'nome': item,
                                'info': info,
                                'path': backup_path
                            })
                        except:
                            pass
            
            if not backups:
                await ctx.send("❌ Nenhum backup válido encontrado.")
                return
            
            embed = discord.Embed(
                title="📂 Backups de Voz Disponíveis",
                description=f"Encontrados {len(backups)} backup(s)",
                color=discord.Color.blue()
            )
            
            for i, backup in enumerate(backups[:10], 1):  # Máximo 10
                info = backup['info']
                embed.add_field(
                    name=f"{i}. {backup['nome']}",
                    value=f"🎵 **Voz:** `{info.get('voice_id', 'N/A')[:15]}...`\n" +
                          f"📅 **Data:** {info.get('timestamp', 'N/A')}\n" +
                          f"📁 **Arquivos:** {info.get('total_files', 0)}",
                    inline=False
                )
            
            embed.set_footer(text="💡 Use !restaurar_backup <nome> para restaurar")
            await ctx.send(embed=embed)
            
        except Exception as e:
            await ctx.send(f"❌ Erro ao listar backups: {e}")

    @commands.command(name='reload_cache', aliases=['refresh_cache', 'atualizar_cache'])
    @commands.has_permissions(administrator=True)
    async def reload_cache(self, ctx, action: str = None):
        """
        Atualiza o cache de vozes e frases
        Uso: !reload_cache [clear|rebuild|info]
        """
        embed_inicial = discord.Embed(
            title="🔄 Reload do Cache",
            description="Atualizando sistema de cache...",
            color=discord.Color.blue()
        )
        message = await ctx.send(embed=embed_inicial)
        
        try:
            if action == "clear":
                # Limpa todo o cache
                cache_dir = 'cached_voices'
                temp_dir = 'temp_audio'
                
                arquivos_removidos = 0
                
                # Remove arquivos do cache
                if os.path.exists(cache_dir):
                    for arquivo in os.listdir(cache_dir):
                        if arquivo.endswith('.mp3'):
                            os.remove(os.path.join(cache_dir, arquivo))
                            arquivos_removidos += 1
                
                # Remove arquivos temporários
                if os.path.exists(temp_dir):
                    for arquivo in os.listdir(temp_dir):
                        if arquivo.endswith('.mp3'):
                            os.remove(os.path.join(temp_dir, arquivo))
                            arquivos_removidos += 1
                
                embed = discord.Embed(
                    title="🗑️ Cache Limpo",
                    description=f"Cache completamente limpo!\n**Arquivos removidos:** {arquivos_removidos}",
                    color=discord.Color.orange()
                )
                embed.add_field(
                    name="📝 Próximos Passos",
                    value="• Use `!reload_cache rebuild` para recriar o cache\n• Ou aguarde - será recriado automaticamente conforme necessário",
                    inline=False
                )
                
            elif action == "rebuild":
                # Reconstrói todo o cache
                if not ELEVENLABS_API_KEY or not VOICE_ID:
                    embed = discord.Embed(
                        title="❌ Erro",
                        description="ElevenLabs não configurado. Não é possível reconstruir cache.",
                        color=discord.Color.red()
                    )
                    await message.edit(embed=embed)
                    return
                
                embed_building = discord.Embed(
                    title="🔨 Reconstruindo Cache",
                    description="Gerando todas as frases com a voz atual...",
                    color=discord.Color.blue()
                )
                await message.edit(embed=embed_building)
                
                # Limpa cache atual
                cache_dir = 'cached_voices'
                if os.path.exists(cache_dir):
                    for arquivo in os.listdir(cache_dir):
                        if arquivo.endswith('.mp3'):
                            os.remove(os.path.join(cache_dir, arquivo))
                
                # Reconstrói todas as frases
                await self.gerar_todas_frases_nova_voz(VOICE_ID, ctx)
                
                embed = discord.Embed(
                    title="✅ Cache Reconstruído",
                    description=f"Cache completamente reconstruído com a voz atual!\n**Mensagens:** {len(self.mensagens_sistema)}",
                    color=discord.Color.green()
                )
                
            elif action == "info":
                # Mostra informações detalhadas do cache
                cache_dir = 'cached_voices'
                temp_dir = 'temp_audio'
                backup_dir = 'backup_voices'
                
                cache_files = len([f for f in os.listdir(cache_dir) if f.endswith('.mp3')]) if os.path.exists(cache_dir) else 0
                temp_files = len([f for f in os.listdir(temp_dir) if f.endswith('.mp3')]) if os.path.exists(temp_dir) else 0
                backup_files = len(glob.glob(os.path.join(backup_dir, '**', '*.mp3'), recursive=True)) if os.path.exists(backup_dir) else 0
                
                embed = discord.Embed(
                    title="📊 Informações Detalhadas do Cache",
                    description="Estado atual do sistema de cache",
                    color=discord.Color.blue()
                )
                
                voice_display = f"{VOICE_ID[:15]}..." if VOICE_ID and len(VOICE_ID) > 15 else VOICE_ID if VOICE_ID else 'N/A'
                embed.add_field(
                    name="💾 Cache Principal",
                    value=f"**Arquivos:** {cache_files}\n**Mensagens:** {len(self.mensagens_sistema)}\n**Voz Atual:** `{voice_display}`",
                    inline=True
                )
                
                embed.add_field(
                    name="🗂️ Arquivos Temporários",
                    value=f"**Arquivos:** {temp_files}\n**Pasta:** `{temp_dir}/`",
                    inline=True
                )
                
                embed.add_field(
                    name="🔄 Backups",
                    value=f"**Arquivos:** {backup_files}\n**Pasta:** `{backup_dir}/`",
                    inline=True
                )
                
                embed.add_field(
                    name="⚙️ Status",
                    value=f"**ElevenLabs:** {'✅ OK' if ELEVENLABS_API_KEY else '❌ Não configurado'}\n**Voz ID:** {'✅ OK' if VOICE_ID else '❌ Não configurado'}",
                    inline=False
                )
                
                economia_estimada = cache_files * 0.20
                embed.add_field(
                    name="💰 Economia Estimada",
                    value=f"**Créditos salvos:** ~{cache_files * 1000} chars\n**Valor aprox:** ${economia_estimada:.2f} USD",
                    inline=False
                )
                
            else:
                # Reload padrão - atualiza mensagens sem regenerar tudo
                embed = discord.Embed(
                    title="🔄 Cache Atualizado",
                    description="Sistema de cache recarregado com sucesso!",
                    color=discord.Color.green()
                )
                
                embed.add_field(
                    name="📈 Estatísticas",
                    value=f"**Mensagens do sistema:** {len(self.mensagens_sistema)}\n**Cache mantido:** ✅\n**Configurações:** Atualizadas",
                    inline=False
                )
                
                embed.add_field(
                    name="🛠️ Opções Avançadas",
                    value="• `!reload_cache clear` - Limpar cache\n• `!reload_cache rebuild` - Reconstruir cache\n• `!reload_cache info` - Informações detalhadas",
                    inline=False
                )
            
            await message.edit(embed=embed)
            
        except Exception as e:
            embed_erro = discord.Embed(
                title="❌ Erro no Reload do Cache",
                description=f"Erro: {str(e)}",
                color=discord.Color.red()
            )
            await message.edit(embed=embed_erro)

    @commands.command(name='trocar_musica', aliases=['change_music', 'nova_musica', 'music'])
    @commands.has_permissions(manage_channels=True)
    async def trocar_musica(self, ctx, *, nome_arquivo: str = None):
        """
        Troca a música de fundo do sistema
        Uso: !trocar_musica <nome_do_arquivo.mp3>
        Ou: !trocar_musica (para listar músicas disponíveis)
        """
        
        if not nome_arquivo:
            # Lista músicas disponíveis
            arquivos_mp3 = []
            
            # Procura por arquivos MP3 no diretório principal
            for arquivo in os.listdir('.'):
                if arquivo.endswith('.mp3') and os.path.isfile(arquivo):
                    size = os.path.getsize(arquivo)
                    size_mb = size / (1024 * 1024)
                    arquivos_mp3.append({
                        'name': arquivo,
                        'size': f"{size_mb:.1f}MB",
                        'current': arquivo == self.musica_espera
                    })
            
            if not arquivos_mp3:
                await ctx.send("❌ Nenhum arquivo MP3 encontrado no diretório.")
                return
            
            embed = discord.Embed(
                title="🎵 Músicas Disponíveis",
                description="Selecione uma música para usar como fundo",
                color=discord.Color.blue()
            )
            
            current_music = ""
            available_music = ""
            
            for i, music in enumerate(arquivos_mp3, 1):
                music_info = f"`{i}.` **{music['name']}** ({music['size']})"
                if music['current']:
                    current_music = f"🎵 **Atual:** {music_info}\n"
                else:
                    available_music += f"{music_info}\n"
            
            if current_music:
                embed.add_field(
                    name="🎵 Música Atual",
                    value=current_music,
                    inline=False
                )
            
            if available_music:
                embed.add_field(
                    name="🎼 Outras Músicas",
                    value=available_music,
                    inline=False
                )
            
            embed.add_field(
                name="📝 Como Usar",
                value="• `!trocar_musica nome_arquivo.mp3`\n• Para adicionar novas músicas, coloque arquivos MP3 na pasta do bot",
                inline=False
            )
            
            embed.set_footer(text="💡 A música será trocada automaticamente se o sistema estiver ativo")
            await ctx.send(embed=embed)
            return
        
        # Verifica se o arquivo existe
        if not os.path.exists(nome_arquivo):
            # Procura por nome parcial
            arquivos_encontrados = []
            for arquivo in os.listdir('.'):
                if arquivo.endswith('.mp3') and nome_arquivo.lower() in arquivo.lower():
                    arquivos_encontrados.append(arquivo)
            
            if len(arquivos_encontrados) == 1:
                nome_arquivo = arquivos_encontrados[0]
            elif len(arquivos_encontrados) > 1:
                embed = discord.Embed(
                    title="🔍 Vários Arquivos Encontrados",
                    description=f"Encontrei {len(arquivos_encontrados)} arquivos com '{nome_arquivo}':",
                    color=discord.Color.orange()
                )
                for i, arquivo in enumerate(arquivos_encontrados[:10], 1):
                    embed.add_field(
                        name=f"{i}. {arquivo}",
                        value=f"Use: `!trocar_musica {arquivo}`",
                        inline=False
                    )
                await ctx.send(embed=embed)
                return
            else:
                await ctx.send(f"❌ Arquivo `{nome_arquivo}` não encontrado. Use `!trocar_musica` para ver as opções.")
                return
        
        # Verifica se é um arquivo MP3 válido
        if not nome_arquivo.endswith('.mp3'):
            await ctx.send("❌ Apenas arquivos MP3 são suportados.")
            return
        
        # Salva música anterior
        musica_anterior = self.musica_espera
        
        try:
            # Atualiza a música
            self.musica_espera = nome_arquivo
            
            # Se o sistema estiver ativo, reinicia com a nova música
            if self.is_playing_cycle and self.voice_client:
                embed_trocando = discord.Embed(
                    title="🔄 Trocando Música",
                    description="Aplicando nova música ao sistema...",
                    color=discord.Color.blue()
                )
                message = await ctx.send(embed=embed_trocando)
                
                # Para a música atual
                if self.voice_client.is_playing():
                    self.voice_client.stop()
                
                # Aguarda um pouco e inicia a nova música
                await asyncio.sleep(1)
                sucesso = await self.tocar_musica_espera()
                
                if sucesso:
                    embed = discord.Embed(
                        title="✅ Música Trocada",
                        description="Nova música aplicada com sucesso!",
                        color=discord.Color.green()
                    )
                    embed.add_field(
                        name="🎵 Música Anterior",
                        value=f"`{musica_anterior}`",
                        inline=True
                    )
                    embed.add_field(
                        name="🎶 Nova Música",
                        value=f"`{nome_arquivo}`",
                        inline=True
                    )
                    embed.add_field(
                        name="📊 Status",
                        value="✅ Sistema ativo com nova música",
                        inline=False
                    )
                else:
                    # Reverte se deu erro
                    self.musica_espera = musica_anterior
                    embed = discord.Embed(
                        title="❌ Erro ao Trocar Música",
                        description="Não foi possível reproduzir a nova música. Revertendo...",
                        color=discord.Color.red()
                    )
                
                await message.edit(embed=embed)
            else:
                # Sistema não está ativo, apenas atualiza a configuração
                embed = discord.Embed(
                    title="✅ Música Configurada",
                    description="Nova música definida! Será usada quando o sistema for iniciado.",
                    color=discord.Color.green()
                )
                embed.add_field(
                    name="🎶 Nova Música",
                    value=f"`{nome_arquivo}`",
                    inline=False
                )
                embed.add_field(
                    name="📊 Status",
                    value="⏸️ Sistema pausado - música será aplicada quando iniciar",
                    inline=False
                )
                await ctx.send(embed=embed)
            
        except Exception as e:
            # Reverte em caso de erro
            self.musica_espera = musica_anterior
            embed_erro = discord.Embed(
                title="❌ Erro ao Trocar Música",
                description=f"Erro: {str(e)}",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed_erro)

    @commands.command(name='reiniciar_sistema', aliases=['restart_voice', 'reiniciar_voz'])
    @commands.has_permissions(manage_channels=True)
    async def reiniciar_sistema_voz(self, ctx):
        """Reinicia o sistema de voz (desconecta e conecta novamente)"""
        await ctx.send("♻️ Reiniciando sistema de voz...")
        await self.parar_sistema_voz(ctx)
        await asyncio.sleep(2)
        await self.iniciar_sistema_voz(ctx)

    @commands.command(name='ativar_sistema_voz', aliases=['ativar_voz'])
    @commands.has_permissions(administrator=True)
    async def ativar_sistema_voz(self, ctx):
        """Ativa manualmente o sistema de voz e conecta ao canal configurado"""
        await ctx.send("🔄 Ativando sistema de voz...")
        await self.iniciar_sistema_voz(ctx)

    @commands.command(name='desativar_sistema_voz', aliases=['desativar_voz'])
    @commands.has_permissions(administrator=True)
    async def desativar_sistema_voz(self, ctx):
        """Desativa manualmente o sistema de voz e desconecta do canal"""
        await ctx.send("🛑 Desativando sistema de voz...")
        await self.parar_sistema_voz(ctx)

async def setup(bot):
    await bot.add_cog(VoiceSystem(bot)) 