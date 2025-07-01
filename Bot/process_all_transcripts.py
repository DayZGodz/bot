import os
import pickle
from bs4 import BeautifulSoup
import re
import json
import base64
from collections import Counter

# Lista de staffs autorizados
staffs_autorizados = [
    'shootergod',
    'moraeexs',
    'valentiini',
    'zsky_exe',
    'favelazoficial',
    'apito3'
]

def limpar_nome(nome):
    """Limpa o nome do usuário removendo discriminador e normalizando"""
    # Remove o discriminador (#1234)
    nome = re.sub(r'#\d{4}$', '', nome)
    # Remove caracteres especiais e converte para minúsculas
    nome = re.sub(r'[^\w\s]', '', nome.lower())
    return nome

def extrair_mensagens_base64(html_content):
    """Extrai e decodifica as mensagens em base64 do transcript"""
    try:
        # Encontra o valor de messages="...."
        match = re.search(r'let messages = "([^"]+)"', html_content)
        if not match:
            return None
            
        # Decodifica o base64
        base64_content = match.group(1)
        decoded = base64.b64decode(base64_content)
        messages = json.loads(decoded)
        
        # Converte para o formato que precisamos
        converted_messages = []
        for msg in messages:
            if msg.get('bot'):
                continue
                
            author = msg.get('username', '')
            content = msg.get('content', '')
            
            # Ignora mensagens vazias ou apenas com menções
            if not content or content.startswith('<@'):
                continue
                
            # Extrai conteúdo dos embeds se houver
            if 'embeds' in msg and msg['embeds']:
                for embed in msg['embeds']:
                    if 'description' in embed:
                        content += '\\n' + embed['description']
            
            converted_messages.append({
                'author': author,
                'content': content.strip()
            })
            
        return converted_messages
    except Exception as e:
        print(f"❌ Erro ao decodificar base64: {e}")
        return None

def processar_transcript(filepath):
    """Processa um transcript HTML e retorna pares de pergunta-resposta"""
    pares = []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        # Tenta extrair mensagens do base64 primeiro
        messages = extrair_mensagens_base64(html_content)
        if not messages:
            # Se não conseguir, tenta parsear o HTML diretamente
            soup = BeautifulSoup(html_content, 'html.parser')
            messages = []
            for msg in soup.find_all('div', class_='message'):
                author = msg.find('div', class_='author')
                content = msg.find_all('div')[-1]
                
                if not author or not content:
                    continue
                    
                messages.append({
                    'author': author.get_text().strip(),
                    'content': content.get_text().strip()
                })
        
        # Processa as mensagens para encontrar pares pergunta-resposta
        for i in range(len(messages)-1):
            current_msg = messages[i]
            next_msg = messages[i+1]
            
            current_author = limpar_nome(current_msg['author'])
            next_author = limpar_nome(next_msg['author'])
            
            # Se a mensagem atual é de um usuário e a próxima é de um staff autorizado
            if not any(staff in current_author for staff in staffs_autorizados):
                for staff in staffs_autorizados:
                    if staff in next_author:
                        print(f"✅ Aprendendo com resposta do staff {next_author}")
                        pares.append({
                            'pergunta': current_msg['content'],
                            'resposta': next_msg['content'],
                            'staff': staff
                        })
                        break
        
        return pares
    except Exception as e:
        print(f"❌ Erro ao processar {filepath}: {e}")
        return []

def main():
    # Carrega modelo e base de conhecimento existentes
    try:
        with open('nlp_model/ai_model.pkl', 'rb') as f:
            modelo = pickle.load(f)
        with open('nlp_model/knowledge_base.pkl', 'rb') as f:
            knowledge_base = pickle.load(f)
        print(f"✅ Modelo e base de conhecimento carregados! ({len(knowledge_base)} exemplos)")
    except:
        print("❌ Erro ao carregar modelo. Criando nova base de conhecimento...")
        knowledge_base = []

    # Processa todos os transcripts
    transcript_dir = os.path.join('transcripts', 'html')
    total_processados = 0
    total_aprendidos = 0
    staffs_encontrados = Counter()
    
    print("\n🔄 Iniciando processamento de transcripts...")
    
    for filename in os.listdir(transcript_dir):
        if filename.endswith('.html') and not filename.endswith('_base64.html'):
            filepath = os.path.join(transcript_dir, filename)
            print(f"\n📝 Processando: {filename}")
            
            # Processa o transcript
            novos_pares = processar_transcript(filepath)
            
            # Adiciona à base de conhecimento
            for par in novos_pares:
                if par not in knowledge_base:
                    knowledge_base.append(par)
                    total_aprendidos += 1
                    staffs_encontrados[par['staff']] += 1
            
            total_processados += 1
            print(f"✅ Processado! Novos pares aprendidos: {len(novos_pares)}")
    
    # Salva a base de conhecimento atualizada
    os.makedirs('nlp_model', exist_ok=True)
    with open('nlp_model/knowledge_base.pkl', 'wb') as f:
        pickle.dump(knowledge_base, f)
    
    print(f"\n🎉 Processamento concluído!")
    print(f"📊 Resultados:")
    print(f"   • Transcripts processados: {total_processados}")
    print(f"   • Novas interações aprendidas: {total_aprendidos}")
    print(f"   • Total na base de conhecimento: {len(knowledge_base)}")
    
    if staffs_encontrados:
        print("\n👥 Interações por staff:")
        for staff, count in staffs_encontrados.most_common():
            print(f"   • {staff}: {count} interações")

if __name__ == "__main__":
    main() 