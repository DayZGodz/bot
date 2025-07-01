import json
import base64
from datetime import datetime
import os
import re

def decode_base64_json(encoded_str):
    """Decodifica uma string base64 para JSON"""
    try:
        # Remove a parte do script e pega apenas o JSON base64
        match = re.search(r'let messages = "([^"]+)"', encoded_str)
        if not match:
            return None
        
        base64_str = match.group(1)
        decoded = base64.b64decode(base64_str)
        return json.loads(decoded)
    except Exception as e:
        print(f"❌ Erro ao decodificar JSON: {e}")
        return None

def convert_timestamp(timestamp_str):
    """Converte timestamp para formato legível"""
    try:
        dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        return dt.strftime('%d/%m/%Y às %H:%M:%S')
    except:
        return datetime.now().strftime('%d/%m/%Y às %H:%M:%S')

def create_html_transcript(messages, channel_name):
    """Cria um arquivo HTML no formato esperado pelo sistema"""
    html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <title>Transcript - {channel_name}</title>
    <style>
        body {{ font-family: Arial, sans-serif; background-color: #2f3136; color: #dcddde; }}
        .message {{ margin: 10px 0; padding: 10px; border-left: 3px solid #5865f2; }}
        .author {{ font-weight: bold; color: #00d4aa; }}
        .timestamp {{ color: #72767d; font-size: 12px; }}
    </style>
</head>
<body>
    <h1>Transcript - {channel_name}</h1>
    <p>Gerado em: {datetime.now().strftime('%d/%m/%Y às %H:%M:%S')}</p>
"""
    
    for msg in messages:
        # Pula mensagens do sistema ou vazias
        if not msg.get('content') and not msg.get('embeds'):
            continue
            
        # Formata a data
        created_timestamp = datetime.fromtimestamp(msg['created']/1000).strftime('%d/%m/%Y %H:%M:%S')
        
        # Pega o conteúdo da mensagem
        content = msg.get('content', '')
        
        # Adiciona embeds se existirem
        if msg.get('embeds'):
            for embed in msg['embeds']:
                if embed.get('description'):
                    content += f"\n{embed['description']}"
        
        # Formata a mensagem
        html += f"""
    <div class="message">
        <div class="author">{msg['username']} <span class="timestamp">{created_timestamp}</span></div>
        <div>{content}</div>
    </div>"""

    html += """
</body>
</html>"""
    
    return html

def parse_text_transcript(content):
    """Converte um transcript do formato texto para o formato de mensagens"""
    messages = []
    
    # Extrai informações do cabeçalho
    header_match = re.search(r'Canal: #(.*?) \(ID: (\d+)\)\nTópico: (.*?)\nSalvo em: (.*?)\n', content)
    if not header_match:
        return None
        
    channel_name = header_match.group(1)
    channel_id = header_match.group(2)
    topic = header_match.group(3)
    saved_date = header_match.group(4)
    
    # Processa as mensagens
    message_pattern = r'\[(.*?)\] (.*?): (.*?)(?=\n\[|$)'
    for match in re.finditer(message_pattern, content, re.DOTALL):
        timestamp_str = match.group(1)
        author = match.group(2)
        content = match.group(3).strip()
        
        # Converte timestamp
        try:
            timestamp = datetime.strptime(timestamp_str, '%d/%m/%Y %H:%M:%S')
            unix_timestamp = int(timestamp.timestamp() * 1000)
        except:
            unix_timestamp = 0
        
        # Verifica se é bot
        is_bot = 'Ticket' in author
        
        # Cria a mensagem
        message = {
            'content': content,
            'username': author,
            'bot': is_bot,
            'created': unix_timestamp,
            'avatar': 'default'
        }
        
        # Se tem embed
        if 'Embed:' in content:
            embed_count = re.search(r'Embed: (\d+) embed\(s\)', content)
            if embed_count:
                message['embeds'] = [{
                    'description': f'Ticket embed ({embed_count.group(1)})'
                }]
        
        messages.append(message)
    
    return messages

def convert_transcript(input_file):
    """Converte um transcript para o novo formato HTML bonito"""
    print(f"\n🔄 Convertendo: {input_file}")
    
    try:
        # Lê o arquivo de entrada
        with open(input_file, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Determina o formato e extrai os dados
        if 'let messages = "' in content:
            # Formato base64
            start = content.find('let messages = "') + len('let messages = "')
            end = content.find('";window.Convert')
            base64_str = content[start:end]
            json_str = base64.b64decode(base64_str).decode('utf-8')
            data = json.loads(json_str)
        elif content.startswith('TRANSCRIPT DO TICKET'):
            # Formato texto
            data = parse_text_transcript(content)
            if not data:
                print("❌ Erro ao parsear transcript de texto")
                return
        else:
            # Tenta JSON direto
            try:
                data = json.loads(content)
            except:
                print("❌ Formato de transcript não reconhecido")
                return
            
        # Extrai informações do servidor e canal
        server_name = "FavelaZ"
        channel_name = os.path.basename(input_file).replace('.txt', '').replace('.html', '')
        message_count = len(data)
        
        # Cria o HTML
        html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{
            background-color: #1e2124;
            color: #ffffff;
            font-family: 'Whitney', 'Helvetica Neue', Helvetica, Arial, sans-serif;
            margin: 0;
            padding: 20px;
        }}
        .header {{
            display: flex;
            align-items: center;
            margin-bottom: 20px;
        }}
        .server-icon {{
            width: 50px;
            height: 50px;
            border-radius: 16px;
            margin-right: 10px;
        }}
        .server-info {{
            flex-grow: 1;
        }}
        .server-name {{
            font-size: 24px;
            font-weight: bold;
            margin: 0;
        }}
        .channel-name {{
            font-size: 16px;
            color: #72767d;
            margin: 0;
        }}
        .message-count {{
            font-size: 14px;
            color: #72767d;
        }}
        .message {{
            background-color: #36393f;
            border-radius: 4px;
            padding: 10px;
            margin-bottom: 10px;
        }}
        .author {{
            display: flex;
            align-items: center;
            margin-bottom: 5px;
        }}
        .author-avatar {{
            width: 40px;
            height: 40px;
            border-radius: 50%;
            margin-right: 10px;
        }}
        .author-name {{
            color: #fff;
            font-weight: bold;
        }}
        .timestamp {{
            color: #72767d;
            font-size: 12px;
            margin-left: 10px;
        }}
        .content {{
            color: #dcddde;
            margin-left: 50px;
            white-space: pre-wrap;
        }}
        .bot-tag {{
            background-color: #5865f2;
            color: white;
            border-radius: 3px;
            padding: 1px 4px;
            font-size: 10px;
            font-weight: 500;
            margin-left: 5px;
            text-transform: uppercase;
        }}
        .embed {{
            border-left: 4px solid #ff00c3;
            background-color: #2f3136;
            padding: 8px 10px;
            margin-top: 5px;
        }}
        .embed-title {{
            color: #ffffff;
            font-weight: bold;
        }}
        .embed-description {{
            color: #dcddde;
        }}
    </style>
</head>
<body>
    <div class="header">
        <img class="server-icon" src="https://cdn.discordapp.com/icons/1183634762527670324/a_4bd0a59d5530b51f480826d1f50e0528.gif">
        <div class="server-info">
            <h1 class="server-name">{server_name}</h1>
            <p class="channel-name">{channel_name}</p>
            <p class="message-count">{message_count} messages</p>
        </div>
    </div>
"""
        
        # Processa cada mensagem
        for msg in data:
            # Informações do autor
            author = msg.get('username', 'Unknown')
            is_bot = msg.get('bot', False)
            timestamp = datetime.fromtimestamp(msg.get('created', 0)/1000).strftime('%b %d, %Y %I:%M %p')
            content = msg.get('content', '')
            
            # Avatar do autor (usa um padrão se não encontrar)
            avatar_hash = msg.get('avatar', 'default')
            avatar_url = f"https://cdn.discordapp.com/avatars/{msg.get('user_id', '0')}/{avatar_hash}.png"
            if avatar_hash == 'default':
                avatar_url = "https://cdn.discordapp.com/embed/avatars/0.png"
            
            # Cria o HTML da mensagem
            html += f"""
    <div class="message">
        <div class="author">
            <img class="author-avatar" src="{avatar_url}">
            <span class="author-name">{author}</span>
            {"<span class='bot-tag'>BOT</span>" if is_bot else ""}
            <span class="timestamp">{timestamp}</span>
        </div>
        <div class="content">
            {content}
"""
            
            # Processa embeds se houver
            if 'embeds' in msg and msg['embeds']:
                for embed in msg['embeds']:
                    description = embed.get('description', '')
                    html += f"""
            <div class="embed">
                <div class="embed-description">{description}</div>
            </div>
"""
                    
            html += """
        </div>
    </div>
"""
            
        # Fecha o HTML
        html += """
</body>
</html>
"""
        
        # Salva o arquivo
        output_file = os.path.join('transcripts/html', f"{channel_name}.html")
        os.makedirs('transcripts/html', exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html)
            
        print(f"✅ Transcript convertido: {output_file}")
        
    except Exception as e:
        print(f"❌ Erro ao converter {input_file}: {e}")

def main():
    # Processa todos os arquivos na pasta transcripts
    print("🚀 Iniciando conversão de transcripts")
    
    for filename in os.listdir('transcripts'):
        if filename.endswith(('.txt', '.html')) and not filename.startswith('.'):
            input_file = os.path.join('transcripts', filename)
            convert_transcript(input_file)

if __name__ == "__main__":
    main() 