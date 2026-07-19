# AI Compiler

Ferramenta CLI para tokenização, minificação e compressão de projetos ou arquivos de texto.

## Funcionalidades Principais

*   **Compilação (Minificação/Tokenização):** Compacta arquivos individuais, pastas inteiras ou monitora diretórios para compilação em tempo real.
*   **Descompilação:** Recupera o código/texto original a partir de arquivos compilados.
*   **Gestão de Dicionário:** Busca rápida de IDs por palavras, palavras por IDs e adição de novas palavras ao dicionário de tokens.
*   **Estatísticas:** Visualize o ratio de compressão e ganho de espaço.
*   **Inspeção:** Analise a estrutura dos arquivos compilados.

## Como Usar

O projeto utiliza `manager.py` como interface principal. Execute o script para acessar o menu interativo:

```bash
python3 manager.py
```

Siga as instruções na tela para navegar entre as opções de compilação, descompilação e gestão do dicionário.

## Estrutura do Projeto

*   `manager.py`: Interface de linha de comando (CLI) principal.
*   `motor_v3` / `motor_v2.py`: Núcleos de processamento e lógica de compilação/decompilação.
*   `md_minifier.py`: Módulo específico para minificação de arquivos Markdown.
*   `token_counter.py` / `token.py`: Lógica relacionada à contagem e gestão de tokens.
*   `tests/`: Suite de testes para garantir a integridade da tokenização e minificação.
