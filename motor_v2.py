import tiktoken


import time

import os
import re
import sys
from collections import Counter


print("POC V1")
def estimar_tokens(texto):
    """Calcula tokens usando a biblioteca oficial da OpenAI (tiktoken)."""
    if not texto:
        return 0
    enc = tiktoken.get_encoding("cl100k_base")
    return len(enc.encode(texto))

def calcular_ter(tokens, caracteres):
    """Calcula o Token Efficiency Ratio (TER)"""
    return tokens / caracteres if caracteres > 0 else 0

def eh_arquivo_de_teste(root, file, pasta_orig):
    """Verifica se o arquivo é de teste baseado no nome ou na pasta."""
    caminho_relativo = os.path.relpath(root, pasta_orig).lower()
    partes = caminho_relativo.split(os.sep)
    nome_arquivo = file.lower()
    
    if "test" in partes or "tests" in partes or "teste" in partes or "testes" in partes:
        return True
    if "test" in nome_arquivo or "teste" in nome_arquivo:
        return True
    return False

def construir_dicionario_rag(pasta_orig, ext_orig, limite_palavras=300):
    """Identifica as palavras de maior impacto (frequência x tamanho) para o dicionário da IA."""
    contador = Counter()
    for root, dirs, files in os.walk(pasta_orig):
        for file in files:
            if eh_arquivo_de_teste(root, file, pasta_orig):
                continue
            if not ext_orig or file.endswith(ext_orig):
                caminho = os.path.join(root, file)
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

def minificar_codigo_para_ia(codigo_fonte, dicionario=None):
    """Remove lixo visual para a IA, preservando semântica e palavras-chave."""
    codigo = re.sub(r'/\*.*?\*/', '', codigo_fonte, flags=re.DOTALL)
    codigo = re.sub(r'//.*', '', codigo)
    codigo = re.sub(r'package\s+[\w\.]+;', '', codigo)
    codigo = re.sub(r'import\s+(?:static\s+)?[\w\.\*]+;', '', codigo)
    
    codigo = re.sub(r'@\w+(?:\([^)]*\))?\s*', '', codigo)
    codigo = re.sub(r'\b(System\.out\.\w+|console\.\w+|logger\.\w+|print|Log\.\w+|trace|debug|error|assert)\s*\([^)]*\);?', '', codigo)
    codigo = re.sub(r'(["\']).{15,}?\1', '""', codigo)
    codigo = re.sub(r'\b(public|private|protected|export|final|volatile|strictfp)\s+', '', codigo)
    codigo = re.sub(r'\b(this|self)\.', '', codigo)
    
    codigo = re.sub(r'\s+', ' ', codigo)
    codigo = re.sub(r'\s*([+\-*/%&|<>!^~?:;,{}()\[\]=]+)\s*', r'\1', codigo)
    
    if dicionario:
        for palavra, id_token in sorted(dicionario.items(), key=lambda x: len(x[0]), reverse=True):
            codigo = re.sub(rf'\b{re.escape(palavra)}\b', id_token, codigo)
            
    return codigo.strip()

