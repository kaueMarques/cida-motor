# Especificação: Minificador de Markdown

## Objetivo
Reduzir de forma monotônica os tokens de documentos Markdown (usando o codificador `cl100k_base` do `tiktoken`) mantendo a validade semântica e sem corromper regiões técnicas.

## Comportamento Esperado
- **Monotonicidade:** Qualquer modificação só é aceita se o total de tokens do arquivo final (incluindo qualquer dicionário de escopo de arquivo) for menor que o original.
- **Normalização de Espaço:**
  - Remoção de espaços em branco ao final das linhas.
  - Normalização de espaçamentos em tabelas.
  - Redução de múltiplas linhas em branco para no máximo uma (entre blocos).
- **Remoção de Comentários:** Remoção de comentários HTML (`<!-- ... -->`) não operacionais.
- **Dicionário RAG por Tokens:**
  - Substituição de termos recorrentes por aliases curtos em tokens (ex: `AA`, `AB`).
  - Geração de aliases de custo real otimizado.
  - Cálculo de ganho líquido (`ganho_bruto - custo_entrada_dicionario`).
- **Validação Semântica:** A estrutura de títulos (nível, ordem) e de listas (hierarquia) deve ser validada após a minificação para garantir integridade.
