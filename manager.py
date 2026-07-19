


import os
import sys
import subprocess
from pathlib import Path
from typing import Optional


class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def clear_screen():
    
    os.system('clear' if os.name != 'nt' else 'cls')


def print_header():
    
    print(f"\n{Colors.BOLD}{Colors.CYAN}")
    print("╔═══════════════════════════════════════════════════════════╗")
    print("║          🎯 TOKEN COMPILATION MANAGER 1.0                 ║")
    print("║         Menu Interativo - Gerenciador de Tokens           ║")
    print("╚═══════════════════════════════════════════════════════════╝")
    print(f"{Colors.END}\n")


def print_menu():
    
    print(f"{Colors.BOLD}{Colors.BLUE}[MENU PRINCIPAL]{Colors.END}\n")
    print(f"  {Colors.GREEN}1{Colors.END} - 📦 Compilar arquivo individual")
    print(f"  {Colors.GREEN}2{Colors.END} - 📁 Compilar todos os arquivos da pasta")
    print(f"  {Colors.GREEN}3{Colors.END} - 👀 Compilar e monitorar alterações")
    print(f"  {Colors.GREEN}4{Colors.END} - 🔄 Descompilar arquivo (.tknc)")
    print(f"  {Colors.GREEN}5{Colors.END} - 📊 Ver estatísticas de compilação")
    print(f"  {Colors.GREEN}6{Colors.END} - ⚙️  Opções avançadas")
    print(f"  {Colors.GREEN}7{Colors.END} - 🔁 Iniciar modo Sync Bidirecional")
    print(f"  {Colors.GREEN}0{Colors.END} - ❌ Sair")
    print()


def print_advanced_menu():
    
    print(f"\n{Colors.BOLD}{Colors.BLUE}[OPÇÕES AVANÇADAS]{Colors.END}\n")
    print(f"  {Colors.GREEN}1{Colors.END} - 📦 Compilar com IDs em base alfanumérica (-balpha)")
    print(f"  {Colors.GREEN}2{Colors.END} - 👀 Monitorar com base alfanumérica (-balpha -watch)")
    print(f"  {Colors.GREEN}3{Colors.END} - 🔍 Inspecionar arquivo compilado")
    print(f"  {Colors.GREEN}4{Colors.END} - 🆔 Buscar palavra por ID (-find-id)")
    print(f"  {Colors.GREEN}5{Colors.END} - 🔤 Buscar ID por palavra (-find-word)")
    print(f"  {Colors.GREEN}6{Colors.END} - ➕ Adicionar palavras ao dicionário (-add-words)")
    print(f"  {Colors.GREEN}7{Colors.END} - 📋 Ver ajuda completa")
    print(f"  {Colors.GREEN}0{Colors.END} - 🔙 Voltar ao menu principal")
    print()


def get_user_choice(prompt: str = "Escolha uma opção: ") -> str:
    
    try:
        choice = input(f"{Colors.YELLOW}{prompt}{Colors.END}").strip()
        return choice
    except KeyboardInterrupt:
        print(f"\n{Colors.RED}✗ Operação cancelada pelo usuário.{Colors.END}")
        return "999"


def get_file_path(prompt: str = "Digite o caminho do arquivo: ") -> Optional[Path]:
    
    try:
        path_str = input(f"{Colors.YELLOW}{prompt}{Colors.END}").strip()
        path = Path(path_str).expanduser()
        
        if not path.exists():
            print(f"{Colors.RED}✗ Caminho não encontrado: {path}{Colors.END}")
            return None
        
        return path
    except KeyboardInterrupt:
        print(f"\n{Colors.RED}✗ Operação cancelada.{Colors.END}")
        return None


def run_token_script(args: list[str]) -> int:
    
    try:
        token_script = Path(__file__).parent / "token.py"
        cmd = ["python", str(token_script)] + args
        result = subprocess.run(cmd, capture_output=False)
        return result.returncode
    except Exception as e:
        print(f"{Colors.RED}✗ Erro ao executar token.py: {e}{Colors.END}")
        return 1


def compile_single_file():
    
    print(f"\n{Colors.BOLD}{Colors.CYAN}[COMPILAR ARQUIVO INDIVIDUAL]{Colors.END}\n")
    file_path = get_file_path("Digite o caminho do arquivo: ")
    
    if not file_path:
        return
    
    if not file_path.is_file():
        print(f"{Colors.RED}✗ Caminho deve ser um arquivo, não uma pasta.{Colors.END}")
        return
    
    print(f"\n{Colors.GREEN}⏳ Compilando {file_path.name}...{Colors.END}\n")
    run_token_script([str(file_path)])
    
    print(f"\n{Colors.GREEN}✓ Compilação concluída!{Colors.END}")


