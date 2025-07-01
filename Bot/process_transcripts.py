import os
import json
import base64
from bs4 import BeautifulSoup
import pickle
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.neighbors import KNeighborsClassifier
from sklearn.pipeline import Pipeline

def processar_transcript_base64(filepath):
    """Processa um arquivo de transcript com dados em base64"""
    print(f"\n🔍 Processando transcript base64: {filepath}")
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extrai a string base64 do script
        start = content.find('let messages = "') + len('let messages = "')
        end = content.find('";window.Convert')
        if start == -1 or end == -1:
            print("❌ Formato base64 não encontrado no arquivo")
            return []
            
        base64_str = content[start:end]
        
        # Decodifica os dados
        try:
            json_str = base64.b64decode(base64_str).decode('utf-8')
            messages = json.loads(json_str)
        except:
            print("❌ Erro ao decodificar dados base64")
            return []
        
        # Extrai pares de pergunta-resposta
        qa_pairs = []
        for i in range(len(messages)-1):
            current = messages[i]
            next_msg = messages[i+1]
            
            # Pula mensagens do bot
            if current.get('bot', True) or next_msg.get('bot', True):
                continue
                
            # Extrai conteúdo das mensagens
            current_content = current.get('content', '')
            next_content = next_msg.get('content', '')
            
            # Ignora mensagens muito curtas ou comandos
            if len(current_content) > 5 and not current_content.startswith('!'):
                qa_pairs.append({
                    'pergunta': current_content,
                    'resposta': next_content
                })
        
        print(f"✅ Extraídos {len(qa_pairs)} pares de pergunta-resposta")
        return qa_pairs
        
    except Exception as e:
        print(f"❌ Erro ao processar {filepath}: {e}")
        return []

def processar_transcript_html(filepath):
    """Processa um arquivo de transcript HTML e retorna pares de pergunta-resposta"""
    print(f"\n🔍 Processando transcript HTML: {filepath}")
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            html_content = f.read()
            
        # Verifica se é um transcript base64
        if 'let messages = "' in html_content:
            return processar_transcript_base64(filepath)
        
        # Parse HTML
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Encontra todas as mensagens
        messages = []
        for msg_div in soup.find_all('div', class_='message'):
            # Extrai o autor e conteúdo
            author_div = msg_div.find('div', class_='author')
            content_div = msg_div.find('div', class_='content') or msg_div.find_all('div')[-1]
            
            if author_div and content_div:
                author = author_div.get_text().split('(')[0].strip()
                content = content_div.get_text().strip()
                
                # Verifica se é mensagem do bot
                is_bot = 'Ticket' in author or 'Bot' in author
                
                messages.append({
                    'author': author,
                    'content': content,
                    'is_bot': is_bot
                })
        
        print(f"📝 Encontradas {len(messages)} mensagens")
        
        # Extrai pares de pergunta-resposta
        qa_pairs = []
        for i in range(len(messages)-1):
            current = messages[i]
            next_msg = messages[i+1]
            
            # Pula mensagens do bot
            if current['is_bot'] or next_msg['is_bot']:
                continue
                
            # Ignora mensagens muito curtas ou comandos
            if len(current['content']) > 5 and not current['content'].startswith('!'):
                qa_pairs.append({
                    'pergunta': current['content'],
                    'resposta': next_msg['content']
                })
        
        print(f"✅ Extraídos {len(qa_pairs)} pares de pergunta-resposta")
        return qa_pairs
        
    except Exception as e:
        print(f"❌ Erro ao processar {filepath}: {e}")
        return []

def treinar_modelo(qa_pairs):
    """Treina o modelo de IA com os pares de pergunta-resposta"""
    if not qa_pairs:
        print("❌ Nenhum par de pergunta-resposta para treinar")
        return
        
    print("\n🧠 Treinando modelo de IA...")
    
    # Prepara os dados
    X = [pair['pergunta'] for pair in qa_pairs]
    y = [pair['resposta'] for pair in qa_pairs]
    
    # Cria o pipeline
    pipeline = Pipeline([
        ('vectorizer', TfidfVectorizer(
            ngram_range=(1, 2),
            max_features=5000,
            min_df=2,
            max_df=0.95
        )),
        ('classifier', KNeighborsClassifier(
            n_neighbors=3,
            weights='distance'
        ))
    ])
    
    # Treina o modelo
    pipeline.fit(X, y)
    
    # Salva o modelo e a base de conhecimento
    os.makedirs('nlp_model', exist_ok=True)
    
    with open('nlp_model/ai_model.pkl', 'wb') as f:
        pickle.dump(pipeline, f)
        
    with open('nlp_model/knowledge_base.pkl', 'wb') as f:
        pickle.dump(qa_pairs, f)
    
    print(f"✅ Modelo treinado com {len(qa_pairs)} exemplos")

def main():
    # Processa todos os transcripts HTML
    print("🚀 Iniciando processamento de transcripts HTML")
    
    all_qa_pairs = []
    transcript_dir = "transcripts/html"
    
    for filename in os.listdir(transcript_dir):
        if filename.endswith(".html"):
            filepath = os.path.join(transcript_dir, filename)
            qa_pairs = processar_transcript_html(filepath)
            all_qa_pairs.extend(qa_pairs)
    
    print(f"\n📊 Total de pares pergunta-resposta: {len(all_qa_pairs)}")
    
    # Treina o modelo com todos os pares
    treinar_modelo(all_qa_pairs)

if __name__ == '__main__':
    main() 