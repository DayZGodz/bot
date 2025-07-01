import discord
from discord.ext import commands

class HelpSystem(commands.Cog):
    """Sistema de ajuda personalizado do bot"""
    
    def __init__(self, bot):
        self.bot = bot
        # Remove o comando help padrão
        self.bot.remove_command('help')
    
    @commands.Cog.listener()
    async def on_ready(self):
        print("❓ Sistema de ajuda carregado")

    @commands.command(name='help', aliases=['ajuda', 'comandos'])
    async def help_command(self, ctx, categoria: str = None):
        """Sistema de ajuda personalizado com categorias"""
        if categoria:
            # Help específico por categoria
            if categoria.lower() in ['ticket', 'tickets']:
                embed = discord.Embed(
                    title="🎫 Comandos de Tickets",
                    description="Sistema completo de suporte via tickets",
                    color=discord.Color.blue()
                )
                embed.add_field(
                    name="📝 Comandos Básicos",
                    value="• `!ticket [motivo]` - Criar novo ticket\n• `!close` - Fechar ticket atual",
                    inline=False
                )
                embed.add_field(
                    name="👥 Gerenciamento (Staff)",
                    value="• `!add @usuário` - Adicionar usuário ao ticket\n• `!remove @usuário` - Remover usuário do ticket",
                    inline=False
                )
                embed.add_field(
                    name="ℹ️ Como usar",
                    value="1. Use `!ticket` seguido do motivo\n2. Um canal privado será criado\n3. Converse com a equipe\n4. Use `!close` para fechar",
                    inline=False
                )
                
            elif categoria.lower() in ['ia', 'ai', 'inteligencia']:
                embed = discord.Embed(
                    title="🧠 Sistema de IA",
                    description="IA inteligente que aprende com conversas",
                    color=discord.Color.green()
                )
                embed.add_field(
                    name="🤖 Comandos de Usuário",
                    value="• `!ask [pergunta]` - Fazer pergunta à IA",
                    inline=False
                )
                embed.add_field(
                    name="⚙️ Comandos Administrativos",
                    value="• `!treinar_ia` - Retreinar modelo com novos dados",
                    inline=False
                )
                embed.add_field(
                    name="📚 Como funciona",
                    value="A IA aprende com transcripts de tickets fechados e responde perguntas comuns automaticamente.",
                    inline=False
                )
                
            elif categoria.lower() in ['voz', 'voice', 'audio']:
                embed = discord.Embed(
                    title="🎵 Sistema de Voz",
                    description="Clonagem de voz e mensagens automatizadas",
                    color=discord.Color.purple()
                )
                embed.add_field(
                    name="🔊 Controles do Sistema",
                    value="• `!iniciar_sistema` - Ativar sistema de voz\n• `!parar_sistema` - Desativar sistema\n• `!status_voz` - Ver status atual",
                    inline=False
                )
                embed.add_field(
                    name="🎤 Comandos de Voz",
                    value="• `!falar [texto]` - Bot falar texto específico\n• `!falar_com_musica [texto]` - Falar com jazz de fundo\n• `!controlar_jazz [play/stop/status]` - Controlar música\n• `!add_mensagem [texto]` - Adicionar nova mensagem (Admin)",
                    inline=False
                )
                embed.add_field(
                    name="🎧 Recursos",
                    value="• Clonagem de voz com ElevenLabs\n• Mensagens programadas\n• Música de espera\n• Sistema 24/7",
                    inline=False
                )
                
            elif categoria.lower() in ['admin', 'administração', 'adm']:
                embed = discord.Embed(
                    title="⚙️ Comandos Administrativos",
                    description="Ferramentas para administradores",
                    color=discord.Color.red()
                )
                embed.add_field(
                    name="📊 Informações",
                    value="• `!info` - Status detalhado do bot\n• `!logs [linhas]` - Ver logs do sistema",
                    inline=False
                )
                embed.add_field(
                    name="🛠️ Manutenção",
                    value="• `!reload [cog]` - Recarregar módulos\n• `!reload_all` - Recarregar todos os cogs\n• `!shutdown` - Desligar bot",
                    inline=False
                )
                embed.add_field(
                    name="🗂️ Gerenciamento",
                    value="• `!limpar [quantidade]` - Limpar mensagens\n• `!backup_transcripts` - Backup de tickets\n• `!say [canal] [mensagem]` - Bot enviar mensagem",
                    inline=False
                )
                
            else:
                embed = discord.Embed(
                    title="❌ Categoria Não Encontrada",
                    description="A categoria especificada não existe.",
                    color=discord.Color.red()
                )
                embed.add_field(
                    name="📋 Categorias Disponíveis",
                    value="`ticket` • `ia` • `voz` • `admin`",
                    inline=False
                )
                embed.add_field(
                    name="💡 Exemplo",
                    value="Use `!help ticket` para ver comandos de tickets",
                    inline=False
                )
        else:
            # Help geral - página principal
            embed = discord.Embed(
                title="🤖 Bot de Tickets Avançado",
                description="Sistema completo de suporte com IA e clonagem de voz",
                color=discord.Color.gold()
            )
            
            # Cards das funcionalidades principais
            embed.add_field(
                name="🎫 Sistema de Tickets",
                value="`!help ticket`\nSuporte via canais privados",
                inline=True
            )
            embed.add_field(
                name="🧠 IA Inteligente",
                value="`!help ia`\nRespostas automáticas",
                inline=True
            )
            embed.add_field(
                name="🎵 Sistema de Voz",
                value="`!help voz`\nClonagem e automação",
                inline=True
            )
            embed.add_field(
                name="⚙️ Administração",
                value="`!help admin`\nFerramentas de gestão",
                inline=True
            )
            embed.add_field(
                name="🔗 Links Úteis",
                value="`!invite` - Convite do bot",
                inline=True
            )
            embed.add_field(
                name="❓ Suporte",
                value="Use `!ticket` para ajuda",
                inline=True
            )
            
            # Seção de início rápido
            embed.add_field(
                name="🚀 Começar Agora",
                value="• **Abrir ticket:** `!ticket preciso de ajuda`\n• **Perguntar à IA:** `!ask qual o horário?`\n• **Status do bot:** `!info`",
                inline=False
            )
            
            if self.bot.user.avatar:
                embed.set_thumbnail(url=self.bot.user.avatar.url)
        
        # Footer simples
        embed.set_footer(text=f"Solicitado por {ctx.author.display_name}")
        embed.timestamp = discord.utils.utcnow()
        
        await ctx.send(embed=embed)

    @commands.command(name='comandos_lista', aliases=['command_list'])
    async def lista_comandos(self, ctx):
        """Lista todos os comandos disponíveis de forma resumida"""
        embed = discord.Embed(
            title="📜 Lista Completa de Comandos",
            color=discord.Color.blue()
        )
        
        # Organiza comandos por categoria
        comandos = {
            "🎫 Tickets": [
                "`!ticket [motivo]`", "`!close`", "`!add @user`", "`!remove @user`"
            ],
            "🧠 IA": [
                "`!ask [pergunta]`", "`!treinar_ia`"
            ],
            "🎵 Voz": [
                "`!iniciar_sistema`", "`!falar_com_musica [texto]`", "`!controlar_jazz [acao]`", "`!status_voz`"
            ],
            "⚙️ Admin": [
                "`!info`", "`!limpar [qtd]`", "`!reload [cog]`", "`!backup_transcripts`"
            ],
            "❓ Ajuda": [
                "`!help [categoria]`", "`!comandos_lista`", "`!invite`"
            ]
        }
        
        for categoria, lista_comandos in comandos.items():
            embed.add_field(
                name=categoria,
                value=" • ".join(lista_comandos),
                inline=False
            )
        
        embed.set_footer(text="Use !help [categoria] para detalhes específicos")
        await ctx.send(embed=embed)

    @commands.command(name='exemplo', aliases=['examples'])
    async def exemplos_uso(self, ctx):
        """Mostra exemplos práticos de uso do bot"""
        embed = discord.Embed(
            title="💡 Exemplos Práticos",
            description="Veja como usar as principais funcionalidades:",
            color=discord.Color.green()
        )
        
        exemplos = [
            ("🎫 Criar Ticket", "`!ticket Não consigo fazer login no sistema`", "Abre um canal privado para suporte"),
            ("🧠 Perguntar à IA", "`!ask Qual o horário de funcionamento?`", "IA responde automaticamente"),
            ("🎵 Ativar Voz", "`!iniciar_sistema`", "Bot entra no canal e inicia mensagens automáticas"),
            ("🗣️ Bot Falar", "`!falar Bem-vindos ao nosso servidor!`", "Bot fala o texto com voz clonada"),
            ("📊 Status", "`!info`", "Mostra informações detalhadas do bot"),
            ("🧹 Limpar", "`!limpar 10`", "Remove as últimas 10 mensagens do canal")
        ]
        
        for titulo, comando, descricao in exemplos:
            embed.add_field(
                name=f"{titulo}",
                value=f"**Comando:** {comando}\n**Resultado:** {descricao}",
                inline=False
            )
        
        embed.set_footer(text="Todos os comandos começam com ! (ou prefixo configurado)")
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(HelpSystem(bot)) 