def compile_directory():
    
    print(f"\n{Colors.BOLD}{Colors.CYAN}[COMPILAR PASTA]{Colors.END}\n")
    dir_path = get_file_path("Digite o caminho da pasta: ")
    
    if not dir_path:
        return
    
    if not dir_path.is_dir():
        print(f"{Colors.RED}✗ Caminho deve ser uma pasta, não um arquivo.{Colors.END}")
        return
    
    print(f"\n{Colors.GREEN}⏳ Compilando todos os arquivos em {dir_path}...{Colors.END}\n")
    run_token_script([str(dir_path)])
    
    print(f"\n{Colors.GREEN}✓ Compilação concluída!{Colors.END}")


def compile_with_watch():
    
    print(f"\n{Colors.BOLD}{Colors.CYAN}[COMPILAR E MONITORAR]{Colors.END}\n")
    dir_path = get_file_path("Digite o caminho da pasta: ")
    
    if not dir_path:
        return
    
    if not dir_path.is_dir():
        print(f"{Colors.RED}✗ Caminho deve ser uma pasta, não um arquivo.{Colors.END}")
        return
    
    print(f"\n{Colors.GREEN}⏳ Iniciando monitoramento em {dir_path}...{Colors.END}")
    print(f"{Colors.YELLOW}Pressione Ctrl+C para parar o monitoramento.{Colors.END}\n")
    
    try:
        run_token_script([str(dir_path), "-watch"])
    except KeyboardInterrupt:
        print(f"\n{Colors.RED}✓ Monitoramento interrompido.{Colors.END}")


def start_sync_mode():
    
    print(f"\n{Colors.BOLD}{Colors.CYAN}[SYNC BIDIRECIONAL]{Colors.END}\n")
    dir_path = get_file_path("Digite o caminho da pasta: ")
    
    if not dir_path:
        return
    
    if not dir_path.is_dir():
        print(f"{Colors.RED}✗ Caminho deve ser uma pasta, não um arquivo.{Colors.END}")
        return
    
    print(f"\n{Colors.GREEN}⏳ Iniciando sync bidirecional em {dir_path}...{Colors.END}")
    print(f"{Colors.YELLOW}Pressione Ctrl+C para parar o sync.{Colors.END}\n")
    
    try:
        run_token_script([str(dir_path), "-sync"])
    except KeyboardInterrupt:
        print(f"\n{Colors.RED}✓ Sync interrompido.{Colors.END}")


def decompress_file():
    
    print(f"\n{Colors.BOLD}{Colors.CYAN}[DESCOMPILAR ARQUIVO]{Colors.END}\n")
    file_path = get_file_path("Digite o caminho do arquivo .tknc: ")
    
    if not file_path:
        return
    
    if not file_path.is_file():
        print(f"{Colors.RED}✗ Caminho deve ser um arquivo.{Colors.END}")
        return
    
    if file_path.suffix != ".tknc":
        print(f"{Colors.RED}✗ Arquivo deve ter extensão .tknc (recebido: {file_path.suffix}){Colors.END}")
        return
    
    
    tknd_path = file_path.parent / f"{file_path.stem}.tknd"
    if not tknd_path.exists():
        current = file_path.parent
        found = False
        while current != current.parent:
            if (current / "dictionary.tknd").exists():
                tknd_path = current / "dictionary.tknd"
                found = True
                break
            current = current.parent
        if not found and not tknd_path.exists():
            print(f"{Colors.RED}✗ Dicionário não encontrado: {tknd_path.name} nem dictionary.tknd{Colors.END}")
            return
    
    print(f"\n{Colors.GREEN}⏳ Descompilando {file_path.name}...{Colors.END}\n")
    run_token_script([str(file_path), "-decompress"])
    
    
    original_path = file_path.parent / file_path.stem
    if original_path.exists():
        print(f"\n{Colors.GREEN}✓ Arquivo descompilado: {original_path}{Colors.END}")
    else:
        print(f"\n{Colors.YELLOW}⚠️  Arquivo descompilado pode ter sido salvo com outro nome.{Colors.END}")


