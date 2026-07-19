# Especificação: Tokenizador

## Objetivo
Calcular a quantidade de tokens de um texto, utilizando o motor de contagem (tiktoken).

## Comportamento Esperado
- O motor deve ser capaz de receber texto via stdin e retornar o número inteiro de tokens.
- Deve utilizar a codificação `cl100k_base`.
- Em caso de erro, deve retornar 0 ou tratar de forma a não interromper o fluxo de minificação.
