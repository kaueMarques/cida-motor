# Engine Overview: motor_v2

O `motor_v2` é uma engine de minificação extrema projetada para otimizar bases de código para o consumo por LLMs (Large Language Models), focando na maximização da janela de contexto. Através de uma abordagem inteligente, ele analisa a frequência de termos críticos, extraindo-os para um dicionário de mapeamento (RAG/Variáveis Z) e aplica técnicas de *syntax stripping* para remover ruídos visuais e verbosidade desnecessária. O resultado é um payload compacto que preserva a integridade semântica e estrutural do projeto, garantindo que a IA receba apenas o comportamento puro.

Para assegurar uma interação de alta qualidade, o motor não apenas comprime o código, mas também gera artefatos de governança (`CONSTITUTION.md` e `AGENTS.MD`), que estabelecem as regras de engajamento, instruem o modelo sobre como realizar o mapeamento reverso dos tokens e reforçam que qualquer alteração ou refatoração deve ser aplicada exclusivamente à estrutura do projeto original, não minificado.

### Principais Funcionalidades

1.  **Dicionário RAG (Variáveis Z):** Identificação automática de termos frequentes substituídos por IDs curtos, reduzindo drasticamente o consumo de tokens mantendo a rastreabilidade.
2.  **Syntax Stripping:** Remoção cirúrgica de modificadores, tipagens redundantes e ruídos de log que não agregam valor semântico à tarefa de análise ou refatoração pela IA.
3.  **Governance as Code:** Geração automática de uma `CONSTITUTION.md` e `AGENTS.MD` para guiar a persona da IA e garantir conformidade operacional.
4.  **Token Benchmarking:** Mensuração precisa de tokens (via `tiktoken` da OpenAI) antes e depois do processo, fornecendo métricas reais de economia de custo e contexto.
