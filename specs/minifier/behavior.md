# Especificação: Minificador de Código

## Objetivo
Transformar código-fonte humano em uma versão "minificada" para IAs, mantendo a semântica, mas reduzindo tokens.

## Comportamento Esperado
- **Remoção de Ruído:** Comentários (`/*...*/`, `//`), anotações (`@Annotation`), logs (`System.out...`) e modificadores desnecessários (`public`, `private`, etc.) devem ser removidos.
- **Espaçamento:** Espaços em branco devem ser reduzidos ao mínimo necessário para a validade sintática.
- **Minificação de Variáveis:** Nomes de classes e métodos longos identificados como críticos (frequência >= 3) devem ser substituídos por identificadores B16 (ex: A0, A1, ...).
- **Consistência:** O mapeamento dos identificadores deve ser salvo em `tknd/`.
