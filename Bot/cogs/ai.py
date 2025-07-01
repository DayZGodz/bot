import discord
from discord.ext import commands
import os
import pickle
import re
import json
import asyncio
from datetime import datetime
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.svm import SVC
from sklearn.pipeline import Pipeline
from bs4 import BeautifulSoup
import subprocess
import sys

class AISystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.modelo = None
        self.palavras_chave = {}
        self.knowledge_base = []
        self.limite_confianca = 0.3  # Reduzido para ser mais proativo
        self.model_path = 'nlp_model/ai_model.pkl'
        self.knowledge_path = 'nlp_model/knowledge_base.pkl'
        self.keywords_path = 'data/ai_keywords.json'
        self.transcript_channel_id = None
        self.auto_atendimento = True
        print("🤖 Inicializando sistema de IA...")
        asyncio.create_task(self.inicializar_ia())
    
    @commands.Cog.listener()
    async def on_ready(self):
        print("🧠 Sistema de IA carregado")
        await self.carregar_configuracoes()

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """Monitora mensagens para responder com IA"""
        try:
            # Debug inicial
            print(f"\n🔍 DEBUG: Mensagem recebida")
            print(f"Canal: {message.channel.name if hasattr(message.channel, 'name') else 'DM'}")
            print(f"Autor: {message.author.name}#{message.author.discriminator}")
            print(f"Conteúdo: {message.content}")
            
            # Ignora mensagens do próprio bot
            if message.author.bot:
                print("❌ DEBUG: Mensagem ignorada - é um bot")
                return
                
            # Verifica se é um canal de ticket
            if not isinstance(message.channel, discord.TextChannel):
                print("❌ DEBUG: Mensagem ignorada - não é um canal de texto")
                return
                
            # Verifica se é um canal de ticket pelo nome
            channel_name = message.channel.name.lower()
            is_ticket = any(channel_name.startswith(prefix) for prefix in ['suporte-', 'denuncia-', 'doacao-', 'raid-'])
            
            print(f"📝 DEBUG: Nome do canal: {channel_name}")
            print(f"🎫 DEBUG: É um ticket? {is_ticket}")
            
            if not is_ticket:
                print("❌ DEBUG: Mensagem ignorada - não é um canal de ticket")
                return
                
            # Verifica se o modelo está carregado
            if not self.modelo:
                print("❌ DEBUG: Modelo não carregado")
                return
                
            if not self.knowledge_base:
                print("❌ DEBUG: Base de conhecimento vazia")
                return
                
            # Prepara a mensagem
            pergunta = message.content.lower().strip()
            
            print(f"📝 DEBUG: Processando mensagem: {pergunta}")
            
            # Faz a predição
            predicao = self.modelo.predict([pergunta])[0]
            probabilidades = self.modelo.predict_proba([pergunta])[0]
            confianca = max(probabilidades)
            
            print(f"🎯 DEBUG: Confiança: {confianca:.2f}")
            print(f"💭 DEBUG: Predição: {predicao}")
            
            # Se a confiança for alta o suficiente, responde
            if confianca >= self.limite_confianca:
                print("✨ DEBUG: Confiança suficiente para responder")
                
                # Encontra exemplos similares na base de conhecimento
                exemplos_similares = []
                for exemplo in self.knowledge_base:
                    similaridade = self.calcular_similaridade(pergunta, exemplo['pergunta'])
                    print(f"📊 DEBUG: Similaridade com '{exemplo['pergunta']}': {similaridade:.2f}")
                    if similaridade > 0.3:  # Reduzido o limite de similaridade
                        exemplos_similares.append(exemplo['resposta'])
                        print(f"✅ DEBUG: Exemplo similar encontrado: {exemplo['resposta']}")
                
                # Se encontrou exemplos similares, usa a resposta mais comum
                if exemplos_similares:
                    from collections import Counter
                    resposta = Counter(exemplos_similares).most_common(1)[0][0]
                    print(f"💡 DEBUG: Usando resposta mais comum dos exemplos similares")
                else:
                    resposta = predicao
                    print(f"💡 DEBUG: Usando resposta da predição direta")
                
                print(f"📝 DEBUG: Resposta final escolhida: {resposta}")
                
                # Formata a resposta
                embed = discord.Embed(
                    description=resposta,
                    color=discord.Color.blue()
                )
                embed.set_author(
                    name="Assistente FavelaZ",
                    icon_url=self.bot.user.display_avatar.url
                )
                
                await message.channel.send(embed=embed)
                print("✅ DEBUG: Resposta enviada com sucesso!")
                
        except Exception as e:
            print(f"❌ DEBUG: Erro ao processar mensagem: {e}")
            import traceback
            traceback.print_exc()

    def calcular_similaridade(self, texto1, texto2):
        """Calcula a similaridade entre dois textos"""
        try:
            # Usa o próprio vectorizer do modelo
            vectorizer = self.modelo.named_steps['vectorizer']
            
            # Vetoriza os textos
            vetor1 = vectorizer.transform([texto1])
            vetor2 = vectorizer.transform([texto2])
            
            # Calcula similaridade de cosseno
            from sklearn.metrics.pairwise import cosine_similarity
            return cosine_similarity(vetor1, vetor2)[0][0]
        except Exception as e:
            print(f"❌ Erro ao calcular similaridade: {e}")
            return 0.0

    async def carregar_configuracoes(self):
        """Carrega configurações da IA"""
        try:
            if os.path.exists(self.keywords_path):
                with open(self.keywords_path, 'r', encoding='utf-8') as f:
                    self.palavras_chave = json.load(f)
            print("✅ Configurações de IA carregadas")
        except Exception as e:
            print(f"⚠️ Erro ao carregar configurações: {e}")

    async def salvar_configuracoes(self):
        """Salva configurações da IA"""
        try:
            os.makedirs('data', exist_ok=True)
            with open(self.keywords_path, 'w', encoding='utf-8') as f:
                json.dump(self.palavras_chave, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"⚠️ Erro ao salvar configurações: {e}")

    async def inicializar_ia(self):
        """Inicializa o modelo de IA e carrega a base de conhecimento"""
        try:
            print("📚 Carregando modelo de IA...")
            # Carrega o modelo treinado
            with open(self.model_path, 'rb') as f:
                self.modelo = pickle.load(f)
            
            # Carrega a base de conhecimento
            with open(self.knowledge_path, 'rb') as f:
                self.knowledge_base = pickle.load(f)
            
            print("✅ Modelo de IA carregado com sucesso!")
            print(f"📚 Base de conhecimento: {len(self.knowledge_base)} exemplos")
            
        except Exception as e:
            print(f"❌ Erro ao carregar modelo de IA: {e}")
            print("🔄 Tentando treinar novo modelo...")
            await self.treinar_ia(None)

    async def salvar_modelo(self):
        os.makedirs('nlp_model', exist_ok=True)
        with open(self.model_path, 'wb') as f:
            pickle.dump(self.modelo, f)
        with open(self.knowledge_path, 'wb') as f:
            pickle.dump(self.knowledge_base, f)

    @commands.command(name='treinar')
    @commands.has_permissions(administrator=True)
    async def treinar_ia(self, ctx):
        """Treina a IA com os transcripts (apenas admin)"""
        try:
            print("🔄 Iniciando treinamento da IA...")
            # Executa o script de processamento
            subprocess.run([sys.executable, 'process_transcripts.py'], check=True)
            
            # Recarrega o modelo
            await self.inicializar_ia()
            
            if ctx:
                await ctx.send("✅ IA treinada com sucesso!")
            
        except Exception as e:
            print(f"❌ Erro ao treinar IA: {e}")
            if ctx:
                await ctx.send(f"❌ Erro ao treinar IA: {str(e)[:1500]}")

    @commands.command(name='processar_transcripts')
    @commands.has_permissions(administrator=True)
    async def processar_transcripts_html(self, ctx):
        """Processa todos os transcripts HTML existentes para treinar a IA"""
        try:
            # Envia mensagem inicial
            embed = discord.Embed(
                title="🔄 Processando Transcripts",
                description="Iniciando processamento de todos os transcripts...",
                color=discord.Color.blue()
            )
            status_msg = await ctx.send(embed=embed)

            # Conta quantos transcripts foram processados
            total_processados = 0
            total_aprendidos = 0

            # Processa todos os arquivos HTML na pasta transcripts/html
            transcript_dir = os.path.join('transcripts', 'html')
            for filename in os.listdir(transcript_dir):
                if filename.endswith('.html') and not filename.endswith('_base64.html'):
                    filepath = os.path.join(transcript_dir, filename)
                    print(f"📝 Processando transcript: {filename}")
                    
                    # Processa o transcript
                    if await self.aprender_com_transcript_html(filepath):
                        total_aprendidos += 1
                    total_processados += 1

                    # Atualiza a mensagem de status a cada 5 transcripts
                    if total_processados % 5 == 0:
                        embed.description = f"Processando transcripts...\n\n✅ Processados: {total_processados}\n📚 Aprendidos: {total_aprendidos}"
                        await status_msg.edit(embed=embed)

            # Salva o modelo atualizado
            await self.salvar_modelo()

            # Atualiza mensagem final
            embed.title = "✅ Processamento Concluído"
            embed.description = f"**Resultados:**\n\n📝 Total de transcripts processados: {total_processados}\n📚 Interações aprendidas: {total_aprendidos}\n\n🤖 Modelo atualizado e salvo!"
            embed.color = discord.Color.green()
            await status_msg.edit(embed=embed)

        except Exception as e:
            embed = discord.Embed(
                title="❌ Erro no Processamento",
                description=f"Ocorreu um erro ao processar os transcripts:\n```{str(e)}```",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)

    async def aprender_com_transcript_html(self, filepath: str):
        """Aprende com um transcript HTML"""
        try:
            # Lista de staffs autorizados
            staffs_autorizados = [
                'shootergod',
                'moraeexs',
                'valentiini',
                'zsky_exe',
                'favelazoficial',
                'apito3'
            ]
            
            with open(filepath, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            # Parse HTML
            soup = BeautifulSoup(html_content, 'html.parser')
            messages = soup.find_all('div', class_='message')
            
            # Extrai pares de pergunta-resposta
            for i in range(len(messages)-1):
                current_msg = messages[i]
                next_msg = messages[i+1]
                
                # Pega o autor e conteúdo
                current_author = current_msg.find('div', class_='author').get_text().strip().lower()
                next_author = next_msg.find('div', class_='author').get_text().strip().lower()
                
                current_content = current_msg.find_all('div')[-1].get_text().strip()
                next_content = next_msg.find_all('div')[-1].get_text().strip()
                
                # Se a mensagem atual é de um usuário e a próxima é de um staff autorizado
                if not any(staff in current_author for staff in staffs_autorizados):
                    if any(staff in next_author for staff in staffs_autorizados):
                        print(f"✅ Aprendendo com resposta do staff {next_author}")
                        # Aprende com a interação
                        await self.aprender_com_transcript(current_content, next_content)
            
            print(f"✅ Aprendido com transcript HTML: {filepath}")
            return True
            
        except Exception as e:
            print(f"❌ Erro ao processar transcript HTML: {e}")
            return False

    async def aprender_com_transcript(self, mensagem, resposta_admin):
        """Aprende com interações na sala de transcript"""
        # Extrai palavras-chave da mensagem (apenas palavras relevantes)
        palavras = re.findall(r'\b\w{4,}\b', mensagem.lower())  # Palavras com 4+ caracteres
        
        for palavra in palavras:
            # Ignora palavras muito comuns
            palavras_comuns = ['para', 'com', 'que', 'uma', 'você', 'muito', 'mais', 'como', 'quando', 'onde', 'porque']
            if palavra not in palavras_comuns and palavra not in self.palavras_chave:
                self.palavras_chave[palavra] = resposta_admin
        
        await self.salvar_configuracoes()
        print(f"🧠 IA aprendeu {len(palavras)} nova(s) palavra(s)-chave")

    @commands.command(name='ask')
    async def fazer_pergunta(self, ctx, *, pergunta: str):
        if not self.modelo:
            return await ctx.send("🤖 IA ainda não inicializada.")
        
        try:
            pergunta_processada = pergunta.lower()
            resposta = self.modelo.predict([pergunta_processada])[0]
            confianca = self.modelo.predict_proba([pergunta_processada]).max()
            
            if confianca > 0.6:
                embed = discord.Embed(
                    title="🤖 Resposta da IA",
                    description=resposta,
                    color=discord.Color.blue()
                )
                await ctx.send(embed=embed)
            else:
                embed = discord.Embed(
                    title="🤖 Não tenho certeza",
                    description="Recomendo criar um ticket para ajuda especializada.",
                    color=discord.Color.orange()
                )
                await ctx.send(embed=embed)
                
        except Exception as e:
            await ctx.send("❌ Erro ao processar pergunta.")

    @commands.command(name='add_keyword')
    @commands.has_permissions(administrator=True)
    async def adicionar_palavra_chave(self, ctx, palavra: str, *, resposta: str):
        """Adiciona uma palavra-chave e sua resposta"""
        self.palavras_chave[palavra.lower()] = resposta
        await self.salvar_configuracoes()
        
        embed = discord.Embed(
            title="✅ Palavra-chave adicionada",
            description=f"**Palavra:** {palavra}\n**Resposta:** {resposta}",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)

    @commands.command(name='list_keywords')
    @commands.has_permissions(administrator=True)
    async def listar_palavras_chave(self, ctx):
        """Lista todas as palavras-chave"""
        if not self.palavras_chave:
            await ctx.send("📝 Nenhuma palavra-chave cadastrada.")
            return
        
        embed = discord.Embed(
            title="📝 Palavras-chave cadastradas",
            color=discord.Color.blue()
        )
        
        for palavra, resposta in self.palavras_chave.items():
            embed.add_field(
                name=f"🔑 {palavra}",
                value=resposta[:100] + "..." if len(resposta) > 100 else resposta,
                inline=False
            )
        
        await ctx.send(embed=embed)

    @commands.command(name='remove_keyword')
    @commands.has_permissions(administrator=True)
    async def remover_palavra_chave(self, ctx, palavra: str):
        """Remove uma palavra-chave"""
        if palavra.lower() in self.palavras_chave:
            del self.palavras_chave[palavra.lower()]
            await self.salvar_configuracoes()
            await ctx.send(f"✅ Palavra-chave '{palavra}' removida.")
        else:
            await ctx.send(f"❌ Palavra-chave '{palavra}' não encontrada.")

    @commands.command(name='toggle_auto')
    @commands.has_permissions(administrator=True)
    async def alternar_atendimento_automatico(self, ctx):
        """Alterna o atendimento automático de tickets"""
        self.auto_atendimento = not self.auto_atendimento
        status = "ativado" if self.auto_atendimento else "desativado"
        
        embed = discord.Embed(
            title="🤖 Atendimento Automático",
            description=f"Status: **{status}**",
            color=discord.Color.green() if self.auto_atendimento else discord.Color.red()
        )
        await ctx.send(embed=embed)

    @commands.command(name='setup_transcript')
    @commands.has_permissions(administrator=True)
    async def configurar_sala_transcript(self, ctx):
        """Cria a sala de transcript para aprendizado da IA"""
        try:
            # Cria o canal de transcript
            categoria = ctx.channel.category
            transcript_channel = await ctx.guild.create_text_channel(
                name="📚-transcript-ia",
                category=categoria,
                topic="Sala para aprendizado da IA - Interações entre admins e usuários"
            )
            
            self.transcript_channel_id = transcript_channel.id
            
            embed = discord.Embed(
                title="📚 Sala de Transcript criada",
                description=f"**Canal:** {transcript_channel.mention}\n\n"
                           f"Esta sala será usada para:\n"
                           f"• A IA aprender com as interações\n"
                           f"• Administradores treinarem a IA\n"
                           f"• Melhorar o atendimento automático",
                color=discord.Color.green()
            )
            await ctx.send(embed=embed)
            
        except Exception as e:
            await ctx.send(f"❌ Erro ao criar sala de transcript: {e}")

    @commands.command(name='ia_status')
    @commands.has_permissions(administrator=True)
    async def mostrar_status(self, ctx):
        """Mostra o status atual do sistema de IA"""
        embed = discord.Embed(
            title="🤖 Status do Sistema de IA",
            color=discord.Color.blue()
        )
        
        # Status do modelo
        modelo_status = "✅ Carregado" if self.modelo else "❌ Não carregado"
        embed.add_field(name="🧠 Modelo de IA", value=modelo_status, inline=True)
        
        # Base de conhecimento
        embed.add_field(
            name="📚 Base de Conhecimento",
            value=f"{len(self.knowledge_base)} exemplos",
            inline=True
        )
        
        # Limite de confiança
        embed.add_field(
            name="🎯 Limite de Confiança",
            value=f"{self.limite_confianca:.1%}",
            inline=True
        )
        
        await ctx.send(embed=embed)

    async def responder_ticket(self, channel, mensagem, author):
        """Responde a um ticket usando o modelo de IA"""
        try:
            if not self.modelo or not self.knowledge_base:
                print("❌ DEBUG: Modelo ou base de conhecimento não carregados")
                return None

            # Prepara a mensagem
            pergunta = mensagem.lower().strip()
            
            # Ignora mensagens muito curtas
            if len(pergunta) < 5:
                print("❌ DEBUG: Mensagem muito curta")
                return None
                
            print(f"🔍 DEBUG: Analisando mensagem: {pergunta}")
                
            # Faz a predição
            predicao = self.modelo.predict([pergunta])[0]
            probabilidades = self.modelo.predict_proba([pergunta])[0]
            confianca = max(probabilidades)
            
            print(f"🎯 DEBUG: Confiança: {confianca:.2f}")
            print(f"💭 DEBUG: Predição: {predicao}")
            
            # Se a confiança for alta o suficiente, responde
            if confianca >= self.limite_confianca:
                print("✨ DEBUG: Confiança suficiente para responder")
                
                # Encontra exemplos similares na base de conhecimento
                exemplos_similares = []
                for exemplo in self.knowledge_base:
                    similaridade = self.calcular_similaridade(pergunta, exemplo['pergunta'])
                    print(f"📊 DEBUG: Similaridade com '{exemplo['pergunta']}': {similaridade:.2f}")
                    if similaridade > 0.5:
                        exemplos_similares.append(exemplo['resposta'])
                        print(f"✅ DEBUG: Exemplo similar encontrado: {exemplo['resposta']}")
                
                # Se encontrou exemplos similares, usa a resposta mais comum
                if exemplos_similares:
                    from collections import Counter
                    resposta = Counter(exemplos_similares).most_common(1)[0][0]
                    print(f"💡 DEBUG: Usando resposta mais comum dos exemplos similares")
                else:
                    resposta = predicao
                    print(f"💡 DEBUG: Usando resposta da predição direta")
                
                print(f"📝 DEBUG: Resposta final escolhida: {resposta}")
                
                # Formata a resposta
                embed = discord.Embed(
                    description=resposta,
                    color=discord.Color.blue()
                )
                embed.set_author(
                    name="Assistente FavelaZ",
                    icon_url=self.bot.user.display_avatar.url
                )
                
                return embed
            
            return None
                
        except Exception as e:
            print(f"❌ DEBUG: Erro ao processar mensagem: {e}")
            import traceback
            traceback.print_exc()
            return None

async def setup(bot):
    await bot.add_cog(AISystem(bot)) 