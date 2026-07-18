# 🎓 Skill: Token Compilation Guide

## O Que É Este Skill?

Este skill é um **guia completo e educativo** sobre como o sistema de compilação Token funciona, como interpretar arquivos compilados (`.tknc` + `.tknd`), e como usar apenas esses arquivos para:

✅ Entender a estrutura completa de um projeto  
✅ Sugerir melhorias no código original  
✅ Recuperar o código original a partir do compilado  
✅ Analisar padrões e complexidade de código  

## 📚 Estrutura da Skill

### 1. **SKILL.md** - Guia Teórico Completo
Comece aqui para entender tudo sobre o sistema.

**Contém:**
- Arquitetura do sistema de compilação
- Como o compilador trabalha
- Sistema de codificação (números = palavras)
- Reversão manual (tokens → código)
- Análise de estrutura sem código original
- Padrões de compressão
- Sugestões de refatoração
- Aplicações práticas

**👉 Use quando:**
- Precisa entender o sistema completamente
- Quer aprender como funcionam os tokens
- Precisa de uma referência teórica profunda

---

### 2. **PRACTICAL-EXAMPLES.md** - Guia com Exemplos Reais
Veja como aplicar a teoria na prática usando `Calculator.java`.

**Contém:**
- Análise passo-a-passo do projeto compilado
- Como mapear classes e métodos
- Identificação de padrões
- Sugestões de melhoria concretas
- Recuperação do código original
- Mapa mental da arquitetura

**👉 Use quando:**
- Quer aprender fazendo com exemplo real
- Precisa de um passo-a-passo prático
- Quer ver sugestões de refatoração aplicadas

---

### 3. **CHEAT-SHEET.md** - Referência Rápida
Tabelas, padrões e comandos para usar rapidamente.

**Contém:**
- Tabela de símbolos especiais
- Padrões comuns de IDs
- Decodificação rápida (regex patterns)
- Processo de descompilação em 4 passos
- Checklist de análise
- Código Python para descompilar
- Exemplos rápidos
- Decision tree

**👉 Use quando:**
- Precisa de uma resposta rápida
- Está analisando arquivo e precisa consultar
- Quer copiar padrões/código

---

## 🚀 Como Começar

### Cenário 1: "Quero Entender Como o Token Funciona"
```
1. Leia: SKILL.md (Seção 1-3)
2. Veja: PRACTICAL-EXAMPLES.md (Passo 1-2)
3. Consult: CHEAT-SHEET.md (Quando precisar)
```

### Cenário 2: "Preciso Analisar Meu Código Compilado"
```
1. Rápido: CHEAT-SHEET.md (Decision Tree)
2. Detalhado: PRACTICAL-EXAMPLES.md (Seu arquivo)
3. Referência: SKILL.md (Se ficar em dúvida)
```

### Cenário 3: "Quero Sugerir Melhorias ao Projeto Original"
```
1. Estude: PRACTICAL-EXAMPLES.md (Passo 5-7)
2. Aplique: SKILL.md (Seção 6)
3. Valide: CHEAT-SHEET.md (Confirme padrões)
```

### Cenário 4: "Preciso Recuperar o Código Original"
```
1. Entenda: CHEAT-SHEET.md (Processo 4 passos)
2. Código: CHEAT-SHEET.md (Script Python)
3. Valide: PRACTICAL-EXAMPLES.md (Passo 7)
```

---

## 📊 Estrutura de Arquivo Compilado

```
projeto/
├── SeuArquivo.java
│   ├── SeuArquivo.java.tknc     ← Código Compilado (números + símbolos)
│   ├── SeuArquivo.java.tknd     ← Dicionário (ID → Palavra)
│   └── SeuArquivo.relatorio.txt ← Estatísticas
```

### O Que Cada Arquivo Significa

| Arquivo | Tipo | Propósito |
|---------|------|----------|
| `.tknc` | Compilado | Código com palavras substituídas por números |
| `.tknd` | Dicionário | Mapa: número → palavra original |
| `.relatorio.txt` | Relatório | Estatísticas de compressão |

---

## 🎯 Exemplos Rápidos

### Exemplo 1: Que Linguagem É?
```
Primeiro no .tknd: import, java, class → JAVA
Primeiro no .tknd: def, class, import → PYTHON
```

### Exemplo 2: Quantos Métodos?
```
Contar ocorrências de padrão: [tipo]_[nome]_{
Buscar por: _{$  (abre de método)
```

### Exemplo 3: Qual Tamanho Original?
```
Abrir .relatorio.txt → "Tamanho Original: XXXX bytes"
```

### Exemplo 4: Qual Palavra É ID 17?
```
No .tknd:
grep "^17," arquivo.tknd
Resultado: 17,Calculator
```

---

## 💡 Conceitos-Chave

### Tokenização
Cada palavra única recebe um ID sequencial (1, 2, 3, ...)