def processar_e_comparar(pasta_orig, pasta_comp, ext_orig, ext_comp):
    print("\n" + "=" * 80)
    print("🚀 INICIANDO MINIFICAÇÃO E COMPARAÇÃO DE TOKENS")
    print("=" * 80)
    print(f"📁 Lendo Origem   : {pasta_orig}")
    print(f"📁 Gerando Destino: {pasta_comp}")
    print("-" * 80 + "\n")
    
    total_tokens_orig = 0
    total_tokens_comp = 0
    total_arquivos = 0
    
    print("⏳ Analisando frequências e construindo Dicionário RAG...")
    dicionario_rag = construir_dicionario_rag(pasta_orig, ext_orig)
    
    caminho_dic = os.path.join(pasta_comp, "dict.tkcd")
    with open(caminho_dic, 'w', encoding='utf-8') as fd:
        fd.write("INSTRUÇÃO PARA A IA: Use o mapa abaixo para traduzir o código fonte (formato ID=Palavra):\n")
        for palavra, id_token in dicionario_rag.items():
            fd.write(f"{id_token}={palavra}\n")
            
    print(f"✓ Dicionário RAG gerado com {len(dicionario_rag)} termos críticos em: {caminho_dic}")
    print("-" * 80 + "\n")
    
    for root, dirs, files in os.walk(pasta_orig):
        for file in files:
            if eh_arquivo_de_teste(root, file, pasta_orig):
                continue
            if not ext_orig or file.endswith(ext_orig):
                caminho_orig = os.path.join(root, file)
                caminho_relativo = os.path.relpath(root, pasta_orig)
                
                arquivo_alvo = f"{file}{ext_comp}"
                diretorio_alvo = os.path.normpath(os.path.join(pasta_comp, caminho_relativo))
                os.makedirs(diretorio_alvo, exist_ok=True)
                caminho_comp_arquivo = os.path.join(diretorio_alvo, arquivo_alvo)
                path_visual = os.path.join(caminho_relativo, arquivo_alvo)
                
                try:
                    with open(caminho_orig, 'r', encoding='utf-8', errors='ignore') as f1:
                        conteudo_orig = f1.read()
                        
                    if file.endswith(".java") or file.endswith(".py") or file.endswith(".js"):
                        conteudo_comp = minificar_codigo_para_ia(conteudo_orig, dicionario_rag)
                    else:
                        conteudo_comp = re.sub(r'\s+', ' ', conteudo_orig).strip()
                        
                    with open(caminho_comp_arquivo, 'w', encoding='utf-8', errors='ignore') as f2:
                        f2.write(conteudo_comp)
                        
                    total_arquivos += 1
                    
                    chars_orig = len(conteudo_orig)
                    tokens_orig = estimar_tokens(conteudo_orig)
                    
                    chars_comp = len(conteudo_comp)
                    tokens_comp = estimar_tokens(conteudo_comp)
                    
                    total_tokens_orig += tokens_orig
                    total_tokens_comp += tokens_comp
                    
                    ter_orig = calcular_ter(tokens_orig, chars_orig)
                    ter_comp = calcular_ter(tokens_comp, chars_comp)
                    
                    print(f"📄 {path_visual}")
                    print(f"   [Original]   Chars: {chars_orig:6d} | Tokens: {tokens_orig:6d} | TER: {ter_orig:.2f}")
                    print(f"   [Modificado] Chars: {chars_comp:6d} | Tokens: {tokens_comp:6d} | TER: {ter_comp:.2f}")
                    print("-" * 80)
                except Exception as e:
                    print(f"Erro ao processar {file}: {e}")

    print("\n" + "=" * 80)
    print("📊 RESULTADO DO BENCHMARK")
    print("=" * 80)
    print(f"Pares validados e comparados : {total_arquivos}")
    
    if total_arquivos > 0:
        print(f"Total de Tokens (Original)   : {total_tokens_orig:,}")
        print(f"Total de Tokens (Modificado) : {total_tokens_comp:,}")
        
        if total_tokens_orig > 0:
            diferenca = ((total_tokens_comp - total_tokens_orig) / total_tokens_orig) * 100
        else:
            diferenca = 0
        economia_tokens = total_tokens_orig - total_tokens_comp
        
        print("\n" + "-" * 80)
        if diferenca < 0:
            print(f"✅ SUCESSO: O payload para a IA REDUZIU em {abs(diferenca):.2f}%")
            print(f"   Você economizou {economia_tokens:,} tokens por requisição/leitura nesta base.")
        else:
            print(f"⚠️  ALERTA DE CUSTO: O payload AUMENTOU em {diferenca:+.2f}%")
            print("   O formato dos arquivos modificados está inflando a janela de contexto.")
        print("-" * 80)
        
        caminho_const = os.path.join(pasta_comp, "CONSTITUTION.md")
        caminho_agents = os.path.join(pasta_comp, "AGENTS.MD")
        path_original = os.path.abspath(pasta_orig)
        
        # Cria CONSTITUTION.md
        with open(caminho_const, 'w', encoding='utf-8') as fs:
            fs.write("# 📜 CONSTITUIÇÃO DO AGENTE E REGRAS DE LEITURA (SYSTEM PROMPT)\n\n")
            fs.write(f"## 🎯 CONTEXTO DO PROJETO\n")
            fs.write(f"- **Diretório do Projeto Original:** `{path_original}`\n\n")
            fs.write("## 🎯 SUA PERSONA E OBJETIVO\n")
            fs.write("Você é uma Inteligência Artificial Sênior e Engenheira de Software de Elite. O código que você receberá neste diretório não é para humanos lerem; ele passou por um motor de **Minificação Extrema** para otimizar sua janela de contexto (Context Window). Seu objetivo é conseguir ler esse código desfigurado, entender a arquitetura perfeitamente e ajudar o usuário.\n\n")
            fs.write("## 🔍 COMO LER ESTE CÓDIGO (PARSER MENTAL):\n")
            fs.write("1. **Dicionário RAG (Variáveis Z):** Palavras-chave longas, classes e métodos repetidos foram substituídos por IDs como `Z1`, `Z2`. Consulte `dict.tkcd` para mapear de volta ao nome original.\n")
            fs.write("2. **Espaçamento e Símbolos Colapsados:** Espaços ao redor de operadores (`=`, `+`, `(`, `)`, `{`, `}`) foram brutalmente apagados. Seu parser interno deve conseguir ler esses símbolos colados perfeitamente.\n")
            fs.write("3. **Ocultação de Ruído (Syntax Stripping):** Modificadores (ex: `public`, `private`, `export`), palavras de contexto (`this.`, `self.`), tipagens desnecessárias e logs genéricos foram apagados para poupar tokens. O código exibe apenas o **comportamento puro**.\n\n")
            fs.write("## ⚠️ REGRAS RESTRITAS DE RESPOSTA:\n")
            fs.write("- **NUNCA DEVOLVA CÓDIGO MINIFICADO OU EM TOKENS:** Quando você sugerir refatorações, correções ou analisar a arquitetura, escreva **SEMPRE** em código limpo, perfeitamente indentado e humano.\n")
            fs.write("- **DESCOMPRESSÃO DE NOMES:** Suas respostas devem usar os nomes originais mapeados no arquivo `dict.tkcd` (ex: `TodoController`) e nunca as cifras (`Z1`).\n")
            fs.write("- **ARQUIVOS TKNK/TKCD:** Os arquivos terminados em `.tknc` contêm código minificado. O arquivo `dict.tkcd` contém a relação entre os IDs (`Z1`, `Z2`...) e seus valores originais.\n")
            fs.write("- **CONTEXTO DE EDIÇÃO E LEITURA:** Você deve ler este diretório para entender a arquitetura (usando `dict.tkcd` para descompressão), mas **qualquer alteração, refatoração ou sugestão de código deve ser baseada na estrutura do projeto original/principal (não minificado)** localizado em: `{path_original}`.\n")

        # Cria AGENTS.MD (um resumo operacional para o agente)
        with open(caminho_agents, 'w', encoding='utf-8') as fa:
            fa.write("# 🤖 AGENTS.MD\n\n")
            fa.write("Este projeto está otimizado para agentes via **Minificação Extrema**.\n\n")
            fa.write("### Workflow:\n")
            fa.write("1. **Leitura:** Consulte este diretório para entender o comportamento puro (código minificado).\n")
            fa.write("2. **Mapeamento:** Use `dict.tkcd` para descompactar variáveis (`Z1` -> `NomeReal`).\n")
            fa.write("3. **Execução/Edição:** Realize edições **apenas** no diretório original:\n")
            fa.write(f"   `{path_original}`\n")
            fa.write("\n⚠️ **NUNCA** edite arquivos nesta pasta de minificação. Eles são *read-only* para otimização de contexto.\n")

        print(f"\n🧠 Constituição e Agentes salvos em: {pasta_comp}")
            
        
    else:
        print("\n❌ Nenhum arquivo encontrado.")

