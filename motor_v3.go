package main

import (
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"regexp"
	"sort"
	"strconv"
	"strings"
	"sync"
	"sync/atomic"
	"time"
)
func getB16ID(n int) string {
	prefixChars := "ABCDEF"
	allChars := "0123456789ABCDEF"

	if n < len(prefixChars) {
		return string(prefixChars[n])
	}

	n -= len(prefixChars)
	// Formato de 2 caracteres (A0, A1... FF)
	if n < 6*16 {
		return string(prefixChars[n/16]) + string(allChars[n%16])
	}

	n -= 6 * 16
	// Formato de 3 caracteres (garantindo prefixo A-F)
	prefixIdx := (n / 256) % 6
	if prefixIdx < 0 {
		prefixIdx = 0
	} else if prefixIdx >= len(prefixChars) {
		prefixIdx = len(prefixChars) - 1
	}
	return string(prefixChars[prefixIdx]) + string(allChars[(n/16)%16]) + string(allChars[n%16])
}


func estimarTokens(texto string) int {
	if texto == "" {
		return 0
	}
	cmd := exec.Command("python3", "token_counter.py")
	cmd.Stdin = strings.NewReader(texto)
	out, err := cmd.Output()
	if err != nil {
		return 0
	}
	tokens, _ := strconv.Atoi(strings.TrimSpace(string(out)))
	return tokens
}

func calcularTER(tokens int, caracteres int) float64 {
	if caracteres > 0 {
		return float64(tokens) / float64(caracteres)
	}
	return 0
}

func ehArquivoDeTeste(root string, file string, pastaOrig string) bool {
	relPath, err := filepath.Rel(pastaOrig, root)
	if err != nil {
		return false
	}
	parts := strings.Split(strings.ToLower(relPath), string(os.PathSeparator))
	fileName := strings.ToLower(file)

	for _, p := range parts {
		if p == "test" || p == "tests" || p == "teste" || p == "testes" {
			return true
		}
	}
	return strings.Contains(fileName, "test") || strings.Contains(fileName, "teste")
}

func minificarCodigoParaIA(codigoFonte string, dicionario map[string]string) string {
	codigo := codigoFonte
	
	
	// Remove comments
	codigo = regexp.MustCompile(`(?s)/\*.*?\*/`).ReplaceAllString(codigo, "")
	codigo = regexp.MustCompile(`//.*`).ReplaceAllString(codigo, "")

	// Remove package/imports
	codigo = regexp.MustCompile(`package\s+[\w\.]+;`).ReplaceAllString(codigo, "")
	codigo = regexp.MustCompile(`import\s+(?:static\s+)?[\w\.\*]+;`).ReplaceAllString(codigo, "")

	// Remove annotations and common noise
	codigo = regexp.MustCompile(`@\w+(?:\([^)]*\))?\s*`).ReplaceAllString(codigo, "")
	codigo = regexp.MustCompile(`\b(System\.out\.\w+|console\.\w+|logger\.\w+|print|Log\.\w+|trace|debug|error|assert)\s*\([^)]*\);?`).ReplaceAllString(codigo, "")
	reStrings := regexp.MustCompile(`"(?:[^"\\]|\\.)*"|'(?:[^'\\]|\\.)*'`)
	codigo = reStrings.ReplaceAllStringFunc(codigo, func(s string) string {
		if len(s) > 15 {
			return `""`
		}
		return s
	})
	codigo = regexp.MustCompile(`\b(public|private|protected|export|final|volatile|strictfp)\s+`).ReplaceAllString(codigo, "")
	codigo = regexp.MustCompile(`\b(this|self)\.`).ReplaceAllString(codigo, "")

	// Compact
	codigo = regexp.MustCompile(`\s+`).ReplaceAllString(codigo, " ")
	codigo = regexp.MustCompile(`\s*([+\-*/%&|<>!^~?:;,{}()\[\]=]+)\s*`).ReplaceAllString(codigo, "$1")

	
	type kv struct {
		Key   string
		Value string
	}
	var ss []kv
	for k, v := range dicionario {
		ss = append(ss, kv{k, v})
	}
	sort.Slice(ss, func(i, j int) bool {
		return len(ss[i].Key) > len(ss[j].Key)
	})

	for _, kv := range ss {
		rePalavra := regexp.MustCompile(`\b` + regexp.QuoteMeta(kv.Key) + `\b`)
		codigo = rePalavra.ReplaceAllString(codigo, kv.Value)
	}

	return strings.TrimSpace(codigo)
}

