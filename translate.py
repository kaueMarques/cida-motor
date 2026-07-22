import os
import sys
import json

def reject_duplicate_keys(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"Duplicate JSON key: {key}")
        result[key] = value
    return result

def translate(tokens, tknd_dir):
    mapping = {}
    if not os.path.exists(tknd_dir):
        print(f"Erro: Pasta {tknd_dir} não encontrada.", file=sys.stderr)
        sys.exit(5)
    
    for file in os.listdir(tknd_dir):
        if file.endswith(".cidatkn"):
            try:
                with open(os.path.join(tknd_dir, file), 'r', encoding='utf-8') as f:
                    data = json.load(f, object_pairs_hook=reject_duplicate_keys)
                    if isinstance(data, dict) and "entries" in data:
                        for alias, val in data["entries"].items():
                            mapping[alias] = val
            except Exception as e:
                print(f"Erro ao ler dicionário {file}: {e}", file=sys.stderr)
                sys.exit(5)
    
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