def monitorar_projeto(pasta_orig, pasta_comp, ext_orig, ext_comp):
    print(f"\n👀 Iniciando monitoramento em: {pasta_orig}")
    print("Pressione Ctrl+C para parar.")
    
    arquivos_modificados = {}
    
    for root, _, files in os.walk(pasta_orig):
        for file in files:
            caminho = os.path.join(root, file)
            arquivos_modificados[caminho] = os.path.getmtime(caminho)
            
    while True:
        time.sleep(2)
        mudanca = False
        
        for root, _, files in os.walk(pasta_orig):
            for file in files:
                caminho = os.path.join(root, file)
                if not os.path.exists(caminho): continue
                
                mtime = os.path.getmtime(caminho)
                if caminho not in arquivos_modificados or mtime > arquivos_modificados[caminho]:
                    print(f"\n🔄 Mudança detectada: {file}")
                    arquivos_modificados[caminho] = mtime
                    mudanca = True
        
        if mudanca:
            processar_e_comparar(pasta_orig, pasta_comp, ext_orig, ext_comp)
            print("\n👀 Monitorando novamente...")

def main():
    print("\n======================================================")
    print("   🧠 LLM TOKEN BENCHMARK - COMPARAÇÃO E GERAÇÃO")
    print("======================================================\n")
    
    args = sys.argv[1:]
    if not args:
        print("❌ Erro: Por favor, forneça o caminho do diretório original.")
        print("Uso: python motor_v2.py <caminho_da_pasta> [--watch] [caminho_destino_opcional]")
        return
        
    watch_mode = "--watch" in args
    if watch_mode:
        args.remove("--watch")

    pasta_orig = os.path.abspath(args[0])
    
    if not os.path.isdir(pasta_orig):
        print(f"❌ Erro: Diretório ORIGINAL não encontrado: {pasta_orig}")
        return
    
    ext_orig = ".java"
    ext_comp = ".tknc"

    if len(args) > 1:
        pasta_comp = os.path.abspath(args[1])
    else:
        pasta_comp = pasta_orig.rstrip(os.sep) + "_mimificado"
        
    os.makedirs(pasta_comp, exist_ok=True)
        
    if watch_mode:
        monitorar_projeto(pasta_orig, pasta_comp, ext_orig, ext_comp)
    else:
        print("\n🔍 Analisando e processando as duas pastas...\n")
        processar_e_comparar(pasta_orig, pasta_comp, ext_orig, ext_comp)
        print("\nEncerrando ferramenta.")

if __name__ == "__main__":
    main()