def show_compression_stats():
    
    print(f"\n{Colors.BOLD}{Colors.CYAN}[ESTATÍSTICAS DE COMPILAÇÃO]{Colors.END}\n")
    
    dir_path = get_file_path("Digite o caminho da pasta compilado (ex: ./compilado): ")
    
    if not dir_path:
        return
    
    if not dir_path.is_dir():
        print(f"{Colors.RED}✗ Caminho deve ser uma pasta.{Colors.END}")
        return
    
    
    relatorio_files = list(dir_path.glob("*.relatorio.txt"))
    
    if not relatorio_files:
        print(f"{Colors.YELLOW}⚠️  Nenhum arquivo de relatório encontrado em {dir_path}{Colors.END}")
        return
    
    print(f"\n{Colors.GREEN}📊 Encontrados {len(relatorio_files)} arquivo(s) de relatório:\n{Colors.END}")
    
    total_original = 0
    total_compressed = 0
    
    for relatorio in sorted(relatorio_files):
        try:
            with open(relatorio, "r", encoding="utf-8") as f:
                content = f.read()
            
            
            lines = content.split('\n')
            original_size = 0
            compressed_size = 0
            
            for line in lines:
                if "Tamanho Original:" in line:
                    original_size = int(line.split(":")[-1].strip().split()[0])
                elif "Tamanho Comprimido:" in line:
                    compressed_size = int(line.split(":")[-1].strip().split()[0])
            
            if original_size > 0:
                ratio = ((original_size - compressed_size) / original_size * 100)
                total_original += original_size
                total_compressed += compressed_size
                
                print(f"  {Colors.CYAN}{relatorio.stem}{Colors.END}")
                print(f"    Original:   {Colors.YELLOW}{original_size:>8}{Colors.END} bytes")
                print(f"    Comprimido: {Colors.GREEN}{compressed_size:>8}{Colors.END} bytes")
                print(f"    Redução:    {Colors.BOLD}{ratio:>7.2f}%{Colors.END}")
                print()
        except Exception as e:
            print(f"  {Colors.RED}✗ Erro ao ler {relatorio}: {e}{Colors.END}\n")
    
    if total_original > 0:
        total_ratio = ((total_original - total_compressed) / total_original * 100)
        print(f"  {Colors.BOLD}{Colors.BLUE}─ TOTAL ─{Colors.END}")
        print(f"    Original:   {Colors.YELLOW}{total_original:>8}{Colors.END} bytes")
        print(f"    Comprimido: {Colors.GREEN}{total_compressed:>8}{Colors.END} bytes")
        print(f"    Redução:    {Colors.BOLD}{total_ratio:>7.2f}%{Colors.END}\n")


def inspect_compiled_file():
    
    print(f"\n{Colors.BOLD}{Colors.CYAN}[INSPECIONAR ARQUIVO COMPILADO]{Colors.END}\n")
    
    file_path = get_file_path("Digite o caminho do arquivo .tknc: ")
    
    if not file_path:
        return
    
    if file_path.suffix != ".tknc":
        print(f"{Colors.RED}✗ Arquivo deve ter extensão .tknc.{Colors.END}")
        return
    
    tknd_path = file_path.parent / f"{file_path.stem}.tknd"
    if not tknd_path.exists():
        current = file_path.parent
        found = False
        while current != current.parent:
            if (current / "dictionary.tknd").exists():
                tknd_path = current / "dictionary.tknd"
                found = True
                break
            current = current.parent
        if not found and not tknd_path.exists():
            print(f"{Colors.RED}✗ Dicionário não encontrado: {tknd_path.name} nem dictionary.tknd{Colors.END}")
            return
    
    
    try:
        with open(tknd_path, "r", encoding="utf-8") as f:
            dictionary = f.readlines()
        
        print(f"\n{Colors.GREEN}📋 Informações do Arquivo Compilado:{Colors.END}\n")
        print(f"  Arquivo Compilado: {Colors.CYAN}{file_path.name}{Colors.END}")
        print(f"  Tamanho:           {Colors.YELLOW}{file_path.stat().st_size}{Colors.END} bytes")
        
        print(f"\n  Dicionário: {Colors.CYAN}{tknd_path.name}{Colors.END}")
        print(f"  Palavras únicas: {Colors.GREEN}{len(dictionary)}{Colors.END}")
        
        print(f"\n{Colors.BOLD}  Primeiras 20 entradas do dicionário:{Colors.END}\n")
        for i, line in enumerate(dictionary[:20], 1):
            id_val, word = line.strip().split(",", 1)
            print(f"    {Colors.YELLOW}{id_val:>3}{Colors.END} → {Colors.CYAN}{word}{Colors.END}")
        
        if len(dictionary) > 20:
            print(f"\n    {Colors.YELLOW}... e {len(dictionary) - 20} outras palavras{Colors.END}\n")
        
    except Exception as e:
        print(f"{Colors.RED}✗ Erro ao inspecionar: {e}{Colors.END}")