### Mapeamento
`.tknd` mantém relação: ID ↔ Palavra original

### Normalização
Espaços (`_`, `§n°`), quebras (`¬`), tabs (`#`) recebem símbolos

### Compressão
Resultado é 20-40% menor (típico)

### Reversibilidade
100% recuperável: `.tknc` + `.tknd` = Original

---

## 🔧 Ferramentas Relacionadas

### Compilar Arquivo
```bash
python token.py seu_arquivo.java
```

### Monitorar Alterações
```bash
python token.py seu_arquivo.java -watch
```

### Script de Descompilação
```python
# Ver em CHEAT-SHEET.md
def decompress_token_file(tknc_path, tknd_path): ...
```

---

## 📖 Leitura Recomendada

### Para Iniciantes
1. `SKILL.md` - Seção 1 (Arquitetura)
2. `PRACTICAL-EXAMPLES.md` - Passo 1-2 (Análise Inicial)
3. `CHEAT-SHEET.md` - Símbolos e Padrões

### Para Intermediários
1. `PRACTICAL-EXAMPLES.md` - Passo 3-5 (Métodos)
2. `SKILL.md` - Seção 4-5 (Reversão e Análise)
3. Exercício: Analisar seu próprio arquivo

### Para Avançados
1. `SKILL.md` - Seção 6-7 (Refatoração)
2. `CHEAT-SHEET.md` - Script Python (Automatizar)
3. Projeto: Criar analisador de tokens

---

## ❓ FAQ

### P: Posso recuperar o código original apenas com `.tknc`?
**R**: Não completamente. Precisa de `.tknc` + `.tknd` juntos.

### P: O compilado é menor? Quanto?
**R**: Sim, típicamente 20-40% mais pequeno (varia com o código).

### P: Como identificar um método no compilado?
**R**: Procure por padrão `[tipo]_[nome]_{` onde tipo é um ID de palavra-chave de tipo.

### P: Posso ver o compilado sem código original?
**R**: Sim! Esse é o propósito deste skill. Veja `PRACTICAL-EXAMPLES.md`.

### P: Como sugerir melhorias sem código original?
**R**: Analisando padrões no compilado (duplicação, métodos longos). Veja `SKILL.md` Seção 6.

---

## 🎓 Casos de Uso

### 1. **Auditoria de Código**
- Analisar estrutura de projeto compilado
- Identificar padrões de segurança
- Encontrar código duplicado

### 2. **Educação**
- Ensinar como funciona tokenização
- Compreender compressão de código
- Aprender análise de estrutura

### 3. **Refatoração**
- Identificar oportunidades de melhoria
- Sugerir consolidação de métodos
- Reorganizar estrutura

### 4. **Recuperação**
- Reconstruir código original se perdido
- Validar integridade de compilação
- Comparar versões

### 5. **Otimização**
- Melhorar taxa de compressão
- Simplificar nomenclatura
- Reduzir duplicação

---

## 🔗 Estrutura de Navegação

```
README.md (Você está aqui)
├── SKILL.md ────────────── Teórico Profundo
│   ├── 1. Arquitetura
│   ├── 2. Codificação
│   ├── 3. Reversão
│   ├── 4. Análise Sem Original
│   ├── 5. Padrões Compressão
│   ├── 6. Sugestões de Melhoria
│   └── 7. Processo Prático
│
├── PRACTICAL-EXAMPLES.md ── Exemplo Real (Calculator.java)
│   ├── Passo 1. Análise Inicial
│   ├── Passo 2. Mapear Estrutura
│   ├── Passo 3. Catalogar Métodos
│   ├── Passo 4. Análise Padrões
│   ├── Passo 5. Sugestões
│   ├── Passo 6. Complexidade
│   └── Passo 7. Recuperar Original
│
└── CHEAT-SHEET.md ───────── Referência Rápida
    ├── Tabelas Rápidas
    ├── Padrões Comuns
    ├── Processo Resumido
    ├── Código Python
    ├── Exemplos Rápidos
    └── Decision Tree
```

---

## 📝 Resumo em Uma Frase

**"Skill para entender completamente a estrutura de qualquer projeto usando apenas seus arquivos compilados Token (`.tknc` + `.tknd`), sugerir melhorias no original e recuperar código se necessário."**

---

## 🎯 Próximos Passos

1. **Escolha seu cenário** (veja "Como Começar")
2. **Comece com o documento recomendado**
3. **Pratique com seu próprio arquivo** (execute `python token.py seu_arquivo`)
4. **Aprofunde conforme necessário**
5. **Ensine a alguém** (melhor forma de aprender!)

---

**Versão**: 1.0  
**Criado**: Junho 2026  
**Status**: ✅ Completo e Pronto para Uso

### 📞 Dúvidas?
Consulte o documento relevante:
- Teórico → `SKILL.md`
- Prático → `PRACTICAL-EXAMPLES.md`  
- Rápido → `CHEAT-SHEET.md`
