# Especificação: Perfil BMAD para Markdown

## Objetivo
Preservar o funcionamento semântico e operacional de workflows executados por agentes inteligentes baseados no framework BMAD.

## Regras de Preservação (Invariáveis)
- **Frontmatter YAML:** Manter intactos todas as propriedades e valores operacionais (como `stepsCompleted`, `workflowType`, `inputDocuments`, `nextStepFile`, `outputFile`). Somente espaços finais e linhas vazias redundantes podem ser otimizados.
- **Estruturas de Agente e Workflow:**
  - Preservar códigos de menus, personas e instruções do agente.
  - Manter caminhos de diretórios (como `steps-c/`, `_bmad/`, `_bmad-output/`) e placeholders de variáveis (ex: `{variable}`, `{{variable}}`, `${VARIABLE}`).
  - Não mesclar passos de workflows em um único arquivo, nem quebrar o carregamento progressivo de contexto.
- **Validação Semântica:** A árvore de títulos, links de arquivos (destinos), comandos de terminal e propriedades críticas do frontmatter devem permanecer inalterados ou equivalentes funcionalmente após a descompilação.
