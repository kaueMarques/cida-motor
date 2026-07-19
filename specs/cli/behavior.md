# Especificação: CLI (Motor de Minificação)

## Objetivo
Interface de linha de comando para invocar o motor de minificação e monitoramento.

## Comportamento Esperado
- **Entrada:** Receber o caminho do diretório original como argumento obrigatório.
- **Saída:** Gerar a pasta minificada (opcional ou padrão sufixado com `_mimificado`).
- **Modo Watcher:** Suportar a flag `--watcher` (ou `-watch`) para monitorar mudanças no diretório original e re-executar a minificação.
- **Feedback:** Deve imprimir o progresso da análise e os resultados do benchmark (tokens originais vs minificados, economia).