def find_id_in_dict():
    
    print(f"\n{Colors.BOLD}{Colors.CYAN}[BUSCAR PALAVRA POR ID]{Colors.END}\n")
    tknd_path = get_file_path("Digite o caminho do arquivo .tknd: ")
    if not tknd_path: return
    target_id = input(f"{Colors.YELLOW}Digite o ID para buscar: {Colors.END}").strip()
    if not target_id: return
    run_token_script([str(tknd_path), "-find-id", target_id])


def find_word_in_dict():
    
    print(f"\n{Colors.BOLD}{Colors.CYAN}[BUSCAR ID POR PALAVRA]{Colors.END}\n")
    tknd_path = get_file_path("Digite o caminho do arquivo .tknd: ")
    if not tknd_path: return
    target_word = input(f"{Colors.YELLOW}Digite a palavra para buscar: {Colors.END}").strip()
    if not target_word: return
    run_token_script([str(tknd_path), "-find-word", target_word])


def add_custom_words():
    
    print(f"\n{Colors.BOLD}{Colors.CYAN}[ADICIONAR PALAVRAS AO DICIONÁRIO]{Colors.END}\n")
    
    file_path = input(f"{Colors.YELLOW}Digite o caminho do arquivo .tknd (existente ou novo): {Colors.END}").strip()
    
    if not file_path:
        return
    
    path = Path(file_path).expanduser()
    if path.suffix != ".tknd":
        print(f"{Colors.RED}✗ Caminho deve ser um arquivo com extensão .tknd.{Colors.END}")
        return
    
    words_input = input(f"{Colors.YELLOW}Digite as palavras separadas por vírgula: {Colors.END}").strip()
    
    if not words_input:
        print(f"{Colors.RED}✗ Nenhuma palavra fornecida.{Colors.END}")
        return
        
    print(f"\n{Colors.GREEN}⏳ Adicionando palavras ao dicionário...{Colors.END}\n")
    run_token_script([str(path), "-add-words", words_input])


def show_help():
    
    print(f"\n{Colors.BOLD}{Colors.CYAN}[AJUDA COMPLETA]{Colors.END}\n")
    print(f"{Colors.BOLD}TOKEN COMPILATION MANAGER{Colors.END}")
    print("Menu interativo para compilação e gerenciamento de tokens\n")
    
    print(f"{Colors.BOLD}USO DO SCRIPT PRINCIPAL (token.py):{Colors.END}\n")
    print("  python token.py [-balpha] [-watch] [-decompress] arquivo_ou_pasta\n")
    
    print(f"{Colors.BOLD}OPÇÕES:{Colors.END}")
    print(f"  {Colors.GREEN}-balpha{Colors.END}      Usar IDs em base alfanumérica (0-9, A-Z)")
    print(f"  {Colors.GREEN}-watch{Colors.END}       Monitorar alterações em tempo real")
    print(f"  {Colors.GREEN}-decompress{Colors.END}  Descompilar arquivo .tknc\n")
    print(f"  {Colors.GREEN}-find-id ID{Colors.END}  Buscar palavra por ID em dicionário\n")
    print(f"  {Colors.GREEN}-find-word PALAVRA{Colors.END} Buscar ID por palavra em dicionário\n")
    print(f"  {Colors.GREEN}-add-words P1,P2{Colors.END} Adicionar lista de palavras ao dicionário\n")
    
    print(f"{Colors.BOLD}EXEMPLOS:{Colors.END}")
    print("  python token.py Calculator.java")
    print("  python token.py . -watch")
    print("  python token.py Calculator.java.tknc -decompress")
    print("  python token.py Calculator.java.tknd -find-id 17")
    print("  python token.py Calculator.java.tknd -find-word Calculator")
    print("  python token.py . -balpha -watch\n")
    print("  python token.py main.tknd -add-words list,dict,set\n")
    
    print(f"{Colors.BOLD}ARQUIVOS GERADOS:{Colors.END}")
    print(f"  {Colors.CYAN}.tknc{Colors.END}       Arquivo compilado (código com números)")
    print(f"  {Colors.CYAN}.tknd{Colors.END}       Dicionário (mapa ID → palavra)")
    print(f"  {Colors.CYAN}.relatorio.txt{Colors.END}  Estatísticas de compressão\n")
    
    print(f"{Colors.BOLD}FLUXO TÍPICO:{Colors.END}")
    print("  1. Compilar arquivo → Gera .tknc + .tknd")
    print("  2. Analisar estrutura → Use arquivo .tknc + .tknd")
    print("  3. Descompilar → Recupera código original\n")


