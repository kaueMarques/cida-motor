import os
import re
import sys
import json
from collections import Counter

def estimar_tokens(texto):
    
    if not texto:
        return 0
    tokens = re.findall(r'[a-zA-Z0-9_]+|[^a-zA-Z0-9_\s]', texto)
    return len(tokens)

def calcular_ter(tokens, caracteres):
    
    return tokens / caracteres if caracteres > 0 else 0

def construir_dicionario_rag(caminho_orig, limite_palavras=300):
    
    contador = Counter()
    arquivos_para_ler = []
    
    if os.path.isfile(caminho_orig):
        arquivos_para_ler.append(caminho_orig)
    else:
        for root, dirs, files in os.walk(caminho_orig):
            for file in files:
                if file.lower().endswith('.md') or file.lower().endswith('.txt'):
                    arquivos_para_ler.append(os.path.join(root, file))
                    
    for caminho in arquivos_para_ler:
        try:
            with open(caminho, 'r', encoding='utf-8', errors='ignore') as f:
                palavras = re.findall(r'\b[a-zA-Z_]{6,}\b', f.read())
                contador.update(palavras)
        except:
            pass
                    
    dicionario = {}
    id_atual = 1
    palavras_impacto = sorted(contador.items(), key=lambda x: x[1] * len(x[0]), reverse=True)
    
    for palavra, freq in palavras_impacto:
        if freq >= 3:
            dicionario[palavra] = f"Z{id_atual}"
            id_atual += 1
            if id_atual > limite_palavras:
                break
    return dicionario

def minificar_markdown_para_ia(texto, dicionario=None):
    
    texto = re.sub(r'^---\s*[\r\n]+.*?[\r\n]+---\s*[\r\n]+', '', texto, flags=re.DOTALL)
    texto = re.sub(r'<!--.*?-->', '', texto, flags=re.DOTALL)
    
    if dicionario:
        for palavra, id_token in sorted(dicionario.items(), key=lambda x: len(x[0]), reverse=True):
            texto = re.sub(rf'\b{re.escape(palavra)}\b', id_token, texto)
            
    
    texto = re.sub(r'!\[([^\]]*)\]\([^)]+\)', r'[\1]', texto) 
    texto = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', texto)    
    
    
    
    texto = re.sub(r'(?<!\w)(\*\*|__|\*|_)(.*?)\1(?!\w)', r'\2', texto)
    
    
    texto = re.sub(r'^[-*_]{3,}\s*$', '', texto, flags=re.MULTILINE)
    
    
    texto = re.sub(r'\|\s+', '|', texto)
    texto = re.sub(r'\s+\|', '|', texto)
    
    
    texto = re.sub(r' {2,}', ' ', texto)
    texto = re.sub(r'\n{3,}', '\n\n', texto)
    return texto.strip()

