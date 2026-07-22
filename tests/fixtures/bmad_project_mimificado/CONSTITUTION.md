# Constituição do Motor de Minificação

## Regras de Funcionamento
1. Minificação Extrema: Remove ruídos, comentários, espaçamentos, tipagens desnecessárias e modificadores de acesso.
2. Mapeamento (Tokens B16): Termos críticos substituídos por IDs B16 (A0, A1... AF, B0...).
5. Ferramenta de Tradução (translate.py): Caso seja estritamente necessário entender um identificador, utilize o script 'translate.py' na raiz do projeto original passando o token como argumento. *AVISO: Armazene a tradução em seu contexto imediato para evitar chamadas redundantes.*