def advanced_menu():
    
    while True:
        clear_screen()
        print_header()
        print_advanced_menu()
        
        choice = get_user_choice()
        
        if choice == "1":
            print(f"\n{Colors.BOLD}{Colors.CYAN}[COMPILAR COM BASE ALFANUMÉRICA]{Colors.END}\n")
            file_path = get_file_path("Digite o caminho (arquivo ou pasta): ")
            
            if file_path:
                print(f"\n{Colors.GREEN}⏳ Compilando com -balpha...{Colors.END}\n")
                run_token_script([str(file_path), "-balpha"])
                print(f"\n{Colors.GREEN}✓ Compilação concluída!{Colors.END}")
                input(f"\n{Colors.YELLOW}Pressione Enter para continuar...{Colors.END}")
        
        elif choice == "2":
            print(f"\n{Colors.BOLD}{Colors.CYAN}[COMPILAR E MONITORAR COM BASE ALFANUMÉRICA]{Colors.END}\n")
            dir_path = get_file_path("Digite o caminho da pasta: ")
            
            if dir_path and dir_path.is_dir():
                print(f"\n{Colors.GREEN}⏳ Compilando com -balpha -watch...{Colors.END}")
                print(f"{Colors.YELLOW}Pressione Ctrl+C para parar.{Colors.END}\n")
                try:
                    run_token_script([str(dir_path), "-balpha", "-watch"])
                except KeyboardInterrupt:
                    print(f"\n{Colors.RED}✓ Monitoramento interrompido.{Colors.END}")
        
        elif choice == "3":
            inspect_compiled_file()
            input(f"\n{Colors.YELLOW}Pressione Enter para continuar...{Colors.END}")
        
        elif choice == "4":
            find_id_in_dict()
            input(f"\n{Colors.YELLOW}Pressione Enter para continuar...{Colors.END}")
            
        elif choice == "5":
            find_word_in_dict()
            input(f"\n{Colors.YELLOW}Pressione Enter para continuar...{Colors.END}")
            
        elif choice == "6":
            add_custom_words()
            input(f"\n{Colors.YELLOW}Pressione Enter para continuar...{Colors.END}")
            
        elif choice == "7":
            show_help()
            input(f"\n{Colors.YELLOW}Pressione Enter para continuar...{Colors.END}")
        
        elif choice == "0":
            break
        
        else:
            print(f"{Colors.RED}✗ Opção inválida!{Colors.END}")
            input(f"\n{Colors.YELLOW}Pressione Enter para continuar...{Colors.END}")


def main():
    
    while True:
        clear_screen()
        print_header()
        print_menu()
        
        choice = get_user_choice()
        
        if choice == "1":
            compile_single_file()
            input(f"\n{Colors.YELLOW}Pressione Enter para continuar...{Colors.END}")
        
        elif choice == "2":
            compile_directory()
            input(f"\n{Colors.YELLOW}Pressione Enter para continuar...{Colors.END}")
        
        elif choice == "3":
            compile_with_watch()
            input(f"\n{Colors.YELLOW}Pressione Enter para continuar...{Colors.END}")
        
        elif choice == "4":
            decompress_file()
            input(f"\n{Colors.YELLOW}Pressione Enter para continuar...{Colors.END}")
        
        elif choice == "5":
            show_compression_stats()
            input(f"\n{Colors.YELLOW}Pressione Enter para continuar...{Colors.END}")
        
        elif choice == "6":
            advanced_menu()
            
        elif choice == "7":
            start_sync_mode()
            input(f"\n{Colors.YELLOW}Pressione Enter para continuar...{Colors.END}")
        
        elif choice == "0":
            print(f"\n{Colors.GREEN}✓ Até logo!{Colors.END}\n")
            sys.exit(0)
        
        else:
            print(f"{Colors.RED}✗ Opção inválida!{Colors.END}")
            input(f"\n{Colors.YELLOW}Pressione Enter para continuar...{Colors.END}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Colors.RED}✗ Programa interrompido.{Colors.END}\n")
        sys.exit(1)
