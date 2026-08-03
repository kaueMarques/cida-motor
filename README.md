# CIDA-MOTOR

O CIDA-MOTOR é um motor de transpilação projetado para otimizar e preparar código-fonte para modelos de linguagem (IA). Ele reduz o tamanho do código, removendo ruídos (comentários, anotações, espaços desnecessários) e criando um dicionário de tokens para tornar o contexto mais eficiente.

## Como usar

O CIDA-MOTOR agora roda automaticamente em modo *watcher* (observador), monitorando alterações na pasta de origem em tempo real.

### Como compilar

Para gerar o binário do motor, utilize o compilador Go:

```bash
go build motor_v3.go
```

### Execução

Para rodar o motor, basta executar o binário passando a pasta de origem do código que você deseja processar:

```bash
./motor_v3 <pasta_do_seu_projeto> <pasta_de_saida> 
```

Se você não passar nenhum argumento, ele utilizará o diretório atual (`.`) como pasta de origem.

### O que acontece?

1. Ao iniciar, o motor monitora a pasta informada.
2. Sempre que qualquer arquivo na pasta for alterado, o motor detecta automaticamente, reprocessa os arquivos e gera uma versão minificada e tokenizada na pasta de destino (que, por padrão, é criada automaticamente com o sufixo `_mimificado`).
3. O modo *watcher* continuará rodando até que você interrompa o processo (pressione `Ctrl+C` no terminal).
