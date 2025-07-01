#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
import asyncio

# Carrega variáveis de ambiente
load_dotenv()

print("=== DEBUG DO SISTEMA DE TICKETS ===")
print(f"BOT_TOKEN: {'✅ Configurado' if os.getenv('BOT_TOKEN') else '❌ Não configurado'}")
print(f"SUPPORT_ROLE_ID: {os.getenv('SUPPORT_ROLE_ID', '0')}")
print(f"TICKET_CATEGORY_ID: {os.getenv('TICKET_CATEGORY_ID', '0')}")

# Configuração do bot
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True

bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f"🤖 Bot conectado: {bot.user}")
    print(f"📊 Servidores: {len(bot.guilds)}")
    
    for guild in bot.guilds:
        print(f"\n🏛️ Servidor: {guild.name} (ID: {guild.id})")
        
        # Verifica se o SUPPORT_ROLE_ID existe
        support_role_id = int(os.getenv('SUPPORT_ROLE_ID', 0))
        support_role = guild.get_role(support_role_id)
        print(f"👥 Support Role: {'✅ Encontrado' if support_role else '❌ Não encontrado'} (ID: {support_role_id})")
        
        # Verifica se a categoria existe
        ticket_category_id = int(os.getenv('TICKET_CATEGORY_ID', 0))
        category = discord.utils.get(guild.categories, id=ticket_category_id)
        print(f"📁 Categoria Tickets: {'✅ Encontrada' if category else '❌ Não encontrada'} (ID: {ticket_category_id})")
        
        # Lista todas as categorias
        print(f"📂 Categorias disponíveis:")
        for cat in guild.categories:
            print(f"   - {cat.name} (ID: {cat.id})")
        
        # Lista todos os roles
        print(f"👤 Roles disponíveis:")
        for role in guild.roles:
            if role.name != "@everyone":
                print(f"   - {role.name} (ID: {role.id})")

# Teste de criação de ticket simplificado
@bot.command(name='test_ticket')
async def test_ticket(ctx):
    """Teste básico de criação de ticket"""
    print(f"\n🧪 TESTE DE TICKET INICIADO por {ctx.author}")
    
    try:
        # Verifica configurações básicas
        support_role_id = int(os.getenv('SUPPORT_ROLE_ID', 0))
        support_role = ctx.guild.get_role(support_role_id)
        
        if not support_role:
            await ctx.send(f"❌ Support Role não encontrado! ID configurado: {support_role_id}")
            return
        
        ticket_category_id = int(os.getenv('TICKET_CATEGORY_ID', 0))
        category = discord.utils.get(ctx.guild.categories, id=ticket_category_id)
        
        if not category:
            await ctx.send(f"❌ Categoria de tickets não encontrada! ID configurado: {ticket_category_id}")
            return
        
        # Tenta criar um canal de teste
        test_channel = await category.create_text_channel(
            name=f"test-ticket-{ctx.author.id}",
            topic=f"Teste de ticket por {ctx.author.display_name}",
            overwrites={
                ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False),
                ctx.author: discord.PermissionOverwrite(read_messages=True, send_messages=True),
                support_role: discord.PermissionOverwrite(read_messages=True, send_messages=True),
                bot.user: discord.PermissionOverwrite(read_messages=True, send_messages=True)
            }
        )
        
        await ctx.send(f"✅ Teste de ticket criado com sucesso: {test_channel.mention}")
        await test_channel.send(f"🧪 **TESTE DE TICKET**\n\nCanal criado por: {ctx.author.mention}\nSistema funcionando corretamente!")
        
        print(f"✅ Teste de ticket bem-sucedido: {test_channel.name}")
        
    except Exception as e:
        await ctx.send(f"❌ Erro no teste de ticket: {str(e)}")
        print(f"❌ Erro no teste: {e}")

# Teste do dropdown
@bot.command(name='test_dropdown')
async def test_dropdown(ctx):
    """Teste do dropdown de tickets"""
    print(f"\n🧪 TESTE DE DROPDOWN INICIADO por {ctx.author}")
    
    try:
        # Importa o sistema de tickets
        from cogs.tickets import AdvancedTicketSystem, OpenTicketDropdownView
        
        # Cria uma instância temporária
        ticket_system = AdvancedTicketSystem(bot)
        
        # Cria o embed de teste
        embed = discord.Embed(
            title="🧪 TESTE DO DROPDOWN",
            description="Teste do sistema de seleção de categorias",
            color=0xFF8C00
        )
        
        # Cria a view
        view = OpenTicketDropdownView(ticket_system)
        
        await ctx.send(embed=embed, view=view)
        print("✅ Dropdown de teste criado")
        
    except Exception as e:
        await ctx.send(f"❌ Erro no teste do dropdown: {str(e)}")
        print(f"❌ Erro no dropdown: {e}")

if __name__ == "__main__":
    try:
        bot.run(os.getenv('BOT_TOKEN'))
    except Exception as e:
        print(f"❌ Erro ao iniciar bot: {e}") 