def main():
    print("\n======================================================")
    print("   📝 MARKDOWN RAG MINIFIER - STANDALONE")
    print("======================================================\n")
    
    args = sys.argv[1:]
    if not args:
        caminho_input = input("👉 Cole o caminho da pasta ou arquivo .md para minificar:\n> ").strip()
        if not caminho_input:
            print("❌ Erro: Nenhum caminho fornecido.")
            return
        caminho_orig = os.path.abspath(os.path.expanduser(caminho_input))
    else:
        caminho_orig = os.path.abspath(os.path.expanduser(args[0]))

    if not os.path.exists(caminho_orig):
        print(f"❌ Erro: Caminho não encontrado: {caminho_orig}")
        return

    dicionario_rag = construir_dicionario_rag(caminho_orig)
    dic_invertido = {id_token: palavra for palavra, id_token in dicionario_rag.items()}
    
    
    if dic_invertido:
        rag_str = ", ".join(f"{k}={v}" for k, v in dic_invertido.items())
        header_rag = f"> 🤖 AI RAG DICT: {rag_str}\n\n"
    else:
        header_rag = ""

    arquivos_alvo = [caminho_orig] if os.path.isfile(caminho_orig) else [os.path.join(root, file) for root, _, files in os.walk(caminho_orig) for file in files if file.lower().endswith(".md") or file.lower().endswith(".txt")]
    
    total_tokens_orig = 0
    total_tokens_comp = 0
    total_arquivos = 0
    arquivos_ignorados = []
    
    for caminho in arquivos_alvo:
        try:
            with open(caminho, 'r', encoding='utf-8', errors='ignore') as f:
                conteudo = f.read()
            
            minificado = minificar_markdown_para_ia(conteudo, dicionario_rag)
            conteudo_final = f"{header_rag}{minificado}"
            
            chars_orig = len(conteudo)
            tokens_orig = estimar_tokens(conteudo)
            
            chars_comp = len(conteudo_final)
            tokens_comp = estimar_tokens(conteudo_final)
            
            
            if tokens_comp >= tokens_orig:
                arquivos_ignorados.append(caminho)
                print(f"⏭️  Ignorado (sem redução): {caminho}")
                print(f"   Tokens: {tokens_orig:6d} -> {tokens_comp:6d}")
                print("-" * 80)
                continue
            
            pasta = os.path.dirname(caminho)
            nome = os.path.basename(caminho)
            caminho_comp = os.path.join(pasta, f"{os.path.splitext(nome)[0]}_mimificado.md")
            
            with open(caminho_comp, 'w', encoding='utf-8') as f:
                f.write(conteudo_final)
                
            total_arquivos += 1
            
            chars_orig = len(conteudo)
            tokens_orig = estimar_tokens(conteudo)
            
            chars_comp = len(conteudo_final)
            tokens_comp = estimar_tokens(conteudo_final)
            
            total_tokens_orig += tokens_orig
            total_tokens_comp += tokens_comp
            
            ter_orig = calcular_ter(tokens_orig, chars_orig)
            ter_comp = calcular_ter(tokens_comp, chars_comp)
            
            print(f"📄 {caminho_comp}")
            print(f"   [Original]   Chars: {chars_orig:6d} | Tokens: {tokens_orig:6d} | TER: {ter_orig:.2f}")
            print(f"   [Modificado] Chars: {chars_comp:6d} | Tokens: {tokens_comp:6d} | TER: {ter_comp:.2f}")
            print("-" * 80)
        except Exception as e:
            print(f"Erro ao processar {caminho}: {e}")

    
    print("\n" + "=" * 80)
    print("📊 RESULTADO DO BENCHMARK")
    print("=" * 80)
    print(f"Arquivos lidos               : {len(arquivos_alvo)}")
    print(f"Arquivos minificados         : {total_arquivos}")
    
    if arquivos_ignorados:
        pasta_base = os.path.dirname(caminho_orig) if os.path.isfile(caminho_orig) else caminho_orig
        caminho_ignorados = os.path.join(pasta_base, "arquivos_ignorados.txt")
        with open(caminho_ignorados, 'w', encoding='utf-8') as f:
            f.write("Arquivos ignorados (não houve redução de tokens):\n\n")
            f.write("\n".join(arquivos_ignorados))
        print(f"Arquivos ignorados           : {len(arquivos_ignorados)} (Lista salva em: {caminho_ignorados})")
    else:
        print(f"Arquivos ignorados           : 0")
    
    if total_arquivos > 0:
        print(f"Total de Tokens (Original)   : {total_tokens_orig:,}")
        print(f"Total de Tokens (Modificado) : {total_tokens_comp:,}")
        
        diferenca = ((total_tokens_comp - total_tokens_orig) / total_tokens_orig) * 100 if total_tokens_orig > 0 else 0
        economia_tokens = total_tokens_orig - total_tokens_comp
        
        print("\n" + "-" * 80)
        if diferenca < 0:
            print(f"✅ SUCESSO: O payload para a IA REDUZIU em {abs(diferenca):.2f}%")
            print(f"   Você economizou {economia_tokens:,} tokens por requisição/leitura nesta base.")
        else:
            print(f"⚠️  ALERTA DE CUSTO: O payload AUMENTOU em {diferenca:+.2f}%")
            print("   O formato modificado está inflando a janela de contexto em relação ao original.")
        print("-" * 80)

if __name__ == "__main__":
    main()