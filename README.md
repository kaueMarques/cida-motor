# CIDA Motor
### Companheira de Desenvolvimento com IA

![Go](https://img.shields.io/badge/Language-Go-blue)
![Python](https://img.shields.io/badge/Language-Python-yellow)

Ferramenta CLI para tokenização, minificação e compressão de projetos ou arquivos de texto.

## Funcionalidades Principais

*   **Compilação (Minificação/Tokenização):** Compacta arquivos individuais, pastas inteiras ou monitora diretórios para compilação em tempo real.
*   **Descompilação:** Recupera o código/texto original a partir de arquivos compilados.
*   **Gestão de Dicionário:** Busca rápida de IDs por palavras, palavras por IDs e adição de novas palavras ao dicionário de tokens.
*   **Estatísticas:** Visualize o ratio de compressão e ganho de espaço.
*   **Inspeção:** Analise a estrutura dos arquivos compilados.

## Como Usar

O projeto utiliza o `motor_v3.go` como motor de processamento principal.

### Execução

Para rodar a versão em Go, utilize o comando:

```bash
go run motor_v3.go <pasta_original> [pasta_destino] [--watcher]
```

*   `<pasta_original>`: Caminho da pasta que contém o código a ser minificado/tokenizado.
*   `[pasta_destino]`: (Opcional) Pasta onde os arquivos processados serão salvos. Se omitido, será criada uma pasta com o nome `[pasta_original]_mimificado`.
*   `[--watcher]`: (Opcional) Ativa o modo de monitoramento (watcher) em tempo real, recompilando automaticamente ao detectar alterações.

## Como utilizar com IA

Após a conclusão da minificação:

1. Acesse a pasta de destino gerada (ex: `pasta_mimificada`).
2. Utilize o arquivo `PROMPT_INICIAL.MD` encontrado dentro desta pasta como contexto inicial ou prompt de sistema no seu CLI de LLM.
3. Isso garante que a IA compreenda a estrutura tokenizada e o contexto técnico necessário para processar o código minificado.

## Estrutura do Projeto

*   `motor_v3.go`: Motor principal de processamento (versão Go de alta performance).
*   `motor_v2.py`: Versão legada do motor de processamento (Py).
*   `md_minifier.py`: Módulo específico para minificação de arquivos Markdown.
*   `token_counter.py` / `token.py`: Lógica relacionada à contagem e gestão de tokens.
*   `tests/`: Suite de testes para garantir a integridade da tokenização e minificação.
