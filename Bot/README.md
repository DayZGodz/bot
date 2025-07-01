# 🤖 Bot Discord FavelaZ - Sistema Completo de Tickets e Voz

**O bot mais avançado para servidores de DayZ com IA inteligente, sistema de voz automatizado e tickets profissionais.**

## 🚀 **CONFIGURAÇÃO AUTOMÁTICA COMPLETA**

### **Comando Mágico - Apenas Uma Vez!**
```bash
!setup_servidor
```

**Este comando único criará automaticamente:**
- 🛡️ **Categoria Admin** com 5 canais de controle
- 🎮 **Categoria FavelaZ** com sistema de tickets e voz
- ⚙️ **Configuração automática** do arquivo `.env`
- 🎫 **Painel de tickets** instalado e funcionando
- 📞 **Sistema de voz** conectado automaticamente
- 🤖 **IA inteligente** ativa para atendimento

---

## 🎯 **Funcionalidades Principais**

### 🎫 **Sistema de Tickets Avançado**
- **Painel interativo** com botões modernos
- **FAQ automática** para reduzir tickets
- **Sistema de prioridades** (Baixa/Média/Alta)
- **Claim/Release** para organização da equipe
- **Fechamento automático** por inatividade (72h)
- **Transcripts automáticos** salvos
- **Estatísticas em tempo real**

### 🎵 **Sistema de Voz Profissional**
- **Clonagem de voz** com ElevenLabs
- **Mensagens automáticas** personalizáveis
- **Música de espera** com fade in/out cinematográfico
- **Cache inteligente** (economia de créditos)
- **Crossfade profissional** entre música e fala
- **Central de atendimento** 24/7

### 🤖 **IA Inteligente**
- **Aprendizado automático** com transcripts
- **Respostas contextuais** baseadas em conversas anteriores
- **Análise de sentimentos** para melhor atendimento
- **Melhora contínua** com uso

---

## 📋 **Comandos Principais**

### 🔧 **Setup e Administração (Apenas Dono)**
```bash
!setup_servidor              # Configuração automática completa
!gerenciar_mensagens         # Interface para gerenciar mensagens de voz
```

### 🎫 **Sistema de Tickets**
```bash
!painel_tickets              # Cria painel interativo
!stats_tickets               # Estatísticas detalhadas
!tag <nome>                  # Sistema FAQ rápido
!add_tag <nome> <resposta>   # Adiciona nova resposta FAQ
!claim                       # Reivindica ticket (staff)
!release                     # Libera ticket reivindicado
```

### 🎵 **Sistema de Voz**
```bash
!iniciar_sistema            # Conecta e inicia sistema completo
!falar <texto>              # Reproduz texto com voz clonada
!controlar_jazz <ação>      # Controla música (play/stop/status)
!cache_info                 # Informações de economia
!pre_gerar_cache           # Gera todos os áudios antecipadamente
```

### 🛡️ **Comandos Admin**
```bash
!info                       # Informações do servidor
!limpar <quantidade>        # Limpa mensagens
!backup                     # Backup das configurações
!logs                       # Logs do sistema
```

---

## ⚡ **Instalação Rápida**

### 1. **Clone o Repositório**
```bash
git clone https://github.com/seu-usuario/bot-faveladz.git
cd bot-faveladz
```

### 2. **Instale Dependências**
```bash
pip install -r requirements.txt
```

### 3. **Configure o `.env`** (Apenas o Token)
```env
BOT_TOKEN=seu_token_do_discord
ELEVENLABS_API_KEY=sua_chave_da_elevenlabs
VOICE_ID=id_da_voz_clonada
```

### 4. **Execute o Bot**
```bash
python start_bot.py
```

### 5. **Configure Automaticamente**
```bash
!setup_servidor
```

**Pronto! Seu servidor está 100% configurado!**

---

## 🏗️ **Estrutura Criada Automaticamente**