func main() {
	if len(os.Args) < 2 {
		fmt.Println("Uso: motor_v3 <pasta_original> [pasta_destino] [--watcher]")
		return
	}

	pastaOrig := os.Args[1]
	pastaComp := ""
	isWatcher := false

	for _, arg := range os.Args[2:] {
		if arg == "--watcher" || arg == "-watch" {
			isWatcher = true
		} else if pastaComp == "" {
			pastaComp = arg
		}
	}

	if pastaComp == "" {
		execPath, _ := os.Executable()
		execDir := filepath.Dir(execPath)
		pastaComp = filepath.Join(execDir, filepath.Base(pastaOrig)+"_mimificado")
	}

	fmt.Println("🚀 Iniciando Minificação (Go Version)")
	fmt.Printf("📂 Origem: %s\n📂 Destino: %s\n", pastaOrig, pastaComp)

	var files []string
	filepath.WalkDir(pastaOrig, func(path string, d os.DirEntry, err error) error {
		if err != nil { return nil }
		if d.IsDir() && path == pastaComp { return filepath.SkipDir }
		if !d.IsDir() {
			files = append(files, path)
		}
		return nil
	})

	if isWatcher {
		fmt.Println("👀 Modo Watcher ativado. Pressione Ctrl+C para sair.")
		var lastModTimes = make(map[string]time.Time)
		for {
			changed := false
			filepath.WalkDir(pastaOrig, func(path string, d os.DirEntry, err error) error {
				if err != nil { return nil }
				if d.IsDir() && path == pastaComp { return filepath.SkipDir }
				if !d.IsDir() {
					info, _ := d.Info()
					if t, ok := lastModTimes[path]; !ok || info.ModTime().After(t) {
						lastModTimes[path] = info.ModTime()
						changed = true
					}
				}
				return nil
			})

			if changed {
				fmt.Println("🔄 Alteração detectada, recompilando...")
				processarEComparar(pastaOrig, pastaComp)
			}
			time.Sleep(2 * time.Second)
		}
	} else {
		processarEComparar(pastaOrig, pastaComp)
	}
}

func processarEComparar(pastaOrig string, pastaComp string) {
	if _, err := os.Stat(pastaComp); os.IsNotExist(err) {
		fmt.Printf("📂 Criando pasta de destino: %s\n", pastaComp)
		os.MkdirAll(pastaComp, 0755)
		os.MkdirAll(filepath.Join(pastaComp, "tknd"), 0755)
		criarReadmeMinificado(pastaComp, pastaOrig)
		criarReadmeTknd(filepath.Join(pastaComp, "tknd"))
		gerarScriptTraducao(pastaComp)
	}

	fmt.Println("⏳ Analisando frequências e construindo dicionário de termos...")
	dicionario := construirDicionario(pastaOrig, pastaComp)

	var files []string
	filepath.WalkDir(pastaOrig, func(path string, d os.DirEntry, err error) error {
		if err != nil { return nil }
		if d.IsDir() && path == pastaComp { return filepath.SkipDir }
		if !d.IsDir() {
			files = append(files, path)
		}
		return nil
	})

	fmt.Printf("✓ Dicionário de termos gerado com %d termos críticos. Processando %d arquivos...\n", len(dicionario), len(files))

	var wg sync.WaitGroup
	var totalFiles = int64(len(files))
	var processedFiles int64 = 0
	jobs := make(chan string, len(files))

	numWorkers := 32
	for range numWorkers {
		wg.Add(1)
		go func() {
			defer wg.Done()
			for filePath := range jobs {
				relPath, _ := filepath.Rel(pastaOrig, filePath)
				destPath := filepath.Join(pastaComp, relPath) + ".tknc"
				os.MkdirAll(filepath.Dir(destPath), 0755)

				conteudo, _ := os.ReadFile(filePath)
				minificado := minificarCodigoParaIA(string(conteudo), dicionario)
				os.WriteFile(destPath, []byte(minificado), 0644)
				
				count := atomic.AddInt64(&processedFiles, 1)
				remaining := totalFiles - count
				fmt.Printf("\rProcessando: %d/%d (Faltam: %d arquivos)...", count, totalFiles, remaining)
			}
		}()
	}

	for _, file := range files {
		jobs <- file
	}
	close(jobs)

	// File generation moved into criarReadmeMinificado below
}

