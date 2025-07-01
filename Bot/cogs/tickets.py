import discord
from discord.ext import commands
import json
import datetime
import os
import asyncio
from typing import Optional, cast, Dict
import aiohttp
import tempfile
import base64
import shutil
import re
import ftplib

class TicketSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.tickets = {}
        self.stats = {'abertos': 0, 'fechados': 0}
        self.load_tickets()
        self.load_stats()
        self.ticket_lock = asyncio.Lock()
        self.INFO_CHANNEL_NAME = "📢-informações"
        
        # Nomes das categorias
        self.CATEGORIES = {
            "SUPORTE": "...... [ SUPORTE ] ......",
            "DOACAO": "...... [ DOAÇÕES ] ......",
            "RAID": "...... [ RAIDS ] ......",
            "DENUNCIA": "...... [ DENÚNCIAS ] ......"
        }
        
        self.SUPPORT_ROLE_NAME = "🎫 Suporte FavelaZ"
        self.TICKETS_CHANNEL_NAME = "🎫-suporte-tickets"

    def load_tickets(self):
        """Carrega os tickets do arquivo JSON"""
        try:
            with open('data/tickets.json', 'r', encoding='utf-8') as f:
                self.tickets = json.load(f)
        except FileNotFoundError:
            self.tickets = {}
            self.save_tickets()

    def load_stats(self):
        """Carrega as estatísticas do arquivo JSON"""
        try:
            with open('data/ticket_stats.json', 'r', encoding='utf-8') as f:
                self.stats = json.load(f)
        except FileNotFoundError:
            self.stats = {'abertos': 0, 'fechados': 0}
            with open('data/ticket_stats.json', 'w', encoding='utf-8') as f:
                json.dump(self.stats, f, indent=4)

    def save_tickets(self):
        """Salva os tickets no arquivo JSON"""
        os.makedirs('data', exist_ok=True)
        with open('data/tickets.json', 'w', encoding='utf-8') as f:
            json.dump(self.tickets, f, indent=4)

    async def get_user_open_ticket(self, guild, user_id):
        """Verifica se o usuário já tem um ticket aberto"""
        for channel_id, ticket_data in self.tickets.items():
            if ticket_data.get('user') == user_id and not ticket_data.get('closed', False):
                channel = guild.get_channel(int(channel_id))
                if channel:
                    return channel
        return None

    async def get_channel_by_name(self, guild: discord.Guild, name: str, channel_type: type) -> Optional[discord.abc.GuildChannel]:
        """Encontra um canal pelo nome"""
        for channel in guild.channels:
            if channel.name.lower() == name.lower() and isinstance(channel, channel_type):
                return channel
        return None

    async def verificar_canais(self, guild: discord.Guild) -> list:
        """Verifica se todos os canais necessários existem"""
        erros = []
        
        # Verifica canal de tickets
        tickets_channel = await self.get_channel_by_name(guild, self.TICKETS_CHANNEL_NAME, discord.TextChannel)
        if not tickets_channel:
            erros.append(f"❌ Canal '{self.TICKETS_CHANNEL_NAME}' não encontrado")
        
        # Verifica canal de informações
        info_channel = await self.get_channel_by_name(guild, self.INFO_CHANNEL_NAME, discord.TextChannel)
        if not info_channel:
            erros.append(f"❌ Canal '{self.INFO_CHANNEL_NAME}' não encontrado")
            
        return erros

    @commands.Cog.listener()
    async def on_ready(self):
        """Verifica os canais quando o bot iniciar"""
        print("\n🔍 Verificando configurações do sistema de tickets...")
        
        for guild in self.bot.guilds:
            erros = await self.verificar_canais(guild)
            if erros:
                print(f"\n⚠️ AVISOS para o servidor {guild.name}:")
                for erro in erros:
                    print(erro)
                print("\nℹ️ Certifique-se que todos os canais necessários existem no servidor!")
            else:
                print(f"\n✅ Todas as configurações estão corretas no servidor {guild.name}!")

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def setup_tickets(self, ctx):
        """Configura o sistema de tickets"""
        try:
            # Definição da classe TicketModal (mantendo o sistema de formulário já implementado)
            class TicketModal(discord.ui.Modal):
                def __init__(self, cog, category: str):
                    title = {
                        "DOACAO": "Formulário de Doação",
                        "RAID": "Formulário de Raid",
                        "DENUNCIA": "Formulário de Denúncia",
                        "SUPORTE": "Formulário de Suporte"
                    }.get(category, "Formulário de Ticket")
                    super().__init__(title=title)
                    self.cog = cog
                    self.category = category
                    if category == "DENUNCIA":
                        self.motivo = discord.ui.TextInput(
                            label="Descreva o motivo da sua denuncia:",
                            style=discord.TextStyle.paragraph,
                            required=True,
                            min_length=10,
                            max_length=1000
                        )
                        self.denunciado = discord.ui.TextInput(
                            label="Nome da pessoa que você quer denunciar:",
                            style=discord.TextStyle.short,
                            required=True,
                            min_length=3,
                            max_length=50
                        )
                        self.nome_ingame = discord.ui.TextInput(
                            label="Nos informe seu nome ingame:",
                            style=discord.TextStyle.short,
                            required=True,
                            min_length=3,
                            max_length=50
                        )
                        self.steam_id = discord.ui.TextInput(
                            label="Informe sua Steam ID",
                            style=discord.TextStyle.short,
                            required=True,
                            min_length=5,
                            max_length=50
                        )
                        self.data_hora = discord.ui.TextInput(
                            label="Informe a Data e Hora do ocorrido",
                            style=discord.TextStyle.short,
                            required=True,
                            placeholder="DD/MM HH:MM",
                            min_length=5,
                            max_length=50
                        )
                        self.add_item(self.motivo)
                        self.add_item(self.denunciado)
                        self.add_item(self.nome_ingame)
                        self.add_item(self.steam_id)
                        self.add_item(self.data_hora)
                    else:
                        self.problema = discord.ui.TextInput(
                            label="Por favor nos Informe qual o seu problema.",
                            style=discord.TextStyle.paragraph,
                            required=True,
                            min_length=10,
                            max_length=1000
                        )
                        self.nome_ingame = discord.ui.TextInput(
                            label="Nos informe seu nome ingame:",
                            style=discord.TextStyle.short,
                            required=True,
                            min_length=3,
                            max_length=50
                        )
                        self.steam_id = discord.ui.TextInput(
                            label="Informe sua Steam ID",
                            style=discord.TextStyle.short,
                            required=True,
                            min_length=5,
                            max_length=50
                        )
                        self.add_item(self.problema)
                        self.add_item(self.nome_ingame)
                        self.add_item(self.steam_id)

                async def on_submit(self, interaction: discord.Interaction):
                    # Validação do Steam ID
                    steam_id = self.steam_id.value.strip()
                    if not (steam_id.isdigit() and 15 <= len(steam_id) <= 20):
                        await interaction.response.send_message(
                            "❌ O campo Steam ID deve conter apenas números e ter entre 15 e 20 dígitos.",
                            ephemeral=True
                        )
                        return

                    # Verificação da Steam ID via Steam Web API
                    steam_api_key = "840BB63C5FC990DA332C1125247C2983"
                    steam_profile = None
                    async with aiohttp.ClientSession() as session:
                        url = f"https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v2/?key={steam_api_key}&steamids={steam_id}"
                        async with session.get(url) as resp:
                            if resp.status == 200:
                                data = await resp.json()
                                players = data.get("response", {}).get("players", [])
                                if players:
                                    steam_profile = players[0]

                    try:
                        if not interaction.guild:
                            await interaction.response.send_message("❌ Este comando só pode ser usado em servidores!", ephemeral=True)
                            return

                        async with self.cog.ticket_lock:
                            # Verifica se já tem ticket aberto
                            existing_ticket = await self.cog.get_user_open_ticket(interaction.guild, interaction.user.id)
                            if existing_ticket:
                                await interaction.response.send_message(
                                    f"❌ Você já tem um ticket aberto em {existing_ticket.mention}!\n"
                                    "Por favor, utilize o ticket existente ou aguarde ele ser fechado.",
                                    ephemeral=True
                                )
                                return

                            # Configuração de permissões
                            overwrites = {
                                interaction.guild.default_role: discord.PermissionOverwrite(read_messages=False),
                                interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
                                interaction.guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
                            }

                            # Adiciona permissão para o cargo de suporte
                            support_role = discord.utils.get(interaction.guild.roles, name=self.cog.SUPPORT_ROLE_NAME)
                            if support_role:
                                overwrites[support_role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)

                            # Obtém ou cria a categoria
                            category_channel = await self.cog.get_or_create_category(
                                interaction.guild,
                                self.cog.CATEGORIES[self.category]
                            )
                            
                            if not category_channel:
                                await interaction.response.send_message("❌ Erro ao criar categoria!", ephemeral=True)
                                return

                            # Garante que as estatísticas existam
                            if 'total' not in self.cog.stats:
                                self.cog.stats['total'] = 0
                            if 'abertos' not in self.cog.stats:
                                self.cog.stats['abertos'] = 0
                            if 'fechados' not in self.cog.stats:
                                self.cog.stats['fechados'] = 0

                            # Cria o canal
                            next_number = self.cog.stats['total'] + 1
                            channel_name = f"{self.category.lower()}-{next_number}"
                            
                            channel = await interaction.guild.create_text_channel(
                                name=channel_name,
                                category=category_channel,
                                overwrites=overwrites,
                                topic=f"Ticket de {interaction.user.name}"
                            )

                            # Registra o ticket
                            ticket_data = {
                                'user': interaction.user.id,
                                'category': self.category,
                                'created_at': str(datetime.datetime.now()),
                                'closed': False,
                                'nome_ingame': self.nome_ingame.value,
                                'steam_id': self.steam_id.value
                            }

                            if self.category == "DENUNCIA":
                                ticket_data.update({
                                    'motivo': self.motivo.value,
                                    'denunciado': self.denunciado.value,
                                    'data_hora': self.data_hora.value
                                })
                            else:
                                ticket_data['problema'] = self.problema.value

                            self.cog.tickets[str(channel.id)] = ticket_data

                            # Atualiza estatísticas
                            self.cog.stats['total'] = next_number
                            self.cog.stats['abertos'] += 1

                            # Salva os dados
                            self.cog.save_tickets()
                            with open('data/ticket_stats.json', 'w', encoding='utf-8') as f:
                                json.dump(self.cog.stats, f, indent=4)

                            # Cria a mensagem inicial
                            await self.cog.create_initial_ticket_message(channel, interaction.user, ticket_data, steam_profile)
                            
                            await interaction.response.send_message(f"✅ Seu ticket foi criado em {channel.mention}", ephemeral=True)

                    except Exception as e:
                        print(f"Erro ao criar ticket: {e}")
                        await interaction.response.send_message("❌ Ocorreu um erro ao criar o ticket.", ephemeral=True)

            # Painel igual à imagem fornecida
            guild_name = ctx.guild.name.upper()
            embed = discord.Embed(
                title=f"SUPORTE - {guild_name}",
                description=(
                    "📢 **Precisa de ajuda? Abra um ticket!**\n"
                    "Selecione a categoria correta e nossa equipe irá te atender.\n\n"
                    "<:categoria:> **Categorias:**\n"
                    "<:doacao:> - Doação\n"
                    "<:raid:> - Raid\n"
                    "<:denuncia:> - Denúncia\n"
                    "<:suporte:> - Suporte\n\n"
                    "<:importante:> **Importante:** Ao abrir o ticket, informe sua **Steam ID e Nome in-game** na descrição para agilizar o atendimento!\n"
                    "<:atencao:> Clique no botão abaixo e aguarde o atendimento!"
                ),
                color=0x2F3136
            )
            embed.set_image(url="https://media.discordapp.net/attachments/1294802305086128128/1364769929391243345/suporte_final.png")
            current_date = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
            embed.set_footer(text=f"favelazoficial.com.br • {current_date}")

            # Select menu igual ao da imagem
            options = [
                discord.SelectOption(label="Doação", emoji="💎", value="DOACAO"),
                discord.SelectOption(label="Raid", emoji="🛡️", value="RAID"),
                discord.SelectOption(label="Denúncia", emoji="❌", value="DENUNCIA"),
                discord.SelectOption(label="Suporte", emoji="🛠️", value="SUPORTE")
            ]
            class TicketDropdown(discord.ui.Select):
                def __init__(self, cog: 'TicketSystem'):
                    super().__init__(
                        placeholder="Faça uma seleção",
                        min_values=1,
                        max_values=1,
                        options=options,
                        custom_id="ticket_select"
                    )
                    self.cog = cog
                async def callback(self, interaction: discord.Interaction):
                    modal = TicketModal(self.cog, self.values[0])
                    await interaction.response.send_modal(modal)
            class TicketView(discord.ui.View):
                def __init__(self, cog: 'TicketSystem'):
                    super().__init__(timeout=None)
                    self.add_item(TicketDropdown(cog))
            await ctx.send(embed=embed, view=TicketView(self))
            
        except Exception as e:
            print(f"Erro ao criar painel: {e}")
            await ctx.send("❌ Erro ao criar o painel de tickets!")

    async def get_or_create_category(self, guild, category_name):
        """Obtém ou cria uma categoria para os tickets"""
        # Procura a categoria existente
        for category in guild.categories:
            if category.name == category_name:
                return category

        # Cria uma nova categoria
        try:
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(read_messages=False),
                guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
            }

            # Adiciona permissão para o cargo de suporte
            support_role = discord.utils.get(guild.roles, name=self.SUPPORT_ROLE_NAME)
            if support_role:
                overwrites[support_role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)

            return await guild.create_category(
                name=category_name,
                overwrites=overwrites,
                reason="Categoria de tickets"
            )
        except Exception as e:
            print(f"Erro ao criar categoria: {e}")
            return None

    def get_steam_admin_roles(self):
        """Retorna a lista de IDs dos cargos que podem ver informações do Steam"""
        return [
            1133883847557505024,  # Admin
            1133883847557505025,  # Moderador
            1133883847557505026   # Staff
        ]

    def add_steam_admin_role(self, role_id):
        roles = self.get_steam_admin_roles()
        if role_id not in roles:
            roles.append(role_id)
            with open('data/steam_admin_roles.json', 'w', encoding='utf-8') as f:
                json.dump(roles, f)

    @commands.command(name='add_steamadmin')
    @commands.has_permissions(administrator=True)
    async def add_steamadmin(self, ctx, role: discord.Role):
        """Adiciona um cargo que pode ver informações da Steam ID nos tickets"""
        self.add_steam_admin_role(role.id)
        await ctx.send(f'✅ O cargo {role.mention} agora pode ver informações detalhadas da Steam ID nos tickets.')

    @commands.command(name='remove_steamadmin')
    @commands.has_permissions(administrator=True)
    async def remove_steamadmin(self, ctx, role: discord.Role):
        """Remove um cargo da lista de cargos que podem ver informações da Steam ID nos tickets"""
        roles = self.get_steam_admin_roles()
        if role.id in roles:
            roles.remove(role.id)
            with open('data/steam_admin_roles.json', 'w', encoding='utf-8') as f:
                json.dump(roles, f)
            await ctx.send(f'✅ O cargo {role.mention} foi removido da lista de cargos Steam Admin.')
        else:
            await ctx.send(f'❌ O cargo {role.mention} não está na lista de cargos Steam Admin.')

    @commands.command(name='list_steamadmin')
    @commands.has_permissions(administrator=True)
    async def list_steamadmin(self, ctx):
        """Lista todos os cargos que podem ver informações da Steam ID nos tickets"""
        roles = self.get_steam_admin_roles()
        if not roles:
            await ctx.send('Nenhum cargo Steam Admin cadastrado.')
            return
        role_mentions = []
        for role_id in roles:
            role = ctx.guild.get_role(role_id)
            if role:
                role_mentions.append(role.mention)
            else:
                role_mentions.append(f'`{role_id}` (não encontrado)')
        await ctx.send('Cargos Steam Admin:\n' + '\n'.join(role_mentions))

    async def close_ticket(self, channel, closer):
        """Função central para fechar tickets"""
        try:
            print(f"[DEBUG] Iniciando fechamento do ticket {channel.name}")
            
            # Gera o transcript HTML
            transcript_path = await self.generate_transcript_html(channel)
            print(f"[DEBUG] Transcript gerado: {transcript_path}")

            if transcript_path:
                # Envia o transcript no canal
                try:
                    if transcript_path.startswith('http'):
                        embed = discord.Embed(
                            title="📄 Transcript do Ticket",
                            description=f"O transcript está disponível em:\n{transcript_path}",
                            color=discord.Color.blue()
                        )
                        await channel.send(embed=embed)
                    else:
                        with open(transcript_path, 'rb') as f:
                            file = discord.File(f, filename=os.path.basename(transcript_path))
                            await channel.send(file=file)
                    print(f"[DEBUG] Transcript enviado no canal")
                except Exception as e:
                    print(f"[ERRO] Falha ao enviar transcript: {e}")
                    import traceback
                    traceback.print_exc()

            # Envia mensagem de fechamento
            embed = discord.Embed(
                title="Ticket Fechado",
                description=f"Ticket fechado por {closer.mention}",
                color=discord.Color.red()
            )
            await channel.send(embed=embed)
            print(f"[DEBUG] Mensagem de fechamento enviada")
            
            # Aguarda 5 segundos
            await asyncio.sleep(5)
            
            # Deleta o canal
            await channel.delete(reason=f"Ticket fechado por {closer.name}")
            print(f"[DEBUG] Canal deletado")
            
        except Exception as e:
            print(f"[ERRO] Falha ao fechar ticket: {e}")
            import traceback
            traceback.print_exc()
            try:
                await channel.send("❌ Ocorreu um erro ao fechar o ticket.")
            except:
                pass

    @commands.command(name='close', aliases=['fechar'])
    async def close_ticket_command(self, ctx):
        """Fecha um ticket"""
        if not ctx.channel.name.startswith(('suporte-', 'doacao-')):
            await ctx.send("❌ Este comando só pode ser usado em canais de ticket.")
            return

        # Verifica se o usuário tem permissão
        steam_admin_roles = self.get_steam_admin_roles()
        if not any(role.id in steam_admin_roles for role in ctx.author.roles):
            await ctx.send("❌ Você não tem permissão para fechar tickets.")
            return

        await self.close_ticket(ctx.channel, ctx.author)

    @commands.command(name='fechar_ticket')
    async def fechar_ticket_command(self, ctx):
        """Alias para o comando de fechar ticket"""
        await self.close_ticket_command(ctx)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        """Fecha um ticket via reação"""
        # Ignora reações de bots
        if payload.member.bot:
            return

        channel = self.bot.get_channel(payload.channel_id)
        if not channel or not channel.name.startswith(('suporte-', 'doacao-')):
            return

        if str(payload.emoji) == '🔒':
            # Verifica se o usuário tem permissão
            steam_admin_roles = self.get_steam_admin_roles()
            if any(role.id in steam_admin_roles for role in payload.member.roles):
                await self.close_ticket(channel, payload.member)

    @commands.Cog.listener()
    async def on_button_click(self, interaction):
        """Fecha um ticket via botão"""
        if not interaction.channel.name.startswith(('suporte-', 'doacao-')):
            return

        if interaction.custom_id == 'close_ticket':
            # Verifica se o usuário tem permissão
            steam_admin_roles = self.get_steam_admin_roles()
            if any(role.id in steam_admin_roles for role in interaction.user.roles):
                await interaction.response.defer()
                await self.close_ticket(interaction.channel, interaction.user)
            else:
                await interaction.response.send_message("❌ Você não tem permissão para fechar tickets.", ephemeral=True)

    # Configurações FTP
    FTP_HOST = "ftp.bahamasrp.site"
    FTP_USER = "bobgodz@bahamasrp.site"
    FTP_PASS = "G@m3rB4h@m@s2024"
    FTP_DIR = "transcripts"
    URL_BASE = "https://bahamasrp.site/bobgodz/transcripts/"

    def upload_transcript_ftp(self, local_file):
        try:
            ftp = ftplib.FTP(self.FTP_HOST)
            ftp.login(self.FTP_USER, self.FTP_PASS)
            
            # Cria o diretório transcripts se não existir
            try:
                ftp.mkd(self.FTP_DIR)
            except:
                pass
            ftp.cwd(self.FTP_DIR)
            
            # Upload do arquivo de transcript
            with open(local_file, 'rb') as f:
                ftp.storbinary(f'STOR {os.path.basename(local_file)}', f)
            
            ftp.quit()
            return True
        except Exception as e:
            print(f"[ERRO] Falha no upload FTP: {str(e)}")
            return False

    async def gerar_e_enviar_transcript(self, channel, guild):
        try:
            transcript_file, transcript_data = await self.generate_transcript_html_summary(channel)
            transcript_channel = discord.utils.get(guild.text_channels, name="📚-transcript-ia")
            if not transcript_channel:
                print("[ERRO] Canal de transcript não encontrado!")
                return False
                
            embed = discord.Embed(color=discord.Color.dark_green())
            embed.set_author(name=transcript_data['ticket_owner'], icon_url=transcript_data['ticket_owner_avatar'])
            embed.add_field(name="Ticket Owner", value=transcript_data['ticket_owner_mention'], inline=True)
            embed.add_field(name="Ticket Name", value=channel.name, inline=True)
            embed.add_field(name="Total Messages", value=str(transcript_data['msg_count']), inline=True)
            embed.add_field(name="Attachments", value=f"Saved: {transcript_data['attachments_saved']} | Skipped: {transcript_data['attachments_skipped']}", inline=True)
            
            # Upload via FTP
            success = self.upload_transcript_ftp(transcript_file)
            if success:
                file_name = os.path.basename(transcript_file)
                public_url = f"{self.URL_BASE}{file_name}"
                
                class DirectLinkView(discord.ui.View):
                    def __init__(self):
                        super().__init__()
                        self.add_item(discord.ui.Button(label='Ver Transcript', url=public_url))
                
                await transcript_channel.send(embed=embed, view=DirectLinkView())
                return True
            else:
                # Fallback: enviar como arquivo se o FTP falhar
                file = discord.File(transcript_file)
                await transcript_channel.send(embed=embed, file=file)
                return True
                
        except Exception as e:
            print(f"[ERRO] Falha ao gerar/enviar transcript: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

    def format_discord_content(self, content, guild):
        if not content:
            return ""
            
        # Formata menções de usuários
        def replace_user_mention(match):
            user_id = match.group(1)
            user = guild.get_member(int(user_id))
            if user:
                return f'<span class="mention">@{user.display_name}</span>'
            return f'<span class="mention">@Unknown User</span>'
            
        # Formata menções de canais
        def replace_channel_mention(match):
            channel_id = match.group(1)
            channel = guild.get_channel(int(channel_id))
            if channel:
                return f'<span class="mention">#{channel.name}</span>'
            return f'<span class="mention">#deleted-channel</span>'
            
        # Formata menções de cargos
        def replace_role_mention(match):
            role_id = match.group(1)
            role = guild.get_role(int(role_id))
            if role:
                return f'<span class="mention">@{role.name}</span>'
            return f'<span class="mention">@deleted-role</span>'
            
        # Formata código inline
        def replace_inline_code(match):
            return f'<code class="inline">{match.group(1)}</code>'
            
        # Formata blocos de código
        def replace_code_block(match):
            lang = match.group(1) if match.group(1) else ""
            code = match.group(2)
            return f'<div class="code-block"><div class="code-header">{lang}</div><pre><code>{code}</code></pre></div>'

        # Formata negrito
        def replace_bold(match):
            return f'<strong>{match.group(1)}</strong>'

        # Formata itálico
        def replace_italic(match):
            return f'<em>{match.group(1)}</em>'

        # Formata links
        def replace_link(match):
            text = match.group(1)
            url = match.group(2)
            return f'<a href="{url}" target="_blank" class="link">{text}</a>'
            
        # Aplica as substituições
        content = re.sub(r'<@!?(\d+)>', replace_user_mention, content)
        content = re.sub(r'<#(\d+)>', replace_channel_mention, content)
        content = re.sub(r'<@&(\d+)>', replace_role_mention, content)
        content = re.sub(r'`([^`]+)`', replace_inline_code, content)
        content = re.sub(r'```(\w+)?\n?([\s\S]+?)```', replace_code_block, content)
        content = re.sub(r'\*\*([^\*]+)\*\*', replace_bold, content)
        content = re.sub(r'\*([^\*]+)\*', replace_italic, content)
        content = re.sub(r'\[([^\]]+)\]\(([^\)]+)\)', replace_link, content)
        
        return content

    async def generate_transcript_html(self, channel):
        """Gera o transcript do ticket em HTML"""
        try:
            print(f"[DEBUG] Iniciando geração do transcript HTML para o canal {channel.name}")
            
            # Coleta todas as mensagens
            messages = []
            async for message in channel.history(limit=None, oldest_first=True):
                messages.append({
                    'author': message.author.name,
                    'avatar_url': str(message.author.avatar.url) if message.author.avatar else None,
                    'content': message.content,
                    'timestamp': message.created_at.strftime('%d/%m/%Y %H:%M'),
                    'attachments': [attachment.url for attachment in message.attachments],
                    'embeds': [embed.to_dict() for embed in message.embeds]
                })
            
            print(f"[DEBUG] Coletadas {len(messages)} mensagens")

            # Gera o HTML
            css = """* { margin: 0; padding: 0; box-sizing: border-box; } 
            body { font-family: 'gg sans', sans-serif; background-color: #313338; color: #dcddde; line-height: 1.5; } 
            .container { max-width: 1200px; margin: 0 auto; padding: 20px; } 
            .header { background-color: #2b2d31; padding: 20px; border-radius: 8px; margin-bottom: 20px; display: flex; align-items: center; gap: 15px; } 
            .header img { width: 64px; height: 64px; border-radius: 50%; } 
            .header-info h1 { font-size: 24px; color: #ffffff; margin-bottom: 5px; } 
            .header-info p { font-size: 14px; color: #b5bac1; } 
            .messages { display: flex; flex-direction: column; gap: 20px; } 
            .message { display: flex; gap: 15px; padding: 10px; border-radius: 8px; transition: background-color 0.2s; } 
            .message:hover { background-color: #2e3035; } 
            .message-avatar { width: 40px; height: 40px; border-radius: 50%; } 
            .message-content { flex: 1; } 
            .message-header { display: flex; align-items: baseline; gap: 10px; margin-bottom: 5px; } 
            .message-author { font-weight: 500; color: #ffffff; } 
            .message-timestamp { font-size: 12px; color: #b5bac1; } 
            .message-text { color: #dcddde; white-space: pre-wrap; } 
            .message-attachments { display: flex; flex-wrap: wrap; gap: 10px; margin-top: 10px; } 
            .message-attachments img { max-width: 300px; max-height: 300px; border-radius: 4px; } 
            .message-embeds { margin-top: 10px; } 
            .embed { background-color: #2b2d31; border-left: 4px solid #5865f2; border-radius: 4px; padding: 10px; margin-top: 5px; } 
            .embed-title { font-weight: 600; color: #ffffff; margin-bottom: 5px; } 
            .embed-description { color: #dcddde; } 
            code { background-color: #2b2d31; padding: 2px 6px; border-radius: 4px; font-family: 'Consolas', monospace; } 
            pre { background-color: #2b2d31; padding: 10px; border-radius: 4px; overflow-x: auto; margin: 10px 0; } 
            a { color: #00a8fc; text-decoration: none; } 
            a:hover { text-decoration: underline; } 
            ::-webkit-scrollbar { width: 8px; height: 8px; } 
            ::-webkit-scrollbar-track { background: transparent; } 
            ::-webkit-scrollbar-thumb { background-color: #202225; border-radius: 4px; } 
            ::-webkit-scrollbar-thumb:hover { background-color: #2e3338; }"""

            html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Transcript do Ticket</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=gg+sans:wght@400;500;700&display=swap');
{css}
</style>
</head>
<body>
<div class="container">
<div class="header">
<img src="{str(channel.guild.icon.url) if channel.guild.icon else ''}" alt="Server Icon">
<div class="header-info">
<h1>{channel.name}</h1>
<p>Transcript gerado em {datetime.datetime.now().strftime('%d/%m/%Y %H:%M')}</p>
</div>
</div>
<div class="messages">"""

            # Adiciona as mensagens
            for msg in messages:
                html += f"""<div class="message">
<img class="message-avatar" src="{msg['avatar_url'] or ''}" alt="Avatar">
<div class="message-content">
<div class="message-header">
<span class="message-author">{msg['author']}</span>
<span class="message-timestamp">{msg['timestamp']}</span>
</div>
<div class="message-text">{self.format_discord_content(msg['content'], channel.guild)}</div>"""

                # Adiciona anexos
                if msg['attachments']:
                    html += '<div class="message-attachments">'
                    for attachment in msg['attachments']:
                        if any(attachment.lower().endswith(ext) for ext in ['.png', '.jpg', '.jpeg', '.gif', '.webp']):
                            html += f'<img src="{attachment}" alt="Attachment">'
                        else:
                            html += f'<a href="{attachment}" target="_blank">📎 Anexo</a>'
                    html += '</div>'

                # Adiciona embeds
                if msg['embeds']:
                    html += '<div class="message-embeds">'
                    for embed in msg['embeds']:
                        html += f"""<div class="embed">
{f'<div class="embed-title">{embed.get("title", "")}</div>' if embed.get("title") else ""}
{f'<div class="embed-description">{embed.get("description", "")}</div>' if embed.get("description") else ""}
</div>"""
                    html += '</div>'

                html += '</div></div>'

            html += '</div></div></body></html>'

            # Salva o arquivo
            os.makedirs('transcripts/html', exist_ok=True)
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"transcript_{channel.name}_{channel.id}_{timestamp}.html"
            filepath = os.path.join('transcripts/html', filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(html)
            print(f"[DEBUG] Transcript HTML salvo com sucesso")

            # Envia para o FTP
            try:
                import ftplib
                ftp = ftplib.FTP('ftp.seusite.com')
                ftp.login('usuario', 'senha')
                ftp.cwd('transcripts')
                
                with open(filepath, 'rb') as f:
                    ftp.storbinary(f'STOR {filename}', f)
                
                ftp.quit()
                print(f"[DEBUG] Transcript enviado para o FTP")
                
                # Retorna a URL do arquivo
                return f"https://seusite.com/transcripts/{filename}"
                
            except Exception as e:
                print(f"[ERRO] Falha ao enviar para o FTP: {e}")
                return filepath

        except Exception as e:
            print(f"[ERRO] Falha ao gerar transcript HTML: {e}")
            import traceback
            traceback.print_exc()
            return None

    def encode_data(self, data):
        """Codifica dados para base64 no formato do TicketTool"""
        import base64
        import json
        return base64.b64encode(json.dumps(data).encode()).decode()

    def encode_messages(self, messages):
        """Codifica mensagens para o formato do TicketTool"""
        encoded_messages = []
        for msg in messages:
            message_data = {
                'discordData': {},
                'attachments': [],
                'reactions': [],
                'content': msg.content,
                'components': [],
                'user_id': str(msg.author.id),
                'bot': msg.author.bot,
                'username': msg.author.name,
                'nick': msg.author.display_name,
                'tag': msg.author.discriminator,
                'avatar': msg.author.avatar.url if msg.author.avatar else '',
                'id': str(msg.id),
                'created': int(msg.created_at.timestamp() * 1000),
                'edited': int(msg.edited_at.timestamp() * 1000) if msg.edited_at else None
            }
            
            # Adiciona embeds se houver
            if msg.embeds:
                message_data['embeds'] = []
                for embed in msg.embeds:
                    embed_data = {
                        'description': embed.description,
                        'fields': []
                    }
                    if embed.fields:
                        for field in embed.fields:
                            embed_data['fields'].append({
                                'name': field.name,
                                'value': field.value,
                                'inline': field.inline
                            })
                    message_data['embeds'].append(embed_data)
            
            # Adiciona anexos se houver
            if msg.attachments:
                for attachment in msg.attachments:
                    message_data['attachments'].append({
                        'url': attachment.url,
                        'filename': attachment.filename,
                        'content_type': attachment.content_type
                    })
            
            encoded_messages.append(message_data)
        
        import base64
        import json
        return base64.b64encode(json.dumps(encoded_messages).encode()).decode()

    async def generate_transcript_html_summary(self, channel):
        guild = channel.guild
        messages = []
        attachments_saved = 0
        attachments_skipped = 0
        ticket_owner = None
        ticket_owner_avatar = guild.icon.url if guild.icon else ''
        user_counts = {}
        user_info = []
        
        # Coleta todas as mensagens primeiro
        message_list = []
        async for message in channel.history(limit=None, oldest_first=True):
            message_list.append(message)
            
            # Conta mensagens por usuário
            user_id = message.author.id
            if user_id not in user_counts:
                user_counts[user_id] = {
                    'count': 0,
                    'name': f"{message.author.name}",
                    'id': str(user_id)
                }
            user_counts[user_id]['count'] += 1
            
            if not ticket_owner and not message.author.bot:
                ticket_owner = message.author
                ticket_owner_avatar = message.author.avatar.url if hasattr(message.author, 'avatar') and message.author.avatar else ''

            # Conta anexos
            if message.attachments:
                for attachment in message.attachments:
                    if attachment.url.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp')):
                        attachments_saved += 1
                    else:
                        attachments_skipped += 1

        # Organiza informações dos usuários
        for user_id, data in user_counts.items():
            user_info.append(f"{data['count']} - {data['name']} ({data['id']})")

        # Gera o HTML
        css = """* { margin: 0; padding: 0; box-sizing: border-box; } body { font-family: 'gg sans', sans-serif; background-color: #313338; color: #dcddde; line-height: 1.5; } .container { max-width: 1200px; margin: 0 auto; padding: 20px; } .header { background-color: #2b2d31; padding: 20px; border-radius: 8px; margin-bottom: 20px; display: flex; align-items: center; gap: 15px; } .header img { width: 64px; height: 64px; border-radius: 50%; } .header-info h1 { font-size: 24px; color: #ffffff; margin-bottom: 5px; } .header-info p { font-size: 14px; color: #b5bac1; } .messages { display: flex; flex-direction: column; gap: 20px; } .message { display: flex; gap: 15px; padding: 10px; border-radius: 8px; transition: background-color 0.2s; } .message:hover { background-color: #2e3035; } .message-avatar { width: 40px; height: 40px; border-radius: 50%; } .message-content { flex: 1; } .message-header { display: flex; align-items: baseline; gap: 10px; margin-bottom: 5px; } .message-author { font-weight: 500; color: #ffffff; } .message-timestamp { font-size: 12px; color: #b5bac1; } .message-text { color: #dcddde; white-space: pre-wrap; } .message-attachments { display: flex; flex-wrap: wrap; gap: 10px; margin-top: 10px; } .message-attachments img { max-width: 300px; max-height: 300px; border-radius: 4px; } .message-embeds { margin-top: 10px; } .embed { background-color: #2b2d31; border-left: 4px solid #5865f2; border-radius: 4px; padding: 10px; margin-top: 5px; } .embed-title { font-weight: 600; color: #ffffff; margin-bottom: 5px; } .embed-description { color: #dcddde; } code { background-color: #2b2d31; padding: 2px 6px; border-radius: 4px; font-family: 'Consolas', monospace; } pre { background-color: #2b2d31; padding: 10px; border-radius: 4px; overflow-x: auto; margin: 10px 0; } a { color: #00a8fc; text-decoration: none; } a:hover { text-decoration: underline; } ::-webkit-scrollbar { width: 8px; height: 8px; } ::-webkit-scrollbar-track { background: transparent; } ::-webkit-scrollbar-thumb { background-color: #202225; border-radius: 4px; } ::-webkit-scrollbar-thumb:hover { background-color: #2e3338; }"""

        html = f"""<!DOCTYPE html><html lang="pt-BR"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>Transcript do Ticket</title><style>@import url('https://fonts.googleapis.com/css2?family=gg+sans:wght@400;500;700&display=swap');{css}</style></head><body><div class="container"><div class="header"><img src="{str(guild.icon.url) if guild.icon else ''}" alt="Server Icon"><div class="header-info"><h1>{channel.name}</h1><p>Transcript gerado em {datetime.datetime.now().strftime('%d/%m/%Y %H:%M')}</p></div></div><div class="messages">"""

        # Adiciona as mensagens
        for msg in message_list:
            timestamp = msg.created_at.strftime("%d/%m/%Y às %H:%M")
            avatar_url = msg.author.avatar.url if hasattr(msg.author, 'avatar') and msg.author.avatar else ''
            
            html += f"""<div class="message"><img class="message-avatar" src="{avatar_url}" alt="Avatar"><div class="message-content"><div class="message-header"><span class="message-author">{msg.author.name}</span><span class="message-timestamp">{timestamp}</span></div><div class="message-text">{self.format_discord_content(msg.content, guild)}</div>"""
            
            # Adiciona embeds
            if msg.embeds:
                for embed in msg.embeds:
                    if embed.description:
                        html += f"""<div class="embed">{self.format_discord_content(embed.description, guild)}</div>"""

            # Adiciona anexos
            if msg.attachments:
                html += '<div class="message-attachments">'
                for attachment in msg.attachments:
                    if any(attachment.lower().endswith(ext) for ext in ['.png', '.jpg', '.jpeg', '.gif', '.webp']):
                        html += f'<img src="{attachment}" alt="Attachment">'
                    else:
                        html += f'<a href="{attachment}" target="_blank">📎 Anexo</a>'
                html += '</div>'
            
            html += '</div></div>'

        html += '</div></div></body></html>'

        # Salva o arquivo
        os.makedirs('transcripts/html', exist_ok=True)
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"transcript_{channel.name}_{channel.id}_{timestamp}.html"
        filepath = os.path.join('transcripts/html', filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html)
            
        # Retorna o arquivo e dados para o embed
        transcript_data = {
            'ticket_owner': ticket_owner.name if ticket_owner else 'Unknown',
            'ticket_owner_mention': ticket_owner.mention if ticket_owner else 'Unknown',
            'ticket_owner_avatar': ticket_owner_avatar,
            'msg_count': len(message_list),
            'attachments_saved': attachments_saved,
            'attachments_skipped': attachments_skipped
        }
        
        return filepath, transcript_data

    async def generate_transcript_text(self, channel):
        """Gera o transcript do ticket em texto puro"""
        try:
            print(f"[DEBUG] Iniciando geração do transcript para o canal {channel.name}")
            
            # Coleta todas as mensagens
            messages = []
            async for message in channel.history(limit=None, oldest_first=True):
                messages.append({
                    'author': message.author.name,
                    'content': message.content,
                    'timestamp': message.created_at.strftime('%d/%m/%Y %H:%M')
                })
            
            print(f"[DEBUG] Coletadas {len(messages)} mensagens")

            # Gera o texto
            text = f"Transcript do Ticket: {channel.name}\n"
            text += f"Gerado em: {datetime.datetime.now().strftime('%d/%m/%Y %H:%M')}\n\n"

            # Adiciona as mensagens
            for msg in messages:
                text += f"[{msg['timestamp']}] {msg['author']}: {msg['content']}\n"

            # Cria o diretório se não existir
            os.makedirs('transcripts/text', exist_ok=True)
            print(f"[DEBUG] Diretório transcripts/text criado/verificado")

            # Gera o nome do arquivo
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"transcript_{channel.name}_{channel.id}_{timestamp}.txt"
            filepath = os.path.join('transcripts/text', filename)
            print(f"[DEBUG] Arquivo será salvo em: {filepath}")
            
            # Salva o arquivo
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(text)
            print(f"[DEBUG] Transcript salvo com sucesso")

            return filepath

        except Exception as e:
            print(f"[ERRO] Falha ao gerar transcript: {e}")
            import traceback
            traceback.print_exc()
            return None

    def load_steam_admin_roles(self):
        """Carrega os IDs dos cargos de admin do Steam"""
        try:
            with open('data/steam_admin_roles.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return []

    async def create_initial_ticket_message(self, channel, user, ticket_data=None, steam_profile=None):
        """Cria a mensagem inicial do ticket"""
        try:
            print(f"[DEBUG] Criando mensagem inicial para o ticket {channel.name}")
            
            description = (
                f"Olá {user.mention}!\n"
                "Se possível anexar fotos ou video para melhorar compreensão\n"
                "Para fechar este ticket, reaja com 🔒\n\n"
                f"{channel.guild.name} • {datetime.datetime.now().strftime('%d/%m/%Y %H:%M')}\n\n"
            )

            # Adiciona informações do Steam se disponível
            steam_info = ""
            if steam_profile:
                steam_info = (
                    f"**Nome Steam:** {steam_profile.get('personaname','Desconhecido')}\n"
                    f"**Perfil:** [Abrir perfil]({steam_profile.get('profileurl','')})\n"
                )
            elif ticket_data and ticket_data.get('steam_id'):
                steam_info = "❌ Steam ID não encontrada ou inválida na Steam Web API.\n"

            # Verifica se o autor ou algum membro do canal tem cargo de steam admin
            steam_admin_roles = self.get_steam_admin_roles()
            allowed = False
            for member in channel.members:
                if any(role.id in steam_admin_roles for role in getattr(member, 'roles', [])):
                    allowed = True
                    break
            if not allowed:
                steam_info = ''

            # Adiciona informações do formulário se disponíveis
            if ticket_data:
                if ticket_data.get('category') == "DENUNCIA":
                    description += (
                        "**Descreva o motivo da sua denuncia:**\n"
                        f"```{ticket_data.get('motivo', '')}```\n"
                        "**Nome da pessoa que você quer denunciar:**\n"
                        f"```{ticket_data.get('denunciado', '')}```\n"
                        "**Nos informe seu nome ingame:**\n"
                        f"```{ticket_data.get('nome_ingame', '')}```\n"
                        "**Informe sua Steam ID**\n"
                        f"```{ticket_data.get('steam_id', '')}```\n"
                        f"{steam_info}"
                        "**Informe a Data e Hora do ocorrido**\n"
                        f"```{ticket_data.get('data_hora', '')}```"
                    )
                else:
                    description += (
                        "Por favor nos Informe qual o seu problema.\n"
                        f"```{ticket_data.get('problema', '')}```\n"
                        "Nos informe seu nome ingame:\n"
                        f"```{ticket_data.get('nome_ingame', '')}```\n"
                        "Informe sua Steam ID\n"
                        f"```{ticket_data.get('steam_id', '')}```\n"
                        f"{steam_info}"
                    )
            else:
                description += (
                    "Por favor nos Informe qual o seu problema.\n"
                    "```\n\n```\n"
                    "Nos informe seu nome ingame:\n"
                    "```\n\n```\n"
                    "Informe sua Steam ID\n"
                    "```\n\n```"
                )

            embed = discord.Embed(
                description=description,
                color=0x2F3136  # Cor escura do Discord
            )
            if steam_profile and steam_profile.get('avatarfull'):
                embed.set_thumbnail(url=steam_profile['avatarfull'])

            # Adiciona botões de ação
            class TicketActionButtons(discord.ui.View):
                def __init__(self, cog):
                    super().__init__(timeout=None)
                    self.cog = cog

                @discord.ui.button(label="Fechar Ticket", style=discord.ButtonStyle.red, custom_id="close_ticket")
                async def close_ticket(self, button_interaction: discord.Interaction, button: discord.ui.Button):
                    await self.cog.close_ticket(button_interaction.channel, button_interaction.user)

            # Envia a mensagem inicial com o botão
            await channel.send(embed=embed, view=TicketActionButtons(self))
            print(f"[DEBUG] Mensagem inicial criada com sucesso para {channel.name}")

        except Exception as e:
            print(f"[ERRO] Falha ao criar mensagem inicial do ticket: {e}")
            import traceback
            traceback.print_exc()

    @commands.Cog.listener()
    async def on_message(self, message):
        """Manipula mensagens recebidas"""
        # Ignora mensagens de bots
        if message.author.bot:
            return

        # Verifica se é um canal de ticket
        if not isinstance(message.channel, discord.TextChannel):
            return
            
        if not message.channel.name.startswith(('suporte-', 'doacao-')):
            return

        # Se for um ticket novo (menos de 1 minuto), ignora comandos de IA
        channel_age = (datetime.datetime.utcnow() - message.channel.created_at).total_seconds()
        if channel_age < 60:  # 60 segundos = 1 minuto
            print(f"[DEBUG] Ticket novo ({channel_age}s), ignorando processamento de IA")
            return

        # Processa o resto da lógica de IA aqui...
        # (seu código existente de processamento de IA)

async def setup(bot):
    await bot.add_cog(TicketSystem(bot)) 