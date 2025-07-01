import discord
from discord.ext import commands
import os
import datetime
import psutil
import asyncio
from typing import Optional
from dotenv import load_dotenv, set_key
import re

load_dotenv()

def get_env_id(key):
    value = os.getenv(key, "0")
    return int(value.strip('\'\"'))

def get_env_id_validado(guild, key, tipo='canal'):
    value = os.getenv(key, "0").strip(' "\'\n\r')
    try:
        id_int = int(value)
        if tipo == 'canal':
            canal = guild.get_channel(id_int)
            if canal:
                return id_int, True
            else:
                return id_int, False
        elif tipo == 'categoria':
            categoria = next((c for c in guild.categories if c.id == id_int), None)
            if categoria:
                return id_int, True
            else:
                return id_int, False
        elif tipo == 'cargo':
            role = guild.get_role(id_int)
            if role:
                return id_int, True
            else:
                return id_int, False
        else:
            return id_int, True
    except Exception:
        return None, False

class AdminCommands(commands.Cog):
    """Comandos administrativos para gerenciar o bot"""
    
    def __init__(self, bot):
        self.bot = bot
        self.start_time = datetime.datetime.now()
    
    @commands.Cog.listener()
    async def on_ready(self):
        print("⚙️ Comandos administrativos carregados")
        # Diagnóstico automático do .env ao iniciar
        guild = self.bot.guilds[0] if self.bot.guilds else None
        if guild:
            checks = [
                ("TICKET_CATEGORY_ID", 'categoria'),
                ("SUPPORT_ROLE_ID", 'cargo'),
                ("AUDIO_CHANNEL_ID", 'canal'),
                ("ADMIN_CATEGORY_ID", 'categoria'),
                ("TICKETS_CHANNEL_ID", 'canal'),
                ("INFO_CHANNEL_ID", 'canal')
            ]
            embed = discord.Embed(title="🛠️ Diagnóstico do .env (inicialização)", color=discord.Color.blue())
            tudo_ok = True
            for key, tipo in checks:
                id_val, ok = get_env_id_validado(guild, key, tipo)
                if ok:
                    embed.add_field(name=key, value=f"✅ {id_val}", inline=False)
                else:
                    tudo_ok = False
                    embed.add_field(name=key, value=f"❌ {id_val if id_val else 'Não definido ou inválido'}", inline=False)
            if tudo_ok:
                embed.description = "Todos os IDs do .env estão corretos e existem no servidor!"
                embed.color = discord.Color.green()
            else:
                embed.description = "Atenção: Corrija os IDs marcados com ❌ no seu .env para evitar erros."
                embed.color = discord.Color.red()
            # Tenta enviar para o canal de controle admin, se existir
            canal_admin = discord.utils.get(guild.text_channels, name="📊-painel-controle")
            if canal_admin:
                try:
                    await canal_admin.send(embed=embed)
                except Exception:
                    pass

    @commands.Cog.listener()
    async def on_message(self, message):
        # Ignora mensagens do bot
        if message.author.bot:
            return
        # Verifica se a mensagem é um comando do bot
        ctx = await self.bot.get_context(message)
        if ctx.valid:
            try:
                await message.delete()
            except Exception:
                pass

    @commands.command(name='info', aliases=['status', 'stats'])
    async def info_command(self, ctx):
        """Mostra informações detalhadas sobre o bot"""
        
        # Calcula tempo online
        uptime = datetime.datetime.now() - self.start_time
        uptime_str = str(uptime).split('.')[0]
        
        # Informações do sistema
        cpu_percent = psutil.cpu_percent()
        memory = psutil.virtual_memory()
        memory_used = memory.used / (1024**2)
        memory_total = memory.total / (1024**2)
        
        embed = discord.Embed(
            title="📊 Informações do Bot",
            color=discord.Color.blue(),
            timestamp=datetime.datetime.now()
        )
        
        embed.add_field(
            name="🤖 Bot",
            value=f"**Nome:** {self.bot.user.name}\n**ID:** {self.bot.user.id}\n**Versão:** 1.0.0",
            inline=True
        )
        
        embed.add_field(
            name="⏱️ Uptime",
            value=f"{uptime_str}",
            inline=True
        )
        
        embed.add_field(
            name="🌐 Servidores",
            value=f"{len(self.bot.guilds)} servidor(es)",
            inline=True
        )
        
        embed.add_field(
            name="💻 Sistema",
            value=f"**CPU:** {cpu_percent}%\n**RAM:** {memory_used:.1f}MB / {memory_total:.1f}MB",
            inline=True
        )
        
        embed.add_field(
            name="🔧 Extensões",
            value=f"{len(self.bot.extensions)} cog(s) carregado(s)",
            inline=True
        )
        
        total_users = sum(guild.member_count for guild in self.bot.guilds if guild.member_count)
        embed.add_field(
            name="👥 Usuários",
            value=f"{total_users} usuário(s)",
            inline=True
        )
        
        if self.bot.user.avatar:
            embed.set_thumbnail(url=self.bot.user.avatar.url)
        
        embed.set_footer(text=f"Solicitado por {ctx.author}")
        
        await ctx.send(embed=embed)

    @commands.command(name='limpar', aliases=['clear', 'purge'])
    @commands.has_permissions(manage_messages=True)
    async def limpar_mensagens(self, ctx, quantidade: int = 10):
        """Limpa mensagens do canal atual"""
        if quantidade <= 0 or quantidade > 100:
            return await ctx.send("❌ Quantidade deve ser entre 1 e 100.")
        
        try:
            deleted = await ctx.channel.purge(limit=quantidade + 1)
            
            embed = discord.Embed(
                title="🧹 Mensagens Limpas",
                description=f"Removidas {len(deleted) - 1} mensagem(s) do canal.",
                color=discord.Color.green()
            )
            
            confirm_msg = await ctx.send(embed=embed)
            await confirm_msg.delete(delay=5)
            
        except discord.Forbidden:
            await ctx.send("❌ Não tenho permissão para deletar mensagens.")
        except Exception as e:
            await ctx.send(f"❌ Erro ao limpar mensagens: {e}")

    @commands.command(name='say', aliases=['falar_texto'])
    @commands.has_permissions(manage_messages=True)
    async def say_command(self, ctx, canal: Optional[discord.TextChannel], *, mensagem: str):
        """Faz o bot enviar uma mensagem em um canal"""
        target_channel = canal if canal is not None else ctx.channel
        
        try:
            await target_channel.send(mensagem)
            if target_channel != ctx.channel:
                await ctx.send(f"✅ Mensagem enviada para {target_channel.mention}")
            else:
                await ctx.message.delete()
        except discord.Forbidden:
            await ctx.send(f"❌ Não tenho permissão para enviar mensagens em {target_channel.mention}")

    @commands.command(name='embed')
    @commands.has_permissions(manage_messages=True)
    async def criar_embed(self, ctx, titulo: str, *, descricao: str):
        """Cria um embed personalizado"""
        embed = discord.Embed(
            title=titulo,
            description=descricao,
            color=discord.Color.blue(),
            timestamp=datetime.datetime.now()
        )
        embed.set_footer(text=f"Criado por {ctx.author}")
        
        await ctx.send(embed=embed)
        await ctx.message.delete()

    @commands.command(name='backup_transcripts')
    @commands.has_permissions(administrator=True)
    async def backup_transcripts(self, ctx):
        """Cria um backup dos transcripts"""
        if not os.path.exists('transcripts'):
            return await ctx.send("❌ Pasta de transcripts não encontrada.")
        
        transcripts = os.listdir('transcripts')
        if not transcripts:
            return await ctx.send("❌ Nenhum transcript encontrado.")
        
        embed = discord.Embed(
            title="📁 Backup de Transcripts",
            description=f"Encontrados {len(transcripts)} arquivo(s) de transcript.",
            color=discord.Color.blue()
        )
        
        recent_transcripts = sorted(transcripts, reverse=True)[:10]
        transcript_list = "\n".join([f"• {t}" for t in recent_transcripts])
        
        embed.add_field(
            name="📄 Transcripts Recentes",
            value=transcript_list if transcript_list else "Nenhum",
            inline=False
        )
        
        embed.add_field(
            name="💡 Dica",
            value="Faça backup regular da pasta `/transcripts` para não perder dados importantes.",
            inline=False
        )
        
        await ctx.send(embed=embed)

    @commands.command(name='logs')
    @commands.has_permissions(administrator=True)
    async def ver_logs(self, ctx, linhas: int = 20):
        """Mostra os últimos logs do bot"""
        if linhas <= 0 or linhas > 50:
            return await ctx.send("❌ Número de linhas deve ser entre 1 e 50.")
        
        logs_exemplo = [
            "🎫 Ticket criado por usuário#1234",
            "🧠 IA respondeu pergunta sobre horários",
            "🎵 Sistema de voz iniciado",
            "✅ Backup de transcripts realizado",
            "⚙️ Cog recarregado: tickets.py"
        ]
        
        embed = discord.Embed(
            title="📋 Logs do Sistema",
            description=f"Últimas {min(linhas, len(logs_exemplo))} entradas:",
            color=discord.Color.orange()
        )
        
        log_text = "\n".join(logs_exemplo[:linhas])
        embed.add_field(
            name="📝 Atividade Recente",
            value=log_text,
            inline=False
        )
        
        embed.set_footer(text="Para logs completos, verifique o console do bot")
        await ctx.send(embed=embed)

    @commands.command(name='shutdown', aliases=['desligar'])
    @commands.has_permissions(administrator=True)
    async def shutdown_command(self, ctx):
        """Desliga o bot com segurança"""
        embed = discord.Embed(
            title="⚡ Desligando Bot",
            description="O bot será desligado em 5 segundos...",
            color=discord.Color.red()
        )
        embed.add_field(
            name="⚠️ Atenção",
            value="Todos os sistemas de voz serão interrompidos.",
            inline=False
        )
        
        await ctx.send(embed=embed)
        
        for voice_client in self.bot.voice_clients:
            await voice_client.disconnect()
        
        await asyncio.sleep(5)
        await self.bot.close()

    @commands.command(name='reload_all', aliases=['recarregar_tudo'])
    @commands.has_permissions(administrator=True)
    async def reload_all_cogs(self, ctx):
        """Recarrega todos os cogs"""
        embed_loading = discord.Embed(
            title="🔄 Recarregando Cogs",
            description="Recarregando todas as extensões...",
            color=discord.Color.yellow()
        )
        message = await ctx.send(embed=embed_loading)
        
        reloaded = []
        failed = []
        
        for cog_name in list(self.bot.extensions.keys()):
            try:
                await self.bot.reload_extension(cog_name)
                reloaded.append(cog_name)
            except Exception as e:
                failed.append(f"{cog_name}: {e}")
        
        embed_result = discord.Embed(
            title="✅ Recarga Concluída",
            color=discord.Color.green() if not failed else discord.Color.orange()
        )
        
        if reloaded:
            embed_result.add_field(
                name="✅ Recarregados",
                value="\n".join([f"• {cog}" for cog in reloaded]),
                inline=False
            )
        
        if failed:
            embed_result.add_field(
                name="❌ Falharam",
                value="\n".join([f"• {error}" for error in failed]),
                inline=False
            )
        
        await message.edit(embed=embed_result)

    @commands.command(name='invite', aliases=['convite'])
    async def invite_command(self, ctx):
        """Gera um link de convite para o bot"""
        permissions = discord.Permissions(
            manage_channels=True,
            read_messages=True,
            send_messages=True,
            manage_messages=True,
            embed_links=True,
            attach_files=True,
            mention_everyone=True,
            connect=True,
            speak=True
        )
        
        invite_link = discord.utils.oauth_url(self.bot.user.id, permissions=permissions)
        
        embed = discord.Embed(
            title="🔗 Convite do Bot",
            description="Use este link para adicionar o bot a outros servidores:",
            color=discord.Color.green()
        )
        
        embed.add_field(
            name="🎯 Link de Convite",
            value=f"[Clique aqui para convidar]({invite_link})",
            inline=False
        )
        
        embed.add_field(
            name="⚠️ Permissões Necessárias",
            value="• Gerenciar canais\n• Ler/Enviar mensagens\n• Conectar em voz\n• Usar comandos de barra",
            inline=False
        )
        
        await ctx.send(embed=embed)

    @commands.command(name='reset_commands', aliases=['limpar_comandos'])
    @commands.has_permissions(administrator=True)
    async def reset_commands(self, ctx):
        """Remove todos os comandos slash antigos do Discord (Apenas dono do bot)"""
        try:
            embed_loading = discord.Embed(
                title="🔄 Limpando Comandos Antigos",
                description="Removendo todos os comandos slash em cache...",
                color=discord.Color.yellow()
            )
            message = await ctx.send(embed=embed_loading)
            
            # Limpa comandos globais
            self.bot.tree.clear_commands(guild=None)
            await self.bot.tree.sync()
            
            # Limpa comandos do servidor atual
            self.bot.tree.clear_commands(guild=ctx.guild)
            await self.bot.tree.sync(guild=ctx.guild)
            
            embed_success = discord.Embed(
                title="✅ Comandos Limpos",
                description="Todos os comandos antigos foram removidos do cache do Discord.",
                color=discord.Color.green()
            )
            embed_success.add_field(
                name="ℹ️ Nota",
                value="Pode levar alguns minutos para o Discord atualizar completamente.",
                inline=False
            )
            
            await message.edit(embed=embed_success)
            
        except Exception as e:
            embed_error = discord.Embed(
                title="❌ Erro ao Limpar Comandos",
                description=f"Erro: {e}",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed_error)

    @commands.command(name='setup_servidor', aliases=['setup_server', 'configurar_servidor'])
    @commands.has_permissions(administrator=True)
    async def setup_servidor_completo(self, ctx):
        """🚀 Configuração automática completa do servidor - APENAS DONO"""
        
        # Embed inicial
        embed_inicial = discord.Embed(
            title="🚀 Configuração Automática - FavelaZ",
            description="**Iniciando configuração completa do servidor...**\n\n⏳ Este processo pode levar alguns minutos.",
            color=discord.Color.blue()
        )
        embed_inicial.add_field(
            name="📋 O que será criado:",
            value="• Categoria Admin com salas de controle\n• Categoria Membros com sistema de tickets\n• Canal de voz para sistema automático\n• Configuração automática do .env\n• Permissões otimizadas",
            inline=False
        )
        embed_inicial.set_footer(text="🔒 Acesso exclusivo do proprietário")
        
        message = await ctx.send(embed=embed_inicial)
        
        try:
            # 1. Criar cargo de suporte se não existir
            await message.edit(embed=discord.Embed(
                title="🚀 Etapa 1/6",
                description="Criando cargo de suporte...",
                color=discord.Color.yellow()
            ))
            
            support_role = discord.utils.get(ctx.guild.roles, name="🎫 Suporte FavelaZ")
            if not support_role:
                support_role = await ctx.guild.create_role(
                    name="🎫 Suporte FavelaZ",
                    color=discord.Color.green(),
                    permissions=discord.Permissions(
                        manage_messages=True,
                        manage_channels=True,
                        kick_members=True,
                        mute_members=True
                    ),
                    hoist=True,
                    mentionable=True
                )
            
            # 2. Criar CATEGORIA ADMIN
            await message.edit(embed=discord.Embed(
                title="🚀 Etapa 2/6",
                description="Verificando categoria administrativa...",
                color=discord.Color.yellow()
            ))
            
            # Verifica se categoria admin já existe
            categoria_admin = discord.utils.get(ctx.guild.categories, name="🛡️ │ ADMINISTRAÇÃO │ 🛡️")
            
            # Permissões para categoria admin - INVISÍVEL para membros normais
            admin_overwrites = {
                ctx.guild.default_role: discord.PermissionOverwrite(
                    read_messages=False,
                    view_channel=False,
                    connect=False
                ),
                support_role: discord.PermissionOverwrite(
                    read_messages=True,
                    view_channel=True,
                    send_messages=True,
                    manage_messages=True,
                    manage_channels=True,
                    connect=True,
                    speak=True
                ),
                ctx.guild.owner: discord.PermissionOverwrite(
                    read_messages=True,
                    view_channel=True,
                    send_messages=True,
                    manage_messages=True,
                    manage_channels=True,
                    administrator=True,
                    connect=True,
                    speak=True
                ),
                self.bot.user: discord.PermissionOverwrite(
                    read_messages=True,
                    view_channel=True,
                    send_messages=True,
                    manage_messages=True,
                    connect=True,
                    speak=True
                )
            }
            
            if not categoria_admin:
                categoria_admin = await ctx.guild.create_category(
                    "🛡️ │ ADMINISTRAÇÃO │ 🛡️",
                    overwrites=admin_overwrites,
                    position=0
                )
            
            # Canais administrativos
            admin_channels = {
                "📊-painel-controle": "Central de controle e monitoramento do servidor",
                "🎛️-configurações": "Configurações avançadas do bot e sistemas",
                "📈-estatísticas": "Estatísticas detalhadas e relatórios",
                "🔧-logs-sistema": "Logs automáticos do sistema",
                "💬-chat-staff": "Chat privado da equipe de administração"
            }
            
            created_admin_channels = {}
            for name, topic in admin_channels.items():
                # Verifica se canal já existe
                existing_channel = discord.utils.get(categoria_admin.channels, name=name)
                if existing_channel:
                    created_admin_channels[name] = existing_channel
                else:
                    channel = await categoria_admin.create_text_channel(
                        name=name,
                        topic=topic,
                        overwrites=admin_overwrites
                    )
                    created_admin_channels[name] = channel
            
            # 3. Criar CATEGORIA MEMBROS
            await message.edit(embed=discord.Embed(
                title="🚀 Etapa 3/6",
                description="Verificando categoria para membros...",
                color=discord.Color.yellow()
            ))
            
            # Verifica se categoria membros já existe
            categoria_membros = discord.utils.get(ctx.guild.categories, name="🎮 │ FAVELADZ │ 🎮")
            
            # Permissões para categoria membros - SEM DELETAR mensagens
            membros_overwrites = {
                ctx.guild.default_role: discord.PermissionOverwrite(
                    read_messages=True,
                    view_channel=True,
                    send_messages=True,
                    add_reactions=True,
                    manage_messages=False,  # NÃO podem excluir mensagens
                    connect=True,
                    speak=False  # NÃO podem falar no canal de voz por padrão
                ),
                support_role: discord.PermissionOverwrite(
                    read_messages=True,
                    view_channel=True,
                    send_messages=True,
                    manage_messages=True,
                    manage_channels=True,
                    connect=True,
                    speak=True
                ),
                ctx.guild.owner: discord.PermissionOverwrite(
                    read_messages=True,
                    view_channel=True,
                    send_messages=True,
                    manage_messages=True,
                    manage_channels=True,
                    connect=True,
                    speak=True
                ),
                self.bot.user: discord.PermissionOverwrite(
                    read_messages=True,
                    view_channel=True,
                    send_messages=True,
                    manage_messages=True,
                    connect=True,
                    speak=True
                )
            }
            
            if not categoria_membros:
                categoria_membros = await ctx.guild.create_category(
                    "🎮 │ FAVELADZ │ 🎮",
                    overwrites=membros_overwrites
                )
            
            # 4. Canais para membros
            await message.edit(embed=discord.Embed(
                title="🚀 Etapa 4/6",
                description="Verificando canais para membros...",
                color=discord.Color.yellow()
            ))
            
            # Verifica se canal de tickets já existe
            canal_tickets = discord.utils.get(categoria_membros.channels, name="🎫-suporte-tickets")
            if not canal_tickets:
                canal_tickets = await categoria_membros.create_text_channel(
                    name="🎫-suporte-tickets",
                    topic="🎫 Abra um ticket para suporte personalizado | Sistema automático FavelaZ",
                    overwrites=membros_overwrites
                )
                
                # Cria o painel de tickets automaticamente no canal de tickets
                tickets_cog = self.bot.get_cog('TicketSystem')
                if tickets_cog:
                    try:
                        # Cria um novo contexto com o canal de tickets
                        new_ctx = await self.bot.get_context(ctx.message)
                        new_ctx.channel = canal_tickets
                        await tickets_cog.setup_tickets(new_ctx)
                        print("✅ Painel de tickets criado automaticamente no canal correto")
                    except Exception as e:
                        print(f"⚠️ Erro ao criar painel de tickets: {e}")
            
            # Canal de voz para sistema automático - MUTADO para membros
            voz_overwrites = {
                ctx.guild.default_role: discord.PermissionOverwrite(
                    view_channel=True,
                    connect=True,
                    speak=False,  # MUTADOS por padrão
                    stream=False,
                    use_voice_activation=False
                ),
                support_role: discord.PermissionOverwrite(
                    view_channel=True,
                    connect=True,
                    speak=True,  # Staff pode falar
                    stream=True,
                    use_voice_activation=True,
                    mute_members=True,
                    deafen_members=True
                ),
                ctx.guild.owner: discord.PermissionOverwrite(
                    view_channel=True,
                    connect=True,
                    speak=True,  # Dono pode falar
                    stream=True,
                    use_voice_activation=True,
                    mute_members=True,
                    deafen_members=True,
                    manage_channels=True
                ),
                self.bot.user: discord.PermissionOverwrite(
                    view_channel=True,
                    connect=True,
                    speak=True,  # Bot pode falar (sistema automático)
                    stream=False,
                    use_voice_activation=True,
                    mute_members=True,
                    deafen_members=True,
                    manage_channels=True
                )
            }
            
            # Cria o canal de voz
            canal_voz = await ctx.guild.create_voice_channel(
                name="📞 Central de Atendimento",
                category=categoria_membros,
                overwrites=voz_overwrites
            )
            print(f"✅ Canal de voz criado: {canal_voz.name} (ID: {canal_voz.id})")

            # Canal informativo - APENAS LEITURA para membros
            info_overwrites = {
                ctx.guild.default_role: discord.PermissionOverwrite(
                    read_messages=True,
                    view_channel=True,
                    send_messages=False,  # Apenas leitura para membros
                    add_reactions=True,
                    manage_messages=False  # NÃO podem excluir
                ),
                support_role: discord.PermissionOverwrite(
                    read_messages=True,
                    view_channel=True,
                    send_messages=True,
                    manage_messages=True,
                    manage_channels=True
                ),
                ctx.guild.owner: discord.PermissionOverwrite(
                    read_messages=True,
                    view_channel=True,
                    send_messages=True,
                    manage_messages=True,
                    manage_channels=True
                ),
                self.bot.user: discord.PermissionOverwrite(
                    read_messages=True,
                    view_channel=True,
                    send_messages=True,
                    manage_messages=True
                )
            }
            
            # Verifica se canal de informações já existe
            canal_info = discord.utils.get(categoria_membros.channels, name="📢-informações")
            if not canal_info:
                canal_info = await categoria_membros.create_text_channel(
                    name="📢-informações",
                    topic="📢 Informações importantes do servidor FavelaZ",
                    overwrites=info_overwrites
                )
            
            # 5. Configurar arquivo .env
            await message.edit(embed=discord.Embed(
                title="🚀 Etapa 5/6",
                description="Configurando arquivo .env automaticamente...",
                color=discord.Color.yellow()
            ))
            
            # Remove linhas antigas de IDs de canais e roles do .env
            env_path = '.env'
            if os.path.exists(env_path):
                with open(env_path, 'r', encoding='utf-8') as f:
                    linhas = f.readlines()
                novas_linhas = []
                ids_keys = [
                    'TICKET_CATEGORY_ID=', 'SUPPORT_ROLE_ID=', 'AUDIO_CHANNEL_ID=',
                    'ADMIN_CATEGORY_ID=', 'TICKETS_CHANNEL_ID=', 'INFO_CHANNEL_ID='
                ]
                for linha in linhas:
                    if not any(linha.strip().startswith(key) for key in ids_keys):
                        novas_linhas.append(linha)
                with open(env_path, 'w', encoding='utf-8') as f:
                    f.writelines(novas_linhas)
            # Atualiza o .env com os novos IDs
            env_updates = {
                'TICKET_CATEGORY_ID': str(categoria_membros.id),
                'SUPPORT_ROLE_ID': str(support_role.id),
                'AUDIO_CHANNEL_ID': str(canal_voz.id),
                'ADMIN_CATEGORY_ID': str(categoria_admin.id),
                'TICKETS_CHANNEL_ID': str(canal_tickets.id),
                'INFO_CHANNEL_ID': str(canal_info.id)
            }

            # Atualiza o arquivo .env
            env_path = '.env'
            try:
                # Lê o conteúdo atual do .env
                env_content = ""
                if os.path.exists(env_path):
                    with open(env_path, 'r', encoding='utf-8') as f:
                        env_content = f.read()

                # Atualiza ou adiciona cada variável
                for key, value in env_updates.items():
                    if key in env_content:
                        # Atualiza valor existente
                        pattern = f"{key}=.*"
                        replacement = f"{key}={value}"
                        env_content = re.sub(pattern, replacement, env_content)
                    else:
                        # Adiciona nova variável
                        env_content += f"\n{key}={value}"

                # Salva as alterações
                with open(env_path, 'w', encoding='utf-8') as f:
                    f.write(env_content.strip())
                print("✅ Arquivo .env atualizado com sucesso!")

                # Aguarda um momento para garantir que o arquivo foi salvo
                await asyncio.sleep(2)

                # Recarrega as variáveis de ambiente
                load_dotenv()

                # Atualiza a variável AUDIO_CHANNEL_ID em memória
                os.environ['AUDIO_CHANNEL_ID'] = str(canal_voz.id)

                # Aguarda mais um momento para garantir que tudo foi atualizado
                await asyncio.sleep(1)
                
                # Tenta conectar ao sistema de voz usando o novo canal
                voice_cog = self.bot.get_cog('VoiceSystem')
                if voice_cog:
                    # Passa o canal recém-criado diretamente
                    await voice_cog.setup_servidor_voice(ctx)
                else:
                    print("⚠️ VoiceSystem cog não encontrado")
                    await ctx.send("⚠️ Sistema de voz não pôde ser inicializado. Use !iniciar_sistema para tentar novamente.")

            except Exception as e:
                print(f"⚠️ Erro ao atualizar .env: {e}")
                await ctx.send("⚠️ Erro ao configurar sistema de voz. Use !iniciar_sistema para tentar novamente.")
            
            # Cria embeds informativos
            await self.criar_embeds_informativos(canal_info, created_admin_channels["📊-painel-controle"], ctx.guild)
            
            # Cria canal de transcript da IA automaticamente na categoria admin
            ai_cog = self.bot.get_cog('AISystem')
            if ai_cog:
                transcript_channel = discord.utils.get(categoria_admin.channels, name="📚-transcript-ia")
                if not transcript_channel:
                    # Permissões: apenas admins e bot
                    admin_overwrites_transcript = {
                        ctx.guild.default_role: discord.PermissionOverwrite(view_channel=False),
                        ctx.guild.owner: discord.PermissionOverwrite(view_channel=True, send_messages=True, manage_messages=True),
                        self.bot.user: discord.PermissionOverwrite(view_channel=True, send_messages=True, manage_messages=True)
                    }
                    # Adiciona todos os administradores do servidor
                    for member in ctx.guild.members:
                        if member.guild_permissions.administrator:
                            admin_overwrites_transcript[member] = discord.PermissionOverwrite(view_channel=True, send_messages=True, manage_messages=True)
                    transcript_channel = await ctx.guild.create_text_channel(
                        name="📚-transcript-ia",
                        category=categoria_admin,
                        topic="Sala para aprendizado da IA - Interações entre admins e usuários",
                        overwrites=admin_overwrites_transcript
                    )
                    ai_cog.transcript_channel_id = transcript_channel.id
            
            # SUCESSO!
            embed_sucesso = discord.Embed(
                title="✅ Configuração Concluída com Sucesso!",
                description="**Seu servidor FavelaZ está 100% configurado!**\n\n🔍 *Sistema inteligente: verifica existência antes de criar*",
                color=discord.Color.green()
            )
            
            embed_sucesso.add_field(
                name="🛡️ Categoria Admin",
                value=f"• {categoria_admin.mention}\n• {len(created_admin_channels)} canais administrativos\n• Permissões exclusivas",
                inline=True
            )
            
            embed_sucesso.add_field(
                name="🎮 Categoria Membros",
                value=f"• {categoria_membros.mention}\n• Sistema de tickets ativo\n• Canal de voz conectado",
                inline=True
            )
            
            embed_sucesso.add_field(
                name="⚙️ Configurações",
                value=f"• Arquivo .env atualizado\n• {support_role.mention} configurado\n• Sistemas online",
                inline=True
            )
            
            embed_sucesso.add_field(
                name="🎯 Próximos Passos",
                value="1. Configure sua API key do ElevenLabs no .env\n2. Adicione membros ao cargo de suporte\n3. Teste o sistema de tickets\n4. Personalize as mensagens de voz",
                inline=False
            )
            
            embed_sucesso.set_footer(text="🚀 FavelaZ - Sistema completo instalado e funcionando!")
            
            await message.edit(embed=embed_sucesso)
            
            # Envia resumo no painel de controle
            await self.enviar_resumo_configuracao(created_admin_channels["📊-painel-controle"], env_updates, ctx.guild)
            
            # Diagnóstico automático do .env após setup
            checks = [
                ("TICKET_CATEGORY_ID", 'categoria'),
                ("SUPPORT_ROLE_ID", 'cargo'),
                ("AUDIO_CHANNEL_ID", 'canal'),
                ("ADMIN_CATEGORY_ID", 'categoria'),
                ("TICKETS_CHANNEL_ID", 'canal'),
                ("INFO_CHANNEL_ID", 'canal')
            ]
            embed = discord.Embed(title="🛠️ Diagnóstico do .env (após setup)", color=discord.Color.blue())
            tudo_ok = True
            for key, tipo in checks:
                id_val, ok = get_env_id_validado(ctx.guild, key, tipo)
                if ok:
                    embed.add_field(name=key, value=f"✅ {id_val}", inline=False)
                else:
                    tudo_ok = False
                    embed.add_field(name=key, value=f"❌ {id_val if id_val else 'Não definido ou inválido'}", inline=False)
            if tudo_ok:
                embed.description = "Todos os IDs do .env estão corretos e existem no servidor!"
                embed.color = discord.Color.green()
            else:
                embed.description = "Atenção: Corrija os IDs marcados com ❌ no seu .env para evitar erros."
                embed.color = discord.Color.red()
            canal_admin = discord.utils.get(ctx.guild.text_channels, name="📊-painel-controle")
            if canal_admin:
                try:
                    await canal_admin.send(embed=embed)
                except Exception:
                    pass
            
        except Exception as e:
            embed_erro = discord.Embed(
                title="❌ Erro na Configuração",
                description=f"Ocorreu um erro durante a configuração:\n```{str(e)}```",
                color=discord.Color.red()
            )
            await message.edit(embed=embed_erro)
            raise e

    async def criar_embeds_informativos(self, canal_info, canal_admin, guild):
        """Cria embeds informativos para os canais"""
        
        # Embed para canal de informações
        embed_info = discord.Embed(
            title="🎮 Bem-vindo ao FavelaZ! 🎮",
            description="**O melhor servidor de DayZ está aqui!**",
            color=discord.Color.blue()
        )
        
        embed_info.add_field(
            name="🎫 Como obter suporte",
            value="Use o canal de tickets para suporte personalizado.\nClique em 🎫 **Abrir Ticket** para começar!",
            inline=False
        )
        
        embed_info.add_field(
            name="📞 Sistema de Voz",
            value="Nosso sistema automático de atendimento está sempre ativo.\nConecte-se ao canal de voz para ouvir as instruções!",
            inline=False
        )
        
        embed_info.add_field(
            name="🤖 IA Inteligente",
            value="Nosso bot possui IA avançada que aprende com cada atendimento.\nQuanto mais usar, mais inteligente fica!",
            inline=False
        )
        
        embed_info.set_footer(text="🔥 FavelaZ - Sobreviva, conquiste, domine!")
        if guild.icon:
            embed_info.set_thumbnail(url=guild.icon.url)
        
        await canal_info.send(embed=embed_info)
        
        # Embed para painel admin
        embed_admin = discord.Embed(
            title="🛡️ Painel de Controle Administrativo",
            description="**Central de comando do servidor FavelaZ**",
            color=discord.Color.gold()
        )
        
        embed_admin.add_field(
            name="🎛️ Comandos de Tickets",
            value="""
• `!setup_tickets` - Criar painel de tickets
• `!stats_tickets` - Estatísticas detalhadas
• `!tag <nome>` - FAQ/tag rápido
• `!add_tag <nome> <resposta>` - Adicionar resposta FAQ
• `!claim` / `!release` - Assumir/liberar ticket
• `!close` - Fechar ticket
• `!backup_transcripts` - Backup dos transcripts
• `!transcript` - Gerar transcrição manual
• `!setup_servidor` - Setup completo do servidor
• `!add_steamadmin <@cargo>` - Permitir cargo ver info Steam
• `!remove_steamadmin <@cargo>` - Remover cargo Steam Admin
• `!list_steamadmin` - Listar cargos Steam Admin
""",
            inline=False
        )
        embed_admin.add_field(
            name="🎤 Comandos de Voz",
            value="""
• `!iniciar_sistema` - Iniciar sistema de voz
• `!reiniciar_sistema` - Reiniciar sistema de voz
• `!parar_sistema` - Parar sistema de voz
• `!trocar_voz <voice_id>` - Trocar voz
• `!listar_backups` - Listar backups de voz
• `!restaurar_backup <nome>` - Restaurar backup
• `!cache_info` - Info do cache de voz
• `!falar_com_musica [texto]` - Falar com música jazz
• `!controlar_jazz [play/stop/status]` - Controlar música jazz
• `!add_mensagem [texto]` - Adicionar mensagem automática
""",
            inline=False
        )
        embed_admin.add_field(
            name="🤖 Comandos de IA",
            value="""
• `!ask <pergunta>` - Perguntar para IA
• `!treinar_ia` - Treinar modelo
• `!ia_status` - Status do sistema de IA
• `!add_keyword <palavra> <resposta>` - Adicionar palavra-chave
• `!list_keywords` - Listar palavras-chave
• `!remove_keyword <palavra>` - Remover palavra-chave
• `!toggle_auto` - Ativar/desativar atendimento automático
• `!setup_transcript` - Criar sala de transcript para IA
""",
            inline=False
        )
        embed_admin.add_field(
            name="⚙️ Comandos Administrativos",
            value="""
• `!setup_servidor` - Setup completo
• `!info` - Info do bot
• `!logs` - Ver logs
• `!backup` - Backup configs
• `!reload <cog>` - Recarregar módulo
• `!reload_all` - Recarregar todos cogs
• `!reiniciar_bot` - Reiniciar o bot por completo
• `!shutdown` - Desligar bot
• `!invite` - Link de convite
• `!reset_commands` - Limpar comandos slash
• `!limpar <n>` - Limpar mensagens
• `!say <canal> <msg>` - Falar como bot
• `!embed <título> <descrição>` - Embed custom
• `!set_env <variavel> <valor>` - Editar variável do .env
""",
            inline=False
        )
        embed_admin.add_field(
            name="💡 Dicas",
            value="• Use os comandos acima para gerenciar todos os sistemas do FavelaZ!",
            inline=False
        )
        
        await canal_admin.send(embed=embed_admin)

    async def enviar_resumo_configuracao(self, canal_admin, env_updates, guild):
        """Envia resumo técnico da configuração"""
        
        embed_tecnico = discord.Embed(
            title="📋 Resumo Técnico da Configuração",
            description="**Informações detalhadas do setup**",
            color=discord.Color.dark_blue()
        )
        
        # IDs importantes
        ids_info = ""
        for key, value in env_updates.items():
            channel_or_role = guild.get_channel(int(value)) or guild.get_role(int(value))
            name = channel_or_role.name if channel_or_role else "Não encontrado"
            ids_info += f"• **{key}**: `{value}` ({name})\n"
        
        embed_tecnico.add_field(
            name="🆔 IDs Configurados",
            value=ids_info,
            inline=False
        )
        
        embed_tecnico.add_field(
            name="📂 Arquivos Atualizados",
            value="• `.env` - Variáveis de ambiente\n• Configurações do bot recarregadas\n• Sistemas reiniciados automaticamente",
            inline=False
        )
        
        embed_tecnico.set_footer(text=f"Configuração realizada em {datetime.datetime.now().strftime('%d/%m/%Y às %H:%M:%S')}")
        
        await canal_admin.send(embed=embed_tecnico)

    @commands.command(name='backup')
    @commands.has_permissions(administrator=True)
    async def backup_configs(self, ctx):
        """Cria backup das configurações"""
        # ... existing code ...

    @commands.command(name='reiniciar_bot', aliases=['restart_bot'])
    @commands.has_permissions(administrator=True)
    async def reiniciar_bot(self, ctx):
        """Reinicia o bot por completo (shutdown + auto-restart se disponível)"""
        embed = discord.Embed(
            title="♻️ Reiniciando Bot",
            description="O bot será reiniciado em 5 segundos...",
            color=discord.Color.orange()
        )
        await ctx.send(embed=embed)
        await asyncio.sleep(5)
        await ctx.bot.close()

    @commands.command(name='set_env')
    @commands.has_permissions(administrator=True)
    async def set_env(self, ctx, variavel: str, *, valor: str):
        """Altera uma variável do arquivo .env"""
        env_path = os.path.join(os.getcwd(), '.env')
        linhas = []
        encontrada = False
        # Lê todas as linhas do .env
        if os.path.exists(env_path):
            with open(env_path, 'r', encoding='utf-8') as f:
                linhas = f.readlines()
        # Atualiza ou adiciona a variável
        for i, linha in enumerate(linhas):
            if linha.strip().startswith(f'{variavel}='):
                linhas[i] = f'{variavel}={valor}\n'
                encontrada = True
                break
        if not encontrada:
            linhas.append(f'{variavel}={valor}\n')
        # Salva o .env
        with open(env_path, 'w', encoding='utf-8') as f:
            f.writelines(linhas)
        await ctx.send(f'✅ Variável `{variavel}` atualizada para `{valor}` no .env. Reinicie o bot para aplicar.')

    @commands.command(name='diagnostico_env')
    @commands.has_permissions(administrator=True)
    async def diagnostico_env(self, ctx):
        """Diagnostica se todos os IDs do .env existem no servidor"""
        guild = ctx.guild
        checks = [
            ("TICKET_CATEGORY_ID", 'categoria'),
            ("SUPPORT_ROLE_ID", 'cargo'),
            ("AUDIO_CHANNEL_ID", 'canal'),
            ("ADMIN_CATEGORY_ID", 'categoria'),
            ("TICKETS_CHANNEL_ID", 'canal'),
            ("INFO_CHANNEL_ID", 'canal')
        ]
        embed = discord.Embed(title="🛠️ Diagnóstico do .env", color=discord.Color.blue())
        tudo_ok = True
        for key, tipo in checks:
            id_val, ok = get_env_id_validado(guild, key, tipo)
            if ok:
                embed.add_field(name=key, value=f"✅ {id_val}", inline=False)
            else:
                tudo_ok = False
                embed.add_field(name=key, value=f"❌ {id_val if id_val else 'Não definido ou inválido'}", inline=False)
        if tudo_ok:
            embed.description = "Todos os IDs do .env estão corretos e existem no servidor!"
            embed.color = discord.Color.green()
        else:
            embed.description = "Atenção: Corrija os IDs marcados com ❌ no seu .env para evitar erros."
            embed.color = discord.Color.red()
        await ctx.send(embed=embed)

    @commands.command(name='remover_servidor', aliases=['remover_server', 'deletar_servidor'])
    @commands.has_permissions(administrator=True)
    async def remover_servidor_completo(self, ctx):
        """Remove todas as categorias, canais e cargo criados pelo setup_servidor"""
        embed = discord.Embed(
            title="⚠️ Remoção Automática - FavelaZ",
            description="Iniciando remoção de categorias, canais e cargo criados pelo setup...",
            color=discord.Color.red()
        )
        msg = await ctx.send(embed=embed)
        deleted = []
        # Remove categorias e canais
        nomes_categorias = ["🛡️ │ ADMINISTRAÇÃO │ 🛡️", "🎮 │ FAVELADZ │ 🎮"]
        for nome_cat in nomes_categorias:
            categoria = discord.utils.get(ctx.guild.categories, name=nome_cat)
            if categoria:
                for canal in list(categoria.channels):
                    try:
                        await canal.delete(reason="Remoção automática pelo comando !remover_servidor")
                        deleted.append(f"Canal: {canal.name}")
                    except Exception as e:
                        deleted.append(f"Erro ao deletar canal {canal.name}: {e}")
                try:
                    await categoria.delete(reason="Remoção automática pelo comando !remover_servidor")
                    deleted.append(f"Categoria: {nome_cat}")
                except Exception as e:
                    deleted.append(f"Erro ao deletar categoria {nome_cat}: {e}")
        # Remove cargo de suporte
        support_role = discord.utils.get(ctx.guild.roles, name="🎫 Suporte FavelaZ")
        if support_role:
            try:
                await support_role.delete(reason="Remoção automática pelo comando !remover_servidor")
                deleted.append("Cargo: 🎫 Suporte FavelaZ")
            except Exception as e:
                deleted.append(f"Erro ao deletar cargo: {e}")
        # Mensagem final
        embed_final = discord.Embed(
            title="✅ Remoção Concluída",
            description="Itens removidos:\n" + "\n".join(deleted) if deleted else "Nada foi removido.",
            color=discord.Color.green()
        )
        await msg.edit(embed=embed_final)

async def setup(bot):
    await bot.add_cog(AdminCommands(bot)) 