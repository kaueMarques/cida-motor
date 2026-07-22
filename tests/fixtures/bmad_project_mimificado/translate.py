import os
import sys

def translate(tokens, tknd_dir):
    mapping = {}
    if not os.path.exists(tknd_dir):
        return f"Erro: Pasta {tknd_dir} não encontrada."
    
    for file in os.listdir(tknd_dir):
        if file.endswith(".tknd"):
            with open(os.path.join(tknd_dir, file), 'r', encoding='utf-8') as f:
                for line in f:
                    parts = line.strip().split('=')
                    if len(parts) == 2:
                        mapping[parts[0]] = parts[1]
    
    results = {}
    for t in tokens:
        results[t] = mapping.get(t, "Não encontrado")
    return results

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python3 translate.py [ID1] [ID2] ... [--path <caminho_da_pasta_tknd>]")
    else:
        tknd_dir = os.path.join(os.getcwd(), "tknd")
        
        args = sys.argv[1:]
        if "--path" in args:
            idx = args.index("--path")
            if idx + 1 < len(args):
                tknd_dir = args[idx+1]
                args = args[:idx] + args[idx+2:]
        
        print(translate(args, tknd_dir))