func criarReadmeMinificado(pastaDestino string, pastaOrigem string) {
	absPath, _ := filepath.Abs(pastaOrigem)
	conteudo := fmt.Sprintf(`# ⚠️ PROJETO MINIFICADO - SOMENTE LEITURA

Este diretório contém uma versão otimizada (minificada) do seu código, gerada automaticamente para reduzir drasticamente o consumo de tokens em modelos de linguagem (LLMs).

## 🚨 AVISO IMPORTANTE: Fluxo de Trabalho

1. LEIA APENAS ESTA PASTA (Minificada): Use os arquivos nesta pasta como contexto. Eles foram processados pelo motor de minificação e contêm o comportamento puro do sistema.

2. EDITE APENAS A PASTA ORIGINAL (Não Minificada): Todas as alterações, refatorações, correções de bugs e novas funcionalidades devem ser feitas exclusivamente na pasta fonte original:
   %s

3. NUNCA EDITE ARQUIVOS NESTA PASTA: Esta pasta é gerenciada por um motor automático. Qualquer alteração manual aqui será sobrescrita na próxima execução da compilação.

## 🤖 Orientações para a I.A.
- Ferramenta de Tradução (translate.py): Caso seja estritamente necessário entender um identificador, utilize o script 'translate.py' na raiz do projeto original. *AVISO: Use esta ferramenta apenas quando necessário e armazene a tradução em seu contexto imediato para evitar chamadas redundantes.*
- Edição: As sugestões de código devem ser baseadas na estrutura da pasta original.
`, absPath)
	
	os.WriteFile(filepath.Join(pastaDestino, "README_MINIFICADO.md"), []byte(conteudo), 0644)
	os.WriteFile(filepath.Join(pastaDestino, "CONSTITUTION.md"), []byte(getConstitutionContent()), 0644)
	os.WriteFile(filepath.Join(pastaDestino, "AGENTS.md"), []byte(getAgentsContent()), 0644)
	os.WriteFile(filepath.Join(pastaDestino, "PROMPT_INICIAL.MD"), []byte(getPromptInicialContent()), 0644)
}

func criarReadmeTknd(pastaTknd string) {
	conteudo := `# Diretório de Dicionários de Tokens (tknd)

Este diretório contém o mapeamento completo entre os identificadores ofuscados encontrados no código minificado e os seus nomes originais.

## Estrutura dos Arquivos
Os arquivos estão segmentados em blocos de 500 registros para facilitar a consulta pela I.A. 
Cada arquivo é nomeado de acordo com o identificador do primeiro token contido nele (ex: A0.tknd contém os mapeamentos de A0 a A1F3...).

## Como utilizar
Sempre que encontrar um identificador ofuscado (ex: A5), procure no arquivo correspondente dentro desta pasta para identificar sua função ou nome original.

## Ferramenta de Tradução (translate.py)
Para facilitar a tradução automática, utilize o script 'translate.py' disponível na raiz do projeto original passando os tokens como argumento.
Exemplo: python3 translate.py A0 B1
`
	os.WriteFile(filepath.Join(pastaTknd, "README.md"), []byte(conteudo), 0644)
}

