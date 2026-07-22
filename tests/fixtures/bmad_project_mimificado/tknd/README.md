# Diretório de Dicionários de Tokens (tknd)

Este diretório contém o mapeamento completo entre os identificadores ofuscados encontrados no código minificado e os seus nomes originais.

## Estrutura dos Arquivos
Os arquivos estão segmentados em blocos de 500 registros para facilitar a consulta pela I.A. 
Cada arquivo é nomeado de acordo com o identificador do primeiro token contido nele (ex: A0.tknd contém os mapeamentos de A0 a A1F3...).

## Como utilizar
Sempre que encontrar um identificador ofuscado (ex: A5), procure no arquivo correspondente dentro desta pasta para identificar sua função ou nome original.

## Ferramenta de Tradução (translate.py)
Para facilitar a tradução automática, utilize o script 'translate.py' disponível na raiz do projeto original passando os tokens como argumento.
Exemplo: python3 translate.py A0 B1