### 🛡️ **Categoria Admin**
- 📊 **painel-controle** - Central de monitoramento
- 🎛️ **configurações** - Configurações avançadas
- 📈 **estatísticas** - Relatórios detalhados
- 🔧 **logs-sistema** - Logs automáticos
- 💬 **chat-staff** - Chat privado da equipe

### 🎮 **Categoria FavelaZ**
- 🎫 **suporte-tickets** - Sistema de tickets com painel
- 📞 **Central de Atendimento** - Canal de voz automático
- 📢 **informações** - Informações do servidor

---

## 🎭 **Sistema de Mensagens Personalizáveis**

### **Interface Visual Completa (Apenas Dono)**
- ➕ **Adicionar** novas mensagens
- ✏️ **Editar** mensagens existentes
- 🗑️ **Remover** mensagens
- 📋 **Listar** todas as mensagens
- 🔄 **Recarregar** cache para nova voz

### **Mensagens Padrão**
1. "Bem-vindo ao melhor servidor de DayZ. FavelaZ ."
2. "Sua chamada é importante para nós. Aguarde enquanto conectamos você a um atendente."
3. "Para agilizar seu atendimento, tenha em mãos o número do seu protocolo."
4. "Nosso horário de funcionamento é das nove às dezoito horas, de segunda a sexta-feira."
5. "Você pode abrir um ticket a qualquer momento digitando exclamação ticket."
6. "Obrigado por escolher nossos serviços. Aguarde na linha."
7. "Seu tempo de espera estimado é de aproximadamente dois minutos."
8. "Para emergências, entre em contato através do nosso canal prioritário."

---

## 💡 **Funcionalidades Avançadas**

### 🎯 **Sistema FAQ Inteligente**
- Respostas automáticas para perguntas comuns
- Reduz tickets desnecessários
- Interface com select menu
- Fácil gerenciamento

### 📊 **Estatísticas em Tempo Real**
- Tickets ativos, criados e fechados
- Performance da equipe
- Tempo médio de atendimento
- Análise de eficiência

### 🔒 **Sistema de Segurança**
- Permissões avançadas
- Anti-múltiplas sessões
- Backup automático
- Logs detalhados

### 💾 **Cache Inteligente**
- Economia de créditos ElevenLabs
- Primeiro uso: gera áudios
- Usos seguintes: zero créditos
- Comando para pré-gerar tudo

---

## 📁 **Estrutura de Arquivos**

```
Bot/
├── cogs/
│   ├── admin.py          # Comandos administrativos e setup
│   ├── ai.py             # Sistema de IA inteligente
│   ├── tickets.py        # Sistema completo de tickets
│   ├── voice_system.py   # Sistema de voz e mensagens
│   └── help_system.py    # Sistema de ajuda
├── cached_voices/        # Cache de áudios (criado automaticamente)
├── temp_audio/          # Arquivos temporários
├── transcripts/         # Transcripts salvos
├── data/               # Dados do sistema (criado automaticamente)
├── nlp_model/          # Modelo de IA
├── main.py             # Arquivo principal
├── start_bot.py        # Script de inicialização
├── requirements.txt    # Dependências
└── .env               # Configurações (atualizado automaticamente)
```

---

## 🎉 **Resultado Final**

Após executar `!setup_servidor`, você terá:

✅ **Servidor 100% configurado automaticamente**  
✅ **Sistema de tickets profissional funcionando**  
✅ **Bot conectado ao canal de voz**  
✅ **Mensagens automáticas reproduzindo**  
✅ **IA inteligente ativa**  
✅ **Cache de voz otimizado**  
✅ **Permissões configuradas**  
✅ **Arquivo .env atualizado**  

**Seu servidor FavelaZ estará pronto para receber os membros com uma experiência profissional completa!**

---

## 🔥 **FavelaZ - Sobreviva, Conquiste, Domine!**

*Sistema desenvolvido especificamente para servidores de DayZ com foco na experiência do usuário e eficiência administrativa.* 