func getPromptInicialContent() string {
	return `# Instruções Iniciais para a I.A.

A primeira coisa que você deve fazer ao receber este código é ler e compreender rigorosamente a **CONSTITUTION.md**, a **AGENTS.md** e o **README_MINIFICADO.md**.

## Regras de Comportamento após o Entendimento:
1. **Atuação:** Você não deve se referir a este projeto como um "projeto minificado" ou mencionar termos técnicos de ofuscação (B16, tokens) em suas respostas aos usuários.
2. **Abordagem:** Responda ao usuário como se estivesse lidando com um projeto de código fonte padrão, humano e legível. 
5. **Ferramenta de Tradução:** Caso seja estritamente necessário entender um identificador ofuscado, utilize o script 'translate.py' localizado na raiz do projeto original. *AVISO: Use esta ferramenta apenas quando necessário e armazene a tradução em seu contexto imediato para evitar chamadas redundantes.*
`
}

func getConstitutionContent() string {
	return `# Constituição do Motor de Minificação

## Regras de Funcionamento
1. Minificação Extrema: Remove ruídos, comentários, espaçamentos, tipagens desnecessárias e modificadores de acesso.
2. Mapeamento (Tokens B16): Termos críticos substituídos por IDs B16 (A0, A1... AF, B0...).
5. Ferramenta de Tradução (translate.py): Caso seja estritamente necessário entender um identificador, utilize o script 'translate.py' na raiz do projeto original passando o token como argumento. *AVISO: Armazene a tradução em seu contexto imediato para evitar chamadas redundantes.*
`
}

func getAgentsContent() string {
	return `# Agentes de Processamento

Este projeto está otimizado para agentes via Minificação Extrema.

## Regras de Consulta ao Dicionário
1. Leitura: Consulte esta pasta para entender o comportamento puro.
## Ferramenta de Tradução (translate.py)
Caso seja estritamente necessário entender um identificador, utilize o script 'translate.py' na raiz do projeto original passando o token como argumento.
*AVISO:* Use esta ferramenta apenas quando necessário e armazene a tradução em seu contexto imediato para evitar chamadas redundantes.

⚠️ NUNCA edite arquivos nesta pasta de minificação. Eles são read-only para otimização de contexto e serão sobrescritos.
`
}

func gerarScriptTraducao(pastaDestino string) {
	conteudo := `import os
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
        # Default para pasta tknd relativa ao executável ou diretório atual
        tknd_dir = os.path.join(os.getcwd(), "tknd")
        
        args = sys.argv[1:]
        if "--path" in args:
            idx = args.index("--path")
            if idx + 1 < len(args):
                tknd_dir = args[idx+1]
                args = args[:idx] + args[idx+2:]
        
        print(translate(args, tknd_dir))
`
	os.WriteFile(filepath.Join(pastaDestino, "translate.py"), []byte(conteudo), 0755)
}

func construirDicionario(pastaOrig string, pastaComp string) map[string]string {
	contador := make(map[string]int)
	rePalavras := regexp.MustCompile(`\b[a-zA-Z_]{6,}\b`)

	filepath.WalkDir(pastaOrig, func(path string, d os.DirEntry, err error) error {
		if err != nil || d.IsDir() { return nil }
		conteudo, _ := os.ReadFile(path)
		palavras := rePalavras.FindAllString(string(conteudo), -1)
		for _, p := range palavras { contador[p]++ }
		return nil
	})

	type kv struct { Key string; Freq int }
	var ss []kv
	for k, v := range contador { ss = append(ss, kv{k, v}) }
	sort.Slice(ss, func(i, j int) bool {
		return ss[i].Freq*len(ss[i].Key) > ss[j].Freq*len(ss[j].Key)
	})

	dicionario := make(map[string]string)
	
	// Gerar arquivos de bloco
	for i := 0; i < len(ss); i += 500 {
		end := i + 500
		if end > len(ss) {
			end = len(ss)
		}
		
		startID := getB16ID(i)
		fileName := fmt.Sprintf("%s.tknd", startID)
		file, _ := os.Create(filepath.Join(pastaComp, "tknd", fileName))
		
		for j := i; j < end; j++ {
			if ss[j].Freq >= 3 {
				token := getB16ID(j)
				dicionario[ss[j].Key] = token
				file.WriteString(fmt.Sprintf("%s=%s\n", token, ss[j].Key))
			}
		}
		file.Close()
	}
	return dicionario
}
